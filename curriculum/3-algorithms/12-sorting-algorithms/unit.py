"""3.12 Sorting algorithms — for when you are asked HOW sort works.

Self-contained: loaded by file path, so no package-relative imports.

`sorted()` is the right answer in every real situation, and this unit is the one place
where it is forbidden -- because the question being simulated is "implement it", and
because two of these are genuinely useful on their own:

  * the MERGE step is the k-way merge and the basis of external sorting;
  * PARTITION is quickselect, which finds the kth largest in O(n) average without
    sorting anything.

Stability is the property that decides which of these you may substitute for which, so it
is drilled directly rather than mentioned.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="MERGE_SORT",
        signature="(nums: list[int]) -> list[int]",
        doc="Ascending, by merge sort. Duplicates kept.",
        constraint_note="split, sort each half, merge; no sorted() and no sort()",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="the point is the recurrence: sorting two halves is the "
                               "same problem, and merging two sorted lists is linear",
                       hint="base case is a list of 0 or 1; merge with two indices"),
        ),
    ),
    Method(
        display="PARTITION",
        signature="(nums: list[int], pivot: int) -> tuple[list[int], list[int], list[int]]",
        doc="(less than pivot, equal to pivot, greater than pivot). Within each part, "
            "values keep their original relative order.",
        # Three-way, because it is what makes quicksort survive many duplicates and what
        # quickselect actually needs.
        constraint_note="one pass into three buckets; no sorting",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="partitioning is the step quicksort is built from, and a "
                               "THREE-way split is what stops many equal values degrading "
                               "it to O(n^2)",
                       hint="one loop, three appends"),
        ),
    ),
    Method(
        display="QUICKSELECT",
        signature="(nums: list[int], k: int) -> int | None",
        doc="The kth SMALLEST value, with k counting from 1. None when k is out of range. "
            "Duplicates count separately: the 2nd smallest of [5, 5] is 5.",
        constraint_note="partition and recurse into one side only; do not sort",
        constraints=(
            ForbidCall(("sorted", "sort", "nsmallest", "nlargest"),
                       because="sorting is O(n log n) for one value; recursing into only "
                               "the side that can contain the answer is O(n) on average, "
                               "and that is the whole idea",
                       hint="partition, then decide which of the three parts holds k"),
        ),
    ),
    Method(
        display="COUNTING_SORT",
        fuzz=("nonneg",),
        signature="(nums: list[int], top: int) -> list[int]",
        doc="Ascending, by counting. Values are between 0 and `top` inclusive; anything "
            "outside that range is ignored. Empty when `top` is negative.",
        constraint_note="tally into buckets, then read them out; no comparisons",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="comparison sorting cannot beat O(n log n); counting sidesteps "
                               "the bound entirely by not comparing, at the cost of needing "
                               "a known, small range",
                       hint="a list of counts of length top + 1, then expand it"),
        ),
    ),
    Method(
        display="STABLE_BY_KEY",
        signature="(rows: list[tuple[str, int]], ) -> list[tuple[str, int]]",
        doc="Rows ordered by their number ascending, with rows sharing a number left in "
            "their original relative order. Implement the sort; do not call one.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Sorting algorithms", theme="how the library does it, and when to borrow a step"),)

TAG_GLOSSARY = {
    "divide": "splitting a problem into two of the same shape",
    "partition": "arranging around a pivot",
    "selection": "finding one order statistic without sorting",
    "counting": "sorting without comparing",
    "stability": "equal keys keeping their original order",
    "edge-values": "empty inputs, k out of range, all equal, values outside the range",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("merge_basic", "MERGE_SORT", [3, 1, 2], ret=[1, 2, 3],
       tags=["divide"], visible=True, doc="Ascending."),
    _c("merge_duplicates", "MERGE_SORT", [2, 1, 2], ret=[1, 2, 2],
       tags=["divide", "edge-values"], visible=True, doc="Duplicates are kept."),
    _c("merge_already", "MERGE_SORT", [1, 2, 3], ret=[1, 2, 3], tags=["divide"]),
    _c("merge_reversed", "MERGE_SORT", [3, 2, 1], ret=[1, 2, 3], tags=["divide"]),
    _c("merge_single", "MERGE_SORT", [7], ret=[7], tags=["divide", "edge-values"]),
    _c("merge_empty", "MERGE_SORT", [], ret=[], tags=["divide", "edge-values"], visible=True,
       doc="The base case has to accept an empty list, not only a single item."),
    _c("merge_negatives", "MERGE_SORT", [0, -2, 1], ret=[-2, 0, 1], tags=["divide"]),
    _c("merge_odd_length", "MERGE_SORT", [5, 1, 4, 2, 3], ret=[1, 2, 3, 4, 5],
       tags=["divide", "edge-values"],
       why="an odd length means the two halves differ in size, which an off-by-one split "
           "either loses an element from or recurses forever on"),

    _c("partition_basic", "PARTITION", [3, 1, 4, 1, 5], 3,
       ret=([1, 1], [3], [4, 5]), tags=["partition"], visible=True,
       doc="Three buckets, and each keeps its input order."),
    _c("partition_no_equals", "PARTITION", [1, 5], 3, ret=([1], [], [5]),
       tags=["partition", "edge-values"], visible=True,
       doc="The middle bucket may be empty; the pivot need not be present."),
    _c("partition_all_equal", "PARTITION", [2, 2], 2, ret=([], [2, 2], []),
       tags=["partition", "edge-values"], visible=True,
       doc="Everything equal. A two-way partition puts these all on one side and is what "
           "makes quicksort quadratic on repeated values."),
    _c("partition_empty", "PARTITION", [], 1, ret=([], [], []),
       tags=["partition", "edge-values"]),
    _c("partition_order_kept", "PARTITION", [9, 8, 1], 5, ret=([1], [], [9, 8]),
       tags=["partition", "stability"],
       why="within a bucket the original order stands; 9 came before 8"),

    _c("select_first", "QUICKSELECT", [3, 1, 2], 1, ret=1,
       tags=["selection"], visible=True, doc="k counts from 1, so this is the smallest."),
    _c("select_middle", "QUICKSELECT", [3, 1, 2], 2, ret=2, tags=["selection"]),
    _c("select_last", "QUICKSELECT", [3, 1, 2], 3, ret=3, tags=["selection"]),
    _c("select_duplicates", "QUICKSELECT", [5, 5], 2, ret=5,
       tags=["selection", "edge-values"], visible=True,
       doc="Duplicates count separately, so the 2nd smallest of two 5s is 5."),
    _c("select_k_too_big", "QUICKSELECT", [1], 2, ret=None,
       tags=["selection", "edge-values"], visible=True, doc="Out of range."),
    _c("select_k_zero", "QUICKSELECT", [1], 0, ret=None,
       tags=["selection", "edge-values"],
       why="k counts from 1, so 0 is out of range rather than the first"),
    _c("select_empty", "QUICKSELECT", [], 1, ret=None,
       tags=["selection", "edge-values"]),
    _c("select_negatives", "QUICKSELECT", [0, -5, 3], 1, ret=-5, tags=["selection"]),

    _c("counting_basic", "COUNTING_SORT", [2, 0, 1], 2, ret=[0, 1, 2],
       tags=["counting"], visible=True, doc="Three buckets, read out in order."),
    _c("counting_duplicates", "COUNTING_SORT", [1, 1, 0], 1, ret=[0, 1, 1],
       tags=["counting"], visible=True, doc="A bucket may hold more than one."),
    _c("counting_gaps", "COUNTING_SORT", [3, 0], 3, ret=[0, 3],
       tags=["counting", "edge-values"], visible=True,
       doc="Empty buckets in the middle contribute nothing."),
    _c("counting_out_of_range", "COUNTING_SORT", [1, 9], 2, ret=[1],
       tags=["counting", "edge-values"], visible=True,
       doc="9 is above `top` and is ignored rather than growing the bucket list."),
    _c("counting_top_zero", "COUNTING_SORT", [0, 0], 0, ret=[0, 0],
       tags=["counting", "edge-values"],
       why="a top of 0 still needs one bucket, so the list has length top + 1"),
    _c("counting_negative_top", "COUNTING_SORT", [1], -1, ret=[],
       tags=["counting", "edge-values"]),
    _c("counting_empty", "COUNTING_SORT", [], 3, ret=[],
       tags=["counting", "edge-values"]),

    _c("stable_basic", "STABLE_BY_KEY", [("b", 2), ("a", 1)], ret=[("a", 1), ("b", 2)],
       tags=["checkpoint", "stability"], visible=True, doc="By number ascending."),
    _c("stable_ties_keep_order", "STABLE_BY_KEY",
       [("z", 1), ("a", 1), ("m", 1)], ret=[("z", 1), ("a", 1), ("m", 1)],
       tags=["checkpoint", "stability"], visible=True,
       doc="Every number is equal, so nothing moves. Sorting by the whole tuple would "
           "reorder these alphabetically and be wrong."),
    _c("stable_mixed", "STABLE_BY_KEY",
       [("c", 2), ("a", 1), ("b", 2)], ret=[("a", 1), ("c", 2), ("b", 2)],
       tags=["checkpoint", "stability"], visible=True,
       doc="c comes before b because it did in the input, and both have 2."),
    _c("stable_single", "STABLE_BY_KEY", [("a", 5)], ret=[("a", 5)],
       tags=["checkpoint", "edge-values"]),
    _c("stable_empty", "STABLE_BY_KEY", [], ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("stable_negatives", "STABLE_BY_KEY", [("a", 1), ("b", -1)],
       ret=[("b", -1), ("a", 1)], tags=["checkpoint"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="sorting_algorithms",
    title="3.12 Sorting algorithms",
    blurb="Merge sort, three-way partition, quickselect, counting sort and stability.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("divide", "partition", "stability"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.12 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
