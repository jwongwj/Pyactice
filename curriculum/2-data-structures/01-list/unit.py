"""2.1 List — the operations, and which end of the list they are cheap at.

Self-contained: loaded by file path, so no package-relative imports.

The catalogue's build exercise (a dynamic array with amortised growth) is a class, not a
one-function drill, so it lives outside this unit. What is here is the using half: the
mutating operations, and the three idioms that get reached for wrongly most often --
reversing, deduping and rotating.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall, RequireConstruct
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="INSERT_AT",
        signature="(items: list[int], index: int, value: int) -> list[int]",
        doc="`value` placed at `index`. An index past the end appends.",
        constraint_note="use list.insert; do not rebuild the list by slicing",
        constraints=(
            Forbid(("comprehension",),
                   because="insert shifts the tail for you, and says what you meant",
                   hint="items.insert(index, value), then return items"),
            RequireCall(("insert",), because="this drill is about list.insert"),
        ),
    ),
    Method(
        display="DROP_AT",
        signature="(items: list[int], index: int) -> list[int]",
        doc="The list without the item at `index`. Out of range leaves it unchanged.",
        constraint_note="guard the index, then use del or pop; no comprehension",
        constraints=(
            Forbid(("comprehension",),
                   because="removing by position is not a filter -- a filter would also "
                           "drop equal values elsewhere in the list",
                   hint="check 0 <= index < len(items), then del items[index]"),
        ),
    ),
    Method(
        display="DROP_VALUE",
        signature="(items: list[int], value: int) -> list[int]",
        doc="The list without the FIRST occurrence of `value`. Absent leaves it unchanged.",
        constraint_note="use list.remove and handle the absent case; no comprehension",
        constraints=(
            Forbid(("comprehension",),
                   because="a comprehension removes every occurrence, not the first",
                   hint="remove() raises ValueError when absent -- check first, or catch it"),
        ),
    ),
    Method(
        display="FLIPPED",
        signature="(items: list[int]) -> list[int]",
        doc="The same items, last to first.",
        # The point is the two-pointer swap, so the three one-liners that do it for you
        # are all closed off. This is the one drill in the unit where the loop IS the
        # lesson rather than the thing being replaced.
        # `Forbid(("subscript",))` was the first attempt and is self-contradictory: the
        # two-pointer swap this drill exists to teach is `items[i], items[j] = ...`,
        # which is two subscripts. Requiring the loop closes off the one-liners without
        # forbidding the answer.
        constraint_note="swap from both ends inwards; no reversed(), no .reverse()",
        constraints=(
            ForbidCall(("reversed", "reverse"),
                       because="a[::-1] and reversed() are the right answers in real code "
                               "and teach nothing about the two-pointer swap",
                       hint="i, j = 0, len(items) - 1 and swap while i < j"),
            RequireConstruct("while",
                             because="walking two indices towards each other is the point",
                             hint="while i < j: swap, then i += 1 and j -= 1"),
        ),
    ),
    Method(
        display="DEDUPED",
        signature="(items: list[int]) -> list[int]",
        doc="Duplicates removed, first occurrence kept, original order.",
        constraint_note="one pass with a set of what you have seen; no nested scan",
        constraints=(
            ForbidCall(("count", "index"),
                       because="calling count() or index() inside a loop is a second pass "
                               "per item, which makes an O(n) job O(n^2)",
                       hint="keep a `seen` set and test membership in it"),
        ),
    ),
    Method(
        display="ROTATED",
        signature="(items: list[int], k: int) -> list[int]",
        doc="Rotated RIGHT by k. k may exceed the length, and may be 0.",
        constraint_note="one modulo and two slices; no loop",
        constraints=(
            Forbid(("for", "while"),
                   because="rotation is two slices swapped, and k %= len handles k > len",
                   hint="k %= len(items), then items[-k:] + items[:-k] -- mind k == 0"),
        ),
    ),
    Method(
        display="MERGE_SORTED",
        fuzz=("sorted",),
        signature="(left: list[int], right: list[int]) -> list[int]",
        doc="One sorted list from two already-sorted lists. Keeps duplicates.",
        constraint_note="walk both with two indices; do not concatenate and sort",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="concatenating and re-sorting throws away the fact that both "
                               "inputs are already ordered, which is the whole point",
                       hint="two indices, take the smaller head each step, then append the rest"),
        ),
    ),
    Method(
        display="CHUNKED",
        signature="(items: list[int], size: int) -> list[list[int]]",
        doc="Split into consecutive chunks of `size`. The last chunk may be shorter.",
        constraint_note="one comprehension over a strided range",
        constraints=(
            RequireConstruct("comprehension",
                             because="range's third argument strides, so the chunk starts "
                                     "are range(0, len(items), size)",
                             hint="[items[i:i + size] for i in range(0, len(items), size)]"),
        ),
    ),
    Method(
        display="TOP_SCORES",
        signature="(rows: list[tuple[str, int]], n: int) -> list[str]",
        doc='Names of the n highest scores, highest first, ties broken by name ascending.',
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "List", theme="which end of a list each operation is cheap at"),)

TAG_GLOSSARY = {
    "mutate": "operations that change the list in place",
    "position": "indexing and bounds",
    "two-pointer": "walking a list from both ends, or two lists at once",
    "dedupe": "removing repeats",
    "slicing": "slice bounds, strides and negative indices",
    "ordering": "sort keys and tie-breaks",
    "edge-values": "empty inputs, single items, zero, out of range",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("insert_middle", "INSERT_AT", [1, 2, 3], 1, 9, ret=[1, 9, 2, 3],
       tags=["mutate", "position"], visible=True, doc="The tail shifts right."),
    _c("insert_front", "INSERT_AT", [1, 2], 0, 9, ret=[9, 1, 2], tags=["mutate", "position"]),
    _c("insert_past_end", "INSERT_AT", [1, 2], 7, 9, ret=[1, 2, 9],
       tags=["mutate", "position", "edge-values"], visible=True,
       doc="An index past the end appends rather than raising."),
    _c("insert_into_empty", "INSERT_AT", [], 0, 9, ret=[9],
       tags=["mutate", "edge-values"]),

    _c("drop_at_middle", "DROP_AT", [1, 2, 3], 1, ret=[1, 3],
       tags=["mutate", "position"], visible=True, doc="Only that position goes."),
    _c("drop_at_out_of_range", "DROP_AT", [1, 2], 5, ret=[1, 2],
       tags=["mutate", "position", "edge-values"], visible=True,
       doc="Out of range is not an error here: the list comes back unchanged."),
    # Found by tools/drill_mutation.py: with only `index=5, len=2` for the out-of-range
    # case, widening the guard to `index <= len(items)` survived, because 5 is out of
    # range under both readings. `index == len(items)` is the one value that separates
    # them, and it is the classic off-by-one on an upper bound.
    _c("drop_at_index_equals_length", "DROP_AT", [1, 2], 2, ret=[1, 2],
       tags=["mutate", "position", "edge-values"], visible=True,
       doc="An index of exactly len(items) is one past the last valid position, so the "
           "list comes back unchanged."),
    _c("drop_at_negative", "DROP_AT", [1, 2, 3], -1, ret=[1, 2, 3],
       tags=["mutate", "position", "edge-values"],
       why="a negative index is out of range for this drill, not a count from the end"),
    _c("drop_at_duplicate_value", "DROP_AT", [5, 5, 5], 0, ret=[5, 5],
       tags=["mutate", "position"],
       why="removing by position must not also drop the equal values elsewhere"),

    _c("drop_value_first", "DROP_VALUE", [1, 2, 1], 1, ret=[2, 1],
       tags=["mutate"], visible=True, doc="Only the first occurrence goes."),
    _c("drop_value_absent", "DROP_VALUE", [1, 2], 9, ret=[1, 2],
       tags=["mutate", "edge-values"], visible=True, doc="An absent value is not an error."),
    _c("drop_value_empty", "DROP_VALUE", [], 1, ret=[], tags=["mutate", "edge-values"]),
    _c("drop_value_zero", "DROP_VALUE", [0, 1, 0], 0, ret=[1, 0],
       tags=["mutate", "edge-values"], why="0 is a value to remove, not a missing argument"),

    _c("flipped_basic", "FLIPPED", [1, 2, 3], ret=[3, 2, 1],
       tags=["two-pointer"], visible=True, doc="Last to first."),
    _c("flipped_even", "FLIPPED", [1, 2, 3, 4], ret=[4, 3, 2, 1], tags=["two-pointer"],
       why="an even length has no middle item to leave alone"),
    _c("flipped_single", "FLIPPED", [7], ret=[7], tags=["two-pointer", "edge-values"]),
    _c("flipped_empty", "FLIPPED", [], ret=[], tags=["two-pointer", "edge-values"]),

    _c("deduped_basic", "DEDUPED", [1, 2, 1, 3, 2], ret=[1, 2, 3],
       tags=["dedupe"], visible=True, doc="First occurrence wins, order kept."),
    _c("deduped_all_same", "DEDUPED", [4, 4, 4], ret=[4], tags=["dedupe", "edge-values"]),
    _c("deduped_none", "DEDUPED", [3, 1, 2], ret=[3, 1, 2], tags=["dedupe"],
       why="nothing to remove must not reorder anything either"),
    _c("deduped_empty", "DEDUPED", [], ret=[], tags=["dedupe", "edge-values"]),

    _c("rotated_basic", "ROTATED", [1, 2, 3, 4, 5], 2, ret=[4, 5, 1, 2, 3],
       tags=["slicing"], visible=True, doc="Right by 2: the last two come to the front."),
    _c("rotated_zero", "ROTATED", [1, 2, 3], 0, ret=[1, 2, 3],
       tags=["slicing", "edge-values"], visible=True,
       doc="k of 0 returns the list unchanged."),
    _c("rotated_wraps", "ROTATED", [1, 2, 3], 5, ret=[2, 3, 1],
       tags=["slicing", "edge-values"], visible=True,
       doc="k may exceed the length: 5 on a list of 3 is a rotation by 2."),
    _c("rotated_full_turn", "ROTATED", [1, 2, 3], 3, ret=[1, 2, 3],
       tags=["slicing", "edge-values"], why="a full turn is the same as no turn"),
    _c("rotated_empty", "ROTATED", [], 2, ret=[], tags=["slicing", "edge-values"],
       why="an empty list has no length to take a modulo of"),

    _c("merge_interleaved", "MERGE_SORTED", [1, 4], [2, 3], ret=[1, 2, 3, 4],
       tags=["two-pointer"], visible=True, doc="Take the smaller head each step."),
    _c("merge_one_empty", "MERGE_SORTED", [], [1, 2], ret=[1, 2],
       tags=["two-pointer", "edge-values"], visible=True,
       doc="One side empty: the other is the answer."),
    _c("merge_duplicates", "MERGE_SORTED", [1, 2], [2, 2], ret=[1, 2, 2, 2],
       tags=["two-pointer"], why="duplicates are kept, not collapsed"),
    _c("merge_disjoint", "MERGE_SORTED", [5, 6], [1, 2], ret=[1, 2, 5, 6],
       tags=["two-pointer"],
       why="the tail of the longer remainder must be appended, not dropped"),
    _c("merge_both_empty", "MERGE_SORTED", [], [], ret=[],
       tags=["two-pointer", "edge-values"]),

    _c("chunked_even", "CHUNKED", [1, 2, 3, 4], 2, ret=[[1, 2], [3, 4]],
       tags=["slicing"], visible=True, doc="Consecutive chunks of 2."),
    _c("chunked_ragged", "CHUNKED", [1, 2, 3], 2, ret=[[1, 2], [3]],
       tags=["slicing", "edge-values"], visible=True,
       doc="The last chunk is short rather than padded."),
    _c("chunked_size_one", "CHUNKED", [1, 2], 1, ret=[[1], [2]], tags=["slicing"]),
    _c("chunked_bigger_than_list", "CHUNKED", [1, 2], 9, ret=[[1, 2]],
       tags=["slicing", "edge-values"],
       why="a size larger than the list is one short chunk, not an error"),
    _c("chunked_empty", "CHUNKED", [], 2, ret=[], tags=["slicing", "edge-values"]),

    _c("top_scores_basic", "TOP_SCORES", [("ada", 90), ("bob", 70), ("cyd", 80)], 2,
       ret=["ada", "cyd"], tags=["checkpoint", "ordering"], visible=True,
       doc="Highest first."),
    _c("top_scores_tie", "TOP_SCORES", [("zed", 90), ("ada", 90)], 2,
       ret=["ada", "zed"], tags=["checkpoint", "ordering"], visible=True,
       doc="Equal scores are ordered by name ascending -- so the tie-break runs the "
           "opposite way to the score."),
    _c("top_scores_n_bigger", "TOP_SCORES", [("ada", 5)], 9, ret=["ada"],
       tags=["checkpoint", "edge-values"],
       why="n larger than the input returns everything, not an error"),
    _c("top_scores_n_zero", "TOP_SCORES", [("ada", 5)], 0, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("top_scores_empty", "TOP_SCORES", [], 3, ret=[],
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="lists",
    title="2.1 List",
    blurb="Insert, remove, reverse, dedupe, rotate, merge and chunk.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="easy",
    topics=("mutate", "two-pointer", "slicing"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.1 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
