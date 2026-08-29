# 3.14 Kadane

**Cue: the best contiguous run.**

One sentence, and everything in this unit is a variation of it:

> The best run **ending at this position** is either this value alone, or this value joined
> to the best run ending at the previous position.

```python
best = ending_here = nums[0]
for value in nums[1:]:
    ending_here = max(value, ending_here + value)
    best = max(best, ending_here)
```

Two variables, one pass, O(1) space. It is dynamic programming with the table thrown away,
because each answer depends only on the one immediately before it.

## Start from the data, not from zero

`best = 0` is the classic bug. It silently assumes the empty run is allowed, and an
all-negative list then answers 0 — a run that does not exist.

Decide explicitly:

- **Run may not be empty** (the usual reading): seed both variables from `nums[0]` and
  start the loop at index 1. An all-negative list answers with its least negative value.
- **Run may be empty**: 0 is a valid answer and the seeds can be 0.

Whichever the question wants, seeding from `nums[0]` also means the loop must start at
index 1 — visiting index 0 twice counts it twice, which a single-element list exposes
immediately.

## Keeping the indices

Once you want *where* the best run is, the thing that catches people is that the start
index moves **only on a restart**:

```python
if value > ending_here + value:
    ending_here = value
    start = index          # the run restarted HERE
else:
    ending_here += value   # start is unchanged
if ending_here > best:
    best = ending_here
    best_start, best_end = start, index
```

Updating `start` on every improvement is wrong: extending a run improves it without
restarting it.

Note `>` rather than `>=` in the final comparison. That choice is the tie-break, and it is
worth being deliberate about: strict `>` keeps the earliest and shortest of equally good
runs, `>=` keeps the latest and longest. Say which the question wants.

## Products are not sums

The shape does not transfer. A negative value flips the sign of a product, so the
*smallest* running product is a candidate for the largest as soon as another negative
arrives:

```python
if value < 0:
    high, low = low, high      # swap BEFORE extending
high = max(value, high * value)
low = min(value, low * value)
best = max(best, high)
```

Carry both. The swap happens only on a negative value — swapping unconditionally is a
different (and wrong) algorithm. A zero resets both to zero, which is handled by the
`max(value, ...)` without a special case.

## Wrapping around

The circular version has a neat trick. The best run either wraps or it does not:

- **Does not wrap**: plain Kadane.
- **Does wrap**: then the values it *excludes* form a contiguous run in the middle — so the
  answer is `total - (the minimum subarray)`.

Take the larger of the two. With one caveat that is the whole reason this is a checkpoint:
when every value is negative, the minimum subarray is the entire list, and
`total - minimum` is 0 — which corresponds to taking an *empty* run, and empty is not
allowed. So:

```python
if wrapped == 0 and straight < 0:
    return straight
return max(straight, wrapped)
```

Testing the all-negative case is not optional here. It is the only case where the clever
half of the algorithm produces a wrong answer.

## Where to reach for which

| the question says | you want |
| --- | --- |
| largest sum of a contiguous run | Kadane |
| ...and where it is | Kadane tracking the restart index |
| largest **product** | Kadane carrying both max and min |
| ...circular | max(plain, total − minimum run), with the all-negative guard |
| largest sum of any k elements | sorting or a heap — not contiguous, not this |
| longest run with a property | a sliding window (3.3) |
