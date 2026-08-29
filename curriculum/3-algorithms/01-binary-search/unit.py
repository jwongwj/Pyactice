"""3.1 Binary search — and the version that is not about a sorted list at all.

Self-contained: loaded by file path, so no package-relative imports.

The recognition cue is **a sorted input, or a monotonic answer**. The second half of that
is what makes this an algorithm rather than an API call: when "is X enough?" goes from
False to True exactly once as X grows, you can binary search over X even though there is no
list to search. The checkpoint is that shape.

The drills climb in the catalogue's order: obvious, then disguised, then only-this-works.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="FIND_INDEX",
        fuzz=("sorted", "unique"),
        signature="(nums: list[int], target: int) -> int",
        doc="Index of `target` in an ascending list, or -1 when it is absent. "
            "The list has no duplicates.",
        constraint_note="halve the range each step; no `in`, no index(), no loop over nums",
        constraints=(
            ForbidCall(("index", "count"),
                       because="index() is a linear scan, which is the thing binary search "
                               "exists to avoid -- and it raises rather than returning -1",
                       hint="lo, hi = 0, len(nums) - 1 and compare against the midpoint"),
            Forbid(("comprehension",),
                   because="a comprehension visits everything; binary search visits log n",
                   hint="while lo <= hi, move whichever bound the comparison rules out"),
        ),
    ),
    Method(
        display="INSERT_POSITION",
        fuzz=("sorted",),
        signature="(nums: list[int], target: int) -> int",
        doc="The leftmost index at which `target` could be inserted with the list staying "
            "ascending. Equal to the index of `target` when it is present.",
        constraint_note="this is bisect_left; write it, do not import it",
        constraints=(
            ForbidCall(("bisect_left", "bisect", "insort", "index"),
                       because="the module is the right answer in real code, and writing it "
                               "once is what makes the boundary version legible later",
                       hint="no `== target` branch at all: narrow until lo == hi"),
        ),
    ),
    Method(
        display="FIRST_OCCURRENCE",
        fuzz=("sorted",),
        signature="(nums: list[int], target: int) -> int",
        doc="Index of the FIRST occurrence of `target`, or -1 when absent. "
            "Duplicates are possible.",
        constraint_note="do not stop at the first hit; keep narrowing leftwards",
        constraints=(
            ForbidCall(("index", "bisect_left", "bisect"),
                       because="finding *a* match is the easy half -- a plain binary search "
                               "lands on an arbitrary one of the duplicates",
                       hint="on a hit, record it and continue searching the LEFT half"),
        ),
    ),
    Method(
        display="LAST_OCCURRENCE",
        fuzz=("sorted",),
        signature="(nums: list[int], target: int) -> int",
        doc="Index of the LAST occurrence of `target`, or -1 when absent.",
        constraint_note="the mirror of FIRST_OCCURRENCE; continue rightwards on a hit",
        constraints=(
            ForbidCall(("index", "rindex", "bisect_right", "bisect"),
                       because="the mirror image is worth writing once, because getting it "
                               "wrong is how an off-by-one hides",
                       hint="on a hit, record it and continue searching the RIGHT half"),
        ),
    ),
    Method(
        display="ROTATED_MIN",
        fuzz=("rotated", "unique"),
        signature="(nums: list[int]) -> int",
        doc="The smallest value in an ascending list that has been rotated an unknown "
            "number of times. -1 for an empty list. No duplicates.",
        constraint_note="compare the midpoint to the RIGHT end to decide which half is sorted",
        constraints=(
            ForbidCall(("min", "sorted", "sort", "index"),
                       because="min() is O(n) and ignores the structure -- the list is still "
                               "sorted, just starting in the wrong place, and that is enough "
                               "to halve the range",
                       hint="if nums[mid] > nums[hi] the minimum is to the RIGHT of mid"),
        ),
    ),
    Method(
        display="MIN_CAPACITY",
        fuzz=("positive",),
        signature="(weights: list[int], days: int) -> int",
        doc="The smallest ship capacity that ships every weight within `days` days. "
            "Weights are shipped in the given order and cannot be split or reordered; each "
            "day takes as many as fit. 0 when there are no weights, and -1 when `days` is "
            "less than 1.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Binary search",
                theme="a sorted input, or a monotonic answer"),)

TAG_GLOSSARY = {
    "classic": "the plain search over a sorted list",
    "boundary": "the first or last of several equal values",
    "rotated": "sorted, but starting somewhere in the middle",
    "on-the-answer": "binary searching a value, with no list to search",
    "off-by-one": "loop bounds, and which half to discard",
    "edge-values": "empty inputs, absent targets, single items",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("find_present", "FIND_INDEX", [1, 3, 5, 7], 5, ret=2,
       tags=["classic"], visible=True, doc="Found at index 2."),
    _c("find_absent", "FIND_INDEX", [1, 3, 5], 4, ret=-1,
       tags=["classic", "edge-values"], visible=True, doc="Absent gives -1, not an error."),
    _c("find_first", "FIND_INDEX", [1, 3, 5], 1, ret=0, tags=["classic", "off-by-one"],
       why="the leftmost element must be reachable, which a `lo < hi` loop can miss"),
    _c("find_last", "FIND_INDEX", [1, 3, 5], 5, ret=2, tags=["classic", "off-by-one"],
       why="so must the rightmost"),
    _c("find_single_hit", "FIND_INDEX", [4], 4, ret=0, tags=["classic", "edge-values"]),
    _c("find_single_miss", "FIND_INDEX", [4], 9, ret=-1, tags=["classic", "edge-values"]),
    _c("find_empty", "FIND_INDEX", [], 1, ret=-1, tags=["classic", "edge-values"]),
    _c("find_below_all", "FIND_INDEX", [5, 6], 1, ret=-1, tags=["classic", "edge-values"]),

    _c("insert_middle", "INSERT_POSITION", [1, 3, 5], 4, ret=2,
       tags=["boundary"], visible=True, doc="4 belongs between 3 and 5."),
    _c("insert_present", "INSERT_POSITION", [1, 3, 5], 3, ret=1,
       tags=["boundary"], visible=True,
       doc="Present: the leftmost position it could go is its own index."),
    _c("insert_duplicates", "INSERT_POSITION", [1, 3, 3, 5], 3, ret=1,
       tags=["boundary"], visible=True,
       doc="LEFTmost, so index 1 -- before both 3s, not between them."),
    _c("insert_before_all", "INSERT_POSITION", [2, 4], 1, ret=0,
       tags=["boundary", "off-by-one"]),
    _c("insert_after_all", "INSERT_POSITION", [2, 4], 9, ret=2,
       tags=["boundary", "off-by-one"],
       why="one past the last index is a valid insertion point"),
    _c("insert_empty", "INSERT_POSITION", [], 1, ret=0,
       tags=["boundary", "edge-values"]),

    _c("first_occ_duplicates", "FIRST_OCCURRENCE", [1, 2, 2, 2, 3], 2, ret=1,
       tags=["boundary"], visible=True,
       doc="Three 2s: the first is at index 1. A plain search lands on index 2."),
    _c("first_occ_single", "FIRST_OCCURRENCE", [1, 2, 3], 2, ret=1, tags=["boundary"]),
    _c("first_occ_absent", "FIRST_OCCURRENCE", [1, 3], 2, ret=-1,
       tags=["boundary", "edge-values"], visible=True, doc="Absent gives -1."),
    _c("first_occ_all_same", "FIRST_OCCURRENCE", [2, 2, 2], 2, ret=0,
       tags=["boundary", "edge-values"], visible=True,
       doc="Every element matches, so the answer is index 0."),
    _c("first_occ_at_end", "FIRST_OCCURRENCE", [1, 1, 2], 2, ret=2,
       tags=["boundary", "off-by-one"]),
    # Found by `drill_mutation.py --triage`: two mutants survived every other case here.
    # The target sitting at index 0 of a list that ALSO has duplicates later is the shape
    # that separates them -- [2,2,2] has index 0 but nothing to search past.
    _c("first_occ_at_index_zero", "FIRST_OCCURRENCE", [-1, 0, 2, 2], -1, ret=0,
       tags=["boundary", "off-by-one"], visible=True,
       doc="The target is the very first element, and there are duplicates further "
           "right. Narrowing leftwards must reach index 0 rather than stopping short."),
    _c("first_occ_empty", "FIRST_OCCURRENCE", [], 1, ret=-1,
       tags=["boundary", "edge-values"]),

    _c("last_occ_duplicates", "LAST_OCCURRENCE", [1, 2, 2, 2, 3], 2, ret=3,
       tags=["boundary"], visible=True, doc="The last of the three 2s is at index 3."),
    _c("last_occ_all_same", "LAST_OCCURRENCE", [2, 2, 2], 2, ret=2,
       tags=["boundary", "edge-values"], visible=True,
       doc="Every element matches, so the answer is the final index."),
    _c("last_occ_absent", "LAST_OCCURRENCE", [1, 3], 2, ret=-1,
       tags=["boundary", "edge-values"]),
    _c("last_occ_at_start", "LAST_OCCURRENCE", [1, 2, 2], 1, ret=0,
       tags=["boundary", "off-by-one"]),
    _c("last_occ_single", "LAST_OCCURRENCE", [5], 5, ret=0,
       tags=["boundary", "edge-values"]),
    # Also from triage: the target at the final index of a two-element list. [2,2,2]
    # reaches the last index too, but every element matches, so a mutant that fails to
    # move right still lands on an equal value and looks correct.
    _c("last_occ_two_elements", "LAST_OCCURRENCE", [-1, 2], 2, ret=1,
       tags=["boundary", "off-by-one"], visible=True,
       doc="Two elements, target is the second. The midpoint of [0,1] is 0, so the "
           "search must step right to find it at all."),
    _c("last_occ_empty", "LAST_OCCURRENCE", [], 1, ret=-1,
       tags=["boundary", "edge-values"]),

    _c("rotated_basic", "ROTATED_MIN", [4, 5, 1, 2, 3], ret=1,
       tags=["rotated"], visible=True, doc="Rotated so the minimum sits in the middle."),
    _c("rotated_not_rotated", "ROTATED_MIN", [1, 2, 3], ret=1,
       tags=["rotated", "edge-values"], visible=True,
       doc="A rotation of zero is still a valid input, and the minimum is the first."),
    _c("rotated_by_one", "ROTATED_MIN", [3, 1, 2], ret=1, tags=["rotated"]),
    _c("rotated_min_at_end", "ROTATED_MIN", [2, 3, 1], ret=1,
       tags=["rotated", "off-by-one"],
       why="the minimum being the last element is where a `hi = mid - 1` step overshoots"),
    _c("rotated_single", "ROTATED_MIN", [7], ret=7, tags=["rotated", "edge-values"]),
    _c("rotated_two", "ROTATED_MIN", [2, 1], ret=1, tags=["rotated", "edge-values"]),
    _c("rotated_empty", "ROTATED_MIN", [], ret=-1, tags=["rotated", "edge-values"]),
    _c("rotated_negatives", "ROTATED_MIN", [0, 1, -2, -1], ret=-2,
       tags=["rotated", "edge-values"]),

    _c("capacity_basic", "MIN_CAPACITY", [1, 2, 3], 2, ret=3,
       tags=["checkpoint", "on-the-answer"], visible=True,
       doc="Capacity 3 ships [1,2] then [3]. Capacity 2 would need three days."),
    _c("capacity_one_day", "MIN_CAPACITY", [1, 2, 3], 1, ret=6,
       tags=["checkpoint", "on-the-answer"], visible=True,
       doc="One day means everything at once, so the answer is the total."),
    _c("capacity_many_days", "MIN_CAPACITY", [1, 5, 3], 9, ret=5,
       tags=["checkpoint", "on-the-answer"], visible=True,
       doc="More days than weights: the answer is the LARGEST single weight, because "
           "nothing can be split. This is the lower bound the search must not go below."),
    _c("capacity_exact_fit", "MIN_CAPACITY", [2, 2, 2], 3, ret=2,
       tags=["checkpoint"], why="one weight per day is allowed, so the largest weight suffices"),
    # From triage: every other capacity case tolerated starting the day's load at 1
    # instead of 0, because their answers happened to coincide.
    _c("capacity_uneven", "MIN_CAPACITY", [2, 5, 1], 2, ret=6,
       tags=["checkpoint", "on-the-answer"], visible=True,
       doc="[2] then [5,1] needs 6. Note 6 is neither the largest weight (5) nor the "
           "total (8) -- the answer is genuinely interior to the search range."),
    _c("capacity_empty", "MIN_CAPACITY", [], 3, ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("capacity_zero_days", "MIN_CAPACITY", [1], 0, ret=-1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Zero days cannot ship anything, which is refused rather than answered."),
    # First written as [3,1,1,3] expecting 5, which Gate 1 rejected: the in-order answer
    # there is 4, and the input demonstrated nothing about ordering. [1,4,1] does --
    # in order it needs 5, and shipping the 4 first would need only 4.
    _c("capacity_order_matters", "MIN_CAPACITY", [1, 4, 1], 2, ret=5,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Weights ship in the order given. [1,4] then [1] needs capacity 5; being "
           "allowed to ship the 4 first would have needed only 4."),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="binary_search",
    title="3.1 Binary search",
    blurb="Classic, insert position, first and last occurrence, rotated, and on the answer.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("classic", "boundary", "on-the-answer"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.1 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
