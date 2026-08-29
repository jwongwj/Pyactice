"""Executes a candidate's solution against a problem's cases.

Design notes:
  * A fresh instance per case. Shared state between cases hides bugs.
  * Per-op wall-clock timeout via `signal.setitimer`, raising a BaseException so a
    candidate's broad `except Exception:` cannot swallow it.
  * `NotImplementedError` is reported as NOT_IMPLEMENTED rather than as a wrong
    answer, so an untouched stub reads as "not done yet" instead of "broken".
  * Missing methods are reported by name, because forgetting to add the level-3
    `*_at` variants is the most common way a run goes entirely red.
"""

from __future__ import annotations

import copy
import importlib.util
import io
import signal
import sys
import time
import traceback
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from . import constraints as constraints_mod
from .expect import ANY, Grade, Raises, Verdict, compare, describe
from .model import KIND_PROGRESSIVE, Case, Method, Op, Problem


class Outcome(Enum):
    PASS = "pass"
    LENIENT = "lenient"
    FAIL = "fail"
    ERROR = "error"
    NOT_IMPLEMENTED = "not_implemented"
    MISSING_METHOD = "missing_method"
    TIMEOUT = "timeout"


_BAD = {
    Outcome.FAIL,
    Outcome.ERROR,
    Outcome.NOT_IMPLEMENTED,
    Outcome.MISSING_METHOD,
    Outcome.TIMEOUT,
}


@dataclass
class OpResult:
    op: Op
    outcome: Outcome
    actual: Any = None
    verdict: Verdict | None = None
    detail: str = ""
    traceback_text: str = ""


@dataclass
class CaseResult:
    case: Case
    outcome: Outcome
    ops: list[OpResult] = field(default_factory=list)
    elapsed_ms: float = 0.0
    stdout: str = ""

    @property
    def passed(self) -> bool:
        return self.outcome is Outcome.PASS

    @property
    def failing_op(self) -> OpResult | None:
        for result in self.ops:
            if result.outcome in _BAD or result.outcome is Outcome.LENIENT:
                return result
        return None

    @property
    def failing_index(self) -> int:
        for index, result in enumerate(self.ops):
            if result.outcome is not Outcome.PASS:
                return index
        return -1


@dataclass
class LevelResult:
    level: int
    cases: list[CaseResult]

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    @property
    def clean(self) -> bool:
        return self.total > 0 and self.passed == self.total

    @property
    def weight_total(self) -> int:
        return sum(c.case.weight for c in self.cases)

    @property
    def weight_passed(self) -> int:
        return sum(c.case.weight for c in self.cases if c.passed)


@dataclass
class RunResult:
    problem: Problem
    levels: list[LevelResult]
    solution_path: Path
    load_error: str = ""
    started_at: float = 0.0
    duration_s: float = 0.0
    # display name -> the constraints that were not met. Kept separate from case
    # outcomes on purpose: "correct, but not the point of this drill" is a different
    # verdict from "wrong", and conflating them destroys the teaching.
    violations: dict = field(default_factory=dict)

    def violated(self, display: str) -> tuple:
        return tuple(self.violations.get(display, ()))

    def level(self, number: int) -> LevelResult | None:
        for entry in self.levels:
            if entry.level == number:
                return entry
        return None

    @property
    def highest_clean_level(self) -> int:
        highest = 0
        for number in sorted(entry.level for entry in self.levels):
            result = self.level(number)
            if result and result.clean:
                highest = number
            else:
                break
        return highest

    def score(self) -> tuple[int, int]:
        """Points earned out of the problem's total.

        The progressive format apportions its total across weighted levels, because
        that is how the real assessment scores (see docs/ASSESSMENT_BRIEF.md). Every
        other kind has one level and no weights, so it scores on the plain fraction
        of cases passed -- weighting nothing is more honest than inventing a split.
        """
        total = self.problem.total_points
        if self.problem.kind != KIND_PROGRESSIVE:
            passed = sum(l.weight_passed for l in self.levels)
            possible = sum(l.weight_total for l in self.levels)
            return (round(total * passed / possible) if possible else 0), total

        earned = 0
        for level_spec in self.problem.levels:
            result = self.level(level_spec.number)
            if result is None or result.weight_total == 0:
                continue
            earned += round(level_spec.weight * result.weight_passed / result.weight_total)
        return earned, total


