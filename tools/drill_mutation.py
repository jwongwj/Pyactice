"""Gate 2 for drill units: mechanical mutation, one drill at a time.

`tools/mutation_check.py` carries a hand-written catalogue of classic candidate bugs per
industry problem. That does not scale to a hundred one-function drills, and it does not
need to: a drill is small enough that the classic bugs ARE the mechanical ones -- an
off-by-one, a flipped comparison, a dropped guard, a tie-break sorted the wrong way.

So this generates mutants instead of listing them. For each drill it walks the oracle's
own function, applies one mutation at a time, and requires the drill's cases to notice.
A mutant that survives means one of two things, and they need different fixes:

  * the cases are too weak -- some real bug would pass the drill. Add a case.
  * the mutation was semantically null -- `i + 1` where the value is never used, a guard
    that is always true anyway. Nothing to fix, but you have to read it to know.

So survivors are reported with their diff rather than merely counted. There is no
"acceptable survivor count" configured anywhere on purpose: a number in a config file is
a number nobody reads again, and the judgement here is exactly what must not be
automated away.

    python3 tools/drill_mutation.py <unit-key> <path/to/oracle.py>
    python3 tools/drill_mutation.py lists /tmp/oracles/lists.py --drill deduped
"""

from __future__ import annotations

import argparse
import ast
import copy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.loader import all_problems          # noqa: E402
from harness.runner import run as run_cases      # noqa: E402

# Comparison operators, and what each becomes. Every swap is a real candidate bug:
# `<=` for `<` is the inclusive-boundary mistake, `==` for `!=` inverts a guard.
_COMPARE_SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
}


class _Mutator(ast.NodeTransformer):
    """Applies exactly ONE mutation, identified by its index in a pre-order walk.

    One at a time matters: two simultaneous mutations can cancel out, and a surviving
    pair tells you nothing about which half the suite missed.
    """

    def __init__(self, kind: str, target: int):
        self.kind = kind
        self.target = target
        self.seen = -1
        self.applied: str = ""

    def _hit(self) -> bool:
        self.seen += 1
        return self.seen == self.target

    def visit_Compare(self, node: ast.Compare):
        self.generic_visit(node)
        if self.kind == "compare":
            for index, op in enumerate(node.ops):
                replacement = _COMPARE_SWAPS.get(type(op))
                if replacement is None:
                    continue
                if self._hit():
                    was = type(op).__name__
                    node.ops[index] = replacement()
                    self.applied = f"comparison {was} -> {replacement.__name__}"
        return node

    def visit_Constant(self, node: ast.Constant):
        # `is True`/`is False` are bools, and bool is a subclass of int -- tweaking one
        # produces `if 2:` which is a different mutation than intended.
        if self.kind in ("int+1", "int-1") and isinstance(node.value, int) \
                and not isinstance(node.value, bool):
            if self._hit():
                delta = 1 if self.kind == "int+1" else -1
                was = node.value
                node.value = node.value + delta
                self.applied = f"literal {was} -> {node.value}"
        return node

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        if self.kind in ("guard-true", "guard-false"):
            if self._hit():
                wanted = self.kind == "guard-true"
                self.applied = f"guard `{ast.unparse(node.test)}` -> {wanted}"
                node.test = ast.Constant(value=wanted)
        return node

    def visit_BoolOp(self, node: ast.BoolOp):
        self.generic_visit(node)
        if self.kind == "bool-flip":
            if self._hit():
                was = type(node.op).__name__
                node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
                self.applied = f"{was} -> {type(node.op).__name__}"
        return node

    def visit_UnaryOp(self, node: ast.UnaryOp):
        self.generic_visit(node)
        # Dropping a unary minus is how a descending sort key silently becomes ascending,
        # which is the single most common tie-break bug in this whole bank.
        if self.kind == "drop-negation" and isinstance(node.op, ast.USub):
            if self._hit():
                self.applied = f"dropped the minus in `-{ast.unparse(node.operand)}`"
                return node.operand
        if self.kind == "drop-not" and isinstance(node.op, ast.Not):
            if self._hit():
                self.applied = f"dropped the `not` in `{ast.unparse(node)}`"
                return node.operand
        return node

    def visit_keyword(self, node: ast.keyword):
        self.generic_visit(node)
        # `reverse=True` <-> `reverse=False`, and the same for any other bool keyword.
        if self.kind == "flip-keyword" and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, bool):
            if self._hit():
                was = node.value.value
                node.value = ast.Constant(value=not was)
                self.applied = f"{node.arg}={was} -> {not was}"
        return node


