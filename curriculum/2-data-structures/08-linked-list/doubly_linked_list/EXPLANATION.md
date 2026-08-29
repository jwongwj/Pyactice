# Explanation

## The shape of the answer

```python
class _Node:
    __slots__ = ("value", "prev", "next")
    def __init__(self, value=None):
        self.value, self.prev, self.next = value, None, None


class DoublyLinkedList:
    def __init__(self):
        self.head = _Node()          # sentinels: no value, never removed
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.nodes = {}
        self.next_handle = 0
        self.count = 0

    def _insert_between(self, value, before, after):
        node = _Node(value)
        node.prev, node.next = before, after
        before.next = after.prev = node
        handle = self.next_handle
        self.next_handle += 1
        self.nodes[handle] = node
        self.count += 1
        return handle

    def push_front(self, value):
        return self._insert_between(value, self.head, self.head.next)

    def push_back(self, value):
        return self._insert_between(value, self.tail.prev, self.tail)

    def remove(self, handle):
        node = self.nodes.pop(handle, None)
        if node is None:
            return False
        node.prev.next = node.next
        node.next.prev = node.prev
        self.count -= 1
        return True

    def items(self):
        out, node = [], self.head.next
        while node is not self.tail:
            out.append(node.value)
            node = node.next
        return out

    def reversed_items(self):
        out, node = [], self.tail.prev
        while node is not self.head:
            out.append(node.value)
            node = node.prev
        return out

    def size(self):
        return self.count
```

## `before.next = after.prev = node`

One line doing both halves of the splice. It is worth writing it that way because the two
assignments must never be separated by anything — a partial splice leaves the list
traversable in one direction and broken in the other, which `items` will not notice and
`reversed_items` will.

That is exactly why `reversed_items` is in the interface. It is not a feature anyone
wants; it is the assertion that both chains agree.

## `self.nodes.pop(handle, None)`

One call does three things: looks the node up, removes the entry so the handle is spent,
and returns None for an unknown handle. Checking membership and then deleting is two lookups
and one more chance to forget the delete.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `backward_chain_agrees` | a `prev` link not set on insertion |
| `remove_middle` | not repairing both chains |
| `remove_front_and_back` | special-casing the ends, or forgetting to |
| `remove_twice_is_false` | a handle not being spent — size goes negative |
| `handles_not_reused` | recycling freed handles, reviving stale ones |
| `remove_everything` | sentinels left pointing at removed nodes |
| `duplicates_are_separate` | removing by value instead of by handle |

## Complexity

| operation | cost |
| --- | --- |
| push_front / push_back / remove / size | O(1) |
| items / reversed_items | O(n) |

The O(1) removal is the whole point, and it is only O(1) *because* you already hold the
node. Removing by value is still O(n) — you have to find it first.

## Where this is used

- **LRU cache** — a dict from key to node plus this list. The dict finds the node in O(1);
  this unlinks and re-inserts it in O(1). Neither structure can do it alone, which is the
  problem beside this one.
- `collections.OrderedDict` and modern `dict` use the same arrangement internally, which is
  why `move_to_end` is O(1).
