# Approach

## The question behind the question

A stack is trivial — a Python list is one. The only thing being asked is: **how do you keep
an aggregate that has to survive a pop?**

A single `self.minimum` works until the minimum is popped, and then there is no way to
recover the previous one without looking at everything. That is the trap, and it is worth
reaching before writing code: push 5, push 3, pop. What is the minimum now, and where would
you have stored it?

## The idea

Store the minimum **as it stood at each depth**, alongside the value:

```python
self.values = []
self.minima = []          # minima[i] is the smallest among values[0..i]
```

On push, the new minimum is `min(value, current minimum)`. On pop, discard both — and the
top of `minima` is automatically the minimum for the shallower stack, because that is what
it was when that value was pushed.

Every operation stays O(1), at the cost of one extra integer per element.

## The trap inside the trap

It is tempting to push onto `minima` only when the value is **strictly** smaller, to save
space. That breaks on duplicates:

```
push 2   -> minima [2]
push 2   -> not strictly smaller, so nothing pushed
pop      -> pops a value AND a minimum
get_min  -> the stack still holds a 2, and the minimum stack is empty
```

Either push unconditionally, or use `<=`, or store `(minimum, count)` pairs. The
unconditional version is the one to write under time pressure.

## Alternative worth mentioning

A single stack of `(value, minimum_at_this_depth)` tuples is the same idea in one
structure, and is arguably tidier. Storing the *difference* from the current minimum is a
known trick that gets it into O(1) extra space overall — worth naming, not worth writing.

## Order of work

1. `push`, `pop`, `top`, `size` with a plain list. Get LIFO right first.
2. Add the second stack and `get_min`.
3. Then the empty cases — all four accessors on an empty stack.
4. Then the duplicate-minimum case, deliberately, because it is the one that bites.
