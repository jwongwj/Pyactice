# 1.6 Truthiness, None and conditionals

Read this first. One screen, then ten small functions.

## The one bug this unit exists for

```python
name = name or "anonymous"
```

This reads as *"use the default when the name is missing."* It means *"use the default
when the name is **falsy**."* Those are not the same thing, and the difference is a
category of bug that is very hard to find later.

Falsy values in Python: `None`, `False`, `0`, `0.0`, `""`, `[]`, `{}`, `set()`.

So `configured or 8080` silently throws away a configured port of `0`. `name or
"anonymous"` renames a user whose name is legitimately `""`. `count or 10` replaces a
real count of zero. The data was there; the code decided it wasn't.

**When you mean "missing", say `is None`:**

```python
port = 8080 if configured is None else configured
```

Three drills in this unit have a case with a real `0` or `""` in it, precisely to fail
the `or` version.

## When truthiness *is* the right test

For "does this collection have anything in it", truthiness is exactly right:

```python
if items:          # good
if len(items) > 0: # noise
```

An empty collection is falsy, and that is what you meant. Note that it is about the
container, not the contents: `[0]` is a list with one thing in it, so it is truthy.

## Chained comparisons

```python
low <= value <= high
```

One expression, each operand evaluated once. `low <= value and value <= high` says the
same thing with `value` written twice.

## Conditional expressions

```python
"high" if score >= 80 else "mid" if score >= 50 else "low"
```

A ternary chain is an expression, so it can be returned directly. Past two or three
branches, a real `if` statement or a lookup table is clearer — this unit uses three to
show the shape, not to recommend twelve.

## `any` and `all`

```python
all(s >= 50 for s in scores)
any(s < 50 for s in scores)
```

Both short-circuit — `any` stops at the first true, `all` at the first false — so they are
not just shorter than the loop, they do less work.

Their empty-input answers surprise people and are worth memorising:

```python
all([])   # True    "every element passed" — there were none to fail
any([])   # False   "some element passed"  — there were none to pass
```

## Guarding, not catching

```python
0 if value is None else len(value)
```

A `try/except TypeError` around `len` would also work and is worse: it is slower on the
failing path, and it catches *other* things that raise `TypeError` too, hiding a real bug
behind a plausible-looking default.

## How this unit is graded

```
✓ has_items      correct
○ port           correct, but
                   You used `or`.
                   → 8080 if configured is None else configured
```

`○` costs you no test case. The checkpoint, `validate`, has **no constraints** — and its
cases include both an empty name that must be *accepted* and an age of `0` that must be
*rejected*, which is the whole unit in one function.
