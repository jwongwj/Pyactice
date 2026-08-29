# LRU cache

Implement a fixed-size cache that evicts the **least recently used** key when it is full.
Every operation must be O(1).

```python
class LRUCache:
    def set_capacity(self, capacity: int) -> None: ...     # discards everything
    def put(self, key: str, value: int) -> str | None: ...  # returns the evicted key
    def get(self, key: str) -> int | None: ...
    def keys(self) -> list[str]: ...                        # most recent first
    def size(self) -> int: ...
```

- A **use** is a successful `get` or any `put`. Both make the key most recently used.
- A `get` that **misses** changes nothing.
- `put` on a key already present replaces its value and **never evicts**.
- `put` returns the key it evicted, or `None`.
- A capacity of 0 or less holds nothing — a `put` evicts the key it was just given.
- An unsized cache behaves as one of capacity 0.
