"""2.4 Set — O(1) membership, and the price you pay for it.

Self-contained: loaded by file path, so no package-relative imports.

The price is order. Half of this unit is the set operations; the other half is knowing
when you needed order back, and what to reach for instead.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall, RequireConstruct
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="UNIQUE_SORTED",
        signature="(items: list[int]) -> list[int]",
        doc="The distinct items, ascending.",
        constraint_note="a set, then sorted; no loop",
        constraints=(
            Forbid(("for", "while"),
                   because="a set discards duplicates and sorted() puts the order back, "
                           "which is only safe because you are choosing the order here",
                   hint="sorted(set(items))"),
        ),
    ),
    Method(
        display="UNIQUE_STABLE",
        signature="(items: list[int]) -> list[int]",
        doc="The distinct items in the order they first appeared.",
        constraint_note="dict.fromkeys keeps insertion order; a set does not",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="a set loses the order and sorting invents a new one -- "
                               "neither is 'the order they first appeared'",
                       hint="list(dict.fromkeys(items))"),
        ),
    ),
    Method(
        display="COMMON",
        signature="(left: list[int], right: list[int]) -> list[int]",
        doc="Items in both, ascending, without duplicates.",
        constraint_note="set intersection; no nested loop and no `in` against a list",
        constraints=(
            Forbid(("for", "while"),
                   because="`x in list` is O(n), so a loop over one list testing the other "
                           "is quadratic; intersection is linear",
                   hint="sorted(set(left) & set(right))"),
        ),
    ),
    Method(
        display="ONLY_IN_FIRST",
        signature="(left: list[int], right: list[int]) -> list[int]",
        doc="Items in `left` but not in `right`, ascending, without duplicates.",
        constraint_note="set difference; mind that it is not symmetric",
        constraints=(
            Forbid(("for", "while"),
                   because="difference is one operator, and writing it out invites doing it "
                           "the wrong way round",
                   hint="sorted(set(left) - set(right))"),
        ),
    ),
    Method(
        display="IN_ALL_THREE",
        signature="(a: list[int], b: list[int], c: list[int]) -> list[int]",
        doc="Items present in all three, ascending, without duplicates.",
        constraint_note="one intersection across all three",
        constraints=(
            Forbid(("for", "while"),
                   because="intersection takes several arguments, so three collections need "
                           "no more code than two",
                   hint="sorted(set(a).intersection(b, c))"),
        ),
    ),
    Method(
        display="TAG_GROUPS",
        signature="(rows: list[tuple[str, list[str]]]) -> dict[frozenset[str], list[str]]",
        doc="Names grouped by their exact set of tags, regardless of the order the tags "
            "were listed in. Names stay in input order.",
        constraint_note="a frozenset is hashable, so it can be the key; a set is not",
        constraints=(
            RequireCall(("frozenset",),
                        because="two rows with the same tags in a different order belong "
                                "together, and a plain set cannot be a dict key at all",
                        hint="key = frozenset(tags), then group under it"),
        ),
    ),
    Method(
        display="OVERLAP_REPORT",
        signature="(groups: dict[str, list[str]]) -> list[str]",
        doc='"a+b: n" for every pair of group names sharing at least one member, where n '
            'is how many they share. Pairs are named in alphabetical order and the list is '
            'ordered by n descending, then by the pair name ascending.',
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Set", theme="O(1) membership, at the cost of order"),)

TAG_GLOSSARY = {
    "dedupe": "removing repeats",
    "order-lost": "where a set discards the order and what to use instead",
    "membership": "O(1) containment versus a list scan",
    "algebra": "union, intersection and difference",
    "as-key": "a frozenset used as a dict key",
    "edge-values": "empty inputs, disjoint inputs, single items",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("unique_sorted_basic", "UNIQUE_SORTED", [3, 1, 3, 2], ret=[1, 2, 3],
       tags=["dedupe"], visible=True, doc="Distinct and ascending."),
    _c("unique_sorted_already", "UNIQUE_SORTED", [1, 2], ret=[1, 2], tags=["dedupe"]),
    _c("unique_sorted_empty", "UNIQUE_SORTED", [], ret=[], tags=["dedupe", "edge-values"]),
    _c("unique_sorted_negative", "UNIQUE_SORTED", [0, -1, -1], ret=[-1, 0],
       tags=["dedupe", "edge-values"]),

    _c("unique_stable_basic", "UNIQUE_STABLE", [3, 1, 3, 2], ret=[3, 1, 2],
       tags=["dedupe", "order-lost"], visible=True,
       doc="First-seen order, which is NOT sorted order -- 3 came first."),
    _c("unique_stable_descending_input", "UNIQUE_STABLE", [5, 4, 3], ret=[5, 4, 3],
       tags=["order-lost"], visible=True,
       doc="Nothing to remove, and nothing to reorder either. `sorted(set(...))` would "
           "return [3, 4, 5] and be wrong."),
    _c("unique_stable_empty", "UNIQUE_STABLE", [], ret=[],
       tags=["dedupe", "edge-values"]),
    _c("unique_stable_all_same", "UNIQUE_STABLE", [7, 7], ret=[7],
       tags=["dedupe", "edge-values"]),

    _c("common_basic", "COMMON", [1, 2, 3], [2, 3, 4], ret=[2, 3],
       tags=["algebra", "membership"], visible=True, doc="In both."),
    _c("common_disjoint", "COMMON", [1], [2], ret=[],
       tags=["algebra", "edge-values"], visible=True, doc="Nothing in both."),
    _c("common_duplicates", "COMMON", [2, 2], [2], ret=[2],
       tags=["algebra", "edge-values"],
       why="a repeated item shared once is still reported once"),
    _c("common_empty", "COMMON", [], [1], ret=[], tags=["algebra", "edge-values"]),

    _c("only_in_first_basic", "ONLY_IN_FIRST", [1, 2, 3], [2], ret=[1, 3],
       tags=["algebra"], visible=True, doc="In left, not in right."),
    _c("only_in_first_not_symmetric", "ONLY_IN_FIRST", [1], [1, 2], ret=[],
       tags=["algebra", "edge-values"], visible=True,
       doc="Right has an extra item, but this asks only about left -- so the answer is "
           "empty. Doing the subtraction the other way round would give [2]."),
    _c("only_in_first_all", "ONLY_IN_FIRST", [1, 2], [], ret=[1, 2], tags=["algebra"]),
    _c("only_in_first_empty", "ONLY_IN_FIRST", [], [1], ret=[],
       tags=["algebra", "edge-values"]),

    _c("in_all_three_basic", "IN_ALL_THREE", [1, 2, 3], [2, 3], [3], ret=[3],
       tags=["algebra"], visible=True, doc="Only 3 is in all three."),
    _c("in_all_three_pairwise_only", "IN_ALL_THREE", [1, 2], [2, 3], [3, 1], ret=[],
       tags=["algebra", "edge-values"], visible=True,
       doc="Every pair shares something, but nothing is in all three. Intersecting only "
           "the first two would wrongly give [2]."),
    _c("in_all_three_identical", "IN_ALL_THREE", [1], [1], [1], ret=[1], tags=["algebra"]),
    _c("in_all_three_one_empty", "IN_ALL_THREE", [1], [1], [], ret=[],
       tags=["algebra", "edge-values"]),

    _c("tag_groups_basic", "TAG_GROUPS", [("ada", ["x", "y"]), ("bob", ["y", "x"])],
       ret={frozenset({"x", "y"}): ["ada", "bob"]}, tags=["as-key"], visible=True,
       doc="Same tags listed in a different order is the same group."),
    _c("tag_groups_distinct", "TAG_GROUPS", [("ada", ["x"]), ("bob", ["y"])],
       ret={frozenset({"x"}): ["ada"], frozenset({"y"}): ["bob"]}, tags=["as-key"]),
    _c("tag_groups_empty_tags", "TAG_GROUPS", [("ada", [])],
       ret={frozenset(): ["ada"]}, tags=["as-key", "edge-values"], visible=True,
       doc="No tags is a group of its own, keyed by the empty frozenset."),
    _c("tag_groups_repeated_tag", "TAG_GROUPS", [("ada", ["x", "x"]), ("bob", ["x"])],
       ret={frozenset({"x"}): ["ada", "bob"]}, tags=["as-key", "edge-values"],
       why="a set collapses the repeat, so ['x','x'] and ['x'] are the same group"),
    _c("tag_groups_empty", "TAG_GROUPS", [], ret={}, tags=["as-key", "edge-values"]),

    _c("overlap_basic", "OVERLAP_REPORT", {"a": ["1", "2"], "b": ["2", "3"]},
       ret=["a+b: 1"], tags=["checkpoint"], visible=True,
       doc="One shared member, and the pair is named alphabetically."),
    _c("overlap_ordering", "OVERLAP_REPORT",
       {"a": ["1", "2"], "b": ["1", "2"], "c": ["2"]},
       ret=["a+b: 2", "a+c: 1", "b+c: 1"], tags=["checkpoint"], visible=True,
       doc="Ordered by count descending, then by pair name ascending."),
    # Every other case here happens to list its groups alphabetically, which hides the
    # bug this catches: iterating `groups` in insertion order instead of sorted order
    # names the pair "c+a" and lists it first. Found by tools/drill_mutation.py -- not
    # from a mutant it killed, but from noticing that nothing tested the ordering
    # independently of the generation order.
    _c("overlap_unsorted_input", "OVERLAP_REPORT", {"c": ["1"], "a": ["1"], "b": ["1"]},
       ret=["a+b: 1", "a+c: 1", "b+c: 1"], tags=["checkpoint", "edge-values"],
       visible=True,
       doc="The groups are given as c, a, b. Both halves of each pair name and the list "
           "itself are alphabetical regardless of the order they arrived in."),
    _c("overlap_none", "OVERLAP_REPORT", {"a": ["1"], "b": ["2"]}, ret=[],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Groups sharing nothing are not reported at all."),
    _c("overlap_single_group", "OVERLAP_REPORT", {"a": ["1"]}, ret=[],
       tags=["checkpoint", "edge-values"], why="one group forms no pair with itself"),
    _c("overlap_empty", "OVERLAP_REPORT", {}, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("overlap_duplicate_members", "OVERLAP_REPORT",
       {"a": ["1", "1"], "b": ["1"]}, ret=["a+b: 1"],
       tags=["checkpoint", "edge-values"],
       why="'1' is shared once however many times it is listed"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="sets",
    title="2.4 Set",
    blurb="Dedupe with and without order, the set algebra, and frozenset as a key.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="easy",
    topics=("algebra", "membership", "as-key"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.4 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
