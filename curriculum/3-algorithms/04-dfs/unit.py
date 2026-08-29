"""3.4 DFS — explore fully, and the reasons to write it iteratively.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **"explore everything reachable"** or **"all paths"**. BFS answers "fewest
steps"; DFS answers "is there any", "how many pieces", and "list them all".

Unit 2.11 uses a traversal to answer questions about graphs. This unit is about the
traversal itself: the grid form, the explicit stack, and the one thing that separates a
correct DFS from a hang -- marking a cell before you queue it rather than after you pop it.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="FLOOD_FILL",
        fuzz=("grid",),
        signature="(grid: list[list[int]], row: int, col: int, colour: int) "
                  "-> list[list[int]]",
        doc="Every cell connected to (row, col) through equal values, up/down/left/right, "
            "repainted to `colour`. The grid is rectangular. A start outside the grid "
            "leaves it unchanged, and so does a start already holding `colour`.",
        constraint_note="iterative, with an explicit stack; no recursion",
        constraints=(
            Forbid(("recursion",),
                   because="a 200x200 region of one colour recurses forty thousand deep "
                           "and Python gives out around a thousand",
                   hint="push the start, then pop-and-push-neighbours until empty"),
        ),
    ),
    Method(
        display="ISLAND_SIZES",
        fuzz=("grid",),
        signature="(grid: list[list[int]]) -> list[int]",
        doc="The size of every group of connected 1s, largest first, ties in any order "
            "resolved by sorting descending. Diagonals do not connect.",
        constraint_note="one traversal per unvisited land cell; iterative",
        constraints=(
            Forbid(("recursion",),
                   because="the same stack-depth argument, and the outer loop is what "
                           "turns one traversal into 'find every piece'",
                   hint="for each unvisited 1, walk its whole island and count it"),
        ),
    ),
    Method(
        display="ALL_PATHS",
        fuzz=("edges",),
        signature="(edges: list[tuple[int, int]], nodes: int) -> list[list[int]]",
        doc="Every path from node 0 to node `nodes - 1` in a directed acyclic graph, each "
            "as the list of nodes visited. Paths sorted ascending. Empty when there are "
            "none, and when `nodes` is less than 1.",
        # The drill where DFS is genuinely the right tool: BFS would have to carry a whole
        # path per queue entry, which is what a DFS stack already is.
        constraint_note="carry the path as you descend, and undo it on the way back",
        constraints=(
            ForbidCall(("permutations", "combinations", "product"),
                       because="enumerating every ordering and filtering is factorial; "
                               "DFS only ever walks edges that exist",
                       hint="append the node, recurse or push, then pop it back off"),
        ),
    ),
    Method(
        display="HAS_PATH",
        fuzz=("edges",),
        signature="(edges: list[tuple[int, int]], nodes: int, start: int, goal: int) "
                  "-> bool",
        doc="Is `goal` reachable from `start` along directed edges? A node reaches itself. "
            "False when either is outside 0..nodes-1. The graph may contain cycles.",
        constraint_note="mark on push, not on pop; a cycle must not loop forever",
        constraints=(
            Forbid(("recursion",),
                   because="marking a node visited only when you POP it lets the same "
                           "node be pushed many times before it is first processed, and "
                           "a cycle then never terminates",
                   hint="add to `seen` at the moment you push"),
        ),
    ),
    Method(
        display="LONGEST_REGION",
        fuzz=("grid",),
        signature="(grid: list[list[int]]) -> int",
        doc="The length of the longest strictly increasing path through the grid, moving "
            "up/down/left/right. A single cell is a path of 1. 0 for an empty grid.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "DFS", theme="explore fully, with your own stack"),)

TAG_GLOSSARY = {
    "fill": "repainting a connected region",
    "pieces": "one traversal per unvisited start",
    "paths": "carrying the route, and undoing it",
    "cycles": "why marking on push rather than pop matters",
    "memo": "remembering an answer per cell",
    "edge-values": "empty grids, starts out of range, no path, single cells",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("fill_basic", "FLOOD_FILL", [[1, 1], [0, 1]], 0, 0, 2, ret=[[2, 2], [0, 2]],
       tags=["fill"], visible=True, doc="The three connected 1s are repainted."),
    _c("fill_stops_at_boundary", "FLOOD_FILL", [[1, 0], [0, 1]], 0, 0, 2,
       ret=[[2, 0], [0, 1]], tags=["fill"], visible=True,
       doc="Diagonal neighbours do not connect, so the far 1 is untouched."),
    _c("fill_same_colour", "FLOOD_FILL", [[1, 1]], 0, 0, 1, ret=[[1, 1]],
       tags=["fill", "edge-values"], visible=True,
       doc="Repainting to the colour already there must return rather than loop forever."),
    _c("fill_out_of_range", "FLOOD_FILL", [[1]], 5, 5, 2, ret=[[1]],
       tags=["fill", "edge-values"], visible=True, doc="A start outside the grid."),
    _c("fill_negative_start", "FLOOD_FILL", [[1]], -1, 0, 2, ret=[[1]],
       tags=["fill", "edge-values"]),
    _c("fill_whole_grid", "FLOOD_FILL", [[0, 0], [0, 0]], 1, 1, 7,
       ret=[[7, 7], [7, 7]], tags=["fill"]),
    # From triage: `(5, 5)` on a 1x1 grid is rejected by every bound at once, so the
    # column checks were never exercised on their own.
    _c("fill_col_equals_cols", "FLOOD_FILL", [[1, 1, 1]], 1, 2, 1, ret=[[1, 1, 1]],
       tags=["fill", "edge-values"], visible=True,
       doc="The row is out of range and the column is in range."),
    _c("fill_col_past_end", "FLOOD_FILL", [[1, 1], [0, 1]], 0, 2, -1,
       ret=[[1, 1], [0, 1]], tags=["fill", "edge-values"], visible=True,
       doc="A column of exactly the column count is one past the last."),
    _c("fill_negative_col", "FLOOD_FILL", [[1], [1], [1]], 2, -1, 0,
       ret=[[1], [1], [1]], tags=["fill", "edge-values"], visible=True,
       doc="A negative column would index from the far end if it were let through."),
    _c("fill_empty", "FLOOD_FILL", [], 0, 0, 1, ret=[], tags=["fill", "edge-values"]),

    _c("islands_two", "ISLAND_SIZES", [[1, 0], [0, 1]], ret=[1, 1],
       tags=["pieces"], visible=True, doc="Two islands of one cell each."),
    _c("islands_sizes_sorted", "ISLAND_SIZES", [[1, 1, 0], [0, 0, 0], [1, 0, 0]],
       ret=[2, 1], tags=["pieces"], visible=True, doc="Largest first."),
    _c("islands_none", "ISLAND_SIZES", [[0, 0]], ret=[],
       tags=["pieces", "edge-values"], visible=True, doc="No land at all."),
    _c("islands_all", "ISLAND_SIZES", [[1, 1], [1, 1]], ret=[4], tags=["pieces"]),
    _c("islands_u_shape", "ISLAND_SIZES", [[1, 0, 1], [1, 1, 1]], ret=[5],
       tags=["pieces"], visible=True,
       doc="Joined along the bottom, so one island of five and not two of smaller."),
    _c("islands_empty", "ISLAND_SIZES", [], ret=[], tags=["pieces", "edge-values"]),

    _c("paths_two", "ALL_PATHS", [(0, 1), (0, 2), (1, 3), (2, 3)], 4,
       ret=[[0, 1, 3], [0, 2, 3]], tags=["paths"], visible=True,
       doc="Two routes, each listed in full."),
    _c("paths_one", "ALL_PATHS", [(0, 1)], 2, ret=[[0, 1]], tags=["paths"]),
    _c("paths_none", "ALL_PATHS", [(0, 1)], 3, ret=[],
       tags=["paths", "edge-values"], visible=True,
       doc="Node 2 is the goal and nothing reaches it."),
    _c("paths_single_node", "ALL_PATHS", [], 1, ret=[[0]],
       tags=["paths", "edge-values"], visible=True,
       doc="Start and goal are the same node, so the path is that node alone."),
    _c("paths_shared_prefix", "ALL_PATHS", [(0, 1), (1, 2), (1, 3), (2, 3)], 4,
       ret=[[0, 1, 2, 3], [0, 1, 3]], tags=["paths"], visible=True,
       doc="Both routes share a prefix, which is what the undo-on-the-way-back is for: "
           "the shorter path must not carry the longer one's tail."),
    _c("paths_zero_nodes", "ALL_PATHS", [], 0, ret=[],
       tags=["paths", "edge-values"]),

    _c("has_path_direct", "HAS_PATH", [(0, 1)], 2, 0, 1, ret=True,
       tags=["cycles"], visible=True, doc="One edge."),
    _c("has_path_transitive", "HAS_PATH", [(0, 1), (1, 2)], 3, 0, 2, ret=True,
       tags=["cycles"]),
    _c("has_path_wrong_way", "HAS_PATH", [(0, 1)], 2, 1, 0, ret=False,
       tags=["cycles"], visible=True, doc="Edges are directed."),
    _c("has_path_cycle", "HAS_PATH", [(0, 1), (1, 0)], 2, 0, 1, ret=True,
       tags=["cycles"], visible=True,
       doc="A two-node cycle. Marking on pop rather than on push never terminates here."),
    _c("has_path_self", "HAS_PATH", [], 2, 1, 1, ret=True,
       tags=["cycles", "edge-values"], visible=True, doc="A node reaches itself."),
    _c("has_path_out_of_range", "HAS_PATH", [], 2, 0, 9, ret=False,
       tags=["cycles", "edge-values"]),
    _c("has_path_self_no_edges", "HAS_PATH", [], 2, 0, 0, ret=True,
       tags=["cycles", "edge-values"], visible=True,
       doc="A node reaches itself even with no edges at all -- the self-check must come "
           "before anything that needs the graph."),
    _c("has_path_no_nodes", "HAS_PATH", [], -1, 2, 2, ret=False,
       tags=["cycles", "edge-values"], visible=True,
       doc="With a negative node count nothing is in range, so not even the self-check "
           "applies."),
    _c("has_path_unreachable", "HAS_PATH", [(0, 1)], 3, 0, 2, ret=False,
       tags=["cycles", "edge-values"]),

    _c("longest_basic", "LONGEST_REGION", [[1, 2], [4, 3]], ret=4,
       tags=["checkpoint", "memo"], visible=True,
       doc="1 to 2 to 3 to 4 winds round the grid."),
    _c("longest_flat", "LONGEST_REGION", [[5, 5], [5, 5]], ret=1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Strictly increasing, so equal neighbours do not extend a path."),
    _c("longest_single", "LONGEST_REGION", [[7]], ret=1,
       tags=["checkpoint", "edge-values"]),
    _c("longest_row", "LONGEST_REGION", [[1, 2, 3]], ret=3, tags=["checkpoint"]),
    _c("longest_descending", "LONGEST_REGION", [[3, 2, 1]], ret=3,
       tags=["checkpoint"], visible=True,
       doc="A path may run in any direction, so a descending row read backwards is "
           "increasing."),
    _c("longest_empty", "LONGEST_REGION", [], ret=0,
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="dfs",
    title="3.4 DFS",
    blurb="Flood fill, island sizes, all paths, reachability with cycles.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("fill", "paths", "cycles"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.4 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
