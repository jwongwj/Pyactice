"""Queue from two stacks — the build exercise for unit 2.6.

A classic because the naive answer is O(n) per operation and the good one is O(1)
*amortised*, which is a different and more interesting claim. Values are moved from an
input stack to an output stack only when the output stack runs dry; each value is moved at
most once, so n operations cost O(n) in total even though one of them may cost O(n) alone.

Being able to state that argument is the exercise. The code is fifteen lines.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="ENQUEUE", signature="(self, value: int) -> None", level=1,
           doc="Add a value at the back."),
    Method(display="DEQUEUE", signature="(self) -> int | None", level=1,
           doc="Remove and return the value at the front, or None when empty."),
    Method(display="PEEK", signature="(self) -> int | None", level=1,
           doc="The value at the front without removing it, or None when empty."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many values are held."),
)

LEVELS = (Level(1, "Queue from two stacks", theme="amortised, not worst case"),)

TAG_GLOSSARY = {
    "fifo": "first-in first-out order",
    "transfer": "moving between the two stacks, and when",
    "interleaved": "adding while values are already waiting to come out",
    "empty": "operations on an empty queue",
}

CASES = (
    case("enqueue_then_dequeue", 1, [
        op("ENQUEUE", 1), op("ENQUEUE", 2), op("DEQUEUE", ret=1), op("DEQUEUE", ret=2),
    ], tags=["fifo"], visible=True, doc="First in, first out -- the opposite of a stack."),
    case("peek_does_not_remove", 1, [
        op("ENQUEUE", 5), op("PEEK", ret=5), op("PEEK", ret=5), op("SIZE", ret=1),
    ], tags=["fifo"], visible=True, doc="Peeking twice gives the same value."),
    case("interleaved_adds_and_removes", 1, [
        op("ENQUEUE", 1), op("ENQUEUE", 2), op("DEQUEUE", ret=1),
        op("ENQUEUE", 3), op("DEQUEUE", ret=2), op("DEQUEUE", ret=3),
    ], tags=["interleaved", "transfer"], visible=True,
       doc="A value added AFTER a transfer has begun must still come out last. Moving "
           "everything across on every dequeue gets this wrong."),
    case("empty_operations", 1, [
        op("DEQUEUE", ret=None), op("PEEK", ret=None), op("SIZE", ret=0),
    ], tags=["empty"], visible=True, doc="Empty answers None rather than raising."),
    case("drain_then_refill", 1, [
        op("ENQUEUE", 1), op("DEQUEUE", ret=1), op("DEQUEUE", ret=None),
        op("ENQUEUE", 2), op("DEQUEUE", ret=2),
    ], tags=["empty", "transfer"],
       doc="An emptied queue behaves like a fresh one."),
    case("size_counts_both_stacks", 1, [
        op("ENQUEUE", 1), op("ENQUEUE", 2), op("DEQUEUE", ret=1), op("SIZE", ret=1),
        op("ENQUEUE", 3), op("SIZE", ret=2),
    ], tags=["transfer"],
       doc="After a transfer the values live in two places, and size must count both."),
    case("peek_triggers_transfer", 1, [
        op("ENQUEUE", 1), op("ENQUEUE", 2), op("PEEK", ret=1), op("DEQUEUE", ret=1),
    ], tags=["transfer"], visible=True,
       doc="Peek has to see the front too, so it needs the same transfer as dequeue."),
    case("many_then_drain", 1, [
        op("ENQUEUE", 1), op("ENQUEUE", 2), op("ENQUEUE", 3),
        op("DEQUEUE", ret=1), op("DEQUEUE", ret=2), op("DEQUEUE", ret=3),
        op("DEQUEUE", ret=None), op("SIZE", ret=0),
    ], tags=["fifo", "transfer"]),
    case("duplicates_kept", 1, [
        op("ENQUEUE", 7), op("ENQUEUE", 7), op("DEQUEUE", ret=7), op("SIZE", ret=1),
    ], tags=["fifo"], doc="Equal values are two values."),
    case("negatives_and_zero", 1, [
        op("ENQUEUE", 0), op("ENQUEUE", -1), op("PEEK", ret=0), op("DEQUEUE", ret=0),
        op("PEEK", ret=-1),
    ], tags=["fifo"], doc="0 is a value, not an absence."),
    case("transfer_only_when_dry", 1, [
        op("ENQUEUE", 1), op("DEQUEUE", ret=1), op("ENQUEUE", 2), op("ENQUEUE", 3),
        op("DEQUEUE", ret=2), op("ENQUEUE", 4), op("DEQUEUE", ret=3),
        op("DEQUEUE", ret=4),
    ], tags=["interleaved", "transfer"],
       doc="Repeated interleaving. Transferring while the output stack still holds "
           "values reverses part of the queue."),
)

PROBLEM = Problem(
    key="two_stack_queue",
    title="Queue from two stacks",
    blurb="A FIFO queue built from two LIFO stacks, O(1) amortised.",
    class_name="TwoStackQueue",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("fifo", "amortised"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.6 build exercise — see docs/CATALOGUE.md",
)
