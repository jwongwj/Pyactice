# Explanation

## The shape of the answer

```python
class UnionFind:
    def reset(self, size):
        size = max(0, size)
        self.parent = list(range(size))
        self.count = [1] * size
        self.groups_left = size

    def find(self, member):
        if not 0 <= member < len(self.parent):
            return -1
        root = member
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[member] != root:          # path compression
            self.parent[member], member = root, self.parent[member]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == -1 or rb == -1 or ra == rb:
            return False
        if self.count[ra] < self.count[rb]:         # union by size
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.count[ra] += self.count[rb]
        self.groups_left -= 1
        return True
```

`connected`, `groups` and `group_size` are then one line each on top of `find`.

## The two loops in find

The first walks to the root. The second walks the same path again, repointing everything at
it. Splitting them is what makes the compression easy to write without recursion — the
second loop needs to know the root, which the first found.

Note the second loop's assignment order: `self.parent[member], member = root, self.parent[member]`.
The right-hand side is evaluated first, so the old parent is captured before it is
overwritten. Reversing those two clauses loses the rest of the path.

## Sizes belong on the root

`count[root]` is the size of the group; `count` for a non-root is stale and meaningless.
That is why `group_size` calls `find` first. Keeping a size per *member* and updating both
on a union looks reasonable and quietly goes wrong the third time two groups merge.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `transitive_membership` | comparing parents instead of roots |
| `union_twice_is_idempotent` | decrementing the group count on a no-op union |
| `union_self_is_idempotent` | the same, for a member joined to itself |
| `union_two_groups` | sizes kept on members rather than on the root |
| `out_of_range` / `negative_member` | a missing range check, which would IndexError |
| `group_members_all_agree` | nothing — deliberately. It asserts connectivity rather than which member is the root, because union by size and union by rank pick different ones and both are right |

## Complexity

With both optimisations, m operations over n members cost O(m·α(n)), where α is the inverse
Ackermann function — below 5 for any n you will ever see, so effectively constant.

Without them: O(n) per operation in the worst case. The optimisations are not polish.

## Union-Find or a traversal?

Union-Find answers connectivity for a graph **still being built**. A traversal answers it
for a graph you already have, and re-answering after every new edge means re-traversing.

If a question says "after each query, report…", it is asking for this. See unit 2.12 for
the same comparison in more detail, and unit 2.11 for the traversal side.
