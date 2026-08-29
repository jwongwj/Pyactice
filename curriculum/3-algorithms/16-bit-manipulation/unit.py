"""3.16 Bit manipulation — pairs cancelling, flags, and subsets by counting.

Self-contained: loaded by file path, so no package-relative imports.

Three cues, and they are quite different from each other:

  * everything appears twice except one thing      -> XOR, because x ^ x is 0
  * a set of yes/no flags, or "every subset"       -> an integer as a bit field
  * counting bits, or the lowest set bit           -> x & (x - 1) clears it

Python's integers are arbitrary precision and negative numbers behave as if they had
infinitely many leading 1s, so `~x` and right-shifting a negative do not do what they do in
C. Every drill here is stated over non-negative inputs for that reason, except where the
sign is the point.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="LONELY_VALUE",
        signature="(nums: list[int]) -> int",
        doc="The one value appearing an odd number of times, when every other value "
            "appears an even number of times. 0 for an empty list.",
        constraint_note="XOR everything together; no dict, no set, no counting",
        constraints=(
            ForbidCall(("Counter", "set", "dict", "count"),
                       because="counting works and costs O(n) memory; XOR costs one "
                               "integer, because a ^ a is 0 and the order does not matter",
                       hint="fold the whole list with ^, starting from 0"),
        ),
    ),
    Method(
        display="COUNT_BITS",
        fuzz=("nonneg",),
        signature="(value: int) -> int",
        doc="How many 1 bits are in the binary form of a non-negative integer.",
        constraint_note="clear the lowest set bit each step; no string conversion",
        constraints=(
            ForbidCall(("bin", "format", "str", "bit_count"),
                       because="`bin(x).count('1')` is the right answer in real code and "
                               "teaches nothing; `x & (x - 1)` clears the lowest set bit, "
                               "so the loop runs once per SET bit rather than once per bit",
                       hint="while value: value &= value - 1; count += 1"),
        ),
    ),
    Method(
        display="IS_POWER_OF_FOUR",
        fuzz=("nonneg",),
        signature="(value: int) -> bool",
        doc="True when the value is 4, 16, 64 and so on -- a power of four. 1 counts "
            "(four to the zero). 0 and negatives do not.",
        # A power of four is a power of two whose single bit sits at an EVEN position.
        constraint_note="one set bit, and it must be at an even position",
        constraints=(
            ForbidCall(("log", "sqrt", "bin", "str"),
                       because="floating-point logs give wrong answers for large values, "
                               "and a loop of divisions is slower than two bit tests",
                       hint="value & (value - 1) == 0 proves a single set bit; then mask "
                            "against 0x5555... to place it"),
        ),
    ),
    Method(
        display="SUBSET_AT",
        signature="(items: list[str], index: int) -> list[str]",
        doc="The `index`-th subset of `items`, where bit i of `index` selects items[i]. "
            "Members keep the order they have in `items`. An index outside "
            "0..2^len(items)-1 gives an empty list.",
        constraint_note="read the bits of `index`; no recursion and no itertools",
        constraints=(
            ForbidCall(("combinations", "product", "powerset"),
                       because="an integer IS a subset -- 2^n subsets and 2^n integers, "
                               "and bit i answers 'is items[i] in'. Recognising that is "
                               "what makes bitmask enumeration and bitmask DP available",
                       hint="index >> i & 1 tests bit i"),
        ),
    ),
    Method(
        display="SINGLE_OF_THREE",
        signature="(nums: list[int]) -> int",
        doc="The one value appearing once, when every other value appears exactly three "
            "times. Values are non-negative. 0 for an empty list.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Bit manipulation", theme="an integer as a set of flags"),)

TAG_GLOSSARY = {
    "xor": "values cancelling in pairs",
    "popcount": "counting or clearing set bits",
    "single-bit": "recognising a power of two or four",
    "bitmask": "an integer standing for a subset",
    "modular": "counting bits modulo something other than two",
    "edge-values": "zero, one, empty inputs, indices out of range",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("lonely_basic", "LONELY_VALUE", [4, 1, 2, 1, 2], ret=4,
       tags=["xor"], visible=True, doc="Everything but 4 appears twice."),
    _c("lonely_first", "LONELY_VALUE", [7, 3, 3], ret=7, tags=["xor"]),
    _c("lonely_single", "LONELY_VALUE", [9], ret=9, tags=["xor", "edge-values"]),
    _c("lonely_empty", "LONELY_VALUE", [], ret=0, tags=["xor", "edge-values"], visible=True,
       doc="Nothing to fold, and 0 is XOR's identity."),
    _c("lonely_with_zero", "LONELY_VALUE", [0, 5, 5], ret=0,
       tags=["xor", "edge-values"], visible=True,
       doc="The lonely value may itself be 0, which is indistinguishable from 'nothing "
           "found' if you use falsiness as the test."),
    _c("lonely_four_times", "LONELY_VALUE", [2, 2, 2, 2, 3], ret=3,
       tags=["xor", "edge-values"],
       why="four is an even count, so those cancel in pairs just as two would"),

    _c("bits_basic", "COUNT_BITS", 11, ret=3,
       tags=["popcount"], visible=True, doc="1011 in binary."),
    _c("bits_zero", "COUNT_BITS", 0, ret=0, tags=["popcount", "edge-values"], visible=True,
       doc="No bits set."),
    _c("bits_one", "COUNT_BITS", 1, ret=1, tags=["popcount", "edge-values"]),
    _c("bits_power_of_two", "COUNT_BITS", 16, ret=1, tags=["popcount"],
       why="a power of two has exactly one set bit, which is the next drill"),
    _c("bits_all_ones", "COUNT_BITS", 255, ret=8, tags=["popcount"]),
    _c("bits_large", "COUNT_BITS", 1023, ret=10, tags=["popcount", "edge-values"],
       why="Python integers are arbitrary precision, so there is no word size to overflow"),

    _c("power_four_yes", "IS_POWER_OF_FOUR", 16, ret=True,
       tags=["single-bit"], visible=True, doc="4 squared."),
    _c("power_four_one", "IS_POWER_OF_FOUR", 1, ret=True,
       tags=["single-bit", "edge-values"], visible=True, doc="Four to the zero."),
    _c("power_four_is_two_not_four", "IS_POWER_OF_FOUR", 8, ret=False,
       tags=["single-bit"], visible=True,
       doc="8 is a power of TWO with one set bit, and its bit is at an odd position. "
           "This is the case that separates the two questions."),
    _c("power_four_zero", "IS_POWER_OF_FOUR", 0, ret=False,
       tags=["single-bit", "edge-values"], visible=True,
       doc="Zero has no set bits, and `0 & -1 == 0` says 'single bit' if you forget to "
           "check for it separately."),
    _c("power_four_negative", "IS_POWER_OF_FOUR", -4, ret=False,
       tags=["single-bit", "edge-values"]),
    _c("power_four_not_a_power", "IS_POWER_OF_FOUR", 12, ret=False, tags=["single-bit"]),
    _c("power_four_large", "IS_POWER_OF_FOUR", 1024, ret=True,
       tags=["single-bit"], why="4^5, and far beyond what a float log handles exactly"),

    _c("subset_none", "SUBSET_AT", ["a", "b"], 0, ret=[],
       tags=["bitmask"], visible=True, doc="Index 0 selects nothing."),
    _c("subset_first", "SUBSET_AT", ["a", "b"], 1, ret=["a"],
       tags=["bitmask"], visible=True, doc="Bit 0 is set, so items[0] is in."),
    _c("subset_second", "SUBSET_AT", ["a", "b"], 2, ret=["b"], tags=["bitmask"]),
    _c("subset_all", "SUBSET_AT", ["a", "b"], 3, ret=["a", "b"],
       tags=["bitmask"], visible=True, doc="Both bits set."),
    _c("subset_order_kept", "SUBSET_AT", ["z", "a"], 3, ret=["z", "a"],
       tags=["bitmask"], why="the order comes from `items`, not from sorting"),
    _c("subset_out_of_range", "SUBSET_AT", ["a"], 5, ret=[],
       tags=["bitmask", "edge-values"], visible=True,
       doc="One item has two subsets, so 5 is out of range and gives nothing rather "
           "than silently ignoring the high bits."),
    _c("subset_negative", "SUBSET_AT", ["a"], -1, ret=[],
       tags=["bitmask", "edge-values"]),
    _c("subset_no_items", "SUBSET_AT", [], 0, ret=[],
       tags=["bitmask", "edge-values"],
       why="the empty list has exactly one subset, at index 0"),

    _c("three_basic", "SINGLE_OF_THREE", [2, 2, 3, 2], ret=3,
       tags=["checkpoint", "modular"], visible=True,
       doc="2 appears three times. Plain XOR gives 2 here, not 3, because three copies "
           "do not cancel."),
    _c("three_longer", "SINGLE_OF_THREE", [0, 1, 0, 1, 0, 1, 99], ret=99,
       tags=["checkpoint", "modular"], visible=True, doc="Two values tripled, one alone."),
    _c("three_single", "SINGLE_OF_THREE", [5], ret=5,
       tags=["checkpoint", "edge-values"]),
    _c("three_empty", "SINGLE_OF_THREE", [], ret=0,
       tags=["checkpoint", "edge-values"]),
    _c("three_lonely_zero", "SINGLE_OF_THREE", [7, 7, 7, 0], ret=0,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="The lonely value is 0 again, and again falsiness is the wrong test."),
    _c("three_high_bits", "SINGLE_OF_THREE", [1024, 1024, 1024, 3], ret=3,
       tags=["checkpoint", "modular"],
       why="counting bits per position must reach beyond the low byte"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="bits",
    title="3.16 Bit manipulation",
    blurb="XOR cancelling, popcount, powers of four, subsets as integers.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="algorithms",
    difficulty="medium",
    topics=("xor", "bitmask", "popcount"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 3.16 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
