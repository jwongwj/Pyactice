# 3.9 Topological sort

**Cue: "must come before", in any wording** — prerequisites, build order, task
dependencies, install order.

The useful extra fact: the algorithm also *detects impossibility*. Dependencies with a
cycle have no valid order, and Kahn's algorithm reports that for free by finishing early.

## Kahn's algorithm

Count how many things each item is waiting for. Start with the items waiting for nothing.
Every time one is emitted, decrement its dependents and emit any that reach zero.

```python
counts = {item: 0 for item in items}          # seed EVERY item
for before, after in befores:
    graph[before].append(after)
    counts[after] += 1

ready = [item for item in items if counts[item] == 0]
while ready:
    item = ready.pop()
    out.append(item)
    for nxt in graph[item]:
        counts[nxt] -= 1
        if counts[nxt] == 0:
            ready.append(nxt)

if len(out) != len(items):
    return []        # something never reached zero: a cycle
```

Seeding every item at zero is load-bearing. Build the counts with a `defaultdict` and only
the items that are *depended on* get a key — and the items with no key are precisely the
ones the sort has to start from.

## The cycle check is free

`len(out) != len(items)` is the whole test. Anything still waiting when the ready list
empties is waiting on something inside a cycle. No separate detection pass, no colours, no
recursion stack.

That is the main reason to prefer Kahn's to the depth-first version in an interview: the
impossible case falls out of the algorithm instead of needing its own argument.

## Making the answer unique

Several orders are usually valid, which makes a test awkward. Pick the smallest available
item at each step and the answer becomes deterministic:

```python
import heapq
heapq.heapify(ready)
item = heapq.heappop(ready)
```

Worth doing whenever a question says "return the lexicographically smallest order", and
worth *asking about* when it does not.

## Levels instead of a sequence

Drain the whole ready set at once and you get items grouped by depth:

```python
while ready:
    out.append(sorted(ready))
    ready = [everything that reached zero because of this group]
```

The number of groups is the length of the longest dependency chain — which is exactly how
long a build takes with unlimited parallelism. Same code, a different question.

## Inferring the dependencies first

The hard version gives you no dependency list. In "alien dictionary" you are given words
already sorted in an unknown alphabet, and the order has to be *derived*:

```python
for first, second in zip(words, words[1:]):
    for a, b in zip(first, second):
        if a != b:
            befores.append((a, b))
            break            # only the FIRST difference tells you anything
```

Two traps:

- **Only the first differing character is evidence.** Everything after it is unconstrained.
- **A word followed by a strict prefix of itself is contradictory** in any alphabet —
  `["abc", "ab"]` cannot be sorted, and this failure has nothing to do with letter order.
  It is the case people miss, because it is not a cycle.

## Where to reach for which

| the question says | you want |
| --- | --- |
| valid order of dependencies | Kahn's |
| can this be scheduled at all | Kahn's, and compare the counts |
| how long with unlimited parallelism | Kahn's, one level at a time |
| the smallest valid order | Kahn's with a heap |
| shortest path in a DAG | topological order, then relax in that order |
| there are cycles and you want them | DFS with three states (unit 2.11) |
