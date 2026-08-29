"""Terminal rendering.

Failure output is the harness's most important surface: it is what the candidate
reads a hundred times in ninety minutes. It shows the shortest reproduction (the
operations up to and including the failure) rather than a diff of internal state,
because that is what you can paste into your own scratch code and re-run.
"""

from __future__ import annotations

import os
import shutil
import sys
from typing import Iterable

from .examples import examples_for
from .expect import describe
from .model import Case, Problem
from .runner import CaseResult, LevelResult, Outcome, RunResult

_ENABLED = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _paint(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _ENABLED else text


def bold(text: str) -> str:
    return _paint("1", text)


def dim(text: str) -> str:
    return _paint("2", text)


def green(text: str) -> str:
    return _paint("32", text)


def red(text: str) -> str:
    return _paint("31", text)


def yellow(text: str) -> str:
    return _paint("33", text)


def blue(text: str) -> str:
    return _paint("36", text)


def magenta(text: str) -> str:
    return _paint("35", text)


def width() -> int:
    return min(shutil.get_terminal_size((100, 24)).columns, 100)


def rule(label: str = "", char: str = "─") -> str:
    total = width()
    if not label:
        return dim(char * total)
    text = f"{char}{char} {label} "
    return dim(text + char * max(0, total - len(text)))


_MARKS = {
    Outcome.PASS: ("✓", green),
    Outcome.LENIENT: ("≈", yellow),
    Outcome.FAIL: ("✗", red),
    Outcome.ERROR: ("!", red),
    Outcome.NOT_IMPLEMENTED: ("·", dim),
    Outcome.MISSING_METHOD: ("?", magenta),
    Outcome.TIMEOUT: ("T", red),
}

_LABELS = {
    Outcome.PASS: "pass",
    Outcome.LENIENT: "wrong type",
    Outcome.FAIL: "wrong answer",
    Outcome.ERROR: "crashed",
    Outcome.NOT_IMPLEMENTED: "not implemented",
    Outcome.MISSING_METHOD: "method missing",
    Outcome.TIMEOUT: "timed out",
}


def mark(outcome: Outcome) -> str:
    symbol, paint = _MARKS[outcome]
    return paint(symbol)


def outcome_label(outcome: Outcome) -> str:
    _, paint = _MARKS[outcome]
    return paint(_LABELS[outcome])


def case_line(result: CaseResult, *, hidden_names: bool) -> str:
    entry = result.case
    name = entry.id if entry.visible or not hidden_names else f"hidden::{entry.id}"
    label = "" if result.passed else f"  {outcome_label(result.outcome)}"
    tags = dim(f"  [{', '.join(entry.tags)}]") if entry.tags and not result.passed else ""
    return f"  {mark(result.outcome)} {name}{label}{tags}"


def blind_case_line(result: CaseResult, ordinal: int) -> str:
    """Exam mode: an opaque number, the way the real grader numbers its tests."""
    label = "" if result.passed else f"  {outcome_label(result.outcome)}"
    return f"  {mark(result.outcome)} test {ordinal}{label}"


def blind_detail(result: CaseResult, ordinal: int) -> list[str]:
    """Everything exam mode is willing to say about a failure.

    The number and the outcome, plus the candidate's own `print()` output and their
    own traceback. No case id, no tags, no operation names, no expected value --
    those are the affordances the real assessment withholds, and the point of this
    mode is to practise without them.
    """
    lines = ["", bold(f"  test {ordinal}") + dim(f"   level {result.case.level}")]
    lines.append(f"    {outcome_label(result.outcome)}")

    failing = result.failing_op
    if failing is not None and failing.outcome in (
        Outcome.MISSING_METHOD,
        Outcome.TIMEOUT,
        Outcome.NOT_IMPLEMENTED,
        Outcome.ERROR,
    ):
        if failing.detail:
            lines.append(f"    {yellow(failing.detail)}")
        for text_line in (failing.traceback_text or "").rstrip().splitlines():
            lines.append(dim(f"    | {text_line}"))

    if result.stdout.strip():
        printed = result.stdout.rstrip().splitlines()
        lines.append(f"    {blue('your output')}")
        for text_line in printed[:12]:
            lines.append(dim(f"      {text_line[:160]}"))
        if len(printed) > 12:
            lines.append(dim(f"      ... {len(printed) - 12} more lines"))
    return lines


def failure_detail(result: CaseResult, problem: Problem, *, reveal: bool) -> list[str]:
    """The shortest reproduction for a failing case."""
    lines: list[str] = []
    entry = result.case
    header = f"{entry.id}" if entry.visible or reveal else f"hidden::{entry.id}"
    lines.append("")
    lines.append(bold(f"  {header}") + dim(f"   level {entry.level}"))
    if entry.doc and (entry.visible or reveal):
        lines.append(dim(f"    {entry.doc}"))
    if entry.tags:
        lines.append(dim(f"    tags: {', '.join(entry.tags)}"))

    index = result.failing_index
    show_ops = entry.visible or reveal

    if not show_ops:
        lines.append(
            dim("    (hidden case - run with --reveal to see the operations)")
        )
        # Operation names only -- public, and enough to see what is being tested.
        shape = []
        for position, operation in enumerate(entry.ops):
            name = operation.name
            if position == index:
                shape.append(red(name))
            elif position < index:
                shape.append(green(name))
            else:
                shape.append(dim(name))
        lines.append("    " + dim(" → ").join(shape))
        lines.append(dim("    (names only; arguments and expected values stay hidden)"))

        failing = result.failing_op
        if failing is not None:
            lines.append(f"    step {index + 1}: {outcome_label(failing.outcome)}")
            # A crash is the candidate's own exception on their own line, so it is
            # shown in full even for a hidden case.
            if failing.outcome in (
                Outcome.MISSING_METHOD,
                Outcome.TIMEOUT,
                Outcome.NOT_IMPLEMENTED,
                Outcome.ERROR,
            ):
                if failing.detail:
                    lines.append(f"    {yellow(failing.detail)}")
                for text_line in (failing.traceback_text or "").rstrip().splitlines():
                    lines.append(dim(f"    | {text_line}"))
        if result.stdout.strip():
            printed = result.stdout.rstrip().splitlines()
            lines.append(f"    {blue('your output')}")
            for text_line in printed[:12]:
                lines.append(dim(f"      {text_line[:160]}"))
        return lines

    for position, op_result in enumerate(result.ops):
        prefix = "    "
        rendered = op_result.op.render()
        if position < index:
            lines.append(dim(f"{prefix}{rendered}"))
            continue

        lines.append(f"{prefix}{bold(rendered)}")
        if op_result.op.expect is not None or True:
            expected = describe(op_result.op.expect)
            if expected != "<not checked>":
                lines.append(f"{prefix}  expected: {green(expected)}")
        if op_result.outcome in (Outcome.FAIL, Outcome.LENIENT):
            lines.append(f"{prefix}  actual:   {red(repr(op_result.actual))}")
        if op_result.detail:
            lines.append(f"{prefix}  {yellow(op_result.detail)}")
        if op_result.op.why:
            lines.append(dim(f"{prefix}  why: {op_result.op.why}"))
        if op_result.traceback_text:
            for text_line in op_result.traceback_text.rstrip().splitlines():
                lines.append(dim(f"{prefix}  | {text_line}"))
        break

    if result.stdout.strip():
        printed = result.stdout.rstrip().splitlines()
        lines.append(f"    {blue('your output')}")
        for text_line in printed[:12]:
            lines.append(dim(f"      {text_line[:160]}"))
        if len(printed) > 12:
            lines.append(dim(f"      ... {len(printed) - 12} more lines"))
    return lines


def constraint_report(result: RunResult) -> list[str]:
    """The second verdict: correct, but not the way the drill is teaching.

    Deliberately its own section with its own mark. `\u25cb` is not `\u2717`: one means
    "you have not learned this yet", the other means "you got this right the long way
    round", and a learner who cannot tell them apart learns neither.
    """
    if not result.violations:
        return []

    # Only claim "correct, but" for drills whose cases actually pass. A violation on a
    # drill that is also WRONG is noise on top of the real failure -- and asserting it
    # was correct would be a plain lie.
    failing: set[str] = set()
    for level in result.levels:
        for case_result in level.cases:
            if not case_result.passed:
                for operation in case_result.case.ops:
                    failing.add(operation.name)

    shown = {d: f for d, f in result.violations.items() if d not in failing}
    if not shown:
        return []

    lines = ["", rule("not the point of the drill")]
    for display, found in shown.items():
        lines.append("")
        lines.append(f"  {yellow('\u25cb')} {bold(display)}{dim('   correct, but')}")
        for violation in found:
            where = dim(f"  (line {violation.line})") if violation.line else ""
            lines.append(f"      {violation.message}{where}")
            if violation.hint:
                lines.append(f"      {blue('\u2192')} {violation.hint}")
    lines.append("")
    lines.append(dim("  These do not cost you a case. They are what the drill is for."))
    return lines


def render_examples(problem: Problem, level: int) -> str:
    """Render this level's visible cases as worked examples.

    Generated from the cases themselves rather than written into the markdown, so
    the statement can never drift from what the grader actually checks -- and so
    every ambiguous rule is demonstrated by something executable.
    """
    cases = examples_for(problem, level)
    if not cases:
        return ""

    lines = ["", bold("### Examples"), ""]
    for entry in cases:
        if entry["doc"]:
            lines.append(f"  {blue(entry['doc'])}")
        lines.append(dim("  ```"))
        for operation in entry["ops"]:
            rendered = f"  {operation['call']}"
            expected = operation["expected"]
            if expected is None:
                lines.append(rendered)
            elif expected == "throws":
                lines.append(f"{rendered}   {dim('→')} {yellow('throws')}")
            else:
                lines.append(f"{rendered}   {dim('→')} {green(expected)}")
            if operation["why"]:
                lines.append(dim(f"        # {operation['why']}"))
        lines.append(dim("  ```"))
        lines.append("")
    return "\n".join(lines)


def level_summary(level: LevelResult, problem: Problem, unlocked: int) -> str:
    spec = problem.level(level.level)
    state = green("CLEAR") if level.clean else red(f"{level.passed}/{level.total}")
    lock = "" if level.level <= unlocked else dim(" (locked)")
    return f"{bold(f'Level {level.level}')} {dim(spec.title)}  {state}{lock}"


def render_run(
    result: RunResult,
    *,
    unlocked: int,
    verbose: bool = False,
    reveal: bool = False,
    blind: bool = False,
    max_failures: int = 3,
) -> str:
    lines: list[str] = []
    problem = result.problem

    if result.load_error:
        lines.append(red(bold("Could not load your solution.")))
        lines.append("")
        for text_line in result.load_error.rstrip().splitlines():
            lines.append(f"  {text_line}")
        return "\n".join(lines)

    if blind:
        return _render_blind(result, unlocked=unlocked, max_failures=max_failures)

    for level in result.levels:
        lines.append("")
        lines.append(level_summary(level, problem, unlocked))
        for case_result in level.cases:
            if case_result.passed and not verbose:
                continue
            lines.append(case_line(case_result, hidden_names=not reveal))
        if level.clean and not verbose:
            lines.append(dim(f"  all {level.total} cases pass"))

    failures = [
        case_result
        for level in result.levels
        for case_result in level.cases
        if not case_result.passed
    ]
    if failures:
        lines.append("")
        lines.append(rule("first failures"))
        for case_result in failures[:max_failures]:
            lines.extend(failure_detail(case_result, problem, reveal=reveal))
        if len(failures) > max_failures:
            lines.append("")
            lines.append(dim(f"  ... and {len(failures) - max_failures} more failing cases"))

    return "\n".join(lines)


def _render_blind(result: RunResult, *, unlocked: int, max_failures: int) -> str:
    """Exam mode's whole output surface: numbered tests and your own output."""
    lines: list[str] = []
    problem = result.problem
    failures: list[tuple[int, CaseResult]] = []

    for level in result.levels:
        lines.append("")
        lines.append(level_summary(level, problem, unlocked))
        for ordinal, case_result in enumerate(level.cases, start=1):
            lines.append(blind_case_line(case_result, ordinal))
            if not case_result.passed:
                failures.append((ordinal, case_result))

    if failures:
        lines.append("")
        lines.append(rule("first failures"))
        for ordinal, case_result in failures[:max_failures]:
            lines.extend(blind_detail(case_result, ordinal))
        if len(failures) > max_failures:
            lines.append("")
            lines.append(dim(f"  ... and {len(failures) - max_failures} more failing tests"))

    lines.append("")
    lines.append(dim("  exam mode: no case names, no tags, no expected values."))
    return "\n".join(lines)


def score_line(result: RunResult) -> str:
    earned, total = result.score()
    # The 520 band is the real assessment's, so it only means something on that scale.
    # For any other kind, say what the number is and do not imply a verdict.
    strong = round(total * 520 / 600)
    good = round(total * 400 / 600)
    band = green if earned >= strong else (yellow if earned >= good else red)
    note = f"({strong}+ is a strong band)" if total == 600 else ""
    return f"{bold('Estimated score')} {band(f'{earned}/{total}')}" + (f" {dim(note)}" if note else "")


def bar(fraction: float, size: int = 24) -> str:
    filled = int(round(fraction * size))
    return green("█" * filled) + dim("░" * (size - filled))


def table(rows: Iterable[Iterable[str]], headers: Iterable[str]) -> str:
    headers = list(headers)
    rows = [list(map(str, row)) for row in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], _visible_len(cell))
    out = ["  ".join(bold(h.ljust(widths[i])) for i, h in enumerate(headers))]
    for row in rows:
        out.append("  ".join(_pad(cell, widths[i]) for i, cell in enumerate(row)))
    return "\n".join(out)


def _visible_len(text: str) -> int:
    result, in_escape = 0, False
    for char in text:
        if char == "\033":
            in_escape = True
        elif in_escape:
            if char == "m":
                in_escape = False
        else:
            result += 1
    return result


def _pad(text: str, target: int) -> str:
    return text + " " * max(0, target - _visible_len(text))
