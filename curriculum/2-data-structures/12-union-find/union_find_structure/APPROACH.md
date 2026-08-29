# Approach

## The representation

An array where each member points at another member. Follow the pointers and you reach a
**root**; two members are in the same group exactly when they share a root.

```python
self.parent = list(range(size))     # everyone is their own root
```

That is the whole data structure. Everything else is two operations over it.

## find returns the ROOT, not the parent

This is the distinction the whole thing rests on, and the one the drills in unit 2.12 keep
depending on. `parent[x]` is one step; the root is however many steps it takes:

```python
root = member
while self.parent[root] != root:
    root = self.parent[root]
```

Comparing parents rather than roots answers "no" for two members that are genuinely in the
same group by a longer path.

**Write it iteratively.** The recursive version is the one in every textbook and it blows
the stack on exactly the long chain an unoptimised union-find produces.

## The two optimisations

Without them, `find` degrades into walking a linked list and the structure is O(n) per
operation.

**Path compression** — after finding the root, point everything you walked past straight at
it. Next time the walk is one step:

```python
while self.parent[member] != root:
    self.parent[member], member = root, self.parent[member]
```

**Union by size** (or by rank) — attach the smaller tree under the larger, so the trees
stay shallow rather than growing into a chain.

Together they give effectively constant time. Path compression alone is three lines and is
the one to remember if you only write one.

## Have union report whether it did anything

```python
if ra == rb:
    return False        # already together; this changed nothing
```

Almost every question built on this structure is really asking that. How many groups are
left, which edge is redundant, did this connection matter — all of them are counting the
`True`s.

Keep a running `groups` count and decrement it there, rather than recounting roots at the
end.

## Order of work

1. `reset` and an iterative `find`, with the range check.
2. `union` returning the boolean, and the group count decremented in the same place.
3. `connected` and `group_size` on top of `find`.
4. Then path compression, then union by size. Both are optimisations; get it correct first.
