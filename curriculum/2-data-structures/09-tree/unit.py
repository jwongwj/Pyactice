"""2.9 Tree — recursion that is actually shaped like the data.

Self-contained: loaded by file path, so no package-relative imports.

A tree is where recursion stops being a trick and starts being the obvious reading of the
problem: "the depth of this tree is one more than the deeper of its two subtrees" is both
the definition and the code. The drills that are NOT recursive -- level order, and the
bounds version of the BST check -- are the ones worth the most attention, because they are
where the obvious recursion gives the wrong answer.

The node type is authored ONCE here and exec'd to build the cases; the identical source is
the problem's preamble, so a node the learner builds is the same shape as one a test
passes in. See unit 2.8 for the same arrangement.

The catalogue's build exercises -- BST insert/search/delete, and serialise/deserialise --
are classes or method pairs, so they arrive as `design` problems.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

PREAMBLE = '''
class TreeNode:
    """One node of a binary tree.

    `__eq__` compares whole subtrees by value, so a test can say "the answer is the
    node holding 2, with these children" without caring about object identity. It
    reads the attributes off the other node rather than checking its type.
    """

    def __init__(self, value: int, left: "TreeNode | None" = None,
                 right: "TreeNode | None" = None) -> None:
        self.value = value
        self.left = left
        self.right = right

    def __eq__(self, other: object) -> bool:
        if other is None or not hasattr(other, "value"):
            return False
        return (self.value == other.value
                and self.left == getattr(other, "left", None)
                and self.right == getattr(other, "right", None))

    def __repr__(self) -> str:
        if self.left is None and self.right is None:
            return f"({self.value})"
        return f"({self.value} {self.left!r} {self.right!r})"
'''

_NS: dict = {}
exec(PREAMBLE, _NS)
TreeNode = _NS["TreeNode"]


def tree(values):
    """Build a tree from a level-order list, `None` for an absent child.

    The same shorthand the questions themselves use, so a case reads like the picture:
    [1, 2, 3] is a root of 1 with children 2 and 3.
    """
    if not values or values[0] is None:
        return None
    nodes = [None if v is None else TreeNode(v) for v in values]
    children = iter(nodes[1:])
    for node in nodes:
        if node is None:
            continue
        node.left = next(children, None)
        node.right = next(children, None)
    return nodes[0]


METHODS = (
    Method(
        display="IN_ORDER",
        signature="(root: TreeNode | None) -> list[int]",
        doc="Values left, node, right. For a search tree this comes out ascending.",
        constraint_note="recursion is the shortest correct answer here; take it",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="an in-order walk of a SEARCH tree is ascending as a "
                               "consequence, not as a step -- sorting the values would "
                               "also 'work' on a tree that is not a search tree, and "
                               "hide that you never walked it in order",
                       hint="in_order(left) + [value] + in_order(right)"),
        ),
    ),
    Method(
        display="PRE_ORDER",
        signature="(root: TreeNode | None) -> list[int]",
        doc="Values node, left, right. This is the order that lets you rebuild the tree.",
        constraint_note="the same shape as IN_ORDER with the node moved to the front",
        constraints=(
            ForbidCall(("sorted", "sort", "reverse", "reversed"),
                       because="the three traversals differ ONLY in where the node's own "
                               "value goes; deriving one from another by reordering is a "
                               "coincidence that does not survive an unbalanced tree",
                       hint="[value] + pre_order(left) + pre_order(right)"),
        ),
    ),
    Method(
        display="POST_ORDER",
        signature="(root: TreeNode | None) -> list[int]",
        doc="Values left, right, node. This is the order to free or fold a tree in, "
            "because children are finished before their parent.",
        constraint_note="node last; children are complete before the parent is visited",
        constraints=(
            ForbidCall(("sorted", "sort", "reverse", "reversed"),
                       because="post-order is not pre-order backwards, however much the "
                               "three-node example suggests it is",
                       hint="post_order(left) + post_order(right) + [value]"),
        ),
    ),
    Method(
        display="MAX_DEPTH",
        signature="(root: TreeNode | None) -> int",
        doc="Nodes on the longest root-to-leaf path. 0 for an empty tree, 1 for a leaf.",
        constraint_note="one line of recursion; the definition IS the code",
        constraints=(
            ForbidCall(("deque", "append"),
                       because="the recursive reading needs no queue and no accumulator: "
                               "the depth of a tree is one more than the deeper subtree",
                       hint="0 if root is None else 1 + max(depth(left), depth(right))"),
        ),
    ),
    Method(
        display="LEVEL_ORDER",
        signature="(root: TreeNode | None) -> list[list[int]]",
        doc="One list of values per level, top to bottom, left to right within a level.",
        # The one drill here that recursion does NOT do naturally: a depth-first walk
        # visits a whole subtree before the sibling, which is the wrong order entirely.
        constraint_note="breadth-first with a queue; recursion visits in the wrong order",
        constraints=(
            Forbid(("recursion",),
                   because="depth-first finishes an entire subtree before starting its "
                           "sibling, so it cannot produce a level at a time",
                   hint="a queue holding one level; drain exactly len(queue) nodes per row"),
        ),
    ),
    Method(
        display="IS_BST",
        signature="(root: TreeNode | None) -> bool",
        doc="True when every value in the left subtree is strictly less than the node, "
            "every value in the right subtree strictly greater, and both subtrees are "
            "themselves search trees. An empty tree is one.",
        constraint_note="carry a low/high bound down; comparing with children alone is wrong",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="checking only node-against-its-two-children passes trees "
                               "that are not search trees, and the fix is to pass the "
                               "allowed RANGE down rather than to look sideways",
                       hint="valid(node, low, high) -- the left child inherits `high = "
                           "node.value`, the right inherits `low = node.value`"),
        ),
    ),
    Method(
        display="DIAMETER",
        signature="(root: TreeNode | None) -> int",
        doc="Nodes on the longest path between any two nodes, which need not pass through "
            "the root. 0 for an empty tree, 1 for a single node.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Tree", theme="recursion shaped like the data, except when it is not"),)

TAG_GLOSSARY = {
    "traverse": "the three depth-first orders",
    "depth": "how far down, and the recursive definition of it",
    "level-order": "breadth-first, a row at a time",
    "bounds": "carrying an allowed range down the tree",
    "unbalanced": "trees that lean, where a coincidence on a balanced tree breaks",
    "edge-values": "empty trees, single nodes, one-sided trees",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("in_order_bst", "IN_ORDER", tree([2, 1, 3]), ret=[1, 2, 3],
       tags=["traverse"], visible=True, doc="A search tree comes out ascending."),
    _c("in_order_not_sorted", "IN_ORDER", tree([1, 2, 3]), ret=[2, 1, 3],
       tags=["traverse", "unbalanced"], visible=True,
       doc="NOT a search tree, so the in-order walk is not ascending. This is the case "
           "that separates walking from sorting."),
    _c("in_order_left_chain", "IN_ORDER", tree([3, 2, None, 1]), ret=[1, 2, 3],
       tags=["traverse", "unbalanced"]),
    _c("in_order_single", "IN_ORDER", tree([7]), ret=[7], tags=["traverse", "edge-values"]),
    _c("in_order_empty", "IN_ORDER", None, ret=[], tags=["traverse", "edge-values"]),

    _c("pre_order_basic", "PRE_ORDER", tree([1, 2, 3]), ret=[1, 2, 3],
       tags=["traverse"], visible=True, doc="Node first, then left, then right."),
    _c("pre_order_deeper", "PRE_ORDER", tree([1, 2, 3, 4, 5]), ret=[1, 2, 4, 5, 3],
       tags=["traverse", "unbalanced"], visible=True,
       doc="The whole left subtree is finished before the right one begins."),
    _c("pre_order_single", "PRE_ORDER", tree([7]), ret=[7], tags=["traverse", "edge-values"]),
    _c("pre_order_empty", "PRE_ORDER", None, ret=[], tags=["traverse", "edge-values"]),

    _c("post_order_basic", "POST_ORDER", tree([1, 2, 3]), ret=[2, 3, 1],
       tags=["traverse"], visible=True, doc="Both children before the node."),
    _c("post_order_deeper", "POST_ORDER", tree([1, 2, 3, 4, 5]), ret=[4, 5, 2, 3, 1],
       tags=["traverse", "unbalanced"], visible=True,
       doc="Reversing the pre-order of this tree gives [3, 5, 4, 2, 1], which is not "
           "this. The two orders are genuinely different walks."),
    _c("post_order_single", "POST_ORDER", tree([7]), ret=[7],
       tags=["traverse", "edge-values"]),
    _c("post_order_empty", "POST_ORDER", None, ret=[], tags=["traverse", "edge-values"]),

    _c("depth_balanced", "MAX_DEPTH", tree([1, 2, 3]), ret=2,
       tags=["depth"], visible=True, doc="Root plus one level."),
    _c("depth_lopsided", "MAX_DEPTH", tree([1, 2, None, 3]), ret=3,
       tags=["depth", "unbalanced"], visible=True,
       doc="Only the left side is deep, and the answer follows the LONGER side."),
    _c("depth_single", "MAX_DEPTH", tree([7]), ret=1,
       tags=["depth", "edge-values"], visible=True, doc="A leaf is depth 1, not 0."),
    _c("depth_empty", "MAX_DEPTH", None, ret=0, tags=["depth", "edge-values"]),

    _c("level_order_basic", "LEVEL_ORDER", tree([1, 2, 3]), ret=[[1], [2, 3]],
       tags=["level-order"], visible=True, doc="One list per level."),
    _c("level_order_ragged", "LEVEL_ORDER", tree([1, 2, 3, 4, None, None, 5]),
       ret=[[1], [2, 3], [4, 5]], tags=["level-order", "unbalanced"], visible=True,
       doc="4 and 5 are on the same level despite being under different parents. A "
           "depth-first walk would report them apart."),
    _c("level_order_chain", "LEVEL_ORDER", tree([1, 2, None, 3]), ret=[[1], [2], [3]],
       tags=["level-order", "unbalanced"]),
    _c("level_order_single", "LEVEL_ORDER", tree([7]), ret=[[7]],
       tags=["level-order", "edge-values"]),
    _c("level_order_empty", "LEVEL_ORDER", None, ret=[],
       tags=["level-order", "edge-values"], visible=True,
       doc="No levels at all -- not [[]]."),

    _c("is_bst_true", "IS_BST", tree([2, 1, 3]), ret=True,
       tags=["bounds"], visible=True, doc="A proper search tree."),
    _c("is_bst_local_only", "IS_BST", tree([5, 1, 6, None, None, 4, 7]), ret=False,
       tags=["bounds", "unbalanced"], visible=True,
       doc="Every node is correctly placed relative to its OWN children, and the tree is "
           "still not a search tree: the 4 is in the right subtree of 5. This is the case "
           "a children-only check gets wrong."),
    _c("is_bst_equal_left", "IS_BST", tree([2, 2]), ret=False,
       tags=["bounds", "edge-values"], visible=True,
       doc="Strictly less, so an equal value on the left is not allowed."),
    _c("is_bst_equal_right", "IS_BST", tree([2, None, 2]), ret=False,
       tags=["bounds", "edge-values"]),
    _c("is_bst_single", "IS_BST", tree([7]), ret=True, tags=["bounds", "edge-values"]),
    _c("is_bst_empty", "IS_BST", None, ret=True, tags=["bounds", "edge-values"]),
    _c("is_bst_deep_left", "IS_BST", tree([3, 1, 4, None, 2]), ret=True,
       tags=["bounds", "unbalanced"],
       why="2 sits under 1 on the right, which is legal because the bound from 3 allows it"),

    _c("diameter_through_root", "DIAMETER", tree([1, 2, 3]), ret=3,
       tags=["checkpoint"], visible=True, doc="2 -> 1 -> 3 is three nodes."),
    _c("diameter_avoids_root", "DIAMETER", tree([1, 2, None, 3, 4, 5, None, 6]), ret=5,
       tags=["checkpoint", "unbalanced"], visible=True,
       doc="The longest path lies entirely inside the left subtree and never touches the "
           "root, which is why the answer is not simply the two depths added."),
    _c("diameter_chain", "DIAMETER", tree([1, 2, None, 3]), ret=3,
       tags=["checkpoint", "unbalanced"], visible=True,
       doc="A leaning tree: the longest path is the chain itself."),
    _c("diameter_single", "DIAMETER", tree([7]), ret=1,
       tags=["checkpoint", "edge-values"]),
    _c("diameter_empty", "DIAMETER", None, ret=0, tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="trees",
    title="2.9 Tree",
    blurb="The three traversals, depth, level order, the BST check and the diameter.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("traverse", "level-order", "bounds"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    preamble=PREAMBLE,
    source="Curriculum unit 2.9 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
