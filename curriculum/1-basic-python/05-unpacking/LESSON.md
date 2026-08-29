# 1.5 Unpacking and assignment

Read this first. One screen, then nine small functions.

## The idea

Unpacking replaces index arithmetic with names. `pair[0]` and `pair[1]` tell you nothing;
`first, last = pair` tells you everything. Every drill here is a place where indexing works
and naming reads better — and where the named version has fewer places to be off by one.

## Swapping

```python
a, b = b, a
```

The right-hand side is built as a tuple first, so no temporary variable is needed and no
order of operations to get wrong.

## Unpacking in a loop header

```python
for first, last in people:
    ...

[f"{first} {last}" for first, last in people]
```

The header is where the names belong. Reaching for `person[0]` inside the body means the
reader has to remember what position 0 was.

## Star unpacking

```python
first, *rest = items         # rest is ALWAYS a list, even when empty
*init, last = items          # everything up to the last, and the last
first, *middle, last = items # both ends named, everything else collected
```

`*rest` is what you want instead of `items[0]` and `items[1:]`, because it cannot go out
of range in a way that silently returns something wrong — it raises if there is nothing to
unpack, so you guard the empty case deliberately.

Note that `*rest` gives a **list**, even when the original was a tuple, and even when it
ends up empty.

## Ignoring a part

```python
for x, y, _ in points:
```

`_` is a convention, not a keyword — it is an ordinary name. What it buys you is a reader
who can see at a glance that the third value is deliberately unused, rather than wondering
whether you forgot it.

## Slice bounds count from the end, and do not raise

```python
items[-2:]      # last two, or fewer, or none — never an IndexError
items[1:-1]     # everything but the ends
```

This is why a slice is often better than computed indices: `items[len(items)-2:]` is the
same thing with two more chances to be wrong, and it does raise on an empty list.

## Transposing with `zip(*rows)`

```python
rows = [("a", 1), ("b", 2)]
names, values = zip(*rows)      # ("a", "b"), (1, 2)
```

The `*` unpacks the rows into separate arguments, so `zip` walks them in parallel and
effectively transposes. Two things to know: it yields **tuples**, so convert if you need
lists; and `zip(*[])` yields nothing at all, so an empty input needs its own answer rather
than crashing on an unpack.

## Building a dict from pairs

```python
dict([("a", 1), ("b", 2)])
```

No comprehension needed. As with any dict, a repeated key keeps the last value.

## How this unit is graded

```
✓ swapped        correct
○ head_tail      correct, but
                   You used `subscript`.
                   → first, *rest = items
```

`○` costs you no test case. The checkpoint, `regroup`, has **no constraints**.