class _OpTimeout(BaseException):
    """Deliberately not an Exception: candidate code must not be able to catch it."""


def _timeout_handler(signum, frame):  # pragma: no cover - signal path
    raise _OpTimeout()


class _Deadline:
    """Per-operation wall-clock guard. Degrades to a no-op off the POSIX main thread."""

    def __init__(self, seconds: float):
        self.seconds = seconds
        self.armed = False
        self.previous = None

    def __enter__(self):
        if self.seconds <= 0 or not hasattr(signal, "setitimer"):
            return self
        try:
            self.previous = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
            self.armed = True
        except (ValueError, OSError):  # not the main thread, or unsupported
            self.armed = False
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.armed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            if self.previous is not None:
                signal.signal(signal.SIGALRM, self.previous)
        return False


def load_solution(path: Path, class_name: str) -> tuple[Any, str]:
    """Import `path` and return (subject, error). Import errors are returned, not raised.

    The subject is the class to instantiate for class-shaped problems, or the module
    itself when `class_name` is empty (a `function` problem, whose operations are
    top-level defs).
    """
    if not path.exists():
        return None, f"no solution file at {path}"

    module_name = f"_pfs_solution_{path.stem}_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None, f"cannot import {path}"

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            spec.loader.exec_module(module)
    except SyntaxError as exc:
        # Point at the candidate's line. A raw traceback here is all harness
        # frames and buries the one fact that matters: which line will not parse.
        sys.modules.pop(module_name, None)
        where = f"line {exc.lineno}"
        if exc.offset:
            where += f", column {exc.offset}"
        message = f"{type(exc).__name__}: {exc.msg}\n  {path.name}, {where}"
        if exc.text:
            message += f"\n\n    {exc.text.rstrip()}"
            if exc.offset:
                message += "\n    " + " " * max(0, exc.offset - 1) + "^"
        return None, message
    except BaseException:
        sys.modules.pop(module_name, None)
        return None, traceback.format_exc(limit=8)
    finally:
        sys.modules.pop(module_name, None)

    # A `function` problem has no class: the module itself is the subject, so the
    # existing `getattr(subject, python_name)` dispatch finds a top-level `def` with
    # no further change. That is the whole of the seam between the two shapes.
    if not class_name:
        return module, ""

    target = getattr(module, class_name, None)
    if target is None:
        available = [
            name
            for name, value in vars(module).items()
            if isinstance(value, type) and not name.startswith("_")
        ]
        hint = f" Found: {', '.join(available)}." if available else ""
        return None, f"{path.name} defines no class named {class_name!r}.{hint}"
    return target, ""


def _trim_traceback(exc: BaseException, solution_path: Path) -> str:
    """Keep only frames inside the candidate's own file -- harness frames are noise."""
    frames = traceback.extract_tb(exc.__traceback__)
    own = [f for f in frames if Path(f.filename).name == solution_path.name]
    lines = traceback.format_list(own or frames[-3:])
    lines.append(f"{type(exc).__name__}: {exc}")
    return "".join(lines)


