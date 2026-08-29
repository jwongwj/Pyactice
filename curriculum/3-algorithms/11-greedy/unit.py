"""3.11 Greedy — a locally safe choice, provably.

Self-contained: loaded by file path, so no package-relative imports.

Greedy is the easiest family to write and the hardest to justify. The algorithm is always
"take the best-looking option now and never reconsider"; the work is showing that doing so
cannot cost you the optimum. Where that argument fails, the same problem needs dynamic
programming (3.10) instead -- coin change with arbitrary denominations is the standard
example, and taking the largest coin first is the standard wrong answer.

Every drill here carries the exchange argument in its LESSON. If you cannot state why the
local choice is safe, you have guessed rather than solved it.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="CAN_JUMP",
        fuzz=("nonneg",),
        signature="(jumps: list[int]) -> bool",
        doc="Starting at index 0, where each value is the FURTHEST you may jump from that "
            "index, can the last index be reached? An empty list is False; a single "
            "index is True, being already there.",
        constraint_note="carry the furthest reachable index; one pass, no recursion",
        constraints=(
            Forbid(("recursion",),
                   because="trying every jump is exponential; the only thing that matters "
                           "at each step is how far you could get in total, which is one "
                           "running maximum",
                   hint="if index > furthest you are stuck; otherwise furthest = "
                        "max(furthest, index + jumps[index])"),
        ),
    ),
    Method(
        display="MIN_JUMPS",
        fuzz=("nonneg",),
        signature="(jumps: list[int]) -> int",
        doc="The fewest jumps to reach the last index, under the same rule. -1 when it "
            "cannot be reached. 0 for a single index.",
        # The greedy is subtle: you jump only when you run out of the CURRENT range.
        constraint_note="track the end of the current range and the furthest seen; one pass",
        constraints=(
            Forbid(("recursion",),
                   because="this is a breadth-first search that never needs a queue: "
                           "everything reachable in n jumps is a contiguous range, so the "
                           "ranges can be tracked with two integers",
                   hint="when index reaches the end of the current range, take a jump and "
                        "the new range ends at the furthest you had seen"),
        ),
    ),
    Method(
        display="GAS_STATION",
        fuzz=("paired-lists",),
        signature="(gas: list[int], cost: list[int]) -> int",
        doc="The index to start a circular route from so that the tank never goes "
            "negative, or -1 when no start works. `cost[i]` is the fuel used going from i "
            "to i+1, and the two lists are the same length. When several starts work, the "
            "smallest index wins.",
        constraint_note="one pass; when the tank goes negative, restart AFTER the failure",
        constraints=(
            Forbid(("comprehension",),
                   because="trying every start is O(n^2). If the tank dies between i and "
                           "j, then no index in between works either -- so the search can "
                           "skip straight past all of them",
                   hint="total tells you whether ANY start works; a running tank tells "
                        "you where to restart"),
        ),
    ),
    Method(
        display="MAX_MEETINGS",
        fuzz=("ordered-pairs",),
        signature="(meetings: list[tuple[int, int]]) -> int",
        doc="The most meetings that fit in one room without overlapping. A meeting ending "
            "at t and one starting at t may both be kept.",
        constraint_note="sort by END and take whatever still fits",
        constraints=(
            ForbidCall(("heappush", "heappop"),
                       because="the interval finishing soonest leaves the most room for "
                               "everything after it -- that is the exchange argument, and "
                               "it is why the END is the sort key rather than the start",
                       hint="sort by end; keep a meeting when it starts at or after the "
                            "last kept end"),
        ),
    ),
    Method(
        display="MIN_PLATFORMS",
        fuzz=("paired-ordered",),
        signature="(arrivals: list[int], departures: list[int]) -> int",
        doc="The fewest platforms a station needs, given a train's arrival and departure "
            "at the same index; the two lists are the same length and every train "
            "departs strictly after it arrives. A train departing at t "
            "frees its platform before one arriving at t takes it. 0 when there are no "
            "trains.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Greedy", theme="take the safe local choice, and be able to say why"),)

TAG_GLOSSARY = {
    "reach": "how far you can get, carried as a running maximum",
    "restart": "proving a whole prefix can be skipped",
    "exchange": "why the locally best choice cannot cost the optimum",
    "sweep": "walking two sorted sequences at once",
    "edge-values": "empty inputs, single items, unreachable targets, zeros",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("jump_reachable", "CAN_JUMP", [2, 3, 1, 1, 4], ret=True,
       tags=["reach"], visible=True, doc="2 to index 1, then 3 clears the rest."),
    _c("jump_blocked", "CAN_JUMP", [3, 2, 1, 0, 4], ret=False,
       tags=["reach"], visible=True,
       doc="Every route lands on the 0 at index 3 and stops there."),
    _c("jump_single", "CAN_JUMP", [0], ret=True,
       tags=["reach", "edge-values"], visible=True,
       doc="Already at the last index, so no jump is needed and a 0 does not matter."),
    _c("jump_leading_zero", "CAN_JUMP", [0, 1], ret=False,
       tags=["reach", "edge-values"], visible=True,
       doc="A 0 at the start, with somewhere still to go."),
    _c("jump_empty", "CAN_JUMP", [], ret=False, tags=["reach", "edge-values"]),
    _c("jump_exact", "CAN_JUMP", [1, 1, 0], ret=True, tags=["reach"],
       why="landing exactly on the last index counts, and the 0 there is irrelevant"),

    _c("min_jumps_basic", "MIN_JUMPS", [2, 3, 1, 1, 4], ret=2,
       tags=["reach"], visible=True, doc="Index 0 to 1, then 1 to the end."),
    _c("min_jumps_single", "MIN_JUMPS", [0], ret=0,
       tags=["reach", "edge-values"], visible=True, doc="Already there."),
    _c("min_jumps_unreachable", "MIN_JUMPS", [1, 0, 1], ret=-1,
       tags=["reach", "edge-values"], visible=True, doc="Stuck at index 1."),
    _c("min_jumps_one_hop", "MIN_JUMPS", [9, 1, 1], ret=1, tags=["reach"],
       why="one jump can clear the whole list, so the answer is not the length"),
    _c("min_jumps_step_by_step", "MIN_JUMPS", [1, 1, 1], ret=2, tags=["reach"]),
    # Four gaps from `drill_mutation.py --triage`, all about SHORT lists: every case here
    # was either length 1 or length 3+, so the two-element boundary went untested in both
    # the reachable and the stuck direction.
    _c("min_jumps_two", "MIN_JUMPS", [1, 2], ret=1,
       tags=["reach", "edge-values"], visible=True,
       doc="Two indices, one jump. The loop must stop before the last index rather than "
           "taking a jump from it."),
    _c("min_jumps_two_stuck", "MIN_JUMPS", [0, 4], ret=-1,
       tags=["reach", "edge-values"], visible=True,
       doc="A leading 0 with somewhere to go, at the shortest length that can fail."),
    _c("min_jumps_stuck_longer", "MIN_JUMPS", [0, 4, 9], ret=-1,
       tags=["reach", "edge-values"],
       why="the failure sentinel must be -1 and not some other negative"),
    _c("min_jumps_over_a_zero", "MIN_JUMPS", [2, 0, 3, 4], ret=2,
       tags=["reach"], visible=True,
       doc="The 0 at index 1 is jumped OVER rather than landed on, so the route survives."),
    _c("min_jumps_empty", "MIN_JUMPS", [], ret=-1, tags=["reach", "edge-values"]),

    _c("gas_basic", "GAS_STATION", [1, 2, 3, 4, 5], [3, 4, 5, 1, 2], ret=3,
       tags=["restart"], visible=True, doc="Starting at 3 is the only route that survives."),
    _c("gas_impossible", "GAS_STATION", [2, 3], [4, 4], ret=-1,
       tags=["restart"], visible=True,
       doc="Total cost exceeds total gas, so no start can work."),
    _c("gas_smallest_index_wins", "GAS_STATION", [3, 3], [3, 3], ret=0,
       tags=["restart", "edge-values"], visible=True,
       doc="Both starts work, and the smaller index is the answer."),
    _c("gas_single_ok", "GAS_STATION", [5], [3], ret=0,
       tags=["restart", "edge-values"]),
    _c("gas_single_bad", "GAS_STATION", [1], [3], ret=-1,
       tags=["restart", "edge-values"]),
    # Three from triage. The existing cases were length 5, 2, 2 and 1 with a large
    # shortfall; none had the answer at the LAST index, and none had a tank that dipped
    # by exactly one -- the value that separates `tank < 0` from `tank < -1`.
    _c("gas_answer_at_last", "GAS_STATION", [1, 3, 5], [3, 4, 1], ret=2,
       tags=["restart"], visible=True,
       doc="Only the final index works, so the restart has to survive two failures."),
    _c("gas_answer_in_middle", "GAS_STATION", [3, 3, 4], [4, 3, 3], ret=1,
       tags=["restart"], visible=True, doc="The first station fails and the second works."),
    _c("gas_short_by_one", "GAS_STATION", [4], [5], ret=-1,
       tags=["restart", "edge-values"], visible=True,
       doc="The tank ends at exactly -1. Any threshold looser than 'below zero' accepts "
           "this route, and it does not work."),
    _c("gas_empty", "GAS_STATION", [], [], ret=-1, tags=["restart", "edge-values"]),
    _c("gas_exact", "GAS_STATION", [1, 2], [2, 1], ret=1,
       tags=["restart"], visible=True,
       doc="The tank ends at exactly zero, which is allowed -- it may not go BELOW zero."),

    _c("meetings_basic", "MAX_MEETINGS", [(1, 3), (2, 4), (3, 5)], ret=2,
       tags=["exchange"], visible=True, doc="(1,3) and (3,5) -- touching is allowed."),
    _c("meetings_greedy_by_end", "MAX_MEETINGS", [(1, 100), (2, 3), (3, 4)], ret=2,
       tags=["exchange"], visible=True,
       doc="Taking the earliest-STARTING meeting keeps (1,100) and fits nothing else, "
           "for 1. Taking the earliest-ENDING keeps two."),
    _c("meetings_none_overlap", "MAX_MEETINGS", [(1, 2), (3, 4)], ret=2,
       tags=["exchange"]),
    _c("meetings_all_identical", "MAX_MEETINGS", [(1, 5), (1, 5)], ret=1,
       tags=["exchange", "edge-values"], visible=True,
       doc="Two identical meetings, and only one can be kept."),
    _c("meetings_single", "MAX_MEETINGS", [(1, 2)], ret=1,
       tags=["exchange", "edge-values"]),
    _c("meetings_empty", "MAX_MEETINGS", [], ret=0, tags=["exchange", "edge-values"]),

    _c("platforms_basic", "MIN_PLATFORMS", [1, 3, 5], [4, 6, 7], ret=2,
       tags=["checkpoint", "sweep"], visible=True,
       doc="The first two trains overlap; the third arrives after the first has gone."),
    _c("platforms_none_overlap", "MIN_PLATFORMS", [1, 5], [2, 6], ret=1,
       tags=["checkpoint", "sweep"], visible=True, doc="One at a time."),
    _c("platforms_touching", "MIN_PLATFORMS", [1, 2], [2, 3], ret=1,
       tags=["checkpoint", "sweep"], visible=True,
       doc="One departs exactly as the next arrives, so a single platform serves both."),
    _c("platforms_all_at_once", "MIN_PLATFORMS", [1, 1, 1], [9, 9, 9], ret=3,
       tags=["checkpoint", "sweep"], visible=True, doc="Three at once."),
    _c("platforms_two_share_a_start", "MIN_PLATFORMS", [1, -1, 1], [5, 0, 2], ret=2,
       tags=["checkpoint", "sweep"], visible=True,
       doc="Two trains arrive at the same instant and a third has already gone. Given "
           "out of order, so the pairing is by index and not by position in time."),
    _c("platforms_unsorted", "MIN_PLATFORMS", [5, 1], [6, 2], ret=1,
       tags=["checkpoint", "edge-values"],
       why="the two lists are paired by index and are not necessarily in time order"),
    # From triage: every case here had either all trains overlapping or none, so a
    # partial overlap that never reaches the full count went untested.
    _c("platforms_partial_overlap", "MIN_PLATFORMS", [-1, 0, 1, 3], [1, 2, 7, 7], ret=2,
       tags=["checkpoint", "sweep"], visible=True,
       doc="Four trains, never more than two at once. The answer is neither 1 nor the "
           "number of trains, so an off-by-one in the running count shows up here."),
    _c("platforms_single", "MIN_PLATFORMS", [1], [2], ret=1,
       tags=["checkpoint", "edge-values"]),
    _c("platforms_empty", "MIN_PLATFORMS", [], [], ret=0,
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="greedy",
    title="3.11 Greedy",
    blurb="Jump game, minimum jumps, gas station, interval scheduling and platforms.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("reach", "exchange", "sweep"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.11 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
