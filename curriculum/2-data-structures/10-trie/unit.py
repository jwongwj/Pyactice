"""2.10 Trie — a tree keyed by the characters of a word.

Self-contained: loaded by file path, so no package-relative imports.

A trie earns its place when the question is about PREFIXES. A set answers "is this word
present" faster and with less code; only a trie answers "how many words start with this"
without looking at every word.

The catalogue's build exercise -- the Trie class with insert / search / startswith -- is a
class, so it arrives as a `design` problem. These drills are the using half, and they are
written against plain word lists so that the trie is a choice you make inside the function
rather than something the signature forces on you. That is deliberate: the skill being
drilled is recognising when to build one, and two of these are questions where you should
NOT bother.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="WITH_PREFIX",
        signature="(words: list[str], prefix: str) -> list[str]",
        doc="Every word starting with `prefix`, in the order given, duplicates kept. "
            "An empty prefix matches everything.",
        constraint_note="str.startswith does this; a trie would be more code for less",
        constraints=(
            Forbid(("while",),
                   because="one prefix asked once is a filter, and building a trie to "
                           "answer it costs more than the scan it saves -- knowing when "
                           "NOT to reach for the structure is half of this unit",
                   hint="[w for w in words if w.startswith(prefix)]"),
        ),
    ),
    Method(
        display="COUNT_PREFIXES",
        signature="(words: list[str], queries: list[str]) -> list[int]",
        doc="For each query, how many words start with it. One count per query, in order.",
        # Now the trie pays: many queries against one fixed word list.
        constraint_note="share the work across queries; do not rescan `words` per query",
        constraints=(
            ForbidCall(("startswith",),
                       because="one startswith per word per query is O(queries x words); a "
                               "structure built once from `words` answers each query in "
                               "the length of the query alone",
                       hint="count every prefix of every word once, into a dict -- or walk "
                            "a trie whose nodes carry a count"),
        ),
    ),
    Method(
        display="LONGEST_COMMON_PREFIX",
        signature="(words: list[str]) -> str",
        doc="The longest string that every word starts with. Empty when there is none, "
            "and empty for an empty list.",
        constraint_note="walk the words together, character by character",
        constraints=(
            ForbidCall(("startswith",),
                       because="repeatedly shortening a candidate and re-testing it is "
                               "quadratic in the prefix length; comparing one column at a "
                               "time is linear",
                       hint="compare words[0][i] against every other word's i-th "
                            "character, and stop at the first disagreement or short word"),
        ),
    ),
    Method(
        display="AUTOCOMPLETE",
        signature="(entries: list[tuple[str, int]], prefix: str, k: int) -> list[str]",
        doc="The k most-used words starting with `prefix`, most-used first, ties broken "
            "alphabetically. Each entry is (word, times used); a word may appear more than "
            "once and its uses add up.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Trie", theme="when a prefix structure pays, and when it does not"),)

TAG_GLOSSARY = {
    "prefix": "matching the start of a word",
    "shared-work": "building once to answer many queries",
    "columns": "comparing words position by position",
    "ranking": "ordering by use, with a tie-break",
    "edge-values": "empty lists, empty strings, no match, k out of range",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("with_prefix_basic", "WITH_PREFIX", ["cat", "car", "dog"], "ca",
       ret=["cat", "car"], tags=["prefix"], visible=True, doc="In the order given."),
    _c("with_prefix_empty_prefix", "WITH_PREFIX", ["a", "b"], "",
       ret=["a", "b"], tags=["prefix", "edge-values"], visible=True,
       doc="Every string starts with the empty string."),
    _c("with_prefix_whole_word", "WITH_PREFIX", ["cat"], "cat", ret=["cat"],
       tags=["prefix", "edge-values"],
       why="a word is a prefix of itself, so an exact match counts"),
    _c("with_prefix_longer_than_word", "WITH_PREFIX", ["ca"], "cat", ret=[],
       tags=["prefix", "edge-values"], visible=True,
       doc="The prefix is longer than the word, so nothing matches."),
    _c("with_prefix_duplicates", "WITH_PREFIX", ["cat", "cat"], "c",
       ret=["cat", "cat"], tags=["prefix", "edge-values"],
       why="duplicates are kept; this is a filter, not a set"),
    _c("with_prefix_none", "WITH_PREFIX", [], "a", ret=[],
       tags=["prefix", "edge-values"]),

    _c("count_prefixes_basic", "COUNT_PREFIXES", ["cat", "car", "dog"], ["ca", "d", "x"],
       ret=[2, 1, 0], tags=["shared-work"], visible=True,
       doc="One count per query, in the order asked."),
    _c("count_prefixes_empty_query", "COUNT_PREFIXES", ["a", "b"], [""],
       ret=[2], tags=["shared-work", "edge-values"], visible=True,
       doc="The empty prefix matches every word."),
    _c("count_prefixes_whole_word", "COUNT_PREFIXES", ["cat", "ca"], ["cat"],
       ret=[1], tags=["shared-work", "edge-values"],
       why="a word counts as its own prefix, but 'ca' does not start with 'cat'"),
    _c("count_prefixes_duplicates", "COUNT_PREFIXES", ["cat", "cat"], ["ca"],
       ret=[2], tags=["shared-work", "edge-values"], visible=True,
       doc="Two identical words are two words, so the count is 2 rather than 1."),
    _c("count_prefixes_no_words", "COUNT_PREFIXES", [], ["a"], ret=[0],
       tags=["shared-work", "edge-values"]),
    _c("count_prefixes_no_queries", "COUNT_PREFIXES", ["a"], [], ret=[],
       tags=["shared-work", "edge-values"]),
    _c("count_prefixes_repeated_query", "COUNT_PREFIXES", ["ab"], ["a", "a"],
       ret=[1, 1], tags=["shared-work", "edge-values"],
       why="the same query asked twice is answered twice"),

    _c("lcp_basic", "LONGEST_COMMON_PREFIX", ["flower", "flow", "flight"], ret="fl",
       tags=["columns"], visible=True, doc="All three share 'fl' and no more."),
    _c("lcp_none", "LONGEST_COMMON_PREFIX", ["dog", "cat"], ret="",
       tags=["columns", "edge-values"], visible=True, doc="Nothing in common."),
    _c("lcp_one_word", "LONGEST_COMMON_PREFIX", ["solo"], ret="solo",
       tags=["columns", "edge-values"], visible=True,
       doc="With one word, the whole word is the common prefix."),
    _c("lcp_shortest_limits", "LONGEST_COMMON_PREFIX", ["ab", "abc"], ret="ab",
       tags=["columns", "edge-values"], visible=True,
       doc="The shortest word caps the answer, and running past its end is the usual "
           "IndexError."),
    # From `drill_mutation.py --triage`: in every other case here the FIRST word is the
    # shortest, so the loop always ran out of first-word characters before it ran off the
    # end of another word -- and the length guard was never exercised at all.
    _c("lcp_first_is_longest", "LONGEST_COMMON_PREFIX", ["abc", "ab"], ret="ab",
       tags=["columns", "edge-values"], visible=True,
       doc="The first word outlives the second, so the walk must stop at the shorter "
           "one rather than index past its end."),
    _c("lcp_empty_word", "LONGEST_COMMON_PREFIX", ["", "abc"], ret="",
       tags=["columns", "edge-values"]),
    _c("lcp_identical", "LONGEST_COMMON_PREFIX", ["same", "same"], ret="same",
       tags=["columns"]),
    _c("lcp_empty_list", "LONGEST_COMMON_PREFIX", [], ret="",
       tags=["columns", "edge-values"]),

    _c("autocomplete_basic", "AUTOCOMPLETE",
       [("cat", 5), ("car", 9), ("dog", 7)], "ca", 2, ret=["car", "cat"],
       tags=["checkpoint", "ranking"], visible=True,
       doc="Most used first, and 'dog' does not match the prefix."),
    _c("autocomplete_sums_uses", "AUTOCOMPLETE",
       [("cat", 1), ("car", 2), ("cat", 3)], "ca", 1, ret=["cat"],
       tags=["checkpoint", "ranking"], visible=True,
       doc="cat appears twice for a total of 4, which beats car's 2."),
    _c("autocomplete_tie", "AUTOCOMPLETE", [("cz", 5), ("ca", 5)], "c", 2,
       ret=["ca", "cz"], tags=["checkpoint", "ranking"], visible=True,
       doc="Equal use, so alphabetical decides."),
    _c("autocomplete_k_bigger", "AUTOCOMPLETE", [("cat", 1)], "c", 9, ret=["cat"],
       tags=["checkpoint", "edge-values"]),
    _c("autocomplete_k_zero", "AUTOCOMPLETE", [("cat", 1)], "c", 0, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("autocomplete_no_match", "AUTOCOMPLETE", [("cat", 1)], "z", 3, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("autocomplete_empty", "AUTOCOMPLETE", [], "a", 3, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("autocomplete_zero_uses", "AUTOCOMPLETE", [("cat", 0), ("car", 0)], "ca", 2,
       ret=["car", "cat"], tags=["checkpoint", "edge-values"],
       why="a count of 0 is still a match; truthiness is not the test"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="tries",
    title="2.10 Trie",
    blurb="Prefix filtering, prefix counts, the common prefix and autocomplete.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("prefix", "shared-work", "ranking"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.10 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
