# 2.5 Stack

A Python list already is a stack. `append` and `pop` are both O(1) at the end, and that is
all a stack is. So there is nothing to build here — the skill is *recognising* a problem
that wants one.

```python
stack = []
stack.append(x)      # push
stack[-1]            # peek -- guard for empty first
stack.pop()          # pop -- raises IndexError when empty
```

The recurring bug is popping without checking. `if not stack: return False` before every
`pop()` or `stack[-1]`, or the input that has a closer with nothing open crashes instead of
answering.

## Shape 1: things that must close in order

Brackets, tags, quotes. Push each opener; on a closer, the top of the stack must be its
partner:

```python
PAIRS = {")": "(", "]": "[", "}": "{"}

for ch in text:
    if ch in "([{":
        stack.append(ch)
    elif ch in PAIRS:
        if not stack or stack[-1] != PAIRS[ch]:
            return False
        stack.pop()
return not stack
```

Two things this gets right that a counter cannot. `"([)]"` has the right *number* of every
bracket and is still wrong — only a stack knows what is currently open. And a leftover
opener means `stack` is non-empty at the end, which is why the return is `not stack` rather
than `True`.

## Shape 2: an expression with no parentheses

Reverse Polish — `["2", "3", "+", "4", "*"]` is `(2 + 3) * 4`. Push values; on an operator,
pop two and push the result:

```python
right = stack.pop()
left = stack.pop()          # the FIRST pop is the RIGHT operand
```

Getting that backwards is the classic error, and `+` and `*` will not reveal it — only `-`
and `/` will.

The other trap is division. Most versions of this question want truncation **towards
zero**, and Python's `//` floors towards negative infinity: `-7 // 2` is `-4`, but
`int(-7 / 2)` is `-3`. Read which one is wanted.

To tell a number from an operator, test membership in the operator set rather than calling
`isdigit()` — `"-3"` is a perfectly good number and `isdigit()` says no.

## Shape 3: undo

The history *is* the stack. Append an action; on "undo", pop:

```python
if action == "undo":
    if history:
        history.pop()
else:
    history.append(action)
```

If you find yourself reversing at the end, you built the wrong thing — a stack read front
to back is already the surviving history in order.

## Shape 4: the monotonic stack

This is the one worth real practice, because it turns a quadratic answer into a linear one
and shows up under several different names.

"For each element, the next one to its right that is bigger." The obvious answer scans
right from every position: O(n²). Instead, keep a stack of **indices whose answer is not
yet known**, and keep it decreasing:

```python
answer = [-1] * len(nums)
waiting = []
for index, value in enumerate(nums):
    while waiting and nums[waiting[-1]] < value:
        answer[waiting.pop()] = value      # `value` answers everything it beats
    waiting.append(index)
```

Each index is pushed once and popped at most once, so it is O(n) despite the inner loop.
The invariant is that values in the stack are non-increasing from bottom to top; anything
smaller than the arrival has just found its answer.

Note that the stack holds **indices**, not values. You almost always need the position —
to write into the right slot, or to compute a distance.

Which is the same problem again: "how many days until it is warmer" is this exact loop with
`index - popped` instead of `value`. Recognising that two questions are one algorithm is
most of what this subtopic teaches.

Related cues, all the same machinery:

| the question says | you want |
| --- | --- |
| next greater / next smaller | monotonic stack |
| how long until … | monotonic stack, answering in distances |
| largest rectangle under a histogram | monotonic stack of increasing heights |
| how much water is trapped | monotonic stack, or two pointers |

## The histogram, and the sentinel

The checkpoint is the hardest of these. For each bar, the widest rectangle *at that height*
runs from the first shorter bar on its left to the first shorter bar on its right — two
monotonic-stack questions at once. Keep the stack increasing, and when a shorter bar
arrives, everything taller has just found its right edge:

```python
for index, height in enumerate(list(heights) + [0]):    # sentinel
    while stack and heights[stack[-1]] >= height:
        top = stack.pop()
        left = stack[-1] + 1 if stack else 0
        best = max(best, heights[top] * (index - left))
    stack.append(index)
```

The appended `0` is the trick that avoids a second flush loop after the main one: nothing
can be taller than it, so every remaining bar is popped and measured. Sentinels like this
are worth knowing generally — they remove the special case rather than handling it.
