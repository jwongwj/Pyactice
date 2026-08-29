# Explanation

## The shape of the answer

```python
class CircularBuffer:
    def __init__(self):
        self.resize(0)

    def resize(self, capacity):
        self.capacity = max(0, capacity)
        self.slots = [None] * self.capacity
        self.head = 0
        self.count = 0

    def write(self, value):
        if self.capacity == 0:
            return False
        overwriting = self.count == self.capacity
        self.slots[(self.head + self.count) % self.capacity] = value
        if overwriting:
            self.head = (self.head + 1) % self.capacity     # the oldest goes
        else:
            self.count += 1
        return not overwriting

    def read(self):
        if self.count == 0:
            return None
        value = self.slots[self.head]
        self.head = (self.head + 1) % self.capacity
        self.count -= 1
        return value

    def items(self):
        return [self.slots[(self.head + i) % self.capacity] for i in range(self.count)]

    def is_full(self):
        return self.count == self.capacity

    def size(self):
        return self.count
```

## The one subtle line

```python
self.slots[(self.head + self.count) % self.capacity] = value
```

When the buffer is full, `head + count` is `head + capacity`, which modulo capacity is
`head` — the oldest slot. So the same expression writes to the next free slot when there is
one and to the oldest slot when there is not. No branch needed for *where* to write; the
branch is only for what happens to `head` and `count` afterwards.

## Why `is_full` is true at capacity 0

`count == capacity` is `0 == 0`. That falls out rather than being special-cased, and it is
the honest answer: there is no room, which is what full means. Writing a separate
`capacity == 0` branch for `is_full` is extra code that says the same thing.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `empty_and_full_are_different` | resolving the head==tail ambiguity at all |
| `overwrite_then_read_order` | overwriting without advancing `head` |
| `wraps_around` | a write index that does not wrap |
| `capacity_one` | the smallest buffer, where every write overwrites |
| `zero_capacity` / `before_any_resize` | a modulo by zero |
| `resize_discards` | resize keeping the old contents |
| `read_write_interleaved` | a count that does not fall on read |

## Complexity

Every operation is O(1) except `items`, which is O(count) because it builds a list. Space
is exactly `capacity` slots, allocated once, which is the whole point.

## Where this is used

Ring buffers are how audio, networking and logging hold recent data with a hard memory
bound: fixed cost, oldest data lost first, no allocation in the hot path.

`collections.deque(maxlen=n)` is Python's version and is what you should actually use
(unit 2.6). It discards from the opposite end automatically — the same policy, already
written.
