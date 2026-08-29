"""Expectation values and the comparison engine.

The assessment's real graders are strict about return types. Practice graders that
are *equally* strict waste the candidate's time arguing about `100` vs `"100"`, and
practice graders that are sloppy teach bad habits. So this module distinguishes
three outcomes rather than two:

    EXACT    - matches the declared contract precisely
    LENIENT  - semantically right, wrong representation (str/int, [] vs None, ...)
    MISMATCH - wrong

`pfs test` fails LENIENT results by default but labels them unmistakably, so the
candidate learns "read the type hints" without losing ten minutes to it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


class _Any:
    """Sentinel: this operation's return value is not checked."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "ANY"


ANY = _Any()


@dataclass(frozen=True)
class Raises:
    """Sentinel: this operation must raise."""

    kind: type = Exception

    def __repr__(self) -> str:
        return f"Raises({self.kind.__name__})"


class Unordered:
    """Sequence comparison that ignores order (multiset semantics)."""

    __slots__ = ("items",)

    def __init__(self, items):
        self.items = list(items)

    def __repr__(self) -> str:
        return f"Unordered({self.items!r})"


class Exactly:
    """Disable leniency for one expectation.

    Needed where a problem treats an "empty" value as a real value -- a database
    whose fields can hold `""` must distinguish `""` from `None`, and the usual
    "both mean nothing" leniency would wave that through.
    """

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __repr__(self) -> str:
        return f"exactly {self.value!r}"


class OneOf:
    """Any of several accepted values.

    Used only where the published problem statement is genuinely ambiguous and the
    real assessment is known to accept more than one reading. Every use must be
    justified in the problem's DECISIONS.md.
    """

    __slots__ = ("options",)

    def __init__(self, *options):
        self.options = list(options)

    def __repr__(self) -> str:
        return f"OneOf({', '.join(repr(o) for o in self.options)})"


class Grade(Enum):
    EXACT = "exact"
    LENIENT = "lenient"
    MISMATCH = "mismatch"


@dataclass(frozen=True)
class Verdict:
    grade: Grade
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.grade is not Grade.MISMATCH


_EXACT = Verdict(Grade.EXACT)

# Values that all mean "nothing to report". A candidate returning `[]` where the
# contract says `None` is right about the logic and wrong about the contract.
_EMPTY_TYPES = (type(None), str, list, tuple, dict, set)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    # Deliberately exclude bool/int/float: 0 and False are values, not absences.
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return False
    if isinstance(value, _EMPTY_TYPES):
        return len(value) == 0
    return False


