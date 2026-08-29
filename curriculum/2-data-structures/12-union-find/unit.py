"""2.12 Union-Find — the structure for "are these two in the same group yet?"

Self-contained: loaded by file path, so no package-relative imports.

Union-Find earns its place when connections arrive one at a time and you have to answer
connectivity questions as they do. A traversal answers "what is connected" for a graph you
already have; union-find answers it for a graph still being built, without re-traversing
after every edge.

Number of islands is deliberately here as well as under DFS in the catalogue: seeing that
one problem has two correct algorithms is a separate skill from knowing either.

The catalogue's build exercise -- the structure itself, with union by rank and path
compression -- is a class, so it arrives as a `design` problem. These drills use the idea
without asking you to package it.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="GROUP_COUNT",
        signature="(size: int, pairs: list[tuple[int, int]]) -> int",
        doc="Members are 0..size-1, each starting alone. Each pair joins two members' "
            "groups. A pair naming a member outside the range is ignored. How many groups "
            "remain. 0 when size is 0 or less.",
        constraint_note="union-find: a parent array, find with compression, union on join",
        constraints=(
            Forbid(("recursion",),
                   because="the recursive find is the textbook one and blows the stack on "
                           "a long chain, which is exactly what an uncompressed union-find "
                           "produces",
                   hint="start the count at `size` and decrement only when a union "
                        "actually joins two DIFFERENT groups"),
        ),
    ),
    Method(
        display="SAME_GROUP",
        signature="(size: int, pairs: list[tuple[int, int]], a: int, b: int) -> bool",
        doc="After applying every pair, are `a` and `b` in the same group? A member is "
            "always in its own group. Pairs naming a member outside 0..size-1 are ignored. "
            "False when `a` or `b` is itself outside the range.",
        constraint_note="compare roots, not parents -- two members can share a group "
                        "without sharing a parent",
        constraints=(
            Forbid(("recursion",),
                   because="the same stack argument as GROUP_COUNT",
                   hint="find(a) == find(b), where find walks to the root"),
        ),
    ),
    Method(
        display="REDUNDANT_EDGE",
        signature="(edges: list[tuple[int, int]]) -> tuple[int, int] | None",
        doc="The FIRST edge whose two ends were already connected, or None if none is. "
            "Members are whatever integers appear in the edges.",
        constraint_note="an edge is redundant exactly when union finds both ends already "
                        "joined",
        constraints=(
            Forbid(("recursion",),
                   because="the same stack argument, and the answer falls straight out of "
                           "the union step rather than needing a search",
                   hint="walk the edges in order; the first union that finds equal roots "
                        "is the answer"),
        ),
    ),
    Method(
        display="ISLANDS",
        fuzz=("grid",),
        signature="(grid: list[list[int]]) -> int",
        doc="How many groups of horizontally or vertically adjacent 1s the grid holds. "
            "Diagonals do not connect. 0 for an empty grid.",
        # Union-find and a flood fill both answer this, which is the point of including it.
        constraint_note="either union-find over the cells or a flood fill; not recursion",
        constraints=(
            Forbid(("recursion",),
                   because="a 200x200 grid of all 1s recurses forty thousand deep and the "
                           "stack gives out -- the flood fill has to be iterative",
                   hint="union each 1 with the 1 above and the 1 to its left, or push "
                        "neighbours onto an explicit stack"),
        ),
    ),
    Method(
        display="ACCOUNTS_MERGE",
        signature="(accounts: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]",
        doc="Each account is (owner, emails). Two accounts belong to the same person when "
            "they share any email. Merge them: one entry per person, emails deduplicated "
            "and sorted ascending. Result sorted by owner then by first email. An account "
            "with no emails merges with nothing and is kept as it is.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Union-Find", theme="connectivity while the graph is still arriving"),)

TAG_GLOSSARY = {
    "join": "merging two groups",
    "query": "asking whether two members are connected",
    "redundant": "an edge that connects nothing new",
    "grid": "connectivity over cells rather than an edge list",
    "edge-values": "empty inputs, self-pairs, repeated pairs, out-of-range members",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("groups_none_joined", "GROUP_COUNT", 3, [], ret=3,
       tags=["join"], visible=True, doc="Everyone starts alone."),
    _c("groups_one_join", "GROUP_COUNT", 3, [(0, 1)], ret=2,
       tags=["join"], visible=True, doc="Two become one."),
    _c("groups_chain", "GROUP_COUNT", 4, [(0, 1), (1, 2), (2, 3)], ret=1,
       tags=["join"], visible=True, doc="A chain joins everything into one."),
    _c("groups_repeated_pair", "GROUP_COUNT", 3, [(0, 1), (0, 1)], ret=2,
       tags=["join", "edge-values"], visible=True,
       doc="The second join changes nothing, so the count must not drop twice."),
    _c("groups_self_pair", "GROUP_COUNT", 2, [(0, 0)], ret=2,
       tags=["join", "edge-values"], why="joining a member to itself joins nothing"),
    _c("groups_transitive", "GROUP_COUNT", 4, [(0, 1), (2, 3), (1, 2)], ret=1,
       tags=["join"],
       why="the third pair joins two groups that each already had two members"),
    # From `drill_mutation.py --triage`: with sizes of 3, 4, 2, 0 and -2 and no 1, a
    # guard widened to `size <= 1` passed every case.
    _c("groups_single_member", "GROUP_COUNT", 1, [], ret=1,
       tags=["join", "edge-values"], visible=True,
       doc="One member is one group, which the empty-input guard must not swallow."),
    _c("groups_out_of_range_pair", "GROUP_COUNT", 2, [(0, 5)], ret=2,
       tags=["join", "edge-values"], visible=True,
       doc="A pair naming a member that does not exist joins nothing."),
    _c("groups_zero_size", "GROUP_COUNT", 0, [], ret=0, tags=["join", "edge-values"]),
    _c("groups_negative_size", "GROUP_COUNT", -2, [], ret=0,
       tags=["join", "edge-values"]),

    _c("same_direct", "SAME_GROUP", 3, [(0, 1)], 0, 1, ret=True,
       tags=["query"], visible=True, doc="Joined directly."),
    _c("same_transitive", "SAME_GROUP", 3, [(0, 1), (1, 2)], 0, 2, ret=True,
       tags=["query"], visible=True,
       doc="0 and 2 were never paired with each other, and are in the same group. "
           "Comparing parents rather than roots gets this wrong."),
    _c("same_not_joined", "SAME_GROUP", 3, [(0, 1)], 0, 2, ret=False,
       tags=["query"], visible=True, doc="Different groups."),
    _c("same_itself", "SAME_GROUP", 2, [], 1, 1, ret=True,
       tags=["query", "edge-values"], why="a member is always in its own group"),
    _c("same_out_of_range", "SAME_GROUP", 2, [], 0, 9, ret=False,
       tags=["query", "edge-values"], visible=True,
       doc="A member outside the range is not in any group, so the answer is False "
           "rather than an error."),
    # Also from triage: every query here used member 1 or above, so widening the lower
    # bound to `0 < a` passed them all; and no query used an index of exactly `size`,
    # so widening the upper bound to `b <= size` did too.
    _c("same_member_zero", "SAME_GROUP", 3, [(0, 1)], 0, 0, ret=True,
       tags=["query", "edge-values"], visible=True,
       doc="Member 0 is a real member, and is in its own group."),
    _c("same_index_equals_size", "SAME_GROUP", 2, [], 0, 2, ret=False,
       tags=["query", "edge-values"], visible=True,
       doc="Members run 0..size-1, so an index of exactly `size` is outside the range."),
    # The mirrors of the two cases above. Triage found both: the range guard has two
    # halves and two arguments, and testing the boundary on `b` alone leaves the `a` half
    # of the guard free to be wrong. Symmetric arguments need symmetric cases -- the same
    # blind spot as the left/right one in unit 2.8's merge.
    _c("same_first_index_equals_size", "SAME_GROUP", 2, [], 2, 0, ret=False,
       tags=["query", "edge-values"],
       why="the boundary applies to the first argument as much as the second"),
    _c("same_second_negative", "SAME_GROUP", 2, [], 0, -1, ret=False,
       tags=["query", "edge-values"],
       why="and so does the lower bound"),
    _c("same_out_of_range_pair", "SAME_GROUP", 2, [(0, 5)], 0, 1, ret=False,
       tags=["query", "edge-values"],
       why="the pair is ignored, so 0 and 1 were never actually joined"),
    _c("same_negative", "SAME_GROUP", 2, [], -1, 0, ret=False,
       tags=["query", "edge-values"]),

    _c("redundant_found", "REDUNDANT_EDGE", [(0, 1), (1, 2), (0, 2)], ret=(0, 2),
       tags=["redundant"], visible=True,
       doc="0 and 2 are already connected through 1 by the time the third edge arrives."),
    _c("redundant_none", "REDUNDANT_EDGE", [(0, 1), (1, 2)], ret=None,
       tags=["redundant"], visible=True, doc="A tree has no redundant edge."),
    _c("redundant_first_of_several", "REDUNDANT_EDGE",
       [(0, 1), (1, 0), (2, 3), (3, 2)], ret=(1, 0),
       tags=["redundant"], visible=True,
       doc="Two edges are redundant and the FIRST one is the answer."),
    _c("redundant_self_loop", "REDUNDANT_EDGE", [(5, 5)], ret=(5, 5),
       tags=["redundant", "edge-values"],
       why="both ends of a self-loop are already connected, trivially"),
    _c("redundant_empty", "REDUNDANT_EDGE", [], ret=None,
       tags=["redundant", "edge-values"]),
    _c("redundant_disjoint", "REDUNDANT_EDGE", [(0, 1), (2, 3)], ret=None,
       tags=["redundant", "edge-values"]),

    _c("islands_one", "ISLANDS", [[1, 1], [0, 1]], ret=1,
       tags=["grid"], visible=True, doc="All three 1s touch."),
    _c("islands_two", "ISLANDS", [[1, 0], [0, 1]], ret=2,
       tags=["grid"], visible=True,
       doc="Diagonally adjacent does NOT connect, so these are two islands."),
    _c("islands_none", "ISLANDS", [[0, 0], [0, 0]], ret=0,
       tags=["grid", "edge-values"], visible=True, doc="No land at all."),
    _c("islands_all", "ISLANDS", [[1, 1], [1, 1]], ret=1, tags=["grid"]),
    _c("islands_empty", "ISLANDS", [], ret=0, tags=["grid", "edge-values"]),
    _c("islands_single_row", "ISLANDS", [[1, 0, 1]], ret=2, tags=["grid", "edge-values"]),
    _c("islands_u_shape", "ISLANDS", [[1, 0, 1], [1, 1, 1]], ret=1,
       tags=["grid"], visible=True,
       doc="The two columns join along the bottom, so it is one island -- a walk that "
           "only looks up and left per cell must still union them."),

    _c("accounts_merge_two", "ACCOUNTS_MERGE",
       [("ada", ["a@x", "b@x"]), ("ada", ["b@x", "c@x"])],
       ret=[("ada", ["a@x", "b@x", "c@x"])], tags=["checkpoint"], visible=True,
       doc="The shared b@x proves these are one person."),
    _c("accounts_same_name_different_people", "ACCOUNTS_MERGE",
       [("ada", ["a@x"]), ("ada", ["z@x"])],
       ret=[("ada", ["a@x"]), ("ada", ["z@x"])], tags=["checkpoint"], visible=True,
       doc="The same owner name is NOT evidence: with no shared email these stay two "
           "entries, ordered by their first email."),
    _c("accounts_transitive", "ACCOUNTS_MERGE",
       [("bob", ["a@x"]), ("bob", ["c@x"]), ("bob", ["a@x", "c@x"])],
       ret=[("bob", ["a@x", "c@x"])], tags=["checkpoint"], visible=True,
       doc="The third account links the first two, which shared nothing directly."),
    _c("accounts_no_emails", "ACCOUNTS_MERGE", [("cyd", [])], ret=[("cyd", [])],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="An account with no emails can merge with nothing and is kept as it is."),
    _c("accounts_empty", "ACCOUNTS_MERGE", [], ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("accounts_sorted_by_owner", "ACCOUNTS_MERGE",
       [("zed", ["z@x"]), ("ada", ["a@x"])],
       ret=[("ada", ["a@x"]), ("zed", ["z@x"])], tags=["checkpoint"],
       why="the result is sorted by owner, not left in input order"),
    _c("accounts_duplicate_emails", "ACCOUNTS_MERGE", [("ada", ["b@x", "a@x", "b@x"])],
       ret=[("ada", ["a@x", "b@x"])], tags=["checkpoint", "edge-values"],
       why="emails are deduplicated and sorted within one account too"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="union_find",
    title="2.12 Union-Find",
    blurb="Group counting, connectivity queries, redundant edges, islands and merging.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="hard",
    topics=("join", "query", "grid"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.12 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
