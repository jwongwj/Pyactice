# 2.4 Set

A set is a dict with only keys. That gets you O(1) membership and free deduplication, and
costs you order.

## Membership is the whole point

```python
if item in some_list:      # O(n) -- it walks the list
if item in some_set:       # O(1) -- it hashes and looks
```

This one substitution is the single most common way to turn a quadratic answer into a
linear one. Any time you find yourself testing containment inside a loop, the thing being
tested against should be a set:

```python
lookup = set(haystack)                 # built once, O(n)
found = [x for x in needles if x in lookup]
```

Building the set costs one pass. Doing `x in haystack` inside the comprehension costs a
pass *per needle*.

## Order is gone, and pretending otherwise is a bug

A set has no order. It is not sorted, it is not insertion-ordered, and the iteration order
you observe is an implementation detail you must not rely on. So when you dedupe, decide
which order you actually want:

```python
sorted(set(items))              # distinct, ascending -- you chose sorted order
list(dict.fromkeys(items))      # distinct, FIRST-SEEN order
```

`dict.fromkeys` is the idiom worth memorising. It builds a dict with those keys and `None`
values, and because dicts keep insertion order, the keys come back in the order they first
appeared. `sorted(set(...))` is a different answer, and substituting one for the other is a
real bug whenever the input was not already ascending.

## The algebra

```python
a | b       a.union(b)              in either
a & b       a.intersection(b)       in both
a - b       a.difference(b)         in a, not in b
a ^ b       a.symmetric_difference(b)   in exactly one
```

Two things to hold on to:

- **Difference is not symmetric.** `a - b` and `b - a` are different questions. Re-read
  which one was asked; this is where the mistakes are.
- **The method forms take several arguments, the operators take one.** So three
  collections need no more code than two:

  ```python
  set(a).intersection(b, c)          # in all three
  set(a) & set(b) & set(c)           # the same, more typing
  ```

  Doing this in two steps invites the classic error of intersecting the first two and
  forgetting the third — which returns items that are in *some* pair rather than in all
  three.

The method forms also accept any iterable, so `set(a).intersection(b, c)` does not require
`b` and `c` to be sets already.

## frozenset

A set is mutable, therefore unhashable, therefore not usable as a dict key or a member of
another set. `frozenset` is the immutable version, and it is hashable:

```python
groups = {}
for name, tags in rows:
    groups.setdefault(frozenset(tags), []).append(name)
```

That groups rows by their *exact set of tags*, regardless of the order the tags were listed
in, and collapsing duplicates on the way — `["x", "x"]` and `["x"]` land in the same group,
because a set has no repeats. The empty frozenset is a perfectly good key, so rows with no
tags group together too.

This is the natural key whenever the identity of something is "which things it has" rather
than "what order they were given in".

## Sets of what

Everything in a set must be hashable, on the same terms as a dict key: tuples yes, lists
no. A set of tuples is a common and useful thing; a set of lists is a `TypeError`.

```python
seen = set()
for pair in pairs:                 # pairs are tuples
    if pair not in seen:
        seen.add(pair)
```

## Where to reach for which

| you want | use |
| --- | --- |
| fast membership, order irrelevant | `set` |
| distinct items, ascending | `sorted(set(items))` |
| distinct items, first-seen order | `list(dict.fromkeys(items))` |
| distinct items *and* their counts | `Counter` (unit 2.3) |
| a set used as a key | `frozenset` |
