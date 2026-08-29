# 3.18 Intervals

Nearly every interval question is *sort, then walk once*. The entire difficulty is deciding
**which end to sort by**, and it is not the same answer every time:

| the question | sort by |
| --- | --- |
| merge the overlapping ones | **start** |
| how many overlap at once | starts and ends **separately** |
| keep as many as possible | **end** |

Sorting by the wrong end gives a plausible answer that is wrong on inputs you will not
think to try.

## Decide what "touching" means, first

`[1, 2]` and `[2, 3]` share exactly one point. Do they overlap?

There is no universal answer — it depends on whether the numbers are *points* or
*durations*. A meeting ending at 2 and another starting at 2 do not conflict. Two ranges of
integers `1..2` and `2..3` both contain 2 and do.

Ask, or state your assumption. Then be consistent, because the comparison changes:

```python
if start <= current_end:    # touching counts as overlapping
if start <  current_end:    # touching does not
```

## Merging

```python
out = []
for start, end in sorted(intervals):
    if out and start <= out[-1][1]:
        out[-1] = (out[-1][0], max(out[-1][1], end))
    else:
        out.append((start, end))
```

Sorting by start is what makes one pass enough: any interval that overlaps the one you are
holding must start before it ends, and you will meet it next.

The `max` is load-bearing. An interval fully *contained* in the current one — `(1,9)` then
`(2,3)` — would otherwise shorten the answer to `(1,3)`. This is the case to test.

## Inserting into an already-merged list

Three phases, no sorting, one pass:

1. emit everything that ends **before** the new interval starts;
2. absorb everything that touches it, widening both bounds as you go;
3. emit the rest.

```python
while i < len(intervals) and intervals[i][1] < start:
    out.append(intervals[i]); i += 1
while i < len(intervals) and intervals[i][0] <= end:
    start = min(start, intervals[i][0])
    end   = max(end,   intervals[i][1])
    i += 1
out.append((start, end))
out.extend(intervals[i:])
```

Both `min` and `max` are needed: the new interval may extend past either end, or be
entirely swallowed by an existing one.

## Counting simultaneous overlaps

The trick is that **the ends do not have to stay attached to their starts**. Sort them into
two independent lists and walk both:

```python
starts = sorted(m[0] for m in meetings)
ends   = sorted(m[1] for m in meetings)
rooms = best = 0
e = 0
for s in starts:
    while e < len(ends) and ends[e] <= s:
        rooms -= 1          # a room freed at or before this start
        e += 1
    rooms += 1
    best = max(best, rooms)
```

Once you see that separating them is allowed, the whole problem collapses into a merge-like
sweep with no data structure at all. The alternative — a heap of end times — is equally
correct and hides the insight.

Note `<=` in the inner loop: that is the "touching frees the room" decision made explicit.

## The greedy: sort by END

"Remove the fewest intervals so none overlap" is the same as "keep the most". The greedy
rule is: **always keep the interval that ends soonest.**

```python
for start, end in sorted(intervals, key=lambda pair: pair[1]):
    if last_end is None or start >= last_end:
        kept += 1
        last_end = end
```

Why the end and not the start? Because the interval that finishes earliest leaves the most
room for everything after it. Sorting by start would keep `(1, 100)` and lose several short
intervals that could all have fitted inside it — `[(1,100), (2,3), (3,4)]` is the smallest
case that shows the difference: sorting by start removes 2, sorting by end removes 1.

This is a genuine greedy with an exchange argument behind it, which is why it lives near
unit 3.11.

## Gaps

The complement of "what is busy" is "what is free". Merge the busy intervals first — if you
do not, two overlapping busy blocks leave a phantom gap between them — then walk the merged
list, emitting whatever lies between the end of one and the start of the next.

Keep a `cursor` and always advance it with `max(cursor, end)`, or a fully contained busy
block drags it backwards.

## The edge cases that actually bite

- **Degenerate intervals** where start equals end. They are well-formed and behave
  differently from every other case.
- **Unsorted input**, when the code assumed sorted.
- **Containment**, where the second interval is entirely inside the first.
- **Touching**, in both directions — the new interval ending where an old one starts is a
  different code path from the reverse.

## Where to reach for which

| the question says | you want |
| --- | --- |
| combine what overlaps | sort by start, extend or emit |
| how many at the same time | starts and ends sorted separately |
| fit in as many as possible | sort by end, greedy |
| when am I free | merge the busy, then walk the gaps |
| does a new one conflict | binary search the sorted starts (3.1) |
