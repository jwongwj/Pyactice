# 3.6 Backtracking

**Cue: "every combination", "all possible", "is there an arrangement".**

Every one of these is four lines:

```
choose a candidate
if it is still consistent:
    record it, recurse, then UNDO the record
move on to the next candidate
```

## The undo

That is what makes it backtracking rather than brute force, and it is where the bugs are:

```python
picked.append(value)
walk(index + 1)
picked.pop()            # without this, one branch contaminates the next
```

A missing undo leaves earlier choices marked as taken, so later branches see a state that
is not theirs — usually producing *fewer* answers than expected, which is a confusing
symptom to debug.

The mirror mistake is copying the partial answer at every step instead of undoing it. That
is correct and turns an O(depth) space algorithm into an exponential one.

When you record a complete answer, though, you **must** copy:

```python
out.append(list(picked))    # a snapshot; `picked` keeps changing
```

## The two shapes

**Take it or leave it** — subsets, partitions, knapsack:

```python
walk(index + 1)                    # leave it
picked.append(items[index]); walk(index + 1); picked.pop()   # take it
```

**Used or unused** — permutations, n-queens, anything where every item is placed
somewhere:

```python
for index, value in enumerate(items):
    if index in used: continue
    used.add(index); order.append(value)
    walk()
    order.pop(); used.discard(index)
```

Recognising which shape a question is saves the whole design step.

## Repeats and duplicates

Two different questions that look alike:

- **A candidate may be reused.** Recurse at the *same* index rather than the next one.
  That is what allows `[2,2,2]` while never producing `[2,3]` and `[3,2]` as two answers,
  because the index never goes backwards.
- **The input contains duplicates.** Sort first, then skip a candidate equal to the one
  before it at the same depth — otherwise the same answer appears several times.

## Pruning

The second skill, and the one that separates a working answer from a fast one: reject a
branch before it is finished.

```python
if remaining < 0:
    return
```

Cheap impossibility tests are worth looking for. "Can these numbers be split into two equal
halves?" — if the total is **odd**, no split exists and the entire search can be skipped.
Noticing that is worth more than optimising the search itself.

n-queens is the standard demonstration: without pruning it enumerates every arrangement of
queens; with three sets — used columns, used rising diagonals, used falling diagonals — the
tree collapses to something a laptop finishes instantly.

```python
if column in columns or row - column in rising or row + column in falling:
    continue
```

`row - column` is constant along one diagonal and `row + column` along the other, which is
why those two expressions are the whole diagonal test.

## When it is really DP

If the same subproblem recurs with the same state, memoise it and it becomes dynamic
programming (unit 3.10). Backtracking is for when you need every answer, or when the states
do not overlap. "Count the ways" usually wants DP; "list the ways" wants this.

## Where to reach for which

| the question says | you want |
| --- | --- |
| every subset | take-it-or-leave-it |
| every ordering | used/unused |
| every combination summing to k | reuse the same index, prune on the remainder |
| is there any valid arrangement | backtracking with early exit |
| how MANY ways | DP (3.10), usually |
| the best one, not all of them | DP or greedy, usually |
