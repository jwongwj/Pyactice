# 3.8 A\*

**Cue: shortest path, and you have a usable estimate of how far is left.**

Dijkstra expands whatever is cheapest so far, which spreads outwards in every direction
equally. A\* adds an estimate of the *remaining* distance and expands whatever looks best
overall — so the search leans towards the goal instead of filling the map.

```python
heapq.heappush(heap, (steps + heuristic(cell, goal), steps, cell))
```

That is the entire difference from unit 3.7. Everything else is identical.

## The heuristic decides everything

- **Admissible** means it never OVERestimates. An admissible heuristic keeps A\* optimal.
- **Consistent** is stronger: the estimate never drops by more than the step costs. A
  consistent heuristic also lets you settle each node once, exactly as in Dijkstra.
- **A heuristic of zero** makes A\* into Dijkstra. Always admissible, never guided.
- **An overestimating heuristic** makes it fast and *wrong*.

Manhattan distance is admissible on a four-way grid, because you cannot reach a cell in
fewer than `|Δrow| + |Δcol|` moves. It stops being admissible the moment diagonal moves are
allowed — then it overestimates, and you want Chebyshev distance instead.

Use Manhattan for four-way movement, Chebyshev for eight-way, straight-line for continuous
space. Straight-line distance is admissible on a grid too, and it is not the true cost — it
underestimates more than it needs to, so it guides less well and drags floating point into
an integer problem.

## What "wrong" actually looks like

Not a crash. A quietly longer path.

With an inflated heuristic, the search dives at the goal, settles a cell by a route that is
not the cheapest, and then refuses to reconsider it because it is settled. The reported
length is simply too big, and nothing signals that anything happened.

Two things worth knowing about this, both of which are easy to get wrong when testing:

- **An inadmissible heuristic is not guaranteed to be wrong** — only *unguaranteed to be
  right*. On small or open grids it usually still finds the shortest route, because there
  is only one and the greedy dive happens to follow it. You have to look for a maze where
  it fails; you will not stumble on one.
- **Weighted A\* trades optimality for speed deliberately.** Multiplying an admissible
  heuristic by w bounds the answer at w times optimal — which is often a fine trade in a
  game or a router, and never a fine trade in an interview question that says "shortest".

## What it buys you

On an open grid, Dijkstra settles cells in a widening diamond around the start; A\* settles
a narrow corridor towards the goal. Same answer, a fraction of the work.

On a single corridor with no choices, it saves nothing — there is nowhere else to go. The
payoff is proportional to how many alternatives the heuristic lets you ignore.

## When not to bother

- **No usable estimate.** If you cannot bound the remaining distance, the heuristic is zero
  and this is Dijkstra with extra code.
- **The graph is tiny.** The bookkeeping costs more than it saves.
- **Every edge costs the same.** Plain BFS is simpler and already optimal.

In an interview, "this is Dijkstra, and if we had coordinates I would add a Manhattan
heuristic to guide it" is usually the right amount of A\*.

## Where to reach for which

| the question says | you want |
| --- | --- |
| fewest steps, unweighted | BFS (3.5) |
| cheapest, no estimate available | Dijkstra (3.7) |
| cheapest, with coordinates | A\* with Manhattan or Chebyshev |
| fast enough is good enough | weighted A\*, and say so out loud |
| the estimate might overestimate | do not settle nodes once — or accept it is not optimal |
