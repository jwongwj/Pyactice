"""3.9 Topological sort — dependencies, and the order that satisfies them.

Self-contained: loaded by file path, so no package-relative imports.

The cue is **"must come before"** in any wording: prerequisites, build order, task
dependencies, install order. The answer is always the same shape, and the useful fact is
that the algorithm also *detects impossibility*: a set of dependencies with a cycle has no
valid order, and Kahn's algorithm reports it for free by finishing early.

Kahn's, in one paragraph: count how many things each item is waiting for; start with the
items waiting for nothing; every time an item is emitted, decrement its dependents and emit
any that reach zero. If items remain when the queue empties, they are in a cycle.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="IN_DEGREES",
        signature="(items: list[str], befores: list[tuple[str, str]]) -> dict[str, int]",
        doc="How many things each item must wait for. `(a, b)` means a must come before b, "
            "so it adds one to b's count. Every item is a key, even at zero. Pairs naming "
            "an unknown item are ignored.",
        # Forbidding `if` was the first attempt and contradicts this drill's own rule
        # that unknown items are ignored -- which needs a condition. What the constraint
        # is actually for is the SEED: an item nothing depends on must still appear, and
        # setdefault or defaultdict would create keys only for items that are depended on.
        constraint_note="seed every item at zero first, then count; no setdefault",
        constraints=(
            ForbidCall(("setdefault", "defaultdict", "Counter"),
                       because="building the dict as you go creates a key only for items "
                               "something depends ON -- and the items with no key are "
                               "exactly the ones a topological sort has to start from",
                       hint="{item: 0 for item in items}, then count the second of each pair"),
        ),
    ),
    Method(
        display="TOPO_ORDER",
        signature="(items: list[str], befores: list[tuple[str, str]]) -> list[str]",
        doc="An order satisfying every 'a before b'. Where several are valid, the "
            "alphabetically smallest available item is chosen at each step, so the answer "
            "is unique. Empty when no order exists. Pairs naming an unknown item are "
            "ignored.",
        constraint_note="Kahn's: emit what is waiting for nothing, then relax its dependents",
        constraints=(
            Forbid(("recursion",),
                   because="the depth-first version also works and reports cycles less "
                           "directly; Kahn's makes 'no valid order' fall out of the "
                           "algorithm rather than needing a separate check",
                   hint="a heap or a repeatedly-sorted list of the ready items keeps the "
                        "alphabetical tie-break"),
        ),
    ),
    Method(
        display="CAN_FINISH",
        signature="(items: list[str], befores: list[tuple[str, str]]) -> bool",
        doc="Is any valid order possible? False exactly when the dependencies contain a "
            "cycle. Pairs naming an unknown item are ignored.",
        constraint_note="count what you managed to emit; anything left is in a cycle",
        constraints=(
            Forbid(("recursion",),
                   because="this is TOPO_ORDER stopping at the count rather than the "
                           "sequence -- recognising that one answers the other is the drill",
                   hint="if fewer items came out than went in, something is stuck"),
        ),
    ),
    Method(
        display="DEPTH_LEVELS",
        signature="(items: list[str], befores: list[tuple[str, str]]) -> list[list[str]]",
        doc="Items grouped by how many steps of dependency lie behind them: everything "
            "waiting for nothing, then everything that only waited for those, and so on. "
            "Each group sorted alphabetically. Empty when no order exists.",
        # This is the "how long does the build take with unlimited parallelism" question.
        constraint_note="drain a whole level at a time, exactly as in level-order BFS",
        constraints=(
            Forbid(("recursion",),
                   because="the number of groups is the length of the longest dependency "
                           "chain, which is what a build with unlimited parallelism costs",
                   hint="take len(ready) items per round, as with a tree's level order"),
        ),
    ),
    Method(
        display="ALIEN_ORDER",
        signature="(words: list[str]) -> str",
        doc="The alphabet implied by a list of words already sorted in that alphabet, as a "
            "string. Only letters appearing in the words are included, and where several "
            "alphabets fit, the alphabetically smallest available letter is chosen at each "
            "step. Empty when the list is contradictory -- including when a word is "
            "followed by a strict prefix of itself.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Topological sort", theme="dependencies, and detecting the impossible"),)

TAG_GLOSSARY = {
    "counting": "how many things each item waits for",
    "kahn": "emitting what is ready and relaxing its dependents",
    "cycle": "detecting that no order exists",
    "levels": "grouping by depth rather than sequencing",
    "inference": "deriving the dependencies before sorting them",
    "edge-values": "no items, no dependencies, unknown names, self-dependency",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("degrees_basic", "IN_DEGREES", ["a", "b", "c"], [("a", "b"), ("a", "c")],
       ret={"a": 0, "b": 1, "c": 1}, tags=["counting"], visible=True,
       doc="a waits for nothing; b and c each wait for a."),
    _c("degrees_no_pairs", "IN_DEGREES", ["a", "b"], [], ret={"a": 0, "b": 0},
       tags=["counting", "edge-values"], visible=True,
       doc="Every item is a key even at zero -- those are the ones a sort starts from."),
    _c("degrees_chain", "IN_DEGREES", ["a", "b", "c"], [("a", "b"), ("b", "c")],
       ret={"a": 0, "b": 1, "c": 1}, tags=["counting"]),
    _c("degrees_unknown_ignored", "IN_DEGREES", ["a"], [("a", "z")], ret={"a": 0},
       tags=["counting", "edge-values"], visible=True,
       doc="A pair naming an item that does not exist adds nothing and creates no key."),
    _c("degrees_duplicate_pair", "IN_DEGREES", ["a", "b"], [("a", "b"), ("a", "b")],
       ret={"a": 0, "b": 2}, tags=["counting", "edge-values"],
       why="a repeated dependency is counted twice, and must be relaxed twice too"),
    _c("degrees_empty", "IN_DEGREES", [], [], ret={}, tags=["counting", "edge-values"]),

    _c("topo_chain", "TOPO_ORDER", ["c", "b", "a"], [("a", "b"), ("b", "c")],
       ret=["a", "b", "c"], tags=["kahn"], visible=True,
       doc="Input order does not matter; the dependencies decide."),
    _c("topo_tie_alphabetical", "TOPO_ORDER", ["b", "a"], [], ret=["a", "b"],
       tags=["kahn"], visible=True,
       doc="Nothing depends on anything, so the alphabetical tie-break decides."),
    _c("topo_diamond", "TOPO_ORDER", ["a", "b", "c", "d"],
       [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")],
       ret=["a", "b", "c", "d"], tags=["kahn"], visible=True,
       doc="b and c are both ready after a, and b is chosen first."),
    _c("topo_cycle", "TOPO_ORDER", ["a", "b"], [("a", "b"), ("b", "a")], ret=[],
       tags=["cycle"], visible=True, doc="A cycle, so no order exists."),
    _c("topo_self_dependency", "TOPO_ORDER", ["a"], [("a", "a")], ret=[],
       tags=["cycle", "edge-values"], visible=True,
       doc="An item waiting for itself is the shortest possible cycle."),
    _c("topo_empty", "TOPO_ORDER", [], [], ret=[], tags=["kahn", "edge-values"]),
    _c("topo_partial_cycle", "TOPO_ORDER", ["a", "b", "c"], [("b", "c"), ("c", "b")],
       ret=[], tags=["cycle"],
       why="one component sorts fine and the whole thing still has no valid order"),

    _c("finish_yes", "CAN_FINISH", ["a", "b"], [("a", "b")], ret=True,
       tags=["cycle"], visible=True, doc="A straight dependency."),
    _c("finish_no", "CAN_FINISH", ["a", "b"], [("a", "b"), ("b", "a")], ret=False,
       tags=["cycle"], visible=True, doc="A cycle."),
    _c("finish_no_deps", "CAN_FINISH", ["a", "b"], [], ret=True, tags=["cycle"]),
    _c("finish_empty", "CAN_FINISH", [], [], ret=True,
       tags=["cycle", "edge-values"], visible=True,
       doc="Nothing to order, which is trivially possible."),
    _c("finish_long_cycle", "CAN_FINISH", ["a", "b", "c"],
       [("a", "b"), ("b", "c"), ("c", "a")], ret=False, tags=["cycle"]),
    # From triage: the existing unknown-item case has the unknown on the LEFT of the
    # pair. A self-referential pair naming an item that does not exist is the shape that
    # separates "ignore the pair" from "create the item and then find its cycle".
    _c("finish_unknown_self_pair", "CAN_FINISH", ["a", "z", "c"],
       [("z", "a"), ("c", "z"), ("c", "a"), ("b", "b")], ret=True,
       tags=["cycle", "edge-values"], visible=True,
       doc="('b','b') is a self-dependency on an item that does not exist. Ignored, it "
           "changes nothing; created, it looks like a cycle and the answer flips."),
    _c("finish_unknown_ignored", "CAN_FINISH", ["a"], [("z", "a")], ret=True,
       tags=["cycle", "edge-values"]),

    _c("levels_chain", "DEPTH_LEVELS", ["a", "b", "c"], [("a", "b"), ("b", "c")],
       ret=[["a"], ["b"], ["c"]], tags=["levels"], visible=True,
       doc="A chain of three needs three rounds."),
    _c("levels_parallel", "DEPTH_LEVELS", ["a", "b", "c"], [("a", "b"), ("a", "c")],
       ret=[["a"], ["b", "c"]], tags=["levels"], visible=True,
       doc="b and c can be done at the same time, so two rounds."),
    _c("levels_none", "DEPTH_LEVELS", ["b", "a"], [], ret=[["a", "b"]],
       tags=["levels"], visible=True, doc="Everything at once, sorted within the group."),
    _c("levels_cycle", "DEPTH_LEVELS", ["a", "b"], [("a", "b"), ("b", "a")], ret=[],
       tags=["levels", "cycle"]),
    _c("levels_unknown_self_pair", "DEPTH_LEVELS", ["a", "d", "c"],
       [("d", "a"), ("c", "d"), ("c", "a"), ("b", "b")],
       ret=[["c"], ["d"], ["a"]], tags=["levels", "edge-values"], visible=True,
       doc="The same unknown self-dependency as in CAN_FINISH. Ignoring it leaves a "
           "clean three-level chain."),
    _c("levels_empty", "DEPTH_LEVELS", [], [], ret=[],
       tags=["levels", "edge-values"]),
    _c("levels_uneven", "DEPTH_LEVELS", ["a", "b", "c", "d"],
       [("a", "b"), ("b", "d")], ret=[["a", "c"], ["b"], ["d"]],
       tags=["levels"], visible=True,
       doc="c waits for nothing and appears in the first group even though the chain "
           "beside it is three long."),

    _c("alien_basic", "ALIEN_ORDER", ["ba", "bc", "ac"], ret="bac",
       tags=["checkpoint", "inference"], visible=True,
       doc="'ba' before 'bc' gives a < c; 'bc' before 'ac' gives b < a."),
    _c("alien_single_word", "ALIEN_ORDER", ["abc"], ret="abc",
       tags=["checkpoint", "inference"], visible=True,
       doc="One word implies nothing, so the letters come out alphabetically."),
    _c("alien_prefix_invalid", "ALIEN_ORDER", ["abc", "ab"], ret="",
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A word followed by a strict prefix of itself is contradictory in any "
           "alphabet, and this is the case that has nothing to do with letter order."),
    _c("alien_prefix_valid", "ALIEN_ORDER", ["ab", "abc"], ret="abc",
       tags=["checkpoint", "edge-values"], visible=True,
       doc="The same two words the other way round are perfectly consistent."),
    _c("alien_cycle", "ALIEN_ORDER", ["ab", "ba", "ab"], ret="",
       tags=["checkpoint", "cycle"], visible=True,
       doc="a before b and b before a."),
    _c("alien_empty", "ALIEN_ORDER", [], ret="",
       tags=["checkpoint", "edge-values"]),
    _c("alien_repeated_word", "ALIEN_ORDER", ["ab", "ab"], ret="ab",
       tags=["checkpoint", "edge-values"],
       why="two identical words imply nothing and are not a contradiction"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="topological",
    title="3.9 Topological sort",
    blurb="In-degrees, Kahn's algorithm, cycle detection, depth levels, alien order.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="hard",
    topics=("kahn", "cycle", "levels"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.9 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
