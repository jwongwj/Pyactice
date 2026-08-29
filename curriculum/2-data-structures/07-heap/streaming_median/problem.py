"""Streaming median — the build exercise for unit 2.7.

Two heaps facing each other: a max-heap of the smaller half and a min-heap of the larger
half. The median is then always at one or both of their tops, and every insertion is
O(log n) instead of the O(n log n) a re-sort would cost.

The whole difficulty is the invariant -- which half a new value belongs to, and how the
sizes are kept within one of each other. Get that written down before writing code.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="ADD", signature="(self, value: int) -> None", level=1,
           doc="Add a value to the stream."),
    Method(display="MEDIAN", signature="(self) -> int | None", level=1,
           doc="The median of everything added so far, using integer division towards "
               "negative infinity for an even count. None when nothing has been added."),
    Method(display="LOWER_HALF_SIZE", signature="(self) -> int", level=1,
           doc="How many values are at or below the median -- the size of the lower "
               "structure. With an odd count this is the larger half by one."),
    Method(display="COUNT", signature="(self) -> int", level=1,
           doc="How many values have been added."),
    Method(display="SMALLEST", signature="(self) -> int | None", level=1,
           doc="The smallest value added, or None when nothing has been. Must not scan "
               "the whole stream."),
)

LEVELS = (Level(1, "Streaming median", theme="two heaps facing each other"),)

TAG_GLOSSARY = {
    "basics": "adding and reading the median",
    "parity": "odd and even counts, which differ",
    "balance": "keeping the two halves within one of each other",
    "rebalance": "a value that belongs in the other half",
    "empty": "before anything has been added",
    "negatives": "negative values and zero",
}

CASES = (
    case("single_value", 1, [
        op("ADD", 5), op("MEDIAN", ret=5), op("COUNT", ret=1),
        op("LOWER_HALF_SIZE", ret=1),
    ], tags=["basics", "parity"], visible=True,
       doc="One value is its own median, and it sits in the lower half."),
    case("two_values_average", 1, [
        op("ADD", 1), op("ADD", 3), op("MEDIAN", ret=2), op("LOWER_HALF_SIZE", ret=1),
    ], tags=["parity"],
       doc="An even count averages the two middles, and the halves are equal in size."),
    case("three_values", 1, [
        op("ADD", 1), op("ADD", 3), op("ADD", 2), op("MEDIAN", ret=2),
        op("LOWER_HALF_SIZE", ret=2),
    ], tags=["parity", "balance"], visible=True,
       doc="An odd count takes the middle, and the lower half is the larger by one."),
    case("descending_input", 1, [
        op("ADD", 5), op("ADD", 4), op("ADD", 3), op("ADD", 2), op("MEDIAN", ret=3),
    ], tags=["rebalance"], visible=True,
       doc="Every value belongs in the LOWER half when it arrives, so every insertion "
           "forces a rebalance. Adding to whichever heap is smaller without comparing "
           "gets this wrong."),
    case("ascending_input", 1, [
        op("ADD", 1), op("ADD", 2), op("ADD", 3), op("ADD", 4), op("MEDIAN", ret=2),
    ], tags=["rebalance"], visible=True,
       doc="The mirror: everything belongs in the upper half. Note 2 and not 3 -- "
           "integer division of 2+3 rounds down."),
    case("even_negative_average", 1, [
        op("ADD", -3), op("ADD", -2), op("MEDIAN", ret=-3),
    ], tags=["parity", "negatives"], visible=True,
       doc="-3 + -2 is -5, and integer division towards negative infinity gives -3. "
           "Truncating towards zero would give -2."),
    case("empty", 1, [
        op("MEDIAN", ret=None), op("COUNT", ret=0), op("LOWER_HALF_SIZE", ret=0),
        op("SMALLEST", ret=None),
    ], tags=["empty"], visible=True, doc="Nothing added yet."),
    case("duplicates", 1, [
        op("ADD", 2), op("ADD", 2), op("ADD", 2), op("MEDIAN", ret=2), op("COUNT", ret=3),
    ], tags=["basics"], doc="Equal values are separate values."),
    # From `drill_mutation.py --triage`: reading `lower[-1]` instead of `lower[0]` picks
    # an arbitrary heap element rather than the top. It happens to coincide on every
    # other case here; four values with a repeat separates them.
    case("even_count_with_duplicates", 1, [
        op("ADD", 1), op("ADD", 2), op("ADD", 2), op("ADD", 2),
        op("MEDIAN", ret=2), op("COUNT", ret=4), op("LOWER_HALF_SIZE", ret=2),
    ], tags=["parity", "balance"], visible=True,
       doc="Four values, three of them equal. The median is read from the TOP of each "
           "half; any other position in a heap is arbitrary."),
    case("smallest_tracks", 1, [
        op("ADD", 5), op("SMALLEST", ret=5), op("ADD", 2), op("SMALLEST", ret=2),
        op("ADD", 9), op("SMALLEST", ret=2),
    ], tags=["basics"],
       doc="The smallest lives at the bottom of the lower half, which is not the top of "
           "either heap -- so it needs its own tracking or a walk of one heap."),
    case("zero_included", 1, [
        op("ADD", 0), op("MEDIAN", ret=0), op("SMALLEST", ret=0),
    ], tags=["negatives", "empty"],
       doc="0 is a value; using falsiness to mean 'nothing added' gets this wrong."),
    case("interleaved_reads", 1, [
        op("ADD", 1), op("MEDIAN", ret=1), op("ADD", 2), op("MEDIAN", ret=1),
        op("ADD", 3), op("MEDIAN", ret=2), op("ADD", 4), op("MEDIAN", ret=2),
        op("ADD", 5), op("MEDIAN", ret=3),
    ], tags=["parity", "balance"], visible=True,
       doc="The median after every insertion. Reading must not disturb the heaps."),
    case("large_then_small", 1, [
        op("ADD", 100), op("ADD", 1), op("MEDIAN", ret=50), op("LOWER_HALF_SIZE", ret=1),
        op("ADD", 50), op("MEDIAN", ret=50),
    ], tags=["rebalance", "balance"],
       doc="100 arrives first and must move to the upper half once 1 arrives."),
    case("balance_never_off_by_two", 1, [
        op("ADD", 1), op("ADD", 2), op("ADD", 3), op("ADD", 4), op("ADD", 5),
        op("LOWER_HALF_SIZE", ret=3), op("COUNT", ret=5),
    ], tags=["balance"],
       doc="Five values split three and two, never four and one."),
)

PROBLEM = Problem(
    key="streaming_median",
    title="Streaming median",
    blurb="The median of a growing stream, in O(log n) per value, using two heaps.",
    class_name="StreamingMedian",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="hard",
    topics=("top-n", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.7 build exercise — see docs/CATALOGUE.md",
)
