"""3.2 Two pointers — sorted input, and a pair or triple to find.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **a sorted sequence and a question about a pair**. Two indices walking towards
each other turn an O(n^2) scan of every pair into one O(n) pass, and the reason it is
correct is worth stating out loud: at each step you can prove which end cannot be part of
the answer, so discarding it loses nothing.

`two_sum_pairs`, the standalone problem beside this unit, is the unsorted version -- which
wants a dict, not two pointers. Knowing which of the two you are looking at is the skill.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="PAIR_SUM",
        fuzz=("sorted",),
        signature="(nums: list[int], target: int) -> tuple[int, int] | None",
        doc="The (index, index) of two DIFFERENT positions in an ascending list whose "
            "values add to `target`, or None. When several pairs work, the one with the "
            "smallest first index wins.",
        constraint_note="two indices from the ends; no dict and no nested loop",
        constraints=(
            ForbidCall(("dict", "set", "index"),
                       because="a dict solves the UNSORTED version in O(n) memory; sorted "
                               "input buys you the same time in O(1), and forgetting that "
                               "is the whole point of having both questions",
                       hint="lo, hi at the two ends -- if the sum is too small only "
                            "raising lo can help, and vice versa"),
        ),
    ),
    Method(
        display="SORTED_SQUARES",
        fuzz=("sorted",),
        signature="(nums: list[int]) -> list[int]",
        doc="The squares of an ascending list, themselves ascending.",
        # Squaring destroys the order when negatives are present -- and the largest square
        # is always at one END, which is exactly what two pointers exploit.
        constraint_note="fill the answer from the back, taking the bigger end each step",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="re-sorting is O(n log n) and throws away what you were "
                               "given; the largest square is always at one end or the "
                               "other, so the answer can be filled back to front in O(n)",
                       hint="compare abs(nums[lo]) with abs(nums[hi])"),
        ),
    ),
    Method(
        display="MOST_WATER",
        signature="(heights: list[int]) -> int",
        doc="The largest area between two lines: the distance between them times the "
            "shorter of the two. 0 when there are fewer than two lines.",
        constraint_note="two pointers from the ends; always move the SHORTER one inwards",
        constraints=(
            Forbid(("comprehension",),
                   because="every pair is O(n^2); moving the shorter line inwards is "
                           "O(n), and is correct because the shorter line caps the area "
                           "for every pairing it is part of -- so nothing is lost",
                   hint="move whichever side is shorter; moving the taller one can only "
                        "narrow the width without raising the cap"),
        ),
    ),
    Method(
        display="THREE_SUM",
        fuzz=("sorted",),
        signature="(nums: list[int]) -> list[tuple[int, int, int]]",
        doc="Every distinct triple of values from an ascending list that sums to 0, each "
            "triple ascending, the list of triples ascending. Values may be reused only "
            "as often as they appear.",
        constraint_note="fix one value, then two pointers on the rest; skip duplicates",
        constraints=(
            ForbidCall(("combinations", "permutations", "product"),
                       because="itertools makes this a one-liner and an O(n^3) one; the "
                               "point is the outer loop plus an inner two-pointer sweep",
                       hint="for each index i, run PAIR_SUM's sweep over nums[i+1:] "
                            "looking for -nums[i]"),
        ),
    ),
    Method(
        display="SORT_COLORS",
        fuzz=("colors",),
        signature="(values: list[int]) -> list[int]",
        doc="Sort a list containing only 0, 1 and 2 in ONE pass. The Dutch national flag "
            "problem.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Two pointers", theme="prove which end cannot matter, then discard it"),)

TAG_GLOSSARY = {
    "converge": "two indices walking towards each other",
    "duplicates": "skipping repeats so an answer is reported once",
    "ordering": "the order of the answer, and of what is inside it",
    "partition": "moving items into regions in one pass",
    "edge-values": "empty inputs, one item, no answer, all equal",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("pair_found", "PAIR_SUM", [1, 3, 5, 7], 8, ret=(0, 3),
       tags=["converge"], visible=True, doc="1 + 7. Indices, not values."),
    _c("pair_middle", "PAIR_SUM", [1, 2, 3, 4], 5, ret=(0, 3),
       tags=["converge", "ordering"], visible=True,
       doc="Both (0,3) and (1,2) sum to 5, and the smallest first index wins."),
    _c("pair_none", "PAIR_SUM", [1, 2], 99, ret=None,
       tags=["converge", "edge-values"], visible=True, doc="No pair works."),
    _c("pair_negatives", "PAIR_SUM", [-3, -1, 2], -4, ret=(0, 1), tags=["converge"]),
    _c("pair_duplicates", "PAIR_SUM", [2, 2], 4, ret=(0, 1),
       tags=["converge", "duplicates"],
       why="two equal values at different positions are two different positions"),
    # From triage: every other answer here involves index 0 or the final index, so a
    # sweep that stops early still found them. This pair is strictly interior.
    _c("pair_interior", "PAIR_SUM", [-4, 0, 3, 8], 3, ret=(1, 2),
       tags=["converge"], visible=True,
       doc="Neither end is part of the answer, so both pointers have to move inwards "
           "before it is found."),
    _c("pair_single", "PAIR_SUM", [4], 8, ret=None,
       tags=["converge", "edge-values"],
       why="one item cannot pair with itself"),
    _c("pair_empty", "PAIR_SUM", [], 0, ret=None, tags=["converge", "edge-values"]),

    _c("squares_all_positive", "SORTED_SQUARES", [1, 2, 3], ret=[1, 4, 9],
       tags=["converge"], visible=True, doc="Already in order."),
    _c("squares_with_negatives", "SORTED_SQUARES", [-4, -1, 0, 3], ret=[0, 1, 9, 16],
       tags=["converge"], visible=True,
       doc="Squaring destroys the order: -4 squares to the LARGEST value despite being "
           "first. The biggest square is always at one end or the other."),
    _c("squares_all_negative", "SORTED_SQUARES", [-3, -2], ret=[4, 9],
       tags=["converge", "edge-values"], visible=True,
       doc="All negative, so the order reverses completely."),
    _c("squares_single", "SORTED_SQUARES", [-5], ret=[25],
       tags=["converge", "edge-values"]),
    _c("squares_empty", "SORTED_SQUARES", [], ret=[], tags=["converge", "edge-values"]),
    _c("squares_zero", "SORTED_SQUARES", [-1, 0, 1], ret=[0, 1, 1], tags=["converge"],
       why="two different values can square to the same thing"),

    _c("water_basic", "MOST_WATER", [1, 8, 6, 2, 5, 4, 8, 3, 7], ret=49,
       tags=["converge"], visible=True,
       doc="The lines at index 1 (height 8) and index 8 (height 7) are seven apart and "
           "capped at 7, giving 49. Note the winning pair is not the two tallest lines."),
    _c("water_two_lines", "MOST_WATER", [1, 1], ret=1,
       tags=["converge"], visible=True, doc="One apart, capped at 1."),
    _c("water_tall_narrow_vs_short_wide", "MOST_WATER", [9, 1, 1, 9], ret=27,
       tags=["converge"], visible=True,
       doc="The two 9s are three apart for 27, which beats any adjacent pairing."),
    _c("water_one_line", "MOST_WATER", [5], ret=0, tags=["converge", "edge-values"]),
    _c("water_empty", "MOST_WATER", [], ret=0, tags=["converge", "edge-values"]),
    _c("water_zeros", "MOST_WATER", [0, 0], ret=0, tags=["converge", "edge-values"]),
    _c("water_descending", "MOST_WATER", [4, 3, 2, 1], ret=4, tags=["converge"],
       why="the widest pair is capped at 1 for an area of 3; indices 0 and 2, capped at "
           "2 and two apart, beat it with 4"),

    _c("three_sum_basic", "THREE_SUM", [-1, 0, 1, 2], ret=[(-1, 0, 1)],
       tags=["converge", "duplicates"], visible=True,
       doc="One triple sums to zero."),
    _c("three_sum_two_triples", "THREE_SUM", [-2, -1, 0, 1, 2],
       ret=[(-2, 0, 2), (-1, 0, 1)], tags=["converge", "ordering"], visible=True,
       doc="Two triples, each ascending, and the list of them ascending."),
    _c("three_sum_duplicate_values", "THREE_SUM", [-1, -1, 0, 1, 1],
       ret=[(-1, 0, 1)], tags=["converge", "duplicates"], visible=True,
       doc="The same triple is reachable four ways and is reported ONCE. Skipping "
           "repeats is the fiddly half of this problem."),
    _c("three_sum_all_zero", "THREE_SUM", [0, 0, 0], ret=[(0, 0, 0)],
       tags=["converge", "duplicates"], visible=True,
       doc="Three zeros are a valid triple; a fourth zero would not add a second one."),
    _c("three_sum_triple_duplicate", "THREE_SUM", [-1, -1, -1, 2], ret=[(-1, -1, 2)],
       tags=["converge", "duplicates"], visible=True,
       doc="Three equal values and one other. Skipping duplicates has to advance past "
           "ALL the repeats, not one of them, or the sweep never makes progress."),
    _c("three_sum_none", "THREE_SUM", [1, 2, 3], ret=[],
       tags=["converge", "edge-values"]),
    _c("three_sum_too_short", "THREE_SUM", [0, 0], ret=[],
       tags=["converge", "edge-values"]),
    _c("three_sum_empty", "THREE_SUM", [], ret=[], tags=["converge", "edge-values"]),

    _c("colors_mixed", "SORT_COLORS", [2, 0, 1], ret=[0, 1, 2],
       tags=["checkpoint", "partition"], visible=True, doc="One pass, three regions."),
    _c("colors_longer", "SORT_COLORS", [2, 0, 2, 1, 1, 0], ret=[0, 0, 1, 1, 2, 2],
       tags=["checkpoint", "partition"], visible=True, doc="Counts preserved."),
    # From triage: no case here has a 1 that must travel to the END. The three-way
    # partition leaves 1s in the middle, and when there are no 2s the middle IS the end.
    _c("colors_one_travels_right", "SORT_COLORS", [0, 1, 0, 0], ret=[0, 0, 0, 1],
       tags=["checkpoint", "partition"], visible=True,
       doc="A single 1 among 0s has to end up last. Every 0 swapped forward pushes it "
           "along, which is what the middle pointer is for."),
    _c("colors_already", "SORT_COLORS", [0, 1, 2], ret=[0, 1, 2],
       tags=["checkpoint", "partition"]),
    _c("colors_all_same", "SORT_COLORS", [1, 1], ret=[1, 1],
       tags=["checkpoint", "edge-values"]),
    _c("colors_missing_value", "SORT_COLORS", [2, 0], ret=[0, 2],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A colour that never appears must not appear in the answer either."),
    _c("colors_empty", "SORT_COLORS", [], ret=[], tags=["checkpoint", "edge-values"]),
    _c("colors_reversed", "SORT_COLORS", [2, 2, 1, 1, 0, 0], ret=[0, 0, 1, 1, 2, 2],
       tags=["checkpoint", "partition"],
       why="the worst arrangement, where every element has to move"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="two_pointers",
    title="3.2 Two pointers",
    blurb="Converging indices: pair sums, sorted squares, most water, three-sum.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("converge", "duplicates", "partition"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.2 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
