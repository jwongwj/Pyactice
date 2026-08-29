"""Serialise and deserialise a tree — the build exercise for unit 2.9.

Turning a tree into a string and back. The interesting constraint is that the string must
capture the SHAPE, not only the values: an in-order walk of a binary tree is famously
ambiguous, because several different trees produce the same one.

Pre-order with explicit markers for absent children is unambiguous, and rebuilding from it
is one pass -- which is why it is the encoding worth knowing.
"""

from __future__ import annotations

from harness.model import KIND_DESIGN, Level, Method, Problem, case, op

METHODS = (
    Method(display="BUILD", signature="(self, values: list[int | None]) -> None", level=1,
           doc="Replace the tree with one built from a LEVEL-ORDER list, where None means "
               "an absent child. An empty list, or one starting with None, gives an empty "
               "tree."),
    Method(display="ENCODE", signature="(self) -> str", level=1,
           doc="The tree as a string: pre-order -- node, left, right -- with values "
               "separated by commas and an absent child written as `#`. An empty tree "
               "encodes as `#`."),
    Method(display="DECODE", signature="(self, text: str) -> bool", level=1,
           doc="Replace the tree with one rebuilt from that encoding. False when the text "
               "is not a valid encoding, in which case the tree is left EMPTY."),
    Method(display="PRE_ORDER", signature="(self) -> list[int]", level=1,
           doc="The values, node before children -- so the encoding without its markers."),
    Method(display="IN_ORDER", signature="(self) -> list[int]", level=1,
           doc="The values, left before node before right."),
    Method(display="SIZE", signature="(self) -> int", level=1,
           doc="How many nodes the tree holds."),
)

LEVELS = (Level(1, "Tree codec", theme="the shape has to survive the round trip"),)

TAG_GLOSSARY = {
    "round-trip": "encode then decode giving the same tree",
    "markers": "absent children, and why they are needed",
    "ambiguity": "different trees that would otherwise encode the same",
    "invalid": "text that is not a valid encoding",
    "empty": "the empty tree, at both ends",
}

CASES = (
    case("encode_simple", 1, [
        op("BUILD", [1, 2, 3]), op("ENCODE", ret="1,2,#,#,3,#,#"),
    ], tags=["markers"], visible=True,
       doc="Pre-order with a marker for every absent child, including the leaves'."),
    case("encode_empty", 1, [
        op("ENCODE", ret="#"), op("SIZE", ret=0),
    ], tags=["empty"], doc="An empty tree is a single marker."),
    case("round_trip", 1, [
        op("BUILD", [1, 2, 3]), op("ENCODE", ret="1,2,#,#,3,#,#"),
        op("DECODE", "1,2,#,#,3,#,#", ret=True), op("PRE_ORDER", ret=[1, 2, 3]),
        op("IN_ORDER", ret=[2, 1, 3]), op("SIZE", ret=3),
    ], tags=["round-trip"], visible=True, doc="Out and back, unchanged."),
    case("shape_survives_a_left_chain", 1, [
        op("BUILD", [1, 2, None, 3]), op("ENCODE", ret="1,2,3,#,#,#,#"),
        op("IN_ORDER", ret=[3, 2, 1]),
    ], tags=["ambiguity", "markers"], visible=True,
       doc="A tree leaning entirely left."),
    case("shape_survives_a_right_chain", 1, [
        op("BUILD", [1, None, 2, None, 3]),
        op("ENCODE", ret="1,#,2,#,3,#,#"), op("IN_ORDER", ret=[1, 2, 3]),
    ], tags=["ambiguity", "markers"], visible=True,
       doc="A tree leaning entirely right. Its IN-ORDER is [1,2,3] -- exactly the same as "
           "a balanced tree's would be, which is why in-order alone cannot be an "
           "encoding. The pre-order form distinguishes them."),
    case("decode_rebuilds_shape", 1, [
        op("DECODE", "1,#,2,#,3,#,#", ret=True), op("PRE_ORDER", ret=[1, 2, 3]),
        op("IN_ORDER", ret=[1, 2, 3]), op("SIZE", ret=3),
    ], tags=["round-trip"], visible=True,
       doc="Decoding the right-leaning chain gives back a right-leaning chain."),
    case("decode_empty", 1, [
        op("BUILD", [1]), op("DECODE", "#", ret=True), op("SIZE", ret=0),
        op("ENCODE", ret="#"),
    ], tags=["empty"], doc="A single marker decodes to nothing."),
    case("decode_rejects_truncated", 1, [
        op("DECODE", "1,2", ret=False), op("SIZE", ret=0), op("ENCODE", ret="#"),
    ], tags=["invalid"], visible=True,
       doc="The text runs out before the tree is complete. A rejected decode leaves the "
           "tree EMPTY rather than half built."),
    case("decode_rejects_trailing", 1, [
        op("DECODE", "1,#,#,5", ret=False), op("SIZE", ret=0),
    ], tags=["invalid"], visible=True,
       doc="The tree is complete and there is text left over, which means the encoding "
           "described something else."),
    case("decode_rejects_rubbish", 1, [
        op("DECODE", "x,#,#", ret=False), op("SIZE", ret=0),
    ], tags=["invalid"], doc="Not a number and not a marker."),
    case("decode_rejects_empty_text", 1, [
        op("DECODE", "", ret=False), op("SIZE", ret=0),
    ], tags=["invalid", "empty"],
       doc="The empty string is not the encoding of the empty tree -- `#` is."),
    case("negatives_and_zero", 1, [
        op("BUILD", [0, -2]), op("ENCODE", ret="0,-2,#,#,#"),
        op("DECODE", "0,-2,#,#,#", ret=True), op("PRE_ORDER", ret=[0, -2]),
    ], tags=["round-trip", "markers"], visible=True,
       doc="A leading minus is part of the number, and 0 is a value rather than an "
           "absence."),
    case("build_replaces", 1, [
        op("BUILD", [1, 2, 3]), op("BUILD", [9]), op("PRE_ORDER", ret=[9]),
        op("SIZE", ret=1),
    ], tags=["empty"], doc="Building again discards what was there."),
    case("build_empty", 1, [
        op("BUILD", []), op("SIZE", ret=0), op("ENCODE", ret="#"),
        op("BUILD", [None]), op("SIZE", ret=0),
    ], tags=["empty"]),
    case("larger_round_trip", 1, [
        op("BUILD", [5, 3, 8, 1, 4, None, 9]),
        op("IN_ORDER", ret=[1, 3, 4, 5, 8, 9]),
        op("DECODE", "5,3,1,#,#,4,#,#,8,#,9,#,#", ret=True),
        op("IN_ORDER", ret=[1, 3, 4, 5, 8, 9]), op("SIZE", ret=6),
    ], tags=["round-trip"],
       doc="Six nodes with a gap. Encode, then decode that exact string, and the walk is "
           "unchanged."),
)

PROBLEM = Problem(
    key="tree_codec",
    title="Serialise and deserialise a tree",
    blurb="A string that captures a tree's shape, and the rebuild that reads it back.",
    class_name="TreeCodec",
    kind=KIND_DESIGN,
    total_points=100,
    category="data-structures",
    difficulty="hard",
    topics=("traverse", "invariant"),
    levels=LEVELS,
    methods=METHODS,
    cases=CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum 2.9 build exercise — see docs/CATALOGUE.md",
)
