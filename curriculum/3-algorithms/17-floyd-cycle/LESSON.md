# 3.17 Floyd cycle detection

Unit 2.8 uses the tortoise and hare to answer *is there a cycle*. This is the rest of what
the technique gives you — and the reason it is worth knowing rather than reaching for a set.

## Phase one: the meeting

```python
slow = fast = start
while True:
    slow = step(slow)
    fast = step(step(fast))
    if slow == fast:
        break
```

**Move, then compare.** Comparing first reports a meeting immediately on every input,
because both pointers begin in the same place. That ordering is the single most common bug
here.

If there is a cycle, the fast pointer gains one position per step on the slow one and must
eventually land on it. If there is not, the fast pointer runs off the end — which is why the
linked-list version guards on both `fast` and `fast.next`.

## The meeting point is not the entrance

Worth stating plainly, because it is the intuition everyone starts with and it is wrong.
They meet *somewhere inside* the cycle, and where depends on how long the run-in is.

## Phase two: finding the entrance

Restart one pointer at the beginning, leave the other where they met, and move both **one
step at a time**. They meet at the entrance.

```python
finder = start
while finder != slow:
    finder = step(finder)
    slow = step(slow)
return finder
```

The algebra, briefly. Let the tail be `t` and the cycle length `c`, and say they meet `m`
steps into the cycle. The slow pointer has taken `t + m`; the fast has taken twice that, and
is at the same place, so `2(t + m) − (t + m) = t + m` is a whole number of laps. So `t + m`
is a multiple of `c` — which means walking `t` more steps from the meeting point lands
exactly on the entrance, and walking `t` steps from the start does too.

You do not need to reproduce that under pressure. You need to know the second phase exists
and what it does.

## The cycle's length

Once they have met, keep one still and walk the other until it comes back. That count is
the length. No extra memory, one lap.

## The disguised version

This is the point of the unit. **There need not be a linked list at all** — only a function
from a state to the next state.

"Find the duplicate in a list of n+1 values, each between 1 and n" is `i -> nums[i]`. Two
different positions map to the same place, and that is exactly what a cycle entrance is —
so the value at the entrance is the duplicate:

```python
slow = nums[slow]; fast = nums[nums[fast]]     # identical loop, different `step`
```

O(1) memory, and it does not modify the input. Counting works too and costs O(n) memory;
sorting works and destroys the input. When a question forbids both, this is what it is
asking for.

"Happy numbers" is the same shape again — the step is "sum the squares of the digits", and
the question is whether the chain reaches 1 or loops.

## Recognising it

Look for: a deterministic step from one state to the next, a finite state space, and a
question about repetition, duplication or termination. If a set of seen states would work
but is forbidden or too large, this is the alternative.

## Where to reach for which

| the question says | you want |
| --- | --- |
| does this loop | slow and fast pointers |
| where does the loop start | phase two |
| how long is the loop | one lap after the meeting |
| find the duplicate, O(1) space, do not modify | Floyd on `i -> nums[i]` |
| the middle of a list you cannot measure | two speeds, no cycle needed |
| a cycle in a general graph | three-state DFS (2.11) — this needs one next-state |
