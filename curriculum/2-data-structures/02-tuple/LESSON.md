# 2.2 Tuple

A tuple is not a read-only list. The difference that earns it a place in your toolkit is
that it is **hashable**, and that is what lets it be a dict key, a set member, or an
element you can dedupe.

## Immutable, and what that does not mean

```python
point = (1, 2)
point[0] = 9        # TypeError
```

Immutable means the *tuple* cannot be rebound to different elements. It says nothing about
the elements themselves:

```python
row = ("ada", [1, 2])
row[1].append(3)    # fine -- the list inside is still mutable
hash(row)           # TypeError: unhashable type: 'list'
```

That second line is the rule that matters: a tuple is hashable **only if everything in it
is**. A tuple of tuples can be a key; a tuple containing a list cannot.

## Returning several values

There is no special syntax. `return a, b` builds a tuple, and the caller unpacks it:

```python
def min_max(items):
    return min(items), max(items)

low, high = min_max([3, 1, 2])
```

This is why Python needs no out-parameters and no one-off result classes. Where a function
has nothing to return, return the pair `(None, None)` rather than a bare `None` — the
caller is already writing `low, high = ...`, and `None` would fail to unpack.

## The tuple as a dict key

This is the unit's real lesson. When something is identified by two things, the pair is
the key:

```python
visits = {}
for city, day in entries:
    visits[(city, day)] = visits.get((city, day), 0) + 1
```

The tempting alternative is to join them into a string, `f"{city}|{day}"`. It works right
up until a separator appears in the data — `("a|b", "mon")` and `("a", "b|mon")` both
become `"a|b|mon"` and silently merge. A tuple key has no separator to collide with.

The same applies to sets: `set()` of tuples deduplicates pairs, and `(1, 2)` and `(2, 1)`
are properly distinct.

## The compound sort key

One `sorted` call with a tuple key sorts on several fields at once, most significant
first:

```python
sorted(rows, key=lambda r: (r[1], -r[2]))   # dept ascending, pay descending
```

Two things to know:

- **Negating reverses one field.** `reverse=True` reverses *all* of them, which is almost
  never what a tie-break wants. Negation only works on numbers.
- **For a descending string, use two passes**, least significant key first, and rely on
  the sort being stable:

  ```python
  rows.sort(key=lambda r: r[0])                 # then break ties by name ascending
  rows.sort(key=lambda r: r[1], reverse=True)   # primary key last
  ```

Stability is also why you sometimes need *no* tie-break: if nothing distinguishes two rows
under the key, they keep their input order. Relying on that silently is a trap in one
direction — it means a missing tie-break can pass a test whose input happened to arrive in
the right order already.

## namedtuple

A plain tuple makes the reader remember what `[1]` was. A named one does not:

```python
from collections import namedtuple

Reading = namedtuple("Reading", "label value")
best = Reading("sensor-a", 91)
best.value          # 91
best[1]             # 91 -- still a tuple
```

The reason it is free to adopt: a namedtuple **is** a tuple. It unpacks, it compares equal
to the plain tuple with the same contents, and it is hashable on the same terms. Nothing
that consumed the tuple has to change.

For a mutable equivalent with the same readability, `dataclasses.dataclass` is the modern
answer — but it is not hashable by default, and not a tuple, so it will not compare equal
to one.

## Where to reach for which

| you want | use |
| --- | --- |
| a fixed-size record, possibly a key | tuple |
| the same, but readable at the call site | `namedtuple` |
| a growing, changing sequence | list |
| a record with methods and mutation | `dataclass` |
