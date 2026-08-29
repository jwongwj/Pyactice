"""3.18 Intervals — sort by the right end, then sweep.

Self-contained: loaded by file path, so no package-relative imports.

Nearly every interval question is "sort, then walk once", and the whole difficulty is
deciding WHICH end to sort by:

  * merging overlaps          -> sort by START
  * how many overlap at once  -> sort the starts and ends separately, or use a heap
  * keeping the most you can  -> sort by END, which is the greedy in unit 3.11

Every drill here assumes each interval is well-formed -- its start is at or before its
end. That is a precondition, not something the drills check.

The other decision to make explicitly is whether touching counts as overlapping. [1,2] and
[2,3] share a single point; whether that is one interval or two is a choice, and every
drill here states which it takes.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="MERGE_INTERVALS",
        fuzz=("ordered-pairs",),
        signature="(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]",
        doc="Overlapping intervals combined, sorted by start. TOUCHING counts as "
            "overlapping, so [1,2] and [2,3] become [1,3]. Input may be in any order.",
        constraint_note="sort by start, then extend or emit; one pass",
        constraints=(
            Forbid(("while",),
                   because="once sorted by start, an interval either extends the one you "
                           "are holding or begins a new one -- there is nothing to search "
                           "for and nothing to repeat",
                   hint="hold the current interval; if the next starts at or before your "
                        "end, extend the end to max(end, next end)"),
        ),
    ),
    Method(
        display="INSERT_INTERVAL",
        fuzz=("ordered-pairs", "disjoint-sorted"),
        signature="(intervals: list[tuple[int, int]], new: tuple[int, int]) "
                  "-> list[tuple[int, int]]",
        doc="`new` inserted into an already-sorted, non-overlapping list, merging whatever "
            "it touches. Touching counts as overlapping.",
        constraint_note="three phases: before, merge, after -- no re-sorting",
        constraints=(
            ForbidCall(("sort", "sorted"),
                       because="the input is already sorted and disjoint, so inserting is "
                               "one linear pass; re-sorting throws that away",
                       hint="emit everything ending before `new` starts, absorb everything "
                            "that touches it, then emit the rest"),
        ),
    ),
    Method(
        display="MIN_ROOMS",
        fuzz=("ordered-pairs",),
        signature="(meetings: list[tuple[int, int]]) -> int",
        doc="The fewest rooms needed to hold every meeting. A meeting ending at time t and "
            "one starting at t may share a room -- ends free the room before starts take "
            "it.",
        # The classic sweep: sort starts and ends independently and walk both.
        # `Forbid(("comprehension",))` was the first attempt and forbids its own answer:
        # separating the ends from the starts is naturally `sorted(m[1] for m in ...)`,
        # a generator expression. There are two standard solutions to this question --
        # a heap of end times, and the two-sorted-lists sweep -- so forbidding the heap
        # names the one being taught without banning the way to write it.
        constraint_note="sort the starts and the ends separately, then sweep; no heap",
        constraints=(
            ForbidCall(("heappush", "heappop", "heapify", "heapreplace"),
                       because="a heap of end times is the other correct answer and hides "
                               "the insight: the ends do not have to stay attached to "
                               "their starts, and once separated this is one merge-like "
                               "pass with no structure at all",
                       hint="two sorted lists and two indices: a start before the next end "
                            "needs a room, otherwise a room is freed"),
        ),
    ),
    Method(
        display="ERASE_OVERLAPS",
        fuzz=("ordered-pairs",),
        signature="(intervals: list[tuple[int, int]]) -> int",
        doc="The fewest intervals to remove so that none of the rest overlap. Touching "
            "does NOT count as overlapping here: [1,2] and [2,3] may both stay.",
        constraint_note="greedy: sort by END and keep whatever still fits",
        constraints=(
            Forbid(("comprehension",),
                   because="sorting by START keeps a long interval that blocks several "
                           "short ones; the interval that ends soonest leaves the most "
                           "room for everything after it, which is why the end is the key",
                   hint="sort by end; keep an interval when it starts at or after the "
                        "last kept end, otherwise count a removal"),
        ),
    ),
    Method(
        display="FREE_SLOTS",
        fuzz=("ordered-pairs",),
        signature="(busy: list[tuple[int, int]], day: tuple[int, int], length: int) "
                  "-> list[tuple[int, int]]",
        doc="Every gap of at least `length` inside `day`, given busy intervals that may "
            "overlap and arrive in any order. Gaps are returned sorted by start, and are "
            "as large as possible rather than cut to `length`. A `length` of 0 or less "
            "returns nothing.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Intervals", theme="which end you sort by is the whole decision"),)

TAG_GLOSSARY = {
    "merge": "combining overlapping ranges",
    "touching": "whether a shared endpoint counts as an overlap",
    "sweep": "walking starts and ends independently",
    "greedy": "sorting by end to keep the most",
    "gaps": "what is left between the busy parts",
    "edge-values": "empty inputs, one interval, nothing overlapping, containment",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("merge_basic", "MERGE_INTERVALS", [(1, 3), (2, 6), (8, 10)],
       ret=[(1, 6), (8, 10)], tags=["merge"], visible=True,
       doc="The first two overlap; the third stands alone."),
    _c("merge_touching", "MERGE_INTERVALS", [(1, 2), (2, 3)], ret=[(1, 3)],
       tags=["merge", "touching"], visible=True,
       doc="Touching counts here, so these become one."),
    _c("merge_unsorted_input", "MERGE_INTERVALS", [(8, 10), (1, 3)],
       ret=[(1, 3), (8, 10)], tags=["merge"], visible=True,
       doc="Input order does not matter; the answer is sorted by start."),
    _c("merge_contained", "MERGE_INTERVALS", [(1, 9), (2, 3)], ret=[(1, 9)],
       tags=["merge", "edge-values"], visible=True,
       doc="Fully contained. The end must be max(end, next end), not simply the next "
           "end, or the answer shrinks to (1, 3)."),
    # From triage: every merging case here has the later interval extending FURTHER, so
    # the `max(end, next end)` could be replaced by either operand and still pass.
    _c("merge_same_end", "MERGE_INTERVALS", [(8, 10), (0, 1), (3, 10)],
       ret=[(0, 1), (3, 10)], tags=["merge", "edge-values"], visible=True,
       doc="(3,10) and (8,10) end together, so the merged end is unchanged and only the "
           "start matters -- and a disjoint interval sits before them both."),
    _c("merge_disjoint", "MERGE_INTERVALS", [(1, 2), (4, 5)], ret=[(1, 2), (4, 5)],
       tags=["merge"]),
    # Degenerate intervals -- start equal to end -- are well-formed and were missing
    # from every case here. Found by triage, three times over across this unit.
    _c("merge_degenerate_first", "MERGE_INTERVALS", [(-1, -1), (0, 10), (6, 8)],
       ret=[(-1, -1), (0, 10)], tags=["merge", "edge-values"], visible=True,
       doc="A zero-width interval stands alone, and the (6,8) that follows is swallowed "
           "by (0,10) without shortening it."),
    _c("merge_single", "MERGE_INTERVALS", [(1, 2)], ret=[(1, 2)],
       tags=["merge", "edge-values"]),
    _c("merge_empty", "MERGE_INTERVALS", [], ret=[], tags=["merge", "edge-values"]),
    _c("merge_identical", "MERGE_INTERVALS", [(1, 2), (1, 2)], ret=[(1, 2)],
       tags=["merge", "edge-values"]),

    _c("insert_between", "INSERT_INTERVAL", [(1, 2), (6, 7)], (3, 5),
       ret=[(1, 2), (3, 5), (6, 7)], tags=["merge"], visible=True,
       doc="Touching nothing, so it slots in."),
    _c("insert_merges", "INSERT_INTERVAL", [(1, 3), (6, 9)], (2, 5),
       ret=[(1, 5), (6, 9)], tags=["merge"], visible=True,
       doc="Absorbs the first."),
    _c("insert_swallows_several", "INSERT_INTERVAL", [(1, 2), (4, 5), (7, 8)], (0, 9),
       ret=[(0, 9)], tags=["merge", "edge-values"], visible=True,
       doc="One interval can absorb every existing one."),
    _c("insert_touching", "INSERT_INTERVAL", [(1, 2)], (2, 3), ret=[(1, 3)],
       tags=["merge", "touching"], visible=True, doc="Touching merges."),
    _c("insert_contained", "INSERT_INTERVAL", [(0, 8)], (0, 3), ret=[(0, 8)],
       tags=["merge", "edge-values"], visible=True,
       doc="The new interval is entirely inside an existing one, so the answer is "
           "unchanged -- the absorbing runs the other way round from the usual case."),
    _c("insert_at_front", "INSERT_INTERVAL", [(5, 6)], (1, 2), ret=[(1, 2), (5, 6)],
       tags=["merge", "edge-values"]),
    _c("insert_touching_at_start", "INSERT_INTERVAL", [(1, 8)], (-1, 1), ret=[(-1, 8)],
       tags=["merge", "touching"], visible=True,
       doc="The mirror of insert_touching: the new interval ENDS exactly where the "
           "existing one begins, and they still merge."),
    _c("insert_at_back", "INSERT_INTERVAL", [(1, 2)], (5, 6), ret=[(1, 2), (5, 6)],
       tags=["merge", "edge-values"]),
    _c("insert_into_empty", "INSERT_INTERVAL", [], (1, 2), ret=[(1, 2)],
       tags=["merge", "edge-values"]),

    _c("rooms_overlapping", "MIN_ROOMS", [(0, 30), (5, 10), (15, 20)], ret=2,
       tags=["sweep"], visible=True,
       doc="The long meeting overlaps both short ones, but the short ones do not overlap "
           "each other, so two rooms suffice."),
    _c("rooms_none_overlap", "MIN_ROOMS", [(1, 2), (3, 4)], ret=1, tags=["sweep"]),
    _c("rooms_touching_share", "MIN_ROOMS", [(1, 2), (2, 3)], ret=1,
       tags=["sweep", "touching"], visible=True,
       doc="One ends exactly as the other begins, so they share a room. Treating that as "
           "an overlap gives 2."),
    _c("rooms_all_at_once", "MIN_ROOMS", [(1, 9), (2, 9), (3, 9)], ret=3,
       tags=["sweep"], visible=True, doc="Three at once needs three."),
    _c("rooms_degenerate", "MIN_ROOMS", [(0, 9), (9, 9)], ret=1,
       tags=["sweep", "edge-values"], visible=True,
       doc="A zero-length meeting starting exactly as another ends. One room does for "
           "both, and the sweep must not run off the end of its list of ends."),
    _c("rooms_degenerate_same_start", "MIN_ROOMS", [(-1, -1), (-1, 20)], ret=1,
       tags=["sweep", "edge-values"], visible=True,
       doc="Both begin at the same instant and one takes no time at all, so it frees "
           "its room immediately and a single room serves both."),
    _c("rooms_unsorted_sequential", "MIN_ROOMS", [(10, 20), (0, 1), (20, 30)], ret=1,
       tags=["sweep", "edge-values"], visible=True,
       doc="Three meetings, given out of order, that never overlap. Every other case "
           "here arrives sorted."),
    _c("rooms_single", "MIN_ROOMS", [(1, 2)], ret=1, tags=["sweep", "edge-values"]),
    _c("rooms_empty", "MIN_ROOMS", [], ret=0, tags=["sweep", "edge-values"]),
    _c("rooms_identical", "MIN_ROOMS", [(1, 2), (1, 2)], ret=2,
       tags=["sweep", "edge-values"],
       why="two meetings at exactly the same time still need two rooms"),

    _c("erase_basic", "ERASE_OVERLAPS", [(1, 2), (2, 3), (3, 4), (1, 3)], ret=1,
       tags=["greedy"], visible=True,
       doc="Removing [1,3] leaves three that only touch. Touching is allowed here."),
    _c("erase_none_needed", "ERASE_OVERLAPS", [(1, 2), (3, 4)], ret=0,
       tags=["greedy"], visible=True, doc="Already disjoint."),
    _c("erase_greedy_by_end", "ERASE_OVERLAPS", [(1, 100), (2, 3), (3, 4)], ret=1,
       tags=["greedy"], visible=True,
       doc="Sorting by START would keep [1,100] and remove both short ones for a count "
           "of 2. Keeping the interval that ends soonest gives 1, which is the answer."),
    _c("erase_all_identical", "ERASE_OVERLAPS", [(1, 2), (1, 2), (1, 2)], ret=2,
       tags=["greedy", "edge-values"], visible=True,
       doc="Only one of three identical intervals can stay."),
    _c("erase_single", "ERASE_OVERLAPS", [(1, 2)], ret=0,
       tags=["greedy", "edge-values"]),
    _c("erase_empty", "ERASE_OVERLAPS", [], ret=0, tags=["greedy", "edge-values"]),

    _c("free_basic", "FREE_SLOTS", [(2, 4)], (0, 8), 2, ret=[(0, 2), (4, 8)],
       tags=["checkpoint", "gaps"], visible=True,
       doc="Before and after the busy block, and each gap is as large as it can be."),
    _c("free_too_short", "FREE_SLOTS", [(1, 7)], (0, 8), 2, ret=[],
       tags=["checkpoint", "gaps"], visible=True,
       doc="Both gaps are one long, and two is required."),
    _c("free_overlapping_busy", "FREE_SLOTS", [(2, 5), (3, 6)], (0, 9), 2,
       ret=[(0, 2), (6, 9)], tags=["checkpoint", "gaps"], visible=True,
       doc="The busy intervals overlap and must be merged first, or a phantom gap "
           "appears between them."),
    _c("free_unsorted_busy", "FREE_SLOTS", [(5, 7), (1, 2)], (0, 9), 2,
       ret=[(2, 5), (7, 9)], tags=["checkpoint", "gaps"], visible=True,
       doc="Busy intervals arrive in any order."),
    _c("free_nothing_busy", "FREE_SLOTS", [], (0, 5), 2, ret=[(0, 5)],
       tags=["checkpoint", "edge-values"]),
    _c("free_fully_busy", "FREE_SLOTS", [(0, 5)], (0, 5), 1, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("free_busy_outside_day", "FREE_SLOTS", [(9, 10)], (0, 5), 2, ret=[(0, 5)],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A busy block entirely outside the day does not carve anything out of it."),
    # A `length` of exactly 1 separates `length <= 0` from `length <= 1`; every other
    # case here uses 2, which both readings reject the same way.
    _c("free_length_one", "FREE_SLOTS", [], (7, 9), 1, ret=[(7, 9)],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="The smallest length that still asks for something."),
    _c("free_zero_length", "FREE_SLOTS", [], (0, 5), 0, ret=[],
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="intervals",
    title="3.18 Intervals",
    blurb="Merging, inserting, counting overlaps, the end-sorted greedy, and free gaps.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("merge", "sweep", "greedy"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.18 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
