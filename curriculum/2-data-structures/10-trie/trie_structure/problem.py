"""Trie — the build exercise for unit 2.10.

The structure the unit's drills deliberately avoid, so that building it is a separate
exercise from knowing when to. Three operations, and the whole design is in the difference
between two of them: `search` asks whether a word ENDS here, `starts_with` only whether the
path exists.

Without a marker for "a word ends at this node", the two questions are indistinguishable --
which is the first thing to get right.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="INSERT", signature="(self, word: str) -> bool", level=1,
           doc="Add a word. True when it is new, False when it was already there."),
    Method(display="SEARCH", signature="(self, word: str) -> bool", level=1,
           doc="Is this exact word stored? A stored prefix of it does not count."),
    Method(display="STARTS_WITH", signature="(self, prefix: str) -> bool", level=1,
           doc="Does any stored word begin with this? A stored word is a prefix of itself."),
    Method(display="COUNT_WITH", signature="(self, prefix: str) -> int", level=1,
           doc="How many stored words begin with this prefix."),
    Method(display="DELETE", signature="(self, word: str) -> bool", level=1,
           doc="Remove a word. True when it was there. Other words sharing its path must "
               "survive."),
    Method(display="WORDS", signature="(self) -> list[str]", level=1,
           doc="Every stored word, sorted ascending."),
    Method(display="NODE_COUNT", signature="(self) -> int", level=1,
           doc="How many nodes the trie holds, not counting the root. This is the number "
               "of distinct prefixes stored."),
)

LEVELS = (Level(1, "Trie", theme="a word ending here is not the same as a path existing"),)

TAG_GLOSSARY = {
    "basics": "inserting and finding",
    "marker": "the distinction between a word and a prefix",
    "sharing": "words sharing a path, and nodes counted once",
    "prune": "deleting without disturbing the words that remain",
    "empty": "the empty trie and the empty word",
}

CASES = (
    case("insert_and_search", 1, [
        op("INSERT", "cat", ret=True), op("SEARCH", "cat", ret=True),
        op("SEARCH", "ca", ret=False), op("STARTS_WITH", "ca", ret=True),
    ], tags=["marker"], visible=True,
       doc='"ca" is a path but not a word. This is the distinction the whole structure '
           "exists to make, and a trie without an end-of-word marker cannot."),
    case("word_is_its_own_prefix", 1, [
        op("INSERT", "cat"), op("STARTS_WITH", "cat", ret=True),
        op("COUNT_WITH", "cat", ret=1),
    ], tags=["marker"], doc="A stored word begins with itself."),
    case("prefix_of_a_stored_word", 1, [
        op("INSERT", "cat"), op("INSERT", "ca", ret=True), op("SEARCH", "ca", ret=True),
        op("SEARCH", "cat", ret=True), op("WORDS", ret=["ca", "cat"]),
    ], tags=["marker"], visible=True,
       doc="Storing a prefix of an existing word adds a marker on a node that already "
           "existed -- so no new nodes, and both words are now findable."),
    case("duplicate_insert", 1, [
        op("INSERT", "cat", ret=True), op("INSERT", "cat", ret=False),
        op("COUNT_WITH", "", ret=1),
    ], tags=["basics"], doc="Stored once."),
    case("nodes_are_shared", 1, [
        op("INSERT", "cat"), op("NODE_COUNT", ret=3), op("INSERT", "car"),
        op("NODE_COUNT", ret=4), op("INSERT", "dog"), op("NODE_COUNT", ret=7),
    ], tags=["sharing"], visible=True,
       doc='"car" adds only one node, because "ca" already existed. That sharing is why a '
           "trie is compact for words with common prefixes."),
    case("count_with_prefix", 1, [
        op("INSERT", "cat"), op("INSERT", "car"), op("INSERT", "dog"),
        op("COUNT_WITH", "ca", ret=2), op("COUNT_WITH", "d", ret=1),
        op("COUNT_WITH", "x", ret=0), op("COUNT_WITH", "", ret=3),
    ], tags=["basics"],
       doc="The empty prefix matches everything."),
    case("delete_leaves_siblings", 1, [
        op("INSERT", "cat"), op("INSERT", "car"), op("DELETE", "cat", ret=True),
        op("SEARCH", "cat", ret=False), op("SEARCH", "car", ret=True),
        op("STARTS_WITH", "ca", ret=True), op("WORDS", ret=["car"]),
    ], tags=["prune"], visible=True,
       doc='Deleting "cat" must not remove the shared "ca" path that "car" still needs.'),
    case("delete_prunes_dead_nodes", 1, [
        op("INSERT", "cat"), op("INSERT", "dog"), op("NODE_COUNT", ret=6),
        op("DELETE", "cat", ret=True), op("NODE_COUNT", ret=3),
        op("STARTS_WITH", "c", ret=False),
    ], tags=["prune"], visible=True,
       doc="With nothing else sharing them, the three nodes of \"cat\" go entirely. "
           "Leaving them behind makes STARTS_WITH answer True for a path to nowhere."),
    case("delete_keeps_a_prefix_word", 1, [
        op("INSERT", "ca"), op("INSERT", "cat"), op("DELETE", "cat", ret=True),
        op("SEARCH", "ca", ret=True), op("NODE_COUNT", ret=2),
        op("STARTS_WITH", "cat", ret=False),
    ], tags=["prune", "marker"],
       doc='Pruning has to stop at the node marking "ca", which is still a word.'),
    case("delete_absent", 1, [
        op("INSERT", "cat"), op("DELETE", "car", ret=False),
        op("DELETE", "ca", ret=False), op("SEARCH", "cat", ret=True),
        op("NODE_COUNT", ret=3),
    ], tags=["prune"],
       doc='Deleting "ca" -- a path that exists but is not a word -- changes nothing.'),
    case("empty_trie", 1, [
        op("SEARCH", "a", ret=False), op("STARTS_WITH", "a", ret=False),
        # Two characters, deliberately. With one, the walk ends before it ever
        # dereferences the missing node -- so a missing null check survives. Found by
        # `drill_mutation.py --triage`.
        op("STARTS_WITH", "ca", ret=False), op("SEARCH", "ca", ret=False),
        op("COUNT_WITH", "ca", ret=0),
        op("STARTS_WITH", "", ret=True), op("COUNT_WITH", "", ret=0),
        op("WORDS", ret=[]), op("NODE_COUNT", ret=0), op("DELETE", "a", ret=False),
    ], tags=["empty"], visible=True,
       doc="Nothing stored. The empty prefix still matches -- vacuously."),
    case("empty_word", 1, [
        op("INSERT", "", ret=True), op("SEARCH", "", ret=True),
        op("NODE_COUNT", ret=0), op("WORDS", ret=[""]), op("COUNT_WITH", "", ret=1),
    ], tags=["empty", "marker"], visible=True,
       doc="The empty word is stored as a marker on the ROOT, which is why it adds no "
           "nodes."),
    case("delete_empty_word", 1, [
        op("INSERT", ""), op("INSERT", "a"), op("DELETE", "", ret=True),
        op("SEARCH", "", ret=False), op("SEARCH", "a", ret=True),
    ], tags=["empty", "prune"],
       doc="Removing the root's own marker must not disturb the rest of the trie."),
    case("words_are_sorted", 1, [
        op("INSERT", "dog"), op("INSERT", "cat"), op("INSERT", "ca"),
        op("WORDS", ret=["ca", "cat", "dog"]),
    ], tags=["basics"],
       doc="Sorted, not in insertion order -- and a prefix sorts before the word it "
           "extends."),
    case("count_after_delete", 1, [
        op("INSERT", "cat"), op("INSERT", "car"), op("COUNT_WITH", "ca", ret=2),
        op("DELETE", "car", ret=True), op("COUNT_WITH", "ca", ret=1),
        op("COUNT_WITH", "", ret=1),
    ], tags=["prune"],
       doc="A per-node count kept on insert has to be decremented on delete too."),
)

PROBLEM = Problem(
    key="trie_structure",
    title="Trie",
    blurb="Insert, search, startswith and the delete that has to prune carefully.",
    class_name="Trie",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="hard",
    topics=("prefix", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.10 build exercise — see docs/CATALOGUE.md",
)
