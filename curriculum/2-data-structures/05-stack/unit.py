"""2.5 Stack — last in, first out, and the monotonic trick that makes it powerful.

Self-contained: loaded by file path, so no package-relative imports.

A Python list already is a stack: `append` and `pop` are both O(1) at the end. So there is
nothing to build here, and the drills are about recognising the shape of a problem that
wants one -- matching pairs, deferred decisions, and "the next thing bigger than this".

The catalogue's MinStack is a class with O(1) `min()`, so it arrives as a `design` problem
rather than a drill.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="BALANCED",
        signature="(text: str) -> bool",
        doc="True when every bracket closes in the right order. Handles (), [] and {}. "
            "Other characters are ignored.",
        constraint_note="one pass with a stack; no counters and no repeated replace()",
        constraints=(
            ForbidCall(("replace", "count"),
                       because="counting brackets cannot tell \"([)]\" from \"([])\", and "
                               "stripping pairs in a loop is quadratic",
                       hint="push openers, and on a closer check it matches the top"),
        ),
    ),
    Method(
        display="EVAL_RPN",
        signature="(tokens: list[str]) -> int",
        doc="Value of a reverse-Polish expression. Operators are + - * /, and division "
            "truncates towards zero. An empty token list is 0.",
        constraint_note="one pass with a stack; no eval() and no recursion",
        constraints=(
            ForbidCall(("eval", "exec"),
                       because="eval runs arbitrary code and answers a different question "
                               "than the one asked",
                       hint="push numbers; on an operator pop two, apply, push the result"),
            Forbid(("recursion",),
                   because="postfix needs no recursion -- that is the point of it",
                   hint="a single left-to-right pass over the tokens"),
        ),
    ),
    Method(
        display="APPLY_UNDO",
        signature="(actions: list[str]) -> list[str]",
        doc='Each action is a word, or "undo" which cancels the most recent surviving '
            'action. "undo" with nothing to cancel is ignored.',
        constraint_note="the history IS the stack; push and pop as you go",
        constraints=(
            ForbidCall(("reverse", "reversed"),
                       because="a stack read in order is already the history; reversing it "
                               "means you built the wrong thing",
                       hint="append a word, pop on \"undo\", and guard the empty pop"),
        ),
    ),
    Method(
        display="NEXT_GREATER",
        signature="(nums: list[int]) -> list[int]",
        doc="For each position, the next value to its right that is strictly greater, "
            "or -1 when there is none.",
        # The naive answer is a nested loop and is quadratic. A monotonic stack is linear,
        # and is the same idea as DAILY_WAIT below wearing different clothes.
        constraint_note="one pass with a decreasing stack; no nested loop over nums",
        constraints=(
            Forbid(("comprehension",),
                   because="the nested scan is O(n^2); a stack of positions still waiting "
                           "for their answer is O(n)",
                   hint="keep a stack of INDICES whose answer is unknown; when a bigger "
                        "value arrives, it is the answer for everything it beats"),
        ),
    ),
    Method(
        display="DAILY_WAIT",
        signature="(temps: list[int]) -> list[int]",
        doc="For each day, how many days until a strictly warmer one, or 0 if none comes.",
        constraint_note="the same monotonic stack as NEXT_GREATER, answering in distances",
        constraints=(
            Forbid(("comprehension",),
                   because="this is NEXT_GREATER with the index difference instead of the "
                           "value -- recognising that is the drill",
                   hint="stack of indices; on a warmer day, answer = today - popped index"),
        ),
    ),
    Method(
        display="LARGEST_RECTANGLE",
        fuzz=("nonneg",),
        signature="(heights: list[int]) -> int",
        doc="Area of the largest rectangle that fits under the histogram, where each bar "
            "is 1 wide. 0 for no bars.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Stack", theme="last in, first out -- and the monotonic stack"),)

TAG_GLOSSARY = {
    "matching": "pairs that must close in order",
    "postfix": "evaluating an expression with no parentheses",
    "history": "undo and deferred state",
    "monotonic": "a stack kept in sorted order to answer 'the next bigger one'",
    "off-by-one": "which slot an answer is written into, and which half is discarded",
    "edge-values": "empty inputs, single items, nothing to pop",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("balanced_simple", "BALANCED", "([]{})", ret=True,
       tags=["matching"], visible=True, doc="Every bracket closes in order."),
    _c("balanced_interleaved", "BALANCED", "([)]", ret=False,
       tags=["matching"], visible=True,
       doc="The counts are right and the order is not. This is the case a counter "
           "cannot distinguish from \"([])\"."),
    _c("balanced_unclosed", "BALANCED", "(", ret=False, tags=["matching", "edge-values"]),
    _c("balanced_extra_closer", "BALANCED", ")", ret=False,
       tags=["matching", "edge-values"], why="a closer with an empty stack must not pop"),
    _c("balanced_empty", "BALANCED", "", ret=True, tags=["matching", "edge-values"],
       visible=True, doc="Nothing unbalanced about nothing."),
    _c("balanced_other_chars", "BALANCED", "a(b)c", ret=True, tags=["matching"],
       why="non-bracket characters are ignored, not rejected"),
    _c("balanced_wrong_type", "BALANCED", "(]", ret=False, tags=["matching"],
       why="the closer must match the TYPE on top, not merely find something there"),

    _c("rpn_basic", "EVAL_RPN", ["2", "3", "+"], ret=5,
       tags=["postfix"], visible=True, doc="2 + 3."),
    _c("rpn_nested", "EVAL_RPN", ["2", "3", "+", "4", "*"], ret=20,
       tags=["postfix"], visible=True, doc="(2 + 3) * 4, with no parentheses needed."),
    _c("rpn_order_matters", "EVAL_RPN", ["5", "3", "-"], ret=2,
       tags=["postfix"], visible=True,
       doc="The FIRST popped value is the right operand: 5 - 3, not 3 - 5."),
    _c("rpn_truncates_toward_zero", "EVAL_RPN", ["-7", "2", "/"], ret=-3,
       tags=["postfix", "edge-values"], visible=True,
       doc="-7 / 2 truncates towards zero, so -3. Python's // would floor to -4."),
    _c("rpn_single_number", "EVAL_RPN", ["42"], ret=42, tags=["postfix", "edge-values"]),
    _c("rpn_negative_literal", "EVAL_RPN", ["-3", "-4", "*"], ret=12,
       tags=["postfix", "edge-values"],
       why="a leading minus is part of the number; isdigit() alone would reject it"),
    _c("rpn_empty", "EVAL_RPN", [], ret=0, tags=["postfix", "edge-values"]),

    _c("undo_basic", "APPLY_UNDO", ["a", "b", "undo"], ret=["a"],
       tags=["history"], visible=True, doc="The most recent action is cancelled."),
    _c("undo_twice", "APPLY_UNDO", ["a", "b", "undo", "undo"], ret=[],
       tags=["history"], visible=True, doc="Two undos remove two actions."),
    _c("undo_empty_history", "APPLY_UNDO", ["undo", "a"], ret=["a"],
       tags=["history", "edge-values"], visible=True,
       doc="An undo with nothing to cancel is ignored rather than an error."),
    _c("undo_then_more", "APPLY_UNDO", ["a", "undo", "b"], ret=["b"], tags=["history"],
       why="the undo applies at the moment it appears, not to the final list"),
    _c("undo_none", "APPLY_UNDO", [], ret=[], tags=["history", "edge-values"]),
    _c("undo_over_undo", "APPLY_UNDO", ["a", "undo", "undo"], ret=[],
       tags=["history", "edge-values"],
       why="the second undo has nothing left and must not remove a surviving action"),

    _c("next_greater_basic", "NEXT_GREATER", [2, 1, 3], ret=[3, 3, -1],
       tags=["monotonic"], visible=True, doc="3 is next-greater for both 2 and 1."),
    _c("next_greater_descending", "NEXT_GREATER", [3, 2, 1], ret=[-1, -1, -1],
       tags=["monotonic"], visible=True, doc="Nothing to the right is ever bigger."),
    _c("next_greater_equal_not_greater", "NEXT_GREATER", [2, 2, 3], ret=[3, 3, -1],
       tags=["monotonic", "edge-values"], visible=True,
       doc="Strictly greater, so an equal value does not answer it."),
    _c("next_greater_single", "NEXT_GREATER", [5], ret=[-1],
       tags=["monotonic", "edge-values"]),
    # From `drill_mutation.py --triage`: every other case here has either all positions
    # answered or none. A list where the FIRST is unanswered and a LATER one is answered
    # is what separates a correct default from one written into the wrong slot.
    _c("next_greater_first_unanswered", "NEXT_GREATER", [5, -1, 3], ret=[-1, 3, -1],
       tags=["monotonic", "off-by-one"], visible=True,
       doc="Nothing beats the leading 5, the -1 is answered by 3, and the 3 has nothing "
           "to its right."),
    _c("next_greater_empty", "NEXT_GREATER", [], ret=[], tags=["monotonic", "edge-values"]),

    _c("daily_wait_basic", "DAILY_WAIT", [30, 40, 50], ret=[1, 1, 0],
       tags=["monotonic"], visible=True, doc="Each next day is warmer."),
    _c("daily_wait_gap", "DAILY_WAIT", [50, 30, 40, 60], ret=[3, 1, 1, 0],
       tags=["monotonic"], visible=True,
       doc="Day 0 waits three days for 60 -- the distance, not the temperature."),
    _c("daily_wait_never", "DAILY_WAIT", [50, 50], ret=[0, 0],
       tags=["monotonic", "edge-values"], visible=True,
       doc="Equal is not warmer, so neither day is ever answered."),
    _c("daily_wait_empty", "DAILY_WAIT", [], ret=[], tags=["monotonic", "edge-values"]),

    _c("rect_basic", "LARGEST_RECTANGLE", [2, 1, 5, 6, 2, 3], ret=10,
       tags=["checkpoint"], visible=True,
       doc="The 5 and 6 together give 2 wide x 5 high."),
    _c("rect_uniform", "LARGEST_RECTANGLE", [3, 3, 3], ret=9,
       tags=["checkpoint"], visible=True, doc="Three bars of 3 is one rectangle of 9."),
    _c("rect_single", "LARGEST_RECTANGLE", [4], ret=4, tags=["checkpoint", "edge-values"]),
    _c("rect_empty", "LARGEST_RECTANGLE", [], ret=0, tags=["checkpoint", "edge-values"]),
    _c("rect_zero_bar_splits", "LARGEST_RECTANGLE", [2, 0, 2], ret=2,
       tags=["checkpoint", "edge-values"], visible=True,
       doc="A bar of height 0 divides the histogram: the answer cannot span it."),
    _c("rect_ascending", "LARGEST_RECTANGLE", [1, 2, 3, 4], ret=6,
       tags=["checkpoint", "edge-values"],
       why="3 wide x 2 high beats 1x4 and 4x1 -- the best rectangle is interior"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="stacks",
    title="2.5 Stack",
    blurb="Balanced brackets, RPN, undo history and the monotonic stack.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("matching", "monotonic", "postfix"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.5 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
