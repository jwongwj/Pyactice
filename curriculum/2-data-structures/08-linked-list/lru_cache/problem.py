"""LRU cache — the build exercise for unit 2.8, and the reason the doubly linked list beside
it exists.

Neither a dict nor a list can do this alone. A dict finds a key in O(1) and has no order; a
list has order and finds nothing quickly. Together -- a dict from key to NODE, and a doubly
linked list holding the recency order -- every operation is O(1).

Recognising that a question needs two structures cooperating is the skill. It comes up
again for any "most recent", "least frequent" or "top-k as it changes" problem.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="SET_CAPACITY", signature="(self, capacity: int) -> None", level=1,
           doc="Discard everything and start again holding at most `capacity` entries. A "
               "capacity of 0 or less holds nothing."),
    Method(display="PUT", signature="(self, key: str, value: int) -> str | None", level=1,
           doc="Store a value, making that key the most recently used. When the cache is "
               "full this evicts the LEAST recently used key and returns it; otherwise "
               "returns None. Overwriting an existing key never evicts."),
    Method(display="GET", signature="(self, key: str) -> int | None", level=1,
           doc="The value for a key, and using it makes that key the most recently used. "
               "None when absent -- a miss does not change the order."),
    Method(display="KEYS", signature="(self) -> list[str]", level=1,
           doc="Every key held, MOST recently used first."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many entries are held."),
)

LEVELS = (Level(1, "LRU cache", theme="a dict and a list, cooperating"),)

TAG_GLOSSARY = {
    "basics": "storing and retrieving",
    "recency": "what counts as a use, and what it does to the order",
    "eviction": "which key goes, and when",
    "overwrite": "putting a key that is already there",
    "capacity": "zero capacity, and shrinking",
    "miss": "a get for a key that is not there",
}

CASES = (
    case("put_and_get", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1, ret=None), op("GET", "a", ret=1),
        op("SIZE", ret=1),
    ], tags=["basics"], doc="Nothing evicted, so PUT returns None."),
    case("get_promotes", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1), op("PUT", "b", 2),
        op("KEYS", ret=["b", "a"]), op("GET", "a", ret=1), op("KEYS", ret=["a", "b"]),
    ], tags=["recency"], visible=True,
       doc="A successful GET counts as a use and moves the key to the front."),
    case("evicts_least_recent", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1), op("PUT", "b", 2),
        op("PUT", "c", 3, ret="a"), op("KEYS", ret=["c", "b"]), op("GET", "a", ret=None),
    ], tags=["eviction"], visible=True,
       doc="'a' was least recently used, so it goes and PUT reports which key was lost."),
    case("get_saves_a_key_from_eviction", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1), op("PUT", "b", 2),
        op("GET", "a", ret=1), op("PUT", "c", 3, ret="b"), op("KEYS", ret=["c", "a"]),
    ], tags=["recency", "eviction"], visible=True,
       doc="The GET on 'a' made 'b' the oldest, so 'b' is evicted instead. This is the "
           "case that proves a GET really does reorder."),
    case("overwrite_does_not_evict", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1), op("PUT", "b", 2),
        op("PUT", "a", 9, ret=None), op("SIZE", ret=2), op("GET", "a", ret=9),
        op("KEYS", ret=["a", "b"]),
    ], tags=["overwrite"], visible=True,
       doc="The cache was full, and putting an EXISTING key replaces rather than adds -- "
           "so nothing is evicted, and the key is promoted."),
    case("miss_does_not_reorder", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1), op("PUT", "b", 2),
        op("GET", "z", ret=None), op("PUT", "c", 3, ret="a"),
    ], tags=["miss", "recency"], visible=True,
       doc="A GET that misses must not touch the order, or the wrong key is evicted next."),
    case("capacity_one", 1, [
        op("SET_CAPACITY", 1), op("PUT", "a", 1, ret=None), op("PUT", "b", 2, ret="a"),
        op("KEYS", ret=["b"]), op("SIZE", ret=1),
    ], tags=["eviction", "capacity"],
       doc="Every put after the first evicts."),
    case("zero_capacity", 1, [
        op("SET_CAPACITY", 0), op("PUT", "a", 1, ret="a"), op("SIZE", ret=0),
        op("GET", "a", ret=None), op("KEYS", ret=[]),
    ], tags=["capacity"], visible=True,
       doc="Nothing can be held, so the key that was just put is itself the one evicted."),
    case("before_any_capacity", 1, [
        op("SIZE", ret=0), op("GET", "a", ret=None), op("KEYS", ret=[]),
        op("PUT", "a", 1, ret="a"),
    ], tags=["capacity"], doc="An unsized cache behaves as one of capacity 0."),
    case("set_capacity_discards", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1), op("SET_CAPACITY", 2),
        op("SIZE", ret=0), op("GET", "a", ret=None),
    ], tags=["capacity"], doc="Sizing starts again, even at the same capacity."),
    case("value_zero_is_a_value", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 0), op("GET", "a", ret=0),
        op("SIZE", ret=1),
    ], tags=["basics", "miss"],
       doc="A stored 0 must be distinguishable from a miss; falsiness is not the test."),
    case("keys_order_after_overwrite_of_oldest", 1, [
        op("SET_CAPACITY", 3), op("PUT", "a", 1), op("PUT", "b", 2), op("PUT", "c", 3),
        op("PUT", "a", 9, ret=None), op("KEYS", ret=["a", "c", "b"]),
        op("PUT", "d", 4, ret="b"),
    ], tags=["overwrite", "recency"],
       doc="Overwriting the OLDEST key promotes it, so the next eviction takes the "
           "second oldest instead."),
    case("eviction_frees_the_key_completely", 1, [
        op("SET_CAPACITY", 1), op("PUT", "a", 1), op("PUT", "b", 2, ret="a"),
        op("GET", "a", ret=None), op("PUT", "a", 7, ret="b"), op("GET", "a", ret=7),
        op("SIZE", ret=1),
    ], tags=["eviction", "miss"],
       doc="An evicted key must be gone from the dict as well as the list, or this GET "
           "returns a stale value from an unlinked node."),
    case("long_sequence", 1, [
        op("SET_CAPACITY", 3), op("PUT", "a", 1), op("PUT", "b", 2), op("PUT", "c", 3),
        op("GET", "a", ret=1), op("PUT", "d", 4, ret="b"),
        op("KEYS", ret=["d", "a", "c"]), op("GET", "c", ret=3),
        op("PUT", "e", 5, ret="a"), op("KEYS", ret=["e", "c", "d"]),
    ], tags=["recency", "eviction"], visible=True,
       doc="Several promotions and evictions. Every step depends on the previous order "
           "being exactly right."),
    case("repeated_get_same_key", 1, [
        op("SET_CAPACITY", 2), op("PUT", "a", 1), op("PUT", "b", 2),
        op("GET", "b", ret=2), op("GET", "b", ret=2), op("KEYS", ret=["b", "a"]),
    ], tags=["recency"],
       doc="Promoting a key that is already at the front must not corrupt the list -- "
           "unlinking and re-inserting the same node is where that goes wrong."),
)

PROBLEM = Problem(
    key="lru_cache",
    title="LRU cache",
    blurb="A fixed-size cache evicting the least recently used key, all operations O(1).",
    class_name="LRUCache",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="hard",
    topics=("repoint", "invariant", "default"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.8 build exercise — see docs/CATALOGUE.md",
)
