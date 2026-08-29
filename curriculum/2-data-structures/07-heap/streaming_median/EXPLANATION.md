# Explanation

## The shape of the answer

```python
import heapq

class StreamingMedian:
    def __init__(self):
        self.lower = []        # max-heap, negated
        self.upper = []        # min-heap
        self.least = None

    def add(self, value):
        self.least = value if self.least is None else min(self.least, value)
        heapq.heappush(self.lower, -value)
        heapq.heappush(self.upper, -heapq.heappop(self.lower))
        if len(self.upper) > len(self.lower):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))

    def median(self):
        if not self.lower:
            return None
        if len(self.lower) > len(self.upper):
            return -self.lower[0]
        return (-self.lower[0] + self.upper[0]) // 2

    def lower_half_size(self):
        return len(self.lower)

    def count(self):
        return len(self.lower) + len(self.upper)

    def smallest(self):
        return self.least
```

## Why the unconditional dance works

Push the new value into the lower half. Its top is now the largest of the small values —
which may be the new value itself, or may be one displaced by it. Move that top into the
upper half. Invariant 1 now holds regardless of where the new value belonged, because the
largest small value has been offered to the upper half.

That move may leave the upper half one too big, so the third step moves its smallest back.
Invariant 2 now holds too.

No comparisons, no branches on the value. Correct for every input, including the two
adversarial ones — ascending and descending.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `descending_input` | adding to whichever heap is smaller, ignoring the value |
| `ascending_input` | the same in the other direction, and the round-down |
| `even_negative_average` | truncating towards zero instead of flooring |
| `balance_never_off_by_two` | a missing or one-sided rebalance |
| `large_then_small` | a value that must move to the other half later |
| `zero_included` | falsiness standing in for "nothing added" |
| `smallest_tracks` | assuming the smallest is at a heap top |
| `interleaved_reads` | `median` disturbing the heaps |

`descending_input` is the one worth running by hand. It is four lines of input and it
falsifies the intuitive design completely.

## Complexity

| operation | cost |
| --- | --- |
| add | O(log n) |
| median, count, lower_half_size, smallest | O(1) |

Re-sorting per insertion would be O(n log n) each; keeping a sorted list with `bisect`
would be O(1) to read and O(n) to insert, because the shift is linear. Two heaps are the
only structure here that is logarithmic on insert *and* constant to read.

## Where this idea appears again

The general shape — **keep two structures facing each other so a boundary is always at a
top** — also solves the sliding-window median, "IPO"-style problems where you repeatedly
take the best affordable option, and any question about a running k-th largest.

`heapq.nlargest` (unit 2.7) is the one-shot version. This is what you need when the data
keeps arriving.
