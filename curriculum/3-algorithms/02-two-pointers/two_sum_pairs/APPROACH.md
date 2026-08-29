# Approach — Pair Sums

## What to notice first

The question asks for pairs **by value**, not by position. That one word decides the
whole shape of the answer: you are not enumerating index pairs, you are collecting a
*set* of value pairs. Every duplicate-handling headache in this problem dissolves once
you hold that distinction, and none of them do if you don't.

## The naive attempt, and what it costs

The obvious solution is two nested loops over indices:

```python
for i in range(len(numbers)):
    for j in range(i + 1, len(numbers)):
        if numbers[i] + numbers[j] == target:
            ...
```

This is correct, and it is the answer most people write first. It has two problems.

**It is O(n²).** At 50,000 elements that is 1.25 billion additions. The hidden case with
40,000 elements exists precisely to reject it — not to be cruel, but because "can you get
from the quadratic answer to the linear one" is the actual question being asked.

**It produces duplicates.** `[1, 1, 4, 4, 4]` with target 5 has six index pairs that work
and exactly one distinct value pair. If you build a list, you must dedupe it afterwards;
if you build a set, you never had the problem.

## The idea

One pass, carrying a set of the values you have already walked past:

> For each value, its partner is `target - value`. If you have **already seen** that
> partner, the pair exists. Record it, then add the current value to the seen set.

That ordering — check, *then* add — is the whole trick, and it is what makes the
self-pairing rule fall out for free rather than needing a special case:

- `[3, 1, 4]`, target 6: when you reach `3`, `seen` is empty, so `3`'s partner `3` is not
  there. Nothing is recorded. Correct — there is only one `3`.
- `[3, 3, 1]`, target 6: at the *second* `3`, the first one is already in `seen`, so the
  pair is recorded. Correct — those are two different elements.

Check-then-add means "have I seen a *different* element holding this value", which is
exactly the rule the statement states. Add-then-check would let every element pair with
itself, and you would then need an explicit guard to undo it.

## Getting the shape of the answer right

Three separate requirements, and they are easiest to satisfy in this order:

1. **Sort inside the pair.** Store `(min, max)` rather than the order you met them in.
2. **Dedupe.** A `set` of those tuples. Because each tuple is already sorted, `(1, 4)` and
   `(4, 1)` cannot both be in it.
3. **Sort the pairs.** `sorted()` on a set of tuples orders by first element then second,
   which is what the statement asks for. Convert to lists at the very end.

Do steps 1 and 2 as you go and step 3 once at the end. Doing 3 as you go costs a sort per
insertion for no benefit.

## Complexity

Time **O(n log n)**, space **O(n)**. The pass is linear; the final `sorted()` over the
found pairs dominates only when there are many of them, and there can never be more pairs
than input values.

An O(n) sort-free version is possible if you are willing to return the pairs in an
unspecified order — but the statement specifies the order, so the sort is required work
rather than sloppiness.

## The alternative worth knowing

Sort the input, then walk two pointers inward from both ends. Also O(n log n), also
correct, and it handles duplicates by skipping equal neighbours. It is the better answer
when the input is already sorted, or when you need the pairs *in* sorted order without a
second pass, or when O(n) extra space is not available.

It has a trap this problem tests directly: sorting the input means **sorting a copy**.
`numbers` belongs to the caller. `sorted(numbers)` is fine; `numbers.sort()` is a bug that
passes every single-call test and fails the moment anyone calls you twice.
