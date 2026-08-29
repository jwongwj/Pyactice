# Approach

## Why one structure is not enough

- A **dict** finds a key in O(1) and knows nothing about order.
- A **list** knows order and finds a key in O(n).

The question demands both, in O(1). So use both, pointing at each other:

```python
self.index = {}     # key -> the NODE holding it
self.order = ...    # a doubly linked list, most recent at the front
```

The dict maps a key to the *node*, not to the value. That is the whole trick: the dict
finds the node in O(1), and because the list is doubly linked, that node unlinks and
re-inserts in O(1) too (the problem beside this one).

Recognising "this needs two structures cooperating" is the transferable part. It comes up
for LFU caches, "top k as it changes", and anything with both a lookup and an ordering.

## The three operations

**get(key)** — miss returns None and changes nothing. Hit: move the node to the front,
return its value.

**put(key, value)** — if the key exists, overwrite the value, move to front, **return None**.
It cannot evict, because the size did not grow. Otherwise insert at the front, and if that
took the size past the capacity, unlink the node at the back and delete its key.

**Eviction deletes from both structures.** Removing the node from the list but leaving the
key in the dict leaves a pointer to an unlinked node — and the next `get` on that key
returns a stale value from a node that is no longer in the cache. That is the classic bug,
and it does not show up until the key is asked for again.

## Capacity of zero

Not an error. Nothing can be held, so a `put` inserts and immediately evicts — and the key
it evicts is the one just given. Handle it by letting the normal eviction path run rather
than special-casing, and check the arithmetic works when the capacity is 0.

## Promoting a node that is already at the front

Unlink-then-insert on the front node has to survive being a no-op. If the unlink is written
in terms of the node's neighbours and the insert in terms of the sentinels, it does — but a
version that caches `self.head.next` before unlinking will splice the node next to itself.
Worth checking deliberately, because a repeated `get` on the same key is a completely
ordinary thing for a cache to see.

## Order of work

1. `set_capacity`, `size`, and the two empty structures.
2. `put` for a new key, without eviction. Then `keys`, so you can see the order.
3. `get`, with the promotion.
4. Eviction, deleting from both structures.
5. The overwrite path, which is `get`'s promotion plus a value change and no eviction.
6. Then capacity 0, and a repeated `get` on the front key.

## What to say out loud

`collections.OrderedDict` has `move_to_end` and `popitem(last=False)`, which makes this
about six lines — and `functools.lru_cache` exists. Say that, then write the long version,
because the long version is what is being asked for.
