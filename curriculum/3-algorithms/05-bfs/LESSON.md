# 3.5 BFS

**Cue: fewest steps, unweighted.**

BFS expands in distance order, so the first time it reaches anything it has reached it by a
shortest route. That single property is the whole reason to prefer it, and it is the first
thing to say when asked why.

```python
distance = {start: 0}
queue = deque([start])
while queue:
    node = queue.popleft()
    for nxt in neighbours(node):
        if nxt not in distance:
            distance[nxt] = distance[node] + 1    # set on ENQUEUE
            queue.append(nxt)
```

Three things to get right, and they are the same three every time:

- **`popleft`, not `pop`.** A stack turns this into a DFS that still looks like BFS and
  quietly returns paths that are not shortest.
- **Record the distance when you enqueue**, not when you dequeue. Otherwise the same node
  is queued many times before it is first processed.
- **Decide what you are counting** — cells visited or steps taken. They differ by one, and
  a single-node input is what tells you which the question meant.

## Multi-source

The trick worth knowing. If several places start at distance zero, put them *all* in the
queue before the loop begins:

```python
for cell in every_rotten_cell:
    queue.append(cell)
```

Running one BFS per source and taking the minimum gives the same answer and is far slower.
Seeding them together costs one pass. "How long until the rot spreads everywhere", "how far
is every cell from the nearest exit", "which office is nearest each house" — all the same
shape.

## Levels

When the answer is *per round* rather than per node, drain exactly one level at a time:

```python
while queue:
    for _ in range(len(queue)):      # take the length BEFORE the loop
        ...
    rounds += 1
```

Taking `len(queue)` first is what fixes the boundary; anything appended inside belongs to
the next round. Same idea as a tree's level-order traversal (unit 2.9).

## Implicit graphs

There need not be a graph object at all. In a word ladder the nodes are words and the
neighbours are generated:

```python
for position in range(len(word)):
    for letter in "abcdefghijklmnopqrstuvwxyz":
        candidate = word[:position] + letter + word[position + 1:]
```

Recognising that something *is* a graph is most of the difficulty. A state you can change
by small steps, with a question about the fewest steps, is a BFS — whether the states are
words, numbers, board positions or jug volumes.

Discard each word from the pool as you reach it. That is the visited set, wearing different
clothes, and without it the queue explodes.

The numeric version is the same: from a value you can double or subtract one, and "fewest
operations" is BFS over integers. Bound the range or it never terminates.

## Where BFS stops being enough

The moment edges have **different costs**, the first arrival is no longer the cheapest, and
you need a heap ordered by cost — that is Dijkstra, unit 3.7. BFS is Dijkstra for the
special case where every edge costs 1.

## Where to reach for which

| the question says | you want |
| --- | --- |
| fewest steps, all steps equal | BFS |
| fewest steps, weighted | Dijkstra (3.7) |
| spreading from several places at once | multi-source BFS |
| how many rounds | BFS draining a level at a time |
| all paths | DFS (3.4) — BFS would carry a path per entry |
| is it reachable at all | either; DFS is usually shorter |
