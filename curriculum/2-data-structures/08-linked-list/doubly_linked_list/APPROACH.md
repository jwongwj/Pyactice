# Approach

## What the second link buys

In a singly linked list, removing a node means finding its **predecessor** — which means
walking from the head, which is O(n). With a `prev` link, the predecessor is already there:

```python
node.prev.next = node.next
node.next.prev = node.prev
```

Two assignments, no search. That is the entire reason the structure exists, and it is what
the LRU cache beside this problem is built on.

## Sentinels remove every special case

Without them, removing the first node means updating `self.head`; removing the last means
updating `self.tail`; and removing the only node means both. Three branches, each easy to
get wrong.

With two nodes that hold no value — a permanent head and a permanent tail — every real node
has both a `prev` and a `next`, always:

```python
self.head.next = self.tail
self.tail.prev = self.head
```

Now the two-line unlink above is correct for every node, including the first and last.
Insertion is likewise uniform: splice between two known nodes.

Worth the two extra objects. It is the single biggest simplification available in this
problem.

## Handles

The tests need a way to name a node without holding a reference to it, and the handle is
that. A dict from handle to node is enough:

```python
self.nodes = {}
self.next_handle = 0
```

Two rules that the cases check:

- **Delete the entry on removal**, so a spent handle reports False rather than unlinking
  something a second time — which would corrupt the neighbours and drive `size` negative.
- **Never reuse a handle.** A counter that only goes up guarantees a stale handle stays
  stale. Reusing freed numbers makes old handles silently valid again.

## Order of work

1. The node type, the two sentinels, and `size`.
2. A private splice helper, then `push_front` and `push_back` on top of it.
3. `items` — walk forward from `head.next` until you reach the tail sentinel.
4. `reversed_items` — the same walk backwards. This is what catches a dangling `prev`.
5. `remove`, with the handle bookkeeping.