def _as_number(value: Any):
    """Return a float if `value` is a number or a clean numeric string, else None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _numbers_equal(a: float, b: float) -> bool:
    return a == b or math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, (list, tuple))


def compare(expected: Any, actual: Any) -> Verdict:
    """Compare a contract value against a candidate's return value."""
    if expected is ANY:
        return _EXACT

    if isinstance(expected, Exactly):
        if type(expected.value) is type(actual) and expected.value == actual:
            return _EXACT
        return Verdict(
            Grade.MISMATCH,
            f"must be exactly {expected.value!r} ({type(expected.value).__name__}); "
            f"got {actual!r} ({type(actual).__name__})",
        )

    if isinstance(expected, OneOf):
        best = Verdict(Grade.MISMATCH, f"none of {expected!r}")
        for option in expected.options:
            verdict = compare(option, actual)
            if verdict.grade is Grade.EXACT:
                return verdict
            if verdict.grade is Grade.LENIENT:
                best = verdict
        return best

    if isinstance(expected, Unordered):
        if not _is_sequence(actual):
            return Verdict(Grade.MISMATCH, f"expected a sequence, got {type(actual).__name__}")
        return _compare_unordered(expected.items, list(actual))

    # Fast path: Python equality already agrees.
    try:
        if type(expected) is type(actual) and expected == actual:
            return _EXACT
    except Exception:  # pragma: no cover - exotic __eq__ on candidate objects
        pass

    if _is_empty(expected) and _is_empty(actual):
        if type(expected) is type(actual):
            return _EXACT
        # A SUBCLASS of the contracted type is not a representation error. An empty
        # Counter is an empty dict, and grading it lenient meant the same solution
        # passed `Counter(["a"])` exactly -- the dict branch below uses isinstance --
        # and failed only on empty input, for a reason nothing to do with its logic.
        # `[]` for `None`, `""` for `[]` and `()` for `[]` all still land here, which
        # is what this branch is for.
        if isinstance(actual, type(expected)):
            return _EXACT
        return Verdict(
            Grade.LENIENT,
            f"contract says {expected!r}, you returned {actual!r} (both mean 'nothing')",
        )

    if _is_sequence(expected):
        if not _is_sequence(actual):
            return Verdict(
                Grade.MISMATCH, f"expected a sequence, got {type(actual).__name__}"
            )
        return _compare_ordered(list(expected), list(actual))

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return Verdict(Grade.MISMATCH, f"expected a dict, got {type(actual).__name__}")
        if set(expected) != set(actual):
            return Verdict(Grade.MISMATCH, "different keys")
        worst = Grade.EXACT
        for key in expected:
            verdict = compare(expected[key], actual[key])
            if verdict.grade is Grade.MISMATCH:
                return Verdict(Grade.MISMATCH, f"at key {key!r}: {verdict.note}")
            if verdict.grade is Grade.LENIENT:
                worst = Grade.LENIENT
        return Verdict(worst, "dict values differ only in representation" if worst is Grade.LENIENT else "")

    expected_number = _as_number(expected)
    actual_number = _as_number(actual)
    if expected_number is not None and actual_number is not None:
        if _numbers_equal(expected_number, actual_number):
            if type(expected) is type(actual):
                return _EXACT
            return Verdict(
                Grade.LENIENT,
                f"contract says {type(expected).__name__} {expected!r}, "
                f"you returned {type(actual).__name__} {actual!r}",
            )
        return Verdict(Grade.MISMATCH, "")

    try:
        if expected == actual:
            return Verdict(
                Grade.LENIENT,
                f"equal but different types: {type(expected).__name__} vs {type(actual).__name__}",
            )
    except Exception:  # pragma: no cover
        pass

    return Verdict(Grade.MISMATCH, "")


def _compare_ordered(expected: list, actual: list) -> Verdict:
    if len(expected) != len(actual):
        return Verdict(
            Grade.MISMATCH, f"length {len(actual)}, expected {len(expected)}"
        )
    worst = Grade.EXACT
    notes = []
    for index, (want, got) in enumerate(zip(expected, actual)):
        verdict = compare(want, got)
        if verdict.grade is Grade.MISMATCH:
            return Verdict(Grade.MISMATCH, f"index {index}: {want!r} != {got!r}")
        if verdict.grade is Grade.LENIENT:
            worst = Grade.LENIENT
            if verdict.note:
                notes.append(f"index {index}: {verdict.note}")
    return Verdict(worst, "; ".join(notes))


def _compare_unordered(expected: list, actual: list) -> Verdict:
    if len(expected) != len(actual):
        return Verdict(
            Grade.MISMATCH, f"length {len(actual)}, expected {len(expected)}"
        )
    remaining = list(actual)
    worst = Grade.EXACT
    for want in expected:
        for index, got in enumerate(remaining):
            verdict = compare(want, got)
            if verdict.ok:
                if verdict.grade is Grade.LENIENT:
                    worst = Grade.LENIENT
                remaining.pop(index)
                break
        else:
            return Verdict(Grade.MISMATCH, f"missing {want!r}")
    return Verdict(worst, "order-insensitive match with representation differences" if worst is Grade.LENIENT else "")


def describe(value: Any) -> str:
    """Render a value for a failure message, with its type when that is the story."""
    if value is ANY:
        return "<not checked>"
    if isinstance(value, (Raises, Unordered, OneOf, Exactly)):
        return repr(value)
    return f"{value!r}"
