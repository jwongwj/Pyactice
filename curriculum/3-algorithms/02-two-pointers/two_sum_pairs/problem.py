"""Pair sums — the first `function`-kind problem, and the proof of that seam.

Deliberately chosen to be the easiest interesting thing in the category: everybody
recognises two-sum, so any failure here is the harness's fault and not the problem's.
It still carries the three traps that make the genre worth practising -- duplicate
values, a target reachable only by using one element twice (which is not allowed),
and the ordering of the returned pairs.
"""

from __future__ import annotations

from harness.model import KIND_FUNCTION, Level, Method, Problem, case, op


METHODS = (
    Method(
        display="PAIR_SUMS",
        # No `self`: a function problem's signature is the function's own.
        signature="(numbers: list[int], target: int) -> list[list[int]]",
        level=1,
        doc=(
            "Every pair of values from numbers that sums to target, each pair sorted "
            "ascending, the list of pairs sorted, no duplicates."
        ),
    ),
)

LEVELS = (Level(1, "Pair sums", theme="hash set vs nested loop"),)

TAG_GLOSSARY = {
    "basics": "the ordinary case with one or more pairs",
    "empty": "no input, or no pair that sums to the target",
    "duplicates": "repeated values in the input",
    "same-element": "the target is twice one value",
    "ordering": "the order of the pairs and of the values inside a pair",
    "negatives": "negative numbers and zero",
    "scale": "an input large enough to punish an O(n^2) scan",
}

# ---------------------------------------------------------------------------
# cases (inline: a path-loaded curriculum module has no package to import from)


LEVEL_1 = [
    case(
        "basic_one_pair",
        1,
        [op("PAIR_SUMS", [1, 2, 3, 4], 5, ret=[[1, 4], [2, 3]])],
        tags=["basics", "ordering"],
        visible=True,
        doc="Each pair is sorted ascending, and the pairs come back sorted.",
    ),
    case(
        "no_pair_is_empty_not_none",
        1,
        [op("PAIR_SUMS", [1, 2, 3], 100, ret=[])],
        tags=["empty"],
        visible=True,
        doc="No pair means an empty list.",
    ),
    case(
        "an_element_cannot_pair_with_itself",
        1,
        # [3, 1, 4]: no two DIFFERENT elements sum to 6, so the only candidate is
        # 3 + 3, which needs the single 3 twice. An earlier draft used [3, 1, 5],
        # where 1 + 5 = 6 is a real pair -- the differential gate caught it.
        [op("PAIR_SUMS", [3, 1, 4], 6, ret=[])],
        tags=["same-element"],
        visible=True,
        doc="3 + 3 = 6 but there is only one 3, and a value cannot use itself twice.",
    ),
    case(
        "a_repeated_value_can_pair_with_its_twin",
        1,
        [op("PAIR_SUMS", [3, 3, 1], 6, ret=[[3, 3]])],
        tags=["duplicates", "same-element"],
        visible=True,
        doc="Two separate 3s are two elements, so they do pair.",
    ),
    case(
        "each_distinct_pair_appears_once",
        1,
        [op("PAIR_SUMS", [1, 1, 4, 4, 4], 5, ret=[[1, 4]])],
        tags=["duplicates"],
        visible=True,
        doc="Pairs are distinct by value, however many ways they can be formed.",
    ),
    case(
        "empty_input",
        1,
        [op("PAIR_SUMS", [], 5, ret=[])],
        tags=["empty"],
    ),
    case(
        "single_element",
        1,
        [op("PAIR_SUMS", [5], 5, ret=[])],
        tags=["empty"],
    ),
    case(
        "negatives_and_zero",
        1,
        [op("PAIR_SUMS", [-3, 0, 3, 5, -5], 0, ret=[[-5, 5], [-3, 3]])],
        tags=["negatives", "ordering"],
    ),
    case(
        "zero_target_needs_two_zeroes",
        1,
        [op("PAIR_SUMS", [0, 1, 2], 0, ret=[])],
        tags=["negatives", "same-element"],
    ),
    case(
        "two_zeroes_pair",
        1,
        [op("PAIR_SUMS", [0, 0], 0, ret=[[0, 0]])],
        tags=["negatives", "duplicates"],
    ),
    case(
        "negative_target",
        1,
        [op("PAIR_SUMS", [-1, -2, -3, 1], -3, ret=[[-2, -1]])],
        tags=["negatives"],
    ),
    case(
        "many_pairs_sorted_by_first_then_second",
        1,
        [
            op(
                "PAIR_SUMS",
                [10, 20, 30, 40, 50, 60],
                70,
                ret=[[10, 60], [20, 50], [30, 40]],
            )
        ],
        tags=["ordering"],
    ),
    case(
        "input_order_does_not_leak_into_output",
        1,
        [
            op(
                "PAIR_SUMS", [4, 1, 3, 2], 5, ret=[[1, 4], [2, 3]],
                why="same answer as the sorted input, so insertion order cannot show through",
            )
        ],
        tags=["ordering"],
    ),
    case(
        "the_input_list_is_not_modified",
        1,
        [
            op("PAIR_SUMS", [4, 1, 3, 2], 5, ret=[[1, 4], [2, 3]]),
            # A solution that sorts in place passes the line above and fails here.
            op("PAIR_SUMS", [4, 1, 3, 2], 100, ret=[]),
        ],
        tags=["ordering"],
        visible=True,
        doc="Sorting is fine, but sort a copy — the caller's list must come back untouched.",
    ),
    case(
        "large_input_rules_out_a_quadratic_scan",
        1,
        [
            op(
                "PAIR_SUMS",
                list(range(0, 40000, 2)),
                39998,
                # Every even a + b = 39998 with a < b, a from 0..19998 step 2.
                ret=[[a, 39998 - a] for a in range(0, 19999, 2)],
                why="40k elements: a nested loop is 800M comparisons and times out",
            )
        ],
        tags=["scale"],
    ),
]

ALL_CASES = tuple(LEVEL_1)


PROBLEM = Problem(
    key="two_sum_pairs",
    title="Pair Sums",
    blurb="Find every distinct pair of values in a list that adds up to a target.",
    class_name="",              # function kind: no class to instantiate
    kind=KIND_FUNCTION,
    total_points=100,
    category="algorithms",
    difficulty="easy",
    topics=("hash-set", "two-pointers", "deduplication"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Classic two-sum variant, asked in some form at nearly every company.",
)
