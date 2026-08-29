# 2.6 Queue and deque

The whole subtopic exists because of one fact from unit 2.1: `list.pop(0)` is O(n). Every
element after the removed one shifts left, so draining a list from the front is O(n²).

```python
from collections import deque

d = deque([1, 2, 3])
d.append(4)          # O(1) right
d.appendleft(0)      # O(1) LEFT -- this is what a list cannot do
d.pop()              # O(1) right
d.popleft()          # O(1) left
```

What you give up is O(1) indexing. `d[0]` and `d[-1]` are cheap, but `d[n]` in the middle
walks there. A deque is for the ends; a list is for random access.

## maxlen: a window that discards for you

```python
recent = deque(values, maxlen=3)
```

Once full, appending drops from the opposite end automatically. This is the tidiest way to
keep "the last N of a stream", and unlike a slice it works on data you cannot index — a
generator, a socket, a log being read line by line. `maxlen=0` is legal and holds nothing.

## rotate

```python
d.rotate(1)      # right: [1,2,3] -> [3,1,2]
d.rotate(-1)     # left:  [1,2,3] -> [2,3,1]
```

It handles `k` larger than the length and negative `k` without any arithmetic of your own,
which is exactly where the two-slice version from unit 2.1 goes wrong. It is also safe on
an empty deque, where the slice version divides by zero.

## Breadth-first search

This is the payoff. BFS explores in **distance order**: everything one step away, then
everything two steps away, and so on. The consequence is that the first time you reach a
cell, you have reached it by a shortest path. Depth-first search finds *a* path, not the
shortest one — so for "fewest steps", the queue is not a detail, it is the algorithm.

```python
queue = deque([(0, 0, 1)])          # row, col, steps-so-far
seen = {(0, 0)}
while queue:
    row, col, steps = queue.popleft()
    if (row, col) == target:
        return steps
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = row + dr, col + dc
        if in_bounds(nr, nc) and (nr, nc) not in seen and grid[nr][nc] == 0:
            seen.add((nr, nc))       # mark on ENQUEUE, not on dequeue
            queue.append((nr, nc, steps + 1))
return -1
```

Four details, each of which is a bug when missed:

- **Mark visited when you enqueue**, not when you dequeue. Otherwise the same cell is
  queued several times before it is first processed, and the queue blows up.
- **`popleft`, not `pop`.** `pop` turns it into a depth-first search that still looks
  like BFS, and it will happily return a path that is not the shortest.
- **Check the start and the end** before you begin. A blocked start is unreachable, not
  free.
- **Decide what you are counting.** Cells visited, or steps taken? They differ by one, and
  a single-cell grid is the case that tells you which the question meant.

The same loop, seeded with several starting cells at once, is "multi-source BFS" — how
long for rot to spread to every orange, how far is every cell from the nearest exit. The
only change is what goes into the queue before the loop starts.

## The monotonic deque, and the sliding-window maximum

"The maximum of every window of k" done directly is `max()` per window: O(n·k). The linear
answer is a deque of **indices**, kept with their values decreasing:

```python
window = deque()
for index, value in enumerate(nums):
    while window and window[0] <= index - k:      # left: fell out of the window
        window.popleft()
    while window and nums[window[-1]] < value:    # right: can never be the max again
        window.pop()
    window.append(index)
    if index >= k - 1:
        answer.append(nums[window[0]])
```

The insight is the second `while`: if a value smaller than the newcomer is still in the
window, it can never be the maximum again — the newcomer is bigger *and* leaves later. So
it can be discarded permanently. Every index enters and leaves once, so it is O(n).

Note `<` rather than `<=` in that eviction. Equal values must not evict each other, or a
window can lose the copy it still needed.

This is the stack version from 2.5 with one extra ability: because a deque is cheap at both
ends, it can also expire things from the *front* for being too old. That is the whole
difference between "next greater" and "maximum in a window".

## Where to reach for which

| you want | use |
| --- | --- |
| FIFO, or anything popping from the front | `deque` |
| LIFO | `list` — `append` / `pop` |
| the last N of a stream | `deque(maxlen=n)` |
| fewest steps, unweighted | BFS with a `deque` |
| max/min of every window | monotonic `deque` of indices |
| fewest steps, *weighted* | a heap, not a queue — that is Dijkstra, unit 3.7 |
