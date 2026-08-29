"""2.6 Queue and deque — O(1) at both ends, and what that unlocks.

Self-contained: loaded by file path, so no package-relative imports.

The whole subtopic exists because `list.pop(0)` is O(n). Once you have a structure that is
cheap at the front, breadth-first search and the sliding-window maximum both become
straightforward, and both are here.

The catalogue's build exercises -- a queue from two stacks, a circular buffer -- are
classes, so they arrive as `design` problems.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="SERVED_ORDER",
        signature="(arrivals: list[str], capacity: int) -> list[str]",
        doc="Everyone arrives first, joining a queue that holds at most `capacity`; "
            "arrivals beyond that are turned away. Then the queue is served to "
            "exhaustion. Returns the names served, in the order they were served. "
            "A capacity of 0 or less serves nobody.",
        constraint_note="use collections.deque and popleft; never pop(0)",
        constraints=(
            RequireCall(("deque",),
                        because="pop(0) on a list shifts every remaining element, so a "
                                "loop of them is quadratic; a deque is O(1) at both ends",
                        hint="deque for the waiting line, popleft() to serve"),
        ),
    ),
    Method(
        display="LAST_N",
        signature="(values: list[int], n: int) -> list[int]",
        doc="The last n values, in order. Fewer if there were fewer. n of 0 gives nothing.",
        constraint_note="use deque(maxlen=n) and let it discard for you; no slicing",
        constraints=(
            Forbid(("subscript",),
                   because="a deque with maxlen drops from the front as you append, which "
                           "is the whole point -- it needs no bounds arithmetic and works "
                           "on a stream you cannot slice",
                   hint="deque(values, maxlen=n), then list(...)"),
        ),
    ),
    Method(
        display="ROTATED_QUEUE",
        signature="(items: list[int], k: int) -> list[int]",
        doc="Rotated RIGHT by k, using a deque. k may exceed the length or be negative; "
            "a negative k rotates left.",
        constraint_note="use deque.rotate; no slicing and no modulo of your own",
        constraints=(
            RequireCall(("rotate",),
                        because="deque.rotate already handles k larger than the length and "
                                "negative k, which is where the slice version goes wrong",
                        hint="d = deque(items); d.rotate(k); return list(d)"),
        ),
    ),
    Method(
        display="BFS_STEPS",
        fuzz=("grid",),
        signature="(grid: list[list[int]]) -> int",
        doc="Fewest steps from the top-left to the bottom-right, moving up/down/left/right "
            "through cells equal to 0. Cells equal to 1 are walls. The count is the number "
            "of cells visited including both ends. -1 when unreachable, and -1 when the "
            "grid is empty or either end is a wall.",
        constraint_note="breadth-first with a deque; depth-first does not give the fewest",
        constraints=(
            RequireCall(("deque",),
                        because="BFS reaches every cell by a shortest path because it "
                                "expands in distance order -- DFS finds *a* path, not the "
                                "shortest",
                        hint="queue of (row, col, steps), and mark visited on ENQUEUE"),
        ),
    ),
    Method(
        display="WINDOW_MAX",
        signature="(nums: list[int], k: int) -> list[int]",
        doc="The maximum of every window of k consecutive values, left to right. Empty "
            "when k is 0 or larger than the list.",
        constraint_note="a decreasing deque of indices; do not call max() per window",
        constraints=(
            ForbidCall(("max",),
                       because="max() per window is O(n*k); a deque that drops values it "
                               "can prove are beaten is O(n)",
                       hint="hold INDICES, evict those out of the window at the front and "
                            "those smaller than the arrival at the back"),
        ),
    ),
    Method(
        display="TASK_ROUNDS",
        fuzz=("nonneg",),
        signature="(tasks: list[str], gap: int) -> int",
        doc="Time units to finish all tasks, one per unit, where two tasks with the same "
            "name must be at least `gap` units apart. Idle units count. Tasks are taken in "
            "the given order and may not be reordered; when the next task is not yet "
            "allowed, the machine idles.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Queue and deque", theme="cheap at both ends"),)

TAG_GLOSSARY = {
    "fifo": "first-in first-out order",
    "bounded": "a fixed-size window that discards as it fills",
    "rotate": "moving elements around the ends",
    "bfs": "breadth-first search, and why it gives the shortest path",
    "monotonic": "a deque kept in sorted order to answer 'the max in this window'",
    "off-by-one": "window bounds, and which end is evicted",
    "edge-values": "empty inputs, zero capacity, unreachable targets",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("served_all_fit", "SERVED_ORDER", ["a", "b"], 5, ret=["a", "b"],
       tags=["fifo"], visible=True, doc="Everyone fits, so everyone is served in order."),
    _c("served_turned_away", "SERVED_ORDER", ["a", "b", "c"], 1, ret=["a"],
       tags=["fifo"], visible=True,
       doc="All three arrive before anyone is served, so the queue of 1 holds only 'a' "
           "and the other two are turned away."),
    _c("served_exactly_full", "SERVED_ORDER", ["a", "b"], 2, ret=["a", "b"],
       tags=["fifo", "edge-values"],
       why="capacity is the number that FIT, not the number before turning away starts"),
    _c("served_zero_capacity", "SERVED_ORDER", ["a"], 0, ret=[],
       tags=["fifo", "edge-values"], visible=True, doc="Nobody can wait, so nobody is served."),
    _c("served_negative_capacity", "SERVED_ORDER", ["a"], -1, ret=[],
       tags=["fifo", "edge-values"]),
    _c("served_empty", "SERVED_ORDER", [], 3, ret=[], tags=["fifo", "edge-values"]),

    _c("last_n_basic", "LAST_N", [1, 2, 3, 4], 2, ret=[3, 4],
       tags=["bounded"], visible=True, doc="The window keeps the newest two."),
    _c("last_n_shorter", "LAST_N", [1], 3, ret=[1],
       tags=["bounded", "edge-values"], visible=True, doc="Fewer values than the window."),
    _c("last_n_zero", "LAST_N", [1, 2], 0, ret=[], tags=["bounded", "edge-values"],
       why="maxlen=0 is a valid deque that holds nothing"),
    _c("last_n_empty", "LAST_N", [], 2, ret=[], tags=["bounded", "edge-values"]),

    _c("rotate_basic", "ROTATED_QUEUE", [1, 2, 3, 4], 1, ret=[4, 1, 2, 3],
       tags=["rotate"], visible=True, doc="Right by 1."),
    _c("rotate_negative", "ROTATED_QUEUE", [1, 2, 3], -1, ret=[2, 3, 1],
       tags=["rotate", "edge-values"], visible=True, doc="A negative k rotates left."),
    _c("rotate_wraps", "ROTATED_QUEUE", [1, 2, 3], 4, ret=[3, 1, 2],
       tags=["rotate", "edge-values"], why="rotate handles k larger than the length itself"),
    _c("rotate_empty", "ROTATED_QUEUE", [], 2, ret=[], tags=["rotate", "edge-values"],
       why="rotating nothing must not divide by a length of zero"),
    _c("rotate_zero", "ROTATED_QUEUE", [1, 2], 0, ret=[1, 2], tags=["rotate"]),

    _c("bfs_straight", "BFS_STEPS", [[0, 0], [0, 0]], ret=3,
       tags=["bfs"], visible=True,
       doc="Three cells visited: start, one step, finish."),
    _c("bfs_around_wall", "BFS_STEPS", [[0, 1], [0, 0]], ret=3,
       tags=["bfs"], visible=True, doc="Down then right, since right is a wall."),
    _c("bfs_blocked", "BFS_STEPS", [[0, 1], [1, 0]], ret=-1,
       tags=["bfs", "edge-values"], visible=True, doc="No route at all."),
    _c("bfs_single_cell", "BFS_STEPS", [[0]], ret=1,
       tags=["bfs", "edge-values"], visible=True,
       doc="Start and finish are the same cell, and it counts as one."),
    _c("bfs_start_is_wall", "BFS_STEPS", [[1, 0], [0, 0]], ret=-1,
       tags=["bfs", "edge-values"], why="the start being a wall is unreachable, not free"),
    _c("bfs_end_is_wall", "BFS_STEPS", [[0, 0], [0, 1]], ret=-1,
       tags=["bfs", "edge-values"]),
    # From `drill_mutation.py --triage`: the other routes here all begin by going DOWN,
    # so a mutant that mishandles the first rightward step survived them all.
    _c("bfs_right_then_down", "BFS_STEPS", [[0, 0], [1, 0]], ret=3,
       tags=["bfs"], visible=True,
       doc="Directly below the start is a wall, so the only route is right then down."),
    _c("bfs_empty", "BFS_STEPS", [], ret=-1, tags=["bfs", "edge-values"]),
    _c("bfs_prefers_short", "BFS_STEPS", [[0, 0, 0], [1, 1, 0], [0, 0, 0]], ret=5,
       tags=["bfs"], why="the only route is along the top and down the right edge"),

    _c("window_max_basic", "WINDOW_MAX", [1, 3, 2], 2, ret=[3, 3],
       tags=["monotonic"], visible=True, doc="Windows [1,3] and [3,2]."),
    _c("window_max_decreasing", "WINDOW_MAX", [4, 3, 2, 1], 2, ret=[4, 3, 2],
       tags=["monotonic"], visible=True,
       doc="Each window's maximum is its left edge, so nothing is ever evicted for "
           "being small -- only for leaving the window."),
    _c("window_max_size_one", "WINDOW_MAX", [2, 1], 1, ret=[2, 1], tags=["monotonic"]),
    _c("window_max_whole_list", "WINDOW_MAX", [1, 5, 2], 3, ret=[5], tags=["monotonic"]),
    _c("window_max_k_too_big", "WINDOW_MAX", [1, 2], 5, ret=[],
       tags=["monotonic", "edge-values"], visible=True,
       doc="No window of 5 exists in a list of 2, so there is nothing to report."),
    _c("window_max_k_zero", "WINDOW_MAX", [1, 2], 0, ret=[],
       tags=["monotonic", "edge-values"]),
    _c("window_max_empty", "WINDOW_MAX", [], 2, ret=[], tags=["monotonic", "edge-values"]),
    # Also from triage: a maximum that ENTERS mid-window and must survive the left edge
    # sliding past. Every other case here has its maximum at a window edge.
    _c("window_max_survives_slide", "WINDOW_MAX", [1, 0, 1, -1], 3, ret=[1, 1],
       tags=["monotonic", "off-by-one"], visible=True,
       doc="Windows [1,0,1] and [0,1,-1]. The second window's maximum is the 1 at "
           "index 2, which arrived during the first window and must not have been "
           "discarded when the leading 1 left."),
    _c("window_max_duplicates", "WINDOW_MAX", [2, 2, 2], 2, ret=[2, 2],
       tags=["monotonic", "edge-values"],
       why="equal values must not evict each other, or a window loses its maximum early"),

    _c("rounds_no_repeat", "TASK_ROUNDS", ["a", "b", "c"], 2, ret=3,
       tags=["checkpoint"], visible=True, doc="All different, so no waiting."),
    _c("rounds_with_idle", "TASK_ROUNDS", ["a", "a"], 2, ret=3,
       tags=["checkpoint"], visible=True,
       doc="a at time 0, then one idle unit, then a at time 2 -- three units in total."),
    _c("rounds_gap_zero", "TASK_ROUNDS", ["a", "a"], 0, ret=2,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A gap of 0 imposes no wait at all."),
    _c("rounds_gap_absorbed", "TASK_ROUNDS", ["a", "b", "a"], 2, ret=3,
       tags=["checkpoint"], visible=True,
       doc="b fills the gap, so the second a needs no idle time."),
    _c("rounds_empty", "TASK_ROUNDS", [], 3, ret=0, tags=["checkpoint", "edge-values"]),
    _c("rounds_single", "TASK_ROUNDS", ["a"], 5, ret=1, tags=["checkpoint", "edge-values"]),
    _c("rounds_long_gap", "TASK_ROUNDS", ["a", "a", "a"], 3, ret=7,
       tags=["checkpoint", "edge-values"],
       why="times 0, 3 and 6 -- the total is the last time plus one, not a sum of gaps"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="queues",
    title="2.6 Queue and deque",
    blurb="popleft instead of pop(0), bounded windows, rotation, BFS and the window max.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("fifo", "bfs", "monotonic"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.6 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
