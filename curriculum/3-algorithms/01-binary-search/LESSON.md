# 3.1 Binary search

**Cue: a sorted input, or a monotonic answer.** The second half is what makes this an
algorithm rather than a library call, and it is where the hard versions live.

## The template, and why the bounds fight you

Binary search is four lines and famously hard to get right. Almost every bug is one of
three things: an inclusive bound treated as exclusive, a bound that fails to move so the
loop never ends, or a midpoint that rounds the wrong way.

Pick **one** template and keep it. This one uses an inclusive `hi`:

```python
lo, hi = 0, len(nums) - 1
while lo <= hi:                    # <= because hi is a real index
    mid = (lo + hi) // 2
    if nums[mid] == target:
        return mid
    if nums[mid] < target:
        lo = mid + 1               # mid is ruled out, so + 1
    else:
        hi = mid - 1               # mid is ruled out, so - 1
return -1
```

The `+ 1` and `- 1` are what guarantee termination: the range shrinks every iteration
because `mid` itself is discarded. Writing `lo = mid` instead is the classic infinite loop.

## The other template: no equality branch

For "where does this belong" questions, do not test equality at all. Narrow until the two
bounds meet, and the meeting point is the answer:

```python
lo, hi = 0, len(nums)              # hi is EXCLUSIVE here -- one past the end
while lo < hi:                     # < because hi is not a real index
    mid = (lo + hi) // 2
    if nums[mid] < target:
        lo = mid + 1
    else:
        hi = mid                   # mid might be the answer, so do NOT skip it
return lo
```

That is `bisect_left`: the leftmost position where `target` could be inserted with the list
staying sorted. Note `hi = mid`, not `mid - 1` — in this template `hi` is a candidate, not
a rejected value. Mixing the two templates is where the off-by-ones come from.

`bisect_left` and `bisect_right` in the standard library do this, and in real code you
should use them. Writing it once is what makes the boundary versions below legible.

## First and last occurrence

With duplicates, a plain search lands on an *arbitrary* one of them. To find the first, do
not stop when you find a match — record it and keep searching to the left:

```python
found = -1
while lo <= hi:
    mid = (lo + hi) // 2
    if nums[mid] == target:
        found = mid
        hi = mid - 1               # keep looking LEFT
    elif nums[mid] < target:
        lo = mid + 1
    else:
        hi = mid - 1
return found
```

For the last occurrence, the one changed line is `lo = mid + 1` on a match — keep looking
right. The two are mirror images, and writing both is worth it because getting the mirror
subtly wrong is exactly how an off-by-one hides.

The cases that catch a broken version are the ones where the answer is at an *end*: the
target at index 0, or at the final index. A midpoint-first search reaches the middle
easily and the edges only if the bounds are right.

## Rotated

A sorted list rotated an unknown amount is still sorted — it just starts in the wrong
place. That is enough structure to halve the range. Compare the midpoint to the **right
end** to work out which half is properly ordered:

```python
lo, hi = 0, len(nums) - 1
while lo < hi:
    mid = (lo + hi) // 2
    if nums[mid] > nums[hi]:
        lo = mid + 1               # the minimum is strictly RIGHT of mid
    else:
        hi = mid                   # mid might BE the minimum
return nums[lo]
```

Comparing against the right end rather than the left is deliberate: with the left end,
`[1, 2, 3]` and `[2, 3, 1]` are indistinguishable at the midpoint. Duplicates break this
entirely — with `[2, 2, 2, 1, 2]` neither half can be ruled out, and the worst case
degrades to O(n).

## Binary search on the answer

This is the version worth recognising, because there is no list to search at all.

When a question asks for the **smallest X that works** (or the largest that does), and
"does X work?" is *monotonic* — false, false, false, true, true, true, with the flip
happening exactly once — you can binary search over X itself:

```python
lo, hi = smallest_conceivable, largest_conceivable
while lo < hi:
    mid = (lo + hi) // 2
    if works(mid):
        hi = mid                   # mid works, so the answer is mid or smaller
    else:
        lo = mid + 1               # mid fails, so the answer is bigger
return lo
```

The three things to get right, in order of how often they are got wrong:

1. **Prove the monotonicity.** If a bigger capacity can ever be *worse*, the search is
   invalid and will return nonsense rather than failing loudly.
2. **Choose the bounds from the problem, not from optimism.** For "smallest ship capacity",
   nothing below the heaviest single item can ever work, because items cannot be split; and
   the total always works. So `lo, hi = max(weights), sum(weights)`. Starting `lo` at 0
   wastes iterations and starting it at 1 can return an impossible answer.
3. **Write `works()` as a plain simulation.** It is usually a simple greedy pass, and it is
   where the actual reading of the question lives — whether items may be reordered, whether
   a day can be empty, what happens on an exact fit.

Once you see this shape it appears everywhere: minimum eating speed, smallest divisor,
splitting an array into k parts, the largest minimum gap. The question never mentions
sorting or searching.

## Where to reach for which

| the question says | use |
| --- | --- |
| find X in a sorted list | the classic template |
| where would X go | `bisect_left` |
| first / last occurrence of X | record and keep narrowing that way |
| sorted, but rotated | compare the midpoint to the right end |
| smallest / largest X such that … | binary search on the answer |
| unsorted, find a pair summing to k | a dict, not a search (unit 2.3) |
