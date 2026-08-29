# Approach

## The representation

A fixed list, a read index and a write index:

```python
self.slots = [None] * capacity
self.head = 0        # where the next read comes from
self.count = 0       # how many are held
```

The write position is derived: `(head + count) % capacity`. Everything is modular
arithmetic on those two numbers, and nothing is ever appended or removed.

## The decision that defines the problem

With a head index and a tail index alone, **`head == tail` means both empty and full**. The
two states are indistinguishable, and every bug in a circular buffer traces back to that.

Three standard resolutions:

1. **Keep a count** — the simplest, and what the sketch above does. One extra integer, no
   ambiguity, and `size` is free.
2. **Leave one slot unused** — full means `(tail + 1) % capacity == head`. Costs a slot,
   avoids the counter.
3. **Keep a full flag** — set on write when the indices meet, cleared on read.

Any of them is fine; pick one and say why. The counter is the least error-prone under time
pressure.

## Overwriting

When a write finds the buffer full, the oldest value goes:

```python
if self.count == self.capacity:
    self.head = (self.head + 1) % self.capacity     # drop the oldest
    ...                                             # count stays the same
    return False
```

**The head must move.** Writing into the slot without advancing the read index leaves the
overwritten value logically still present, and it comes back out later.

## Zero capacity

A real state, not an error. Nothing fits, so every write is refused, `is_full` is true
vacuously, and every read is `None`. Guard the modulo — `% 0` raises — before doing any
arithmetic.

The same applies before `resize` is ever called: treat an unsized buffer as one of
capacity 0 rather than crashing.

## Order of work

1. `resize`, `size`, `is_full` — the state, with the zero case handled.
2. `write` and `read` for the non-full case.
3. `items`, walking `count` slots from `head` with the modulo.
4. Then the overwrite path, and only then the wrap-around cases.
