"""1.3 Int and number manipulation — divmod, //, %, bases, and where floats lie.

Self-contained: loaded by file path, so no package-relative imports.

Two drills here exist to be surprising rather than useful: negative floor division and
float rounding. Both are correct Python that reads like a bug, and both cost people real
money in real systems, so they get a visible case each.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="SPLIT_TOTAL",
        signature="(total: int, per_box: int) -> tuple[int, int]",
        doc="(full boxes, items left over).",
        constraint_note="one divmod call; not // and % separately",
        constraints=(
            RequireCall(("divmod",), because="one operation gives you both, and cannot drift apart",
                        hint="divmod(total, per_box)"),
        ),
    ),
    Method(
        display="HMS",
        signature="(seconds: int) -> tuple[int, int, int]",
        doc="(hours, minutes, seconds) from a count of seconds.",
        constraint_note="divmod twice; no manual // and %",
        constraints=(
            RequireCall(("divmod",), because="the same tool applied twice, outermost unit first",
                        hint="minutes, sec = divmod(seconds, 60); hours, minutes = divmod(minutes, 60)"),
        ),
    ),
    Method(
        display="FLOOR_PAIR",
        signature="(a: int, b: int) -> tuple[int, float]",
        doc="(a // b, a / b) — floor division and true division side by side.",
        constraint_note="no int() or math.floor(); use the operators",
        constraints=(
            ForbidCall(("int", "floor"), because="// IS floor division; converting afterwards truncates instead",
                       hint="(a // b, a / b)"),
        ),
    ),
    Method(
        display="WRAP",
        signature="(index: int, length: int) -> int",
        doc="index wrapped into range(length), for negative indices too.",
        constraint_note="use %; no while loop",
        constraints=(
            Forbid(("while", "for"), because="Python's % already returns a non-negative result for a positive modulus",
                   hint="index % length"),
        ),
    ),
    Method(
        display="TOWARDS_ZERO",
        signature="(a: int, b: int) -> int",
        doc="a divided by b, rounded TOWARDS ZERO (so -7/2 is -3, not -4).",
        # The trap: // rounds towards negative infinity, which is not what most other
        # languages' integer division does.
        constraint_note="beware: // rounds towards MINUS INFINITY, not towards zero",
        constraints=(
            Forbid(("while",), because="this is arithmetic, not iteration"),
        ),
    ),
    Method(
        display="DIGITS",
        signature="(number: int) -> list[int]",
        doc="The decimal digits of a non-negative number, most significant first. 0 -> [0].",
        constraint_note="arithmetic only — no str() and no int()",
        constraints=(
            ForbidCall(("str", "int"), because="extracting digits with % 10 and // 10 is the arithmetic worth knowing",
                       hint="repeatedly take number % 10, then number //= 10"),
        ),
    ),
    Method(
        display="MONEY",
        signature="(amount: float) -> str",
        doc='amount as a string with exactly 2 decimals, e.g. 1.5 -> "1.50".',
        constraint_note="an f-string format spec; no manual rounding",
        constraints=(
            ForbidCall(("round",), because="two decimals is a format spec; round() returns a float that still lies",
                       hint='f"{amount:.2f}"'),
        ),
    ),
    Method(
        display="EXACT_CENTS",
        signature="(cents_a: int, cents_b: int) -> int",
        doc="Add two amounts held in whole cents. No floats anywhere.",
        constraint_note="integers only — no float() and no round()",
        constraints=(
            ForbidCall(("float", "round"),
                       because="money in floats is how 0.1 + 0.2 becomes 0.30000000000000004; hold cents as ints",
                       hint="cents_a + cents_b"),
        ),
    ),
    Method(
        display="CLAMP",
        signature="(value: int, low: int, high: int) -> int",
        doc="value pulled into the range [low, high].",
        constraint_note="one expression with min and max; no if statement",
        constraints=(
            Forbid(("if",), because="clamping is a composition of min and max",
                   hint="max(low, min(high, value))"),
        ),
    ),
    Method(
        display="AS_BINARY",
        signature="(number: int) -> str",
        doc='The binary digits with no "0b" prefix. 5 -> "101". 0 -> "0".',
        constraint_note="use bin and strip the prefix; no loop",
        constraints=(
            Forbid(("while", "for"), because="bin() already does the conversion",
                   hint='bin(number)[2:]  or  f"{number:b}"'),
        ),
    ),
    Method(
        display="FROM_HEX",
        signature="(text: str) -> int",
        doc='Parse a hex string like "ff" or "0xFF" into an int.',
        constraint_note="int(text, 16) — the second argument is the base",
        constraints=(
            RequireCall(("int",), because="int() takes a base, so there is nothing to hand-roll",
                        hint='int(text, 16)'),
            Forbid(("for", "while"), because="no digit loop needed"),
        ),
    ),
    Method(
        display="IS_POWER_OF_TWO",
        signature="(number: int) -> bool",
        doc="True when number is a positive power of two.",
        constraint_note="the n & (n-1) trick; no loop, no logarithm",
        constraints=(
            Forbid(("while", "for"), because="a power of two has exactly one bit set, and n & (n-1) clears the lowest",
                   hint="number > 0 and number & (number - 1) == 0"),
            ForbidCall(("log", "log2"), because="floating-point logs are inexact at large powers"),
        ),
    ),
    Method(
        display="BITS_SET",
        signature="(number: int) -> int",
        doc="How many 1 bits are in a non-negative number.",
        constraint_note="use int.bit_count(); no loop",
        constraints=(
            Forbid(("while", "for"), because="bit_count is a single call in 3.10+",
                   hint="number.bit_count()"),
        ),
    ),
    Method(
        display="ROOT",
        signature="(number: int) -> int",
        doc="The integer square root of a non-negative number: the largest r with r*r <= number.",
        constraint_note="use math.isqrt; ** 0.5 is a float and loses precision",
        constraints=(
            RequireCall(("isqrt",), because="** 0.5 is inexact and fails on large integers",
                        hint="math.isqrt(number)"),
        ),
    ),
    Method(
        display="TOTALS",
        signature="(numbers: list[int]) -> tuple[int, int]",
        doc="(sum, product). The product of an empty list is 1.",
        constraint_note="use sum and math.prod; no loop",
        constraints=(
            Forbid(("for", "while"), because="both are one call",
                   hint="(sum(numbers), math.prod(numbers))"),
        ),
    ),
    Method(
        display="HUMAN_BYTES",
        signature="(count: int) -> str",
        doc=(
            'A byte count as "512 B", "1.5 KB", "2.0 MB", "3.0 GB" — 1024 to a step, '
            "one decimal place above bytes, and bytes shown as a whole number."
        ),
        constraint_note="checkpoint: no constraints — pick the right tools yourself",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Int and number manipulation", theme="arithmetic that does not lie"),)

TAG_GLOSSARY = {
    "divmod": "quotient and remainder together",
    "division": "floor versus true division, and negatives",
    "modulo": "wrapping and cycling",
    "digits": "decimal digits by arithmetic",
    "float-traps": "why floats are wrong for money",
    "bases": "binary and hex conversion",
    "bits": "bitwise tricks",
    "roots": "integer square root",
    "aggregate": "sum and product",
    "edge-values": "zero, one, negatives, empty",
    "checkpoint": "the whole unit at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)],
                tags=tags, visible=visible, doc=doc)


CASES = [
    _c("split_total_basic", "SPLIT_TOTAL", 17, 5, ret=(3, 2), tags=["divmod"], visible=True,
       doc="Three full boxes, two left over."),
    _c("split_total_exact", "SPLIT_TOTAL", 10, 5, ret=(2, 0), tags=["divmod"]),
    _c("split_total_smaller", "SPLIT_TOTAL", 3, 5, ret=(0, 3), tags=["divmod", "edge-values"]),

    _c("hms_basic", "HMS", 3725, ret=(1, 2, 5), tags=["divmod"], visible=True,
       doc="1h 2m 5s."),
    _c("hms_zero", "HMS", 0, ret=(0, 0, 0), tags=["divmod", "edge-values"]),
    _c("hms_under_a_minute", "HMS", 42, ret=(0, 0, 42), tags=["divmod"]),
    _c("hms_many_hours", "HMS", 100000, ret=(27, 46, 40), tags=["divmod"]),

    _c("floor_pair_positive", "FLOOR_PAIR", 7, 2, ret=(3, 3.5), tags=["division"], visible=True,
       doc="// gives an int, / always gives a float."),
    _c("floor_pair_exact", "FLOOR_PAIR", 8, 2, ret=(4, 4.0), tags=["division"],
       why="8 / 2 is 4.0, a float, not 4"),
    _c("floor_pair_negative", "FLOOR_PAIR", -7, 2, ret=(-4, -3.5), tags=["division", "edge-values"],
       why="-7 // 2 is -4: // rounds towards MINUS INFINITY, not towards zero"),

    _c("wrap_inside", "WRAP", 2, 5, ret=2, tags=["modulo"]),
    _c("wrap_over", "WRAP", 7, 5, ret=2, tags=["modulo"], visible=True, doc="Wraps around."),
    _c("wrap_negative", "WRAP", -1, 5, ret=4, tags=["modulo"], visible=True,
       doc="Python's % is non-negative for a positive modulus, so -1 wraps to the end."),

    _c("towards_zero_positive", "TOWARDS_ZERO", 7, 2, ret=3, tags=["division"]),
    _c("towards_zero_negative", "TOWARDS_ZERO", -7, 2, ret=-3, tags=["division"], visible=True,
       doc="-3, not -4. Python's // rounds towards minus infinity, which is NOT this."),
    _c("towards_zero_exact", "TOWARDS_ZERO", -8, 2, ret=-4, tags=["division", "edge-values"]),
    _c("towards_zero_both_negative", "TOWARDS_ZERO", -7, -2, ret=3, tags=["division"]),

    _c("digits_basic", "DIGITS", 507, ret=[5, 0, 7], tags=["digits"], visible=True,
       doc="Most significant first, including interior zeros."),
    _c("digits_zero", "DIGITS", 0, ret=[0], tags=["digits", "edge-values"], visible=True,
       doc="Zero is one digit, not no digits — the loop has to run at least once."),
    _c("digits_single", "DIGITS", 7, ret=[7], tags=["digits"]),
    _c("digits_long", "DIGITS", 1234567890, ret=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0], tags=["digits"]),

    _c("money_pads", "MONEY", 1.5, ret="1.50", tags=["float-traps"], visible=True,
       doc="Always two decimals."),
    _c("money_whole", "MONEY", 3.0, ret="3.00", tags=["float-traps"]),
    _c("money_half_cent_rounds_down", "MONEY", 22.125, ret="22.12",
       tags=["float-traps", "edge-values"], visible=True,
       doc="22.12, NOT 22.13 — .125 has no exact binary form, so the stored value is a hair low."),
    _c("money_zero", "MONEY", 0.0, ret="0.00", tags=["float-traps", "edge-values"]),

    _c("exact_cents_basic", "EXACT_CENTS", 10, 20, ret=30, tags=["float-traps"], visible=True,
       doc="Whole cents as ints: 0.1 + 0.2 in floats is 0.30000000000000004."),
    _c("exact_cents_zero", "EXACT_CENTS", 0, 0, ret=0, tags=["float-traps", "edge-values"]),
    _c("exact_cents_large", "EXACT_CENTS", 999999999, 1, ret=1000000000, tags=["float-traps"]),

    _c("clamp_inside", "CLAMP", 5, 0, 10, ret=5, tags=["aggregate"]),
    _c("clamp_below", "CLAMP", -3, 0, 10, ret=0, tags=["aggregate"], visible=True,
       doc="Pulled up to the low bound."),
    _c("clamp_above", "CLAMP", 99, 0, 10, ret=10, tags=["aggregate"]),
    _c("clamp_on_bound", "CLAMP", 10, 0, 10, ret=10, tags=["aggregate", "edge-values"]),

    _c("as_binary_basic", "AS_BINARY", 5, ret="101", tags=["bases"], visible=True,
       doc='No "0b" prefix.'),
    _c("as_binary_zero", "AS_BINARY", 0, ret="0", tags=["bases", "edge-values"]),
    _c("as_binary_power", "AS_BINARY", 8, ret="1000", tags=["bases"]),

    _c("from_hex_lower", "FROM_HEX", "ff", ret=255, tags=["bases"], visible=True,
       doc="With or without the 0x prefix, upper or lower case."),
    _c("from_hex_prefixed", "FROM_HEX", "0xFF", ret=255, tags=["bases"]),
    _c("from_hex_zero", "FROM_HEX", "0", ret=0, tags=["bases", "edge-values"]),

    _c("power_of_two_yes", "IS_POWER_OF_TWO", 64, ret=True, tags=["bits"], visible=True,
       doc="Exactly one bit set."),
    _c("power_of_two_no", "IS_POWER_OF_TWO", 12, ret=False, tags=["bits"]),
    _c("power_of_two_one", "IS_POWER_OF_TWO", 1, ret=True, tags=["bits", "edge-values"],
       why="1 is 2**0"),
    _c("power_of_two_zero", "IS_POWER_OF_TWO", 0, ret=False, tags=["bits", "edge-values"],
       visible=True, doc="0 has no bits set, so it is not a power of two — the n&(n-1) trick alone says yes."),
    _c("power_of_two_negative", "IS_POWER_OF_TWO", -8, ret=False, tags=["bits", "edge-values"]),

    _c("bits_set_basic", "BITS_SET", 7, ret=3, tags=["bits"], visible=True, doc="0b111."),
    _c("bits_set_zero", "BITS_SET", 0, ret=0, tags=["bits", "edge-values"]),
    _c("bits_set_large", "BITS_SET", 2 ** 40 + 1, ret=2, tags=["bits"]),

    _c("root_exact", "ROOT", 16, ret=4, tags=["roots"], visible=True, doc="Exact square."),
    _c("root_inexact", "ROOT", 17, ret=4, tags=["roots"], visible=True,
       doc="The largest r with r*r <= n, so 17 gives 4."),
    _c("root_zero", "ROOT", 0, ret=0, tags=["roots", "edge-values"]),
    _c("root_huge", "ROOT", 10 ** 30, ret=10 ** 15, tags=["roots", "edge-values"],
       why="(10**30) ** 0.5 is a float and comes out slightly wrong; isqrt is exact"),

    _c("totals_basic", "TOTALS", [1, 2, 3, 4], ret=(10, 24), tags=["aggregate"], visible=True,
       doc="Sum and product."),
    _c("totals_empty", "TOTALS", [], ret=(0, 1), tags=["aggregate", "edge-values"], visible=True,
       doc="Empty: sum 0, product 1 — the identity of each operation."),
    _c("totals_with_zero", "TOTALS", [5, 0, 3], ret=(8, 0), tags=["aggregate"]),

    _c("human_bytes_small", "HUMAN_BYTES", 512, ret="512 B", tags=["checkpoint"], visible=True,
       doc="Under 1024 stays in whole bytes."),
    _c("human_bytes_kb", "HUMAN_BYTES", 1536, ret="1.5 KB", tags=["checkpoint"], visible=True,
       doc="One decimal place above bytes."),
    _c("human_bytes_mb", "HUMAN_BYTES", 2 * 1024 ** 2, ret="2.0 MB", tags=["checkpoint"]),
    _c("human_bytes_gb", "HUMAN_BYTES", 3 * 1024 ** 3, ret="3.0 GB", tags=["checkpoint"]),
    _c("human_bytes_zero", "HUMAN_BYTES", 0, ret="0 B", tags=["checkpoint", "edge-values"]),
    _c("human_bytes_boundary", "HUMAN_BYTES", 1024, ret="1.0 KB",
       tags=["checkpoint", "edge-values"], why="exactly 1024 steps up"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="ints",
    title="1.3 Int and number manipulation",
    blurb="divmod, floor division, modulo, digits, bases, bit tricks, and where floats lie.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("divmod", "modulo", "bases", "bits", "float-traps"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.3 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