def run_case(
    solution_class: Any,
    problem: Problem,
    entry: Case,
    solution_path: Path,
    *,
    op_timeout: float = 4.0,
    stop_on_first_failure: bool = True,
) -> CaseResult:
    methods = problem.method_map()
    result = CaseResult(case=entry, outcome=Outcome.PASS)
    captured = io.StringIO()
    started = time.perf_counter()

    # For a class-shaped problem this is a fresh instance per case, which is what
    # keeps cases independent. For a `function` problem `solution_class` is already
    # the module and there is nothing to construct.
    if not problem.is_class_kind:
        instance = solution_class
        construct = None
    else:
        construct = solution_class
    try:
        with redirect_stdout(captured):
            if construct is not None:
                instance = construct()
    except BaseException as exc:
        kind = (
            Outcome.NOT_IMPLEMENTED
            if isinstance(exc, NotImplementedError)
            else Outcome.ERROR
        )
        result.outcome = kind
        result.ops.append(
            OpResult(
                op=entry.ops[0],
                outcome=kind,
                detail=f"{problem.class_name or problem.key}() constructor raised",
                traceback_text=_trim_traceback(exc, solution_path),
            )
        )
        result.elapsed_ms = (time.perf_counter() - started) * 1000
        result.stdout = captured.getvalue()
        return result

    for operation in entry.ops:
        method_spec: Method | None = methods.get(operation.name)
        python_name = (
            method_spec.resolved_name()
            if method_spec
            else operation.name.lower()
        )
        bound = getattr(instance, python_name, None)

        if bound is None or not callable(bound):
            result.ops.append(
                OpResult(
                    op=operation,
                    outcome=Outcome.MISSING_METHOD,
                    detail=(
                        f"{problem.class_name} has no method {python_name}()"
                        if problem.is_class_kind
                        else f"your file defines no function {python_name}()"
                    ),
                )
            )
            result.outcome = Outcome.MISSING_METHOD
            break

        op_result = _invoke(bound, operation, solution_path, captured, op_timeout)
        result.ops.append(op_result)

        if op_result.outcome is not Outcome.PASS:
            if result.outcome is Outcome.PASS or (
                result.outcome is Outcome.LENIENT and op_result.outcome in _BAD
            ):
                result.outcome = op_result.outcome
            if op_result.outcome in _BAD and stop_on_first_failure:
                break

    result.elapsed_ms = (time.perf_counter() - started) * 1000
    result.stdout = captured.getvalue()
    return result


def _invoke(
    bound: Any,
    operation: Op,
    solution_path: Path,
    captured: io.StringIO,
    op_timeout: float,
) -> OpResult:
    expects_raise = isinstance(operation.expect, Raises)

    # Hand the solution its OWN copy of every argument.
    #
    # `Op` is frozen but its `args` tuple can hold mutable objects, and `ALL_CASES` is
    # built once at import, so without this the same list is passed to every run of
    # every case in the process. A solution that sorts or reverses its input in place
    # would corrupt the argument for each later case -- and permanently, in the
    # long-running `./pfs ui` server, where the fix is a restart nobody knows to do.
    # No problem in the bank had a mutable argument when this was written, which is
    # exactly why it went unnoticed; in-place mutation is a whole genre of function
    # problem, so it stops being latent the moment one is authored.
    try:
        args = copy.deepcopy(operation.args)
        kwargs = {k: copy.deepcopy(v) for k, v in operation.kwargs}
    except Exception:
        # Deliberately not fatal: an exotic un-copyable argument should degrade to the
        # old shared-object behaviour rather than fail the case for a harness reason.
        args = operation.args
        kwargs = dict(operation.kwargs)

    try:
        with _Deadline(op_timeout):
            with redirect_stdout(captured):
                actual = bound(*args, **kwargs)
    except _OpTimeout:
        return OpResult(
            op=operation,
            outcome=Outcome.TIMEOUT,
            detail=f"exceeded {op_timeout:g}s -- likely an infinite loop or a runaway scan",
        )
    except NotImplementedError:
        return OpResult(
            op=operation,
            outcome=Outcome.NOT_IMPLEMENTED,
            detail=f"{operation.name} is still a stub",
        )
    except TypeError as exc:
        # Distinguish "your signature does not match the contract" from a genuine
        # TypeError raised by the candidate's own logic.
        message = str(exc)
        # Parenthesised deliberately. Written without them this was `A or (B and C)`,
        # because `and` binds tighter than `or` -- so any TypeError mentioning the word
        # "argument" was reported as a signature mismatch regardless of where it came
        # from. `getattr` for the name because a callable need not have `__name__`
        # (a functools.partial does not), and the AttributeError escaped this handler
        # and aborted the whole run.
        name = getattr(bound, "__name__", "")
        if "positional argument" in message or ("argument" in message and name and name in message):
            if expects_raise:
                return _raise_matched(operation, exc)
            return OpResult(
                op=operation,
                outcome=Outcome.ERROR,
                detail=f"signature mismatch: {message}",
                traceback_text=_trim_traceback(exc, solution_path),
            )
        if expects_raise:
            return _raise_matched(operation, exc)
        return OpResult(
            op=operation,
            outcome=Outcome.ERROR,
            detail=message,
            traceback_text=_trim_traceback(exc, solution_path),
        )
    except Exception as exc:
        if expects_raise:
            return _raise_matched(operation, exc)
        return OpResult(
            op=operation,
            outcome=Outcome.ERROR,
            detail=f"unexpected {type(exc).__name__}: {exc}",
            traceback_text=_trim_traceback(exc, solution_path),
        )

    if expects_raise:
        return OpResult(
            op=operation,
            outcome=Outcome.FAIL,
            actual=actual,
            detail=(
                f"expected {describe(operation.expect)}, but the call returned "
                f"{actual!r} without raising"
            ),
        )

    verdict = compare(operation.expect, actual)
    if verdict.grade is Grade.EXACT:
        return OpResult(op=operation, outcome=Outcome.PASS, actual=actual, verdict=verdict)
    if verdict.grade is Grade.LENIENT:
        return OpResult(
            op=operation,
            outcome=Outcome.LENIENT,
            actual=actual,
            verdict=verdict,
            detail=verdict.note,
        )
    return OpResult(
        op=operation,
        outcome=Outcome.FAIL,
        actual=actual,
        verdict=verdict,
        detail=verdict.note,
    )


