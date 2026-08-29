# 3.11 Greedy

**Cue: a locally safe choice, provably.**

Greedy is the easiest family to write and the hardest to justify. The algorithm is always
"take the best-looking option now and never reconsider". The work is showing that doing so
cannot cost you the optimum.

If you cannot make that argument, you have guessed. And where the argument fails, the same
problem needs dynamic programming — coin change with arbitrary denominations is the
standard example, and taking the largest coin first is the standard wrong answer (unit
3.10).

## The exchange argument

The usual proof shape: take any optimal solution, and show you can swap its first choice
for the greedy one without making it worse. Repeat, and the greedy solution is optimal.

For interval scheduling: the meeting that **ends soonest** leaves the most room for
everything after it. Any optimal schedule's first meeting can be replaced by that one — it
finishes no later, so nothing else has to move. That is the whole proof, and it is why the
sort key is the *end* and not the start.

Sorting by start keeps `(1, 100)` and loses several short meetings that would all have
fitted inside it.

## Carrying a running maximum

"Can I reach the end, where each value is how far I may jump?" needs no search:

```python
furthest = 0
for index, reach in enumerate(jumps):
    if index > furthest:
        return False          # this position was never reachable
    furthest = max(furthest, index + reach)
```

The only thing that matters at each step is how far you could get in total. Trying every
jump is exponential; this is one pass.

## Ranges, for the fewest jumps

The minimum-jumps version is subtler and worth knowing, because it is a breadth-first
search that needs no queue. Everything reachable in n jumps is a **contiguous range**, so
two integers track it:

```python
if index == range_end:        # ran out of the current range
    taken += 1
    range_end = furthest      # the next range ends at the furthest we had seen
```

Note the loop stops **before** the last index — arriving there needs no further jump, and
counting one is the off-by-one this problem is famous for.

## Proving a whole prefix can be skipped

The gas station route is the neatest greedy here. If the tank dies somewhere between i and
j, then **no start between them works either** — each of those starts has strictly less
fuel in hand at every later point. So the search can jump straight past all of them:

```python
if tank < 0:
    start = index + 1        # restart AFTER the failure
    tank = 0
```

And a separate running total answers whether *any* start works: if total gas is less than
total cost, none does. Two facts, one pass, no nesting.

The tank ending at exactly zero is allowed — it may not go *below*. That boundary is the
one to test.

## Sweeping two sorted sequences

For "how many at once", separate the starts from the ends and walk both. The ends do not
have to stay attached to their starts (unit 3.18):

```python
for start in sorted(starts):
    while ends[e] <= start:
        in_use -= 1; e += 1
    in_use += 1
    best = max(best, in_use)
```

Whether `<=` or `<` is the "does touching count" decision, made explicit.

## When greedy is wrong

Signs to be suspicious of:

- The choice affects what is available later in a way you cannot bound.
- Denominations, weights or values are arbitrary rather than structured.
- The question asks "how many ways" rather than "the best".

The honest interview move is to state the greedy rule, say why you think it is safe, and
say what you would fall back to if it is not.

## Where to reach for which

| the question says | you want |
| --- | --- |
| fit in as many as possible | sort by end, take what fits |
| can I reach the end | a running furthest-reachable |
| fewest steps, ranges | two integers, jump when the range runs out |
| where to start a circular route | one pass, restart after the failure |
| how many at once | sort starts and ends separately |
| coins, arbitrary denominations | DP (3.10) — greedy is wrong |
