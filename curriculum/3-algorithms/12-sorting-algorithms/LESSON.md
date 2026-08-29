# 3.12 Sorting algorithms

`sorted()` is the right answer in every real situation. This unit is the one place it is
forbidden, because the question being simulated is "implement it" — and because two of
these steps are genuinely useful on their own.

## What Python actually does

`sorted()` and `list.sort()` use **Timsort**: a merge sort that finds runs already in order
and merges them. O(n log n) worst case, O(n) on data that is already nearly sorted, and
**stable**.

`sorted()` returns a new list; `.sort()` sorts in place and returns `None`. Assigning the
result of `.sort()` is the classic slip (unit 2.1).

## Merge sort

Split, sort each half, merge:

```python
if len(nums) <= 1:
    return list(nums)
left, right = merge_sort(nums[:mid]), merge_sort(nums[mid:])
# then the two-pointer merge from unit 2.1
```

The base case has to accept an **empty** list, not only a single item, or an odd-length
split recurses forever on one side.

Properties: O(n log n) always, stable, needs O(n) extra space. The merge step is the
valuable part on its own — it is how you combine sorted files too big for memory, and
`heapq.merge` is its k-way generalisation.

## Partition, and why three-way

```python
less, equal, greater = [], [], []
for value in nums:
    (less if value < pivot else greater if value > pivot else equal).append(value)
```

Two-way partitioning puts every equal value on one side, so an input of all-equal values
degrades quicksort to O(n²). Three-way handles duplicates for free and is the version worth
remembering.

## Quickselect

The reason partition is worth knowing. To find the kth smallest, partition and then recurse
into **only the side that can contain the answer**:

```python
if k <= len(less):        values = less
elif k <= len(less) + len(equal):  return pivot
else:  k -= len(less) + len(equal); values = greater
```

O(n) on average, because the work halves each time instead of doubling. Sorting to find one
value is O(n log n) for no reason.

Worst case is O(n²) with unlucky pivots. Say so, and say that a random or median-of-three
pivot fixes it in practice.

## Counting sort

The one that beats the comparison bound — by not comparing:

```python
counts = [0] * (top + 1)
for value in nums: counts[value] += 1
```

O(n + k) where k is the value range. Worth it when the range is small and known; useless
when it is not, because the bucket list is the size of the range regardless of how many
values you have.

The comparison lower bound of O(n log n) applies to algorithms that *compare*. Counting
sort sidesteps it entirely, which is the theoretical point worth being able to state.

## Stability

**Stable** means equal keys keep their original relative order. It matters more than it
sounds:

- It is what lets you sort by several keys in separate passes — sort by the least
  significant first, then the most significant, and the earlier order survives inside
  ties (unit 2.2).
- Sorting rows by the *whole tuple* rather than by the key alone silently reorders ties by
  the other fields, which is a different answer.

Merge sort and insertion sort are stable; quicksort and heapsort are not.

## Where to reach for which

| you need | use |
| --- | --- |
| to sort something | `sorted()` — every time |
| the kth smallest / largest | quickselect, or `heapq.nsmallest` |
| the k best of n, k small | a heap (2.7) |
| small known integer range | counting sort |
| several sorted inputs combined | `heapq.merge` |
| ties to keep their order | anything stable — Timsort is |
| to explain how sort works | merge sort, then partition |
