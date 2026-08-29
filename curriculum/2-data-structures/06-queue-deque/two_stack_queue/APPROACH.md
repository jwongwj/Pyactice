# Approach

## Why two stacks

A stack reverses order. Two of them reverse it twice, which is the original order back.

Keep an **input** stack that everything is pushed onto, and an **output** stack that
everything is popped from. Values move from input to output exactly once, and arrive
reversed — which for a stack means the oldest value is now on top.

```python
self.incoming = []
self.outgoing = []
```

## The one rule

**Transfer only when the output stack is empty.**

```python
def _shift(self):
    if not self.outgoing:
        while self.incoming:
            self.outgoing.append(self.incoming.pop())
```

That condition is the whole design. Transferring whenever something is enqueued, or on
every dequeue, mixes values that arrived at different times and scrambles the order —
a value added *after* a transfer began would come out too early.

Both `dequeue` and `peek` need the front, so both call `_shift` first.

## The amortised argument

One dequeue may move n values and cost O(n). But each value is moved from input to output
**at most once in its life**, so across n operations the total work is O(n) — an average of
O(1) each.

That is a different claim from "every operation is O(1)", and being able to state the
difference is the point of the exercise. Say it out loud: *worst case O(n), amortised
O(1)*.

## Order of work

1. `enqueue` and `size` — trivial.
2. `_shift`, and `dequeue` on top of it.
3. `peek`, which is `dequeue` without the pop, and needs the same `_shift`.
4. Then the interleaving cases, which are where the transfer condition is tested.
