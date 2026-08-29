"""2.2 Tuple — immutability, hashability, and the compound sort key.

Self-contained: loaded by file path, so no package-relative imports.

A tuple is not "a list you cannot change". The difference that earns its place is that it
is hashable, which is what lets it be a dict key or a set member -- and that is what most
of this unit is about.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="MIN_MAX",
        signature="(items: list[int]) -> tuple[int | None, int | None]",
        doc="(smallest, largest). (None, None) when there is nothing.",
        constraint_note="return one tuple; no loop",
        constraints=(
            Forbid(("for", "while"),
                   because="min() and max() are the answer, and a tuple returns both "
                           "without an out-parameter or a wrapper class",
                   hint="guard the empty case, then `return min(items), max(items)`"),
        ),
    ),
    Method(
        display="VISITS",
        signature="(entries: list[tuple[str, str]]) -> dict[tuple[str, str], int]",
        doc="How many times each (city, day) pair appears.",
        # The lesson is that the pair itself is the key. A list cannot do this job.
        constraint_note="key the dict on the pair itself; do not join it into a string",
        constraints=(
            ForbidCall(("join", "format", "str"),
                       because="a tuple is hashable, so it can BE the key -- flattening it "
                               "to \"city|day\" invents a separator that can appear in the data",
                       hint="counts[entry] = counts.get(entry, 0) + 1"),
        ),
    ),
    Method(
        display="BY_DEPT_THEN_PAY",
        signature="(rows: list[tuple[str, str, int]]) -> list[str]",
        doc="Names, ordered by department ascending then pay descending.",
        constraint_note="one sort with a tuple key; not two passes",
        constraints=(
            Forbid(("for", "while"),
                   because="a tuple key sorts on several fields at once, and negating the "
                           "number reverses that field alone",
                   hint="sorted(rows, key=lambda r: (r[1], -r[2])) -- r is (name, dept, pay)"),
        ),
    ),
    Method(
        display="PEAK",
        signature="(readings: list[tuple[str, int]]) -> tuple[str, int]",
        doc='The highest reading as a named record with fields `label` and `value`. '
            'Ties go to the label that sorts first. ("", 0) when there are none.',
        constraint_note="build it with collections.namedtuple, not a plain tuple",
        constraints=(
            RequireCall(("namedtuple",),
                        because="a bare tuple makes the caller remember that [1] is the "
                                "value; a named one says so, and still compares equal to "
                                "the plain tuple, so nothing downstream has to change",
                        hint="Reading = namedtuple('Reading', 'label value')"),
        ),
    ),
    Method(
        display="UNIQUE_PAIRS",
        signature="(pairs: list[tuple[int, int]]) -> list[tuple[int, int]]",
        doc="Duplicate pairs removed, first occurrence kept, original order.",
        constraint_note="use a set of the pairs themselves",
        constraints=(
            ForbidCall(("count", "index"),
                       because="pairs are hashable, so set membership is O(1) -- scanning "
                               "the output list for each pair is the quadratic version",
                       hint="a `seen` set of tuples, exactly as for ints"),
        ),
    ),
    Method(
        display="LEADERBOARD",
        signature="(games: list[tuple[str, str, int]]) -> list[str]",
        doc='"name: total" per player, totals summed across games, highest total first, '
            'ties by name ascending. Players with no games do not appear.',
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Tuple", theme="hashable, so it can be a key"),)

TAG_GLOSSARY = {
    "several-returns": "returning more than one value at once",
    "as-key": "a tuple used as a dict key or set member",
    "ordering": "sort keys and tie-breaks",
    "named": "namedtuple and readable field access",
    "dedupe": "removing repeats",
    "edge-values": "empty inputs, single items, zero, ties",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("min_max_basic", "MIN_MAX", [3, 1, 2], ret=(1, 3),
       tags=["several-returns"], visible=True, doc="Smallest first."),
    _c("min_max_single", "MIN_MAX", [7], ret=(7, 7), tags=["several-returns", "edge-values"],
       why="one item is both the smallest and the largest"),
    _c("min_max_empty", "MIN_MAX", [], ret=(None, None),
       tags=["several-returns", "edge-values"], visible=True,
       doc="Nothing to compare: both halves are None, and min() would raise."),
    _c("min_max_negative", "MIN_MAX", [-5, -1], ret=(-5, -1), tags=["several-returns"]),

    _c("visits_basic", "VISITS", [("rome", "mon"), ("rome", "mon"), ("rome", "tue")],
       ret={("rome", "mon"): 2, ("rome", "tue"): 1}, tags=["as-key"], visible=True,
       doc="The pair itself is the key."),
    _c("visits_separator_in_data", "VISITS", [("a|b", "mon"), ("a", "b|mon")],
       ret={("a|b", "mon"): 1, ("a", "b|mon"): 1}, tags=["as-key", "edge-values"],
       visible=True,
       doc="Both pairs would collide into \"a|b|mon\" if the key were a joined string. "
           "As tuples they stay distinct."),
    _c("visits_empty", "VISITS", [], ret={}, tags=["as-key", "edge-values"]),

    _c("by_dept_basic", "BY_DEPT_THEN_PAY",
       [("ada", "eng", 100), ("bob", "art", 90), ("cyd", "eng", 120)],
       ret=["bob", "cyd", "ada"], tags=["ordering"], visible=True,
       doc="Department ascending, then pay descending inside it."),
    _c("by_dept_tie_on_pay", "BY_DEPT_THEN_PAY",
       [("zed", "eng", 100), ("ada", "eng", 100)], ret=["zed", "ada"],
       tags=["ordering", "edge-values"], visible=True,
       doc="Equal pay in the same department keeps the input order -- Python's sort is "
           "stable, and nothing here asks for a third key."),
    _c("by_dept_empty", "BY_DEPT_THEN_PAY", [], ret=[], tags=["ordering", "edge-values"]),
    _c("by_dept_one_dept", "BY_DEPT_THEN_PAY",
       [("ada", "eng", 10), ("bob", "eng", 20)], ret=["bob", "ada"], tags=["ordering"],
       why="within one department it is purely pay descending"),

    _c("peak_basic", "PEAK", [("a", 5), ("b", 9)], ret=("b", 9),
       tags=["named"], visible=True,
       doc="A namedtuple compares equal to the plain tuple, so this is what it looks like."),
    _c("peak_tie", "PEAK", [("z", 9), ("a", 9)], ret=("a", 9),
       tags=["named", "edge-values"], visible=True,
       doc="Equal values: the label that sorts first wins."),
    _c("peak_empty", "PEAK", [], ret=("", 0), tags=["named", "edge-values"]),
    _c("peak_negative", "PEAK", [("a", -5), ("b", -1)], ret=("b", -1), tags=["named"],
       why="the highest of several negatives is still the highest, not the one nearest zero"),

    _c("unique_pairs_basic", "UNIQUE_PAIRS", [(1, 2), (1, 2), (2, 1)],
       ret=[(1, 2), (2, 1)], tags=["dedupe", "as-key"], visible=True,
       doc="(1, 2) and (2, 1) are different pairs."),
    _c("unique_pairs_none", "UNIQUE_PAIRS", [(1, 1), (2, 2)], ret=[(1, 1), (2, 2)],
       tags=["dedupe"], why="nothing to remove must not reorder anything either"),
    _c("unique_pairs_empty", "UNIQUE_PAIRS", [], ret=[], tags=["dedupe", "edge-values"]),
    _c("unique_pairs_all_same", "UNIQUE_PAIRS", [(0, 0), (0, 0)], ret=[(0, 0)],
       tags=["dedupe", "edge-values"]),

    _c("leaderboard_basic", "LEADERBOARD",
       [("ada", "g1", 3), ("bob", "g1", 5), ("ada", "g2", 4)],
       ret=["ada: 7", "bob: 5"], tags=["checkpoint"], visible=True,
       doc="Totals summed per player, highest first."),
    _c("leaderboard_tie", "LEADERBOARD", [("zed", "g1", 5), ("ada", "g1", 5)],
       ret=["ada: 5", "zed: 5"], tags=["checkpoint", "ordering"], visible=True,
       doc="Equal totals are ordered by name ascending."),
    _c("leaderboard_empty", "LEADERBOARD", [], ret=[], tags=["checkpoint", "edge-values"]),
    _c("leaderboard_zero_total", "LEADERBOARD", [("ada", "g1", 0)], ret=["ada: 0"],
       tags=["checkpoint", "edge-values"],
       why="a total of 0 is a total; only having no games at all keeps a player out"),
    _c("leaderboard_negative", "LEADERBOARD", [("ada", "g1", 5), ("ada", "g2", -2)],
       ret=["ada: 3"], tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="tuples",
    title="2.2 Tuple",
    blurb="Several returns, the tuple as a dict key, compound sort keys and namedtuple.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="easy",
    topics=("as-key", "ordering", "named"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.2 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
