# Explanation — Pair Sums

A walkthrough of the solution in the order you meet it. Read `APPROACH.md` first for
*why* it is shaped this way; this file is *what each line does*.

```python
def pair_sums(numbers, target):
    seen = set()
    found = set()
    for value in numbers:
        partner = target - value
        if partner in seen:
            found.add((min(value, partner), max(value, partner)))
        seen.add(value)
    return [list(pair) for pair in sorted(found)]
```

Nine lines. Every one of them is doing a job the statement asked for.

## `seen` and `found` are both sets, for different reasons

`seen` is a set because the only question ever asked of it is "is this value in here",
and that is O(1) on a set and O(n) on a list. Swap it for a list and you are back to
quadratic time with extra steps.

`found` is a set because the answer must not contain duplicates. `[1, 1, 4, 4, 4]` with
target 5 hits the `found.add(...)` line **six** times — once for each `(1, 4)` index
pairing — and a set makes those six writes collapse into the one entry the statement
wants. This is the line that would otherwise need a "have I already got this pair?"
check.

## `partner = target - value`

The reframing that makes the whole thing linear. Instead of asking "which other element
pairs with this one" (which requires looking at other elements), it asks "what value
*would* pair with this one" — arithmetic, no search. Only then does it check whether that
value has been met.

## The order of `if partner in seen` and `seen.add(value)`

**This is the line to understand.** Checking before adding means `seen` holds only
elements strictly *before* the current one, so a match is always between two different
elements.

Trace `[3, 1, 4]` with target 6:

| value | partner | `seen` before the check | in `seen`? | `found` |
| --- | --- | --- | --- | --- |
| 3 | 3 | `{}` | no | `{}` |
| 1 | 5 | `{3}` | no | `{}` |
| 4 | 2 | `{3, 1}` | no | `{}` |

Result `[]`. The single `3` never pairs with itself, because at the moment it was checked
it had not yet been added.

Now trace `[3, 3, 1]` with the same target:

| value | partner | `seen` before the check | in `seen`? | `found` |
| --- | --- | --- | --- | --- |
| 3 | 3 | `{}` | no | `{}` |
| 3 | 3 | `{3}` | **yes** | `{(3, 3)}` |
| 1 | 5 | `{3}` | no | `{(3, 3)}` |

Result `[[3, 3]]`. Two elements, so they pair.

Swap the two lines and both traces return `[[3, 3]]` — the first one wrongly. You would
then need `if partner in seen and partner != value` to patch it, plus a separate branch
for the genuine twin case. Ordering the two statements correctly does that work for you.

## `(min(value, partner), max(value, partner))`

Two jobs in one expression. It satisfies "each pair sorted ascending", and — because the
tuple is normalised before it goes in — it is what lets the set dedupe properly. Store
`(value, partner)` unsorted and `{(1, 4), (4, 1)}` are two different entries, so the same
pair comes back twice in a different order depending on which element you met first.

A tuple rather than a list because lists are unhashable and cannot go in a set at all.

## `[list(pair) for pair in sorted(found)]`

The last line does the two remaining requirements.

`sorted()` on a set of tuples compares element by element, so `(10, 60)` sorts before
`(20, 50)` — first element, then second as the tie-break. Exactly the order the statement
specifies, for free.

`list(pair)` converts each tuple back, because the contract says `list[list[int]]`. This
matters more than it looks: the grader distinguishes types, and `[(1, 4)]` is not
`[[1, 4]]`. Returning tuples is the single most common way a correct algorithm here still
fails.

## Why `numbers` is never touched

Nothing in this solution writes to `numbers` — it only iterates. That satisfies "`numbers`
belongs to the caller" without any effort.

The two-pointer alternative does not get it for free. It needs the input sorted, and
`numbers.sort()` mutates the caller's list. The test that catches it calls the function
twice on the same list and checks the second answer, which is why an in-place sort looks
perfectly correct right up until it doesn't.

## The traps, and which case pins each one

| trap | case |
| --- | --- |
| a lone element pairing with itself | `an_element_cannot_pair_with_itself` |
| twins failing to pair | `a_repeated_value_can_pair_with_its_twin` |
| duplicate pairs in the output | `each_distinct_pair_appears_once` |
| pair or list not sorted | `basic_one_pair`, `many_pairs_sorted_by_first_then_second` |
| insertion order leaking through | `input_order_does_not_leak_into_output` |
| `None` instead of `[]` | `no_pair_is_empty_not_none` |
| sorting the caller's list in place | `the_input_list_is_not_modified` |
| quadratic scan | `large_input_rules_out_a_quadratic_scan` |
| zero needing two zeroes | `zero_target_needs_two_zeroes`, `two_zeroes_pair` |
