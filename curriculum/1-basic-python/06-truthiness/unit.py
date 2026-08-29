"""1.6 Truthiness, None and conditionals — where `or` quietly eats your zero.

Self-contained: loaded by file path, so no package-relative imports.

The spine of this unit is one bug: `value or default` looks like "use the default when
the value is missing" and actually means "use the default when the value is falsy". 0,
"" and [] are all falsy and all legitimate values, so the idiom silently replaces real
data. Three drills circle it from different angles.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="HAS_ITEMS",
        signature="(items: list) -> bool",
        doc="True when the list has anything in it.",
        constraint_note="test the collection directly; no len() comparison",
        constraints=(
            ForbidCall(("len",), because="an empty collection is already falsy",
                       hint="bool(items)"),
        ),
    ),
    Method(
        display="LABEL",
        signature="(name: str | None) -> str",
        doc='name, or "anonymous" when it is None. An EMPTY name stays empty.',
        # The bug, stated as a requirement: `name or "anonymous"` passes the None case
        # and fails the empty-string case.
        constraint_note='use `is None`, not `or` — an empty name is a real name',
        constraints=(
            Forbid(("or",),
                   because='`name or "anonymous"` replaces any FALSY name, and "" is falsy '
                           "but perfectly real",
                   hint='"anonymous" if name is None else name'),
        ),
    ),
    Method(
        display="PORT",
        signature="(configured: int | None) -> int",
        doc="configured, or 8080 when it is None. A configured 0 stays 0.",
        constraint_note="`is None`, not `or` — a configured 0 is a real port",
        constraints=(
            Forbid(("or",),
                   because="`configured or 8080` silently discards a configured 0",
                   hint="8080 if configured is None else configured"),
        ),
    ),
    Method(
        display="FIRST_SET",
        signature="(values: list) -> object",
        doc="The first value that is not None. None when they are all None.",
        constraint_note="use next() with a default and an `is not None` test",
        constraints=(
            RequireCall(("next",), because="a generator plus next() reads as one statement",
                        hint="next((v for v in values if v is not None), None)"),
            Forbid(("break",), because="next() with a default expresses early exit as a value"),
        ),
    ),
    Method(
        display="IN_RANGE",
        signature="(value: int, low: int, high: int) -> bool",
        doc="True when low <= value <= high.",
        constraint_note="use a chained comparison; no `and`",
        constraints=(
            Forbid(("if",), because="a chained comparison is the whole expression",
                   hint="low <= value <= high"),
        ),
    ),
    Method(
        display="GRADE",
        signature="(score: int) -> str",
        doc='"high" for 80+, "mid" for 50-79, "low" below 50.',
        constraint_note="one conditional expression; no `if` statement",
        constraints=(
            Forbid(("if",), because="a ternary chain is an expression and returns directly",
                   hint='"high" if score >= 80 else "mid" if score >= 50 else "low"'),
        ),
    ),
    Method(
        display="ALL_PASSED",
        signature="(scores: list[int]) -> bool",
        doc="True when every score is 50 or more. True for an empty list.",
        constraint_note="use all(); no loop",
        constraints=(
            RequireCall(("all",), because="all() short-circuits and says what it means",
                        hint="all(s >= 50 for s in scores)"),
            Forbid(("for", "while"), because="all() is the loop"),
        ),
    ),
    Method(
        display="ANY_FAILED",
        signature="(scores: list[int]) -> bool",
        doc="True when at least one score is below 50. False for an empty list.",
        constraint_note="use any(); no loop",
        constraints=(
            RequireCall(("any",), because="any() short-circuits on the first hit",
                        hint="any(s < 50 for s in scores)"),
            Forbid(("for", "while"), because="any() is the loop"),
        ),
    ),
    Method(
        display="SAFE_LENGTH",
        signature="(value: object) -> int",
        doc="The length of value, or 0 when value is None.",
        constraint_note="guard with `is None`; do not catch a TypeError",
        constraints=(
            Forbid(("try",), because="a None check is cheaper and clearer than catching TypeError",
                   hint="0 if value is None else len(value)"),
        ),
    ),
    Method(
        display="VALIDATE",
        signature="(record: dict) -> str",
        doc=(
            'The FIRST problem with the record, as a message: "missing name" when '
            '"name" is absent or None, "missing age" likewise, "age must be positive" '
            'when age is not greater than zero. "" when the record is fine. '
            "An empty name is allowed."
        ),
        constraint_note="checkpoint: no constraints — pick the right tools yourself",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Truthiness, None and conditionals", theme="falsy is not the same as missing"),)

TAG_GLOSSARY = {
    "truthy": "empty collections are falsy",
    "none": "None versus falsy",
    "chained": "chained comparisons and ternaries",
    "quantifier": "any and all",
    "short-circuit": "and/or short-circuiting",
    "edge-values": "zero, empty string, empty list",
    "checkpoint": "the whole unit at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("has_items_yes", "HAS_ITEMS", [1], ret=True, tags=["truthy"], visible=True,
       doc="A non-empty collection is truthy."),
    _c("has_items_no", "HAS_ITEMS", [], ret=False, tags=["truthy"]),
    _c("has_items_falsy_content", "HAS_ITEMS", [0], ret=True, tags=["truthy", "edge-values"],
       visible=True, doc="A list holding 0 is not empty — the CONTENTS being falsy is irrelevant."),

    _c("label_name", "LABEL", "ada", ret="ada", tags=["none"], visible=True,
       doc="A real name is kept."),
    _c("label_none", "LABEL", None, ret="anonymous", tags=["none"], visible=True,
       doc="None becomes the default."),
    _c("label_empty_stays_empty", "LABEL", "", ret="", tags=["none", "edge-values"],
       visible=True,
       doc='"" is a real name. `name or "anonymous"` gets this wrong — it is falsy, not missing.'),

    _c("label_whitespace_is_real", "LABEL", "  ", ret="  ", tags=["none", "edge-values"],
       why="only None is missing; whitespace is content"),

    _c("port_configured", "PORT", 3000, ret=3000, tags=["none"], visible=True,
       doc="A configured port is used."),
    _c("port_none", "PORT", None, ret=8080, tags=["none"]),
    _c("port_zero_stays_zero", "PORT", 0, ret=0, tags=["none", "edge-values"], visible=True,
       doc="0 is a real port number. `configured or 8080` would silently replace it."),

    _c("first_set_basic", "FIRST_SET", [None, 0, 2], ret=0, tags=["none"], visible=True,
       doc="0 is not None, so 0 is the answer."),
    _c("first_set_all_none", "FIRST_SET", [None, None], ret=None, tags=["none"]),
    _c("first_set_empty", "FIRST_SET", [], ret=None, tags=["none", "edge-values"]),

    _c("in_range_inside", "IN_RANGE", 5, 1, 10, ret=True, tags=["chained"], visible=True,
       doc="Both bounds are inclusive."),
    _c("in_range_on_bound", "IN_RANGE", 10, 1, 10, ret=True, tags=["chained", "edge-values"]),
    _c("in_range_outside", "IN_RANGE", 0, 1, 10, ret=False, tags=["chained"]),

    _c("grade_high", "GRADE", 90, ret="high", tags=["chained"], visible=True,
       doc="80 and above."),
    _c("grade_boundary_80", "GRADE", 80, ret="high", tags=["chained", "edge-values"]),
    _c("grade_mid", "GRADE", 50, ret="mid", tags=["chained", "edge-values"]),
    _c("grade_low", "GRADE", 49, ret="low", tags=["chained"]),

    _c("all_passed_yes", "ALL_PASSED", [50, 80], ret=True, tags=["quantifier"], visible=True,
       doc="50 is a pass."),
    _c("all_passed_no", "ALL_PASSED", [50, 49], ret=False, tags=["quantifier"]),
    _c("all_passed_empty", "ALL_PASSED", [], ret=True, tags=["quantifier", "edge-values"],
       visible=True, doc="all() of nothing is True — vacuously, everything passed."),

    _c("any_failed_yes", "ANY_FAILED", [80, 10], ret=True, tags=["quantifier"], visible=True,
       doc="One failure is enough."),
    _c("any_failed_no", "ANY_FAILED", [80, 90], ret=False, tags=["quantifier"]),
    _c("any_failed_empty", "ANY_FAILED", [], ret=False, tags=["quantifier", "edge-values"],
       visible=True, doc="any() of nothing is False — the mirror of all()."),

    _c("safe_length_string", "SAFE_LENGTH", "abc", ret=3, tags=["short-circuit"], visible=True,
       doc="Normal case."),
    _c("safe_length_none", "SAFE_LENGTH", None, ret=0, tags=["short-circuit"]),
    _c("safe_length_empty", "SAFE_LENGTH", "", ret=0, tags=["short-circuit", "edge-values"]),

    _c("validate_ok", "VALIDATE", {"name": "ada", "age": 30}, ret="",
       tags=["checkpoint"], visible=True, doc="A good record gives an empty message."),
    _c("validate_missing_name", "VALIDATE", {"age": 30}, ret="missing name",
       tags=["checkpoint"], visible=True, doc="Absent key."),
    _c("validate_none_name", "VALIDATE", {"name": None, "age": 30}, ret="missing name",
       tags=["checkpoint"]),
    _c("validate_empty_name_is_fine", "VALIDATE", {"name": "", "age": 30}, ret="",
       tags=["checkpoint", "edge-values"], visible=True,
       doc='An empty name is allowed — this is the falsy-versus-missing distinction again.'),
    _c("validate_missing_age", "VALIDATE", {"name": "ada"}, ret="missing age",
       tags=["checkpoint"]),
    _c("validate_zero_age", "VALIDATE", {"name": "ada", "age": 0},
       ret="age must be positive", tags=["checkpoint", "edge-values"], visible=True,
       doc="0 is present but not positive, so the message is about the value, not absence."),
    _c("validate_name_first", "VALIDATE", {}, ret="missing name",
       tags=["checkpoint", "edge-values"], why="the FIRST problem, and name is checked first"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="truthiness",
    title="1.6 Truthiness, None and conditionals",
    blurb="Falsy is not the same as missing: `or` defaults, is None, any, all and ternaries.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("none", "truthy", "quantifier"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.6 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
