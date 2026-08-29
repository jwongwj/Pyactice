"""Doubly linked list with O(1) removal — the build exercise for unit 2.8.

The reason a doubly linked list exists: given a node, you can unlink it in constant time
without searching for its predecessor. That is the property the LRU cache beside this
problem is built on, and it is worth having written the unlink once.

Two sentinel nodes -- a head and a tail that hold no value -- remove every special case.
With them, insertion and removal have no branches at all.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="PUSH_FRONT", signature="(self, value: int) -> int", level=1,
           doc="Add a value at the front. Returns a handle for it -- an integer you can "
               "later pass to REMOVE. Handles are never reused."),
    Method(display="PUSH_BACK", signature="(self, value: int) -> int", level=1,
           doc="Add a value at the back, returning its handle."),
    Method(display="REMOVE", signature="(self, handle: int) -> bool", level=1,
           doc="Unlink the value with that handle in O(1). True when it was there, False "
               "when the handle is unknown or already removed."),
    Method(display="ITEMS", signature="(self) -> list[int]", level=1,
           doc="Every value, front to back."),
    Method(display="REVERSED_ITEMS", signature="(self) -> list[int]", level=1,
           doc="Every value, back to front, by walking the backward links."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many values are held."),
)

LEVELS = (Level(1, "Doubly linked list", theme="unlink without searching"),)

TAG_GLOSSARY = {
    "basics": "adding at each end",
    "unlink": "removing a node given only its handle",
    "both-ways": "the forward and backward chains agreeing",
    "handles": "unknown, stale and reused handles",
    "empty": "an empty list, and one emptied by removals",
}

CASES = (
    case("push_front_order", 1, [
        op("PUSH_FRONT", 1), op("PUSH_FRONT", 2), op("ITEMS", ret=[2, 1]),
        op("SIZE", ret=2),
    ], tags=["basics"], visible=True, doc="The most recent front push is first."),
    case("push_back_order", 1, [
        op("PUSH_BACK", 1), op("PUSH_BACK", 2), op("ITEMS", ret=[1, 2]),
    ], tags=["basics"], doc="Back pushes append."),
    case("both_ends", 1, [
        op("PUSH_BACK", 2), op("PUSH_FRONT", 1), op("PUSH_BACK", 3),
        op("ITEMS", ret=[1, 2, 3]),
    ], tags=["basics"], doc="Mixed, and the order is by position."),
    case("backward_chain_agrees", 1, [
        op("PUSH_BACK", 1), op("PUSH_BACK", 2), op("PUSH_BACK", 3),
        op("ITEMS", ret=[1, 2, 3]), op("REVERSED_ITEMS", ret=[3, 2, 1]),
    ], tags=["both-ways"], visible=True,
       doc="Walking backwards must give the exact reverse. A `prev` link left dangling on "
           "insertion shows up here and nowhere else."),
    case("remove_middle", 1, [
        op("PUSH_BACK", 1), op("PUSH_BACK", 2, ret=1), op("PUSH_BACK", 3),
        op("REMOVE", 1, ret=True), op("ITEMS", ret=[1, 3]),
        op("REVERSED_ITEMS", ret=[3, 1]), op("SIZE", ret=2),
    ], tags=["unlink", "both-ways"], visible=True,
       doc="Removing from the middle by handle, with no search. Both chains have to be "
           "repaired, and the second handle is 1 because handles count from 0."),
    case("remove_front_and_back", 1, [
        op("PUSH_BACK", 1, ret=0), op("PUSH_BACK", 2), op("PUSH_BACK", 3, ret=2),
        op("REMOVE", 0, ret=True), op("REMOVE", 2, ret=True), op("ITEMS", ret=[2]),
        op("REVERSED_ITEMS", ret=[2]),
    ], tags=["unlink"], visible=True,
       doc="The two ends. Sentinel nodes are what make these the same code as the middle."),
    case("remove_twice_is_false", 1, [
        op("PUSH_BACK", 1, ret=0), op("REMOVE", 0, ret=True), op("REMOVE", 0, ret=False),
        op("SIZE", ret=0),
    ], tags=["handles"], visible=True,
       doc="A handle is spent once. The second removal must not unlink anything again or "
           "the size goes negative."),
    case("unknown_handle", 1, [
        op("PUSH_BACK", 1), op("REMOVE", 99, ret=False), op("SIZE", ret=1),
    ], tags=["handles"], doc="An unknown handle changes nothing."),
    case("handles_not_reused", 1, [
        op("PUSH_BACK", 1, ret=0), op("REMOVE", 0, ret=True),
        op("PUSH_BACK", 2, ret=1), op("ITEMS", ret=[2]),
    ], tags=["handles"], visible=True,
       doc="The next handle is 1, not 0. Reusing a freed handle would make the stale one "
           "valid again."),
    case("remove_everything", 1, [
        op("PUSH_BACK", 1, ret=0), op("PUSH_BACK", 2, ret=1), op("REMOVE", 0, ret=True),
        op("REMOVE", 1, ret=True), op("ITEMS", ret=[]), op("REVERSED_ITEMS", ret=[]),
        op("SIZE", ret=0), op("PUSH_FRONT", 9), op("ITEMS", ret=[9]),
    ], tags=["empty", "unlink"],
       doc="Emptied by removals, then reused. The sentinels must still point at each "
           "other correctly."),
    case("empty_list", 1, [
        op("ITEMS", ret=[]), op("REVERSED_ITEMS", ret=[]), op("SIZE", ret=0),
        op("REMOVE", 0, ret=False),
    ], tags=["empty"], doc="Nothing added yet."),
    case("duplicates_are_separate", 1, [
        op("PUSH_BACK", 7, ret=0), op("PUSH_BACK", 7, ret=1), op("REMOVE", 0, ret=True),
        op("ITEMS", ret=[7]), op("SIZE", ret=1),
    ], tags=["handles"],
       doc="Two equal values are two nodes, and the handle says which one goes -- "
           "removing by VALUE could not."),
    case("single_node_backward", 1, [
        op("PUSH_FRONT", 5), op("REVERSED_ITEMS", ret=[5]),
    ], tags=["both-ways", "empty"]),
)

PROBLEM = Problem(
    key="doubly_linked_list",
    title="Doubly linked list",
    blurb="A list with backward links, so a known node unlinks in constant time.",
    class_name="DoublyLinkedList",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("repoint", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.8 build exercise — see docs/CATALOGUE.md",
)
