# Explanation

## The shape of the answer

```python
class _Node:
    __slots__ = ("value", "left", "right")
    def __init__(self, value):
        self.value, self.left, self.right = value, None, None


class BST:
    def __init__(self):
        self.root = None

    def insert(self, value):
        if self.root is None:
            self.root = _Node(value)
            return True
        node = self.root
        while True:
            if value == node.value:
                return False                       # no duplicates
            side = "left" if value < node.value else "right"
            child = getattr(node, side)
            if child is None:
                setattr(node, side, _Node(value))
                return True
            node = child

    def contains(self, value):
        node = self.root
        while node is not None:
            if value == node.value:
                return True
            node = node.left if value < node.value else node.right
        return False

    def delete(self, value):
        if not self.contains(value):
            return False
        self.root = self._delete_from(self.root, value)
        return True

    def _delete_from(self, node, value):
        if node is None:
            return None
        if value < node.value:
            node.left = self._delete_from(node.left, value)
        elif value > node.value:
            node.right = self._delete_from(node.right, value)
        else:
            if node.left is None:
                return node.right                  # 0 or 1 child
            if node.right is None:
                return node.left
            successor = node.right                 # smallest on the right
            while successor.left is not None:
                successor = successor.left
            node.value = successor.value
            node.right = self._delete_from(node.right, successor.value)
        return node

    def in_order(self):
        out, stack, node = [], [], self.root
        while stack or node is not None:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            out.append(node.value)
            node = node.right
        return out

    def height(self):
        best, stack = 0, [(self.root, 1)]
        while stack:
            node, depth = stack.pop()
            if node is None:
                continue
            best = max(best, depth)
            stack.append((node.left, depth + 1))
            stack.append((node.right, depth + 1))
        return best

    def min_value(self):
        node = self.root
        if node is None:
            return None
        while node.left is not None:
            node = node.left
        return node.value
```

## `return node.right` covers two cases at once

When there is no left child, returning the right one is correct whether the right child
exists or not — if it does not, it returns `None`, which is exactly "this node is gone".
The zero-child and one-child cases need no separate code.

## Why the successor always has at most one child

It is the **leftmost** node of the right subtree, so by definition it has no left child. So
deleting it recursively can only hit the easy cases, and the recursion is one level deep
rather than unbounded. That is why this reduction works and is not circular.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `delete_node_with_one_child` | dropping the child along with the node |
| `delete_node_with_two_children` | promoting the wrong subtree, or losing one |
| `delete_the_root` | no parent link to repoint |
| `delete_two_children_deep` | a successor that has a right subtree of its own |
| `delete_everything` | a root reference not cleared |
| `duplicates_rejected` | storing a second copy, which breaks `in_order` |
| `height_of_a_chain` | nothing — it documents the degenerate shape |
| `negatives_and_zero` | `if not node.value` as a null check |

## Complexity

| operation | balanced | degenerate |
| --- | --- | --- |
| insert / contains / delete / min | O(log n) | **O(n)** |
| in_order | O(n) | O(n) |

The degenerate column is the honest one. A plain BST built from sorted input is a linked
list, and `height_of_a_chain` demonstrates it. Self-balancing trees — AVL, red-black — add
rotations on insert and delete to keep the height logarithmic. Naming them and saying what
they fix is usually enough; implementing one is a much larger exercise.

Python has no built-in tree. `bisect` over a sorted list gives O(log n) search with O(n)
insertion, and `sortedcontainers` (third party) is what people actually reach for.
