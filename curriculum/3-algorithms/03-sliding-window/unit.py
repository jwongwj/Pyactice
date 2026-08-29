"""3.3 Sliding window — "contiguous", plus "longest" or "shortest".

Self-contained: loaded by file path, so no package-relative imports.

Two shapes, and telling them apart is most of the skill:

  * a FIXED window, where you add the arrival and remove the departure each step;
  * a VARIABLE window, where the right edge always advances and the left edge catches up
    only while the window is invalid.

The variable form only works when validity is monotonic -- when growing the window can
only ever make it worse and shrinking can only ever help. With negative numbers that stops
being true, which is why "subarray sums to k" belongs to prefix sums (3.13) and not here.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="MAX_SUM_K",
        signature="(nums: list[int], k: int) -> int",
        doc="The largest sum of k consecutive values. 0 when k is less than 1 or larger "
            "than the list.",
        constraint_note="one running sum; do not re-add the window each step",
        constraints=(
            ForbidCall(("sum",),
                       because="sum(nums[i:i+k]) per position re-reads the whole window "
                               "every time, which is O(n*k); adding the arrival and "
                               "subtracting the departure is O(n)",
                       hint="build the first window, then slide: total += nums[i] - "
                            "nums[i - k]"),
        ),
    ),
    Method(
        display="LONGEST_UNIQUE",
        signature="(text: str) -> int",
        doc="The length of the longest run of characters with no repeat inside it.",
        constraint_note="grow right, and pull left in only while the window is invalid",
        constraints=(
            Forbid(("comprehension",),
                   because="checking every substring is O(n^2) at best; the window never "
                           "moves backwards, so each character is visited twice at most",
                   hint="a set of what is in the window; on a repeat, drop from the left "
                        "until the repeat is gone"),
        ),
    ),
    Method(
        display="LONGEST_ONES",
        fuzz=("binary",),
        signature="(bits: list[int], flips: int) -> int",
        doc="The longest run of 1s you can make by turning at most `flips` zeros into "
            "ones. Values are 0 or 1.",
        # The same window, with "how many zeros are inside" as the validity test.
        constraint_note="the window is valid while it holds at most `flips` zeros",
        constraints=(
            Forbid(("comprehension",),
                   because="this is LONGEST_UNIQUE with a different validity test, and "
                           "recognising that is the drill",
                   hint="count zeros in the window; while there are too many, advance "
                        "the left edge"),
        ),
    ),
    Method(
        display="ANAGRAM_STARTS",
        signature="(text: str, pattern: str) -> list[int]",
        doc="Every start index where a window of len(pattern) characters is an anagram of "
            "`pattern`. Empty when `pattern` is empty or longer than `text`.",
        constraint_note="a fixed window over counts; do not rebuild a Counter per position",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="sorting each window is O(n * m log m); the window's letter "
                               "counts can be updated in O(1) per step and compared whole",
                       hint="one Counter for the pattern, one for the window, add the "
                            "arrival and remove the departure -- and delete keys that "
                            "reach zero, or the dicts never compare equal"),
        ),
    ),
    Method(
        display="MIN_WINDOW",
        signature="(text: str, needed: str) -> str",
        doc="The shortest slice of `text` containing every character of `needed`, counting "
            "repeats. Empty when there is none. When two are equally short, the one "
            "starting earliest wins.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Sliding window", theme="contiguous, and longest or shortest"),)

TAG_GLOSSARY = {
    "fixed": "a window of a known size",
    "variable": "a window that grows and shrinks by validity",
    "counts": "comparing what is inside the window against what is needed",
    "shrink": "when the left edge is allowed to advance",
    "edge-values": "empty inputs, k out of range, no answer",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("max_sum_basic", "MAX_SUM_K", [1, 5, 2, 3], 2, ret=7,
       tags=["fixed"], visible=True, doc="1+5 = 6, 5+2 = 7, 2+3 = 5."),
    _c("max_sum_whole", "MAX_SUM_K", [1, 2], 2, ret=3, tags=["fixed"]),
    _c("max_sum_k_too_big", "MAX_SUM_K", [1, 2], 5, ret=0,
       tags=["fixed", "edge-values"], visible=True, doc="No window of that size exists."),
    _c("max_sum_k_zero", "MAX_SUM_K", [1, 2], 0, ret=0, tags=["fixed", "edge-values"]),
    _c("max_sum_negatives", "MAX_SUM_K", [-5, -1, -3], 2, ret=-4,
       tags=["fixed", "edge-values"], visible=True,
       doc="All negative: the answer is the least bad window, not 0."),
    _c("max_sum_single_negative", "MAX_SUM_K", [-3], 1, ret=-3,
       tags=["fixed", "edge-values"], visible=True,
       doc="One window, and it is negative. Starting `best` at 0 rather than at the "
           "first window's total answers 0 here."),
    _c("max_sum_empty", "MAX_SUM_K", [], 1, ret=0, tags=["fixed", "edge-values"]),
    _c("max_sum_first_is_best", "MAX_SUM_K", [9, 1, 1], 2, ret=10, tags=["fixed"],
       why="the best window is the first one, which a 'strictly better' update misses"),

    _c("unique_basic", "LONGEST_UNIQUE", "abcabcbb", ret=3,
       tags=["variable"], visible=True, doc='"abc" -- the run resets at each repeat.'),
    _c("unique_all_same", "LONGEST_UNIQUE", "bbbb", ret=1,
       tags=["variable", "edge-values"], visible=True, doc="One character at a time."),
    _c("unique_no_repeats", "LONGEST_UNIQUE", "abcd", ret=4, tags=["variable"]),
    _c("unique_repeat_far_back", "LONGEST_UNIQUE", "abba", ret=2,
       tags=["variable", "shrink"], visible=True,
       doc='At the final "a" the left edge must not jump back to index 1 -- it only ever '
           'moves forward, so the answer is "ab" or "ba", not "abba" minus one.'),
    _c("unique_empty", "LONGEST_UNIQUE", "", ret=0, tags=["variable", "edge-values"]),
    _c("unique_single", "LONGEST_UNIQUE", "z", ret=1, tags=["variable", "edge-values"]),

    _c("ones_basic", "LONGEST_ONES", [1, 0, 1, 1, 0], 1, ret=4,
       tags=["variable"], visible=True, doc="Flip one zero to join a run of four."),
    _c("ones_no_flips", "LONGEST_ONES", [1, 0, 1, 1], 0, ret=2,
       tags=["variable", "edge-values"], visible=True,
       doc="With no flips this is simply the longest existing run."),
    _c("ones_all_zero", "LONGEST_ONES", [0, 0, 0], 2, ret=2,
       tags=["variable", "edge-values"], visible=True,
       doc="Only as many as you may flip."),
    _c("ones_flips_exceed", "LONGEST_ONES", [0, 0], 9, ret=2,
       tags=["variable", "edge-values"],
       why="more flips than zeros wins the whole list, not more than its length"),
    _c("ones_flips_exceed_mixed", "LONGEST_ONES", [1, 0, 1], 2, ret=3,
       tags=["variable", "edge-values"], visible=True,
       doc="More flips than zeros, in a list that also has ones. The answer is the whole "
           "list -- it cannot exceed the length, which an unbounded window would."),
    _c("ones_all_ones", "LONGEST_ONES", [1, 1], 1, ret=2, tags=["variable"]),
    _c("ones_empty", "LONGEST_ONES", [], 1, ret=0, tags=["variable", "edge-values"]),

    _c("anagram_basic", "ANAGRAM_STARTS", "cbaebabacd", "abc", ret=[0, 6],
       tags=["counts", "fixed"], visible=True, doc='"cba" at 0 and "bac" at 6.'),
    _c("anagram_overlapping", "ANAGRAM_STARTS", "abab", "ab", ret=[0, 1, 2],
       tags=["counts", "fixed"], visible=True, doc="Windows may overlap."),
    _c("anagram_repeated_letters", "ANAGRAM_STARTS", "aab", "aab", ret=[0],
       tags=["counts", "edge-values"], visible=True,
       doc='Repeats count: "ab" is not an anagram of "aab", so a set of letters is not '
           "enough -- the counts have to match."),
    _c("anagram_none", "ANAGRAM_STARTS", "abc", "xyz", ret=[],
       tags=["counts", "edge-values"]),
    _c("anagram_pattern_longer", "ANAGRAM_STARTS", "ab", "abc", ret=[],
       tags=["counts", "edge-values"]),
    _c("anagram_empty_pattern", "ANAGRAM_STARTS", "abc", "", ret=[],
       tags=["counts", "edge-values"]),
    _c("anagram_whole_string", "ANAGRAM_STARTS", "ba", "ab", ret=[0],
       tags=["counts", "edge-values"]),

    _c("min_window_basic", "MIN_WINDOW", "ADOBECODEBANC", "ABC", ret="BANC",
       tags=["checkpoint"], visible=True,
       doc="The shortest slice holding an A, a B and a C."),
    _c("min_window_repeats_needed", "MIN_WINDOW", "aab", "aa", ret="aa",
       tags=["checkpoint", "counts"], visible=True,
       doc='Two "a"s are needed, so a window with one does not qualify.'),
    _c("min_window_whole", "MIN_WINDOW", "abc", "abc", ret="abc",
       tags=["checkpoint"]),
    _c("min_window_none", "MIN_WINDOW", "abc", "xyz", ret="",
       tags=["checkpoint", "edge-values"], visible=True, doc="Not present at all."),
    _c("min_window_earliest_of_equals", "MIN_WINDOW", "abxab", "ab", ret="ab",
       tags=["checkpoint", "edge-values"], visible=True,
       doc='Two windows are both two characters long, and the earlier one wins.'),
    _c("min_window_shrinks_past_spare", "MIN_WINDOW", "aab", "ab", ret="ab",
       tags=["checkpoint", "shrink"], visible=True,
       doc='The first "a" is spare once the second is inside the window, so the left edge '
           'must keep advancing after the window first becomes valid. Stopping at the '
           'first valid window gives "aab".'),
    _c("min_window_empty_needed", "MIN_WINDOW", "abc", "", ret="",
       tags=["checkpoint", "edge-values"]),
    _c("min_window_empty_text", "MIN_WINDOW", "", "a", ret="",
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="sliding_window",
    title="3.3 Sliding window",
    blurb="Fixed and variable windows: max sum, longest unique, flips, anagrams.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("fixed", "variable", "counts"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.3 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
