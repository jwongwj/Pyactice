"""1.5 Unpacking and assignment — the syntax that removes index arithmetic.

Self-contained: loaded by file path, so no package-relative imports.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireConstruct
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="SWAPPED",
        signature="(a: int, b: int) -> tuple[int, int]",
        doc="(b, a).",
        constraint_note="one tuple assignment; no temporary variable",
        constraints=(
            Forbid(("subscript",), because="tuple assignment swaps without a third name",
                   hint="a, b = b, a"),
        ),
    ),
    Method(
        display="FULL_NAMES",
        signature="(people: list[tuple[str, str]]) -> list[str]",
        doc='"First Last" from each (first, last) pair.',
        # Originally this asked for initials, which needs `first[0]` -- a subscript. The
        # constraint forbids subscripts to force header unpacking, and cannot tell
        # indexing a tuple from indexing a string, so it contradicted its own answer.
        # Better to pick a task the constraint can actually be true for.
        constraint_note="unpack in the comprehension header; no indexing at all",
        constraints=(
            Forbid(("subscript",), because="unpacking in the header names the parts",
                   hint='[f"{first} {last}" for first, last in people]'),
        ),
    ),
    Method(
        display="HEAD_TAIL",
        signature="(items: list[int]) -> tuple[int | None, list[int]]",
        doc="(first item, the rest). (None, []) for an empty list.",
        constraint_note="split it with star unpacking, not indexing or slicing",
        constraints=(
            Forbid(("subscript",), because="star unpacking splits a sequence without slice bounds",
                   hint="first, *rest = items  (guard the empty case first)"),
        ),
    ),
    Method(
        display="LAST_TWO",
        signature="(items: list[int]) -> list[int]",
        doc="The last two items, in order. Fewer if the list is shorter.",
        constraint_note="one slice; no loop",
        constraints=(
            Forbid(("for", "while", "comprehension"),
                   because="a negative slice bound counts from the end and is safe when short",
                   hint="items[-2:]"),
        ),
    ),
    Method(
        display="MIDDLE",
        signature="(items: list[int]) -> list[int]",
        doc="Everything except the first and last item.",
        constraint_note="use *middle unpacking, not slice arithmetic",
        constraints=(
            ForbidCall(("len",), because="*middle expresses this without computing indices",
                       hint="first, *middle, last = items"),
        ),
    ),
    Method(
        display="COORDS",
        signature="(points: list[tuple]) -> list[str]",
        doc='"x,y" from each (x, y, label) triple — the label is ignored.',
        constraint_note="unpack with _ for the part you do not want",
        constraints=(
            Forbid(("subscript",), because="_ documents that a value is deliberately unused",
                   hint="[f\"{x},{y}\" for x, y, _ in points]"),
        ),
    ),
    Method(
        display="COLUMNS",
        signature="(rows: list[tuple]) -> tuple[list, list]",
        doc="Two lists: all the first elements, then all the second elements.",
        constraint_note="use zip(*rows) — the star unpacks the rows as arguments",
        constraints=(
            RequireConstruct("comprehension", because="zip(*rows) returns tuples; the result wants lists",
                             hint="[list(col) for col in zip(*rows)] — mind the empty case"),
            Forbid(("for",), because="zip(*rows) is the transpose"),
        ),
    ),
    Method(
        display="RESHAPE",
        signature="(pairs: list[tuple[str, int]]) -> dict[str, int]",
        doc="A dict from the pairs.",
        constraint_note="dict() takes an iterable of pairs directly; no loop",
        constraints=(
            Forbid(("for", "comprehension"), because="dict(pairs) already does this",
                   hint="dict(pairs)"),
        ),
    ),
    Method(
        display="REGROUP",
        signature="(rows: list[tuple]) -> list[str]",
        doc=(
            'Each (name, scores) row as "name: total" where total is the sum of that '
            "row's scores. Rows with no scores are skipped."
        ),
        constraint_note="checkpoint: no constraints — pick the right tools yourself",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Unpacking and assignment", theme="name the parts instead of indexing them"),)

TAG_GLOSSARY = {
    "swap": "tuple assignment",
    "star": "star unpacking",
    "slicing": "slice bounds from the end",
    "ignore": "the _ convention",
    "transpose": "zip(*rows)",
    "edge-values": "empty, one element, short input",
    "checkpoint": "the whole unit at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("swapped_basic", "SWAPPED", 1, 2, ret=(2, 1), tags=["swap"], visible=True,
       doc="No temporary variable needed."),
    _c("swapped_same", "SWAPPED", 5, 5, ret=(5, 5), tags=["swap", "edge-values"]),
    _c("swapped_negative", "SWAPPED", -1, 3, ret=(3, -1), tags=["swap"]),

    _c("full_names_basic", "FULL_NAMES", [("Ada", "Lovelace"), ("Bob", "Ray")],
       ret=["Ada Lovelace", "Bob Ray"], tags=["star"], visible=True,
       doc="The two parts, named in the comprehension header."),
    _c("full_names_one", "FULL_NAMES", [("Cyd", "Zed")], ret=["Cyd Zed"], tags=["star"]),
    _c("full_names_empty", "FULL_NAMES", [], ret=[], tags=["star", "edge-values"]),

    _c("head_tail_basic", "HEAD_TAIL", [1, 2, 3], ret=(1, [2, 3]), tags=["star"], visible=True,
       doc="The rest is always a list, even when it has one item."),
    _c("head_tail_one", "HEAD_TAIL", [9], ret=(9, []), tags=["star", "edge-values"], visible=True,
       doc="One item: the rest is an empty list, not None."),
    _c("head_tail_empty", "HEAD_TAIL", [], ret=(None, []), tags=["star", "edge-values"]),

    _c("last_two_basic", "LAST_TWO", [1, 2, 3, 4], ret=[3, 4], tags=["slicing"], visible=True,
       doc="In their original order."),
    _c("last_two_short", "LAST_TWO", [7], ret=[7], tags=["slicing", "edge-values"], visible=True,
       doc="A negative slice bound does not raise when the list is shorter."),
    _c("last_two_empty", "LAST_TWO", [], ret=[], tags=["slicing", "edge-values"]),

    _c("middle_basic", "MIDDLE", [1, 2, 3, 4], ret=[2, 3], tags=["star"], visible=True,
       doc="First and last dropped."),
    _c("middle_two", "MIDDLE", [1, 2], ret=[], tags=["star", "edge-values"]),
    _c("middle_one", "MIDDLE", [1], ret=[], tags=["star", "edge-values"],
       why="first and last are the same item, so nothing is in the middle"),

    _c("coords_basic", "COORDS", [(1, 2, "a"), (3, 4, "b")], ret=["1,2", "3,4"],
       tags=["ignore"], visible=True, doc="The third element is ignored."),
    _c("coords_one", "COORDS", [(0, 0, "origin")], ret=["0,0"], tags=["ignore"]),
    _c("coords_empty", "COORDS", [], ret=[], tags=["ignore", "edge-values"]),

    _c("columns_basic", "COLUMNS", [("a", 1), ("b", 2)], ret=(["a", "b"], [1, 2]),
       tags=["transpose"], visible=True, doc="zip(*rows) transposes."),
    _c("columns_one_row", "COLUMNS", [("a", 1)], ret=(["a"], [1]), tags=["transpose"]),
    _c("columns_empty", "COLUMNS", [], ret=([], []), tags=["transpose", "edge-values"],
       visible=True, doc="zip(*[]) yields nothing, so this needs handling."),

    _c("reshape_basic", "RESHAPE", [("a", 1), ("b", 2)], ret={"a": 1, "b": 2},
       tags=["transpose"], visible=True, doc="dict() takes pairs directly."),
    _c("reshape_duplicate", "RESHAPE", [("a", 1), ("a", 2)], ret={"a": 2},
       tags=["transpose", "edge-values"], why="a later pair wins, as with dict assignment"),
    _c("reshape_empty", "RESHAPE", [], ret={}, tags=["transpose", "edge-values"]),

    _c("regroup_basic", "REGROUP", [("ada", [1, 2]), ("bob", [10])],
       ret=["ada: 3", "bob: 10"], tags=["checkpoint"], visible=True,
       doc="Sum of each row's scores."),
    _c("regroup_skips_empty", "REGROUP", [("ada", []), ("bob", [5])], ret=["bob: 5"],
       tags=["checkpoint"], visible=True, doc="A row with no scores is skipped."),
    _c("regroup_none", "REGROUP", [], ret=[], tags=["checkpoint", "edge-values"]),
    _c("regroup_zero_score", "REGROUP", [("ada", [0])], ret=["ada: 0"],
       tags=["checkpoint", "edge-values"], why="a score of 0 is a score; only no scores skips"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="unpacking",
    title="1.5 Unpacking and assignment",
    blurb="Tuple assignment, star unpacking, the _ convention and zip(*rows).",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("star", "transpose", "slicing"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.5 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
