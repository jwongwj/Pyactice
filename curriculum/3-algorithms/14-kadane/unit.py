"""3.14 Kadane — the maximum contiguous subarray, in one pass.

Self-contained: loaded by file path, so no package-relative imports.

One idea, stated once: at each position, the best run ENDING HERE is either this value
alone, or this value joined to the best run ending at the previous position. Whichever is
larger. Everything in this unit is that sentence with something different tracked
alongside.

The decision that produces almost every bug here is what an empty input means, and whether
an all-negative list answers 0. Both are stated in each drill rather than left to taste.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="MAX_SUBARRAY",
        signature="(nums: list[int]) -> int",
        doc="The largest sum of any non-empty run of consecutive values. 0 for an empty "
            "list. An all-negative list answers with its least negative value, NOT 0, "
            "because the run may not be empty.",
        constraint_note="one pass, two running values; no nested loop",
        constraints=(
            Forbid(("comprehension",),
                   because="every start and end is O(n^2); the best run ending at each "
                           "position depends only on the one before it",
                   hint="ending_here = max(value, ending_here + value); best = "
                        "max(best, ending_here)"),
        ),
    ),
    Method(
        display="MIN_SUBARRAY",
        signature="(nums: list[int]) -> int",
        doc="The smallest sum of any non-empty run. 0 for an empty list. The mirror image "
            "of MAX_SUBARRAY.",
        constraint_note="the same pass with min for max",
        constraints=(
            Forbid(("comprehension",),
                   because="worth writing once because the circular version below needs "
                           "both halves at the same time",
                   hint="ending_here = min(value, ending_here + value)"),
        ),
    ),
    Method(
        display="MAX_SUBARRAY_RANGE",
        signature="(nums: list[int]) -> tuple[int, int, int]",
        doc="(sum, start, end) of the best run, `end` INCLUSIVE. (0, -1, -1) for an empty "
            "list. When two runs tie, the one starting earliest wins; if they also start "
            "together, the shorter one wins.",
        # Tracking where the run began is the part people get wrong: the start only moves
        # when the run is restarted, not on every improvement.
        constraint_note="track where the current run started; move it only on a restart",
        constraints=(
            Forbid(("comprehension",),
                   because="the indices are what make this more than the value version, "
                           "and they cannot be recovered afterwards without another scan",
                   hint="when you take `value` alone rather than extending, the run "
                        "restarts and the start index becomes this position"),
        ),
    ),
    Method(
        display="MAX_PRODUCT",
        signature="(nums: list[int]) -> int",
        doc="The largest product of any non-empty run. 0 for an empty list.",
        # Negatives make this genuinely different: the smallest product so far is a
        # candidate for the largest, because one more negative flips it.
        constraint_note="carry the smallest running product as well as the largest",
        constraints=(
            Forbid(("comprehension",),
                   because="a negative value turns the smallest product into the largest, "
                           "so tracking only the maximum is not enough -- this is the one "
                           "drill here where the sum version's shape does not transfer",
                   hint="on a negative value, swap the running max and min before "
                        "extending"),
        ),
    ),
    Method(
        display="MAX_CIRCULAR",
        signature="(nums: list[int]) -> int",
        doc="The largest sum of any non-empty run, where the list wraps around: a run may "
            "end past the last value and continue from the first. No value may be used "
            "twice. 0 for an empty list.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Kadane", theme="the best run ending here, one position at a time"),)

TAG_GLOSSARY = {
    "running": "the best run ending at the current position",
    "indices": "where the run began and ended",
    "negatives": "why an all-negative list is not 0, and why products differ",
    "wrap": "runs that continue past the end",
    "edge-values": "empty inputs, single values, all negative, zeros",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("max_sub_basic", "MAX_SUBARRAY", [-2, 1, -3, 4, -1, 2, 1, -5, 4], ret=6,
       tags=["running"], visible=True, doc="[4, -1, 2, 1] sums to 6."),
    _c("max_sub_all_negative", "MAX_SUBARRAY", [-3, -1, -2], ret=-1,
       tags=["running", "negatives"], visible=True,
       doc="The run may not be empty, so the answer is the least negative value, not 0."),
    _c("max_sub_all_positive", "MAX_SUBARRAY", [1, 2, 3], ret=6, tags=["running"]),
    _c("max_sub_single", "MAX_SUBARRAY", [-5], ret=-5,
       tags=["running", "edge-values"], visible=True,
       doc="One value, and it must be chosen."),
    _c("max_sub_empty", "MAX_SUBARRAY", [], ret=0, tags=["running", "edge-values"]),
    _c("max_sub_zeros", "MAX_SUBARRAY", [-1, 0, -1], ret=0,
       tags=["running", "edge-values"],
       why="0 beats both negatives, and is a real run of one value"),

    _c("min_sub_basic", "MIN_SUBARRAY", [2, -3, 1, -4, 2], ret=-6,
       tags=["running"], visible=True, doc="[-3, 1, -4] sums to -6."),
    _c("min_sub_all_positive", "MIN_SUBARRAY", [3, 1, 2], ret=1,
       tags=["running", "negatives"], visible=True,
       doc="All positive: the smallest run is the smallest single value, not 0."),
    # All four from `drill_mutation.py --triage`. The single-value case here was
    # positive, so nothing exercised the run that must NOT be extended from index 0;
    # and no two-value case started negative.
    _c("min_sub_single_negative", "MIN_SUBARRAY", [-3], ret=-3,
       tags=["running", "edge-values"], visible=True,
       doc="One negative value. Seeding the walk from index 0 and then also visiting "
           "index 0 counts it twice and gives -6."),
    _c("min_sub_negative_first", "MIN_SUBARRAY", [-3, 4], ret=-3,
       tags=["running", "edge-values"], visible=True,
       doc="The best run is the first value alone, so the walk must not be seeded at 0."),
    _c("min_sub_single", "MIN_SUBARRAY", [4], ret=4, tags=["running", "edge-values"]),
    _c("min_sub_empty", "MIN_SUBARRAY", [], ret=0, tags=["running", "edge-values"]),

    _c("range_basic", "MAX_SUBARRAY_RANGE", [-2, 1, -3, 4, -1, 2, 1, -5, 4],
       ret=(6, 3, 6), tags=["indices"], visible=True,
       doc="Sum 6, from index 3 to index 6 inclusive."),
    _c("range_whole", "MAX_SUBARRAY_RANGE", [1, 2], ret=(3, 0, 1), tags=["indices"]),
    _c("range_single_best", "MAX_SUBARRAY_RANGE", [-1, 5, -1], ret=(5, 1, 1),
       tags=["indices"], visible=True,
       doc="A run of one. The start index moves to 1 because the run restarted there."),
    _c("range_all_negative", "MAX_SUBARRAY_RANGE", [-3, -1], ret=(-1, 1, 1),
       tags=["indices", "negatives"], visible=True,
       doc="The least negative value, and where it is."),
    _c("range_tie_earliest", "MAX_SUBARRAY_RANGE", [2, 0], ret=(2, 0, 0),
       tags=["indices", "edge-values"], visible=True,
       doc="[2] and [2, 0] both sum to 2. They start together, so the SHORTER one wins."),
    _c("range_empty", "MAX_SUBARRAY_RANGE", [], ret=(0, -1, -1),
       tags=["indices", "edge-values"]),
    # First written expecting (3, 1, 1), which contradicts this drill's own stated
    # tie-break. Gate 1 rejected it. [0,3] and [3] both sum to 3; the rule says the
    # EARLIEST start wins, and that is index 0.
    _c("range_leading_zero", "MAX_SUBARRAY_RANGE", [0, 3], ret=(3, 0, 1),
       tags=["indices", "edge-values"], visible=True,
       doc="[0,3] and [3] both sum to 3. The earliest start wins, so the leading zero is "
           "part of the answer -- extending across it is not a restart."),

    _c("product_basic", "MAX_PRODUCT", [2, 3, -2, 4], ret=6,
       tags=["running", "negatives"], visible=True, doc="[2, 3]."),
    _c("product_two_negatives", "MAX_PRODUCT", [-2, 3, -4], ret=24,
       tags=["running", "negatives"], visible=True,
       doc="The whole list: two negatives multiply to a positive, so the SMALLEST running "
           "product had to be carried along to become the largest."),
    _c("product_with_zero", "MAX_PRODUCT", [-2, 0, -1], ret=0,
       tags=["running", "edge-values"], visible=True,
       doc="A zero resets both running products, and here it beats either negative."),
    _c("product_single_negative", "MAX_PRODUCT", [-3], ret=-3,
       tags=["running", "edge-values"]),
    _c("product_empty", "MAX_PRODUCT", [], ret=0, tags=["running", "edge-values"]),
    _c("product_negative_then_positives", "MAX_PRODUCT", [-4, 2, 2], ret=4,
       tags=["running", "negatives"], visible=True,
       doc="One negative at the front. Swapping the running max and min on EVERY value "
           "rather than only on a negative one gives 2."),
    _c("product_two_negatives_apart", "MAX_PRODUCT", [-4, 2, -1, 2], ret=16,
       tags=["running", "negatives"], visible=True,
       doc="The whole list: -4 x 2 x -1 x 2 = 16. The running minimum has to survive two "
           "positive values in between to become the maximum at the end."),
    _c("product_all_positive", "MAX_PRODUCT", [1, 2, 3], ret=6, tags=["running"]),

    _c("circular_wraps", "MAX_CIRCULAR", [5, -3, 5], ret=10,
       tags=["checkpoint", "wrap"], visible=True,
       doc="The best run is the last 5 continuing round to the first: 10. The best "
           "non-wrapping run is only 7."),
    _c("circular_no_wrap", "MAX_CIRCULAR", [1, -2, 3, -2], ret=3,
       tags=["checkpoint", "wrap"], visible=True,
       doc="Here the best run does not wrap at all."),
    _c("circular_all_negative", "MAX_CIRCULAR", [-3, -2, -3], ret=-2,
       tags=["checkpoint", "negatives"], visible=True,
       doc="All negative. The wrapping formula 'total minus the minimum run' would give "
           "0 here by taking an empty run, which is not allowed -- so this case has to "
           "fall back to the plain answer."),
    _c("circular_single_negative", "MAX_CIRCULAR", [-1], ret=-1,
       tags=["checkpoint", "negatives"], visible=True,
       doc="A single negative value. The all-negative fallback has to fire on a "
           "one-element list too, and the three-element case above does not prove it."),
    _c("circular_single", "MAX_CIRCULAR", [4], ret=4,
       tags=["checkpoint", "edge-values"]),
    _c("circular_empty", "MAX_CIRCULAR", [], ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("circular_whole_list", "MAX_CIRCULAR", [1, 2, 3], ret=6, tags=["checkpoint"],
       why="all positive, so the whole list wins and no wrap is needed"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="kadane",
    title="3.14 Kadane",
    blurb="Max and min subarray, with indices, max product, and the circular version.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("running", "negatives", "wrap"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.14 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
