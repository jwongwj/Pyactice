"""3.13 Prefix sums — pay once, answer range questions for free.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **repeated questions about ranges**. One pass builds a running total; after that
the sum of any slice is one subtraction. The same trick generalises: prefix products,
prefix maxima, and two dimensions at once.

The pattern that makes it an algorithm rather than a formula is the counting one -- "how
many slices sum to k" -- where a dict of how often each running total has been seen turns
an O(n^2) scan into one pass. That is in unit 2.3 as the Dict checkpoint, deliberately, and
the two-dimensional version is the checkpoint here.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="RUNNING_SUM",
        signature="(nums: list[int]) -> list[int]",
        doc="Each position replaced by the sum of everything up to and including it.",
        constraint_note="one pass carrying a total; no nested sum",
        constraints=(
            ForbidCall(("sum", "accumulate"),
                       because="sum(nums[:i+1]) per position is O(n^2), and this is the "
                               "one-line building block everything below it uses",
                       hint="total += value, appending as you go"),
        ),
    ),
    Method(
        display="RANGE_SUMS",
        signature="(nums: list[int], queries: list[tuple[int, int]]) -> list[int]",
        doc="For each (start, end) query, the sum of nums[start..end] INCLUSIVE. A query "
            "outside the list, or with start after end, gives 0.",
        # The whole point: build once, then each query is O(1).
        constraint_note="build the prefix table once; each query is one subtraction",
        constraints=(
            ForbidCall(("sum",),
                       because="summing the slice per query is O(queries * n) -- the "
                               "prefix table costs one pass and makes every query O(1)",
                       hint="prefix[i] = sum of the first i values, so the answer is "
                            "prefix[end + 1] - prefix[start]"),
        ),
    ),
    Method(
        display="PIVOT_INDEX",
        signature="(nums: list[int]) -> int",
        doc="The leftmost index where everything strictly to its left sums to the same as "
            "everything strictly to its right. -1 when there is none. The value at the "
            "index itself counts for neither side.",
        constraint_note="one total, then one pass adjusting a running left sum",
        constraints=(
            Forbid(("comprehension",),
                   because="recomputing both sides per index is O(n^2); the right side is "
                           "whatever the total minus the left side minus this value is",
                   hint="right = total - left - value"),
        ),
    ),
    Method(
        display="PRODUCT_EXCEPT_SELF",
        signature="(nums: list[int]) -> list[int]",
        doc="Each position replaced by the product of every OTHER value.",
        # Division is the tempting answer and breaks on a zero, which is the trap.
        constraint_note="a prefix pass and a suffix pass; no division",
        constraints=(
            Forbid(("comprehension",),
                   because="dividing the total product by each value fails the moment any "
                           "value is 0, and the prefix/suffix pair needs no division at all",
                   hint="one pass filling in the product of everything to the left, a "
                        "second multiplying in everything to the right"),
        ),
    ),
    Method(
        display="REGION_SUM",
        fuzz=("grid",),
        signature="(grid: list[list[int]], regions: list[tuple[int, int, int, int]]) "
                  "-> list[int]",
        doc="For each (top, left, bottom, right) region, INCLUSIVE on all four sides, the "
            "sum of the cells inside it. A region outside the grid, or inverted, gives 0. "
            "The grid is rectangular.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Prefix sums", theme="pay once, then every range is a subtraction"),)

TAG_GLOSSARY = {
    "running": "carrying a total along one pass",
    "queries": "answering many range questions from one table",
    "balance": "comparing what is left of a point with what is right",
    "two-pass": "a forward pass and a backward pass combined",
    "grid": "the two-dimensional version, and inclusion-exclusion",
    "edge-values": "empty inputs, zeros, out-of-range queries",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("running_basic", "RUNNING_SUM", [1, 2, 3], ret=[1, 3, 6],
       tags=["running"], visible=True, doc="Each position includes itself."),
    _c("running_negatives", "RUNNING_SUM", [1, -2, 3], ret=[1, -1, 2],
       tags=["running", "edge-values"], visible=True,
       doc="The running total may go down, and may go negative."),
    _c("running_single", "RUNNING_SUM", [5], ret=[5], tags=["running", "edge-values"]),
    _c("running_empty", "RUNNING_SUM", [], ret=[], tags=["running", "edge-values"]),
    _c("running_zeros", "RUNNING_SUM", [0, 0], ret=[0, 0], tags=["running"]),

    _c("range_basic", "RANGE_SUMS", [1, 2, 3, 4], [(1, 2), (0, 3)], ret=[5, 10],
       tags=["queries"], visible=True,
       doc="Inclusive at BOTH ends: (1,2) is 2+3, not 2."),
    _c("range_single_cell", "RANGE_SUMS", [1, 2, 3], [(1, 1)], ret=[2],
       tags=["queries", "edge-values"], visible=True,
       doc="A one-wide range is the value itself."),
    _c("range_whole", "RANGE_SUMS", [1, 2], [(0, 1)], ret=[3], tags=["queries"]),
    _c("range_inverted", "RANGE_SUMS", [1, 2, 3], [(2, 1)], ret=[0],
       tags=["queries", "edge-values"], visible=True,
       doc="start after end is not a range, so it sums to 0 rather than borrowing a "
           "negative from the prefix table."),
    _c("range_out_of_bounds", "RANGE_SUMS", [1, 2], [(0, 9)], ret=[0],
       tags=["queries", "edge-values"], visible=True,
       doc="A range reaching past the end gives 0 rather than being clamped."),
    _c("range_negative_start", "RANGE_SUMS", [1, 2], [(-1, 1)], ret=[0],
       tags=["queries", "edge-values"]),
    # From triage. `range_out_of_bounds` used an end far past the list, which a widened
    # bound still rejects; `end == len(nums)` is the one value that separates the two.
    # And a negative start needs a list whose final prefix differs from the queried one,
    # or `table[-1]` coincidentally gives the right answer.
    _c("range_end_equals_length", "RANGE_SUMS", [1, 2], [(0, 2)], ret=[0],
       tags=["queries", "edge-values"], visible=True,
       doc="An end of exactly len(nums) is one past the last valid index."),
    _c("range_negative_start_visible", "RANGE_SUMS", [3, -1, 2, 0], [(-1, 0)], ret=[0],
       tags=["queries", "edge-values"], visible=True,
       doc="A negative start is out of range. Letting it through would index the prefix "
           "table from the wrong end."),
    _c("range_no_queries", "RANGE_SUMS", [1, 2], [], ret=[],
       tags=["queries", "edge-values"]),
    _c("range_repeated", "RANGE_SUMS", [1, 2], [(0, 0), (0, 0)], ret=[1, 1],
       tags=["queries"], why="asking twice answers twice"),

    _c("pivot_middle", "PIVOT_INDEX", [1, 7, 3, 6, 5, 6], ret=3,
       tags=["balance"], visible=True, doc="1+7+3 = 11 on the left, 5+6 = 11 on the right."),
    _c("pivot_at_zero", "PIVOT_INDEX", [2, 1, -1], ret=0,
       tags=["balance", "edge-values"], visible=True,
       doc="Nothing to the left of index 0 sums to 0, and 1 + -1 is also 0."),
    _c("pivot_none", "PIVOT_INDEX", [1, 2, 3], ret=-1,
       tags=["balance", "edge-values"], visible=True, doc="No index balances."),
    _c("pivot_leftmost_of_several", "PIVOT_INDEX", [0, 0, 0], ret=0,
       tags=["balance", "edge-values"], visible=True,
       doc="Every index balances here, and the leftmost is the answer."),
    _c("pivot_single", "PIVOT_INDEX", [7], ret=0,
       tags=["balance", "edge-values"],
       why="both sides are empty, and two empty sums are equal"),
    _c("pivot_empty", "PIVOT_INDEX", [], ret=-1, tags=["balance", "edge-values"]),

    _c("product_basic", "PRODUCT_EXCEPT_SELF", [1, 2, 3, 4], ret=[24, 12, 8, 6],
       tags=["two-pass"], visible=True, doc="Everything except the position itself."),
    _c("product_one_zero", "PRODUCT_EXCEPT_SELF", [1, 0, 3], ret=[0, 3, 0],
       tags=["two-pass", "edge-values"], visible=True,
       doc="With one zero, only that position is non-zero. Dividing the total product "
           "by each value divides by zero here."),
    _c("product_two_zeros", "PRODUCT_EXCEPT_SELF", [0, 0, 3], ret=[0, 0, 0],
       tags=["two-pass", "edge-values"], visible=True,
       doc="With two zeros every position is 0, which a one-zero special case gets wrong."),
    _c("product_negatives", "PRODUCT_EXCEPT_SELF", [-1, 2], ret=[2, -1],
       tags=["two-pass"]),
    _c("product_single", "PRODUCT_EXCEPT_SELF", [5], ret=[1],
       tags=["two-pass", "edge-values"],
       why="the product of no values is 1, the multiplicative identity"),
    _c("product_empty", "PRODUCT_EXCEPT_SELF", [], ret=[],
       tags=["two-pass", "edge-values"]),

    _c("region_basic", "REGION_SUM", [[1, 2], [3, 4]], [(0, 0, 1, 1)], ret=[10],
       tags=["checkpoint", "grid"], visible=True, doc="The whole grid."),
    _c("region_one_cell", "REGION_SUM", [[1, 2], [3, 4]], [(1, 1, 1, 1)], ret=[4],
       tags=["checkpoint", "grid"], visible=True, doc="Inclusive on all four sides."),
    _c("region_row", "REGION_SUM", [[1, 2], [3, 4]], [(0, 0, 0, 1)], ret=[3],
       tags=["checkpoint", "grid"], visible=True,
       doc="The top row. Getting this right is what inclusion-exclusion is for: the "
           "region above is empty and must contribute nothing."),
    _c("region_inverted", "REGION_SUM", [[1, 2], [3, 4]], [(1, 1, 0, 0)], ret=[0],
       tags=["checkpoint", "edge-values"], visible=True, doc="bottom above top."),
    _c("region_out_of_bounds", "REGION_SUM", [[1]], [(0, 0, 5, 5)], ret=[0],
       tags=["checkpoint", "edge-values"]),
    _c("region_negatives", "REGION_SUM", [[-1, 2]], [(0, 0, 0, 1)], ret=[1],
       tags=["checkpoint", "grid"]),
    _c("region_empty_grid", "REGION_SUM", [], [(0, 0, 0, 0)], ret=[0],
       tags=["checkpoint", "edge-values"]),
    _c("region_bottom_equals_rows", "REGION_SUM", [[1]], [(0, 0, 1, 0)], ret=[0],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A bottom of exactly the row count is one past the last row."),
    _c("region_negative_edge", "REGION_SUM", [[0, 1], [1, 1], [1, 1]],
       [(0, -1, 1, -1)], ret=[0], tags=["checkpoint", "edge-values"], visible=True,
       doc="A negative column is out of range, and letting it through reads the prefix "
           "table from the far edge."),
    # The mirror of region_negative_edge, which tested a negative COLUMN only. The four
    # bounds are four separate guards and each needs its own case -- the same asymmetry
    # that hid two gaps in unit 2.12.
    _c("region_negative_top", "REGION_SUM", [[1], [0], [1], [1]], [(-1, 0, 2, 0)],
       ret=[0], tags=["checkpoint", "edge-values"], visible=True,
       doc="A negative top is out of range, exactly as a negative left is."),
    _c("region_no_queries", "REGION_SUM", [[1]], [], ret=[],
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="prefix_sums",
    title="3.13 Prefix sums",
    blurb="Running totals, O(1) range queries, pivot index, product except self.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("running", "queries", "two-pass"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.13 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
