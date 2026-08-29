"""1.2 String manipulation — strip, partition, join, translate.

Self-contained: the loader imports this by file path, so no package-relative imports.

The through-line of this unit is that the string method you want almost always already
exists, and the hand-rolled version is both longer and wrong at an edge. `rpartition`
appears twice on purpose -- filename/extension and dirname/basename are the same tool
solving the two problems people actually hit.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="TRIMMED",
        signature="(raw: str) -> str",
        doc="raw with whitespace removed from both ends.",
        constraint_note="use strip",
        constraints=(RequireCall(("strip",), because="this is what strip is",
                                 hint="raw.strip()"),),
    ),
    Method(
        display="UNWRAP",
        signature="(name: str) -> str",
        doc='Drop a leading "tmp_" and a trailing ".bak" if present.',
        constraint_note="use removeprefix and removesuffix; not slicing",
        constraints=(
            RequireCall(("removeprefix",), because="removeprefix says what it does and is safe when absent",
                        hint='name.removeprefix("tmp_").removesuffix(".bak")'),
            Forbid(("subscript",), because="slicing by a hardcoded length breaks the moment the prefix is absent"),
        ),
    ),
    Method(
        display="SENTENCE",
        signature="(words: list[str]) -> str",
        doc="The words joined by single spaces.",
        constraint_note="use join; no += in a loop",
        constraints=(
            RequireCall(("join",), because="join is O(n); += in a loop is O(n squared)",
                        hint='" ".join(words)'),
            Forbid(("augassign",), because="building a string with += copies it every time"),
        ),
    ),
    Method(
        display="FIELDS",
        signature="(line: str) -> list[str]",
        doc='Split a comma-separated line, with the whitespace trimmed off each field.',
        constraint_note="split, then strip each field",
        constraints=(RequireCall(("split",), because="this drill is about split",
                                 hint='[f.strip() for f in line.split(",")]'),),
    ),
    Method(
        display="EXTENSION",
        signature="(path: str) -> str",
        doc='The part after the LAST dot, or "" when there is no dot.',
        constraint_note="use rpartition; do not use split",
        constraints=(
            RequireCall(("rpartition",), because="rpartition splits once from the right and always returns three parts",
                        hint='path.rpartition(".")[2] -- but mind the no-dot case'),
            ForbidCall(("split",), because="split(\".\")[-1] returns the whole name when there is no dot"),
        ),
    ),
    Method(
        display="BASENAME",
        signature="(path: str) -> str",
        doc="The part after the last slash. The whole string when there is no slash.",
        constraint_note="use rpartition",
        constraints=(
            RequireCall(("rpartition",), because="the same tool as EXTENSION, on a different separator",
                        hint='path.rpartition("/")[2]'),
            ForbidCall(("split",), because="practise the single-split tool"),
        ),
    ),
    Method(
        display="KEY_VALUE",
        signature="(line: str) -> tuple[str, str]",
        doc='Split "a=b=c" on the FIRST "=" into ("a", "b=c"). ("line", "") when there is no "=".',
        constraint_note="use partition, not split",
        constraints=(
            RequireCall(("partition",), because="partition splits once from the left and never raises",
                        hint='key, sep, value = line.partition("=")'),
            ForbidCall(("split",), because="split(\"=\", 1) works but partition handles the missing case for you"),
        ),
    ),
    Method(
        display="REDACT",
        signature="(text: str, secret: str) -> str",
        doc='Every occurrence of secret replaced with "***".',
        constraint_note="use replace",
        constraints=(RequireCall(("replace",), because="this drill is about replace",
                                 hint='text.replace(secret, "***")'),),
    ),
    Method(
        display="SAME_WORD",
        signature="(a: str, b: str) -> bool",
        doc="True when a and b are the same word ignoring case.",
        constraint_note="use casefold, not lower",
        constraints=(
            RequireCall(("casefold",), because="casefold handles cases lower() does not, e.g. German ss",
                        hint="a.casefold() == b.casefold()"),
            ForbidCall(("lower", "upper"), because="lower() is the almost-right answer"),
        ),
    ),
    Method(
        display="IS_IMAGE",
        signature="(name: str) -> bool",
        doc="True when the name ends in .png, .jpg or .gif.",
        constraint_note="one endswith call with a tuple; no `or` chain",
        constraints=(
            RequireCall(("endswith",), because="endswith takes a tuple of suffixes",
                        hint='name.endswith((".png", ".jpg", ".gif"))'),
            Forbid(("for", "comprehension"), because="one call does it"),
        ),
    ),
    Method(
        display="TICKET",
        signature="(number: int) -> str",
        doc='The number as a 5-character string, zero-padded: 42 -> "00042".',
        constraint_note="use zfill or an f-string width; no manual padding loop",
        constraints=(
            Forbid(("for", "while"), because="padding is formatting, not iteration",
                   hint='str(number).zfill(5)   or   f"{number:05d}"'),
        ),
    ),
    Method(
        display="ALIGNED",
        signature="(rows: list[tuple[str, float]]) -> list[str]",
        doc='Each row as "name" left-padded to 8 characters then the value to 2 decimals.',
        constraint_note="f-string format specs: :<8 and :.2f",
        constraints=(
            ForbidCall(("round",), because="formatting to 2 decimals is a format spec, not arithmetic",
                       hint='f"{name:<8}{value:.2f}"'),
        ),
    ),
    Method(
        display="LETTERS_ONLY",
        signature="(text: str) -> str",
        doc="text with every ASCII punctuation character removed.",
        constraint_note="use str.translate with str.maketrans",
        constraints=(
            RequireCall(("translate",), because="translate does one pass; a replace chain does one pass each",
                        hint='text.translate(str.maketrans("", "", string.punctuation))'),
            Forbid(("for", "comprehension"), because="translate is the loop"),
        ),
    ),
    Method(
        display="FIND_AT",
        signature="(text: str, needle: str) -> int",
        doc="The index of the first occurrence, or -1 when absent.",
        constraint_note="use find, not index — index raises",
        constraints=(
            RequireCall(("find",), because="find returns -1; index raises ValueError",
                        hint="text.find(needle)"),
            ForbidCall(("index",), because="index raises when absent, which is not what -1 means"),
        ),
    ),
    # Checkpoint: no constraints.
    Method(
        display="PARSE_LOG",
        signature="(line: str) -> dict",
        doc=(
            'Parse "2026-01-02 ERROR  disk=/dev/sda1 free=12.5" into '
            '{"date":..., "level":..., "disk":..., "free":...} with free as a float. '
            "Return {} for a line that does not match that shape."
        ),
        constraint_note="checkpoint: no constraints — pick the right tools yourself",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "String manipulation", theme="the method you want already exists"),)

TAG_GLOSSARY = {
    "strip": "trimming and removing affixes",
    "join": "building strings from parts",
    "split": "splitting on a delimiter",
    "partition": "splitting exactly once",
    "replace": "substitution",
    "case": "case-insensitive comparison",
    "suffix": "prefix and suffix tests",
    "format": "padding, width and precision",
    "translate": "bulk character removal",
    "search": "finding a substring",
    "edge-values": "empty strings, missing separators, no match",
    "checkpoint": "the whole unit at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)],
                tags=tags, visible=visible, doc=doc)


CASES = [
    _c("trimmed_both_ends", "TRIMMED", "  hi  ", ret="hi", tags=["strip"], visible=True,
       doc="Whitespace from both ends, nothing from the middle."),
    _c("trimmed_inner_kept", "TRIMMED", "  a b  ", ret="a b", tags=["strip"]),
    _c("trimmed_nothing_to_do", "TRIMMED", "hi", ret="hi", tags=["strip", "edge-values"]),
    _c("trimmed_all_space", "TRIMMED", "   ", ret="", tags=["strip", "edge-values"]),

    _c("unwrap_both", "UNWRAP", "tmp_report.bak", ret="report", tags=["strip"], visible=True,
       doc="Both affixes go when both are present."),
    _c("unwrap_neither", "UNWRAP", "report", ret="report", tags=["strip"], visible=True,
       doc="Absent affixes are not an error, and nothing else is removed."),
    _c("unwrap_prefix_only", "UNWRAP", "tmp_report", ret="report", tags=["strip"]),
    _c("unwrap_not_at_the_edge", "UNWRAP", "a_tmp_b.bak.c", ret="a_tmp_b.bak.c",
       tags=["strip", "edge-values"],
       why="removeprefix/removesuffix only match at the very ends"),

    _c("sentence_basic", "SENTENCE", ["a", "b", "c"], ret="a b c", tags=["join"], visible=True,
       doc="Single spaces between, none at the ends."),
    _c("sentence_one", "SENTENCE", ["only"], ret="only", tags=["join", "edge-values"]),
    _c("sentence_empty", "SENTENCE", [], ret="", tags=["join", "edge-values"]),

    _c("fields_basic", "FIELDS", "a, b ,c", ret=["a", "b", "c"], tags=["split"], visible=True,
       doc="Split on commas, then trim each field."),
    _c("fields_one", "FIELDS", "solo", ret=["solo"], tags=["split", "edge-values"]),
    _c("fields_empty_field", "FIELDS", "a,,b", ret=["a", "", "b"], tags=["split", "edge-values"],
       why="an empty field is a field"),

    _c("extension_basic", "EXTENSION", "report.tar.gz", ret="gz", tags=["partition"], visible=True,
       doc="After the LAST dot."),
    _c("extension_none", "EXTENSION", "README", ret="", tags=["partition"], visible=True,
       doc='No dot means "" — this is where split("." )[-1] gets it wrong.'),
    _c("extension_dotfile", "EXTENSION", ".bashrc", ret="bashrc",
       tags=["partition", "edge-values"]),
    _c("extension_trailing_dot", "EXTENSION", "odd.", ret="", tags=["partition", "edge-values"]),

    _c("basename_basic", "BASENAME", "/a/b/c.txt", ret="c.txt", tags=["partition"], visible=True,
       doc="After the last slash."),
    _c("basename_no_slash", "BASENAME", "c.txt", ret="c.txt", tags=["partition"]),
    _c("basename_trailing_slash", "BASENAME", "/a/b/", ret="",
       tags=["partition", "edge-values"]),

    _c("key_value_basic", "KEY_VALUE", "a=b=c", ret=("a", "b=c"), tags=["partition"], visible=True,
       doc="Split on the FIRST separator only."),
    _c("key_value_missing", "KEY_VALUE", "flag", ret=("flag", ""), tags=["partition"], visible=True,
       doc='No separator: the whole string is the key and the value is "".'),
    _c("key_value_empty_value", "KEY_VALUE", "a=", ret=("a", ""), tags=["partition", "edge-values"]),

    _c("redact_basic", "REDACT", "token=abc123 again abc123", "abc123",
       ret="token=*** again ***", tags=["replace"], visible=True, doc="Every occurrence."),
    _c("redact_absent", "REDACT", "nothing here", "abc", ret="nothing here", tags=["replace"]),
    _c("redact_whole_string", "REDACT", "abc", "abc", ret="***", tags=["replace", "edge-values"]),

    _c("same_word_case", "SAME_WORD", "Ada", "ada", ret=True, tags=["case"], visible=True,
       doc="Case is ignored."),
    _c("same_word_different", "SAME_WORD", "ada", "bob", ret=False, tags=["case"]),
    _c("same_word_sharp_s", "SAME_WORD", "strasse", "STRASSE", ret=True,
       tags=["case", "edge-values"]),

    _c("is_image_png", "IS_IMAGE", "a.png", ret=True, tags=["suffix"], visible=True,
       doc="Any of the three extensions."),
    _c("is_image_txt", "IS_IMAGE", "a.txt", ret=False, tags=["suffix"]),
    _c("is_image_substring", "IS_IMAGE", "png.txt", ret=False, tags=["suffix", "edge-values"],
       why="the extension has to be at the END"),

    _c("ticket_pads", "TICKET", 42, ret="00042", tags=["format"], visible=True,
       doc="Five characters, zero-padded on the left."),
    _c("ticket_exact", "TICKET", 12345, ret="12345", tags=["format"]),
    _c("ticket_zero", "TICKET", 0, ret="00000", tags=["format", "edge-values"]),

    # 22.126 rather than 22.125 on purpose: .125 is not exactly representable, so
    # f"{22.125:.2f}" is "22.12". That trap is real and belongs in unit 1.3 (numbers);
    # here it would only obscure the lesson, which is the format spec.
    _c("aligned_basic", "ALIGNED", [("ada", 1.5), ("bob", 22.126)],
       ret=["ada     1.50", "bob     22.13"], tags=["format"], visible=True,
       doc="Name padded to 8, value to 2 decimals."),
    _c("aligned_long_name", "ALIGNED", [("verylongname", 1.0)], ret=["verylongname1.00"],
       tags=["format", "edge-values"],
       why="a name longer than the width is not truncated"),
    _c("aligned_empty", "ALIGNED", [], ret=[], tags=["format", "edge-values"]),

    _c("letters_only_basic", "LETTERS_ONLY", "Hi, there! (ok)", ret="Hi there ok",
       tags=["translate"], visible=True, doc="Punctuation removed; spaces and letters kept."),
    _c("letters_only_nothing", "LETTERS_ONLY", "plain", ret="plain", tags=["translate"]),
    _c("letters_only_all_punct", "LETTERS_ONLY", "!!!", ret="",
       tags=["translate", "edge-values"]),

    _c("find_at_found", "FIND_AT", "hello", "ll", ret=2, tags=["search"], visible=True,
       doc="The index of the first match."),
    _c("find_at_absent", "FIND_AT", "hello", "z", ret=-1, tags=["search"], visible=True,
       doc="-1 when absent — not an exception."),
    _c("find_at_empty_needle", "FIND_AT", "hello", "", ret=0, tags=["search", "edge-values"]),

    _c("parse_log_basic", "PARSE_LOG", "2026-01-02 ERROR  disk=/dev/sda1 free=12.5",
       ret={"date": "2026-01-02", "level": "ERROR", "disk": "/dev/sda1", "free": 12.5},
       tags=["checkpoint"], visible=True,
       doc="free is a float. Note the double space after the level."),
    _c("parse_log_other_level", "PARSE_LOG", "2026-03-04 WARN  disk=/dev/sdb free=0.0",
       ret={"date": "2026-03-04", "level": "WARN", "disk": "/dev/sdb", "free": 0.0},
       tags=["checkpoint"]),
    _c("parse_log_malformed", "PARSE_LOG", "not a log line", ret={},
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A line that does not match the shape gives {}."),
    _c("parse_log_empty", "PARSE_LOG", "", ret={}, tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="strings",
    title="1.2 String manipulation",
    blurb="strip, partition, join, replace, translate and the format specs that replace loops.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("strip", "partition", "join", "translate", "format"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.2 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
