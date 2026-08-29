# 1.7 Sorting

Read this first. One screen, then eight small functions.

This is the highest-value unit in Basic Python. Sorting with a tie-break is the most
common real requirement in interview problems, and sorting *twice* is the most common way
people get it wrong.

## `sorted` versus `.sort()`

```python
sorted(names)     # returns a new list, leaves the input alone
names.sort()      # returns None, mutates the caller's list
```

Default to `sorted`. If a function you wrote reorders the list it was handed, every caller
now has a bug you did not tell them about. One drill here calls your function twice on the
same list precisely to catch `.sort()`.

## Descending

```python
sorted(numbers, reverse=True)
```

One pass. `sorted(numbers)` then `.reverse()` is two, and reads as two decisions.

## The key function

`key` is applied to each element to decide its *ordering*. It never changes the elements:

```python
sorted(names, key=len)                 # by length
sorted(names, key=lambda n: n.split()[-1])   # by last word
sorted(words, key=str.casefold)        # ignoring case, original spelling returned
```

That last one is worth pausing on. `sorted(w.lower() for w in words)` returns
lower-cased words — you have changed the data. `key=str.casefold` changes only the
comparison.

## The whole point: one sort, one compound key

Two fields, opposite directions:

```python
sorted(rows, key=lambda r: (-r["score"], r["name"]))
```

Score **descending**, name **ascending**. Tuples compare element by element, so the second
element only matters when the first is equal — which is exactly what "tie-break" means.
Negating a number reverses just that component.

**`reverse=True` cannot do this.** It flips the entire comparison, so it would reverse the
names too.

And this does not work:

```python
rows.sort(key=lambda r: r["name"])      # first pass
rows.sort(key=lambda r: -r["score"])    # second pass
```

...except that it accidentally does, because the sort is stable. Which brings us to:

## Stability

Python's sort is **stable**: elements with equal keys keep their original relative order.

That means you *can* sort by successive keys, least significant first, and get the right
answer. It also means you don't need to, and shouldn't: one compound key is one pass, one
line, and obviously correct, whereas the multi-pass version is only correct if you get the
order of the passes backwards from how you'd say it out loud.

Where stability genuinely helps: when you want equal items to stay in input order, you get
that for free. Adding the index to the key to "make it deterministic" is noise — it already
is.

## Slicing the top few

```python
sorted(numbers, reverse=True)[:2]
```

A slice past the end of a list returns what there is. No length check needed.

(When the list is large and `n` is small, `heapq.nlargest(n, xs)` is O(n log k) rather
than O(n log n) — that is unit 2.7's business.)

## How this unit is graded

```
✓ alphabetical   correct
○ ranked         correct, but
                   You called `reverse`.
                   → reverse=True flips the whole comparison
```

`○` costs you no test case. The checkpoint, `standings`, has **three** tie-breaks —
points, then goal difference, then name — and wants one sort.
