"""2.11 Graph — a dict of lists, and the four questions you ask of one.

Self-contained: loaded by file path, so no package-relative imports.

Every drill here takes `(nodes, edges)`, and assumes `nodes` is distinct and every edge
names nodes that are in it. Those are preconditions, not things the drills check.

There is no Graph class here and there rarely should be: an adjacency list is
`dict[node, list[node]]`, and building one from a list of edges is the first drill. What is
worth practising is the small set of questions that come up over and over -- how many
pieces is it in, does it have a cycle, can it be two-coloured -- and noticing that they are
all one traversal with different bookkeeping.

Cycle detection differs between directed and undirected graphs in a way that catches
people out, so both are here.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="ADJACENCY",
        fuzz=("edges", "unique"),
        signature="(nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, list[str]]",
        doc="An undirected adjacency list: every node is a key, each edge appears under "
            "BOTH of its ends, and neighbours are listed in the order the edges arrive. "
            "A node with no edges maps to an empty list.",
        constraint_note="build it in one pass; every node is a key, even isolated ones",
        constraints=(
            Forbid(("if",),
                   because="setdefault or defaultdict removes the 'have I seen this key' "
                           "branch, and seeding every node up front removes the other one",
                   hint="start with {node: [] for node in nodes}, then append both ways"),
        ),
    ),
    Method(
        display="DEGREES",
        fuzz=("edges", "unique"),
        signature="(nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, int]",
        doc="How many edges touch each node, undirected. A self-loop counts twice.",
        constraint_note="count both ends of every edge",
        constraints=(
            ForbidCall(("len",),
                       because="counting the neighbour lists means building them first; "
                               "the degrees are one pass over the edges on their own",
                       hint="for a, b in edges: bump a and bump b -- including when a == b"),
        ),
    ),
    Method(
        display="COMPONENTS",
        fuzz=("edges", "unique"),
        signature="(nodes: list[str], edges: list[tuple[str, str]]) -> int",
        doc="How many connected pieces the undirected graph is in. Isolated nodes count "
            "as one piece each.",
        constraint_note="one traversal per unvisited node; count how many you start",
        constraints=(
            Forbid(("recursion",),
                   because="a path of ten thousand nodes recurses ten thousand deep and "
                           "the stack gives out; an explicit stack or queue does not",
                   hint="for each unvisited node, start a walk that marks everything "
                        "reachable, and add one to the count"),
        ),
    ),
    Method(
        display="HAS_CYCLE_DIRECTED",
        fuzz=("edges", "unique"),
        signature="(nodes: list[str], edges: list[tuple[str, str]]) -> bool",
        doc="True when the DIRECTED graph contains a cycle. Each edge (a, b) goes from a "
            "to b only. A self-loop is a cycle.",
        # The trap: "have I seen this node" is not enough. A node reachable by two
        # different paths has been seen and is not a cycle.
        constraint_note="track nodes on the CURRENT path, not merely nodes ever visited",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="a plain visited set reports a diamond as a cycle -- the "
                               "question is whether you reach a node that is still open "
                               "on the path you are standing on",
                       hint="three states, or a recursion stack you remove from on the "
                            "way back out"),
        ),
    ),
    Method(
        display="IS_BIPARTITE",
        fuzz=("edges", "unique"),
        signature="(nodes: list[str], edges: list[tuple[str, str]]) -> bool",
        doc="True when the undirected graph can be two-coloured so that no edge joins two "
            "nodes of the same colour. Disconnected pieces are coloured independently.",
        constraint_note="colour as you traverse; a neighbour must take the opposite colour",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="two-colouring is not a property you can sort your way to: "
                               "it is a traversal that assigns the opposite colour to "
                               "every neighbour and fails on a clash",
                       hint="every component needs its own start, or an uncoloured piece "
                            "is silently declared fine"),
        ),
    ),
    Method(
        display="REACHABLE_WITHIN",
        fuzz=("edges", "unique"),
        signature="(nodes: list[str], edges: list[tuple[str, str]], start: str, "
                  "steps: int) -> list[str]",
        doc="Every node reachable from `start` in at most `steps` undirected edges, sorted "
            "ascending. `start` itself is included when it is a known node, at 0 steps. "
            "An unknown start gives an empty list.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Graph", theme="a dict of lists, and one traversal wearing four hats"),)

TAG_GLOSSARY = {
    "build": "turning edges into an adjacency list",
    "traverse": "visiting everything reachable",
    "components": "how many disconnected pieces",
    "cycle": "detecting a loop, and why directed differs from undirected",
    "colouring": "two-colouring, and what it proves",
    "edge-values": "isolated nodes, self-loops, duplicate edges, unknown starts",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("adjacency_basic", "ADJACENCY", ["a", "b", "c"], [("a", "b"), ("b", "c")],
       ret={"a": ["b"], "b": ["a", "c"], "c": ["b"]}, tags=["build"], visible=True,
       doc="Undirected, so each edge appears under both ends."),
    _c("adjacency_isolated", "ADJACENCY", ["a", "b"], [],
       ret={"a": [], "b": []}, tags=["build", "edge-values"], visible=True,
       doc="A node with no edges is still a key, mapping to an empty list."),
    _c("adjacency_self_loop", "ADJACENCY", ["a"], [("a", "a")], ret={"a": ["a", "a"]},
       tags=["build", "edge-values"], visible=True,
       doc="A self-loop is added under both ends, which for a self-loop is twice."),
    _c("adjacency_duplicate_edge", "ADJACENCY", ["a", "b"], [("a", "b"), ("a", "b")],
       ret={"a": ["b", "b"], "b": ["a", "a"]}, tags=["build", "edge-values"],
       why="a repeated edge is not deduplicated; the caller asked for the edges given"),
    _c("adjacency_empty", "ADJACENCY", [], [], ret={}, tags=["build", "edge-values"]),

    _c("degrees_basic", "DEGREES", ["a", "b", "c"], [("a", "b"), ("b", "c")],
       ret={"a": 1, "b": 2, "c": 1}, tags=["build"], visible=True,
       doc="b is touched by two edges."),
    _c("degrees_self_loop", "DEGREES", ["a"], [("a", "a")], ret={"a": 2},
       tags=["build", "edge-values"], visible=True,
       doc="A self-loop touches its node at BOTH ends, so it counts twice."),
    _c("degrees_isolated", "DEGREES", ["a", "b"], [], ret={"a": 0, "b": 0},
       tags=["build", "edge-values"]),
    _c("degrees_empty", "DEGREES", [], [], ret={}, tags=["build", "edge-values"]),

    _c("components_one", "COMPONENTS", ["a", "b", "c"], [("a", "b"), ("b", "c")], ret=1,
       tags=["components"], visible=True, doc="All joined up."),
    _c("components_two", "COMPONENTS", ["a", "b", "c", "d"], [("a", "b"), ("c", "d")],
       ret=2, tags=["components"], visible=True, doc="Two separate pairs."),
    _c("components_isolated", "COMPONENTS", ["a", "b", "c"], [], ret=3,
       tags=["components", "edge-values"], visible=True,
       doc="No edges at all: every node is its own piece."),
    _c("components_empty", "COMPONENTS", [], [], ret=0,
       tags=["components", "edge-values"]),
    _c("components_ring", "COMPONENTS", ["a", "b", "c"],
       [("a", "b"), ("b", "c"), ("c", "a")], ret=1, tags=["components"],
       why="a cycle is still one piece; revisiting a node must not start a new count"),

    _c("cycle_directed_true", "HAS_CYCLE_DIRECTED", ["a", "b", "c"],
       [("a", "b"), ("b", "c"), ("c", "a")], ret=True,
       tags=["cycle"], visible=True, doc="a to b to c and back to a."),
    _c("cycle_directed_false", "HAS_CYCLE_DIRECTED", ["a", "b", "c"],
       [("a", "b"), ("b", "c")], ret=False, tags=["cycle"], visible=True,
       doc="A straight chain."),
    _c("cycle_directed_diamond", "HAS_CYCLE_DIRECTED", ["a", "b", "c", "d"],
       [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")], ret=False,
       tags=["cycle", "edge-values"], visible=True,
       doc="d is reached twice, by two different paths, and there is still no cycle. "
           "A plain visited set says True here and is wrong."),
    _c("cycle_directed_self_loop", "HAS_CYCLE_DIRECTED", ["a"], [("a", "a")], ret=True,
       tags=["cycle", "edge-values"], visible=True, doc="A node pointing at itself."),
    # From `drill_mutation.py --triage`: the only self-loop case was an ISOLATED node, so
    # the loop was always found by a traversal that started on the looping node itself.
    # Reaching it from elsewhere first exercises a different branch of the state machine.
    _c("cycle_directed_self_loop_reached", "HAS_CYCLE_DIRECTED", ["a", "b"],
       [("b", "b"), ("a", "b")], ret=True, tags=["cycle", "edge-values"], visible=True,
       doc="b loops onto itself and is also reachable from a, so the walk may arrive at "
           "it either way round."),
    _c("cycle_directed_two_way", "HAS_CYCLE_DIRECTED", ["a", "b"],
       [("a", "b"), ("b", "a")], ret=True, tags=["cycle"],
       why="two opposite directed edges are a cycle of length two"),
    _c("cycle_directed_one_way_pair", "HAS_CYCLE_DIRECTED", ["a", "b"],
       [("a", "b")], ret=False, tags=["cycle", "edge-values"],
       why="one directed edge is not a cycle, though the undirected reading would loop"),
    _c("cycle_directed_empty", "HAS_CYCLE_DIRECTED", [], [], ret=False,
       tags=["cycle", "edge-values"]),
    _c("cycle_directed_disconnected", "HAS_CYCLE_DIRECTED", ["a", "b", "c", "d"],
       [("a", "b"), ("c", "d"), ("d", "c")], ret=True, tags=["cycle"],
       why="the cycle is in the second component, so every node must be a possible start"),

    _c("bipartite_path", "IS_BIPARTITE", ["a", "b", "c"], [("a", "b"), ("b", "c")],
       ret=True, tags=["colouring"], visible=True, doc="Alternate the colours along it."),
    _c("bipartite_odd_ring", "IS_BIPARTITE", ["a", "b", "c"],
       [("a", "b"), ("b", "c"), ("c", "a")], ret=False,
       tags=["colouring"], visible=True,
       doc="A ring of three: the third node must clash with one of the other two. Odd "
           "cycles are exactly what makes a graph non-bipartite."),
    _c("bipartite_even_ring", "IS_BIPARTITE", ["a", "b", "c", "d"],
       [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")], ret=True,
       tags=["colouring"], visible=True, doc="A ring of four alternates cleanly."),
    _c("bipartite_self_loop", "IS_BIPARTITE", ["a"], [("a", "a")], ret=False,
       tags=["colouring", "edge-values"],
       why="a self-loop joins a node to itself, which no colouring survives"),
    _c("bipartite_disconnected_bad_piece", "IS_BIPARTITE", ["a", "b", "c", "d", "e"],
       [("a", "b"), ("c", "d"), ("d", "e"), ("e", "c")], ret=False,
       tags=["colouring"], visible=True,
       doc="The first piece is fine and the second is an odd ring. Starting the "
           "colouring only from the first node would miss it."),
    _c("bipartite_empty", "IS_BIPARTITE", [], [], ret=True,
       tags=["colouring", "edge-values"]),
    _c("bipartite_isolated", "IS_BIPARTITE", ["a", "b"], [], ret=True,
       tags=["colouring", "edge-values"]),

    _c("reach_two_steps", "REACHABLE_WITHIN", ["a", "b", "c", "d"],
       [("a", "b"), ("b", "c"), ("c", "d")], "a", 2, ret=["a", "b", "c"],
       tags=["checkpoint"], visible=True,
       doc="Within two edges of a, including a itself at zero."),
    _c("reach_zero_steps", "REACHABLE_WITHIN", ["a", "b"], [("a", "b")], "a", 0,
       ret=["a"], tags=["checkpoint", "edge-values"], visible=True,
       doc="Zero steps still includes the start."),
    _c("reach_sorted_not_visit_order", "REACHABLE_WITHIN", ["a", "b", "z"],
       [("a", "z"), ("a", "b")], "a", 1, ret=["a", "b", "z"],
       tags=["checkpoint"], visible=True,
       doc="z is visited before b, and the answer is sorted regardless."),
    _c("reach_unknown_start", "REACHABLE_WITHIN", ["a"], [], "q", 3, ret=[],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="An unknown start reaches nothing, not even itself."),
    _c("reach_beyond_graph", "REACHABLE_WITHIN", ["a", "b"], [("a", "b")], "a", 99,
       ret=["a", "b"], tags=["checkpoint", "edge-values"]),
    _c("reach_negative_steps", "REACHABLE_WITHIN", ["a"], [], "a", -1, ret=[],
       tags=["checkpoint", "edge-values"],
       why="fewer than zero steps cannot even include the start"),
    # From `drill_mutation.py --triage`: no case combined a self-loop with steps left to
    # spend, so a walk that re-visits what it has already seen never revealed itself --
    # it simply looped forever, which no other case gave it the chance to do.
    # The step count is large ON PURPOSE. A walk that re-enqueues what it has already
    # seen still terminates on a small budget -- the frontier merely doubles each round.
    # At 99 it doubles ninety-nine times, which is the difference between a case that
    # passes a broken answer and one that does not.
    _c("reach_self_loop", "REACHABLE_WITHIN", ["a", "b"], [("a", "a"), ("a", "b")],
       "a", 99, ret=["a", "b"], tags=["checkpoint", "edge-values"], visible=True,
       doc="a loops onto itself, with far more steps than the graph needs. Revisiting a "
           "node must not spend a step and must not re-expand it."),
    _c("reach_disconnected", "REACHABLE_WITHIN", ["a", "b", "c"], [("b", "c")], "a", 5,
       ret=["a"], tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="graphs",
    title="2.11 Graph",
    blurb="Adjacency lists, degrees, components, directed cycles and two-colouring.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("traverse", "components", "cycle"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.11 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
