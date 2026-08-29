# Explanation

## The shape of the answer

```python
class HashMap:
    def __init__(self):
        self.buckets = [[] for _ in range(4)]      # NOT [[]] * 4
        self.count = 0

    def bucket_of(self, key):
        return sum(ord(character) for character in key) % len(self.buckets)

    def bucket_count(self):
        return len(self.buckets)

    def size(self):
        return self.count

    def keys_in(self, bucket):
        if not 0 <= bucket < len(self.buckets):
            return []
        return [key for key, _value in self.buckets[bucket]]

    def get(self, key):
        for existing, value in self.buckets[self.bucket_of(key)]:
            if existing == key:
                return value
        return None

    def put(self, key, value):
        chain = self.buckets[self.bucket_of(key)]
        for index, (existing, _value) in enumerate(chain):
            if existing == key:
                chain[index] = (key, value)
                return False                        # replaced, not added
        if self.count + 1 > 2 * len(self.buckets):
            self._grow()
            chain = self.buckets[self.bucket_of(key)]   # the bucket has MOVED
        chain.append((key, value))
        self.count += 1
        return True

    def remove(self, key):
        chain = self.buckets[self.bucket_of(key)]
        for index, (existing, _value) in enumerate(chain):
            if existing == key:
                del chain[index]
                self.count -= 1
                return True
        return False

    def _grow(self):
        old = self.buckets
        self.buckets = [[] for _ in range(len(old) * 2)]
        for chain in old:
            for key, value in chain:
                self.buckets[self.bucket_of(key)].append((key, value))
```

## The line that is easy to miss

```python
self._grow()
chain = self.buckets[self.bucket_of(key)]   # the bucket has MOVED
```

`chain` was looked up **before** the resize, and after it that list object is no longer in
the array at all — it belongs to the discarded `old`. Appending to the stale reference
stores the key nowhere reachable, and the very next `get` misses. It is a one-line bug that
only appears on the key that triggers the resize.

## Why the resize check is `count + 1 > 2 * len(buckets)`

The check is about the state *after* the insertion. Eight keys in four buckets is exactly
the limit and is allowed; adding a ninth would make nine, which is above it. Writing
`count > 2 * len(buckets)` tests the wrong moment and resizes one key late.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `collision_chains` | a bucket holding one entry instead of a chain |
| `everything_survives_a_resize` | copying chains without rehashing |
| `resizes_at_load_factor` | resizing one key early or one key late |
| `overwrite_returns_false` | treating a replace as an insertion |
| `remove_from_a_chain` | removing the wrong entry, or the whole bucket |
| `out_of_range_bucket` | an unguarded index |
| `value_zero_is_a_value` | falsiness as the miss test |
| `reuse_after_emptying` | a count not decremented on removal |

## Complexity

| operation | average | worst case |
| --- | --- | --- |
| get / put / remove | O(1) | O(n), when every key collides |
| resize | — | O(n), amortised O(1) per insertion |

The worst case is real: an adversary who knows your hash can choose keys that all land in
one bucket and turn every lookup linear. That is why Python **salts** its string hashing per
process — the very thing this problem had to specify away in order to be testable. Trading
that away is the cost of making the structure observable.

## Chaining versus open addressing

| | chaining | open addressing |
| --- | --- | --- |
| collision | append to the bucket's list | probe for another bucket |
| memory | a list object per bucket | one flat array |
| cache behaviour | poor — chains are scattered | good |
| deletion | remove from the list | needs tombstones |
| load factor | can exceed 1 | must stay below 1 |

CPython's dict uses open addressing with a compact layout, which is also why it preserves
insertion order (unit 2.3). Chaining is easier to write correctly under time pressure.
