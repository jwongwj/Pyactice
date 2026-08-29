# 3.15 Monotonic stack

Unit 2.5 introduces this through "next greater element" and "daily temperatures", which are
the same loop twice. This unit is what the pattern is actually *for*: the questions where
it is not obvious that next-greater is even involved.

## The invariant, once

The stack holds **indices whose answer is not yet known**, and their values are monotonic.
When a value arrives that breaks the monotonicity, everything it breaks has just found its
answer — and the arrival is that answer, or the boundary of it.

Each index is pushed once and popped at most once, so the whole thing is O(n) despite the
inner `while`.

## Looking left is easier than looking right

Two directions, and they feel different to write:

```python
# previous smaller: answered on the way IN
while stack and stack[-1] >= value:
    stack.pop()
answer.append(stack[-1] if stack else -1)
stack.append(value)

# next smaller: answered on the way OUT
while stack and nums[stack[-1]] > value:
    answer[stack.pop()] = index
stack.append(index)
```

Looking **left**, the answer is whatever survives the popping — read it immediately.
Looking **right**, you write into the slots of everything you pop. Both are the same
invariant; only the moment of answering differs.

## Hold indices, not values

Almost every real use needs the position: a width, a distance, a slice bound. Holding
indices costs nothing (`nums[stack[-1]]` reads the value) and holding values throws away
information you will want back.

Distances are index differences, which is all "how many days until it is warmer" is.

## Strict or not is a real decision

`>` versus `>=` in the popping condition decides what equal values do. It changes answers,
so read the question:

- "strictly greater" — equal values do not answer each other, and a run of equals keeps
  the *earliest* index.
- "greater or equal" — equal values do answer each other, and the run collapses.

Stock span is the odd one here: it counts days "less than or equal", so it pops on `<=`
where every other drill in this unit pops on a strict comparison.

## Basins: the water problem

The water above a bar is limited by the tallest bar on each **side**, minus the bar itself.
Computing both sides by scanning is O(n²). A decreasing stack finds each basin as it
closes:

```python
while stack and heights[stack[-1]] < height:
    bottom = stack.pop()
    if not stack:
        break                      # no left wall, nothing is held
    width = index - stack[-1] - 1
    depth = min(heights[stack[-1]], height) - heights[bottom]
    total += width * depth
```

Three things: the **shorter** wall sets the level; the width excludes both walls; and with
nothing left on the stack there is no left wall and nothing is trapped.

Two pointers solve the same problem in O(1) space, and are the better answer if you can see
it. Both are worth having.

## The sentinel

Anything still on the stack at the end never met a breaking value. Rather than a second
flush loop, append a value nothing can survive:

```python
for index, height in enumerate(list(heights) + [0]):
```

Nothing can be shorter than 0, so every remaining bar is popped and measured by the normal
path. Sentinels like this are worth knowing generally — they remove the special case
rather than handling it.

## Widest window per bar

The checkpoint uses the pattern twice: for each bar, find the previous smaller and the next
smaller, and the gap between them is the widest window in which that bar is the minimum.
Fill in the best answer for that width, then propagate downwards — a window of size k is at
least as good as one of size k+1.

That "compute a per-element span, then aggregate" shape is what the monotonic stack is
really for.

## Where to reach for which

| the question says | you want |
| --- | --- |
| next greater / smaller | monotonic stack |
| how long until… | monotonic stack, answering distances |
| largest rectangle under a histogram | monotonic stack of increasing heights |
| how much water is trapped | monotonic stack, or two pointers |
| the span of days up to today | monotonic stack (previous greater) |
| max/min of every fixed window | monotonic **deque** (2.6) — it expires from the front too |
