# Explanation

## The shape of the answer

```python
class MinStack:
    def __init__(self):
        self.values = []
        self.minima = []

    def push(self, value):
        self.values.append(value)
        smallest = value if not self.minima else min(value, self.minima[-1])
        self.minima.append(smallest)

    def pop(self):
        if not self.values:
            return None
        self.minima.pop()
        return self.values.pop()

    def top(self):
        return self.values[-1] if self.values else None

    def get_min(self):
        return self.minima[-1] if self.minima else None

    def size(self):
        return len(self.values)
```

Both stacks are always the same height. That invariant is what makes every method a
one-liner: there is no case analysis, because the answer for depth n was computed when
depth n was created.

## Why this is O(1) and the obvious answer is not

`min(self.values)` is O(n) per call. Over m calls that is O(n·m), and a stack this is used
on will be called a lot. Trading one integer per element for constant-time queries is the
whole design.

That trade — precompute an aggregate and carry it, rather than recompute it — is the
recurring idea. Prefix sums (unit 3.13) are the same bargain in a different shape.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `min_restored_after_pop` | a single `self.minimum` variable |
| `min_with_duplicates` | pushing to `minima` only when *strictly* smaller |
| `min_after_all_popped` | a stale minimum surviving an emptied stack |
| `empty_operations` | raising instead of returning None |
| `negatives_and_zero` | using falsiness to mean "no minimum yet" |

The duplicate case is the one worth dwelling on. It fails *late* — the stack is still
non-empty, so nothing looks wrong until `get_min` is called — and it is exactly the kind of
bug a few hand-run examples miss.

## Complexity

| operation | time | space |
| --- | --- | --- |
| push / pop / top / get_min / size | O(1) | O(n) total, two integers per element |

## Where this idea appears again

- **Max queue** — the same problem with a deque, which also has to expire from the front,
  and therefore needs a monotonic structure rather than a parallel stack (unit 2.6).
- **Monotonic stack** — keeping a stack in sorted order so a property is always readable
  at the top (units 2.5 and 3.15).
- **Prefix aggregates** — sums, products, minima computed once and carried (unit 3.13).
