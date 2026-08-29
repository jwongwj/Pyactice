"""2.3 Dict — the structure that turns a scan into a lookup.

Self-contained: loaded by file path, so no package-relative imports.

Most of what makes code slow in an interview is a list where a dict belonged. Most of what
makes it long is `if key in d:` where `get`, `setdefault` or `defaultdict` belonged.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="LOOKUP_OR",
        signature="(table: dict[str, int], key: str, fallback: int) -> int",
        doc="The value at `key`, or `fallback` when it is absent.",
        constraint_note="one call to dict.get; no `in` test, no try",
        constraints=(
            Forbid(("if", "try"),
                   because="get() takes the default as its second argument, which is the "
                           "whole reason it exists",
                   hint="return table.get(key, fallback)"),
        ),
    ),
    Method(
        display="APPEND_TO",
        signature="(table: dict[str, list[int]], key: str, value: int) -> dict[str, list[int]]",
        doc="`value` appended to the list at `key`, creating the list if needed.",
        constraint_note="use dict.setdefault; no `in` test",
        constraints=(
            Forbid(("if",),
                   because="setdefault returns the existing list, or installs and returns "
                           "the default -- which is exactly the two-branch `if` it replaces",
                   hint="table.setdefault(key, []).append(value)"),
            RequireCall(("setdefault",), because="this drill is about setdefault"),
        ),
    ),
    Method(
        display="GROUPED",
        signature="(rows: list[tuple[str, str]], ) -> dict[str, list[str]]",
        doc="For each (group, member) pair, the members under their group, in input order.",
        constraint_note="use collections.defaultdict(list); no `in` test",
        constraints=(
            Forbid(("if",),
                   because="a defaultdict builds the missing list on first access, so the "
                           "loop body is one line",
                   hint="out = defaultdict(list), then out[group].append(member)"),
            RequireCall(("defaultdict",), because="this drill is about defaultdict"),
        ),
    ),
    Method(
        display="TALLY",
        signature="(items: list[str]) -> dict[str, int]",
        doc="How many times each item appears.",
        constraint_note="use collections.Counter",
        constraints=(
            RequireCall(("Counter",),
                        because="counting is solved; a Counter compares equal to the dict "
                                "you would have built by hand",
                        hint="return Counter(items)"),
            ForbidCall(("count",),
                       because="items.count(x) inside a loop re-scans the list per item",
                       hint="Counter does it in one pass"),
        ),
    ),
    Method(
        display="TOP_ITEMS",
        signature="(items: list[str], n: int) -> list[str]",
        doc="The n most common items, most common first, ties broken alphabetically.",
        # Counter.most_common's own tie-break is insertion order, NOT alphabetical, so
        # this cannot be a bare most_common(n) call -- which is the point.
        constraint_note="no manual counting loop; mind that most_common does not "
                        "break ties alphabetically",
        constraints=(
            ForbidCall(("count",),
                       because="the counting is the easy half and Counter already did it",
                       hint="count with Counter, then sort by (-count, item)"),
        ),
    ),
    Method(
        display="MERGED",
        signature="(tables: list[dict[str, int]]) -> dict[str, int]",
        doc="All tables merged into one. On a clash, the LATER table wins.",
        constraint_note="one dict, updated in order; no `in` test",
        constraints=(
            Forbid(("if",),
                   because="update() already overwrites, so a clash needs no branch",
                   hint="out = {}, then out.update(table) for each in order"),
        ),
    ),
    Method(
        display="INVERTED",
        signature="(table: dict[str, str]) -> dict[str, list[str]]",
        doc="Values become keys. Keys that shared a value are collected in a list, "
            "in the original insertion order.",
        constraint_note="collect the collisions; do not let one key overwrite another",
        constraints=(
            Forbid(("if",),
                   because="inverting is only a one-liner when values are unique -- which "
                           "they are not, and the naive version silently loses keys",
                   hint="setdefault or defaultdict(list), then append"),
        ),
    ),
    Method(
        display="FIRST_UNIQUE",
        signature="(text: str) -> str | None",
        doc="The first character that appears exactly once, or None if there is none.",
        constraint_note="count first, then scan once; no count() inside a loop",
        constraints=(
            ForbidCall(("count", "index"),
                       because="text.count(ch) per character is a second pass per "
                               "character, which is the quadratic version of a two-pass job",
                       hint="Counter(text), then walk `text` in order and return the first "
                            "whose count is 1"),
        ),
    ),
    Method(
        display="SUBARRAY_SUM_COUNT",
        signature="(nums: list[int], k: int) -> int",
        doc="How many contiguous slices of `nums` sum to exactly k. Slices may be "
            "of any length, and may overlap.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Dict", theme="a lookup instead of a scan"),)

TAG_GLOSSARY = {
    "default": "get, setdefault and defaultdict",
    "grouping": "collecting rows under a key",
    "counting": "Counter and tallies",
    "ordering": "sort keys and tie-breaks",
    "collision": "two keys competing for one slot",
    "two-pass": "count everything, then decide",
    "edge-values": "empty inputs, zero, absent keys, ties",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("lookup_present", "LOOKUP_OR", {"a": 1}, "a", 0, ret=1,
       tags=["default"], visible=True, doc="Present: the stored value."),
    _c("lookup_absent", "LOOKUP_OR", {"a": 1}, "b", 0, ret=0,
       tags=["default", "edge-values"], visible=True, doc="Absent: the fallback."),
    _c("lookup_stored_zero", "LOOKUP_OR", {"a": 0}, "a", 9, ret=0,
       tags=["default", "edge-values"],
       why="a stored 0 is present, so it wins over the fallback -- `table.get(key) or "
           "fallback` gets this wrong"),
    _c("lookup_empty_table", "LOOKUP_OR", {}, "a", 5, ret=5, tags=["default", "edge-values"]),

    _c("append_to_new_key", "APPEND_TO", {}, "a", 1, ret={"a": [1]},
       tags=["default"], visible=True, doc="The list is created on first use."),
    _c("append_to_existing", "APPEND_TO", {"a": [1]}, "a", 2, ret={"a": [1, 2]},
       tags=["default"], visible=True, doc="An existing list is appended to, not replaced."),
    _c("append_to_other_key", "APPEND_TO", {"a": [1]}, "b", 2, ret={"a": [1], "b": [2]},
       tags=["default"], why="the untouched key must survive"),
    _c("append_to_zero", "APPEND_TO", {}, "a", 0, ret={"a": [0]},
       tags=["default", "edge-values"]),

    _c("grouped_basic", "GROUPED", [("x", "a"), ("y", "b"), ("x", "c")],
       ret={"x": ["a", "c"], "y": ["b"]}, tags=["grouping"], visible=True,
       doc="Members stay in the order they arrived."),
    _c("grouped_single_group", "GROUPED", [("x", "a"), ("x", "b")],
       ret={"x": ["a", "b"]}, tags=["grouping"]),
    _c("grouped_empty", "GROUPED", [], ret={}, tags=["grouping", "edge-values"]),
    _c("grouped_repeated_member", "GROUPED", [("x", "a"), ("x", "a")],
       ret={"x": ["a", "a"]}, tags=["grouping", "edge-values"],
       why="grouping is not deduping -- the repeat is kept"),

    _c("tally_basic", "TALLY", ["a", "b", "a"], ret={"a": 2, "b": 1},
       tags=["counting"], visible=True, doc="A Counter compares equal to this dict."),
    _c("tally_empty", "TALLY", [], ret={}, tags=["counting", "edge-values"], visible=True,
       doc="Nothing counted is an empty dict, not a dict of zeros."),
    _c("tally_all_same", "TALLY", ["z", "z", "z"], ret={"z": 3}, tags=["counting"]),

    _c("top_items_basic", "TOP_ITEMS", ["a", "b", "a", "c", "a", "b"], 2,
       ret=["a", "b"], tags=["counting", "ordering"], visible=True,
       doc="Most common first."),
    _c("top_items_tie_alphabetical", "TOP_ITEMS", ["b", "a"], 2, ret=["a", "b"],
       tags=["counting", "ordering", "edge-values"], visible=True,
       doc="Both appear once. Ties are alphabetical, so 'a' comes first -- which is NOT "
           "what Counter.most_common does on its own: it keeps insertion order, and would "
           "give ['b', 'a'] here."),
    _c("top_items_n_bigger", "TOP_ITEMS", ["a"], 9, ret=["a"],
       tags=["counting", "edge-values"], why="n larger than the input returns everything"),
    _c("top_items_n_zero", "TOP_ITEMS", ["a"], 0, ret=[],
       tags=["counting", "edge-values"]),
    _c("top_items_empty", "TOP_ITEMS", [], 3, ret=[], tags=["counting", "edge-values"]),

    _c("merged_basic", "MERGED", [{"a": 1}, {"b": 2}], ret={"a": 1, "b": 2},
       tags=["collision"], visible=True, doc="Disjoint tables just combine."),
    _c("merged_later_wins", "MERGED", [{"a": 1}, {"a": 2}], ret={"a": 2},
       tags=["collision"], visible=True, doc="On a clash the later table wins."),
    _c("merged_three", "MERGED", [{"a": 1}, {"a": 2}, {"a": 3}], ret={"a": 3},
       tags=["collision"], why="with three tables it is the last, not the second"),
    _c("merged_empty_list", "MERGED", [], ret={}, tags=["collision", "edge-values"]),
    _c("merged_zero_value", "MERGED", [{"a": 1}, {"a": 0}], ret={"a": 0},
       tags=["collision", "edge-values"],
       why="a later 0 still wins; truthiness is not the test"),

    _c("inverted_unique", "INVERTED", {"a": "x", "b": "y"},
       ret={"x": ["a"], "y": ["b"]}, tags=["collision"], visible=True,
       doc="Every value becomes a key holding a list, even with no collision."),
    _c("inverted_collision", "INVERTED", {"a": "x", "b": "x"}, ret={"x": ["a", "b"]},
       tags=["collision"], visible=True,
       doc="Both keys shared a value, so both are kept, in insertion order."),
    _c("inverted_empty", "INVERTED", {}, ret={}, tags=["collision", "edge-values"]),
    _c("inverted_three_way", "INVERTED", {"a": "x", "b": "x", "c": "x"},
       ret={"x": ["a", "b", "c"]}, tags=["collision"],
       why="a two-way fix that overwrites on the third is a common half-fix"),

    _c("first_unique_basic", "FIRST_UNIQUE", "aabbc", ret="c",
       tags=["two-pass"], visible=True, doc="The first with a count of exactly one."),
    _c("first_unique_is_first", "FIRST_UNIQUE", "abb", ret="a", tags=["two-pass"],
       visible=True, doc="It can be the very first character."),
    _c("first_unique_none", "FIRST_UNIQUE", "aabb", ret=None,
       tags=["two-pass", "edge-values"], visible=True, doc="Every character repeats."),
    _c("first_unique_empty", "FIRST_UNIQUE", "", ret=None, tags=["two-pass", "edge-values"]),
    _c("first_unique_order_matters", "FIRST_UNIQUE", "bab", ret="a", tags=["two-pass"],
       why="the answer is in input order, not in the order the counts were built"),

    _c("subarray_basic", "SUBARRAY_SUM_COUNT", [1, 1, 1], 2, ret=2,
       tags=["checkpoint"], visible=True,
       doc="[1,1] at positions 0-1 and 1-2. Slices may overlap."),
    _c("subarray_with_zero_k", "SUBARRAY_SUM_COUNT", [1, -1, 0], 0, ret=3,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="[1,-1], [0] and [1,-1,0] all sum to 0. Negatives mean a running total can "
           "revisit a value, so a sliding window cannot do this."),
    _c("subarray_none", "SUBARRAY_SUM_COUNT", [1, 2], 7, ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("subarray_whole", "SUBARRAY_SUM_COUNT", [3], 3, ret=1, tags=["checkpoint"]),
    _c("subarray_empty", "SUBARRAY_SUM_COUNT", [], 0, ret=0,
       tags=["checkpoint", "edge-values"],
       why="the empty slice is not counted; there are no slices at all"),
    _c("subarray_repeated_prefix", "SUBARRAY_SUM_COUNT", [1, -1, 1, -1], 0, ret=4,
       tags=["checkpoint", "edge-values"],
       why="[1,-1] twice, [-1,1] once and the whole list -- the same running total recurs, "
           "so the count of each prefix matters, not merely whether it was seen"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="dicts",
    title="2.3 Dict",
    blurb="get, setdefault, defaultdict, Counter, merging, inverting and prefix sums.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="easy",
    topics=("default", "grouping", "counting"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.3 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
