# 3.7 Dijkstra

**Cue: shortest path, weighted, all weights non-negative.**

BFS answers the unweighted case because every edge costs the same, so the first arrival is
the cheapest. Once edges differ that stops being true, and the queue has to come out in
order of cost so far — which is a heap.

```python
best = {}
heap = [(0, start)]
while heap:
    cost, node = heapq.heappop(heap)
    if node in best:
        continue                     # already settled
    best[node] = cost
    for nxt, weight in graph[node]:
        if nxt not in best:
            heapq.heappush(heap, (cost + weight, nxt))
```

## Why the first pop is final

When a node comes off the heap it is the cheapest unsettled thing anywhere. Any other route
to it would have to go through something *more* expensive, and every edge costs at least
zero — so no later route can beat it. That is the settle-once argument, and it is what the
`if node in best: continue` line is protecting.

**This is exactly where non-negative matters.** A negative edge could make a settled node
cheaper later, and the algorithm has already moved on. For negative weights you need
Bellman-Ford, which relaxes every edge V−1 times and is slower for a reason. Knowing which
one a question needs is half of what is being tested.

## Lazy deletion

Pushing a node several times and skipping the stale pops — rather than trying to update a
key inside the heap — is the standard Python approach. `heapq` has no decrease-key, and the
duplicates are harmless: the cheapest copy always comes out first, and the rest are skipped
by the settled check.

## Stop early

For a single destination, return the moment the goal is popped. Its cost is already final,
and relaxing the rest of the graph tells you nothing you need.

## Maximum instead of minimum

The algorithm does not care what "better" means, only that it is monotonic. For a path
whose score is a *product* of probabilities, multiplying always shrinks it exactly as adding
weights always grows a cost, so the same code works with the comparison reversed:

```python
heapq.heappush(heap, (-score, node))     # negate, because heapq is a min-heap
```

Note that with a maximised score, a *longer* path can be better — which is the opposite of
the cost version and worth checking your intuition against.

## A maximum over minima

"How long until a signal reaches everyone" is not a total. Every node is reached by its own
cheapest route, and the broadcast is finished when the **last** of them arrives:

```python
return max(best[node] for node in nodes)    # and -1 if any is missing
```

Reading that as a sum is the usual mistake, and it reads backwards the first few times.

## When settle-once stops being valid

Add a limit — "at most k stops" — and the argument collapses. Reaching a node cheaply is
worthless if it used too many stops, so the node cannot be closed on cost alone. Either
carry the stop count as part of the state, or use a level-by-level relaxation
(Bellman-Ford bounded to k+1 rounds), which is the tidier answer.

Recognising that a constraint has invalidated the settle-once rule is the real content of
that question.

## Where to reach for which

| the question says | you want |
| --- | --- |
| fewest steps, all equal | BFS (3.5) |
| cheapest, non-negative weights | Dijkstra |
| cheapest, some weights negative | Bellman-Ford |
| cheapest between ALL pairs | Floyd-Warshall |
| cheapest with a hop limit | Bellman-Ford bounded, or state = (node, hops) |
| cheapest with a good distance estimate | A\* (3.8) |
| a DAG | topological order then relax — linear, and simpler |
