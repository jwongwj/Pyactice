"""MinStack — the build exercise for unit 2.5.

A stack that also answers "what is the smallest thing in here" in O(1). The naive answer
scans on every call and is O(n); the intended one keeps a second stack of the minimum as
it stood at each depth, so popping restores the previous minimum for free.

That second stack is the whole idea, and it generalises: whenever an aggregate has to
survive a pop, store the aggregate alongside the value rather than recomputing it.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="PUSH", signature="(self, value: int) -> None", level=1,
           doc="Put a value on top."),
    Method(display="POP", signature="(self) -> int | None", level=1,
           doc="Remove and return the top value, or None when empty."),
    Method(display="TOP", signature="(self) -> int | None", level=1,
           doc="The top value without removing it, or None when empty."),
    Method(display="GET_MIN", signature="(self) -> int | None", level=1,
           doc="The smallest value currently held, or None when empty. Must not scan."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many values are held."),
)

LEVELS = (Level(1, "MinStack", theme="an aggregate that survives a pop"),)

TAG_GLOSSARY = {
    "basics": "ordinary pushes and pops",
    "minimum": "the tracked minimum, and what happens when it leaves",
    "duplicates": "equal values, where a careless minimum stack loses one",
    "empty": "operations on an empty stack",
    "ordering": "LIFO order itself",
}

CASES = (
    case("push_and_top", 1, [
        op("PUSH", 3), op("PUSH", 5), op("TOP", ret=5), op("SIZE", ret=2),
    ], tags=["basics", "ordering"], visible=True,
       doc="The last value pushed is on top."),
    case("pop_returns_and_removes", 1, [
        op("PUSH", 1), op("PUSH", 2), op("POP", ret=2), op("TOP", ret=1), op("SIZE", ret=1),
    ], tags=["basics", "ordering"], visible=True, doc="Last in, first out."),
    case("min_tracks_pushes", 1, [
        op("PUSH", 5), op("GET_MIN", ret=5), op("PUSH", 3), op("GET_MIN", ret=3),
        op("PUSH", 7), op("GET_MIN", ret=3),
    ], tags=["minimum"], visible=True,
       doc="A larger value does not change the minimum."),
    case("min_restored_after_pop", 1, [
        op("PUSH", 5), op("PUSH", 3), op("POP", ret=3), op("GET_MIN", ret=5),
    ], tags=["minimum"], visible=True,
       doc="Popping the minimum must restore the previous one. This is the case a single "
           "`self.minimum` variable cannot answer."),
    case("min_with_duplicates", 1, [
        op("PUSH", 2), op("PUSH", 2), op("POP", ret=2), op("GET_MIN", ret=2),
    ], tags=["minimum", "duplicates"], visible=True,
       doc="Two equal minima. Pushing onto the minimum stack only when STRICTLY smaller "
           "loses one of them, and the minimum wrongly disappears here."),
    case("min_after_all_popped", 1, [
        op("PUSH", 4), op("POP", ret=4), op("GET_MIN", ret=None), op("TOP", ret=None),
        op("SIZE", ret=0),
    ], tags=["minimum", "empty"],
       doc="an emptied stack is the same as a fresh one"),
    case("empty_operations", 1, [
        op("POP", ret=None), op("TOP", ret=None), op("GET_MIN", ret=None), op("SIZE", ret=0),
    ], tags=["empty"], visible=True,
       doc="Every accessor answers None rather than raising."),
    case("negatives_and_zero", 1, [
        op("PUSH", 0), op("PUSH", -2), op("GET_MIN", ret=-2), op("POP", ret=-2),
        op("GET_MIN", ret=0),
    ], tags=["minimum"], doc="0 is a value, not an absence."),
    case("interleaved", 1, [
        op("PUSH", 3), op("PUSH", 1), op("PUSH", 2), op("GET_MIN", ret=1),
        op("POP", ret=2), op("GET_MIN", ret=1), op("POP", ret=1), op("GET_MIN", ret=3),
    ], tags=["minimum", "ordering"],
       doc="the minimum changes back only when the value holding it leaves"),
    case("many_pushes_one_min", 1, [
        op("PUSH", 9), op("PUSH", 8), op("PUSH", 7), op("PUSH", 1),
        op("GET_MIN", ret=1), op("POP", ret=1), op("GET_MIN", ret=7),
    ], tags=["minimum"]),
    case("push_after_empty", 1, [
        op("PUSH", 1), op("POP", ret=1), op("PUSH", 5), op("GET_MIN", ret=5),
    ], tags=["empty", "minimum"],
       doc="a stale minimum from before the stack emptied must not survive"),
    case("size_tracks", 1, [
        op("SIZE", ret=0), op("PUSH", 1), op("SIZE", ret=1), op("PUSH", 2),
        op("SIZE", ret=2), op("POP", ret=2), op("SIZE", ret=1),
    ], tags=["basics"]),
)

PROBLEM = Problem(
    key="min_stack",
    title="MinStack",
    blurb="A stack that also reports its smallest value in constant time.",
    class_name="MinStack",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("stack", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.5 build exercise — see docs/CATALOGUE.md",
)
