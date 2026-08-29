# 2.11 Graph

There is no Graph class in Python and you rarely want one. A graph is a dict of lists:

```python
from collections import defaultdict

graph = defaultdict(list)
for a, b in edges:
    graph[a].append(b)
    graph[b].append(a)      # BOTH ways for an undirected graph; only the first for directed
```

That one line — whether you append both ways — is the entire difference between a directed
and an undirected graph, and it is the thing to decide before writing anything else.

## Adjacency list or matrix

| | list of lists | matrix |
| --- | --- | --- |
| space | O(V + E) | O(V²) |
| "are a and b joined?" | O(degree) | O(1) |
| "what is a joined to?" | O(degree) | O(V) |
| good for | sparse graphs, which is nearly all of them | dense graphs, or constant-time edge tests |

In an interview, the adjacency list is the default. Reach for a matrix only when the graph
is dense or you need constant-time edge lookups.

Note that `defaultdict` silently creates a key on *read*, so a node with no edges will not
appear in the dict until something asks about it. If isolated nodes matter — and for
counting components they do — seed every node first:

```python
graph = {node: [] for node in nodes}
```

## One traversal, four questions

Almost every graph question here is the same walk with different bookkeeping:

```python
seen = {start}
stack = [start]
while stack:
    node = stack.pop()          # .pop(0) or a deque.popleft() makes it BFS
    for nxt in graph[node]:
        if nxt not in seen:
            seen.add(nxt)
            stack.append(nxt)
```

- **Reachability**: what ends up in `seen`.
- **Components**: start this walk from every node not yet seen, and count how many walks
  you start.
- **Two-colouring**: carry a colour, and give every neighbour the opposite one.
- **Shortest path** (unweighted): the same loop with a queue instead of a stack — unit 2.6.

Use an explicit stack rather than recursion. A path of ten thousand nodes recurses ten
thousand deep, and Python gives out around a thousand.

## Components

The only subtlety is the outer loop. A traversal from one node finds one component; you
have to start a new one from every node not yet reached:

```python
found = 0
for start in nodes:
    if start in seen:
        continue
    found += 1
    walk(start)
```

Isolated nodes are components of size one, which falls out naturally — as long as `nodes`
is the list you iterate, and not the keys of an adjacency dict that never mentioned them.

## Cycle detection: directed is not undirected

This is the trap worth remembering.

**Undirected**: a cycle exists if a walk reaches an already-seen node that is not the one
you just came from. The "came from" exclusion is essential, or every single edge looks like
a cycle of length two.

**Directed**: "have I seen this node" is *not enough*. Consider:

```
a → b → d
a → c → d
```

`d` is reached twice, and there is no cycle. A plain visited set says otherwise. The
question is not "have I been here" but "am I still standing on it" — is this node open on
the path I am currently walking? So you need three states:

```python
# 0 unvisited, 1 on the current path, 2 finished
if state[nxt] == 1:
    return True          # reached something still open -- a cycle
if state[nxt] == 0:
    ...                  # descend
```

A node is set to 1 on the way in and 2 on the way *back out*. Forgetting to set it to 2 —
or setting it on the way in — turns the whole thing back into a visited set.

A self-loop is a cycle in both readings.

## Two-colouring, and what it proves

A graph is bipartite when it can be two-coloured with no edge joining same colours. Walk
it, and give each neighbour the opposite colour to the current node:

```python
if nxt not in colour:
    colour[nxt] = 1 - colour[node]
elif colour[nxt] == colour[node]:
    return False
```

Two things. **Every component needs its own start** — colouring only from the first node
declares an uncoloured piece fine without ever looking at it. And the property this
actually tests is *"no odd cycle"*: a ring of three cannot be two-coloured, a ring of four
can. That equivalence is worth knowing, because questions ask for it both ways round.

## Where to reach for which

| the question says | you want |
| --- | --- |
| how many groups / islands / provinces | components, or union-find (2.12) |
| fewest steps, unweighted | BFS |
| all paths, or "explore fully" | DFS with an explicit stack |
| can this be scheduled / ordered | cycle check, then topological sort (3.9) |
| two teams, no conflicts | bipartite check |
| shortest path with weights | Dijkstra (3.7), not this |
