# Union-Find

Implement disjoint sets: a structure that tracks which members are grouped together as
connections arrive one at a time.

```python
class UnionFind:
    def reset(self, size: int) -> None: ...        # members 0..size-1, each alone
    def find(self, member: int) -> int: ...        # the ROOT of its group, or -1
    def union(self, a: int, b: int) -> bool: ...   # True iff this joined two groups
    def connected(self, a: int, b: int) -> bool: ...
    def groups(self) -> int: ...
    def group_size(self, member: int) -> int: ...
```

- A member outside `0..size-1` is unknown: `find` gives -1, `group_size` gives 0, and
  `union` and `connected` give False.
- `union` returns **False** when the two are already together — it changed nothing.
- Which member ends up as a group's root is up to you; nothing here depends on it.
- `find` and `union` should be near-constant time. Write `find` **iteratively**.
