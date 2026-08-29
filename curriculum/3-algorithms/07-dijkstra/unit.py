"""3.7 Dijkstra — shortest path when the edges have weights.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **shortest path with weights, all non-negative**. BFS answers the unweighted
case because every edge costs the same, so the first arrival is the cheapest. Once edges
differ, that stops being true and the queue has to be ordered by cost so far -- which is a
heap.

The non-negative condition is not a footnote. Dijkstra settles a node the first time it
comes off the heap and never revisits it; a negative edge could make a settled node cheaper
later, and the algorithm would already have moved on. That is what Bellman-Ford is for, and
knowing which one a question needs is half of what is being tested.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="SHORTEST_COSTS",
        fuzz=("edges", "nonneg"),
        signature="(edges: list[tuple[str, str, int]], start: str) -> dict[str, int]",
        doc="The cheapest total cost from `start` to every reachable node, including "
            "`start` at 0. Edges are directed and their weights are non-negative. "
            "Unreachable nodes are absent, and an unknown start gives an empty dict.",
        constraint_note="a heap ordered by cost so far; settle each node once",
        constraints=(
            RequireCall(("heappush", "heappop"),
                        because="a plain queue gives the fewest EDGES, not the cheapest "
                                "cost -- the moment weights differ, the order things come "
                                "out in has to be by cost",
                        hint="push (cost, node); skip anything popped that is already "
                             "settled"),
        ),
    ),
    Method(
        display="SHORTEST_TO",
        fuzz=("edges", "nonneg"),
        signature="(edges: list[tuple[str, str, int]], start: str, goal: str) -> int",
        doc="The cheapest cost from `start` to `goal`, or -1 when unreachable. 0 when they "
            "are the same known node.",
        constraint_note="stop as soon as the goal is settled; do not finish the whole graph",
        constraints=(
            RequireCall(("heappush", "heappop"),
                        because="the first time the goal comes OFF the heap its cost is "
                                "final, so there is no reason to relax the rest of the "
                                "graph -- and knowing why that is safe is the point",
                        hint="return the moment you pop the goal"),
        ),
    ),
    Method(
        display="SLOWEST_ARRIVAL",
        fuzz=("edges", "nonneg"),
        signature="(edges: list[tuple[str, str, int]], nodes: list[str], start: str) -> int",
        doc="How long until a signal from `start` reaches every node in `nodes`: the "
            "LARGEST of the shortest costs. -1 when any node is unreachable.",
        # Network delay time. The answer is a maximum over minima, which reads backwards
        # the first few times.
        # A RequireCall on heappush was the first attempt and is a false positive waiting
        # to happen: the natural answer DELEGATES to SHORTEST_COSTS above, and constraints
        # are checked per function, so reusing your own work would be flagged. What the
        # drill is really about is that the answer is a maximum and not a total.
        constraint_note="the answer is the largest of the cheapest costs, not their sum",
        constraints=(
            ForbidCall(("sum",),
                       because="every node is reached by its own cheapest route, and the "
                               "signal is finished when the LAST of them arrives -- a "
                               "maximum over minima, which reads backwards the first few "
                               "times and is nothing like a total",
                       hint="run SHORTEST_COSTS, then take the max and check the count"),
        ),
    ),
    Method(
        display="MAX_PROBABILITY",
        fuzz=("edges", "nonneg"),
        signature="(edges: list[tuple[str, str, int]], start: str, goal: str) -> int",
        doc="Edge weights are percentages from 0 to 100, and a path's score is the product "
            "of its edges divided by 100 for each step after the first -- so a two-edge "
            "path of 50 and 50 scores 25. The HIGHEST score reachable, as an integer using "
            "integer division at each step. 100 when start and goal are the same known "
            "node, and 0 when unreachable.",
        constraint_note="a max-heap by score; the same settle-once argument runs upwards",
        constraints=(
            RequireCall(("heappush", "heappop"),
                        because="multiplying probabilities shrinks a path exactly as adding "
                                "weights grows one, so the same algorithm works with the "
                                "comparison reversed -- negate the score to use a min-heap",
                        hint="push (-score, node) and settle the best score per node"),
        ),
    ),
    Method(
        display="CHEAPEST_WITH_STOPS",
        fuzz=("edges", "nonneg"),
        signature="(edges: list[tuple[str, str, int]], start: str, goal: str, "
                  "stops: int) -> int",
        doc="The cheapest cost from `start` to `goal` using at most `stops` intermediate "
            "nodes -- so `stops` of 0 means a direct edge only. -1 when there is none.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Dijkstra", theme="cheapest first, and settle once"),)

TAG_GLOSSARY = {
    "relax": "improving a node's best known cost",
    "settle": "why the first pop is final",
    "early-exit": "stopping once the goal is known",
    "reversed": "the same algorithm maximising instead of minimising",
    "bounded": "a limit that makes the settle-once argument fail",
    "edge-values": "unknown nodes, unreachable goals, zero-cost edges",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("costs_chain", "SHORTEST_COSTS", [("a", "b", 1), ("b", "c", 2)], "a",
       ret={"a": 0, "b": 1, "c": 3}, tags=["relax"], visible=True,
       doc="Costs accumulate along the route."),
    _c("costs_cheaper_longer_route", "SHORTEST_COSTS",
       [("a", "b", 10), ("a", "c", 1), ("c", "b", 1)], "a",
       ret={"a": 0, "b": 2, "c": 1}, tags=["relax", "settle"], visible=True,
       doc="b is one edge away at cost 10 and two edges away at cost 2. A breadth-first "
           "walk answers 10 here, which is what makes this Dijkstra and not BFS."),
    _c("costs_unreachable_absent", "SHORTEST_COSTS", [("a", "b", 1), ("c", "d", 1)], "a",
       ret={"a": 0, "b": 1}, tags=["relax", "edge-values"], visible=True,
       doc="Another component simply does not appear."),
    _c("costs_zero_weight", "SHORTEST_COSTS", [("a", "b", 0)], "a", ret={"a": 0, "b": 0},
       tags=["relax", "edge-values"], visible=True,
       doc="A zero-cost edge is allowed, and 0 is a real cost rather than 'no route'."),
    _c("costs_unknown_start", "SHORTEST_COSTS", [("a", "b", 1)], "z", ret={},
       tags=["relax", "edge-values"]),
    _c("costs_directed", "SHORTEST_COSTS", [("a", "b", 1)], "b", ret={"b": 0},
       tags=["relax", "edge-values"],
       why="edges are one-way, so nothing is reachable from b"),
    _c("costs_no_edges", "SHORTEST_COSTS", [], "a", ret={},
       tags=["relax", "edge-values"]),

    _c("to_basic", "SHORTEST_TO", [("a", "b", 1), ("b", "c", 2)], "a", "c", ret=3,
       tags=["early-exit"], visible=True, doc="The whole route."),
    _c("to_cheaper_detour", "SHORTEST_TO",
       [("a", "b", 10), ("a", "c", 1), ("c", "b", 1)], "a", "b", ret=2,
       tags=["early-exit", "settle"], visible=True,
       doc="The detour is cheaper, and must not be settled before it is found."),
    _c("to_same_node", "SHORTEST_TO", [("a", "b", 1)], "a", "a", ret=0,
       tags=["early-exit", "edge-values"], visible=True, doc="Already there."),
    _c("to_unreachable", "SHORTEST_TO", [("a", "b", 1)], "b", "a", ret=-1,
       tags=["early-exit", "edge-values"], visible=True, doc="Edges are directed."),
    _c("to_unknown", "SHORTEST_TO", [("a", "b", 1)], "z", "a", ret=-1,
       tags=["early-exit", "edge-values"]),
    # From triage: every same-node case used a node that appears in an edge, so the
    # "known" half of "the same KNOWN node" was never tested on its own.
    _c("to_same_unknown_node", "SHORTEST_TO", [], "z", "z", ret=-1,
       tags=["early-exit", "edge-values"], visible=True,
       doc="Start and goal are the same, and the node appears in no edge -- so it is "
           "unknown, and the answer is -1 rather than 0."),
    _c("to_no_edges", "SHORTEST_TO", [], "a", "b", ret=-1,
       tags=["early-exit", "edge-values"]),

    _c("slowest_basic", "SLOWEST_ARRIVAL", [("a", "b", 1), ("a", "c", 4)],
       ["a", "b", "c"], "a", ret=4, tags=["relax"], visible=True,
       doc="The last arrival decides, so 4 rather than 5."),
    _c("slowest_chain", "SLOWEST_ARRIVAL", [("a", "b", 1), ("b", "c", 1)],
       ["a", "b", "c"], "a", ret=2, tags=["relax"], visible=True,
       doc="c is two hops of 1, so the signal is done at 2."),
    _c("slowest_unreachable", "SLOWEST_ARRIVAL", [("a", "b", 1)], ["a", "b", "c"], "a",
       ret=-1, tags=["relax", "edge-values"], visible=True,
       doc="One node never hears it at all."),
    _c("slowest_single", "SLOWEST_ARRIVAL", [], ["a"], "a", ret=0,
       tags=["relax", "edge-values"], visible=True,
       doc="Only the start, which hears it immediately."),
    _c("slowest_empty_nodes", "SLOWEST_ARRIVAL", [], [], "a", ret=0,
       tags=["relax", "edge-values"]),

    _c("prob_basic", "MAX_PROBABILITY", [("a", "b", 50), ("b", "c", 50)], "a", "c",
       ret=25, tags=["reversed"], visible=True, doc="50 then 50 gives 25."),
    _c("prob_better_longer", "MAX_PROBABILITY",
       [("a", "c", 20), ("a", "b", 50), ("b", "c", 60)], "a", "c", ret=30,
       tags=["reversed"], visible=True,
       doc="The direct edge scores 20 and the two-edge route scores 30, so MORE edges "
           "can be better -- the opposite of the cost version."),
    _c("prob_same_node", "MAX_PROBABILITY", [("a", "b", 50)], "a", "a", ret=100,
       tags=["reversed", "edge-values"], visible=True,
       doc="Certainty, expressed as 100."),
    _c("prob_unreachable", "MAX_PROBABILITY", [("a", "b", 50)], "b", "a", ret=0,
       tags=["reversed", "edge-values"], visible=True, doc="No route at all."),
    _c("prob_zero_edge", "MAX_PROBABILITY", [("a", "b", 0)], "a", "b", ret=0,
       tags=["reversed", "edge-values"]),
    _c("prob_same_unknown_node", "MAX_PROBABILITY", [], "b", "b", ret=0,
       tags=["reversed", "edge-values"], visible=True,
       doc="The same node, and unknown, so 0 rather than the certainty of 100."),
    _c("prob_no_edges", "MAX_PROBABILITY", [], "a", "b", ret=0,
       tags=["reversed", "edge-values"]),

    _c("stops_direct_only", "CHEAPEST_WITH_STOPS",
       [("a", "b", 100), ("a", "c", 40), ("c", "b", 40)], "a", "b", 0, ret=100,
       tags=["checkpoint", "bounded"], visible=True,
       doc="With no stops allowed, only the direct edge counts."),
    _c("stops_one_allowed", "CHEAPEST_WITH_STOPS",
       [("a", "b", 100), ("a", "c", 40), ("c", "b", 40)], "a", "b", 1, ret=80,
       tags=["checkpoint", "bounded"], visible=True,
       doc="One stop allows the cheaper two-edge route. This is why the settle-once rule "
           "fails here: reaching c cheaply is worthless if it used too many stops."),
    _c("stops_same_node", "CHEAPEST_WITH_STOPS", [("a", "b", 1)], "a", "a", 0, ret=0,
       tags=["checkpoint", "edge-values"], visible=True, doc="Already there."),
    _c("stops_unreachable", "CHEAPEST_WITH_STOPS", [("a", "b", 1)], "b", "a", 5, ret=-1,
       tags=["checkpoint", "edge-values"]),
    _c("stops_negative", "CHEAPEST_WITH_STOPS", [("a", "b", 1)], "a", "b", -1, ret=-1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Fewer than zero stops permits nothing, not even a direct edge."),
    _c("stops_same_unknown_node", "CHEAPEST_WITH_STOPS", [], "c", "c", 40, ret=-1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="An unknown node is not 'already there'."),
    _c("stops_same_node_negative_stops", "CHEAPEST_WITH_STOPS", [], "a", "a", -1, ret=-1,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Both guards apply at once, and either alone is enough to refuse."),
    _c("stops_no_edges", "CHEAPEST_WITH_STOPS", [], "a", "b", 3, ret=-1,
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="dijkstra",
    title="3.7 Dijkstra",
    blurb="Shortest weighted costs, early exit, network delay, and a bounded-stop variant.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="hard",
    topics=("relax", "settle", "reversed"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.7 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
