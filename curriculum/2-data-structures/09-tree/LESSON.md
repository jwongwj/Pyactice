# 2.9 Tree

A tree is where recursion stops being a trick and becomes the obvious reading. "The depth
of a tree is one more than the deeper of its subtrees" is simultaneously the definition and
the code:

```python
def max_depth(root):
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

Every recursive tree function has that shape: **the base case is `None`**, and the
recursive case combines the answers from the two subtrees. If you find yourself managing
state across the whole tree, you are probably fighting it.

## The three traversals

They differ in exactly one thing — where the node's own value goes:

```python
in_order(left)  + [value] + in_order(right)      # left, node, right
[value] + pre_order(left)  + pre_order(right)    # node, left, right
post_order(left) + post_order(right) + [value]   # left, right, node
```

What each is for:

- **In-order** on a *binary search tree* comes out ascending. That is a consequence of the
  BST property, not of the walk — in-order on any other tree is just an order.
- **Pre-order** is the one that lets you rebuild the tree, because the root arrives before
  anything that depends on it. It is what serialisation uses.
- **Post-order** finishes both children before the parent, which is what you want whenever
  a node's answer depends on its subtrees' answers — freeing, summing, or computing depth.

On a three-node tree, post-order looks like reversed pre-order. It is not: on
`[1,2,3,4,5]`, pre-order is `[1,2,4,5,3]` and post-order is `[4,5,2,3,1]`, while reversing
the pre-order gives `[3,5,4,2,1]`. The coincidence dies as soon as the tree is bigger than
the example you checked it on.

## Level order is the exception

Every drill above is naturally recursive. Level order is not, and this is the most useful
thing in the unit: a depth-first walk finishes an entire subtree before touching its
sibling, so it *cannot* produce a level at a time. You need a queue.

```python
rows = []
queue = deque([root])
while queue:
    row = []
    for _ in range(len(queue)):     # exactly the nodes on THIS level
        node = queue.popleft()
        row.append(node.value)
        if node.left:  queue.append(node.left)
        if node.right: queue.append(node.right)
    rows.append(row)
```

The `for _ in range(len(queue))` is the whole trick. Taking the length **before** the loop
fixes how many nodes belong to the current level; anything appended inside belongs to the
next one. Without it you get every value in one flat list.

Two nodes on the same level under *different parents* are what a depth-first walk reports
apart, and a level-order walk reports together. That is the case worth testing.

## Validating a BST: look down, not sideways

The tempting check is "each node is bigger than its left child and smaller than its
right". It is wrong, and it fails on a tree that looks fine locally:

```
      5
     / \
    1   6
       / \
      4   7      <- 4 is in the RIGHT subtree of 5, and 4 < 5
```

Every node satisfies the local check. The tree is not a search tree. The rule is about the
whole subtree, not the immediate children, so carry the allowed **range** down:

```python
def valid(node, low, high):
    if node is None:
        return True
    if low is not None and node.value <= low:
        return False
    if high is not None and node.value >= high:
        return False
    return valid(node.left, low, node.value) and valid(node.right, node.value, high)
```

Going left tightens the *upper* bound to the current value; going right tightens the
*lower* one. The root starts unbounded in both directions.

Decide early whether equal values are allowed — `<=` versus `<` — because the question
usually specifies it and the two readings disagree on a tree with duplicates.

An in-order walk that checks the result is ascending is also correct, and is a good answer
to give: it makes the "in-order of a BST is sorted" property do the work.

## Returning two things at once

The diameter — the longest path between any two nodes — is the pattern worth taking away.
The path need not pass through the root, so you cannot answer it by looking at the root
alone. But a single post-order walk can compute the depth *and* watch for the best path
seen anywhere:

```python
best = 0

def depth(node):
    nonlocal best
    if node is None:
        return 0
    left, right = depth(node.left), depth(node.right)
    best = max(best, left + right + 1)      # longest path THROUGH this node
    return 1 + max(left, right)             # what the parent needs
```

Note the two different quantities: what you *return* is what the parent needs (a depth),
and what you *record* is the answer you are actually after. Conflating them is the usual
bug. Returning a tuple `(depth, best)` instead of using `nonlocal` is equally good and
sometimes clearer.

This shape — one walk, returning one thing upward while accumulating another — solves a
surprising number of tree questions: maximum path sum, the largest BST subtree, counting
balanced subtrees.

## A note on recursion depth

Python's recursion limit is around 1000 frames. A *balanced* tree of a million nodes is
only 20 deep, so recursion is safe. A **degenerate** tree — one that is really a linked
list — is as deep as it is large, and will overflow. If the input might lean, use an
explicit stack.

## Where to reach for which

| the question says | you want |
| --- | --- |
| sorted output from a BST | in-order |
| serialise / rebuild | pre-order |
| the answer depends on subtree answers | post-order |
| level by level, or "the nth row" | BFS with a queue |
| shortest path to a leaf | BFS — it stops at the first one |
| is this a valid BST | bounds carried down |
| longest path anywhere | one walk, return depth, record best |
