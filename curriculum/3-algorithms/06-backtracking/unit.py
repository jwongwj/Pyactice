"""3.6 Backtracking — "all possible", and the undo that makes it affordable.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **"every combination"**, **"all possible"**, or **"is there an arrangement"**.

Every one of these is the same four lines:

    choose a candidate
    if it is still consistent:
        record it, recurse, then UNDO the record
    move on to the next candidate

The undo is what makes it backtracking rather than brute force. It is also where the bugs
are: forgetting it leaves earlier choices contaminating later branches, and copying the
partial answer instead of undoing it turns a linear-space algorithm into an exponential
one.

The second skill is PRUNING -- rejecting a branch before it is finished. n-queens without
pruning enumerates every arrangement; with it, the search collapses.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="SUBSETS",
        signature="(items: list[int]) -> list[list[int]]",
        doc="Every subset, each keeping the input order, the whole list sorted ascending. "
            "Items are distinct.",
        constraint_note="build them by choosing and unchoosing; no itertools",
        constraints=(
            ForbidCall(("combinations", "product", "chain", "powerset"),
                       because="itertools makes this a one-liner, and the point is the "
                               "shape you will need when the choices are constrained and "
                               "no library covers them",
                       hint="at each index, recurse having taken it and having not"),
        ),
    ),
    Method(
        display="PERMUTATIONS",
        signature="(items: list[int]) -> list[list[int]]",
        doc="Every ordering, sorted ascending. Items are distinct.",
        constraint_note="mark used, recurse, unmark; no itertools",
        constraints=(
            ForbidCall(("permutations", "product"),
                       because="the used/unused bookkeeping IS the lesson: it is the same "
                               "structure as n-queens, with a weaker constraint",
                       hint="a `used` set, added to before the recursion and removed after"),
        ),
    ),
    Method(
        display="COMBINATION_SUM",
        fuzz=("positive", "unique"),
        signature="(candidates: list[int], target: int) -> list[list[int]]",
        doc="Every combination of candidates summing to `target`, where each candidate may "
            "be used any number of times. Each combination ascending, the list of them "
            "ascending. Candidates are distinct positive integers.",
        # The pruning drill: once the remainder goes negative, stop.
        constraint_note="prune when the remainder goes below zero; never go backwards",
        constraints=(
            ForbidCall(("combinations", "product", "combinations_with_replacement"),
                       because="the branch that matters is 'reuse this candidate or move "
                               "on', and passing the same index down is what allows "
                               "repeats without producing the same set in two orders",
                       hint="recurse at the SAME index to reuse, at index+1 to move on"),
        ),
    ),
    Method(
        display="PARTITION_EQUAL",
        signature="(nums: list[int]) -> bool",
        doc="Can the values be split into two groups with equal sums? Values are "
            "non-negative. An empty list is True, being two empty groups.",
        fuzz=("nonneg",),
        constraint_note="prune on an odd total before searching at all",
        constraints=(
            ForbidCall(("combinations", "product"),
                       because="an odd total can never split, and checking that first "
                               "avoids the entire search -- recognising a cheap "
                               "impossibility test is half of what pruning is",
                       hint="if the total is odd, return False; otherwise look for a "
                            "subset summing to half"),
        ),
    ),
    Method(
        display="N_QUEENS",
        signature="(size: int) -> int",
        doc="How many ways `size` queens can be placed on a size x size board with no two "
            "sharing a row, column or diagonal. 1 for a size of 0, being the empty "
            "placement. 0 for a negative size.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Backtracking", theme="choose, recurse, undo -- and prune"),)

TAG_GLOSSARY = {
    "choose": "the take-it-or-leave-it branch",
    "undo": "restoring state on the way back out",
    "reuse": "candidates that may be used more than once",
    "prune": "rejecting a branch before it is complete",
    "edge-values": "empty inputs, no solution, sizes of zero",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("subsets_two", "SUBSETS", [1, 2], ret=[[], [1], [1, 2], [2]],
       tags=["choose"], visible=True,
       doc="Four subsets, sorted -- the empty one first."),
    _c("subsets_one", "SUBSETS", [5], ret=[[], [5]], tags=["choose"]),
    _c("subsets_empty", "SUBSETS", [], ret=[[]],
       tags=["choose", "edge-values"], visible=True,
       doc="One subset, and it is empty. Returning [] rather than [[]] is the usual slip."),
    _c("subsets_three", "SUBSETS", [1, 2, 3],
       ret=[[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]],
       tags=["choose"], visible=True, doc="Eight subsets for three items."),

    _c("perms_two", "PERMUTATIONS", [1, 2], ret=[[1, 2], [2, 1]],
       tags=["undo"], visible=True, doc="Two orderings."),
    _c("perms_three", "PERMUTATIONS", [1, 2, 3],
       ret=[[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]],
       tags=["undo"], visible=True,
       doc="Six orderings. A missing undo produces fewer, because a value stays marked "
           "used after its branch is finished."),
    _c("perms_one", "PERMUTATIONS", [7], ret=[[7]], tags=["undo", "edge-values"]),
    _c("perms_empty", "PERMUTATIONS", [], ret=[[]],
       tags=["undo", "edge-values"], visible=True,
       doc="One ordering of nothing, which is the empty ordering."),

    _c("combo_basic", "COMBINATION_SUM", [2, 3], 6, ret=[[2, 2, 2], [3, 3]],
       tags=["reuse"], visible=True, doc="Candidates may repeat."),
    _c("combo_mixed", "COMBINATION_SUM", [2, 3, 5], 8,
       ret=[[2, 2, 2, 2], [2, 3, 3], [3, 5]], tags=["reuse"], visible=True,
       doc="Each combination ascending, and the list of them ascending. [3,2,3] is the "
           "same combination as [2,3,3] and appears once."),
    _c("combo_none", "COMBINATION_SUM", [5], 3, ret=[],
       tags=["reuse", "edge-values"], visible=True, doc="Nothing sums to 3."),
    _c("combo_target_zero", "COMBINATION_SUM", [2], 0, ret=[[]],
       tags=["reuse", "edge-values"], visible=True,
       doc="The empty combination sums to 0, so it is the one answer."),
    _c("combo_exact_single", "COMBINATION_SUM", [4], 4, ret=[[4]], tags=["reuse"]),
    _c("combo_no_candidates", "COMBINATION_SUM", [], 3, ret=[],
       tags=["reuse", "edge-values"]),

    _c("partition_yes", "PARTITION_EQUAL", [1, 5, 11, 5], ret=True,
       tags=["prune"], visible=True, doc="[1,5,5] and [11], both summing to 11."),
    _c("partition_no", "PARTITION_EQUAL", [1, 2, 5], ret=False,
       tags=["prune"], visible=True, doc="A total of 8, and no subset reaches 4."),
    _c("partition_odd_total", "PARTITION_EQUAL", [1, 2], ret=False,
       tags=["prune", "edge-values"], visible=True,
       doc="A total of 3 is odd, so no split exists and the search need not start."),
    _c("partition_empty", "PARTITION_EQUAL", [], ret=True,
       tags=["prune", "edge-values"], visible=True,
       doc="Two empty groups both sum to 0."),
    _c("partition_zeros", "PARTITION_EQUAL", [0, 0], ret=True,
       tags=["prune", "edge-values"]),
    _c("partition_single", "PARTITION_EQUAL", [4], ret=False,
       tags=["prune", "edge-values"],
       why="one value cannot be in both groups, and 4 against 0 is not equal"),

    _c("queens_four", "N_QUEENS", 4, ret=2,
       tags=["checkpoint"], visible=True, doc="The smallest size with a solution above 1."),
    _c("queens_one", "N_QUEENS", 1, ret=1,
       tags=["checkpoint", "edge-values"], visible=True, doc="One queen on one square."),
    _c("queens_two", "N_QUEENS", 2, ret=0,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="No arrangement works on a 2x2 board."),
    _c("queens_three", "N_QUEENS", 3, ret=0, tags=["checkpoint", "edge-values"]),
    _c("queens_zero", "N_QUEENS", 0, ret=1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="An empty board has exactly one arrangement: place nothing."),
    _c("queens_negative", "N_QUEENS", -1, ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("queens_six", "N_QUEENS", 6, ret=4, tags=["checkpoint"],
       why="large enough that an unpruned search is noticeably slower"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="backtracking",
    title="3.6 Backtracking",
    blurb="Subsets, permutations, combination sum, equal partition and n-queens.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="hard",
    topics=("choose", "undo", "prune"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.6 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
