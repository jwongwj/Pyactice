# Explanation

## The shape of the answer

```python
class _Node:
    __slots__ = ("value", "left", "right")
    def __init__(self, value):
        self.value, self.left, self.right = value, None, None


class TreeCodec:
    def __init__(self):
        self.root = None

    def build(self, values):
        if not values or values[0] is None:
            self.root = None
            return
        nodes = [None if v is None else _Node(v) for v in values]
        children = iter(nodes[1:])
        for node in nodes:
            if node is not None:
                node.left = next(children, None)
                node.right = next(children, None)
        self.root = nodes[0]

    def encode(self):
        parts = []

        def walk(node):
            if node is None:
                parts.append("#")
                return
            parts.append(str(node.value))
            walk(node.left)
            walk(node.right)

        walk(self.root)
        return ",".join(parts)

    def decode(self, text):
        tokens = text.split(",")
        position = 0

        def build():
            nonlocal position
            if position >= len(tokens):
                raise ValueError("ran out mid-tree")
            token = tokens[position]
            position += 1
            if token == "#":
                return None
            node = _Node(int(token))             # ValueError if it is rubbish
            node.left = build()
            node.right = build()
            return node

        try:
            root = build()
        except ValueError:
            self.root = None                     # ran out, or a bad token
            return False
        if position != len(tokens):
            self.root = None                     # tokens left over
            return False
        self.root = root
        return True

    def pre_order(self):
        out = []

        def walk(node):
            if node is not None:
                out.append(node.value)
                walk(node.left)
                walk(node.right)

        walk(self.root)
        return out

    def in_order(self):
        out = []

        def walk(node):
            if node is not None:
                walk(node.left)
                out.append(node.value)
                walk(node.right)

        walk(self.root)
        return out

    def size(self):
        return len(self.pre_order())
```

## An index, not an iterator

The first version of this used `iter()` and let `StopIteration` signal the end. It was
wrong, and Gate 1 caught it: `StopIteration` raised **inside** `build` (the text ran out
mid-tree) is indistinguishable from one raised **after** it (the text ended cleanly), so
truncated input was accepted as valid.

An explicit position fixes it. Running out mid-tree raises `ValueError` — the same
rejection path as a bad token — and "was there anything left over" becomes a plain
comparison after the walk:

```python
if position != len(tokens):
    return False
```

Two failure modes, two checks, neither borrowing the other's exception. The lesson
generalises: an exception used as control flow is only safe when exactly one thing can
raise it.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `shape_survives_a_right_chain` | an encoding that records values but not shape |
| `encode_simple` | omitting the markers under leaves |
| `decode_rejects_truncated` | treating a short string as valid |
| `decode_rejects_trailing` | not checking for leftover tokens |
| `decode_rejects_empty_text` | special-casing `""` as the empty tree |
| `negatives_and_zero` | `isdigit()` as the number test, which rejects `-2` |
| `build_replaces` | building alongside instead of replacing |

`shape_survives_a_right_chain` is the one that justifies the whole design: its in-order walk
is `[1,2,3]`, identical to a balanced tree's, and only the pre-order encoding tells them
apart.

## Complexity

Encode and decode are both O(n) in time and O(n) in output size. The recursion is as deep as
the tree is tall — fine for a balanced tree, and a genuine stack risk for a degenerate one,
which is the same caveat as unit 2.9's.

## Where this is used

Every time a structure crosses a boundary: written to disk, sent over a network, cached.
JSON, pickle and protocol buffers all solve this problem, and all of them face the same
question — how much structure does the format have to record for the reader to rebuild what
the writer had.
