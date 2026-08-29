# Approach

## The state

```python
self.buckets = [[] for _ in range(4)]     # each bucket is a chain of (key, value)
self.count = 0
```

A list per bucket. That is "separate chaining", and it is one of the two standard collision
strategies — the other is open addressing, where a colliding key is placed in a *different*
bucket by probing. Chaining is simpler and is what to write.

Note the list comprehension. `[[]] * 4` makes four references to **one** list, and every
key lands in every bucket. It is the classic Python trap and it belongs in this problem.

## Collisions are the design

With more keys than buckets, collisions are guaranteed — that is the pigeonhole principle,
not bad luck. So a bucket is never "a key"; it is always "a chain of keys", even when the
chain has one entry.

Every operation is therefore: find the bucket, then **scan its chain**:

```python
bucket = self.buckets[self.bucket_of(key)]
for index, (existing, _value) in enumerate(bucket):
    if existing == key:
        ...
```

That scan is O(chain length), which is why the load factor matters.

## Why the load factor

Lookups are O(1) *only* while chains stay short. With n keys in b buckets, the average
chain is n/b — so if b never grows, lookups degrade to O(n) and the structure is a list
with extra steps.

Keeping n/b below a constant keeps the average chain a constant. Here that constant is 2:
when adding a new key would push the count above `2 * bucket_count`, double the array.

## Rehashing is not optional

After doubling, every key's bucket is `hash % new_count`, which is a **different number**
from `hash % old_count`. Copying the chains across unchanged leaves every key in the wrong
place, and every subsequent lookup misses.

```python
old = self.buckets
self.buckets = [[] for _ in range(len(old) * 2)]
for chain in old:
    for key, value in chain:
        self.buckets[self.bucket_of(key)].append((key, value))
```

`bucket_of` reads `len(self.buckets)`, so the new array must be in place before the loop.

## Order of work

1. `bucket_of` and `bucket_count`. Everything depends on them.
2. `put` and `get` with the chain scan, ignoring resizing entirely.
3. `remove`, and `keys_in` with its range check.
4. Then the resize, and only then the rehash — checking that an old key is still findable.
