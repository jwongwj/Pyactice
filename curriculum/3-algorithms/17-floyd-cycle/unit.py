"""3.17 Floyd cycle detection — a cycle in O(1) space.

Self-contained: loaded by file path, so no package-relative imports.

Unit 2.8 uses the tortoise and hare to answer *is there a cycle*. This unit is the rest of
what the technique gives you, and the reason it is worth knowing rather than reaching for a
set:

  * WHERE the cycle begins, which needs the second phase and a small piece of algebra;
  * how LONG it is;
  * and the disguised version -- "find the duplicate number" -- where there is no linked
    list at all and the cycle exists only in a function from index to index.

That last one is the point of the unit. Recognising a cycle problem when there are no
pointers in sight is the skill; the loop itself is six lines.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="CYCLE_LENGTH",
        signature="(nexts: list[int]) -> int",
        doc="`nexts[i]` is the position you move to from i, always a valid index. Starting "
            "at 0, how many positions are in the cycle you eventually enter? 0 for an "
            "empty list.",
        constraint_note="meet with two speeds, then walk one lap; no set of seen positions",
        constraints=(
            ForbidCall(("set", "dict", "index", "count"),
                       because="remembering every position visited is O(n) memory and is "
                               "the answer this technique exists to improve on",
                       hint="once slow and fast meet, keep one still and walk the other "
                            "until it comes back"),
        ),
    ),
    Method(
        display="CYCLE_START",
        signature="(nexts: list[int]) -> int",
        doc="The index where the cycle begins, starting from 0. Every position leads "
            "somewhere, so a cycle always exists. -1 for an empty list.",
        # The second phase: after the meeting, one pointer restarts at the beginning and
        # both move at the same speed. Where they meet is the entrance.
        constraint_note="after they meet, restart one at 0 and move both one step at a time",
        constraints=(
            ForbidCall(("set", "dict", "index"),
                       because="the second phase is the part worth knowing: the distance "
                               "from the start to the entrance equals the distance from "
                               "the meeting point to the entrance, going round",
                       hint="slow stays where they met, a new pointer starts at 0, and "
                            "they meet at the entrance"),
        ),
    ),
    Method(
        display="FIND_DUPLICATE",
        signature="(nums: list[int]) -> int",
        doc="A list of n+1 values, each between 1 and n, so at least one value repeats. "
            "The repeated value. -1 when the list is empty. Do not modify the list.",
        constraint_note="treat i -> nums[i] as a chain; the duplicate is the cycle entrance",
        constraints=(
            ForbidCall(("set", "dict", "Counter", "sort", "sorted", "count"),
                       because="counting solves it in O(n) memory and sorting modifies the "
                               "input; the point is that `i -> nums[i]` is a function with "
                               "a cycle, and the value at its entrance is the duplicate",
                       hint="two positions in the chain map to the same place -- and that "
                            "is exactly what a cycle entrance is"),
        ),
    ),
    Method(
        display="MEETING_POINT",
        signature="(nexts: list[int]) -> int",
        doc="Where the two pointers first coincide: both start at 0, then each step moves "
            "slow one position and fast two, and the comparison happens AFTER moving. The "
            "index they land on together. -1 for an empty list.",
        # Written to break the usual misconception. The meeting point is not the cycle
        # entrance, and a case below proves it -- which is exactly why CYCLE_START needs
        # its second phase rather than simply returning what phase one found.
        constraint_note="phase one only: move, then compare; no set of seen positions",
        constraints=(
            ForbidCall(("set", "dict", "index", "count"),
                       because="this is the loop the rest of the unit is built on, and "
                               "getting the move-then-compare order wrong makes every "
                               "input meet immediately at 0",
                       hint="slow = nexts[slow]; fast = nexts[nexts[fast]]; then compare"),
        ),
    ),
    Method(
        display="HAPPY_NUMBER",
        signature="(value: int) -> bool",
        doc="Repeatedly replace the number by the sum of the squares of its digits. True "
            "when this reaches 1; False when it falls into a cycle that never does. "
            "Values below 1 are False.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Floyd cycle detection", theme="a cycle where there are no pointers"),)

TAG_GLOSSARY = {
    "meeting": "the point where the two speeds coincide",
    "entrance": "where the cycle begins, and the algebra that finds it",
    "disguise": "a cycle in a function rather than in a structure",
    "phase-one": "the move-then-compare loop the rest is built on",
    "edge-values": "empty inputs, self-loops, cycles of length one",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("length_whole", "CYCLE_LENGTH", [1, 2, 0], ret=3,
       tags=["meeting"], visible=True, doc="0 to 1 to 2 and back: a cycle of three."),
    _c("length_with_tail", "CYCLE_LENGTH", [1, 2, 3, 2], ret=2,
       tags=["meeting"], visible=True,
       doc="Index 0 and 1 are a run-in; the cycle is 2 to 3 and back, so 2."),
    _c("length_self_loop", "CYCLE_LENGTH", [0], ret=1,
       tags=["meeting", "edge-values"], visible=True,
       doc="A position pointing at itself is a cycle of one."),
    _c("length_tail_into_self_loop", "CYCLE_LENGTH", [1, 1], ret=1,
       tags=["meeting", "edge-values"]),
    _c("length_empty", "CYCLE_LENGTH", [], ret=0, tags=["meeting", "edge-values"]),

    _c("start_at_zero", "CYCLE_START", [1, 2, 0], ret=0,
       tags=["entrance"], visible=True, doc="The whole thing is the cycle."),
    _c("start_after_tail", "CYCLE_START", [1, 2, 3, 2], ret=2,
       tags=["entrance"], visible=True,
       doc="Two positions lead in before the cycle begins at index 2."),
    _c("start_self_loop", "CYCLE_START", [0], ret=0,
       tags=["entrance", "edge-values"]),
    _c("start_long_tail", "CYCLE_START", [1, 2, 3, 4, 3], ret=3,
       tags=["entrance"], visible=True,
       doc="A long run-in and a cycle of two. The second phase has to walk the tail, "
           "which is why it restarts from index 0."),
    _c("start_empty", "CYCLE_START", [], ret=-1, tags=["entrance", "edge-values"]),

    _c("duplicate_basic", "FIND_DUPLICATE", [1, 3, 4, 2, 2], ret=2,
       tags=["disguise"], visible=True, doc="2 appears twice."),
    _c("duplicate_repeated_many", "FIND_DUPLICATE", [2, 2, 2, 2, 2], ret=2,
       tags=["disguise", "edge-values"], visible=True,
       doc="The same value five times is still one duplicate."),
    _c("duplicate_at_start", "FIND_DUPLICATE", [1, 1], ret=1,
       tags=["disguise", "edge-values"], visible=True,
       doc="The smallest possible input: two values, both 1."),
    _c("duplicate_last", "FIND_DUPLICATE", [3, 1, 3, 4, 2], ret=3, tags=["disguise"]),
    _c("duplicate_empty", "FIND_DUPLICATE", [], ret=-1,
       tags=["disguise", "edge-values"]),

    _c("meeting_differs_from_entrance", "MEETING_POINT", [1, 2, 3, 4, 3], ret=4,
       tags=["meeting"], visible=True,
       doc="They meet at index 4, and the cycle BEGINS at index 3. The meeting point is "
           "not the entrance, which is the whole reason CYCLE_START needs a second phase."),
    _c("meeting_whole_cycle", "MEETING_POINT", [1, 2, 0], ret=0,
       tags=["meeting"], visible=True, doc="Here they happen to meet at the entrance."),
    _c("meeting_self_loop", "MEETING_POINT", [0], ret=0,
       tags=["meeting", "edge-values"], visible=True,
       doc="A self-loop meets on the first step -- but only because both pointers MOVED "
           "before being compared. Comparing first would report a meeting on every input."),
    _c("meeting_tail", "MEETING_POINT", [1, 1], ret=1,
       tags=["meeting", "edge-values"]),
    _c("meeting_empty", "MEETING_POINT", [], ret=-1,
       tags=["meeting", "edge-values"]),

    _c("happy_yes", "HAPPY_NUMBER", 19, ret=True,
       tags=["checkpoint", "disguise"], visible=True,
       doc="1+81 = 82, 64+4 = 68, 36+64 = 100, 1+0+0 = 1."),
    _c("happy_no", "HAPPY_NUMBER", 2, ret=False,
       tags=["checkpoint", "disguise"], visible=True,
       doc="Falls into a cycle that never reaches 1."),
    _c("happy_one", "HAPPY_NUMBER", 1, ret=True,
       tags=["checkpoint", "edge-values"], visible=True, doc="Already there."),
    _c("happy_seven", "HAPPY_NUMBER", 7, ret=True, tags=["checkpoint"]),
    _c("happy_zero", "HAPPY_NUMBER", 0, ret=False,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="0 squares to 0 forever, and is excluded by the 'below 1' rule anyway."),
    _c("happy_negative", "HAPPY_NUMBER", -19, ret=False,
       tags=["checkpoint", "edge-values"]),
    _c("happy_large", "HAPPY_NUMBER", 100, ret=True, tags=["checkpoint"],
       why="a power of ten reaches 1 in one step, which a loop that starts by squaring "
           "before testing can miss"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="floyd",
    title="3.17 Floyd cycle detection",
    blurb="Cycle length and entrance, the duplicate number, the middle, happy numbers.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="hard",
    topics=("meeting", "entrance", "disguise"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.17 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
