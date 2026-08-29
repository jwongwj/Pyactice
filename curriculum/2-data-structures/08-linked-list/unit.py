"""2.8 Linked list — pointers, and the two-pointer tricks they make possible.

Self-contained: loaded by file path, so no package-relative imports.

Python has no linked list and you would rarely write one, which is exactly why it is worth
drilling: the questions are not about the structure, they are about manipulating references
without losing the rest of the chain. Reverse, cycle detection and nth-from-the-end are
three different uses of the same idea -- more than one pointer walking at once.

The node type is authored ONCE, here, and exec'd to build the cases. The identical source
goes into the learner's starter file as the problem's preamble, so a node the test passes
in and a node the learner builds are the same shape and compare equal.

The catalogue's build exercises -- a doubly linked list with O(1) removal, and the LRU
cache built from one -- are classes, so they arrive as `design` problems.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

PREAMBLE = '''
class Node:
    """One link in a singly linked list.

    `__eq__` compares the whole chain by value, which is what lets a test say
    "the answer is 3 -> 2 -> 1" without caring which object identities got there.
    It reads `value` and `next` off the other node rather than checking its type,
    so a node you build compares equal to one the tests built.
    """

    def __init__(self, value: int, next: "Node | None" = None) -> None:
        self.value = value
        self.next = next

    def __eq__(self, other: object) -> bool:
        # Named `here`/`there` rather than `left`/`right` on purpose: with those names
        # this loop header is character-for-character the one MERGE_CHAINS needs, and
        # the preamble is printed in that drill's statement.
        here: "Node | None" = self
        there = other
        while here is not None and there is not None:
            if here.value != getattr(there, "value", object()):
                return False
            here, there = here.next, getattr(there, "next", None)
        return here is None and there is None

    def __repr__(self) -> str:
        parts, seen, node = [], set(), self
        while node is not None and id(node) not in seen:
            seen.add(id(node))
            parts.append(str(node.value))
            node = node.next
        return " -> ".join(parts) + (" -> ...(cycle)" if node is not None else "")
'''

_NS: dict = {}
exec(PREAMBLE, _NS)
Node = _NS["Node"]


def chain(values, cycle_at=None):
    """Build a chain from values. `cycle_at` points the last node back at that index."""
    head = None
    nodes = []
    for value in reversed(values):
        head = Node(value, head)
        nodes.append(head)
    if cycle_at is not None and nodes:
        nodes[0].next = nodes[len(values) - 1 - cycle_at]
    return head


METHODS = (
    Method(
        display="LENGTH",
        signature="(head: Node | None) -> int",
        doc="How many nodes are in the chain. 0 for an empty one.",
        constraint_note="walk it with a while loop; there is nothing to call len() on",
        constraints=(
            ForbidCall(("len",),
                       because="a chain has no length to ask for -- you find out by "
                               "walking it, which is the whole difference from a list",
                       hint="node = head, then while node: count += 1; node = node.next"),
        ),
    ),
    Method(
        display="TO_LIST",
        signature="(head: Node | None) -> list[int]",
        doc="The values in order, as a plain list.",
        constraint_note="one walk, collecting as you go",
        constraints=(
            Forbid(("recursion",),
                   because="a chain of ten thousand nodes will exhaust the stack; the "
                           "iterative walk is both simpler and safe",
                   hint="while node is not None: out.append(node.value); node = node.next"),
        ),
    ),
    Method(
        display="REVERSED_CHAIN",
        signature="(head: Node | None) -> Node | None",
        doc="The same nodes, chained in the opposite order.",
        # Three names and one loop. The trap is losing the rest of the chain: as soon as
        # you overwrite node.next you cannot reach what came after unless you saved it.
        constraint_note="re-point in place with three names; do not build new nodes",
        constraints=(
            ForbidCall(("Node", "reversed", "sorted"),
                       because="rebuilding the chain out of new nodes sidesteps the "
                               "pointer work this exists to teach",
                       hint="previous, node = None, head; save node.next BEFORE "
                            "overwriting it"),
        ),
    ),
    Method(
        display="HAS_CYCLE",
        signature="(head: Node | None) -> bool",
        doc="True when following `next` never reaches None.",
        constraint_note="Floyd: a slow and a fast pointer, and no set of seen nodes",
        constraints=(
            ForbidCall(("set", "id", "dict"),
                       because="remembering every node visited is O(n) memory and works; "
                               "two pointers at different speeds is O(1), and is the "
                               "answer the question is looking for",
                       hint="slow moves one, fast moves two; they meet iff there is a cycle"),
        ),
    ),
    Method(
        display="MERGE_CHAINS",
        signature="(left: Node | None, right: Node | None) -> Node | None",
        doc="One ascending chain from two already-ascending chains. Keeps duplicates.",
        # Forbidding `Node` here was the first attempt and contradicts its own hint: the
        # standard dummy-head splice needs a throwaway node, so the constraint would have
        # banned the technique it recommends. Only the shortcut is forbidden now.
        constraint_note="splice the existing nodes together; a dummy head is fine",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="the nodes already exist and both chains are already "
                               "ordered -- collecting the values out to sort them throws "
                               "both facts away",
                       hint="a dummy head makes the first splice the same as every other"),
        ),
    ),
    Method(
        display="DROP_NTH_FROM_END",
        signature="(head: Node | None, n: int) -> Node | None",
        doc="The chain without the nth node counting from the end, where n=1 is the last. "
            "Unchanged when n is larger than the chain, or less than 1.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Linked list", theme="more than one pointer walking at once"),)

TAG_GLOSSARY = {
    "traverse": "walking a chain to its end",
    "repoint": "changing next without losing the rest",
    "two-pointer": "two references moving at different speeds or offsets",
    "merge": "combining two already-ordered chains",
    "edge-values": "empty chains, one node, n out of range",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("length_three", "LENGTH", chain([1, 2, 3]), ret=3,
       tags=["traverse"], visible=True, doc="Three nodes."),
    _c("length_one", "LENGTH", chain([7]), ret=1, tags=["traverse", "edge-values"]),
    _c("length_empty", "LENGTH", None, ret=0, tags=["traverse", "edge-values"],
       visible=True, doc="An empty chain is None, not a node."),

    _c("to_list_basic", "TO_LIST", chain([1, 2, 3]), ret=[1, 2, 3],
       tags=["traverse"], visible=True, doc="In order."),
    _c("to_list_single", "TO_LIST", chain([9]), ret=[9], tags=["traverse", "edge-values"]),
    _c("to_list_empty", "TO_LIST", None, ret=[], tags=["traverse", "edge-values"]),
    _c("to_list_duplicates", "TO_LIST", chain([2, 2]), ret=[2, 2], tags=["traverse"]),

    _c("reverse_basic", "REVERSED_CHAIN", chain([1, 2, 3]), ret=chain([3, 2, 1]),
       tags=["repoint"], visible=True, doc="1 -> 2 -> 3 becomes 3 -> 2 -> 1."),
    _c("reverse_two", "REVERSED_CHAIN", chain([1, 2]), ret=chain([2, 1]),
       tags=["repoint"], why="two nodes is the smallest case where anything moves"),
    _c("reverse_single", "REVERSED_CHAIN", chain([5]), ret=chain([5]),
       tags=["repoint", "edge-values"], visible=True,
       doc="One node reverses to itself, and its next must end up None."),
    _c("reverse_empty", "REVERSED_CHAIN", None, ret=None,
       tags=["repoint", "edge-values"]),
    _c("reverse_four", "REVERSED_CHAIN", chain([1, 2, 3, 4]), ret=chain([4, 3, 2, 1]),
       tags=["repoint"],
       why="the old head must end up pointing at None, not at the node after it"),

    _c("cycle_none", "HAS_CYCLE", chain([1, 2, 3]), ret=False,
       tags=["two-pointer"], visible=True, doc="Ends at None."),
    _c("cycle_at_start", "HAS_CYCLE", chain([1, 2, 3], cycle_at=0), ret=True,
       tags=["two-pointer"], visible=True, doc="The last node points back at the head."),
    _c("cycle_in_middle", "HAS_CYCLE", chain([1, 2, 3, 4], cycle_at=2), ret=True,
       tags=["two-pointer"], visible=True,
       doc="A tail that loops onto itself part-way -- there is still a run-in before it."),
    _c("cycle_self_loop", "HAS_CYCLE", chain([1], cycle_at=0), ret=True,
       tags=["two-pointer", "edge-values"],
       why="one node pointing at itself is the shortest possible cycle"),
    _c("cycle_single_no_loop", "HAS_CYCLE", chain([1]), ret=False,
       tags=["two-pointer", "edge-values"],
       why="the fast pointer must not read .next off None on a one-node chain"),
    _c("cycle_empty", "HAS_CYCLE", None, ret=False,
       tags=["two-pointer", "edge-values"]),

    _c("merge_interleaved", "MERGE_CHAINS", chain([1, 4]), chain([2, 3]),
       ret=chain([1, 2, 3, 4]), tags=["merge"], visible=True,
       doc="Take the smaller head each step."),
    _c("merge_one_empty", "MERGE_CHAINS", None, chain([1, 2]), ret=chain([1, 2]),
       tags=["merge", "edge-values"], visible=True,
       doc="One side empty: the other is the answer."),
    # Both found because `drill_mutation.py --triage` reported these survivors as
    # UNJUDGED rather than null: every case here happened to take its first node from the
    # LEFT chain, and every empty-side case put the empty side on the left. Two blind
    # spots that a symmetric-looking set of cases hid.
    _c("merge_right_head_smaller", "MERGE_CHAINS", chain([5]), chain([1, 2]),
       ret=chain([1, 2, 5]), tags=["merge"], visible=True,
       doc="The answer starts in the RIGHT chain, so the very first choice has to be "
           "made rather than assumed."),
    _c("merge_right_empty", "MERGE_CHAINS", chain([1, 2]), None, ret=chain([1, 2]),
       tags=["merge", "edge-values"], visible=True,
       doc="The mirror of the case above it: an empty chain on the right is just as "
           "valid as one on the left."),
    _c("merge_both_empty", "MERGE_CHAINS", None, None, ret=None,
       tags=["merge", "edge-values"]),
    _c("merge_duplicates", "MERGE_CHAINS", chain([2]), chain([2]), ret=chain([2, 2]),
       tags=["merge"], why="duplicates are kept, not collapsed"),
    _c("merge_tail_left_over", "MERGE_CHAINS", chain([1, 2, 3]), chain([9]),
       ret=chain([1, 2, 3, 9]), tags=["merge"],
       why="the loop ends when one side runs out; the other's remainder must be attached"),

    _c("drop_last", "DROP_NTH_FROM_END", chain([1, 2, 3]), 1, ret=chain([1, 2]),
       tags=["checkpoint", "two-pointer"], visible=True, doc="n=1 is the last node."),
    _c("drop_middle", "DROP_NTH_FROM_END", chain([1, 2, 3]), 2, ret=chain([1, 3]),
       tags=["checkpoint"], visible=True, doc="n=2 counts back two from the end."),
    _c("drop_head", "DROP_NTH_FROM_END", chain([1, 2, 3]), 3, ret=chain([2, 3]),
       tags=["checkpoint", "edge-values"], visible=True,
       doc="n equal to the length removes the HEAD, so the answer starts somewhere else."),
    _c("drop_only_node", "DROP_NTH_FROM_END", chain([5]), 1, ret=None,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Removing the only node leaves an empty chain."),
    _c("drop_n_too_big", "DROP_NTH_FROM_END", chain([1, 2]), 5, ret=chain([1, 2]),
       tags=["checkpoint", "edge-values"]),
    _c("drop_n_zero", "DROP_NTH_FROM_END", chain([1, 2]), 0, ret=chain([1, 2]),
       tags=["checkpoint", "edge-values"], why="n counts from 1, so 0 removes nothing"),
    _c("drop_from_empty", "DROP_NTH_FROM_END", None, 1, ret=None,
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="linked_lists",
    title="2.8 Linked list",
    blurb="Walking a chain, re-pointing it, Floyd's cycle detection and merging.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("repoint", "two-pointer", "merge"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    preamble=PREAMBLE,
    source="Curriculum unit 2.8 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
