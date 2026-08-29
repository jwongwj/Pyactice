"""Debrief analytics -- the measurement half of the practice loop.

Everything here reads the append-only event log. Three signals matter more than
the pass/fail totals:

  time-to-clear   how long each level actually took vs its budget. Where the 90
                  minutes goes is usually a surprise.
  stuck streaks   runs in a row failing the same case. A streak longer than three
                  means you are guessing, and guessing is where sessions die.
  tag failures    which *concept* fails, aggregated across sessions. This is the
                  input to the next drill, not the score.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import render
from .session import Session, format_clock


@dataclass
class RunEvent:
    elapsed_s: float
    level_reached: int
    passed: int
    total: int
    score: int
    failing: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class SessionReport:
    session: Session
    runs: list[RunEvent]
    cleared_at: dict[int, float]
    final_score: int
    final_level: int

    @property
    def run_count(self) -> int:
        return len(self.runs)


def build(session: Session) -> SessionReport:
    runs: list[RunEvent] = []
    cleared: dict[int, float] = {}

    for event in session.events():
        kind = event.get("kind")
        if kind == "run":
            runs.append(
                RunEvent(
                    elapsed_s=event.get("elapsed_s", 0.0),
                    level_reached=event.get("level_reached", 0),
                    passed=event.get("passed", 0),
                    total=event.get("total", 0),
                    score=event.get("score", 0),
                    failing=event.get("failing", []),
                    tags=event.get("tags", []),
                )
            )
        elif kind == "level_cleared":
            cleared[int(event["level"])] = event.get("elapsed_s", 0.0)

    for key, value in session.level_cleared_at.items():
        cleared.setdefault(int(key), value - session.started_at)

    return SessionReport(
        session=session,
        runs=runs,
        cleared_at=cleared,
        final_score=runs[-1].score if runs else 0,
        final_level=max((r.level_reached for r in runs), default=0),
    )


def stuck_streaks(report: SessionReport, minimum: int = 3) -> list[tuple[str, int, float]]:
    """(case id, streak length, seconds spent) for each run of repeated failures."""
    streaks: list[tuple[str, int, float]] = []
    current_case: str | None = None
    start_time = 0.0
    count = 0

    for run in report.runs:
        first = run.failing[0] if run.failing else None
        if first is not None and first == current_case:
            count += 1
        else:
            if current_case and count >= minimum:
                streaks.append((current_case, count, report.runs[-1].elapsed_s - start_time))
            current_case = first
            start_time = run.elapsed_s
            count = 1 if first else 0

    if current_case and count >= minimum:
        last = report.runs[-1].elapsed_s if report.runs else start_time
        streaks.append((current_case, count, last - start_time))
    return streaks


def tag_failures(reports: list[SessionReport]) -> Counter:
    counter: Counter = Counter()
    for report in reports:
        seen: set[tuple[str, str]] = set()
        for run in report.runs:
            for tag in run.tags:
                key = (report.session.id, tag)
                if key not in seen:
                    seen.add(key)
                    counter[tag] += 1
    return counter


def render_session(report: SessionReport, problem_levels) -> str:
    session = report.session
    lines: list[str] = []
    lines.append(render.rule(f"debrief · {session.id}"))
    lines.append("")

    total = session.elapsed_s
    lines.append(
        f"  {render.bold('Wall clock')}  {format_clock(total)} of "
        f"{session.budget_minutes}:00 budget      "
        f"{render.bold('Runs')} {report.run_count}"
    )
    lines.append(
        f"  {render.bold('Final')}       level {report.final_level} · "
        f"score ~{report.final_score}/600"
    )
    lines.append("")

    rows = []
    previous = 0.0
    for spec in problem_levels:
        cleared = report.cleared_at.get(spec.number)
        low, high = spec.budget_minutes
        if cleared is None:
            rows.append(
                [
                    f"L{spec.number} {spec.title}",
                    render.red("not cleared"),
                    "",
                    f"{low}-{high} min",
                ]
            )
            continue
        spent = cleared - previous
        previous = cleared
        verdict = (
            render.green("on budget")
            if spent <= high * 60
            else render.yellow(f"+{format_clock(spent - high * 60)} over")
        )
        rows.append(
            [
                f"L{spec.number} {spec.title}",
                render.green(format_clock(cleared)),
                format_clock(spent),
                f"{low}-{high} min  {verdict}",
            ]
        )
    lines.append(render.table(rows, ["level", "cleared at", "took", "budget"]))
    lines.append("")

    streaks = stuck_streaks(report)
    if streaks:
        lines.append(render.bold("  Stuck streaks") + render.dim("  (3+ runs failing the same case)"))
        for case_id, count, seconds in streaks:
            lines.append(
                f"    {render.red(case_id)}  {count} runs  ~{format_clock(seconds)}"
            )
        lines.append("")
        lines.append(
            render.dim(
                "    A long streak means the next run was a guess. The fix is to stop\n"
                "    running and re-read the failing case's expected value."
            )
        )
        lines.append("")

    failed_tags = Counter()
    for run in report.runs[-1:]:
        failed_tags.update(run.tags)
    if failed_tags:
        lines.append(render.bold("  Unresolved concepts at session end"))
        for tag, _ in failed_tags.most_common():
            lines.append(f"    {render.yellow(tag)}")
        lines.append("")

    return "\n".join(lines)


def render_stats(reports: list[SessionReport]) -> str:
    if not reports:
        return render.dim("No sessions recorded yet. Run `./pfs start <problem>`.")

    lines = [render.rule("cross-session stats"), ""]

    by_problem: dict[str, list[SessionReport]] = defaultdict(list)
    for report in reports:
        by_problem[report.session.problem].append(report)

    rows = []
    for problem_key, group in sorted(by_problem.items()):
        scores = [r.final_score for r in group]
        levels = [r.final_level for r in group]
        best = max(scores) if scores else 0
        last = scores[-1] if scores else 0
        rows.append(
            [
                problem_key,
                str(len(group)),
                f"{max(levels, default=0)}",
                f"{best}",
                f"{last}",
                render.bar(min(1.0, best / 600), 16),
            ]
        )
    lines.append(render.table(rows, ["problem", "attempts", "best lvl", "best", "last", ""]))
    lines.append("")

    counter = tag_failures(reports)
    if counter:
        lines.append(render.bold("  Weakest concepts") + render.dim("  (sessions where the tag was still failing)"))
        worst = counter.most_common(12)
        peak = worst[0][1] if worst else 1
        for tag, count in worst:
            lines.append(
                f"    {render.bar(count / peak, 14)}  {render.yellow(tag)} "
                f"{render.dim(f'({count})')}"
            )
        lines.append("")
        lines.append(
            render.dim(
                "    Drill the top row directly:  ./pfs test --tag <tag> --reveal"
            )
        )
    return "\n".join(lines)
