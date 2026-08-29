"""3.5 BFS — fewest steps, and the multi-source trick.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **fewest steps in an unweighted graph**. BFS expands in distance order, so the
first time it reaches anything it has reached it by a shortest route. That property is the
whole reason to prefer it to DFS, and it is the first thing to say when asked why.

Unit 2.6 introduces the grid form. This unit is the two ideas built on top: seeding the
queue with MANY starts at once, and searching a graph whose nodes are strings you generate
rather than a structure you were given.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="DISTANCES_FROM",
        signature="(edges: list[tuple[str, str]], start: str) -> dict[str, int]",
        doc="How many undirected edges away each reachable node is from `start`, including "
            "`start` itself at 0. Unreachable nodes are absent. An empty dict when `start` "
            "appears in no edge and is therefore unknown.",
        constraint_note="a queue, and set the distance when you ENQUEUE",
        constraints=(
            RequireCall(("deque",),
                        because="a list used as a queue with pop(0) is O(n) per step; and "
                                "a STACK here would give distances that are not shortest",
                        hint="distance[nxt] = distance[node] + 1 at the moment you queue it"),
        ),
    ),
    Method(
        display="ROT_TIME",
        fuzz=("grid",),
        signature="(grid: list[list[int]]) -> int",
        doc="0 is empty, 1 is fresh, 2 is rotten. Each minute, every rotten cell rots its "
            "four neighbours. How many minutes until nothing fresh is left? -1 when "
            "something fresh can never be reached. 0 when nothing is fresh to begin with.",
        # Multi-source: every rotten cell starts in the queue at time 0.
        constraint_note="seed the queue with EVERY rotten cell before the loop starts",
        constraints=(
            RequireCall(("deque",),
                        because="running a separate BFS from each rotten cell and taking "
                                "the minimum is correct and much slower; seeding them all "
                                "at distance 0 gives the same answer in one pass",
                        hint="collect every 2 first, then expand a whole level per minute"),
        ),
    ),
    Method(
        display="LADDER_LENGTH",
        signature="(start: str, goal: str, words: list[str]) -> int",
        doc="The fewest words in a chain from `start` to `goal` where each step changes "
            "exactly one character and every word after the first is in `words`. Counts "
            "both ends. 0 when there is no chain. `start` need not be in `words`.",
        constraint_note="the nodes are words; generate neighbours rather than look them up",
        constraints=(
            Forbid(("recursion",),
                   because="there is no graph object here -- the neighbours of a word are "
                           "generated on demand, and BFS is what makes the FEWEST steps "
                           "come out rather than merely some chain",
                   hint="a set of the words for O(1) membership, and discard each word as "
                        "you reach it so it is never queued twice"),
        ),
    ),
    Method(
        display="NEAREST_EXIT",
        fuzz=("grid",),
        signature="(grid: list[list[int]], row: int, col: int) -> int",
        doc="Steps from (row, col) to the nearest border cell that is not a wall, not "
            "counting the start even if it is on the border. 0 is open and 1 is a wall. "
            "-1 when none is reachable, when the start is a wall, or when the start is "
            "outside the grid.",
        constraint_note="BFS, and do not accept the start itself as the exit",
        constraints=(
            RequireCall(("deque",),
                        because="'nearest' is the cue; a depth-first walk finds an exit "
                                "and not the closest one",
                        hint="expand level by level and stop at the first border cell "
                             "that is not where you began"),
        ),
    ),
    Method(
        display="MIN_MULTIPLY",
        signature="(start: int, goal: int, limit: int) -> int",
        doc="The fewest operations turning `start` into `goal`, where each operation "
            "either doubles the value or subtracts 1. Values must stay between 0 and "
            "`limit` inclusive at every step, INCLUDING the start and the goal -- either "
            "of them outside that range is -1. -1 when it cannot be done.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "BFS", theme="the first time you arrive is the shortest way"),)

TAG_GLOSSARY = {
    "distance": "expanding in order of steps taken",
    "multi-source": "many starts seeded at distance zero",
    "implicit": "a graph whose nodes are generated rather than stored",
    "levels": "draining exactly one level at a time",
    "edge-values": "empty grids, unreachable targets, starts on walls or out of range",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("distances_chain", "DISTANCES_FROM", [("a", "b"), ("b", "c")], "a",
       ret={"a": 0, "b": 1, "c": 2}, tags=["distance"], visible=True,
       doc="One step per edge, and the start is 0."),
    _c("distances_shortest_wins", "DISTANCES_FROM",
       [("a", "b"), ("b", "c"), ("a", "c")], "a", ret={"a": 0, "b": 1, "c": 1},
       tags=["distance"], visible=True,
       doc="c is reachable in two hops and in one, and the answer is 1. This is the case "
           "a depth-first walk gets wrong."),
    _c("distances_unreachable_absent", "DISTANCES_FROM", [("a", "b"), ("c", "d")], "a",
       ret={"a": 0, "b": 1}, tags=["distance", "edge-values"], visible=True,
       doc="c and d are in another component and simply do not appear."),
    _c("distances_unknown_start", "DISTANCES_FROM", [("a", "b")], "z", ret={},
       tags=["distance", "edge-values"], visible=True,
       doc="A start that appears in no edge is unknown, so not even it is reported."),
    _c("distances_no_edges", "DISTANCES_FROM", [], "a", ret={},
       tags=["distance", "edge-values"]),
    _c("distances_cycle", "DISTANCES_FROM", [("a", "b"), ("b", "c"), ("c", "a")], "a",
       ret={"a": 0, "b": 1, "c": 1}, tags=["distance"],
       why="a cycle must not revisit, and c is one step away going the other way"),

    _c("rot_basic", "ROT_TIME", [[2, 1, 1], [1, 1, 0], [0, 1, 1]], ret=4,
       tags=["multi-source"], visible=True, doc="One rotten cell, spreading outwards."),
    _c("rot_two_sources", "ROT_TIME", [[2, 1, 1, 2]], ret=1,
       tags=["multi-source"], visible=True,
       doc="Two rotten ends closing in. Running one BFS per source and taking the minimum "
           "gives the same answer; seeding both at once gives it in one pass."),
    _c("rot_unreachable", "ROT_TIME", [[2, 1], [0, 1]], ret=2,
       tags=["multi-source"], visible=True,
       doc="The lower-right 1 is reached down the right-hand column."),
    _c("rot_isolated_fresh", "ROT_TIME", [[2, 0, 1]], ret=-1,
       tags=["multi-source", "edge-values"], visible=True,
       doc="An empty cell separates the fresh one, so it never rots."),
    _c("rot_nothing_fresh", "ROT_TIME", [[0, 2]], ret=0,
       tags=["multi-source", "edge-values"], visible=True, doc="Already done."),
    _c("rot_no_rotten", "ROT_TIME", [[1]], ret=-1,
       tags=["multi-source", "edge-values"]),
    _c("rot_empty", "ROT_TIME", [], ret=0, tags=["multi-source", "edge-values"]),

    _c("ladder_basic", "LADDER_LENGTH", "hit", "cog", ["hot", "dot", "dog", "cog"], ret=5,
       tags=["implicit"], visible=True, doc="hit, hot, dot, dog, cog."),
    _c("ladder_one_step", "LADDER_LENGTH", "aa", "ab", ["ab"], ret=2,
       tags=["implicit"], visible=True, doc="Both ends counted, so the shortest chain is 2."),
    _c("ladder_no_chain", "LADDER_LENGTH", "hit", "cog", ["hot", "dot", "dog"], ret=0,
       tags=["implicit", "edge-values"], visible=True,
       doc="The goal is not in the word list, so no chain can end there."),
    _c("ladder_same_word", "LADDER_LENGTH", "aa", "aa", ["aa"], ret=1,
       tags=["implicit", "edge-values"], visible=True,
       doc="Already there: a chain of one word."),
    _c("ladder_same_word_absent", "LADDER_LENGTH", "cog", "cog", ["dot", "hot"], ret=0,
       tags=["implicit", "edge-values"], visible=True,
       doc="Start and goal are the same, and the goal is NOT in the word list -- so "
           "there is no chain, even though no step is needed."),
    _c("ladder_empty_words", "LADDER_LENGTH", "aa", "ab", [], ret=0,
       tags=["implicit", "edge-values"]),
    _c("ladder_different_lengths", "LADDER_LENGTH", "aa", "abc", ["abc"], ret=0,
       tags=["implicit", "edge-values"],
       why="a word of another length is never one character away"),

    _c("exit_basic", "NEAREST_EXIT", [[0, 0, 0], [1, 1, 0], [0, 0, 0]], 1, 2, ret=1,
       tags=["distance"], visible=True, doc="One step up to the border."),
    _c("exit_start_on_border", "NEAREST_EXIT", [[0, 0], [0, 0]], 0, 0, ret=1,
       tags=["distance", "edge-values"], visible=True,
       doc="The start is on the border and does NOT count, so the answer is a step away."),
    _c("exit_none", "NEAREST_EXIT", [[1, 1, 1], [1, 0, 1], [1, 1, 1]], 1, 1, ret=-1,
       tags=["distance", "edge-values"], visible=True, doc="Walled in."),
    _c("exit_start_is_wall", "NEAREST_EXIT", [[1, 0], [0, 0]], 0, 0, ret=-1,
       tags=["distance", "edge-values"]),
    _c("exit_out_of_range", "NEAREST_EXIT", [[0]], 5, 5, ret=-1,
       tags=["distance", "edge-values"]),
    # Eight gaps from `drill_mutation.py --triage`, all on the bounds guard. Four
    # separate comparisons decide whether a start is inside the grid, and `(5, 5)` on a
    # 1x1 grid rejects under every one of them -- so none was actually tested.
    _c("exit_row_equals_rows", "NEAREST_EXIT", [[0, 1], [0, 0]], 2, 0, ret=-1,
       tags=["distance", "edge-values"], visible=True,
       doc="A row of exactly the row count is one past the last."),
    _c("exit_col_equals_cols", "NEAREST_EXIT", [[1, 1], [1, 1]], 1, 2, ret=-1,
       tags=["distance", "edge-values"]),
    _c("exit_negative_row", "NEAREST_EXIT", [[0, 1, 0]], -1, 0, ret=-1,
       tags=["distance", "edge-values"]),
    _c("exit_negative_col", "NEAREST_EXIT", [[0], [1], [1], [1]], 0, -1, ret=-1,
       tags=["distance", "edge-values"]),
    _c("exit_col_far_out", "NEAREST_EXIT", [[1, 1]], 0, 5, ret=-1,
       tags=["distance", "edge-values"]),
    _c("exit_start_is_wall_interior", "NEAREST_EXIT", [[1, 0]], 0, 1, ret=-1,
       tags=["distance", "edge-values"], visible=True,
       doc="A single open cell on a 1x2 grid: it IS the border, and the start does not "
           "count as its own exit, so there is nowhere to go."),
    _c("exit_one_wide_column", "NEAREST_EXIT", [[0], [0], [1], [1]], 1, 0, ret=1,
       tags=["distance"], visible=True,
       doc="A one-wide grid, where every cell is on the border. One step up reaches the "
           "top row."),
    _c("exit_walled_below", "NEAREST_EXIT", [[0], [1], [0]], 0, 0, ret=-1,
       tags=["distance", "edge-values"], visible=True,
       doc="The start is on the border and cannot reach any OTHER border cell."),
    _c("exit_empty", "NEAREST_EXIT", [], 0, 0, ret=-1,
       tags=["distance", "edge-values"]),

    _c("multiply_double", "MIN_MULTIPLY", 2, 8, 100, ret=2,
       tags=["checkpoint", "implicit"], visible=True, doc="Double twice."),
    _c("multiply_down", "MIN_MULTIPLY", 5, 3, 100, ret=2,
       tags=["checkpoint"], visible=True, doc="Subtract 1 twice."),
    _c("multiply_mixed", "MIN_MULTIPLY", 3, 10, 100, ret=3,
       tags=["checkpoint", "implicit"], visible=True,
       doc="3 to 6 to 5 to 10 -- going DOWN before doubling is shorter than any route "
           "that only ever goes up."),
    _c("multiply_same", "MIN_MULTIPLY", 4, 4, 100, ret=0,
       tags=["checkpoint", "edge-values"], visible=True, doc="Already there."),
    _c("multiply_limit_blocks", "MIN_MULTIPLY", 3, 10, 6, ret=-1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="The goal is above the limit, so it can never be held."),
    _c("multiply_to_zero", "MIN_MULTIPLY", 2, 0, 10, ret=2,
       tags=["checkpoint", "edge-values"]),
    # Five more from triage: the range check has four comparisons and every existing case
    # failed or passed all of them together.
    _c("multiply_goal_at_limit", "MIN_MULTIPLY", 2, 6, 6, ret=3,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="The goal is exactly the limit, which is allowed: 2 to 4 to 3 to 6."),
    _c("multiply_start_at_limit", "MIN_MULTIPLY", 8, 5, 8, ret=3,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="The start is exactly the limit, and the route runs downwards."),
    _c("multiply_zero_to_zero", "MIN_MULTIPLY", 0, 0, 4, ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("multiply_start_above_limit", "MIN_MULTIPLY", 5, 2, 4, ret=-1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="The start is already outside the range, so nothing is reachable."),
    _c("multiply_negative_limit", "MIN_MULTIPLY", -1, -1, -1, ret=-1,
       tags=["checkpoint", "edge-values"]),
    _c("multiply_below_zero", "MIN_MULTIPLY", 0, 5, 10, ret=-1,
       tags=["checkpoint", "edge-values"],
       why="0 doubles to 0 and cannot go below, so nothing above it is reachable"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="bfs",
    title="3.5 BFS",
    blurb="Distances, multi-source spreading, word ladders, nearest exit.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("distance", "multi-source", "implicit"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.5 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
