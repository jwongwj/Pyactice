"""BST insert / search / delete — the build exercise for unit 2.9.

Insert and search are five lines each. Delete is the exercise: a node with two children
cannot simply be unlinked, because its subtrees have to go somewhere and only one link is
available. The answer -- promote its in-order successor -- is the thing worth having
derived once.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="INSERT", signature="(self, value: int) -> bool", level=1,
           doc="Add a value. True when it was added, False when it was already present -- "
               "duplicates are not stored."),
    Method(display="CONTAINS", signature="(self, value: int) -> bool", level=1,
           doc="Is the value in the tree?"),
    Method(display="DELETE", signature="(self, value: int) -> bool", level=1,
           doc="Remove a value. True when it was there."),
    Method(display="IN_ORDER", signature="(self) -> list[int]", level=1,
           doc="Every value, ascending -- which for a search tree is an in-order walk."),
    Method(display="HEIGHT", signature="(self) -> int", level=1,
           doc="Nodes on the longest root-to-leaf path. 0 for an empty tree."),
    Method(display="MIN_VALUE", signature="(self) -> int | None", level=1,
           doc="The smallest value, or None when empty. Found by going left, not by "
               "scanning."),
)

LEVELS = (Level(1, "BST", theme="deleting a node with two children"),)

TAG_GLOSSARY = {
    "insert": "placing a value, and rejecting duplicates",
    "search": "the property that makes lookup logarithmic",
    "delete-leaf": "removing a node with no children",
    "delete-one": "removing a node with a single child",
    "delete-two": "removing a node with both, which is the hard one",
    "shape": "the height, and what the insertion order does to it",
    "empty": "an empty tree, and one emptied by deletions",
}

CASES = (
    case("insert_and_contains", 1, [
        op("INSERT", 5, ret=True), op("INSERT", 3, ret=True), op("INSERT", 7, ret=True),
        op("CONTAINS", 3, ret=True), op("CONTAINS", 4, ret=False),
        op("IN_ORDER", ret=[3, 5, 7]),
    ], tags=["insert", "search"], visible=True,
       doc="In-order gives them ascending, which is the search-tree property."),
    case("duplicates_rejected", 1, [
        op("INSERT", 5, ret=True), op("INSERT", 5, ret=False), op("IN_ORDER", ret=[5]),
    ], tags=["insert"], doc="Stored once, and the second insert says so."),
    case("delete_leaf", 1, [
        op("INSERT", 5), op("INSERT", 3), op("INSERT", 7), op("DELETE", 3, ret=True),
        op("IN_ORDER", ret=[5, 7]), op("CONTAINS", 3, ret=False),
    ], tags=["delete-leaf"], doc="A leaf just goes."),
    case("delete_node_with_one_child", 1, [
        op("INSERT", 5), op("INSERT", 3), op("INSERT", 1), op("DELETE", 3, ret=True),
        op("IN_ORDER", ret=[1, 5]), op("CONTAINS", 1, ret=True),
    ], tags=["delete-one"], visible=True,
       doc="The single child takes the deleted node's place. Losing it here is the "
           "commonest delete bug."),
    case("delete_node_with_two_children", 1, [
        op("INSERT", 5), op("INSERT", 3), op("INSERT", 8), op("INSERT", 7),
        op("INSERT", 9), op("DELETE", 8, ret=True), op("IN_ORDER", ret=[3, 5, 7, 9]),
        op("CONTAINS", 7, ret=True), op("CONTAINS", 9, ret=True),
    ], tags=["delete-two"], visible=True,
       doc="8 has both children. Neither can simply move up -- there is one link and two "
           "subtrees -- so its in-order successor (9) takes its place."),
    case("delete_the_root", 1, [
        op("INSERT", 5), op("INSERT", 3), op("INSERT", 7), op("DELETE", 5, ret=True),
        op("IN_ORDER", ret=[3, 7]), op("CONTAINS", 5, ret=False), op("HEIGHT", ret=2),
    ], tags=["delete-two"], visible=True,
       doc="The root with two children. There is no parent to repoint, so the tree's own "
           "root reference has to change."),
    case("delete_absent", 1, [
        op("INSERT", 5), op("DELETE", 9, ret=False), op("IN_ORDER", ret=[5]),
    ], tags=["delete-leaf"], doc="Nothing to remove."),
    case("delete_everything", 1, [
        op("INSERT", 5), op("INSERT", 3), op("DELETE", 5, ret=True),
        op("DELETE", 3, ret=True), op("IN_ORDER", ret=[]), op("HEIGHT", ret=0),
        op("MIN_VALUE", ret=None), op("INSERT", 9, ret=True), op("IN_ORDER", ret=[9]),
    ], tags=["empty"], visible=True,
       doc="Emptied by deletions and then reused. The root reference must be back to None."),
    case("height_of_a_chain", 1, [
        op("INSERT", 1), op("INSERT", 2), op("INSERT", 3), op("HEIGHT", ret=3),
        op("IN_ORDER", ret=[1, 2, 3]),
    ], tags=["shape"], visible=True,
       doc="Ascending insertion degenerates into a chain -- a linked list with extra "
           "pointers, and O(n) lookups. This is what balancing exists to prevent."),
    case("height_when_balanced", 1, [
        op("INSERT", 2), op("INSERT", 1), op("INSERT", 3), op("HEIGHT", ret=2),
    ], tags=["shape"], doc="The same three values, inserted middle-first."),
    case("min_goes_left", 1, [
        op("INSERT", 5), op("INSERT", 3), op("INSERT", 1), op("INSERT", 9),
        op("MIN_VALUE", ret=1),
    ], tags=["search"], doc="Leftmost, without looking at the right subtree at all."),
    case("empty_tree", 1, [
        op("CONTAINS", 1, ret=False), op("DELETE", 1, ret=False), op("IN_ORDER", ret=[]),
        op("HEIGHT", ret=0), op("MIN_VALUE", ret=None),
    ], tags=["empty"], doc="Nothing there."),
    case("negatives_and_zero", 1, [
        op("INSERT", 0, ret=True), op("INSERT", -5, ret=True), op("MIN_VALUE", ret=-5),
        op("CONTAINS", 0, ret=True), op("IN_ORDER", ret=[-5, 0]),
    ], tags=["insert", "search"],
       doc="0 is a value; falsiness is not the test for 'no node here'."),
    case("delete_two_children_deep", 1, [
        op("INSERT", 10), op("INSERT", 5), op("INSERT", 15), op("INSERT", 12),
        op("INSERT", 20), op("INSERT", 11), op("DELETE", 15, ret=True),
        op("IN_ORDER", ret=[5, 10, 11, 12, 20]), op("CONTAINS", 11, ret=True),
    ], tags=["delete-two"],
       doc="The successor of 15 is 20, and 20 has no left child. Promoting a successor "
           "that itself has a right subtree is the case to be careful with."),
)

PROBLEM = Problem(
    key="bst",
    title="Binary search tree",
    blurb="Insert, search and the delete that has three separate cases.",
    class_name="BST",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="hard",
    topics=("traverse", "bounds", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.9 build exercise — see docs/CATALOGUE.md",
)