def _raise_matched(operation: Op, exc: Exception) -> OpResult:
    expected: Raises = operation.expect
    if isinstance(exc, expected.kind):
        return OpResult(op=operation, outcome=Outcome.PASS, actual=exc)
    return OpResult(
        op=operation,
        outcome=Outcome.FAIL,
        actual=exc,
        detail=f"raised {type(exc).__name__}, expected {expected.kind.__name__}",
    )


def run(
    problem: Problem,
    solution_path: Path,
    *,
    max_level: int,
    only_level: int | None = None,
    tag: str | None = None,
    case_ids: set[str] | None = None,
    op_timeout: float = 4.0,
) -> RunResult:
    started = time.perf_counter()
    solution_class, error = load_solution(solution_path, problem.class_name)
    result = RunResult(
        problem=problem,
        levels=[],
        solution_path=solution_path,
        load_error=error,
        started_at=time.time(),
    )
    if error:
        result.duration_s = time.perf_counter() - started
        return result

    levels = (
        [only_level]
        if only_level is not None
        else [n for n in range(1, max_level + 1)]
    )

    for number in levels:
        selected = [
            entry
            for entry in problem.cases_for(number)
            if (tag is None or tag in entry.tags)
            and (case_ids is None or entry.id in case_ids)
        ]
        if not selected:
            continue
        level_result = LevelResult(level=number, cases=[])
        for entry in selected:
            level_result.cases.append(
                run_case(
                    solution_class,
                    problem,
                    entry,
                    solution_path,
                    op_timeout=op_timeout,
                )
            )
        result.levels.append(level_result)

    # Constraints are checked once, against the source, after the cases have run.
    # Parsed, never executed -- the same discipline webui/complete.py follows.
    constrained = [m for m in problem.methods if m.constraints and m.level <= max_level]
    if constrained:
        try:
            source = solution_path.read_text()
        except OSError:
            source = ""
        if source:
            for method in constrained:
                outcome = constraints_mod.check(
                    source, method.resolved_name(), method.constraints
                )
                if outcome.violations:
                    result.violations[method.display] = outcome.violations

    result.duration_s = time.perf_counter() - started
    return result
