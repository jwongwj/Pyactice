"""Hash map with chaining — the build exercise for unit 2.3.

What a dict is, underneath: an array of buckets, a hash to pick one, and a list per bucket
for the keys that land in the same place. Collisions are not an edge case -- with more keys
than buckets they are guaranteed -- so the chain is the design and not a fallback.

The load factor is the other half. Lookups stay O(1) only while the chains stay short, and
they only stay short if the bucket array grows with the key count.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="PUT", signature="(self, key: str, value: int) -> bool", level=1,
           doc="Store a value. True when the key is new, False when it replaced an "
               "existing value."),
    Method(display="GET", signature="(self, key: str) -> int | None", level=1,
           doc="The value for a key, or None when absent."),
    Method(display="REMOVE", signature="(self, key: str) -> bool", level=1,
           doc="Delete a key. True when it was there."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many keys are stored."),
    Method(display="BUCKET_COUNT", signature="(self) -> int", level=1,
           doc="How many buckets the array holds. Starts at 4, and DOUBLES whenever the "
               "key count would exceed twice the bucket count -- a load factor of 2."),
    # A SPECIFIED hash, not Python's. `hash()` for strings is salted per process, so
    # bucket numbers would differ between runs and nothing about the structure could be
    # asserted. Specifying it is also realistic: a hash map's behaviour is only
    # reproducible if its hash is.
    Method(display="BUCKET_OF", signature="(self, key: str) -> int", level=1,
           doc="Which bucket a key belongs in: the sum of the character codes of the key, "
               "modulo the bucket count. An empty key hashes to 0."),
    Method(display="KEYS_IN", signature="(self, bucket: int) -> list[str]", level=1,
           doc="The keys currently chained in that bucket, in insertion order. Empty for "
               "a bucket index out of range."),
)

LEVELS = (Level(1, "Hash map", theme="collisions are the design, not the exception"),)

TAG_GLOSSARY = {
    "basics": "storing and retrieving",
    "collision": "two keys in one bucket",
    "overwrite": "putting a key that is already there",
    "resize": "growing the bucket array, and rehashing",
    "absent": "keys that are not there",
    "load": "the load factor and when it triggers",
}

CASES = (
    case("put_and_get", 1, [
        op("PUT", "a", 1, ret=True), op("GET", "a", ret=1), op("SIZE", ret=1),
    ], tags=["basics"], doc="A new key returns True."),
    case("overwrite_returns_false", 1, [
        op("PUT", "a", 1, ret=True), op("PUT", "a", 2, ret=False), op("GET", "a", ret=2),
        op("SIZE", ret=1),
    ], tags=["overwrite"], visible=True,
       doc="Replacing does not grow the map, and says so by returning False."),
    case("absent_key", 1, [
        op("PUT", "a", 1), op("GET", "z", ret=None), op("REMOVE", "z", ret=False),
        op("SIZE", ret=1),
    ], tags=["absent"], doc="Nothing there, nothing changed."),
    case("remove_then_absent", 1, [
        op("PUT", "a", 1), op("REMOVE", "a", ret=True), op("GET", "a", ret=None),
        op("SIZE", ret=0), op("REMOVE", "a", ret=False),
    ], tags=["absent"], doc="Removed once, and gone."),
    case("starts_with_four_buckets", 1, [
        op("BUCKET_COUNT", ret=4), op("PUT", "a", 1), op("BUCKET_COUNT", ret=4),
    ], tags=["load"], doc="Four buckets before anything is stored."),
    case("bucket_of_is_specified", 1, [
        op("BUCKET_OF", "a", ret=1), op("BUCKET_OF", "b", ret=2),
        op("BUCKET_OF", "c", ret=3), op("BUCKET_OF", "", ret=0),
    ], tags=["collision"], visible=True,
       doc="'a' is 97, and 97 % 4 is 1. The hash is specified so the structure can be "
           "observed at all."),
    case("collision_chains", 1, [
        op("PUT", "a", 1), op("PUT", "e", 5), op("KEYS_IN", 1, ret=["a", "e"]),
        op("GET", "a", ret=1), op("GET", "e", ret=5),
    ], tags=["collision"], visible=True,
       doc="97 and 101 both fall in bucket 1, so they chain -- in insertion order -- and "
           "both are still findable. This is the case a map without chaining loses."),
    case("value_zero_is_a_value", 1, [
        op("PUT", "a", 0, ret=True), op("GET", "a", ret=0), op("SIZE", ret=1),
    ], tags=["basics", "absent"],
       doc="A stored 0 must be distinguishable from a miss."),
    case("resizes_at_load_factor", 1, [
        op("PUT", "k1", 1), op("PUT", "k2", 2), op("PUT", "k3", 3), op("PUT", "k4", 4),
        op("PUT", "k5", 5), op("PUT", "k6", 6), op("PUT", "k7", 7), op("PUT", "k8", 8),
        op("BUCKET_COUNT", ret=4), op("SIZE", ret=8),
        op("PUT", "k9", 9), op("BUCKET_COUNT", ret=8), op("SIZE", ret=9),
    ], tags=["resize", "load"], visible=True,
       doc="Eight keys in four buckets is a load factor of exactly 2 and is allowed. The "
           "ninth pushes past it, and the array doubles."),
    case("everything_survives_a_resize", 1, [
        op("PUT", "k1", 1), op("PUT", "k2", 2), op("PUT", "k3", 3), op("PUT", "k4", 4),
        op("PUT", "k5", 5), op("PUT", "k6", 6), op("PUT", "k7", 7), op("PUT", "k8", 8),
        op("PUT", "k9", 9), op("GET", "k1", ret=1), op("GET", "k5", ret=5),
        op("GET", "k9", ret=9), op("SIZE", ret=9),
    ], tags=["resize"], visible=True,
       doc="Every key is still findable after the array grew -- which means every one was "
           "REHASHED into its new bucket. Copying the chains across unchanged loses them."),
    case("bucket_of_unknown_key", 1, [
        op("BUCKET_OF", "z", ret=2),
    ], tags=["collision"],
       doc="122 % 4 is 2. BUCKET_OF answers for any key, stored or not."),
    case("out_of_range_bucket", 1, [
        op("PUT", "a", 1), op("KEYS_IN", 99, ret=[]), op("KEYS_IN", -1, ret=[]),
    ], tags=["collision"],
       doc="An index outside the array is empty rather than an error."),
    case("remove_from_a_chain", 1, [
        op("PUT", "a", 1), op("PUT", "b", 2), op("PUT", "c", 3),
        op("REMOVE", "b", ret=True), op("GET", "a", ret=1), op("GET", "c", ret=3),
        op("GET", "b", ret=None), op("SIZE", ret=2),
    ], tags=["collision", "absent"], visible=True,
       doc="Removing one key must not disturb the others, whether or not they share a "
           "bucket with it."),
    case("chain_order_is_insertion_order", 1, [
        op("PUT", "e", 5), op("PUT", "a", 1), op("KEYS_IN", 1, ret=["e", "a"]),
    ], tags=["collision"],
       doc="Both hash to bucket 1, and the chain keeps the order they arrived in."),
    case("overwrite_within_a_chain", 1, [
        op("PUT", "a", 1), op("PUT", "e", 5), op("PUT", "a", 9, ret=False),
        op("KEYS_IN", 1, ret=["a", "e"]), op("GET", "a", ret=9), op("GET", "e", ret=5),
    ], tags=["collision", "overwrite"],
       doc="Replacing a key that shares a bucket must not move it or disturb its "
           "neighbour."),
    case("remove_leaves_the_chain_usable", 1, [
        op("PUT", "a", 1), op("PUT", "e", 5), op("REMOVE", "a", ret=True),
        op("KEYS_IN", 1, ret=["e"]), op("PUT", "a", 2, ret=True),
        op("KEYS_IN", 1, ret=["e", "a"]),
    ], tags=["collision", "absent"],
       doc="Removing the head of a chain and adding it back puts it at the end."),
    # Both from `drill_mutation.py --triage`. Each needs a NON-EMPTY bucket to be
    # observable at all: with an empty chain, a loop that ignores the key and a guard that
    # lets -1 through both do nothing visible.
    case("remove_absent_key_from_a_used_bucket", 1, [
        op("PUT", "f", 6), op("REMOVE", "b", ret=False), op("KEYS_IN", 2, ret=["f"]),
        op("GET", "f", ret=6), op("SIZE", ret=1),
    ], tags=["absent", "collision"], visible=True,
       doc="'b' and 'f' share bucket 2. Removing the absent one must scan the chain and "
           "find nothing, not take whatever is first."),
    case("negative_bucket_with_content", 1, [
        op("PUT", "c", 3), op("KEYS_IN", 3, ret=["c"]), op("KEYS_IN", -1, ret=[]),
    ], tags=["collision"], visible=True,
       doc="'c' is in bucket 3, the last one. A guard that lets -1 through would return "
           "its contents, because Python indexes -1 from the end."),
    case("reuse_after_emptying", 1, [
        op("PUT", "a", 1), op("REMOVE", "a", ret=True), op("PUT", "a", 5, ret=True),
        op("GET", "a", ret=5), op("SIZE", ret=1),
    ], tags=["absent", "overwrite"],
       doc="Re-adding a removed key is a NEW key again, so PUT returns True."),
)

PROBLEM = Problem(
    key="hash_map",
    title="Hash map with chaining",
    blurb="What a dict is underneath: buckets, chains, and a load factor.",
    class_name="HashMap",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="hard",
    topics=("default", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.3 build exercise — see docs/CATALOGUE.md",
)
