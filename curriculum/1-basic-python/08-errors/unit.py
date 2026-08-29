"""1.8 Errors and context managers — catch what you meant, and only that.

Self-contained: loaded by file path, so no package-relative imports.

Two lessons: `except Exception` hides the bug you have not found yet, and `with` is how
you guarantee cleanup without writing `finally` every time.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall, RequireConstruct
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, Raises, case, op

METHODS = (
    Method(
        display="AS_INT",
        signature="(text: str) -> int | None",
        doc="text as an int, or None when it is not a number.",
        constraint_note="catch ValueError specifically; not a bare `except`",
        constraints=(
            RequireConstruct("try", because="int() raises rather than returning a sentinel",
                             hint="except ValueError: return None"),
            ForbidCall(("isdigit",),
                       because='isdigit() is wrong for "-3" and for "٣"; try/except is the honest test'),
        ),
    ),
    Method(
        display="DIVIDE",
        signature="(a: int, b: int) -> float | None",
        doc="a / b, or None when b is zero.",
        constraint_note="guard with a comparison; do not catch ZeroDivisionError",
        constraints=(
            Forbid(("try",),
                   because="a condition you can test cheaply should be tested, not raised and caught",
                   hint="None if b == 0 else a / b"),
        ),
    ),
    Method(
        display="PICK",
        signature="(data: dict, key: str) -> object",
        doc='data[key], or "unknown" when the key is absent.',
        constraint_note="use dict.get with a default; no try and no `in` test",
        constraints=(
            RequireCall(("get",), because="get() with a default is one lookup and one expression",
                        hint='data.get(key, "unknown")'),
            Forbid(("try", "if"), because="get() already expresses the default"),
        ),
    ),
    Method(
        display="FIRST_NUMBER",
        signature="(items: list[str]) -> int | None",
        doc="The first item that parses as an int, or None.",
        constraint_note="one try per item; keep going after a failure",
        constraints=(
            RequireConstruct("try", because="the failure is per item, so the handler belongs inside the loop"),
        ),
    ),
    Method(
        display="TOTAL_OR_ZERO",
        signature="(values: list) -> int",
        doc="The sum of the values, or 0 when any of them is not a number.",
        constraint_note="catch TypeError specifically",
        constraints=(
            RequireConstruct("try", because="sum() raises TypeError on a bad element",
                            hint="except TypeError: return 0"),
        ),
    ),
    Method(
        display="REQUIRE_POSITIVE",
        signature="(value: int) -> int",
        doc="value when it is positive; otherwise raise ValueError with a useful message.",
        constraint_note="raise ValueError, and say what was wrong",
        constraints=(
            ForbidCall(("assert",), because="assertions are stripped by -O, so they are not validation",
                       hint='raise ValueError(f"expected a positive value, got {value}")'),
        ),
    ),
    Method(
        display="CLEANUP_ORDER",
        signature="(steps: list[str]) -> list[str]",
        doc=(
            'Append "start", then each step, then "end" — and "end" must be appended '
            'even when a step is the string "boom", which you should raise on.'
        ),
        constraint_note="use finally, so the cleanup runs on both paths",
        constraints=(
            RequireConstruct("try", because="finally is the only way to run cleanup on both paths",
                            hint="try: ... finally: log.append('end')"),
        ),
    ),
    Method(
        display="READ_LINES",
        signature="(path: str) -> list[str]",
        doc="The lines of the file with newlines stripped. [] when the file is missing.",
        constraint_note="open with `with`; catch OSError",
        constraints=(
            RequireConstruct("try", because="a missing file is an OSError, not a return value"),
            ForbidCall(("close",), because="`with` closes it for you, even when the body raises",
                       hint="with open(path) as handle: ..."),
        ),
    ),
    Method(
        display="LOAD_CONFIG",
        signature="(lines: list[str]) -> tuple[dict, list[str]]",
        doc=(
            "Parse 'key=value' lines into a dict, coercing values that look like ints. "
            "Return (config, problems) where problems lists the 1-based line numbers "
            "of lines that are not 'key=value', as strings like 'line 3'. "
            "Blank lines and lines starting with # are skipped silently."
        ),
        constraint_note="checkpoint: no constraints — pick the right tools yourself",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Errors and context managers", theme="catch what you meant"),)

TAG_GLOSSARY = {
    "specific": "catching one exception type",
    "guard": "testing instead of catching",
    "default": "get() and defaults",
    "per-item": "handling failure inside a loop",
    "raising": "raising with a useful message",
    "finally": "cleanup on every path",
    "context": "the with statement",
    "edge-values": "empty input, all bad, nothing to do",
    "checkpoint": "the whole unit at once",
}


def _c(name, opname, *args, ret=None, tags=(), visible=False, doc="", why="", raises=None):
    return case(name, 1, [op(opname, *args, ret=ret, raises=raises, why=why)],
                tags=list(tags), visible=visible, doc=doc)


CASES = [
    _c("as_int_number", "AS_INT", "42", ret=42, tags=["specific"], visible=True,
       doc="A plain number parses."),
    _c("as_int_negative", "AS_INT", "-3", ret=-3, tags=["specific"], visible=True,
       doc='Negative numbers parse too — this is where isdigit() gets it wrong.'),
    _c("as_int_text", "AS_INT", "abc", ret=None, tags=["specific"]),
    _c("as_int_empty", "AS_INT", "", ret=None, tags=["specific", "edge-values"]),
    _c("as_int_spaces", "AS_INT", " 7 ", ret=7, tags=["specific", "edge-values"],
       why="int() tolerates surrounding whitespace"),

    _c("divide_basic", "DIVIDE", 7, 2, ret=3.5, tags=["guard"], visible=True,
       doc="Ordinary division."),
    _c("divide_by_zero", "DIVIDE", 1, 0, ret=None, tags=["guard"], visible=True,
       doc="A cheap condition is tested, not raised and caught."),
    _c("divide_zero_numerator", "DIVIDE", 0, 5, ret=0.0, tags=["guard", "edge-values"]),

    _c("pick_present", "PICK", {"a": 1}, "a", ret=1, tags=["default"], visible=True,
       doc="Present key."),
    _c("pick_absent", "PICK", {"a": 1}, "b", ret="unknown", tags=["default"]),
    _c("pick_falsy_value", "PICK", {"a": 0}, "a", ret=0, tags=["default", "edge-values"],
       visible=True,
       doc="0 is present, so 0 is returned — get() distinguishes absent from falsy."),

    _c("first_number_basic", "FIRST_NUMBER", ["a", "12", "3"], ret=12, tags=["per-item"],
       visible=True, doc="Skips what does not parse and keeps going."),
    _c("first_number_none", "FIRST_NUMBER", ["a", "b"], ret=None, tags=["per-item"]),
    _c("first_number_empty", "FIRST_NUMBER", [], ret=None, tags=["per-item", "edge-values"]),

    _c("total_or_zero_basic", "TOTAL_OR_ZERO", [1, 2, 3], ret=6, tags=["specific"],
       visible=True, doc="All numbers."),
    _c("total_or_zero_bad", "TOTAL_OR_ZERO", [1, "x"], ret=0, tags=["specific"], visible=True,
       doc="One bad element makes the whole total 0."),
    _c("total_or_zero_empty", "TOTAL_OR_ZERO", [], ret=0, tags=["specific", "edge-values"]),

    _c("require_positive_ok", "REQUIRE_POSITIVE", 5, ret=5, tags=["raising"], visible=True,
       doc="A positive value comes straight back."),
    _c("require_positive_zero", "REQUIRE_POSITIVE", 0, raises=ValueError, tags=["raising"],
       visible=True, doc="Zero is not positive, so this raises ValueError."),
    _c("require_positive_negative", "REQUIRE_POSITIVE", -1, raises=ValueError, tags=["raising"]),

    _c("cleanup_order_basic", "CLEANUP_ORDER", ["a", "b"],
       ret=["start", "a", "b", "end"], tags=["finally"], visible=True,
       doc="Normal path."),
    _c("cleanup_order_raises", "CLEANUP_ORDER", ["a", "boom", "c"],
       ret=["start", "a", "end"], tags=["finally"], visible=True,
       doc='"boom" stops the work but "end" still runs — that is what finally is for.'),
    _c("cleanup_order_empty", "CLEANUP_ORDER", [], ret=["start", "end"],
       tags=["finally", "edge-values"]),

    _c("read_lines_missing", "READ_LINES", "/definitely/not/a/real/path.txt", ret=[],
       tags=["context"], visible=True, doc="A missing file gives [], not an exception."),
    _c("read_lines_missing_dir", "READ_LINES", "/nope/nope/nope", ret=[], tags=["context"]),
    _c("read_lines_empty_name", "READ_LINES", "", ret=[], tags=["context", "edge-values"]),

    _c("load_config_basic", "LOAD_CONFIG", ["port=8080", "name=api"],
       ret=({"port": 8080, "name": "api"}, []), tags=["checkpoint"], visible=True,
       doc="Values that look like ints become ints."),
    _c("load_config_skips_comments", "LOAD_CONFIG", ["# a comment", "", "a=1"],
       ret=({"a": 1}, []), tags=["checkpoint"], visible=True,
       doc="Blanks and comments are skipped without complaint."),
    _c("load_config_reports_bad_lines", "LOAD_CONFIG", ["a=1", "garbage", "b=2"],
       ret=({"a": 1, "b": 2}, ["line 2"]), tags=["checkpoint"], visible=True,
       doc="A bad line is reported by its 1-based number and does not stop the parse."),
    _c("load_config_negative_value", "LOAD_CONFIG", ["offset=-5"],
       ret=({"offset": -5}, []), tags=["checkpoint", "edge-values"]),
    _c("load_config_empty_value", "LOAD_CONFIG", ["a="], ret=({"a": ""}, []),
       tags=["checkpoint", "edge-values"], why="an empty value is a value, not a bad line"),
    _c("load_config_empty", "LOAD_CONFIG", [], ret=({}, []),
       tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="errors",
    title="1.8 Errors and context managers",
    blurb="Catch one exception type, guard what you can test, and let `with` do the cleanup.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("specific", "finally", "context"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.8 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
