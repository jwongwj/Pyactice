"""3.8 A* — Dijkstra with a guess about how far is left.

Self-contained: loaded by file path, so no package-relative imports.

Dijkstra expands whatever is cheapest so far, which means it spreads outwards in every
direction equally. A* adds an estimate of the REMAINING distance and expands whatever looks
best overall -- so the search leans towards the goal instead of filling the map.

Everything hangs on the estimate, called the heuristic:

  * **Admissible** means it never OVERestimates. An admissible heuristic keeps A* optimal.
  * **Consistent** is stronger and means the estimate never drops by more than the step
    costs; it also lets you settle each node once, exactly as in Dijkstra.
  * A heuristic of zero makes A* into Dijkstra. A heuristic that overestimates makes it
    fast and WRONG, which is the drill this unit exists for.

Manhattan distance is admissible on a four-way grid because you cannot do better than
moving straight there. It stops being admissible the moment diagonal moves are allowed.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="MANHATTAN",
        signature="(a: tuple[int, int], b: tuple[int, int]) -> int",
        doc="The four-way grid distance between two cells: the row difference plus the "
            "column difference, both taken as positive.",
        constraint_note="no square roots; this is not straight-line distance",
        constraints=(
            ForbidCall(("sqrt", "hypot", "dist", "pow"),
                       because="straight-line distance is smaller than any four-way route, "
                               "so it is still admissible -- but it is not the true cost, "
                               "and it drags floating point into an integer problem",
                       hint="abs(row difference) + abs(column difference)"),
        ),
    ),
    Method(
        display="GRID_PATH_COST",
        fuzz=("grid",),
        signature="(grid: list[list[int]], start: tuple[int, int], "
                  "goal: tuple[int, int]) -> int",
        doc="The fewest steps from `start` to `goal` moving up/down/left/right through "
            "cells equal to 0; cells equal to 1 are walls. -1 when unreachable, when "
            "either end is a wall, or when either is outside the grid. 0 when they are "
            "the same open cell.",
        constraint_note="A*: order the frontier by steps-so-far plus the Manhattan estimate",
        constraints=(
            RequireCall(("heappush", "heappop"),
                        because="the frontier is ordered by an estimate rather than by "
                                "arrival order, so it needs a heap -- with a heuristic of "
                                "zero this is exactly Dijkstra",
                        hint="push (steps + manhattan(cell, goal), steps, cell)"),
        ),
    ),
    Method(
        display="EXPANDED_COUNT",
        fuzz=("grid",),
        signature="(grid: list[list[int]], start: tuple[int, int], "
                  "goal: tuple[int, int], weight: int) -> int",
        doc="How many cells A* settles before reaching `goal`, when the Manhattan estimate "
            "is multiplied by `weight`. A weight of 0 makes it Dijkstra. The goal itself "
            "counts as settled. 0 when unreachable or either end is invalid.",
        # The measurable payoff: a bigger weight settles fewer cells. This is the drill
        # that makes "why bother with a heuristic" concrete.
        constraint_note="count settles, not pushes; a weight of 0 must behave as Dijkstra",
        constraints=(
            RequireCall(("heappush", "heappop"),
                        because="the whole point of this drill is that the count FALLS as "
                                "the heuristic grows, and that only shows up if the "
                                "frontier is genuinely ordered by the estimate",
                        hint="count each cell the first time it comes off the heap"),
        ),
    ),
    Method(
        display="IS_ADMISSIBLE",
        signature="(estimates: list[int], truths: list[int]) -> bool",
        doc="Given an estimate and the true remaining cost for each of several states, "
            "is the heuristic admissible -- that is, never larger than the truth? The two "
            "lists are the same length. True for empty lists.",
        constraint_note="one comparison per pair; a single overestimate is enough to fail",
        constraints=(
            ForbidCall(("sum", "max", "sorted"),
                       because="admissibility is per state, not on average: one estimate "
                               "above the truth is what lets A* settle a node too early "
                               "and return a path that is not shortest",
                       hint="all(estimate <= truth for each pair)"),
        ),
    ),
    Method(
        display="PATH_WITH_HEURISTIC",
        fuzz=("grid",),
        signature="(grid: list[list[int]], start: tuple[int, int], "
                  "goal: tuple[int, int], weight: int) -> int",
        doc="The number of steps A* REPORTS when the Manhattan estimate is multiplied by "
            "`weight` and each node is settled only once. With a weight of 1 this is the "
            "true shortest length; with a larger weight it may be too long, because an "
            "overestimating heuristic can settle a cell before its cheapest route is "
            "found. -1 on the usual invalid inputs.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "A*", theme="a guess about what is left, and what it costs to guess wrong"),)

TAG_GLOSSARY = {
    "heuristic": "the estimate of remaining cost",
    "admissible": "never overestimating, and why that is required",
    "expansion": "how much of the map the search touches",
    "degenerate": "a heuristic of zero, which is Dijkstra",
    "wrong": "what an overestimate actually costs you",
    "edge-values": "empty grids, walls, ends out of range",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("manhattan_basic", "MANHATTAN", (0, 0), (2, 3), ret=5,
       tags=["heuristic"], visible=True, doc="Two rows and three columns."),
    _c("manhattan_same", "MANHATTAN", (1, 1), (1, 1), ret=0,
       tags=["heuristic", "edge-values"], visible=True, doc="No distance at all."),
    _c("manhattan_negative", "MANHATTAN", (2, 3), (0, 0), ret=5,
       tags=["heuristic"], visible=True,
       doc="Symmetric: the differences are taken as positive."),
    _c("manhattan_one_axis", "MANHATTAN", (0, 0), (0, 4), ret=4, tags=["heuristic"]),
    _c("manhattan_negative_coords", "MANHATTAN", (-1, -1), (1, 1), ret=4,
       tags=["heuristic", "edge-values"]),

    _c("path_straight", "GRID_PATH_COST", [[0, 0, 0]], (0, 0), (0, 2), ret=2,
       tags=["expansion"], visible=True, doc="Two steps along a clear row."),
    _c("path_around_wall", "GRID_PATH_COST", [[0, 1], [0, 0]], (0, 0), (1, 1), ret=2,
       tags=["expansion"], visible=True, doc="Down then right."),
    _c("path_same_cell", "GRID_PATH_COST", [[0]], (0, 0), (0, 0), ret=0,
       tags=["expansion", "edge-values"], visible=True, doc="Already there."),
    _c("path_blocked", "GRID_PATH_COST", [[0, 1], [1, 0]], (0, 0), (1, 1), ret=-1,
       tags=["expansion", "edge-values"], visible=True, doc="No route."),
    _c("path_start_is_wall", "GRID_PATH_COST", [[1, 0]], (0, 0), (0, 1), ret=-1,
       tags=["expansion", "edge-values"]),
    _c("path_goal_out_of_range", "GRID_PATH_COST", [[0]], (0, 0), (5, 5), ret=-1,
       tags=["expansion", "edge-values"]),
    _c("path_empty", "GRID_PATH_COST", [], (0, 0), (0, 0), ret=-1,
       tags=["expansion", "edge-values"]),
    _c("path_detour", "GRID_PATH_COST", [[0, 0, 0], [1, 1, 0], [0, 0, 0]],
       (0, 0), (2, 0), ret=6, tags=["expansion"], visible=True,
       doc="The direct route is walled off, so the answer is round the outside."),

    _c("expanded_dijkstra", "EXPANDED_COUNT", [[0, 0, 0, 0, 0]], (0, 0), (0, 4), 0,
       ret=5, tags=["degenerate"], visible=True,
       doc="A weight of 0 is Dijkstra: with nothing to guide it, every cell in the row is "
           "settled before the goal."),
    _c("expanded_guided", "EXPANDED_COUNT", [[0, 0, 0, 0, 0]], (0, 0), (0, 4), 1,
       ret=5, tags=["expansion"], visible=True,
       doc="On a single corridor there is nowhere else to go, so the heuristic saves "
           "nothing -- the payoff comes when there are alternatives."),
    _c("expanded_open_grid", "EXPANDED_COUNT",
       [[0, 0, 0], [0, 0, 0], [0, 0, 0]], (0, 0), (0, 2), 1, ret=3,
       tags=["expansion"], visible=True,
       doc="An open grid with a guided search settles only the top row; with a weight of "
           "0 it would settle far more."),
    _c("expanded_same_cell", "EXPANDED_COUNT", [[0]], (0, 0), (0, 0), 1, ret=1,
       tags=["expansion", "edge-values"], visible=True,
       doc="The goal counts as settled, so reaching it immediately is 1 and not 0."),
    _c("expanded_unreachable", "EXPANDED_COUNT", [[0, 1], [1, 0]], (0, 0), (1, 1), 1,
       ret=0, tags=["expansion", "edge-values"]),
    _c("expanded_empty", "EXPANDED_COUNT", [], (0, 0), (0, 0), 1, ret=0,
       tags=["expansion", "edge-values"]),

    _c("admissible_yes", "IS_ADMISSIBLE", [1, 2, 3], [1, 3, 4], ret=True,
       tags=["admissible"], visible=True, doc="Every estimate is at or below the truth."),
    _c("admissible_equal", "IS_ADMISSIBLE", [2, 2], [2, 2], ret=True,
       tags=["admissible"], visible=True,
       doc="Exactly right is admissible -- the perfect heuristic, which expands nothing "
           "unnecessary at all."),
    _c("admissible_one_over", "IS_ADMISSIBLE", [1, 5, 1], [1, 4, 1], ret=False,
       tags=["admissible", "wrong"], visible=True,
       doc="One overestimate out of three is enough. An average would call this fine."),
    _c("admissible_empty", "IS_ADMISSIBLE", [], [], ret=True,
       tags=["admissible", "edge-values"]),
    _c("admissible_all_zero", "IS_ADMISSIBLE", [0, 0], [3, 4], ret=True,
       tags=["admissible", "degenerate"], visible=True,
       doc="A heuristic of zero is always admissible, which is why Dijkstra is always "
           "correct -- and never guided."),

    _c("heuristic_true_shortest", "PATH_WITH_HEURISTIC",
       [[0, 0, 0], [0, 1, 0], [0, 0, 0]], (0, 0), (2, 2), 1, ret=4,
       tags=["checkpoint"], visible=True,
       doc="A weight of 1 is admissible, so the reported length is the true shortest."),
    _c("heuristic_zero_is_dijkstra", "PATH_WITH_HEURISTIC",
       [[0, 0, 0], [0, 1, 0], [0, 0, 0]], (0, 0), (2, 2), 0, ret=4,
       tags=["checkpoint", "degenerate"], visible=True,
       doc="A weight of 0 is Dijkstra, and also correct."),
    # The three below are the same grid at three weights, and are the point of the unit.
    # Finding a maze where an inadmissible heuristic actually goes wrong took a search:
    # small open grids forgive it entirely, because there is usually only one shortest
    # route and the greedy dive happens to follow it. A first attempt at this case
    # asserted a failure that did not occur, and Gate 1 rejected it.
    _c("heuristic_weight_one_correct", "PATH_WITH_HEURISTIC",
       [[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1], [1, 1, 0, 0, 0]], (0, 0), (4, 4), 1, ret=8,
       tags=["checkpoint"], visible=True,
       doc="A maze where the shortest route is 8 steps. An admissible weight finds it."),
    _c("heuristic_weight_two_still_correct", "PATH_WITH_HEURISTIC",
       [[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1], [1, 1, 0, 0, 0]], (0, 0), (4, 4), 2, ret=8,
       tags=["checkpoint", "wrong"], visible=True,
       doc="Weight 2 already overestimates and STILL gets the right answer here. An "
           "inadmissible heuristic is not guaranteed to be wrong -- only unguaranteed to "
           "be right, which is a much harder thing to notice in testing."),
    _c("heuristic_overestimate_is_wrong", "PATH_WITH_HEURISTIC",
       [[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1], [1, 1, 0, 0, 0]], (0, 0), (4, 4), 5, ret=10,
       tags=["checkpoint", "wrong"], visible=True,
       doc="At weight 5 the search dives towards the goal, settles a cell by a route that "
           "is not the cheapest, and reports 10 where the truth is 8. This is what an "
           "inadmissible heuristic actually costs: not a crash, a quietly wrong answer."),
    _c("heuristic_same_cell", "PATH_WITH_HEURISTIC", [[0]], (0, 0), (0, 0), 1, ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("heuristic_blocked", "PATH_WITH_HEURISTIC", [[0, 1], [1, 0]], (0, 0), (1, 1), 1,
       ret=-1, tags=["checkpoint", "edge-values"]),
    _c("heuristic_empty", "PATH_WITH_HEURISTIC", [], (0, 0), (0, 0), 1, ret=-1,
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="a_star",
    title="3.8 A*",
    blurb="Manhattan distance, guided search, how much it saves and what a bad guess costs.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="hard",
    topics=("heuristic", "admissible", "expansion"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.8 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
