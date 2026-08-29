# 2.1 List

A list is a contiguous array of pointers. Everything surprising about its performance
follows from that one fact, so it is worth holding on to rather than memorising a table.

## Which end is cheap

Adding or removing at the **end** is O(1). Anywhere else is O(n), because every element
after the change has to shift along.

| operation | cost | why |
| --- | --- | --- |
| `items.append(x)` | O(1) | writes past the end, into space already reserved |
| `items.pop()` | O(1) | shortens by one, nothing moves |
| `items.insert(0, x)` | O(n) | every element shifts right |
| `items.pop(0)` | O(n) | every element shifts left |
| `items[i]` | O(1) | one multiply and an offset |
| `x in items` | O(n) | it has to look |

`pop(0)` in a loop is the classic accident: it looks like O(n) work and is O(n²). When you
want a queue, reach for `collections.deque`, which is O(1) at both ends. That is unit 2.6.

## Growing is amortised, not free

`append` is *amortised* O(1), not O(1). When the reserved space runs out, CPython
allocates a larger block and copies everything across. Because the new block is
proportionally bigger rather than one slot bigger, the copies get rarer as the list grows,
and the average cost per append settles to a constant. Any one append can still be O(n).

## The mutating operations

`insert`, `remove`, `del` and `pop` change the list **in place** and return either nothing
or the removed item — not the list. This is the single most common slip:

```python
items = [3, 1, 2]
items = items.sort()      # items is now None
items.sort()              # correct: sorts in place
items = sorted(items)     # correct: leaves the original alone
```

`insert` is forgiving about its index: `insert(len(items), x)` appends, and so does
`insert(9999, x)`. `del items[i]` and `items.pop(i)` are not — an index at or past the end
raises `IndexError`. Guard with `0 <= index < len(items)`, and note that the upper bound
is strict: `len(items)` is one past the last valid position.

`remove(x)` deletes the **first** occurrence and raises `ValueError` when there is none.
A comprehension is not a substitute — it removes *every* occurrence:

```python
[i for i in items if i != x]   # removes all of them
items.remove(x)                # removes the first one
```

## Reversing

Three ways, and they are not interchangeable:

```python
items[::-1]          # a new list, original untouched
list(reversed(items))# a new list, via an iterator
items.reverse()      # in place, returns None
```

Under the hood the in-place version is a two-pointer swap: walk one index from the front
and one from the back, exchange them, and stop when they meet.

```python
i, j = 0, len(items) - 1
while i < j:
    items[i], items[j] = items[j], items[i]
    i += 1
    j -= 1
```

Whether the loop guard is `i < j` or `i <= j` makes no difference to the result — when
`i == j` the swap is with itself — but `i < j` says what you mean.

## Deduping while keeping order

A set loses order; sorting to group duplicates loses it too. One pass with a `seen` set
keeps it:

```python
seen, out = set(), []
for item in items:
    if item not in seen:
        seen.add(item)
        out.append(item)
```

The trap is `if item not in out` instead — correct, and quadratic, because searching a
list is O(n). The same trap wears other clothes: `items.count(x)` or `items.index(x)`
inside a loop is a second pass per item.

For hashable items with no other work to do, `list(dict.fromkeys(items))` does the whole
thing, because dicts have preserved insertion order since 3.7.

## Rotating

Rotating right by `k` is two slices swapped:

```python
k %= len(items)               # k may be larger than the list
items[-k:] + items[:-k]
```

The modulo is not optional — `k` larger than the length would otherwise slice past the
end and silently give the wrong answer. Two details:

- An empty list has length 0, and `k % 0` raises `ZeroDivisionError`. Guard it first.
- `k == 0` works out correctly, which surprises people: `-0 == 0`, so `items[-0:]` is the
  whole list and `items[:-0]` is empty, and the two concatenate back to the original.

## Slices, and the stride

`items[start:stop:step]` — `stop` is exclusive, negatives count from the end, and every
bound is clamped rather than raising. `items[-2:]` on a one-item list gives that one item,
no error. The third argument is how you take every chunk boundary at once:

```python
[items[i:i + size] for i in range(0, len(items), size)]
```

## Merging two sorted lists

`sorted(left + right)` is correct and throws away what you were told: both inputs are
already ordered. Walking them with two indices is linear, and is the merge step of merge
sort (unit 3.12):

```python
i = j = 0
out = []
while i < len(left) and j < len(right):
    if left[i] <= right[j]:
        out.append(left[i]); i += 1
    else:
        out.append(right[j]); j += 1
out.extend(left[i:])          # whichever side is left over
out.extend(right[j:])
```

Forgetting the two `extend` calls at the end is the usual bug: the loop stops as soon as
*either* side is exhausted, and the remainder of the other one still has to go somewhere.

## Sorting by more than one thing

One key with a tuple, not two passes:

```python
sorted(rows, key=lambda row: (-row[1], row[0]))
```

Descending score, then ascending name. Negating the number is how you reverse *one*
component while leaving the others ascending — `reverse=True` would flip the name too.
That only works for numbers; for a descending string you need two passes, sorting by the
less significant key first, because Python's sort is stable.
