# Hash map with chaining

Implement what a dict is underneath: an array of buckets, a specified hash to pick one, and
a chain per bucket for keys that collide.

```python
class HashMap:
    def put(self, key: str, value: int) -> bool: ...   # True iff the key is new
    def get(self, key: str) -> int | None: ...
    def remove(self, key: str) -> bool: ...
    def size(self) -> int: ...
    def bucket_count(self) -> int: ...
    def bucket_of(self, key: str) -> int: ...
    def keys_in(self, bucket: int) -> list[str]: ...   # insertion order
```

- **The hash is specified**: the sum of the character codes of the key, modulo the bucket
  count. An empty key hashes to 0. Do not use Python's `hash()` — it is salted per process,
  and the answers would not be reproducible.
- The bucket array starts at **4** and **doubles** whenever storing a new key would take
  the key count above **twice** the bucket count. Eight keys in four buckets is allowed;
  the ninth triggers a resize.
- Every key must be **rehashed** into the new array when it grows.
- `keys_in` for an index outside the array is empty, not an error.
- Do not use a Python `dict` or `set` for the storage. That is the thing being built.