KINDS = ("compare", "int+1", "int-1", "guard-true", "guard-false",
         "bool-flip", "drop-negation", "drop-not", "flip-keyword")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    """The named function, top level or inside a class body.

    A `design` problem's oracle is a class, so its methods are one level down. Nested
    functions deeper than that are a solution's own business and are not searched.
    """
    bodies = [tree.body]
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bodies.append(node.body)
    for body in bodies:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name == name:
                return node                                # type: ignore[return-value]
    return None


def _mutants(source: str, target: str):
    """Every single-mutation variant of `target`, as (label, mutated source)."""
    base = ast.parse(source)
    if _function(base, target) is None:
        return
    for kind in KINDS:
        index = 0
        while True:
            tree = ast.parse(source)
            scope = _function(tree, target)
            mutator = _Mutator(kind, index)
            # Scoped to the one function: mutating a sibling drill's code would be
            # graded against cases that never call it, and always "survive".
            mutator.visit(scope)
            if not mutator.applied:
                break
            yield f"{kind}: {mutator.applied}", ast.unparse(tree)
            index += 1


# ---------------------------------------------------------------------------
# triage: is a survivor a real gap, or a semantically null mutation?


def _shape(value):
    """A crude type signature, used to generate more values of the same shape."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, str):
        return "str"
    if isinstance(value, tuple):
        # Every position's type, in order. Arity alone was not enough: a weighted edge is
        # (str, str, int), and collapsing that to "a tuple of any" made the fuzzer hand
        # integer node names to a drill whose signature says they are strings.
        return "tuple<" + ",".join(_shape(item) for item in value) + ">"
    if isinstance(value, list):
        inner = {_shape(item) for item in value}
        return f"list[{inner.pop() if len(inner) == 1 else 'any'}]"
    if isinstance(value, dict):
        keys = {_shape(k) for k in value}
        vals = {_shape(v) for v in value.values()}
        return (f"dict[{keys.pop() if len(keys) == 1 else 'any'},"
                f"{vals.pop() if len(vals) == 1 else 'any'}]")
    return "other"


def _generate(shape, rng, ints, strings, depth=0):
    """A random value of the given shape, drawn from the vocabulary the cases used.

    Sampling ints and strings from the drill's own cases rather than a generic range
    keeps the inputs in the domain the drill is about -- a grid drill gets 0s and 1s, a
    temperature drill gets temperatures.
    """
    if shape == "bool":
        return rng.choice([True, False])
    if shape == "int":
        return rng.choice(ints) if ints else rng.randint(-3, 5)
    if shape == "str":
        return rng.choice(strings) if strings else "a"
    if shape.startswith("tuple<"):
        parts = shape[6:-1].split(",") if shape[6:-1] else []
        return tuple(_generate(part or "int", rng, ints, strings, depth + 1)
                     for part in parts)
    if shape.startswith("list["):
        inner = shape[5:-1]
        if inner == "any":
            inner = "int"
        length = rng.randint(0, 4 if depth == 0 else 3)
        return [_generate(inner, rng, ints, strings, depth + 1) for _ in range(length)]
    if shape.startswith("dict["):
        keyshape, valshape = shape[5:-1].split(",", 1)
        if keyshape == "any":
            keyshape = "str"
        if valshape == "any":
            valshape = "int"
        return {
            _generate(keyshape, rng, ints, strings, depth + 1):
                _generate(valshape, rng, ints, strings, depth + 1)
            for _ in range(rng.randint(0, 3))
        }
    return None


def _repair(args, rules, rng):
    """Bring a generated input inside the drill's stated precondition.

    Without this the fuzzer happily hands an unsorted list to a binary search and calls
    the disagreement a gap. The drill promised a sorted list; a mutant that misbehaves on
    an unsorted one has not been shown to be a real bug.
    """
    if not rules:
        return args

    if "edges" in rules:
        # Cross-argument, unlike everything below it: an edge list is only meaningful
        # against the node list beside it, and a generated edge naming a node that does
        # not exist tests behaviour no statement here defines.
        vocabulary = next(
            (a for a in args if isinstance(a, list) and a
             and all(isinstance(x, (str, int)) and not isinstance(x, bool) for x in a)),
            None,
        )
        repaired = []
        for value in args:
            if (isinstance(value, list) and value
                    and all(isinstance(x, tuple) for x in value)):
                if vocabulary is None:
                    repaired.append([])
                else:
                    repaired.append([
                        tuple(vocabulary[hash(part) % len(vocabulary)] for part in edge)
                        for edge in value
                    ])
            else:
                repaired.append(value)
        args = repaired

    if "ordered-pairs" in rules:
        # An interval whose end precedes its start is not an interval. Without this the
        # fuzzer invents (10, 5) and reports whatever the oracle happens to do with it
        # as a suite gap -- which it did, thirteen times, on the intervals unit.
        def order(value):
            if isinstance(value, tuple) and len(value) == 2 \
                    and all(isinstance(x, int) for x in value):
                return tuple(sorted(value))
            if isinstance(value, list) and value and all(
                    isinstance(x, tuple) and len(x) == 2
                    and all(isinstance(y, int) for y in x) for x in value):
                return [tuple(sorted(pair)) for pair in value]
            return value

        args = [order(value) for value in args]

    if "disjoint-sorted" in rules:
        # Some drills are handed an already-sorted, non-overlapping list and say so.
        # Generated ones are neither, and every disagreement that produces is about
        # behaviour the statement never promised.
        def tidy(value):
            if not (isinstance(value, list) and value and all(
                    isinstance(x, tuple) and len(x) == 2
                    and all(isinstance(y, int) for y in x) for x in value)):
                return value
            merged = []
            for start, end in sorted(value):
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            return merged

        args = [tidy(value) for value in args]

    if "paired-lists" in rules:
        # Two lists indexed together -- arrivals and departures, gas and cost. A generated
        # pair of different lengths is not an input the drill promises to handle, and the
        # oracle's IndexError is not a suite gap.
        lists = [a for a in args
                 if isinstance(a, list) and all(isinstance(x, int) for x in a)]
        if len(lists) > 1:
            shortest = min(len(a) for a in lists)
            args = [
                value[:shortest]
                if isinstance(value, list) and all(isinstance(x, int) for x in value)
                else value
                for value in args
            ]

    if "paired-ordered" in rules:
        # `paired-lists` plus the guarantee that the two lists are a START and an END for
        # the same thing: a train cannot depart before it arrives. Without this the fuzzer
        # invents one and calls the resulting IndexError a suite gap.
        lists = [i for i, a in enumerate(args)
                 if isinstance(a, list) and all(isinstance(x, int) for x in a)]
        if len(lists) == 2:
            first, second = args[lists[0]], args[lists[1]]
            width = min(len(first), len(second))
            starts, ends = [], []
            for index in range(width):
                lo, hi = sorted((first[index], second[index]))
                starts.append(lo)
                # Strictly after: a zero-duration train makes "does it need a platform"
                # ambiguous, and the drill excludes it rather than answering it.
                ends.append(hi if hi > lo else lo + 1)
            args = list(args)
            args[lists[0]], args[lists[1]] = starts, ends

    if "colors" in rules:
        # The Dutch-flag drill promises only 0, 1 and 2.
        args = [
            [abs(x) % 3 for x in value]
            if isinstance(value, list) and value
            and all(isinstance(x, int) and not isinstance(x, bool) for x in value)
            else value
            for value in args
        ]

    if "nonneg" in rules:
        # Also inside tuples: a weighted edge is (node, node, weight), and Dijkstra
        # requires the weight to be non-negative -- the fuzzer invented -1 and reported
        # what the oracle happens to do with it.
        args = [
            [tuple(abs(x) if isinstance(x, int) and not isinstance(x, bool) else x
                   for x in item) for item in value]
            if (isinstance(value, list) and value
                and all(isinstance(item, tuple) for item in value))
            else value
            for value in args
        ]

    out = []
    for value in args:
        if "grid" in rules and isinstance(value, list) \
                and all(isinstance(row, list) for row in value):
            # A grid is RECTANGULAR and holds only 0 and 1. Generated rows are ragged and
            # full of arbitrary ints, and every "gap" the fuzzer first reported for the
            # BFS drill was an IndexError on a ragged row -- a bug in the probe, not the
            # suite.
            rows = [row for row in value if row]
            if not rows:
                out.append([])
                continue
            width = min(len(row) for row in rows)
            out.append([[1 if cell else 0 for cell in row[:width]] for row in rows])
            continue
        if ("unique" in rules and isinstance(value, list)
                and all(isinstance(x, str) for x in value)):
            out.append(list(dict.fromkeys(value)))
            continue
        if isinstance(value, list) and all(isinstance(x, int) for x in value):
            if "positive" in rules:
                value = [max(1, abs(x)) for x in value]
            elif "nonneg" in rules:
                value = [abs(x) for x in value]
            if "binary" in rules:
                value = [1 if x else 0 for x in value]
            if "unique" in rules:
                value = list(dict.fromkeys(value))
            if "sorted" in rules or "rotated" in rules:
                value = sorted(value)
            if "rotated" in rules and value:
                cut = rng.randrange(len(value))
                value = value[cut:] + value[:cut]
        elif isinstance(value, int) and not isinstance(value, bool):
            if "positive" in rules:
                value = max(1, abs(value))
            elif "nonneg" in rules:
                value = abs(value)
        out.append(value)
    return out


def _vocabulary(problem):
    """Every int and str literal appearing in this drill's case arguments."""
    ints: list[int] = []
    strings: list[str] = []

    def walk(value):
        if isinstance(value, bool):
            return
        if isinstance(value, int):
            ints.append(value)
        elif isinstance(value, str):
            strings.append(value)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                walk(key)
                walk(item)

    for entry in problem.cases:
        for operation in entry.ops:
            walk(list(operation.args))
    # Always worth trying, and frequently the answer: the boundary values.
    ints.extend([0, 1, -1, 2])
    return sorted(set(ints)), sorted(set(strings)) or ["a", "b"]


