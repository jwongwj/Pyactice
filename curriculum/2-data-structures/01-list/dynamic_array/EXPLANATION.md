# Explanation

## The shape of the answer

```python
class DynamicArray:
    def __init__(self):
        self.slots = []
        self.used = 0

    def _grow(self):
        bigger = [None] * max(1, len(self.slots) * 2)
        for index in range(self.used):
            bigger[index] = self.slots[index]
        self.slots = bigger

    def append(self, value):
        if self.used == len(self.slots):
            self._grow()
        self.slots[self.used] = value
        self.used += 1

    def _in_range(self, index):
        return 0 <= index < self.used

    def get(self, index):
        return self.slots[index] if self._in_range(index) else None

    def set(self, index, value):
        if not self._in_range(index):
            return False
        self.slots[index] = value
        return True

    def pop(self):
        if self.used == 0:
            return None
        self.used -= 1
        return self.slots[self.used]       # left in place; the slot is simply unused now

    def size(self):
        return self.used

    def capacity(self):
        return len(self.slots)

    def items(self):
        return [self.slots[i] for i in range(self.used)]
```

## `max(1, len(self.slots) * 2)`

The single most important expression here. Without the `max`, the first append finds
capacity 0, doubles it to 0, and then writes to `slots[0]` of an empty list.

## pop leaves the value behind

`self.used -= 1` is the entire removal. The value is still physically in the slot, and that
is fine — it is unreachable through every method, because every one of them is written
against `used`. The next append overwrites it.

Whether to also clear the slot is a real question in a language with garbage collection: a
stale reference keeps an object alive. Setting `self.slots[self.used] = None` after the read
costs nothing and avoids that. Worth mentioning; not required here.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `capacity_doubles` | growing by a step, or growing when not full |
| `growth_from_one` | doubling 0 and getting 0 |
| `size_and_capacity_differ` | `items` reporting the whole block |
| `out_of_range` | bounds checked against capacity instead of size |
| `negative_index` | Python's negative indexing leaking through |
| `pop_does_not_shrink` | releasing the block eagerly |
| `refill_after_emptying` | reallocating when the existing block would do |
| `value_zero` | falsiness standing in for "no value there" |

`capacity_doubles` is the case that makes the exercise testable at all. Without observing
the capacity, a correct answer and a thin wrapper around `list.append` are
indistinguishable.

## Complexity

| operation | worst case | amortised |
| --- | --- | --- |
| append | O(n) | **O(1)** |
| get / set / pop / size / capacity | O(1) | O(1) |
| items | O(n) | O(n) |

## What CPython actually does

It over-allocates by a growth pattern closer to 1.125× plus a constant, rather than
doubling — gentler on memory, same asymptotics. `list` also stores a pointer array, which is
why `list[i]` is one multiply and an offset regardless of what the elements are (unit 2.1).

Doubling is the version to write and to reason about; the constant does not change the
argument.
