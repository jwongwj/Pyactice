# 3.13 Prefix sums

**Cue: repeated questions about ranges.**

One pass builds a table of running totals. After that, the sum of any slice is a single
subtraction, however many times you are asked.

```python
prefix = [0]
for value in nums:
    prefix.append(prefix[-1] + value)

# sum of nums[start..end] inclusive:
prefix[end + 1] - prefix[start]
```

## The off-by-one, settled once

The table has **n + 1** entries and starts with a 0. That leading zero is not decoration —
it is what makes a range beginning at index 0 work without a special case, because
`prefix[0]` is "the sum of nothing".

With that convention, `prefix[i]` means *the sum of the first i values*, so the slice
`[start, end]` inclusive is `prefix[end + 1] - prefix[start]`. Write the meaning down and
the indices follow; guess the indices and you will be off by one forever.

Build it once, outside the query loop. Building it per query throws away the entire point.

## Bounds are four separate decisions

For a range query, decide and state what happens when:

- `start` is negative
- `end` is past the last index
- `start` is after `end`

Each is its own guard, and each needs its own test. Python's negative indexing makes the
first one particularly nasty: `prefix[-1]` is a perfectly valid expression that silently
returns the *total*, so a missing lower-bound check produces plausible wrong numbers rather
than an error.

## Prefix products, and the two-pass shape

"The product of every value except this one" looks like a job for division: compute the
total product, divide by each value. It breaks the moment any value is zero, and division
is not always available.

Two passes with no division:

```python
out = [1] * len(nums)
running = 1
for i in range(len(nums)):          # everything to the LEFT of i
    out[i] = running
    running *= nums[i]
running = 1
for i in range(len(nums) - 1, -1, -1):   # multiply in everything to the RIGHT
    out[i] *= running
    running *= nums[i]
```

Zeros then need no special handling at all: one zero leaves exactly one position non-zero,
two zeros leave none, and the code above gets both right without knowing it.

This generalises. Any time an answer at position `i` depends on "everything before" and
"everything after", a forward pass and a backward pass will do it in O(n).

## The balance point

"Where do the two sides weigh the same" needs only the total and a running left sum:

```python
right = total - left - value
```

Recomputing both sides at each index is the O(n²) version of the same idea.

## Two dimensions

The same trick with one more term. `table[r][c]` is the sum of the rectangle from the
origin to `(r-1, c-1)`:

```python
table[r + 1][c + 1] = grid[r][c] + table[r][c + 1] + table[r + 1][c] - table[r][c]
```

The subtraction is **inclusion-exclusion**: the region above and the region to the left
both contain the corner region, so it has been added twice and must come off once.

A query reverses the same reasoning:

```python
table[bottom + 1][right + 1] - table[top][right + 1] - table[bottom + 1][left] + table[top][left]
```

Subtract the strip above, subtract the strip to the left, then add back the corner that
was subtracted twice. Drawing four rectangles on paper takes ten seconds and is faster than
reasoning about it.

## Counting, not summing

The pattern that makes this an algorithm rather than a formula: **how many slices sum to
exactly k**. A dict of how often each running total has been seen turns O(n²) into one
pass — see unit 2.3, where it is the Dict checkpoint. The insight is that two prefixes
differing by exactly `k` bracket a slice summing to `k`.

Three details, each a bug when missed: seed the dict with `{0: 1}`; count occurrences
rather than merely recording which totals appeared; and look up before inserting.

## Where to reach for which

| the question says | you want |
| --- | --- |
| many range-sum queries | a prefix table |
| how many subarrays sum to k | prefix sums plus a dict of counts |
| everything except this one | a forward pass and a backward pass |
| the best contiguous run | Kadane (3.14), not this |
| range queries with **updates** in between | a Fenwick or segment tree, not this |
