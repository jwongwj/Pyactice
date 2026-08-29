# Binary search tree

Implement a binary search tree.

```python
class BST:
    def insert(self, value: int) -> bool: ...   # False if already present
    def contains(self, value: int) -> bool: ...
    def delete(self, value: int) -> bool: ...   # False if not present
    def in_order(self) -> list[int]: ...        # ascending
    def height(self) -> int: ...                # nodes on the longest path; 0 if empty
    def min_value(self) -> int | None: ...
```

- **Duplicates are not stored.** A second insert of the same value returns `False`.
- No balancing is required. `height` is whatever the insertion order produced.
- `min_value` must go left, not scan.
