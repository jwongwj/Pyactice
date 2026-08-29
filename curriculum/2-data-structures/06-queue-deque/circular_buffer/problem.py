"""Circular buffer — the build exercise for unit 2.6.

A fixed-size queue that overwrites its oldest entry when full. The interesting part is that
it never allocates after construction: a head index, a tail index and modular arithmetic do
the work a growing list would.

The one decision that makes or breaks it: with head == tail, is the buffer empty or full?
The two states are indistinguishable from the indices alone, so something else has to
distinguish them.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="RESIZE", signature="(self, capacity: int) -> None", level=1,
           doc="Discard everything and start again with room for `capacity` values. A "
               "capacity of 0 or less holds nothing."),
    Method(display="WRITE", signature="(self, value: int) -> bool", level=1,
           doc="Add a value at the back. When the buffer is full this overwrites the "
               "OLDEST value. Returns True when nothing was overwritten, False when "
               "something was -- and False when the capacity is 0."),
    Method(display="READ", signature="(self) -> int | None", level=1,
           doc="Remove and return the oldest value, or None when empty."),
    Method(display="ITEMS", signature="(self) -> list[int]", level=1,
           doc="Everything held, oldest first, without removing anything."),
    Method(display="IS_FULL", signature="(self) -> bool", level=1,
           doc="Is the buffer at capacity? A capacity of 0 is always full."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many values are held."),
)

LEVELS = (Level(1, "Circular buffer", theme="empty and full look the same"),)

TAG_GLOSSARY = {
    "basics": "writing and reading in order",
    "wrap": "indices running past the end and round",
    "overwrite": "what happens when a full buffer is written to",
    "ambiguity": "telling empty from full",
    "capacity": "zero and negative capacities",
}

CASES = (
    case("write_then_read", 1, [
        op("RESIZE", 3), op("WRITE", 1, ret=True), op("WRITE", 2, ret=True),
        op("READ", ret=1), op("READ", ret=2), op("READ", ret=None),
    ], tags=["basics"], visible=True, doc="Oldest first, and empty afterwards."),
    case("items_does_not_consume", 1, [
        op("RESIZE", 3), op("WRITE", 1, ret=True), op("WRITE", 2, ret=True),
        op("ITEMS", ret=[1, 2]), op("ITEMS", ret=[1, 2]), op("SIZE", ret=2),
    ], tags=["basics"], doc="Reading the contents leaves them there."),
    case("fills_up", 1, [
        op("RESIZE", 2), op("IS_FULL", ret=False), op("WRITE", 1, ret=True),
        op("WRITE", 2, ret=True), op("IS_FULL", ret=True), op("SIZE", ret=2),
    ], tags=["ambiguity"],
       doc="Full when the count reaches the capacity."),
    case("overwrites_oldest", 1, [
        op("RESIZE", 2), op("WRITE", 1, ret=True), op("WRITE", 2, ret=True),
        op("WRITE", 3, ret=False), op("ITEMS", ret=[2, 3]), op("SIZE", ret=2),
    ], tags=["overwrite"], visible=True,
       doc="Writing to a full buffer drops the oldest value and reports False. The size "
           "does not grow."),
    case("empty_and_full_are_different", 1, [
        op("RESIZE", 2), op("WRITE", 1, ret=True), op("WRITE", 2, ret=True),
        op("READ", ret=1), op("READ", ret=2), op("IS_FULL", ret=False),
        op("SIZE", ret=0), op("ITEMS", ret=[]),
    ], tags=["ambiguity"], visible=True,
       doc="After filling and draining, the two indices have met again -- and the buffer "
           "is EMPTY, not full. Indices alone cannot tell these apart."),
    case("wraps_around", 1, [
        op("RESIZE", 3), op("WRITE", 1, ret=True), op("WRITE", 2, ret=True),
        op("WRITE", 3, ret=True), op("READ", ret=1), op("WRITE", 4, ret=True),
        op("ITEMS", ret=[2, 3, 4]),
    ], tags=["wrap"], visible=True,
       doc="The fourth write reuses the slot the first value left, so the write index "
           "runs past the end and back to 0."),
    case("overwrite_then_read_order", 1, [
        op("RESIZE", 2), op("WRITE", 1, ret=True), op("WRITE", 2, ret=True),
        op("WRITE", 3, ret=False), op("READ", ret=2), op("READ", ret=3),
        op("READ", ret=None),
    ], tags=["overwrite", "wrap"],
       doc="After an overwrite the read index must have moved too, or the discarded "
           "value comes back."),
    case("zero_capacity", 1, [
        op("RESIZE", 0), op("WRITE", 1, ret=False), op("SIZE", ret=0),
        op("IS_FULL", ret=True), op("READ", ret=None), op("ITEMS", ret=[]),
    ], tags=["capacity"], visible=True,
       doc="Nowhere to put anything: every write is refused and the buffer is always full."),
    case("negative_capacity", 1, [
        op("RESIZE", -2), op("WRITE", 1, ret=False), op("SIZE", ret=0),
    ], tags=["capacity"]),
    case("before_any_resize", 1, [
        op("SIZE", ret=0), op("READ", ret=None), op("ITEMS", ret=[]),
        op("WRITE", 1, ret=False), op("IS_FULL", ret=True),
    ], tags=["capacity"], visible=True,
       doc="A buffer that has never been sized holds nothing, exactly like one sized 0."),
    case("resize_discards", 1, [
        op("RESIZE", 3), op("WRITE", 1, ret=True), op("RESIZE", 3), op("SIZE", ret=0),
        op("ITEMS", ret=[]),
    ], tags=["capacity"], doc="Resizing starts again, even to the same capacity."),
    # From `drill_mutation.py --triage`: `resize_discards` resizes to the SAME capacity
    # with head still at 0, so nothing checked that resize resets the indices. Resizing
    # down after a read leaves a head pointing past the new end.
    case("resize_smaller_after_a_read", 1, [
        op("RESIZE", 3), op("WRITE", 1, ret=True), op("WRITE", 2, ret=True),
        op("READ", ret=1), op("RESIZE", 1), op("WRITE", 9, ret=True),
        op("ITEMS", ret=[9]), op("READ", ret=9), op("SIZE", ret=0),
    ], tags=["capacity", "wrap"], visible=True,
       doc="The read moved the head forward; resizing to a smaller capacity must put it "
           "back, or the next read indexes past the end of the new storage."),
    case("capacity_one", 1, [
        op("RESIZE", 1), op("WRITE", 1, ret=True), op("IS_FULL", ret=True),
        op("WRITE", 2, ret=False), op("ITEMS", ret=[2]), op("READ", ret=2),
        op("SIZE", ret=0),
    ], tags=["overwrite", "wrap"], visible=True,
       doc="A buffer of one is full after a single write, and every later write replaces "
           "what is there."),
    case("read_write_interleaved", 1, [
        op("RESIZE", 2), op("WRITE", 1, ret=True), op("READ", ret=1),
        op("WRITE", 2, ret=True), op("WRITE", 3, ret=True), op("ITEMS", ret=[2, 3]),
        op("IS_FULL", ret=True),
    ], tags=["wrap", "basics"],
       doc="Reading frees a slot, so the next two writes both fit."),
)

PROBLEM = Problem(
    key="circular_buffer",
    title="Circular buffer",
    blurb="A fixed-size queue that overwrites its oldest entry, with no allocation.",
    class_name="CircularBuffer",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("fifo", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.6 build exercise — see docs/CATALOGUE.md",
)
