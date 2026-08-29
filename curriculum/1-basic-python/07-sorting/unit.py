"""1.7 Sorting — one sort, one compound key.

Self-contained: loaded by file path, so no package-relative imports.

This unit exists because of one mistake: sorting twice, once per field, which throws
away the first ordering. `./pfs stats` reports `ordering` and `tie-break` as recurring
failures on the industry problems, and this is where both are learned.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="ALPHABETICAL",
        signature="(names: list[str]) -> list[str]",
        doc="The names sorted, without changing the caller's list.",
        constraint_note="use sorted(), not .sort() — the input belongs to the caller",
        constraints=(
            RequireCall(("sorted",), because="sorted() returns a new list; .sort() mutates in place",
                        hint="sorted(names)"),
            ForbidCall(("sort",), because="mutating an argument surprises every caller"),
        ),
    ),
    Method(
        display="BIGGEST_FIRST",
        signature="(numbers: list[int]) -> list[int]",
        doc="Descending order.",
        constraint_note="use reverse=True; do not sort then reverse",
        constraints=(
            ForbidCall(("reverse",), because="reverse=True is one pass; sort-then-reverse is two",
                       hint="sorted(numbers, reverse=True)"),
        ),
    ),
    Method(
        display="RANKED",
        signature="(rows: list[dict]) -> list[str]",
        doc="Names by 'score' DESCENDING, ties broken by name ASCENDING.",
        # The drill this whole unit is for.
        constraint_note="ONE sorted call with a compound key; two sorts lose the first ordering",
        constraints=(
            RequireCall(("sorted",), because="two directions in one pass needs a tuple key",
                        hint='sorted(rows, key=lambda r: (-r["score"], r["name"]))'),
            ForbidCall(("reverse",),
                       because="reverse=True flips the WHOLE comparison, so it cannot do "
                               "one field down and another up"),
        ),
    ),
    Method(
        display="BY_LAST_NAME",
        signature="(names: list[str]) -> list[str]",
        doc='Full names like "Ada Lovelace" ordered by the last word.',
        constraint_note="use a key function; do not build a decorated list",
        constraints=(
            RequireCall(("sorted",), because="key= computes the ordering without rebuilding the data",
                        hint="sorted(names, key=lambda n: n.split()[-1])"),
            Forbid(("for",), because="no decorate-sort-undecorate needed; key= is that, built in"),
        ),
    ),
    Method(
        display="CASE_BLIND",
        signature="(words: list[str]) -> list[str]",
        doc="Sorted ignoring case, but the original spellings are returned.",
        constraint_note="key=str.casefold; do not lower-case the values themselves",
        constraints=(
            RequireCall(("sorted",), because="key changes the ORDERING, not the elements",
                        hint="sorted(words, key=str.casefold)"),
        ),
    ),
    Method(
        display="STABLE_GROUPS",
        signature="(rows: list[tuple[str, int]]) -> list[tuple[str, int]]",
        doc=(
            "Rows sorted by their number only. Rows with equal numbers keep their "
            "original relative order."
        ),
        constraint_note="rely on sort stability; do not add the index to the key",
        constraints=(
            RequireCall(("sorted",), because="Python's sort is stable, so equal keys keep input order",
                        hint="sorted(rows, key=lambda r: r[1])"),
            ForbidCall(("enumerate",), because="stability already guarantees this; an index tie-break is noise"),
        ),
    ),
    Method(
        display="TOP_TWO",
        signature="(numbers: list[int]) -> list[int]",
        doc="The two largest, largest first. Fewer if there are fewer.",
        constraint_note="sort descending and slice; the slice must not raise when short",
        constraints=(
            Forbid(("if",), because="a slice past the end is already safe",
                   hint="sorted(numbers, reverse=True)[:2]"),
        ),
    ),
    Method(
        display="STANDINGS",
        signature="(rows: list[dict]) -> list[str]",
        doc=(
            'Teams as "N. name (points, goal difference)" — points descending, then '
            "goal difference descending, then name ascending. Numbered from 1."
        ),
        constraint_note="checkpoint: no constraints — three tie-breaks, one sort",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Sorting", theme="one sort, one compound key"),)

TAG_GLOSSARY = {
    "ordering": "ascending, descending and the key function",
    "tie-break": "resolving equal keys",
    "stability": "equal keys keeping input order",
    "purity": "not mutating the caller's list",
    "top-n": "taking the first few",
    "edge-values": "empty, one element, all equal",
    "checkpoint": "the whole unit at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("alphabetical_basic", "ALPHABETICAL", ["c", "a", "b"], ret=["a", "b", "c"],
       tags=["ordering"], visible=True, doc="Plain ascending order."),
    # The purity check: two calls on the same list. .sort() passes the first and
    # fails the second.
    case("alphabetical_leaves_input_alone", 1,
         [op("ALPHABETICAL", ["c", "a"], ret=["a", "c"]),
          op("ALPHABETICAL", ["c", "a"], ret=["a", "c"])],
         tags=["purity"], visible=True,
         doc="The caller's list must come back untouched, so calling twice is identical."),
    _c("alphabetical_empty", "ALPHABETICAL", [], ret=[], tags=["ordering", "edge-values"]),

    _c("biggest_first_basic", "BIGGEST_FIRST", [1, 3, 2], ret=[3, 2, 1],
       tags=["ordering"], visible=True, doc="Descending."),
    _c("biggest_first_equal", "BIGGEST_FIRST", [2, 2], ret=[2, 2], tags=["ordering", "edge-values"]),
    _c("biggest_first_empty", "BIGGEST_FIRST", [], ret=[], tags=["ordering", "edge-values"]),

    _c("ranked_basic", "RANKED",
       [{"name": "ada", "score": 90}, {"name": "bob", "score": 95}],
       ret=["bob", "ada"], tags=["ordering"], visible=True, doc="Highest score first."),
    _c("ranked_ties_go_alphabetical", "RANKED",
       [{"name": "cyd", "score": 90}, {"name": "ada", "score": 90},
        {"name": "bob", "score": 95}],
       ret=["bob", "ada", "cyd"], tags=["tie-break"], visible=True,
       doc="Score DOWN but name UP — reverse=True cannot express this, a negated key can."),
    _c("ranked_all_tied", "RANKED",
       [{"name": "b", "score": 1}, {"name": "a", "score": 1}],
       ret=["a", "b"], tags=["tie-break", "edge-values"]),
    _c("ranked_empty", "RANKED", [], ret=[], tags=["ordering", "edge-values"]),

    _c("by_last_name_basic", "BY_LAST_NAME", ["Bob Ray", "Ada Lovelace"],
       ret=["Ada Lovelace", "Bob Ray"], tags=["ordering"], visible=True,
       doc="Ordered by the LAST word: Lovelace before Ray, so the input order flips."),
    _c("by_last_name_three", "BY_LAST_NAME", ["Zoe Adams", "Ada Lovelace", "Bob Ray"],
       ret=["Zoe Adams", "Ada Lovelace", "Bob Ray"], tags=["ordering"]),
    _c("by_last_name_single_word", "BY_LAST_NAME", ["Cher", "Ada Lovelace"],
       ret=["Cher", "Ada Lovelace"], tags=["ordering", "edge-values"],
       why="a one-word name is its own last word"),

    _c("case_blind_basic", "CASE_BLIND", ["b", "A", "c"], ret=["A", "b", "c"],
       tags=["ordering"], visible=True,
       doc="Case ignored for ordering; the original spelling is returned."),
    _c("case_blind_keeps_spelling", "CASE_BLIND", ["Beta", "alpha"],
       ret=["alpha", "Beta"], tags=["ordering"], visible=True,
       doc='"Beta" comes back capitalised — the key affects order, not content.'),
    _c("case_blind_empty", "CASE_BLIND", [], ret=[], tags=["ordering", "edge-values"]),

    _c("stable_groups_basic", "STABLE_GROUPS", [("a", 2), ("b", 1), ("c", 2)],
       ret=[("b", 1), ("a", 2), ("c", 2)], tags=["stability"], visible=True,
       doc='"a" stays before "c" because Python\'s sort is stable.'),
    _c("stable_groups_all_equal", "STABLE_GROUPS", [("x", 1), ("y", 1), ("z", 1)],
       ret=[("x", 1), ("y", 1), ("z", 1)], tags=["stability"], visible=True,
       doc="All keys equal means the input order is preserved exactly."),
    _c("stable_groups_empty", "STABLE_GROUPS", [], ret=[], tags=["stability", "edge-values"]),

    _c("top_two_basic", "TOP_TWO", [5, 1, 9, 3], ret=[9, 5], tags=["top-n"], visible=True,
       doc="Largest first."),
    _c("top_two_one", "TOP_TWO", [4], ret=[4], tags=["top-n", "edge-values"], visible=True,
       doc="A slice past the end returns what there is — no guard needed."),
    _c("top_two_empty", "TOP_TWO", [], ret=[], tags=["top-n", "edge-values"]),
    _c("top_two_duplicates", "TOP_TWO", [7, 7, 1], ret=[7, 7], tags=["top-n", "edge-values"]),

    _c("standings_basic", "STANDINGS",
       [{"name": "ada", "points": 6, "gd": 2}, {"name": "bob", "points": 9, "gd": 1}],
       ret=["1. bob (9, 1)", "2. ada (6, 2)"], tags=["checkpoint"], visible=True,
       doc="Points first."),
    _c("standings_gd_breaks_tie", "STANDINGS",
       [{"name": "ada", "points": 6, "gd": 2}, {"name": "bob", "points": 6, "gd": 5}],
       ret=["1. bob (6, 5)", "2. ada (6, 2)"], tags=["checkpoint"], visible=True,
       doc="Equal points: better goal difference wins."),
    _c("standings_name_breaks_tie", "STANDINGS",
       [{"name": "cyd", "points": 6, "gd": 2}, {"name": "ada", "points": 6, "gd": 2}],
       ret=["1. ada (6, 2)", "2. cyd (6, 2)"], tags=["checkpoint"], visible=True,
       doc="Everything equal: name ascending. Three tie-breaks, one sort."),
    _c("standings_empty", "STANDINGS", [], ret=[], tags=["checkpoint", "edge-values"]),
    _c("standings_negative_gd", "STANDINGS",
       [{"name": "ada", "points": 3, "gd": -4}, {"name": "bob", "points": 3, "gd": -1}],
       ret=["1. bob (3, -1)", "2. ada (3, -4)"], tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="sorting",
    title="1.7 Sorting",
    blurb="One sorted call, one compound key: descending fields, tie-breaks and stability.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("ordering", "tie-break", "stability"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.7 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
