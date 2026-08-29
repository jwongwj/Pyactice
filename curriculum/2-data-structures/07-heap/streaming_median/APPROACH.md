# Approach

## Why two heaps

The median only depends on the two values in the middle. Everything smaller and everything
larger is irrelevant except for its *count*. So keep the values in two piles and make sure
the middle is always at the top of one of them:

- a **max-heap** of the smaller half, whose top is the largest of the small values;
- a **min-heap** of the larger half, whose top is the smallest of the large values.

The median is then the max-heap's top (odd count), or the average of both tops (even).

`heapq` has no max-heap, so the lower half stores negated values — the trick from unit 2.7.

## Write the invariant down first

Two conditions, and every bug is a violation of one of them:

1. **Everything in the lower half is ≤ everything in the upper half.**
2. **The lower half has the same number of values as the upper, or exactly one more.**

## The insertion, in two steps

Do not try to decide which heap a value belongs to and be done. The reliable version pushes
unconditionally and then repairs:

```python
heapq.heappush(self.lower, -value)                       # always to the lower half
heapq.heappush(self.upper, -heapq.heappop(self.lower))   # move its largest across
if len(self.upper) > len(self.lower):                    # restore the size rule
    heapq.heappush(self.lower, -heapq.heappop(self.upper))
```

Three pushes and two pops, unconditionally, and both invariants hold afterwards. It is
shorter and far harder to get wrong than the version that compares against the tops.

The tempting alternative — "add to whichever heap is smaller" — breaks invariant 1. A
descending input has every value belonging in the lower half, and sizes alone cannot see
that.

## The even case rounds down

`(low + high) // 2` in Python floors towards negative infinity, which is what this problem
asks for. If a question wants truncation towards zero instead, that is `int((low + high) / 2)`
— and the two differ only on negatives, which is exactly where nobody tests.

## The smallest value is not at a heap top

The lower half's top is its *largest*. The smallest value in the stream is at the bottom of
that heap, and a heap does not give you its bottom. Either track it separately as values
arrive, or accept an O(n) scan of one heap and say so.

That asymmetry is worth noticing: a heap answers one question cheaply, not every question.

## Order of work

1. `add` with the three-push dance, and `count`.
2. `median` for the odd case, then the even case.
3. `lower_half_size`, which is just the length.
4. `smallest`, tracked as you go.
5. Then the negative and empty cases.
