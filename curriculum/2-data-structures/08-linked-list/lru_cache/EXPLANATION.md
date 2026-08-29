# Explanation

## The shape of the answer

```python
class _Node:
    __slots__ = ("key", "value", "prev", "next")
    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = self.next = None


class LRUCache:
    def __init__(self):
        self.set_capacity(0)

    def set_capacity(self, capacity):
        self.capacity = max(0, capacity)
        self.index = {}
        self.head = _Node()                  # sentinels
        self.tail = _Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = self.head.next = node

    def get(self, key):
        node = self.index.get(key)
        if node is None:
            return None                      # a miss changes nothing
        self._unlink(node)
        self._push_front(node)
        return node.value

    def put(self, key, value):
        node = self.index.get(key)
        if node is not None:                 # overwrite: cannot evict
            node.value = value
            self._unlink(node)
            self._push_front(node)
            return None
        node = _Node(key, value)
        self.index[key] = node
        self._push_front(node)
        if len(self.index) > self.capacity:
            oldest = self.tail.prev
            self._unlink(oldest)
            del self.index[oldest.key]       # BOTH structures
            return oldest.key
        return None

    def keys(self):
        out, node = [], self.head.next
        while node is not self.tail:
            out.append(node.key)
            node = node.next
        return out

    def size(self):
        return len(self.index)
```

## The node carries its key

`_Node` stores `key` as well as `value`, and that is not redundant. On eviction you have
the node at the back of the list and need to delete its dict entry — which means you need
its key. Without it you would have to search the dict by value, which is O(n) and defeats
the whole design.

That small detail is the one people leave out, and it is the reason eviction is O(1).

## Why the zero-capacity case works with no special code

`put` inserts first and then checks `len(self.index) > self.capacity`. With capacity 0 that
is `1 > 0`, so the node just inserted is at the back as well as the front, and it is the
one evicted. The method returns the key it was handed. No branch needed.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `get_saves_a_key_from_eviction` | a `get` that does not reorder |
| `miss_does_not_reorder` | a miss that promotes anyway |
| `overwrite_does_not_evict` | treating an overwrite as an insertion |
| `zero_capacity` | dividing the capacity check into special cases |
| `value_zero_is_a_value` | `if not node` or `if not value` as the miss test |
| `repeated_get_same_key` | unlink-then-insert corrupting the front node |
| `long_sequence` | any of the above, compounding |
| `evicts_least_recent` | the eviction happening at the wrong end |

`get_saves_a_key_from_eviction` is the one to run by hand. It is five operations and it
fails for any implementation where `get` is a plain dict lookup.

## Complexity

| operation | cost |
| --- | --- |
| get / put / size | O(1) |
| keys | O(n) — it builds the list |

Space is O(capacity): one node and one dict entry per entry held.

## What you would actually use

```python
from collections import OrderedDict
# get:  self.data.move_to_end(key); return self.data[key]
# put:  ... ; if len(self.data) > cap: self.data.popitem(last=False)
```

`OrderedDict` is a dict with exactly this doubly linked list inside it, which is why
`move_to_end` is O(1). And `functools.lru_cache` is the decorator form for memoising a
function. Both are the right answer in real code; this exercise is asking what they are made
of.
