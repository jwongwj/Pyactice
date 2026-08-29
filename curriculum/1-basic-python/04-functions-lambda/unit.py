"""1.4 Functions, lambda and key= — defaults, *args, and the functional toolkit.

Self-contained: loaded by file path, so no package-relative imports.

The centre of this unit is `key=`. Sorting, min, max and the heap helpers all take it,
and once you can write one you can write all of them. The mutable-default drill is here
because it is the one Python gotcha that bites in production rather than in interviews.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall, RequireConstruct
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="GREET",
        signature="(name: str, greeting: str = 'Hello') -> str",
        doc='"<greeting>, <name>!" — greeting defaults to "Hello".',
        constraint_note="use a real default argument; no `if` to fill it in",
        constraints=(
            Forbid(("if",), because="that is what a default argument is for",
                   hint='def greet(name, greeting="Hello")'),
        ),
    ),
    Method(
        display="COLLECT",
        signature="(item: int, into: list | None = None) -> list",
        doc="Append item to `into` and return it. A fresh list when `into` is not given.",
        constraint_note="the default must NOT be a mutable literal",
        constraints=(
            Forbid(("mutable-default",),
                   because="a default is evaluated once at definition time, so one list is "
                           "shared by every call that omits the argument",
                   hint="into: list | None = None, then create the list inside"),
        ),
    ),
    Method(
        display="TALLY",
        signature="(*values: int) -> int",
        doc="The sum of however many arguments are passed. 0 for none.",
        constraint_note="use *args; no list parameter",
        constraints=(
            RequireCall(("sum",), because="*values arrives as a tuple, which sum takes directly",
                        hint="def tally(*values): return sum(values)"),
            Forbid(("for", "while"), because="sum is the loop"),
        ),
    ),
    Method(
        display="SETTINGS",
        signature="(**options: object) -> list[str]",
        doc='["key=value", ...] for every keyword argument, sorted by key.',
        constraint_note="use **kwargs and sorted",
        constraints=(
            RequireCall(("sorted",), because="dict order is insertion order, not sorted order",
                        hint='[f"{k}={options[k]}" for k in sorted(options)]'),
        ),
    ),
    Method(
        display="BY_LENGTH",
        signature="(words: list[str]) -> list[str]",
        doc="The words shortest first, ties broken alphabetically.",
        constraint_note="one sorted call with a compound key; no second sort",
        constraints=(
            RequireCall(("sorted",), because="key= computes the ordering without touching the values",
                        hint="sorted(words, key=lambda w: (len(w), w))"),
            Forbid(("for", "while"), because="sorted is the loop"),
        ),
    ),
    Method(
        display="BY_SCORE",
        signature="(rows: list[dict]) -> list[str]",
        doc="Names ordered by 'score' descending, ties by name ascending.",
        constraint_note="use a lambda key returning a tuple; negate to reverse one part",
        constraints=(
            RequireConstruct("lambda", because="two directions in one key needs an expression",
                             hint='sorted(rows, key=lambda r: (-r["score"], r["name"]))'),
        ),
    ),
    Method(
        display="FIELD_SORT",
        signature="(pairs: list[tuple]) -> list[tuple]",
        doc="Pairs sorted by their SECOND element.",
        constraint_note="use operator.itemgetter, not a lambda",
        constraints=(
            RequireCall(("itemgetter",), because="itemgetter says what it selects and is faster",
                        hint="sorted(pairs, key=operator.itemgetter(1))"),
            Forbid(("lambda",), because="this drill is about the operator module"),
        ),
    ),
    Method(
        display="DOUBLED",
        signature="(numbers: list[int]) -> list[int]",
        doc="Every number doubled.",
        constraint_note="use map; no comprehension and no loop",
        constraints=(
            RequireCall(("map",), because="this drill is about map",
                        hint="list(map(lambda n: n * 2, numbers))"),
            Forbid(("for", "comprehension"), because="practise map here"),
        ),
    ),
    Method(
        display="POSITIVES",
        signature="(numbers: list[int]) -> list[int]",
        doc="Only the numbers greater than zero.",
        constraint_note="use filter; no comprehension and no loop",
        constraints=(
            RequireCall(("filter",), because="this drill is about filter",
                        hint="list(filter(lambda n: n > 0, numbers))"),
            Forbid(("for", "comprehension"), because="practise filter here"),
        ),
    ),
    Method(
        display="SHOUT_LONG",
        signature="(words: list[str]) -> list[str]",
        doc="Words longer than three characters, upper-cased.",
        # The counterweight: map(lambda) + filter(lambda) is the version everyone
        # writes once and nobody enjoys reading.
        constraint_note="this one wants a comprehension — map+filter with two lambdas is worse",
        constraints=(
            RequireConstruct("comprehension",
                             because="transform-and-filter together is exactly what a "
                                     "comprehension says more clearly than nested calls",
                             hint="[w.upper() for w in words if len(w) > 3]"),
            ForbidCall(("map", "filter"), because="two lambdas nested is harder to read, not cleverer"),
        ),
    ),
    Method(
        display="ROUNDED",
        signature="(numbers: list[float], places: int) -> list[float]",
        doc="Every number rounded to `places` decimal places.",
        # Returning a function would be the purer demonstration of partial, but the
        # grader compares return values and cannot compare two functions -- an
        # untestable drill is worse than a slightly less pure one. Pre-binding a
        # keyword for map() is what partial is actually used for anyway.
        constraint_note="use functools.partial to pre-bind places; no lambda",
        constraints=(
            RequireCall(("partial",), because="partial pre-binds an argument without writing a closure",
                        hint="map(functools.partial(round, ndigits=places), numbers)"),
            Forbid(("lambda",), because="this drill is about partial, which replaces this lambda"),
        ),
    ),
    Method(
        display="JOIN_ALL",
        signature="(parts: list[str]) -> str",
        doc='Fold the parts into one string separated by " > ". "" for none.',
        constraint_note="use functools.reduce; not str.join",
        constraints=(
            RequireCall(("reduce",), because="this drill is about folding, which join hides",
                        hint='functools.reduce(lambda a, b: f"{a} > {b}", parts, "")'),
            ForbidCall(("join",), because="join is the right answer in real code; reduce is the lesson here"),
        ),
    ),
    Method(
        display="LEADERBOARD",
        signature="(rows: list[dict], top: int) -> list[str]",
        doc=(
            'The top N as "name (score)", score descending, ties by name ascending. '
            "Rows whose score is None are excluded."
        ),
        constraint_note="checkpoint: no constraints — pick the right tools yourself",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Functions, lambda and key=", theme="key= is the whole unit"),)

TAG_GLOSSARY = {
    "defaults": "default arguments and the mutable-default trap",
    "varargs": "*args and **kwargs",
    "key": "sorting by a computed value",
    "operator": "the operator module",
    "map-filter": "map and filter",
    "functools": "partial and reduce",
    "edge-values": "empty input, ties, no arguments",
    "checkpoint": "the whole unit at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)],
                tags=tags, visible=visible, doc=doc)


CASES = [
    _c("greet_default", "GREET", "Ada", ret="Hello, Ada!", tags=["defaults"], visible=True,
       doc="The default is used when the argument is omitted."),
    _c("greet_override", "GREET", "Ada", "Hi", ret="Hi, Ada!", tags=["defaults"]),
    _c("greet_empty_name", "GREET", "", ret="Hello, !", tags=["defaults", "edge-values"]),

    _c("collect_fresh", "COLLECT", 1, ret=[1], tags=["defaults"], visible=True,
       doc="A new list each time the argument is omitted."),
    _c("collect_given", "COLLECT", 3, [1, 2], ret=[1, 2, 3], tags=["defaults"]),
    # The trap, caught by behaviour as well as by the constraint: two separate calls
    # that both omit the argument must not share a list.
    case("collect_does_not_accumulate", 1,
         [op("COLLECT", 1, ret=[1]), op("COLLECT", 2, ret=[2])],
         tags=["defaults", "edge-values"], visible=True,
         doc="Two calls that omit the list must not share one — this is the famous trap."),

    _c("tally_several", "TALLY", 1, 2, 3, ret=6, tags=["varargs"], visible=True,
       doc="However many arguments are given."),
    _c("tally_one", "TALLY", 5, ret=5, tags=["varargs"]),
    _c("tally_none", "TALLY", ret=0, tags=["varargs", "edge-values"], visible=True,
       doc="No arguments at all sums to 0."),

    case("settings_sorted", 1,
         [op("SETTINGS", kw={"b": 2, "a": 1}, ret=["a=1", "b=2"])],
         tags=["varargs"], visible=True,
         doc="Sorted by key — dict order is insertion order, which is not the same thing."),
    case("settings_one", 1, [op("SETTINGS", kw={"only": "x"}, ret=["only=x"])],
         tags=["varargs"]),
    case("settings_none", 1, [op("SETTINGS", ret=[])],
         tags=["varargs", "edge-values"]),
    case("settings_mixed_values", 1,
         [op("SETTINGS", kw={"n": 1, "flag": True}, ret=["flag=True", "n=1"])],
         tags=["varargs", "edge-values"]),

    _c("by_length_basic", "BY_LENGTH", ["ccc", "a", "bb"], ret=["a", "bb", "ccc"],
       tags=["key"], visible=True, doc="Shortest first."),
    _c("by_length_ties", "BY_LENGTH", ["bb", "aa", "c"], ret=["c", "aa", "bb"],
       tags=["key"], visible=True, doc="Equal lengths are ordered alphabetically."),
    _c("by_length_empty", "BY_LENGTH", [], ret=[], tags=["key", "edge-values"]),

    _c("by_score_basic", "BY_SCORE",
       [{"name": "ada", "score": 90}, {"name": "bob", "score": 95}],
       ret=["bob", "ada"], tags=["key"], visible=True, doc="Highest score first."),
    _c("by_score_ties", "BY_SCORE",
       [{"name": "cyd", "score": 90}, {"name": "ada", "score": 90}],
       ret=["ada", "cyd"], tags=["key"], visible=True,
       doc="Equal scores go alphabetically — two directions in one key."),
    _c("by_score_empty", "BY_SCORE", [], ret=[], tags=["key", "edge-values"]),

    _c("field_sort_basic", "FIELD_SORT", [("a", 3), ("b", 1), ("c", 2)],
       ret=[("b", 1), ("c", 2), ("a", 3)], tags=["operator"], visible=True,
       doc="Ordered by the second element."),
    _c("field_sort_one", "FIELD_SORT", [("a", 1)], ret=[("a", 1)], tags=["operator"]),
    _c("field_sort_empty", "FIELD_SORT", [], ret=[], tags=["operator", "edge-values"]),

    _c("doubled_basic", "DOUBLED", [1, 2, 3], ret=[2, 4, 6], tags=["map-filter"], visible=True,
       doc="map returns an iterator, so wrap it in list()."),
    _c("doubled_empty", "DOUBLED", [], ret=[], tags=["map-filter", "edge-values"]),
    _c("doubled_negative", "DOUBLED", [-2], ret=[-4], tags=["map-filter"]),

    _c("positives_basic", "POSITIVES", [-1, 0, 1, 2], ret=[1, 2], tags=["map-filter"],
       visible=True, doc="Zero is not positive."),
    _c("positives_none", "POSITIVES", [-1, -2], ret=[], tags=["map-filter"]),
    _c("positives_empty", "POSITIVES", [], ret=[], tags=["map-filter", "edge-values"]),

    _c("shout_long_basic", "SHOUT_LONG", ["a", "abcd", "xyz", "hello"],
       ret=["ABCD", "HELLO"], tags=["map-filter"], visible=True,
       doc="Longer than three, then upper-cased."),
    _c("shout_long_boundary", "SHOUT_LONG", ["abc"], ret=[],
       tags=["map-filter", "edge-values"], why="longer than three means four or more"),
    _c("shout_long_empty", "SHOUT_LONG", [], ret=[], tags=["map-filter", "edge-values"]),

    _c("rounded_basic", "ROUNDED", [1.234, 5.678], 2, ret=[1.23, 5.68],
       tags=["functools"], visible=True, doc="Each number to the given number of places."),
    _c("rounded_zero_places", "ROUNDED", [1.6, 2.4], 0, ret=[2.0, 2.0],
       tags=["functools", "edge-values"],
       why="round(x, 0) returns a float, and 2.4 rounds to 2.0"),
    _c("rounded_empty", "ROUNDED", [], 2, ret=[], tags=["functools", "edge-values"]),

    _c("join_all_basic", "JOIN_ALL", ["a", "b", "c"], ret=" > a > b > c",
       tags=["functools"], visible=True,
       doc='Folding from an empty seed puts a separator at the front — that is what reduce does here.'),
    _c("join_all_one", "JOIN_ALL", ["only"], ret=" > only", tags=["functools"]),
    _c("join_all_empty", "JOIN_ALL", [], ret="", tags=["functools", "edge-values"]),

    _c("leaderboard_basic", "LEADERBOARD",
       [{"name": "ada", "score": 90}, {"name": "bob", "score": 95},
        {"name": "cyd", "score": 80}], 2,
       ret=["bob (95)", "ada (90)"], tags=["checkpoint"], visible=True,
       doc="Top 2, score descending."),
    _c("leaderboard_skips_none", "LEADERBOARD",
       [{"name": "ada", "score": None}, {"name": "bob", "score": 95}], 2,
       ret=["bob (95)"], tags=["checkpoint"], visible=True,
       doc="A None score is excluded, and does not leave a gap."),
    _c("leaderboard_top_bigger_than_rows", "LEADERBOARD",
       [{"name": "ada", "score": 1}], 5, ret=["ada (1)"], tags=["checkpoint"]),
    _c("leaderboard_zero_top", "LEADERBOARD",
       [{"name": "ada", "score": 1}], 0, ret=[], tags=["checkpoint", "edge-values"]),
    _c("leaderboard_empty", "LEADERBOARD", [], 3, ret=[], tags=["checkpoint", "edge-values"]),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="functions_lambda",
    title="1.4 Functions, lambda and key=",
    blurb="Default arguments, *args, key= for every sort, map, filter, partial and reduce.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="basic-python",
    difficulty="easy",
    topics=("defaults", "key", "map-filter", "functools"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 1.4 — see docs/CATALOGUE.md",
)

# Authored as one unit; practised as one problem per drill. See harness/units.py for
# why the two differ.
PROBLEMS = split(UNIT)
