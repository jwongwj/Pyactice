# 2.7 Heap / priority queue

A heap answers one question cheaply: **what is the smallest thing here?** Not "give me
everything in order" — just the smallest, over and over, while things keep arriving.

`heapq` is a set of functions over a plain list. There is no Heap class:

```python
import heapq

heap = [5, 1, 3]
heapq.heapify(heap)        # O(n), in place
heapq.heappush(heap, 2)    # O(log n)
heapq.heappop(heap)        # O(log n) -- the SMALLEST
heap[0]                    # peek, O(1)
```

The list is not sorted, and printing it will not look sorted. The only guarantee is that
`heap[0]` is the smallest; the rest satisfies a weaker parent-below-children property.
Relying on any other position is a bug.

## When a heap beats sorting

| you want | cost |
| --- | --- |
| everything in order | `sorted` — O(n log n) |
| the k smallest, k much smaller than n | heap — O(n log k) |
| the smallest, repeatedly, while more arrive | heap — O(log n) per operation |

That third row is the one `sorted` genuinely cannot do. If items keep arriving, a sorted
list must be re-sorted or inserted into; a heap absorbs each one in log n.

When k is close to n, sorting is *better* — one pass of an efficient sort beats n heap
operations, and it is less code. "Use a heap for top-k" is a rule of thumb, not a law.

## nsmallest and nlargest

Nine times out of ten, this is all you need:

```python
heapq.nsmallest(3, nums)              # ascending
heapq.nlargest(3, nums)               # DESCENDING -- largest first
heapq.nsmallest(3, points, key=lambda p: p[0]**2 + p[1]**2)
```

Two things to remember. `nlargest` returns largest-first, so no reversal is needed — adding
one is a common wasted step. And both take a `key`, which is how you order by something
computed rather than by the item itself.

For distances, compare **squared** distance. It orders identically to the real distance and
avoids a `sqrt` that can only introduce floating-point noise.

## There is no max-heap

`heapq` is a min-heap and has no `reverse` flag. Negate on the way in and again on the way
out:

```python
heap = [-value for value in nums]
heapq.heapify(heap)
largest = -heapq.heappop(heap)
```

For tuples, negate only the component you want reversed — the same trick as a compound sort
key in unit 2.2:

```python
heapq.heappush(heap, (-count, word))     # count descending, word ascending
```

This is also how tie-breaks work in a heap: it compares tuples element by element, so the
second component decides when the first is equal. Which means every component must be
comparable — a tuple ending in a dict will raise `TypeError` the moment two priorities tie.
When the payload is not comparable, insert a unique counter before it:

```python
heapq.heappush(heap, (priority, next(counter), payload))
```

## merge

```python
list(heapq.merge(*lists))
```

Merges any number of already-sorted iterables into one sorted stream, lazily. This is the
k-way generalisation of the two-pointer merge from unit 2.1, and it is the right answer
whenever you catch yourself concatenating sorted things and re-sorting.

## Draining a heap is a sort

Popping until empty yields everything in order — that is heapsort, O(n log n). Worth writing
once, because it makes the invariant concrete. It is not worth *using*: `sorted` is faster
in practice and one word long.

## Watch the tie-break

`Counter.most_common` and `nlargest` on counts both break ties by **insertion order**, not
alphabetically. When a question says "ties broken alphabetically", neither does it for you:

```python
ranked = heapq.nsmallest(k, counts.items(), key=lambda item: (-item[1], item[0]))
```

Negated count first, then the item itself — `nsmallest` with that key gives most-frequent
first with alphabetical ties, which is what was actually asked.

## Where to reach for which

| you want | use |
| --- | --- |
| the k best of n | `nsmallest` / `nlargest` |
| the best, repeatedly, as things arrive | `heappush` / `heappop` |
| the largest, from a min-heap | negate in and out |
| several sorted inputs, combined | `heapq.merge` |
| everything in order, one shot | `sorted` — not a heap |
| the running median | two heaps, one of each direction |
