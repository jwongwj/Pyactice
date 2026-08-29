# Approach

## Why the shape is the problem

A tree is not its values. `[1,2,3]` in-order could be a balanced tree, a left chain or a
right chain — three different trees, one traversal. So an encoding that records only the
values it visits cannot be decoded.

Two encodings do work:

- **Pre-order with explicit markers for absent children.** The root arrives before anything
  that depends on it, so the rebuild is one forward pass. This is the one to write.
- **Two traversals** — in-order plus pre-order — which pin the tree uniquely between them,
  but need distinct values and a split-and-recurse rebuild. More work, more assumptions.

## Encoding

```python
def walk(node):
    if node is None:
        parts.append("#")
        return
    parts.append(str(node.value))
    walk(node.left)
    walk(node.right)
```

The marker is what makes it unambiguous. Every node contributes exactly three things — its
value and its two children's encodings — so the string is self-delimiting: reading it left
to right, you always know how much is still owed.

## Decoding

The same walk, consuming instead of producing:

```python
def build():
    token = next(tokens)          # raises when the text runs out
    if token == "#":
        return None
    node = _Node(int(token))
    node.left = build()
    node.right = build()
    return node
```

The recursion mirrors the encoding exactly, which is the whole appeal of pre-order.

## Rejecting bad input properly

Three separate failures, and each needs its own check:

1. **Runs out early** — the token stream is exhausted mid-tree. Catch it.
2. **Text left over** — the tree completed and tokens remain. Check after the walk, not
   during it. This is the one people forget.
3. **A bad token** — not `#` and not an integer. `int()` raising is the check.

And on any failure, **leave the tree empty** rather than half built. Build into a local and
only assign it to `self.root` once the whole parse has succeeded.

## The empty string

`""` is not the encoding of the empty tree — `"#"` is. Splitting `""` on commas gives
`[""]`, one token that is neither a number nor a marker, so the ordinary bad-token path
rejects it without a special case. Worth checking that it does.

## Order of work

1. `build` from the level-order list, and `size`.
2. `pre_order` and `in_order`, so you can see what you have.
3. `encode`.
4. `decode` for valid input.
5. Then the three rejection cases, and the leave-it-empty rule.
