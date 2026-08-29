"""Union-Find — the build exercise for unit 2.12.

The unit's drills use the idea; this is the structure itself, with both optimisations. It
is worth building once because the two optimisations are the entire reason it is fast, and
because `find` returning the ROOT rather than the parent is the distinction the drills keep
depending on.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="RESET", signature="(self, size: int) -> None", level=1,
           doc="Start again with `size` members, numbered 0 to size-1, each alone. A size "
               "of 0 or less leaves no members at all."),
    # `opaque`: which member ends up as the root is the implementation's business, and
    # union by size and union by rank legitimately differ. The statement says so.
    Method(display="FIND", signature="(self, member: int) -> int", level=1,
           fuzz=("opaque",),
           doc="The root of the group `member` belongs to. A member outside 0..size-1 "
               "returns -1. A member is its own root until it is joined to something."),
    Method(display="UNION", signature="(self, a: int, b: int) -> bool", level=1,
           doc="Join two groups. True when they were separate and are now one; False when "
               "they were already together, or either member is out of range."),
    Method(display="CONNECTED", signature="(self, a: int, b: int) -> bool", level=1,
           doc="Are these two in the same group? False when either is out of range."),
    Method(display="GROUPS", signature="(self) -> int", level=1,
           doc="How many separate groups remain."),
    Method(display="GROUP_SIZE", signature="(self, member: int) -> int", level=1,
           doc="How many members share this one's group. 0 when out of range."),
)

LEVELS = (Level(1, "Union-Find", theme="find the root, not the parent"),)

TAG_GLOSSARY = {
    "basics": "a fresh structure, before anything is joined",
    "join": "merging two groups",
    "transitive": "membership that no single union created",
    "idempotent": "a union that changes nothing",
    "range": "members outside 0..size-1",
    "sizes": "the count per group, and the total",
}

CASES = (
    case("fresh_is_all_singletons", 1, [
        op("RESET", 3), op("GROUPS", ret=3), op("FIND", 1, ret=1), op("CONNECTED", 0, 1, ret=False),
        op("GROUP_SIZE", 0, ret=1),
    ], tags=["basics"], visible=True,
       doc="Everyone starts as their own root, in a group of one."),
    case("union_joins", 1, [
        op("RESET", 3), op("UNION", 0, 1, ret=True), op("CONNECTED", 0, 1, ret=True),
        op("GROUPS", ret=2), op("GROUP_SIZE", 0, ret=2),
    ], tags=["join"], visible=True, doc="Two become one, and the count drops."),
    case("union_twice_is_idempotent", 1, [
        op("RESET", 3), op("UNION", 0, 1, ret=True), op("UNION", 0, 1, ret=False), op("GROUPS", ret=2),
    ], tags=["idempotent"], visible=True,
       doc="The second union returns False and changes nothing. Decrementing the count "
           "regardless is the usual bug."),
    case("union_self_is_idempotent", 1, [
        op("RESET", 3), op("UNION", 1, 1, ret=False), op("GROUPS", ret=3),
    ], tags=["idempotent"], doc="A member is already joined to itself."),
    case("transitive_membership", 1, [
        op("RESET", 3), op("UNION", 0, 1, ret=True), op("UNION", 1, 2, ret=True),
        op("CONNECTED", 0, 2, ret=True), op("GROUPS", ret=1),
    ], tags=["transitive"], visible=True,
       doc="0 and 2 were never joined directly. Comparing parents rather than ROOTS "
           "answers False here."),
    # Deliberately NOT asserting which member is the root. Union by size and union by
    # rank pick different ones, and both are correct -- pinning a value here would fail a
    # perfectly good answer. What is testable is that they agree, which CONNECTED says.
    case("group_members_all_agree", 1, [
        op("RESET", 3), op("UNION", 0, 1, ret=True), op("UNION", 1, 2, ret=True),
        op("CONNECTED", 0, 1, ret=True), op("CONNECTED", 1, 2, ret=True),
        op("CONNECTED", 0, 2, ret=True),
    ], tags=["transitive"],
       doc="Every pair in one group is connected, whichever member ended up as the root."),
    case("union_two_groups", 1, [
        op("RESET", 4), op("UNION", 0, 1, ret=True), op("UNION", 2, 3, ret=True), op("GROUPS", ret=2),
        op("UNION", 1, 2, ret=True), op("GROUPS", ret=1), op("GROUP_SIZE", 3, ret=4),
    ], tags=["join", "sizes"],
       doc="Joining two groups that each already had members. The size is the total of "
           "both, which a size kept only on the member and not the root gets wrong."),
    case("out_of_range", 1, [
        op("RESET", 3), op("FIND", 9, ret=-1), op("UNION", 0, 9, ret=False), op("CONNECTED", 0, 9, ret=False),
        op("GROUP_SIZE", 9, ret=0), op("GROUPS", ret=3),
    ], tags=["range"], visible=True,
       doc="An unknown member joins nothing and belongs to no group."),
    case("negative_member", 1, [
        op("RESET", 4), op("FIND", -1, ret=-1), op("CONNECTED", -1, 0, ret=False),
    ], tags=["range"], doc="Negative indices are out of range, not counted from the end."),
    case("connected_to_self", 1, [
        op("RESET", 4), op("CONNECTED", 2, 2, ret=True),
    ], tags=["basics"], doc="A member is always in its own group."),
    case("sizes_stay_consistent", 1, [
        op("RESET", 3), op("UNION", 0, 1, ret=True), op("GROUP_SIZE", 0, ret=2), op("GROUP_SIZE", 1, ret=2),
        op("GROUP_SIZE", 2, ret=1),
    ], tags=["sizes"],
       doc="Both members of a group report the same size, and an untouched member is "
           "still alone."),
    # Both from `drill_mutation.py --triage`, which fuzzes SEQUENCES of calls for a
    # class. Every case here began with RESET, so nothing exercised a freshly built
    # instance -- and four separate mutants survived in that gap.
    case("before_any_reset", 1, [
        op("GROUPS", ret=0), op("FIND", 0, ret=-1), op("CONNECTED", 0, 1, ret=False),
        op("GROUP_SIZE", 0, ret=0), op("UNION", 0, 1, ret=False),
    ], tags=["basics", "range"], visible=True,
       doc="A structure that has never been reset holds no members at all, so every "
           "member is out of range."),
    case("union_where_a_root_is_one", 1, [
        op("RESET", 4), op("UNION", 1, 2, ret=True), op("UNION", 0, 1, ret=True),
        op("GROUPS", ret=2),
    ], tags=["join"], visible=True,
       doc="The second union joins a member to a group whose root is 1. A range check "
           "written against the wrong sentinel rejects it."),
    case("long_chain", 1, [
        op("RESET", 4), op("UNION", 0, 1, ret=True), op("UNION", 1, 2, ret=True),
        op("UNION", 2, 3, ret=True), op("UNION", 0, 3, ret=False),
        op("GROUPS", ret=1), op("GROUP_SIZE", 3, ret=4),
    ], tags=["transitive", "idempotent"],
       doc="A chain built one link at a time. The last union finds them already together."),
)

PROBLEM = Problem(
    key="union_find_structure",
    title="Union-Find",
    blurb="Disjoint sets with union by size and path compression.",
    class_name="UnionFind",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("union-find", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.12 build exercise — see docs/CATALOGUE.md",
)
