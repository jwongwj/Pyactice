# 3.2 Two pointers

**Cue: a sorted sequence, and a question about a pair.**

Two indices walking towards each other turn "check every pair" — O(n²) — into one O(n)
pass. The reason it is correct is worth being able to say out loud, because it is what
tells you whether the trick applies at all:

> At each step, one of the two ends can be *proved* not to belong to any remaining answer.
> Discarding it therefore loses nothing.

If you cannot make that argument for your problem, two pointers is not the tool.

## Pair sums

```python
lo, hi = 0, len(nums) - 1
while lo < hi:
    total = nums[lo] + nums[hi]
    if total == target:
        return (lo, hi)
    if total < target:
        lo += 1          # only a bigger left value can help
    else:
        hi -= 1          # only a smaller right value can help
return None
```

The proof: if the total is too small, then `nums[lo]` paired with *anything still in
range* is also too small, because `nums[hi]` is the largest of them. So `lo` can never be
part of an answer and is safe to drop.

**Sorted or not decides the whole approach.** Unsorted, this same question wants a dict —
one pass, remembering what you have seen, O(n) time and O(n) space. Sorted, two pointers
gets O(n) time and O(1) space. Sorting *in order to* use two pointers costs O(n log n) and
is usually worse than the dict. The standalone `two_sum_pairs` problem beside this unit is
the unsorted version, deliberately.

## Sorted squares

The sneaky one. Squaring a sorted list destroys its order — `[-4, -1, 0, 3]` becomes
`[16, 1, 0, 9]` — so it looks like you must re-sort. But the *largest* square is always at
one end or the other, because the extreme values are the ones furthest from zero. So fill
the answer back to front:

```python
out = [0] * len(nums)
lo, hi = 0, len(nums) - 1
for slot in range(len(nums) - 1, -1, -1):
    if abs(nums[lo]) > abs(nums[hi]):
        out[slot] = nums[lo] ** 2; lo += 1
    else:
        out[slot] = nums[hi] ** 2; hi -= 1
```

This is the pattern to recognise: *the answer is easiest to build from the end*.

## Container with most water

Two lines make a rectangle: width times the *shorter* line. Start at the extremes and
always move the shorter one inwards.

Why is that safe? The shorter line caps the area for **every** pairing it takes part in.
Any other partner is at most as far away — the width can only shrink — and the height is
still capped by that same short line. So no pairing involving it can beat what you just
measured, and it can be discarded.

Moving the taller one would be the mistake: you would give up width while the cap stays
where it is.

## Three-sum: an outer loop plus a sweep

Fix the first value, then run the pair sweep on everything to its right looking for its
negation. O(n²) overall, which is the best known.

All the difficulty is in **not reporting the same triple twice**:

```python
for i in range(len(nums) - 2):
    if i > 0 and nums[i] == nums[i - 1]:
        continue                       # this first value was already tried
    lo, hi = i + 1, len(nums) - 1
    while lo < hi:
        ...
        else:                          # found one
            out.append((nums[i], nums[lo], nums[hi]))
            lo += 1
            while lo < hi and nums[lo] == nums[lo - 1]:
                lo += 1                # skip ALL the repeats, not one
            hi -= 1
```

Two separate skips, and both are needed: one for the fixed value, one inside the sweep.
The inner `while` must advance past *every* repeat — advancing one is what turns
`[-1,-1,-1,2]` into an infinite loop or a duplicated answer.

## Two pointers that do not converge

Not every two-pointer problem walks inwards. The other shapes:

- **Same direction, different speeds** — Floyd's cycle detection (unit 2.8).
- **Same direction, fixed offset** — the nth node from the end (unit 2.8).
- **Read and write** — removing values in place, where one pointer scans and the other
  says where the next kept item goes.
- **Three regions** — the Dutch national flag, this unit's checkpoint.

## The Dutch national flag

Sorting 0s, 1s and 2s in one pass with three pointers: everything before `low` is 0,
everything after `high` is 2, and `mid` is where you are looking.

```python
low = mid = 0
high = len(values) - 1
while mid <= high:
    if values[mid] == 0:
        values[low], values[mid] = values[mid], values[low]
        low += 1; mid += 1
    elif values[mid] == 2:
        values[high], values[mid] = values[mid], values[high]
        high -= 1                      # do NOT advance mid
    else:
        mid += 1
```

The one line to remember is the missing `mid += 1` in the middle branch. A value swapped
in from the right has never been looked at, so you must examine it before moving on. A
value swapped in from the *left* has already been processed, which is why the first branch
does advance.

## Where to reach for which

| the question says | you want |
| --- | --- |
| sorted, find a pair summing to k | two pointers from the ends |
| **un**sorted, find a pair summing to k | a dict |
| sorted, find a triple | outer loop plus a sweep |
| largest area / widest pair | move the shorter side inwards |
| partition into two or three groups | read/write pointers, or Dutch flag |
| longest run with a property | a sliding window (3.3), not this |
