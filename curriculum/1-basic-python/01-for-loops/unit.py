"""1.1 For loops and comprehensions — the first drill unit.

Self-contained on purpose: the loader imports this by file path, because the numbered
directory names are not importable identifiers, so there are no package-relative
imports and the cases live here beside the drills they belong to.

Every drill has a constraint, and the constraint is the lesson. The right answer with a
hand-rolled loop is not the point; letting the language iterate for you is. So the
grader checks the shape of the code as well as the value it returned, and reports the
two separately -- "correct" and "not the point of this drill" are different verdicts.

Constraints are printed into the stub docstring via `constraint_note`. A constraint the
learner could not have known about is a trick question.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall, RequireConstruct
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

# ---------------------------------------------------------------------------
# the drills, in the order they should be met

METHODS = (
    Method(
        display="SHOUT",
        signature="(names: list[str]) -> list[str]",
        doc="Every name in upper case, in the same order.",
        constraint_note="write it as a comprehension; no `for` statement",
        constraints=(
            Forbid(("for",), because="a one-to-one transformation is what a comprehension is for",
                   hint="[name.upper() for name in names]"),
        ),
    ),
    Method(
        display="PY_FILES",
        signature="(paths: list[str]) -> list[str]",
        doc="Only the paths ending in '.py', in the same order.",
        constraint_note="one comprehension with an `if`; no `for` statement",
        constraints=(
            Forbid(("for",), because="filtering is a comprehension with a condition",
                   hint='[p for p in paths if p.endswith(".py")]'),
        ),
    ),
    Method(
        display="NUMBERED",
        signature="(lines: list[str]) -> list[str]",
        doc='["1. first", "2. second", ...] — one-based numbering.',
        constraint_note="use enumerate; do not index with range(len(...))",
        constraints=(
            ForbidCall(("range",), because="enumerate already gives you the index",
                       hint="for i, line in enumerate(lines, start=1)"),
            RequireCall(("enumerate",), because="this drill is about enumerate"),
        ),
    ),
    Method(
        display="PAIR_UP",
        signature="(names: list[str], scores: list[int]) -> list[str]",
        doc='["ada: 90", ...] — pair each name with the score at the same position.',
        constraint_note="use zip; no indexing either list",
        constraints=(
            Forbid(("subscript",), because="zip walks two sequences together",
                   hint="for name, score in zip(names, scores)"),
            RequireCall(("zip",), because="this drill is about zip"),
        ),
    ),
    Method(
        display="BACKWARDS",
        signature="(items: list[int]) -> list[int]",
        doc="The same items, last to first.",
        constraint_note="use reversed; not a [::-1] slice and no index arithmetic",
        constraints=(
            RequireCall(("reversed",), because="this drill is about reversed",
                        hint="list(reversed(items))"),
            Forbid(("subscript",), because="a slice is a different tool; practise this one"),
        ),
    ),
    Method(
        display="EVERY_OTHER",
        signature="(items: list[int]) -> list[int]",
        doc="Items at positions 0, 2, 4, …",
        constraint_note="one slice with a step; no loop of any kind",
        constraints=(
            Forbid(("for", "while", "comprehension"),
                   because="a stride is what the third slice argument is for",
                   hint="items[::2]"),
        ),
    ),
    Method(
        display="FIRST_ADMIN",
        signature="(users: list[dict]) -> dict | None",
        doc="The first user whose 'role' is 'admin', or None if there is none.",
        constraint_note="use next() with a default; no `break`",
        constraints=(
            Forbid(("break",), because="next() with a default expresses early exit as a value",
                   hint='next((u for u in users if u["role"] == "admin"), None)'),
            RequireCall(("next",), because="this drill is about next()"),
        ),
    ),
    Method(
        display="RISING",
        signature="(readings: list[int]) -> list[bool]",
        doc="For each consecutive pair, True when the second is larger. One shorter than the input.",
        constraint_note="compare neighbours with zip; no index arithmetic",
        constraints=(
            RequireCall(("zip",), because="zip(xs, xs[1:]) is the neighbour-pair idiom",
                        hint="[b > a for a, b in zip(readings, readings[1:])]"),
            ForbidCall(("range",), because="indices are not needed to compare neighbours"),
        ),
    ),
    Method(
        display="FLATTEN",
        signature="(rows: list[list[int]]) -> list[int]",
        doc="All the inner values, row by row, in one flat list.",
        constraint_note="one nested comprehension; no `for` statement",
        constraints=(
            Forbid(("for",), because="a nested comprehension reads left to right, outer loop first",
                   hint="[value for row in rows for value in row]"),
            RequireConstruct("comprehension", because="this drill is about nesting them"),
        ),
    ),
    Method(
        display="LOOKUP",
        signature="(records: list[dict]) -> dict[str, str]",
        doc="A dict from each record's 'id' to its 'name'.",
        constraint_note="one dict comprehension; no `for` statement",
        constraints=(
            Forbid(("for",), because="building a mapping is a dict comprehension",
                   hint='{r["id"]: r["name"] for r in records}'),
            RequireConstruct("dictcomp", because="this drill is about dict comprehensions"),
        ),
    ),
    Method(
        display="RUNNING_MAX",
        signature="(items: list[int]) -> list[int]",
        doc="The largest value seen so far at each position. [] for an empty input.",
        # The counterweight drill. A unit that only ever rewards comprehensions
        # produces people who write four-clause monsters; carrying state across
        # iterations is exactly when a plain loop is the clearer tool.
        constraint_note="this one wants a plain `for` loop — carrying state is what they are good at",
        constraints=(
            RequireConstruct("for", because="state that changes as you go belongs in a real loop"),
            Forbid(("comprehension",),
                   because="a comprehension that mutates an outside variable is worse than a loop"),
        ),
    ),
    # The checkpoint. No constraint: the point is to choose the right tool yourself,
    # which is what the unit has been building towards.
    Method(
        display="REPORT",
        signature="(rows: list[dict]) -> list[str]",
        doc=(
            'One line per row, "N. name — score", one-based, ordered by score '
            "descending. Rows with a score of None are skipped."
        ),
        constraint_note="checkpoint: no constraints — pick the right tools yourself",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "For loops and comprehensions", theme="let the language iterate"),)

TAG_GLOSSARY = {
    "comprehension": "list, dict and nested comprehensions",
    "enumerate": "index and value together",
    "zip": "walking two sequences in step",
    "reversed": "iterating backwards",
    "slicing": "slice bounds and the step argument",
    "early-exit": "stopping at the first match",
    "state": "carrying a value across iterations",
    "edge-values": "empty input, one element, ties",
    "checkpoint": "the whole unit at once",
}

# ---------------------------------------------------------------------------
# cases


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(
        name, 1, [op(opname, *args, ret=ret, why=why)],
        tags=tags, visible=visible, doc=doc,
    )


CASES = [
    # SHOUT
    _c("shout_basic", "SHOUT", ["ada", "Bob"], ret=["ADA", "BOB"],
       tags=["comprehension"], visible=True, doc="Order is preserved."),
    _c("shout_empty", "SHOUT", [], ret=[], tags=["comprehension", "edge-values"]),
    _c("shout_already_upper", "SHOUT", ["OK"], ret=["OK"], tags=["comprehension"]),

    # PY_FILES
    _c("py_files_basic", "PY_FILES", ["a.py", "b.txt", "c.py"], ret=["a.py", "c.py"],
       tags=["comprehension"], visible=True, doc="Only the matches, in input order."),
    _c("py_files_none", "PY_FILES", ["a.txt"], ret=[], tags=["comprehension", "edge-values"]),
    _c("py_files_not_substring", "PY_FILES", ["py.txt", "a.pyc"], ret=[],
       tags=["comprehension", "edge-values"],
       why="'.py' must be at the END; .pyc and py.txt are not python files"),

    # NUMBERED
    _c("numbered_basic", "NUMBERED", ["first", "second"], ret=["1. first", "2. second"],
       tags=["enumerate"], visible=True, doc="Numbering starts at 1, not 0."),
    _c("numbered_empty", "NUMBERED", [], ret=[], tags=["enumerate", "edge-values"]),
    _c("numbered_ten", "NUMBERED", [str(n) for n in range(10)],
       ret=[f"{n + 1}. {n}" for n in range(10)], tags=["enumerate"]),

    # PAIR_UP
    _c("pair_up_basic", "PAIR_UP", ["ada", "bob"], [90, 80], ret=["ada: 90", "bob: 80"],
       tags=["zip"], visible=True, doc="Same position in each list."),
    _c("pair_up_stops_at_shorter", "PAIR_UP", ["a", "b", "c"], [1], ret=["a: 1"],
       tags=["zip", "edge-values"], why="zip stops when the shorter sequence runs out"),
    _c("pair_up_empty", "PAIR_UP", [], [], ret=[], tags=["zip", "edge-values"]),

    # BACKWARDS
    _c("backwards_basic", "BACKWARDS", [1, 2, 3], ret=[3, 2, 1],
       tags=["reversed"], visible=True, doc="Last to first."),
    _c("backwards_one", "BACKWARDS", [7], ret=[7], tags=["reversed", "edge-values"]),
    _c("backwards_empty", "BACKWARDS", [], ret=[], tags=["reversed", "edge-values"]),

    # EVERY_OTHER
    _c("every_other_basic", "EVERY_OTHER", [0, 1, 2, 3, 4], ret=[0, 2, 4],
       tags=["slicing"], visible=True, doc="Positions 0, 2, 4 — starting at the first."),
    _c("every_other_even_length", "EVERY_OTHER", [0, 1, 2, 3], ret=[0, 2], tags=["slicing"]),
    _c("every_other_empty", "EVERY_OTHER", [], ret=[], tags=["slicing", "edge-values"]),

    # FIRST_ADMIN
    _c("first_admin_found", "FIRST_ADMIN",
       [{"name": "a", "role": "user"}, {"name": "b", "role": "admin"},
        {"name": "c", "role": "admin"}],
       ret={"name": "b", "role": "admin"},
       tags=["early-exit"], visible=True, doc="The FIRST match, not the last."),
    _c("first_admin_missing", "FIRST_ADMIN", [{"name": "a", "role": "user"}], ret=None,
       tags=["early-exit"], visible=True, doc="None when nobody matches — not an error."),
    _c("first_admin_empty", "FIRST_ADMIN", [], ret=None, tags=["early-exit", "edge-values"]),

    # RISING
    _c("rising_basic", "RISING", [1, 3, 2], ret=[True, False],
       tags=["zip"], visible=True, doc="One result per PAIR, so one shorter than the input."),
    _c("rising_equal_is_not_rising", "RISING", [2, 2], ret=[False],
       tags=["zip", "edge-values"], why="larger means strictly larger"),
    _c("rising_one_element", "RISING", [5], ret=[], tags=["zip", "edge-values"],
       why="one element is no pairs"),
    _c("rising_empty", "RISING", [], ret=[], tags=["zip", "edge-values"]),

    # FLATTEN
    _c("flatten_basic", "FLATTEN", [[1, 2], [3]], ret=[1, 2, 3],
       tags=["comprehension"], visible=True, doc="Row by row, in order."),
    _c("flatten_inner_empty", "FLATTEN", [[], [1], []], ret=[1],
       tags=["comprehension", "edge-values"]),
    _c("flatten_no_rows", "FLATTEN", [], ret=[], tags=["comprehension", "edge-values"]),

    # LOOKUP
    _c("lookup_basic", "LOOKUP",
       [{"id": "a", "name": "Ada"}, {"id": "b", "name": "Bob"}],
       ret={"a": "Ada", "b": "Bob"},
       tags=["comprehension"], visible=True, doc="id -> name."),
    _c("lookup_later_wins", "LOOKUP",
       [{"id": "a", "name": "First"}, {"id": "a", "name": "Second"}],
       ret={"a": "Second"}, tags=["comprehension", "edge-values"],
       why="a repeated key keeps the last value, the way dict assignment does"),
    _c("lookup_empty", "LOOKUP", [], ret={}, tags=["comprehension", "edge-values"]),

    # RUNNING_MAX
    _c("running_max_basic", "RUNNING_MAX", [1, 3, 2, 5], ret=[1, 3, 3, 5],
       tags=["state"], visible=True, doc="The best seen so far, at each position."),
    _c("running_max_descending", "RUNNING_MAX", [5, 4, 3], ret=[5, 5, 5], tags=["state"]),
    _c("running_max_negatives", "RUNNING_MAX", [-5, -2, -9], ret=[-5, -2, -2],
       tags=["state", "edge-values"]),
    _c("running_max_empty", "RUNNING_MAX", [], ret=[], tags=["state", "edge-values"]),

    # REPORT — the checkpoint
    _c("report_basic", "REPORT",
       [{"name": "ada", "score": 90}, {"name": "bob", "score": 95}],
       ret=["1. bob — 95", "2. ada — 90"],
       tags=["checkpoint"], visible=True,
       doc="Highest score first, then numbered from 1."),
    _c("report_skips_none", "REPORT",
       [{"name": "ada", "score": 90}, {"name": "bob", "score": None},
        {"name": "cyd", "score": 95}],
       ret=["1. cyd — 95", "2. ada — 90"],
       tags=["checkpoint"], visible=True,
       doc="A score of None is skipped, and does not consume a number."),
    _c("report_empty", "REPORT", [], ret=[], tags=["checkpoint", "edge-values"]),
    _c("report_all_none", "REPORT", [{"name": "a", "score": None}], ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("report_zero_is_a_score", "REPORT", [{"name": "a", "score": 0}], ret=["1. a — 0"],
       tags=["checkpoint", "edge-values"],
       why="0 is a score; only None is missing"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="for_loops",
    title="1.1 For loops and comprehensions",
    blurb="Let the language do the iterating: comprehensions, enumerate, zip, reversed, slices.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("comprehension", "enumerate", "zip", "reversed", "slicing"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.1 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
