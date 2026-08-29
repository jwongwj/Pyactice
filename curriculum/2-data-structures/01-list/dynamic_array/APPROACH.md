# Approach

## The state

```python
self.slots = []      # the allocated block; len(slots) IS the capacity
self.used = 0         # how many are real
```

Two numbers, and the invariant `0 <= used <= len(slots)`. Every method is a statement about
that invariant.

The distinction between **size** and **capacity** is the whole exercise. A slot can exist
and hold nothing meaningful; only the first `used` slots are the array.

## Growth

```python
if self.used == len(self.slots):
    self._grow()
```

Only when full, and:

```python
new_capacity = max(1, len(self.slots) * 2)
```

`max(1, ...)` matters. Doubling 0 is 0, so an array that starts empty never grows without
it — an infinite loop or an IndexError on the first append.

**Why a factor and not a step.** Growing by a constant means every k appends copy the whole
array, so n appends cost O(n²)/k — still quadratic. Growing by a factor means the copies
happen at 1, 2, 4, 8, … and the total copying across n appends is 1 + 2 + 4 + … + n < 2n.
So the total is O(n) and the average per append is O(1).

That is **amortised** O(1). Any individual append may cost O(n). Say both.

## Why pop does not shrink

If popping released memory as soon as the array was half empty, an append/pop/append cycle
at the boundary would reallocate on every single operation — the worst case becomes the
common case. Real implementations shrink only when the array falls to a *quarter* full, so
there is hysteresis between the two thresholds.

This problem does not ask for shrinking at all. Knowing why the naive version is wrong is
enough.

## Bounds

Three separate checks, and each has its own case:

- `index < 0` — out of range, not from the end.
- `index >= self.used` — out of range even if `index < len(self.slots)`.
- an empty array — everything is out of range.

## Order of work

1. `append`, `size`, `capacity` and `_grow`, with the `max(1, ...)`.
2. `get` and `set` with the bounds check written against `used`.
3. `items`, slicing the first `used` slots.
4. `pop`, decrementing `used` and nothing else.