class _Timeout(BaseException):
    """Not an Exception: candidate-style code must not be able to swallow it."""


def _call_with_limit(function, args, seconds=0.5):
    """Run it, or raise _Timeout. A mutant that never returns is a caught mutant.

    The mutants are executed directly here rather than through the runner, so nothing
    else bounds them -- and a mutated cycle detector loops forever by construction. This
    hung the tool on the first graph unit until it was added.
    """
    import signal

    def fire(_signum, _frame):
        raise _Timeout()

    previous = signal.signal(signal.SIGALRM, fire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return function(*args)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _counterexample(problem, oracle_source, mutant_source, target, tries, seed):
    """An input where oracle and mutant disagree, or None if none was found."""
    import random

    oracle_ns: dict = {}
    mutant_ns: dict = {}
    try:
        exec(compile(oracle_source, "<oracle>", "exec"), oracle_ns)
        exec(compile(mutant_source, "<mutant>", "exec"), mutant_ns)
    except BaseException:
        return None
    good, bad = oracle_ns.get(target), mutant_ns.get(target)
    if good is None or bad is None:
        # A `design` problem's methods live inside a class, so there is no single call to
        # fuzz -- what distinguishes two implementations is a SEQUENCE of calls against
        # one instance. Build those instead.
        if problem.is_class_kind:
            return _sequence_counterexample(
                problem, oracle_ns, mutant_ns, tries, seed)
        return "unfuzzable"

    # Merged across EVERY case, not taken from the first. An empty list yields
    # `list[any]`, so a drill whose first case passes `[]` had its element type decided
    # by the least informative example -- and the fuzzer then handed a list of ints to a
    # parameter documented as a list of pairs.
    shapes: list[str] | None = None
    for entry in problem.cases:
        for operation in entry.ops:
            if operation.name != problem.methods[0].display:
                continue
            found = [_shape(arg) for arg in operation.args]
            if shapes is None:
                shapes = found
            elif len(shapes) == len(found):
                shapes = [
                    known if "any" not in known or "any" in fresh else fresh
                    for known, fresh in zip(shapes, found)
                ]
    if shapes is None:
        return None

    # A shape this generator does not understand yields None for every probe, so the
    # mutant is only ever handed empty input and reports "null" having tested almost
    # nothing. Saying so is the whole point: a vacuous check that looks like a pass is
    # worse than no check.
    if any(shape == "other" for shape in shapes):
        return "unfuzzable"

    ints, strings = _vocabulary(problem)
    rules = tuple(problem.methods[0].fuzz)
    rng = random.Random(seed)
    for _ in range(tries):
        args = _repair(
            [_generate(shape, rng, ints, strings) for shape in shapes], rules, rng)
        try:
            expected = _call_with_limit(good, copy.deepcopy(args))
        except BaseException:
            continue                       # the oracle rejects this input; not a probe
        try:
            actual = _call_with_limit(bad, copy.deepcopy(args))
        except _Timeout:
            return args, expected, "did not terminate"
        except BaseException as error:
            return args, expected, f"raised {type(error).__name__}"
        if expected != actual:
            return args, expected, actual
    return None



def _sequence_counterexample(problem, oracle_ns, mutant_ns, tries, seed):
    """A sequence of calls on which two implementations of a class disagree.

    A single call proves nothing about a stateful object: what separates a correct
    MinStack from a broken one is what happens after a particular history. So each probe
    is a random run of operations, applied to a fresh instance of each, comparing every
    return value as it goes.

    Arguments come from the problem's own cases, so the values stay in the domain the
    author intended without needing a separate vocabulary.
    """
    import random

    cls_name = problem.class_name
    good_cls, bad_cls = oracle_ns.get(cls_name), mutant_ns.get(cls_name)
    if good_cls is None or bad_cls is None:
        return "unfuzzable"

    # Every (method, arguments) pair any case ever used, as the alphabet to draw from.
    alphabet = []
    by_display = {m.display: m.resolved_name() for m in problem.methods}
    # Methods whose return the statement leaves open -- a group's root, an arbitrary
    # index among equals. Their value is not evidence of anything, so comparing it
    # reports two correct implementations as disagreeing.
    opaque = {m.resolved_name() for m in problem.methods if "opaque" in m.fuzz}
    for entry in problem.cases:
        for operation in entry.ops:
            name = by_display.get(operation.name)
            if name:
                alphabet.append((name, tuple(operation.args)))
    if not alphabet:
        return "unfuzzable"

    rng = random.Random(seed)
    for _ in range(tries):
        run = [rng.choice(alphabet) for _ in range(rng.randint(1, 12))]
        try:
            left, right = good_cls(), bad_cls()
        except BaseException:
            return "unfuzzable"
        for name, args in run:
            try:
                expected = _call_with_limit(getattr(left, name), copy.deepcopy(args))
            except BaseException:
                break                      # the oracle rejects this history; stop here
            try:
                actual = _call_with_limit(getattr(right, name), copy.deepcopy(args))
            except _Timeout:
                return run, expected, "did not terminate"
            except BaseException as error:
                return run, expected, f"raised {type(error).__name__}"
            if name not in opaque and expected != actual:
                return run, expected, actual
    return None


def check(unit_key: str, oracle: Path, only: str | None = None,
          triage: int = 0, seed: int = 1) -> int:
    problems = {
        key: problem for key, problem in all_problems().items()
        if problem.solution_key == unit_key or key == unit_key
    }
    if not problems:
        print(f"no drills found for unit {unit_key!r}")
        return 2

    source = oracle.read_text()

    # An oracle missing a drill's function generates no mutants and would otherwise be
    # indistinguishable from a one-liner with nothing to break. Both print, but they mean
    # very different things, so they must not share a line.
    parsed = ast.parse(source)
    missing = sorted(
        (key if len(problem.methods) == 1 else f"{key}.{method.resolved_name()}")
        for key, problem in problems.items()
        for method in problem.methods
        if _function(parsed, method.resolved_name()) is None
    )
    if missing and (not only):
        print(f"  MISSING from the oracle: {', '.join(missing)}")
        print("  (these drills were not verified at all by this gate)")
    total = caught = survivors = skipped = 0
    report: list[str] = []
    unmutable: list[str] = []
    alive: list[tuple] = []

    # A drill has one method; a `design` problem is a class with several, and every one
    # of them deserves mutating. Without this only the first was ever touched, which for
    # a MinStack meant `push` and nothing else.
    targets = []
    for key, problem in sorted(problems.items()):
        names = [method.resolved_name() for method in problem.methods]
        # Private helpers too. A `design` oracle puts its real logic in one -- the whole
        # correctness argument for the two-stack queue lives in `_shift` -- and mutating
        # only the declared interface leaves that untouched and silently uncovered.
        if problem.is_class_kind:
            declared = set(names)
            for node in ast.parse(source).body:
                if not isinstance(node, ast.ClassDef):
                    continue
                for member in node.body:
                    if (isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and member.name not in declared
                            and member.name != "__init__"):
                        names.append(member.name)
        targets.extend((key, problem, name) for name in names)
    for key, problem, target in targets:
        if only and only not in (key, target):
            continue
        seen: set[str] = set()
        drill_total = drill_caught = 0
        for label, mutated in _mutants(source, target):
            # ast.unparse normalises formatting, so a mutation with no semantic effect
            # can reproduce the baseline exactly. Those are not mutants at all.
            if mutated in seen:
                skipped += 1
                continue
            seen.add(mutated)
            total += 1
            drill_total += 1
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "mutant.py"
                path.write_text(mutated)
                try:
                    # 1s, not the runner's usual budget. Every case in a drill unit runs
                    # in microseconds on inputs this small, so a mutant that needs longer
                    # is looping -- and a looping mutant IS a caught one. At 5s the cycle
                    # detection drill alone took over an hour, because every mutant that
                    # failed to terminate paid the full timeout on all 36 cases.
                    result = run_cases(problem, path, max_level=1, op_timeout=1.0)
                except BaseException as error:              # a mutant that will not import
                    caught += 1
                    drill_caught += 1
                    report.append(f"    caught (did not run: {type(error).__name__})  {label}")
                    continue
            failed = sum(1 for lvl in result.levels for c in lvl.cases if not c.passed)
            if failed:
                caught += 1
                drill_caught += 1
            else:
                survivors += 1
                shown = key if len(problem.methods) == 1 else f"{key}.{target}"
                report.append(f"  SURVIVED  {shown}  [{label}]")
                alive.append((shown, problem, target, label, mutated))
        if drill_total:
            mark = "ok  " if drill_caught == drill_total else "GAP "
            label = key if len(problem.methods) == 1 else f"{key}.{target}"
            print(f"  {mark} {label:34} {drill_caught}/{drill_total} mutants caught")
        else:
            # Silence here would read as "covered". A one-liner delegating to a stdlib
            # call has no branch, comparison or literal to break, so this gate has
            # nothing to say about it and Gate 1 plus its constraint are all it has.
            unmutable.append(
                key if len(problem.methods) == 1 else f"{key}.{target}")

    print()
    for line in report:
        if line.strip().startswith("SURVIVED"):
            print(line)
    unmutable = [key for key in unmutable if key not in set(missing)]
    if missing:
        print(f"  {len(missing)} drill(s) absent from the oracle and therefore unchecked: "
              f"{', '.join(missing)}")
    if unmutable:
        print(f"  no mutants generated for {len(unmutable)}: {', '.join(unmutable)}")
        print("  (nothing to break -- a stdlib delegation. Gate 1 and the constraint are\n"
              "   the whole guard for these, which is worth knowing rather than assuming.)")
        print()
    print(f"{total} mutants · {caught} caught · {survivors} survived"
          + (f" · {skipped} formatting-identical, not counted" if skipped else ""))

    if survivors and triage:
        # Judging survivors by reading them is where the mistakes are: a plausible
        # argument for "that cannot matter" is not evidence. So each survivor is run
        # against the oracle over fuzzed inputs shaped like the drill's own cases. A
        # disagreement is a REAL gap and comes with the input that proves it; finding
        # none is not proof of nullity, but it is the same check done far more times
        # than by hand.
        print(f"\n── triage: {triage} fuzzed inputs per survivor ──")
        real = 0
        unfuzzable = 0
        for key, problem, target, label, mutated in alive:
            found = _counterexample(problem, source, mutated, target, triage, seed)
            if found == "unfuzzable":
                unfuzzable += 1
                print(f"  CANNOT FUZZ {key}  [{label}]")
                print(f"           an argument has a shape the generator does not build "
                      f"(a Node, a tree, a custom object).")
                print(f"           This survivor is UNJUDGED -- check it yourself.")
                continue
            if found is None:
                print(f"  null?    {key}  [{label}]")
                continue
            real += 1
            args, expected, actual = found
            print(f"  REAL GAP {key}  [{label}]")
            if args and isinstance(args[0], tuple) and len(args[0]) == 2 \
                    and isinstance(args[0][0], str):
                calls = "; ".join(
                    f"{name}({', '.join(repr(a) for a in values)})"
                    for name, values in args)
                print(f"           {calls}")
            else:
                print(f"           {target}({', '.join(repr(a) for a in args)})")
            print(f"           oracle {expected!r}, mutant {actual!r}")
        print(f"\n{real} of {len(alive)} survivors have a counterexample and need a case.")
        if unfuzzable:
            print(f"{unfuzzable} could not be fuzzed at all and remain UNJUDGED.")
        print(f"{len(alive) - real - unfuzzable} found none in {triage} tries -- likely "
              "null, and the label tells you whether that is believable.")
        return 1 if (real or unfuzzable) else 0

    if survivors:
        print("\nRead every survivor above, or re-run with --triage N to fuzz them against\n"
              "the oracle. Either the drill needs a case, or the mutation was semantically\n"
              "null -- and reading alone is a poor way to tell which.")
    return 1 if survivors else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("unit", help="unit key, e.g. lists")
    parser.add_argument("oracle", type=Path, help="path to the oracle, OUTSIDE the repo")
    parser.add_argument("--drill", help="only this drill (its key or its function name)")
    parser.add_argument("--triage", type=int, default=0, metavar="N",
                        help="for each survivor, fuzz N inputs against the oracle looking "
                             "for a counterexample. Turns a list of survivors to eyeball "
                             "into a list of real gaps with the input that proves each one.")
    parser.add_argument("--seed", type=int, default=1,
                        help="seed for --triage, so a counterexample is reproducible")
    args = parser.parse_args(argv)
    if not args.oracle.exists():
        print(f"no such oracle: {args.oracle}")
        return 2
    return check(args.unit, args.oracle, args.drill, args.triage, args.seed)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
