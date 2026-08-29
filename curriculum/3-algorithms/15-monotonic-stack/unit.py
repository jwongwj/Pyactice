"""3.15 Monotonic stack — the pattern, past the two questions that introduce it.

Self-contained: loaded by file path, so no package-relative imports.

Unit 2.5 introduces the monotonic stack through NEXT_GREATER and DAILY_WAIT, which are the
same loop twice. This unit is what the pattern is actually *for*: the questions where it is
not obvious that "next greater" is even involved.

The invariant, once, so the drills can refer to it: the stack holds INDICES whose answer is
not yet known, and their values are monotonic. When a value arrives that breaks the
monotonicity, everything it breaks has just found its answer -- and the arrival is the
answer, or the boundary of it.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="PREVIOUS_SMALLER",
        signature="(nums: list[int]) -> list[int]",
        doc="For each position, the nearest value to its LEFT that is strictly smaller, "
            "or -1 when there is none.",
        # The mirror of 2.5's NEXT_GREATER: same loop, answered on the way in rather than
        # on the way out.
        constraint_note="an increasing stack, read on the way IN; no nested loop",
        constraints=(
            Forbid(("comprehension",),
                   because="scanning left from every position is O(n^2). Looking LEFT is "
                           "the easier direction: the answer is whatever is left on the "
                           "stack after popping everything too big",
                   hint="pop while the top is >= this value; the new top is the answer"),
        ),
    ),
    Method(
        display="NEXT_SMALLER_INDEX",
        signature="(nums: list[int]) -> list[int]",
        doc="For each position, the INDEX of the nearest strictly smaller value to its "
            "right, or -1 when there is none.",
        constraint_note="the same stack, answering with positions rather than values",
        constraints=(
            Forbid(("comprehension",),
                   because="most real uses need the index, not the value -- a width, a "
                           "distance or a slice bound -- so holding indices is the habit "
                           "worth building",
                   hint="the stack holds indices; the arrival's index is the answer for "
                        "everything it pops"),
        ),
    ),
    Method(
        display="TRAPPED_WATER",
        fuzz=("nonneg",),
        signature="(heights: list[int]) -> int",
        doc="How much water is held between the bars after rain, where each bar is 1 wide.",
        # Two correct answers -- a stack, or two pointers -- and the two-pointer one is
        # left available on purpose, because recognising it is the point.
        constraint_note="a decreasing stack, or two pointers; not a scan per position",
        constraints=(
            Forbid(("comprehension",),
                   because="the water above a bar is limited by the tallest bar on each "
                           "side, and computing both by scanning is O(n^2). A monotonic "
                           "stack finds each basin as it closes; two pointers do it in "
                           "O(1) space -- either is a good answer",
                   hint="a bar taller than the stack top closes a basin whose depth is "
                        "the shorter of the two walls minus the bottom"),
        ),
    ),
    Method(
        display="STOCK_SPAN",
        fuzz=("nonneg",),
        signature="(prices: list[int]) -> list[int]",
        doc="For each day, how many consecutive days up to and including it had a price "
            "less than or equal to that day's.",
        constraint_note="PREVIOUS_GREATER in disguise; the span is an index difference",
        constraints=(
            Forbid(("comprehension",),
                   because="the span ends at the previous STRICTLY GREATER price, so this "
                           "is one of the two questions from unit 2.5 wearing a business "
                           "problem's clothes",
                   hint="pop while the top price is <= today; the span is today's index "
                        "minus the new top's index"),
        ),
    ),
    Method(
        display="MAX_OF_MINS",
        fuzz=("nonneg",),
        signature="(nums: list[int]) -> list[int]",
        doc="For every window size k from 1 to len(nums), the LARGEST minimum of any "
            "window of that size. Position i of the answer is for size i+1.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Monotonic stack",
                theme="the arrival answers everything it breaks"),)

TAG_GLOSSARY = {
    "left": "looking backwards, answered on the way in",
    "right": "looking forwards, answered on the way out",
    "indices": "holding positions rather than values, for widths and distances",
    "basin": "the area between two walls",
    "disguise": "a question that is next-greater without saying so",
    "edge-values": "empty inputs, all equal, monotonic inputs",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("prev_smaller_basic", "PREVIOUS_SMALLER", [3, 1, 4, 2], ret=[-1, -1, 1, 1],
       tags=["left"], visible=True,
       doc="Nothing is left of 3; 1 has only a larger value before it; 4 and 2 both find 1."),
    _c("prev_smaller_increasing", "PREVIOUS_SMALLER", [1, 2, 3], ret=[-1, 1, 2],
       tags=["left"], visible=True, doc="Each value's neighbour is its answer."),
    _c("prev_smaller_decreasing", "PREVIOUS_SMALLER", [3, 2, 1], ret=[-1, -1, -1],
       tags=["left"], visible=True, doc="Nothing to the left is ever smaller."),
    _c("prev_smaller_equal", "PREVIOUS_SMALLER", [2, 2], ret=[-1, -1],
       tags=["left", "edge-values"], visible=True,
       doc="Strictly smaller, so an equal value does not answer it."),
    _c("prev_smaller_single", "PREVIOUS_SMALLER", [5], ret=[-1],
       tags=["left", "edge-values"]),
    _c("prev_smaller_empty", "PREVIOUS_SMALLER", [], ret=[], tags=["left", "edge-values"]),

    _c("next_smaller_basic", "NEXT_SMALLER_INDEX", [3, 1, 4, 2], ret=[1, -1, 3, -1],
       tags=["right", "indices"], visible=True,
       doc="Indices, not values: 3 is answered by the 1 at index 1."),
    _c("next_smaller_none", "NEXT_SMALLER_INDEX", [1, 2, 3], ret=[-1, -1, -1],
       tags=["right", "indices"], visible=True, doc="Increasing, so nothing is answered."),
    _c("next_smaller_all", "NEXT_SMALLER_INDEX", [3, 2, 1], ret=[1, 2, -1],
       tags=["right", "indices"], visible=True, doc="Each answered by its neighbour."),
    _c("next_smaller_equal", "NEXT_SMALLER_INDEX", [2, 2], ret=[-1, -1],
       tags=["right", "edge-values"]),
    _c("next_smaller_empty", "NEXT_SMALLER_INDEX", [], ret=[],
       tags=["right", "edge-values"]),

    _c("water_basic", "TRAPPED_WATER", [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], ret=6,
       tags=["basin"], visible=True, doc="The classic profile."),
    _c("water_simple_basin", "TRAPPED_WATER", [3, 0, 3], ret=3,
       tags=["basin"], visible=True, doc="Three units held between two walls of 3."),
    _c("water_no_basin", "TRAPPED_WATER", [1, 2, 3], ret=0,
       tags=["basin", "edge-values"], visible=True,
       doc="Monotonic, so nothing is enclosed."),
    _c("water_shorter_wall_limits", "TRAPPED_WATER", [5, 0, 2], ret=2,
       tags=["basin"], visible=True,
       doc="The SHORTER wall decides the level, so 2 units and not 5."),
    _c("water_flat", "TRAPPED_WATER", [2, 2, 2], ret=0, tags=["basin", "edge-values"]),
    _c("water_two_bars", "TRAPPED_WATER", [5, 5], ret=0,
       tags=["basin", "edge-values"], why="a basin needs something between its walls"),
    _c("water_empty", "TRAPPED_WATER", [], ret=0, tags=["basin", "edge-values"]),
    _c("water_two_basins", "TRAPPED_WATER", [3, 0, 3, 0, 3], ret=6,
       tags=["basin"], why="two separate basins, each holding 3"),

    _c("span_basic", "STOCK_SPAN", [100, 80, 60, 70, 60, 75, 85],
       ret=[1, 1, 1, 2, 1, 4, 6], tags=["disguise", "indices"], visible=True,
       doc="Each day counts itself plus the run of days behind it that were no higher."),
    _c("span_rising", "STOCK_SPAN", [1, 2, 3], ret=[1, 2, 3],
       tags=["disguise"], visible=True, doc="Every day extends the run."),
    _c("span_falling", "STOCK_SPAN", [3, 2, 1], ret=[1, 1, 1],
       tags=["disguise"], visible=True, doc="No day beats the one before it."),
    _c("span_equal", "STOCK_SPAN", [2, 2], ret=[1, 2],
       tags=["disguise", "edge-values"], visible=True,
       doc="'less than or equal', so an equal price DOES extend the span -- the opposite "
           "of the strict comparison the other drills here use."),
    _c("span_single", "STOCK_SPAN", [5], ret=[1], tags=["disguise", "edge-values"]),
    _c("span_empty", "STOCK_SPAN", [], ret=[], tags=["disguise", "edge-values"]),

    _c("mins_basic", "MAX_OF_MINS", [10, 20, 30], ret=[30, 20, 10],
       tags=["checkpoint"], visible=True,
       doc="Size 1: the largest value. Size 3: the minimum of everything. Sizes in "
           "between fall between."),
    _c("mins_dip", "MAX_OF_MINS", [3, 1, 3], ret=[3, 1, 1],
       tags=["checkpoint"], visible=True,
       doc="Any window of 2 or more contains the 1, so it caps them all."),
    _c("mins_flat", "MAX_OF_MINS", [4, 4], ret=[4, 4],
       tags=["checkpoint", "edge-values"]),
    _c("mins_single", "MAX_OF_MINS", [7], ret=[7],
       tags=["checkpoint", "edge-values"]),
    # Four gaps from triage. The existing cases were all short, flat or strictly
    # monotonic, so nothing exercised a bar whose widest window is genuinely interior.
    _c("mins_zero_first", "MAX_OF_MINS", [0, 10], ret=[10, 0],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A 0 caps every window that contains it, including the full-width one."),
    _c("mins_equal_pair", "MAX_OF_MINS", [1, 7, 7], ret=[7, 7, 1],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Two equal bars, and a window of 2 can sit entirely inside them."),
    _c("mins_interior_peak", "MAX_OF_MINS", [1, 10, 3, 2], ret=[10, 3, 2, 1],
       tags=["checkpoint"], visible=True,
       doc="Every size has a different answer, and none of them is at an edge."),
    _c("mins_zeros_at_both_ends", "MAX_OF_MINS", [0, 1, 3, 0], ret=[3, 1, 0, 0],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Any window of 3 or more touches a 0."),
    _c("mins_empty", "MAX_OF_MINS", [], ret=[], tags=["checkpoint", "edge-values"]),
    _c("mins_descending", "MAX_OF_MINS", [3, 2, 1], ret=[3, 2, 1],
       tags=["checkpoint"],
       why="the answer is non-increasing, which is a useful sanity check on any attempt"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="monotonic_stack",
    title="3.15 Monotonic stack",
    blurb="Previous smaller, next smaller, trapped water, stock span.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="hard",
    topics=("left", "right", "basin"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.15 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
