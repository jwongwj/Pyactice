"""Constraints: grading *how* an answer was reached, not only what it returned.

A Tier 0 drill teaches an idiom. Ask for the three largest values and a nested loop
returns the right list -- so a grader that only checks the return value lets the
learner pass while missing the entire lesson. The idiom was the point; the output was
incidental.

So a drill declares what must be true of the code as well as of the answer, and this
module checks that by parsing the source. It never executes anything: `ast.parse` only,
the same discipline `webui/complete.py` follows.

Two rules this module exists to enforce on itself:

  * A violated constraint is NOT a wrong answer, and must never be reported as one.
    "Wrong" teaches nothing; "correct, but you hand-rolled what the library does in one
    call" teaches the thing. Callers get `passed` and `violations` separately so they
    can say both.
  * Every constraint carries the reason it exists, in words a learner can act on. A
    constraint that only says "forbidden: For" is a trick question.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Iterable

# Nodes a drill can forbid, by the name an author writes in the problem file. Keeping
# this an explicit map rather than `getattr(ast, name)` means a typo is an authoring
# error caught at import, not a constraint that silently never fires.
FORBIDDABLE = {
    "for": (ast.For, ast.AsyncFor),
    "while": (ast.While,),
    "comprehension": (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
    "listcomp": (ast.ListComp,),
    "dictcomp": (ast.DictComp,),
    "lambda": (ast.Lambda,),
    "if": (ast.If,),
    "break": (ast.Break,),
    "continue": (ast.Continue,),
    "try": (ast.Try,),
    "subscript": (ast.Subscript,),
    # `or` and `and` are distinguished, because "do not paper over a missing value with
    # `x or default`" is a real lesson and "do not use boolean operators" is not.
    "or": (),                 # handled specially: ast.BoolOp with ast.Or
    "and": (),                # handled specially: ast.BoolOp with ast.And
    "augassign": (ast.AugAssign,),
    "recursion": (),          # handled specially: a call to the function's own name
    # Also special: a mutable literal as a parameter default. Evaluated ONCE at
    # definition time, so it is shared by every call -- the most famous gotcha in the
    # language, and one you cannot see by reading the function body.
    "mutable-default": (),
}


@dataclass(frozen=True)
class Violation:
    """One constraint that was not met, phrased so the learner knows what to do."""

    rule: str
    message: str
    hint: str = ""
    line: int = 0


@dataclass(frozen=True)
class Result:
    violations: tuple[Violation, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.violations


# ---------------------------------------------------------------------------
# constraint types


@dataclass(frozen=True)
class Forbid:
    """Reject a syntactic construct.

    `because` is mandatory in spirit: a forbidden construct with no stated reason is
    indistinguishable from an arbitrary rule, and the learner correctly resents it.
    """

    what: tuple[str, ...]
    because: str
    hint: str = ""

    def check(self, scope: ast.AST, source: str, target: str) -> list[Violation]:
        found: list[Violation] = []
        for name in self.what:
            if name not in FORBIDDABLE:
                raise ValueError(f"unknown construct {name!r}; known: {sorted(FORBIDDABLE)}")
            if name == "recursion":
                node = _self_call(scope, target)
                if node is not None:
                    found.append(
                        Violation("forbid:recursion", f"{target}() calls itself.",
                                  self.hint or self.because, getattr(node, "lineno", 0))
                    )
                continue
            if name in ("or", "and"):
                wanted = ast.Or if name == "or" else ast.And
                node = next(
                    (n for n in ast.walk(scope)
                     if isinstance(n, ast.BoolOp) and isinstance(n.op, wanted)),
                    None,
                )
                if node is not None:
                    found.append(
                        Violation(f"forbid:{name}", f"You used `{name}`.",
                                  self.hint or self.because, getattr(node, "lineno", 0))
                    )
                continue
            if name == "mutable-default":
                node = _mutable_default(scope)
                if node is not None:
                    found.append(
                        Violation(
                            "forbid:mutable-default",
                            f"{target}() has a mutable default argument.",
                            self.hint or self.because,
                            getattr(node, "lineno", 0),
                        )
                    )
                continue
            types = FORBIDDABLE[name]
            for node in ast.walk(scope):
                if isinstance(node, types):
                    found.append(
                        Violation(
                            f"forbid:{name}",
                            f"You used `{name}`.",
                            self.hint or self.because,
                            getattr(node, "lineno", 0),
                        )
                    )
                    break     # one report per construct; ten is noise, not information
        return found


@dataclass(frozen=True)
class ForbidCall:
    """Reject calling something by name, e.g. sorting the whole list for a top-n drill."""

    names: tuple[str, ...]
    because: str
    hint: str = ""

    def check(self, scope: ast.AST, source: str, target: str) -> list[Violation]:
        called = _calls(scope)
        found = []
        for name in self.names:
            if name in called:
                found.append(
                    Violation(
                        f"forbid-call:{name}",
                        f"You called `{name}`.",
                        self.hint or self.because,
                        called[name],
                    )
                )
        return found


@dataclass(frozen=True)
class RequireCall:
    """Insist on a specific call — the tool the unit is about.

    Matched on the trailing attribute too, so `heapq.nlargest`, `nlargest` and
    `hq.nlargest` all satisfy `RequireCall(("heapq.nlargest",))`. An import-alias
    technicality is not the lesson.
    """

    names: tuple[str, ...]
    because: str
    hint: str = ""

    def check(self, scope: ast.AST, source: str, target: str) -> list[Violation]:
        called = set(_calls(scope))
        tails = {name.rsplit(".", 1)[-1] for name in called}
        for wanted in self.names:
            tail = wanted.rsplit(".", 1)[-1]
            if wanted in called or tail in tails:
                return []
        listed = " or ".join(f"`{n}`" for n in self.names)
        return [Violation("require-call", f"This drill wants {listed}.",
                          self.hint or self.because)]


@dataclass(frozen=True)
class RequireConstruct:
    """Insist on a syntactic form, e.g. "this should be a comprehension"."""

    what: str
    because: str
    hint: str = ""

    def check(self, scope: ast.AST, source: str, target: str) -> list[Violation]:
        if self.what not in FORBIDDABLE:
            raise ValueError(f"unknown construct {self.what!r}")
        types = FORBIDDABLE[self.what]
        if any(isinstance(node, types) for node in ast.walk(scope)):
            return []
        return [Violation("require-construct", f"This drill wants a `{self.what}`.",
                          self.hint or self.because)]


@dataclass(frozen=True)
class MaxStatements:
    """Budget the body of the target function.

    Counts statements rather than lines, so formatting is never the thing being graded.
    A docstring does not count; nobody should have to delete an explanation to pass.
    """

    limit: int
    because: str = "the idiomatic version is dramatically shorter"
    hint: str = ""

    def check(self, scope: ast.AST, source: str, target: str) -> list[Violation]:
        function = scope if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) \
            else _find_function(scope, target)
        if function is None:
            return []
        body = list(function.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body = body[1:]
        count = len(body)
        if count <= self.limit:
            return []
        allowed = "1 statement" if self.limit == 1 else f"{self.limit} statements"
        return [Violation(
            "max-statements",
            f"{target}() has {count} statements; this drill allows {allowed}.",
            self.hint or self.because,
            getattr(function, "lineno", 0),
        )]


# ---------------------------------------------------------------------------
# AST helpers


def _calls(tree: ast.AST) -> dict[str, int]:
    """Called name -> the line of its first call. `a.b.c(...)` records "a.b.c"."""
    out: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _dotted(node.func)
        if name and name not in out:
            out[name] = getattr(node, "lineno", 0)
    return out


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node  # type: ignore[return-value]
    return None


def _mutable_default(scope: ast.AST) -> ast.AST | None:
    """A list/dict/set literal used as a parameter default.

    Only the function's own signature is inspected, never a nested def -- a helper
    defined inside is its own business.
    """
    if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    args = scope.args
    for default in list(args.defaults) + [d for d in args.kw_defaults if d is not None]:
        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
            return default
        # `dict()`, `list()` and `set()` are the same trap wearing a call.
        if isinstance(default, ast.Call) and _dotted(default.func) in {"list", "dict", "set"}:
            return default
    return None


def _self_call(scope: ast.AST, name: str) -> ast.AST | None:
    function = scope if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) \
        else _find_function(scope, name)
    if function is None:
        return None
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and _dotted(node.func).rsplit(".", 1)[-1] == name:
            return node
    return None


# ---------------------------------------------------------------------------
# entry point


def check(source: str, target: str, constraints: Iterable) -> Result:
    """Check `source` against `constraints`, for the function named `target`.

    **Scoped to that function's own body.** A drill unit is a dozen functions in one
    file, so checking the whole module means every drill is judged on every other
    drill's code -- which reported a correct comprehension as "you used `for`" because
    some unrelated drill above it did. The bug is invisible with one function per file
    and unavoidable with twelve.

    Two deliberate no-ops:
      * unparseable source yields nothing, because the runner is already reporting the
        syntax error and constraint noise on top of it buries the one fact that matters;
      * a missing target function yields nothing, for the same reason -- the runner
        reports "your file defines no function x()" far more usefully.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return Result()

    scope = _find_function(tree, target)
    if scope is None:
        return Result()

    violations: list[Violation] = []
    for constraint in constraints:
        violations.extend(constraint.check(scope, source, target))
    return Result(tuple(violations))
