# Approach

## Insert and search are the easy half

The property does all the work: everything smaller is left, everything larger is right. So
both operations are the same walk, and the only difference is what happens at the bottom.

```python
while node is not None:
    if value == node.value: ...
    node = node.left if value < node.value else node.right
```

Write these iteratively. A degenerate tree — which ascending input produces — is as deep as
it is large, and a recursive walk will overflow on it. That is the same argument as unit
2.8's, and this problem contains a case that builds exactly such a chain.

## Delete has three cases, and only one is interesting

**No children.** Unlink it. Done.

**One child.** The child takes its place. Nothing else moves, because everything in that
subtree is already on the correct side of the deleted node's parent.

**Two children.** This is the exercise. The node cannot simply be removed: there is one
link in its parent and two subtrees to attach. Neither child can move up, because the other
subtree would have nowhere to go.

The answer: replace the node's **value** with its **in-order successor** — the smallest
value in its right subtree — and then delete that successor from the right subtree. The
successor is the next value in sorted order, so putting it here keeps every ordering
constraint satisfied. And it has at most one child (it is the leftmost of its subtree, so
it has no left child), which reduces the hard case to one of the easy ones.

The in-order **predecessor** — the largest in the left subtree — works identically. Either
is correct; say which you chose.

## The root has no parent

Every delete repoints a parent's link, except when the node being deleted *is* the root.
Then it is the tree's own root reference that changes.

Two ways to handle it: carry the parent along and special-case `None`, or write delete as a
function that returns the new subtree root and assign it back:

```python
self.root = self._delete_from(self.root, value)
```

The second is shorter and has no special case, which is why it is the usual answer even
when the rest of the code is iterative.

## Order of work

1. `insert` and `contains`, iteratively.
2. `in_order`, which is how you will check everything else.
3. `min_value` and `height`.
4. `delete` for a leaf, then for one child, then for two.
5. Then the root case, and the emptied-then-reused case.
