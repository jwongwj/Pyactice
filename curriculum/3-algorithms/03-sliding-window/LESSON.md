# 3.3 Sliding window

**Cue: "contiguous", plus "longest" or "shortest" or "every window of size k".**

The word that matters is *contiguous*. If the elements need not be adjacent, this is the
wrong tool — that is usually sorting, a heap, or dynamic programming.

## Two shapes

**Fixed** — you know the width. Add the arrival, subtract the departure:

```python
total = sum(nums[:k])
best = total
for i in range(k, len(nums)):
    total += nums[i] - nums[i - k]
    best = max(best, total)
```

**Variable** — the right edge always advances; the left edge catches up only while the
window is invalid:

```python
left = 0
for right, value in enumerate(nums):
    add(value)
    while invalid():
        remove(nums[left])
        left += 1
    best = max(best, right - left + 1)
```

Both are O(n) because **neither pointer ever moves backwards**. Each element is added once
and removed at most once. That is the whole efficiency argument, and it is worth stating in
an interview.

## Initialise `best` from the data, not from zero

`best = 0` is the most common bug in the fixed form. If every window is negative, zero is
not an achievable answer and the function reports a window that does not exist. Start from
the first real window and improve from there.

The same applies to the "no answer" case: decide what an empty input or an impossible `k`
returns, and write it down. Returning 0 for "no window exists" and 0 for "the best window
sums to 0" makes the two indistinguishable.

## The condition for the variable form

The variable window is only correct when validity is **monotonic**: growing the window can
only make it worse, and shrinking can only make it better. Then "shrink until valid again"
is guaranteed to find the shortest fix.

This is why *"the longest subarray summing to at most k"* is a window when the values are
non-negative, and is **not** a window once negatives appear — growing the window might
lower the sum, so shrinking from the left proves nothing. That version belongs to prefix
sums (unit 3.13). Check the sign of your values before reaching for a window.

## The left edge only moves forward

For "longest substring without repeats", the temptation is to jump the left edge to just
after the previous occurrence of the repeated character. That is correct *only* if you also
guard against jumping backwards:

```python
left = max(left, last_seen[character] + 1)
```

Without the `max`, a repeat from long ago drags the left edge back into territory it has
already left, and the window becomes invalid without you noticing. `"abba"` is the shortest
input that shows it: at the final `a`, the last-seen index of `a` is 0, and jumping to 1
would re-admit the `b` at index 2.

The set-based version avoids the trap entirely, because it only ever removes one at a time:

```python
while character in inside:
    inside.discard(text[left]); left += 1
```

## Counts, and the zero-key trap

For anagram windows, compare two `Counter`s. One detail decides whether it works:

```python
window[leaving] -= 1
if window[leaving] == 0:
    del window[leaving]
```

`Counter({'a': 1})` and `Counter({'a': 1, 'b': 0})` are **not equal**. A key that has fallen
to zero has to be deleted, or the comparison never succeeds again after the first departure.

Sorting each window instead is correct and O(n·m log m); the counts are O(1) per step.

## Shrinking past what you no longer need

The minimum-window problem adds one more idea: after the window becomes valid, keep
advancing the left edge while it *stays* valid. A character at the left may be surplus —
already covered by another copy further in — and dropping it gives a shorter answer without
losing validity.

`min_window("aab", "ab")` is the smallest case that shows it. The window `"aab"` is valid;
the first `a` is spare, and the answer is `"ab"`. Stopping at the first valid window is the
bug.

Track how many requirements are still unmet as a single counter rather than comparing whole
dictionaries each step:

```python
if wanted[character] > 0:      # this copy was actually needed
    missing -= 1
wanted[character] -= 1         # may go negative: a surplus copy
```

The count going negative is what marks the surplus, and is what tells you the left edge can
advance.

## Where to reach for which

| the question says | you want |
| --- | --- |
| every window of size k | fixed window |
| longest / shortest contiguous run with a property | variable window |
| ...with negative numbers involved | prefix sums (3.13), not a window |
| max or min *of* each window | monotonic deque (2.6) |
| count of subarrays summing to exactly k | prefix sums with a dict (2.3) |
| not contiguous | sorting, a heap, or DP |
