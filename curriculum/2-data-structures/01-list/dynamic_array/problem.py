"""Dynamic array — the build exercise for unit 2.1.

What a Python list is, underneath. A fixed block of slots, a count of how many are used,
and a rule for what to do when they run out: allocate a proportionally larger block and
copy. Because the block grows by a FACTOR rather than by a constant, the copies get rarer as
the array grows and the average cost per append settles to a constant.

Being able to state that argument -- amortised O(1), worst case O(n) -- is the exercise.
The drill is arranged so the growth is observable, because otherwise nothing distinguishes
a correct implementation from `list.append`.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="APPEND", signature="(self, value: int) -> None", level=1,
           doc="Add a value at the end."),
    Method(display="GET", signature="(self, index: int) -> int | None", level=1,
           doc="The value at `index`, or None when the index is outside 0..size-1. "
               "Negative indices are outside."),
    Method(display="SET", signature="(self, index: int, value: int) -> bool", level=1,
           doc="Replace the value at `index`. False when the index is out of range."),
    Method(display="POP", signature="(self) -> int | None", level=1,
           doc="Remove and return the last value, or None when empty. Does NOT shrink "
               "the allocated block."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many values are held."),
    Method(display="CAPACITY", signature="(self) -> int", level=1,
           doc="How many slots are allocated. Starts at 0, and DOUBLES when a full array "
               "is appended to -- from 0 it becomes 1."),
    Method(display="ITEMS", signature="(self) -> list[int]", level=1,
           doc="The values held, in order. Never the unused slots."),
)

LEVELS = (Level(1, "Dynamic array", theme="grow by a factor, not by a step"),)

TAG_GLOSSARY = {
    "basics": "appending and indexing",
    "growth": "when the block is reallocated, and to what size",
    "bounds": "indices outside the used range",
    "shrink": "what pop does and does not do",
    "empty": "an array with nothing in it",
}

CASES = (
    case("append_and_index", 1, [
        op("APPEND", 10), op("APPEND", 20), op("GET", 0, ret=10), op("GET", 1, ret=20),
        op("SIZE", ret=2),
    ], tags=["basics"], visible=True, doc="In order, indexed from 0."),
    case("capacity_doubles", 1, [
        op("CAPACITY", ret=0), op("APPEND", 1), op("CAPACITY", ret=1),
        op("APPEND", 2), op("CAPACITY", ret=2), op("APPEND", 3), op("CAPACITY", ret=4),
        op("APPEND", 4), op("CAPACITY", ret=4), op("APPEND", 5), op("CAPACITY", ret=8),
    ], tags=["growth"], visible=True,
       doc="0, 1, 2, 4, 4, 8. The block only grows when it is FULL, and it doubles when "
           "it does -- which is what makes appending amortised O(1)."),
    case("size_and_capacity_differ", 1, [
        op("APPEND", 1), op("APPEND", 2), op("APPEND", 3), op("SIZE", ret=3),
        op("CAPACITY", ret=4), op("ITEMS", ret=[1, 2, 3]),
    ], tags=["growth"], visible=True,
       doc="Three values in four slots. ITEMS must report the used ones only, never the "
           "spare slot."),
    case("set_replaces", 1, [
        op("APPEND", 1), op("APPEND", 2), op("SET", 0, 9, ret=True),
        op("ITEMS", ret=[9, 2]), op("SIZE", ret=2),
    ], tags=["basics"], visible=True, doc="Replacing does not change the size."),
    case("out_of_range", 1, [
        op("APPEND", 1), op("GET", 1, ret=None), op("GET", 5, ret=None),
        op("SET", 1, 9, ret=False), op("ITEMS", ret=[1]),
    ], tags=["bounds"], visible=True,
       doc="Index 1 is out of range with one value held -- even though the block has a "
           "slot there. The used size is the bound, not the capacity."),
    case("negative_index", 1, [
        op("APPEND", 1), op("APPEND", 2), op("GET", -1, ret=None),
        op("SET", -1, 9, ret=False),
    ], tags=["bounds"], visible=True,
       doc="Negative indices are out of range here, not counted from the end."),
    case("pop_returns_last", 1, [
        op("APPEND", 1), op("APPEND", 2), op("POP", ret=2), op("SIZE", ret=1),
        op("ITEMS", ret=[1]), op("GET", 1, ret=None),
    ], tags=["shrink"], visible=True,
       doc="The popped slot is immediately out of range again."),
    case("pop_does_not_shrink", 1, [
        op("APPEND", 1), op("APPEND", 2), op("APPEND", 3), op("CAPACITY", ret=4),
        op("POP", ret=3), op("POP", ret=2), op("CAPACITY", ret=4),
    ], tags=["shrink", "growth"], visible=True,
       doc="The allocated block stays. Shrinking on every pop would make an "
           "append/pop/append cycle reallocate every time."),
    case("pop_empty", 1, [
        op("POP", ret=None), op("SIZE", ret=0), op("CAPACITY", ret=0),
    ], tags=["empty"], doc="Nothing to remove, and nothing allocated."),
    case("empty_reads", 1, [
        op("GET", 0, ret=None), op("SET", 0, 1, ret=False), op("ITEMS", ret=[]),
        op("SIZE", ret=0),
    ], tags=["empty", "bounds"]),
    case("refill_after_emptying", 1, [
        op("APPEND", 1), op("APPEND", 2), op("POP", ret=2), op("POP", ret=1),
        op("APPEND", 9), op("ITEMS", ret=[9]), op("CAPACITY", ret=2),
    ], tags=["shrink", "growth"],
       doc="Emptied and reused. The existing block is big enough, so nothing is "
           "reallocated."),
    case("value_zero", 1, [
        op("APPEND", 0), op("GET", 0, ret=0), op("ITEMS", ret=[0]),
    ], tags=["basics"], doc="A stored 0 must be distinguishable from an out-of-range read."),
    case("growth_from_one", 1, [
        op("APPEND", 1), op("CAPACITY", ret=1), op("APPEND", 2), op("CAPACITY", ret=2),
    ], tags=["growth"],
       doc="Doubling from 0 has to give 1, not 0. `capacity * 2` alone never leaves zero."),
)

PROBLEM = Problem(
    key="dynamic_array",
    title="Dynamic array",
    blurb="What a Python list is underneath: slots, a count, and growth by doubling.",
    class_name="DynamicArray",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("mutate", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.1 build exercise — see docs/CATALOGUE.md",
)
