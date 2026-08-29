# 3.4 DFS

**Cue: "explore everything reachable", or "all paths".**

BFS answers *fewest steps*. DFS answers *is there any*, *how many pieces*, and *list them
all*. If the question does not say "shortest", DFS is usually simpler.

## Write it iteratively

```python
seen = {start}
stack = [start]
while stack:
    node = stack.pop()
    for nxt in neighbours(node):
        if nxt not in seen:
            seen.add(nxt)        # mark on PUSH
            stack.append(nxt)
```

Two things, and both are the difference between working and hanging:

- **Iterative, not recursive.** A 200×200 region of one colour recurses forty thousand
  deep; Python gives out around a thousand. Recursion is fine on a balanced tree and a
  liability on a grid or a path.
- **Mark on push, not on pop.** If a node is only marked when it comes off the stack, the
  same node gets pushed many times before it is first processed, and a cycle never
  terminates.

## Flood fill

The grid form. Repaint everything connected to a start through equal values:

```python
original = grid[row][col]
if original == colour:
    return grid          # or this loops forever
```

That guard is not optional. Repainting to the colour already there means every neighbour
still "matches" after being painted, and the search never runs out of work.

Bounds are four separate comparisons — row below zero, row at or past the row count, and
the same for columns. Each is its own guard and each needs its own test; a start far
outside the grid is rejected by all four at once and therefore tests none of them.

## Counting the pieces

One traversal finds one component. The outer loop is what turns that into "find every
piece":

```python
for cell in every_cell:
    if is_land(cell) and cell not in seen:
        sizes.append(walk_the_whole_island(cell))
```

Union-Find (unit 2.12) answers the same question. Flood fill is usually shorter; union-find
wins when the connections arrive over time.

## All paths: carry the route, and undo it

This is where DFS is genuinely the right tool. BFS would have to carry a whole path per
queue entry — which is exactly what a DFS stack already is:

```python
def walk(node, path):
    if node == goal:
        out.append(list(path))     # a COPY, or later mutations corrupt it
        return
    for nxt in graph[node]:
        path.append(nxt)
        walk(nxt, path)
        path.pop()                 # undo
```

Two details. `list(path)` copies — appending `path` itself stores a reference that every
later step keeps mutating. And the `pop()` is what stops one branch's tail leaking into the
next; two routes sharing a prefix is the case that exposes a missing undo.

## Memoising a DFS

The longest increasing path through a grid has overlapping subproblems: many routes reach
the same cell. Remember the answer per cell and the exponential search becomes linear:

```python
if cell in best_from:
    return best_from[cell]
```

No visited set is needed here, because "strictly increasing" already prevents revisiting —
the constraint makes the graph acyclic. That is worth noticing: when the movement rule
itself forbids cycles, the bookkeeping gets simpler.

## Where to reach for which

| the question says | you want |
| --- | --- |
| is X reachable | DFS |
| how many groups / islands | DFS per unvisited start, or union-find |
| all paths, all arrangements | DFS carrying the path |
| fewest steps | BFS (3.5), not this |
| longest path with a monotonic rule | DFS with memoisation |
| the graph is huge and you only need one answer | DFS, and stop early |
