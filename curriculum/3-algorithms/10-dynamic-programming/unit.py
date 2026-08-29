"""3.10 Dynamic programming — overlapping subproblems, solved once.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **overlapping subproblems**: a recursion that would compute the same thing many
times. DP is that recursion with the answers written down.

Two questions get you most of the way, and they are worth asking in this order:

  1. **What is the state?** The smallest description of a subproblem. Usually an index, or
     an index and a remaining budget.
  2. **What is the transition?** How the answer at one state is built from earlier ones.

Everything else -- table or memo, forwards or backwards, one row or two -- is optimisation
after the recurrence is right.

Where a greedy choice IS provably safe, use it instead; unit 3.11 has those. Coin change is
here rather than there precisely because the greedy is wrong for it.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="CLIMB_WAYS",
        fuzz=("nonneg",),
        signature="(steps: int) -> int",
        doc="How many ways to climb `steps` stairs taking 1 or 2 at a time. 1 for zero "
            "steps, being the one way to do nothing. 0 for a negative count.",
        constraint_note="carry two running values; no table and no recursion",
        constraints=(
            Forbid(("recursion",),
                   because="the naive recursion recomputes the same subproblem "
                           "exponentially often; each answer depends only on the two "
                           "before it, so two variables are the whole table",
                   hint="a, b = 1, 1 and roll them forward"),
        ),
    ),
    Method(
        display="HOUSE_ROBBER",
        fuzz=("nonneg",),
        signature="(values: list[int]) -> int",
        doc="The largest total takeable from a row of houses without taking two adjacent "
            "ones. 0 for an empty row. Values are non-negative.",
        constraint_note="at each house: take it plus the best before its neighbour, or skip",
        constraints=(
            Forbid(("recursion",),
                   because="the state is 'the best up to here', and the transition is a "
                           "choice between two earlier states -- the smallest DP there is",
                   hint="take = skip_before + value; skip = max(take_before, skip_before)"),
        ),
    ),
    Method(
        display="COIN_CHANGE",
        fuzz=("positive", "unique"),
        signature="(coins: list[int], amount: int) -> int",
        doc="The fewest coins summing to exactly `amount`, using each denomination as "
            "often as needed. -1 when impossible. 0 for an amount of 0. Denominations are "
            "distinct positive integers.",
        # The standard demonstration that greedy is not enough.
        constraint_note="build up every amount from 0; taking the largest coin first is wrong",
        constraints=(
            Forbid(("recursion",),
                   because="with coins of 1, 3 and 4 making 6, taking the largest first "
                           "gives 4+1+1 -- three coins -- and the answer is 3+3. That is "
                           "why this is DP and not unit 3.11",
                   hint="best[value] = 1 + min(best[value - coin]) over usable coins"),
        ),
    ),
    Method(
        display="LONGEST_INCREASING",
        signature="(nums: list[int]) -> int",
        doc="The length of the longest strictly increasing subsequence, which need NOT be "
            "contiguous. 0 for an empty list.",
        constraint_note="the state is 'longest ending here'; look back at every earlier one",
        constraints=(
            Forbid(("recursion",),
                   because="'subsequence' rather than 'subarray' is the whole difficulty: "
                           "items may be skipped, so a running answer in the Kadane style "
                           "cannot work and the state has to look back at all of them",
                   hint="ending[i] = 1 + max(ending[j] for j < i where nums[j] < nums[i])"),
        ),
    ),
    Method(
        display="EDIT_DISTANCE",
        signature="(source: str, target: str) -> int",
        doc="The fewest single-character insertions, deletions or substitutions turning "
            "`source` into `target`.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Dynamic programming", theme="state, then transition"),)

TAG_GLOSSARY = {
    "rolling": "keeping only the last few answers",
    "choice": "take it or skip it",
    "unbounded": "an item usable any number of times",
    "subsequence": "items chosen in order but not adjacent",
    "grid-dp": "a table indexed by two positions",
    "edge-values": "zero, empty inputs, impossible targets",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("climb_three", "CLIMB_WAYS", 3, ret=3,
       tags=["rolling"], visible=True, doc="1+1+1, 1+2, 2+1."),
    _c("climb_one", "CLIMB_WAYS", 1, ret=1, tags=["rolling", "edge-values"]),
    _c("climb_two", "CLIMB_WAYS", 2, ret=2, tags=["rolling"]),
    _c("climb_zero", "CLIMB_WAYS", 0, ret=1,
       tags=["rolling", "edge-values"], visible=True,
       doc="One way to climb nothing: do nothing. Seeding this as 0 shifts every later "
           "answer by one place."),
    _c("climb_negative", "CLIMB_WAYS", -2, ret=0, tags=["rolling", "edge-values"]),
    _c("climb_ten", "CLIMB_WAYS", 10, ret=89, tags=["rolling"],
       why="Fibonacci, and large enough that an unmemoised recursion is visibly slow"),

    _c("robber_basic", "HOUSE_ROBBER", [2, 7, 9, 3, 1], ret=12,
       tags=["choice"], visible=True, doc="2 + 9 + 1, not 7 + 3."),
    _c("robber_adjacent_biggest", "HOUSE_ROBBER", [2, 1, 1, 2], ret=4,
       tags=["choice"], visible=True,
       doc="The two 2s are not adjacent, so both are takeable."),
    _c("robber_two", "HOUSE_ROBBER", [1, 5], ret=5, tags=["choice", "edge-values"]),
    _c("robber_single", "HOUSE_ROBBER", [7], ret=7, tags=["choice", "edge-values"]),
    _c("robber_empty", "HOUSE_ROBBER", [], ret=0, tags=["choice", "edge-values"]),
    _c("robber_zeros", "HOUSE_ROBBER", [0, 0], ret=0, tags=["choice", "edge-values"]),
    _c("robber_three_middle_best", "HOUSE_ROBBER", [1, 9, 1], ret=9, tags=["choice"],
       why="taking both ends gives 2, and the single middle house beats it"),

    _c("coins_greedy_fails", "COIN_CHANGE", [1, 3, 4], 6, ret=2,
       tags=["unbounded"], visible=True,
       doc="3+3. Taking the largest coin first gives 4+1+1, which is three coins -- this "
           "is the case that rules the greedy out."),
    _c("coins_basic", "COIN_CHANGE", [1, 2, 5], 11, ret=3,
       tags=["unbounded"], visible=True, doc="5+5+1."),
    _c("coins_impossible", "COIN_CHANGE", [2], 3, ret=-1,
       tags=["unbounded", "edge-values"], visible=True, doc="Odd amount, even coin."),
    _c("coins_zero_amount", "COIN_CHANGE", [1], 0, ret=0,
       tags=["unbounded", "edge-values"], visible=True,
       doc="No coins needed, which is 0 rather than -1."),
    _c("coins_exact_single", "COIN_CHANGE", [7], 7, ret=1, tags=["unbounded"]),
    # From triage: no case needed the SAME coin three times over while larger coins
    # were available but unusable.
    _c("coins_repeat_smallest", "COIN_CHANGE", [11, 1, 6], 3, ret=3,
       tags=["unbounded"], visible=True,
       doc="Only the 1 fits, three times. The larger denominations are present and "
           "useless, which a loop that stops at the first unusable coin gets wrong."),
    _c("coins_none", "COIN_CHANGE", [], 5, ret=-1,
       tags=["unbounded", "edge-values"]),
    _c("coins_none_zero", "COIN_CHANGE", [], 0, ret=0,
       tags=["unbounded", "edge-values"],
       why="zero is reachable with no coins even when none are offered"),

    _c("lis_basic", "LONGEST_INCREASING", [10, 9, 2, 5, 3, 7, 101, 18], ret=4,
       tags=["subsequence"], visible=True, doc="2, 3, 7, 101 -- not contiguous."),
    _c("lis_all_equal", "LONGEST_INCREASING", [2, 2, 2], ret=1,
       tags=["subsequence", "edge-values"], visible=True,
       doc="Strictly increasing, so equal values do not extend it."),
    _c("lis_descending", "LONGEST_INCREASING", [5, 4, 3], ret=1,
       tags=["subsequence"], visible=True, doc="Nothing extends anything."),
    _c("lis_ascending", "LONGEST_INCREASING", [1, 2, 3], ret=3, tags=["subsequence"]),
    _c("lis_single", "LONGEST_INCREASING", [7], ret=1,
       tags=["subsequence", "edge-values"]),
    _c("lis_empty", "LONGEST_INCREASING", [], ret=0,
       tags=["subsequence", "edge-values"]),
    _c("lis_skips_a_dip", "LONGEST_INCREASING", [1, 5, 2, 3], ret=3,
       tags=["subsequence"], visible=True,
       doc="1, 2, 3 skips over the 5. A contiguous reading would answer 2."),

    _c("edit_basic", "EDIT_DISTANCE", "horse", "ros", ret=3,
       tags=["checkpoint", "grid-dp"], visible=True,
       doc="Substitute, delete, delete."),
    _c("edit_same", "EDIT_DISTANCE", "abc", "abc", ret=0,
       tags=["checkpoint", "edge-values"], visible=True, doc="Nothing to do."),
    _c("edit_insert_only", "EDIT_DISTANCE", "ab", "abc", ret=1,
       tags=["checkpoint"], visible=True, doc="One insertion."),
    _c("edit_delete_only", "EDIT_DISTANCE", "abc", "ab", ret=1, tags=["checkpoint"]),
    _c("edit_empty_source", "EDIT_DISTANCE", "", "abc", ret=3,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Three insertions -- the first row of the table is 0, 1, 2, 3."),
    _c("edit_empty_target", "EDIT_DISTANCE", "abc", "", ret=3,
       tags=["checkpoint", "edge-values"]),
    _c("edit_both_empty", "EDIT_DISTANCE", "", "", ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("edit_no_overlap", "EDIT_DISTANCE", "abc", "xyz", ret=3,
       tags=["checkpoint"], why="three substitutions beat three deletes and three inserts"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="dynamic_programming",
    title="3.10 Dynamic programming",
    blurb="Climbing stairs, house robber, coin change, LIS and edit distance.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="hard",
    topics=("rolling", "choice", "grid-dp"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.10 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
