# 3.10 Dynamic programming

**Cue: overlapping subproblems** — a recursion that would compute the same thing many
times. DP is that recursion with the answers written down.

## Two questions, in this order

1. **What is the state?** The smallest description of a subproblem. Usually an index, or an
   index and a remaining budget.
2. **What is the transition?** How one state's answer is built from earlier ones.

Everything else — table or memo, forwards or backwards, one row or two — is optimisation
after the recurrence is right. Do not start with the table.

## Start from the recursion

Write the obvious recursive answer first, then notice it recomputes:

```python
def ways(n):
    if n < 0: return 0
    if n == 0: return 1
    return ways(n - 1) + ways(n - 2)
```

Then either memoise it (`@lru_cache`, top-down) or turn it inside out into a loop
(bottom-up). Both are DP; top-down is usually quicker to get right under time pressure and
bottom-up is usually faster and easier to reduce in space.

## Rolling the table away

When each answer depends only on the last one or two, the table is two variables:

```python
a, b = 1, 1
for _ in range(steps):
    a, b = b, a + b
return a
```

The base case is where the off-by-ones live. "Zero steps" has *one* way — do nothing — not
zero ways, and seeding that wrong shifts every later answer by one place. A single-element
input is the cheapest way to catch it.

## Take it or skip it

The smallest interesting DP:

```python
take, skip = 0, 0
for value in values:
    take, skip = skip + value, max(take, skip)
return max(take, skip)
```

Two states per position — the best ending in a take, and the best ending in a skip — and
the transition falls straight out of the rule "no two adjacent".

## Where greedy fails, and why this matters

Coin change is the standard demonstration. With coins of 1, 3 and 4 making 6, taking the
largest first gives 4+1+1 — three coins — and the answer is 3+3. There is no local rule
that gets it right, so every amount has to be built up:

```python
best[value] = 1 + min(best[value - coin] for usable coins)
```

Being able to *say* why the greedy fails is worth as much as the code. Unit 3.11 has the
problems where a greedy choice is provably safe; this is where it is not.

## Subarray is not subsequence

The word decides the algorithm:

- **Subarray / substring** — contiguous. Often a running answer works: Kadane (3.14), a
  sliding window (3.3).
- **Subsequence** — items in order but with gaps. A running answer cannot work, because a
  skipped item may still matter later. The state has to look back:

```python
ending[i] = 1 + max(ending[j] for j < i where nums[j] < nums[i])
```

That is O(n²) and fine for an interview. The O(n log n) version — patience sorting with
`bisect` — is worth mentioning as an improvement even if you write the simpler one.

## Two-dimensional state

When the state is two positions, the table is a grid. Edit distance is the canonical one:

```python
if source[i - 1] == target[j - 1]:
    table[i][j] = table[i - 1][j - 1]              # free
else:
    table[i][j] = 1 + min(table[i - 1][j],         # delete
                          table[i][j - 1],         # insert
                          table[i - 1][j - 1])     # substitute
```

The **first row and column are the base cases**, and they are not zero: turning `""` into a
string of length j costs j insertions. Filling them in is half the work, and getting them
wrong is the usual failure.

Only the previous row is ever read, so the space can be reduced to two rows. Do that after
it works, not before.

## Where to reach for which

| the question says | you want |
| --- | --- |
| how many ways | DP, counting |
| the best total, with a constraint | DP, take-it-or-skip-it |
| fewest / most, and greedy is unsafe | DP over every value |
| contiguous | Kadane or a window, usually |
| subsequence | DP looking back |
| two strings or two sequences | a 2-D table |
| list every solution | backtracking (3.6), not DP |
