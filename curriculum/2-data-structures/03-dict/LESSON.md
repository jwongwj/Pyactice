# 2.3 Dict

Two things make dicts the most load-bearing structure in an interview: lookup is O(1), and
insertion order has been guaranteed since Python 3.7. Most slow answers are a list where a
dict belonged; most long answers are `if key in d:` where a default belonged.

## The four ways to handle a missing key

They are not interchangeable, and picking the wrong one is the most common source of noise
in otherwise correct code.

```python
d.get(key)                  # None if absent, no insertion
d.get(key, fallback)        # fallback if absent, no insertion
d.setdefault(key, [])       # inserts [] if absent, then RETURNS the list either way
defaultdict(list)           # builds the default on any missing access
```

`get` with a fallback replaces a two-branch `if`. The trap is writing `d.get(key) or
fallback` instead: that also replaces a stored `0`, `""` or `[]`, because those are falsy.
If the key is present, its value wins — even when that value is zero. Pass the default as
the second argument and the question never comes up.

`setdefault` is the one people misread. It returns the value at the key, installing the
default first if it was missing, so the whole grow-a-list idiom is one line:

```python
table.setdefault(key, []).append(value)
```

`defaultdict` moves that default into the dict itself:

```python
from collections import defaultdict

groups = defaultdict(list)
for group, member in rows:
    groups[group].append(member)     # no `in` test, no setdefault
```

Its one sharp edge: *reading* a missing key inserts it. `if groups["nope"]` leaves an empty
list behind, which will show up later in `len()` or an iteration. When that matters,
convert back with `dict(groups)` before returning, which also makes the return type say
what it means.

## Counter

Counting is solved. Do not write the loop:

```python
from collections import Counter

counts = Counter(items)          # {item: how many}
counts.most_common(3)            # the three commonest, as (item, count) pairs
counts["never seen"]             # 0, and does NOT insert
```

`Counter` is a `dict` subclass, so it compares equal to the plain dict you would have built
and can be returned wherever a dict is expected.

The important limitation is `most_common`'s tie-break: **equal counts come back in
insertion order**, not sorted. If the question says "ties broken alphabetically", you have
to sort yourself:

```python
ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
```

Counters also do arithmetic — `a + b`, `a - b`, `a & b` — which is occasionally exactly
what a question wants.

## Merging, and who wins

```python
out = {}
for table in tables:
    out.update(table)        # later tables overwrite earlier ones
```

`update` already overwrites, so a clash needs no branch. In 3.9+ `a | b` does the same for
two dicts, with `b` winning. Whichever you use, be sure which direction the question wants
— "the first one wins" needs `setdefault` in a loop instead, or the tables reversed.

## Inverting

Swapping keys and values is a one-liner only when the values are unique:

```python
{v: k for k, v in table.items()}     # silently loses keys that shared a value
```

Two keys with the same value means one of them vanishes, and nothing tells you. If
collisions are possible — and in an interview, assume they are unless told otherwise —
collect them:

```python
out = defaultdict(list)
for key, value in table.items():
    out[value].append(key)
```

Note that this changes the return *type*: every value is now a list, even the ones with a
single key. Being consistent about that is easier to reason about than a mix of scalars and
lists.

## Two passes beat one clever one

"The first character that appears exactly once" cannot be answered in a single pass — you
do not know whether a character repeats until you have seen the rest. So count first, then
walk the original in order:

```python
counts = Counter(text)
for character in text:
    if counts[character] == 1:
        return character
return None
```

Iterating `text` rather than `counts` is what makes the answer *first in the input*. It
happens that iterating the Counter would also work here, since dicts keep insertion order,
but relying on that couples your answer to a detail the question never mentioned.

The trap is `text.count(character)` inside the loop: correct, and quadratic, because each
`count` is another full pass.

## Prefix sums with a dict

The checkpoint is the pattern worth taking away. "How many contiguous slices sum to k" has
an O(n) answer built from a running total and a dict of how often each total has been seen:

```python
seen = {0: 1}          # the empty prefix
running = found = 0
for value in nums:
    running += value
    found += seen.get(running - k, 0)
    seen[running] = seen.get(running, 0) + 1
```

If two prefixes have totals differing by exactly `k`, the slice between them sums to `k`.
Three details, each of which is a bug if missed:

- **Seed `{0: 1}`.** Without it, a slice starting at index 0 is never counted.
- **Count, do not merely record.** The same running total can recur, and each earlier
  occurrence is a distinct slice. A `set` here would undercount.
- **Look up before inserting.** Otherwise a `k` of 0 matches the current prefix against
  itself.

A sliding window cannot do this job once negatives are allowed: the running total is no
longer monotonic, so shrinking the window from the left has no reliable effect.
