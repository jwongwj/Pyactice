# 2.12 Union-Find

Union-Find (or "disjoint set union") answers one question: **are these two things in the
same group yet?** — while the groups are still being formed.

That "yet" is the whole point. A graph traversal answers connectivity for a graph you
already have. Union-Find answers it for a graph still arriving, one edge at a time, without
re-traversing after each one.

## The structure

An array — or dict — where each member points at another member. Follow the pointers and
you reach a **root**; two members are in the same group exactly when they share a root.

```python
parent = {i: i for i in range(size)}     # everyone starts as their own root
```

Two operations:

```python
def find(parent, x):
    root = x
    while parent[root] != root:
        root = parent[root]
    # Path compression: point everything on the way back straight at the root.
    while parent[x] != root:
        parent[x], x = root, parent[x]
    return root


def union(parent, a, b):
    ra, rb = find(parent, a), find(parent, b)
    if ra == rb:
        return False       # already together -- this edge joined nothing
    parent[rb] = ra
    return True
```

Have `union` **return whether it actually merged anything**. Almost every question built on
this structure is really asking that: how many groups are left, which edge is redundant,
did this connection matter.

## The two optimisations, and why they exist

Without them, `find` degrades into walking a linked list, and the whole structure becomes
O(n) per operation.

- **Path compression** — after finding the root, point everything you walked past straight
  at it. Next time the walk is one step.
- **Union by rank (or size)** — attach the smaller tree under the larger, so the trees stay
  shallow rather than growing into a chain.

Together they give effectively constant time per operation. Either one alone is still a
large improvement; path compression is three lines and is the one to remember.

Write `find` **iteratively**. The recursive version is the textbook one and blows the stack
on exactly the long chain an unoptimised union-find produces.

## Counting groups

Do not count at the end by collecting roots — count as you go:

```python
groups = size
for a, b in pairs:
    if union(parent, a, b):
        groups -= 1
```

Start at "everyone alone" and decrement only on a real merge. A repeated pair, or a pair
joining something to itself, merges nothing and must not decrement.

## Finding the redundant edge

An edge is redundant exactly when its two ends were already connected — which is precisely
the `False` that `union` returns. There is nothing else to write:

```python
for a, b in edges:
    if not union(parent, a, b):
        return (a, b)
return None
```

## Grids

For "how many islands", treat every cell as a member and union each land cell with the land
cell **above** and to the **left**. Those two directions are enough: by the time you reach a
cell, everything above and left has been processed, so every adjacency gets considered
exactly once.

```python
for r, c in every_cell:
    if grid[r][c] == 1:
        for dr, dc in ((-1, 0), (0, -1)):
            if in_bounds(r + dr, c + dc) and grid[r + dr][c + dc] == 1:
                union(parent, (r, c), (r + dr, c + dc))
count = len({find(parent, cell) for cell in land_cells})
```

Tuples make fine keys, so there is no need to flatten `(r, c)` into `r * cols + c` — though
that is what you would do in a language with real arrays, and it is worth recognising.

## Union-Find or a traversal?

Islands can be solved both ways, and knowing that is a skill in itself:

| | flood fill (DFS/BFS) | union-find |
| --- | --- | --- |
| the graph is fixed | natural | works, more setup |
| edges arrive over time | re-traverse every time | built for it |
| "are these two connected?", repeatedly | O(V+E) per query | near O(1) per query |
| you need the actual path | yes | no — it only knows the group |
| recursion depth | a risk on large grids | not applicable |

If the question ever says "after each query, report…", it is asking for union-find.

## Grouping by a shared attribute

The account-merge shape is worth recognising. Two records belong together when they share
*any* identifier. Union the record indices, keyed by identifier:

```python
for index, (owner, emails) in enumerate(accounts):
    for email in emails:
        if email in seen:
            union(parent, seen[email], index)
        else:
            seen[email] = index
```

Union the **records**, not the emails — you want one group per person, and each group then
collects its records' details. Watch for a record with nothing to share: it merges with
nothing and stands alone, which is correct and easy to lose.

## Where to reach for which

| the question says | you want |
| --- | --- |
| how many groups after these joins | union-find, counting down |
| which edge creates a cycle | the first `union` returning False |
| are these two connected (repeatedly) | union-find |
| islands / provinces / regions | either — flood fill is often shorter |
| merge records sharing an identifier | union the records, key by identifier |
| the actual path between two nodes | a traversal, not this |
