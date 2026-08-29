"""The `pfs` command line.

Command flow mirrors the real assessment:

    ./pfs start file_hosting     # 90-minute clock starts, level 1 stubs written
    ./pfs spec                   # read the current level's statement
    ...edit workspace/file_hosting/solution.py...
    ./pfs test                   # runs every unlocked level; clears -> unlocks next
    ./pfs finish                 # stops the clock, prints the debrief, unlocks DECISIONS.md

Everything else (`report`, `stats`, `validate`, `decisions`) is for the review
half of the loop and is deliberately unavailable or noisy during a live attempt.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import answer as answer_mod
from . import contract as contract_mod
from . import render, report as report_mod, scaffold, validate as validate_mod
from .loader import BROKEN, ROOT, all_problems, get_problem
from .model import Problem
from .runner import Outcome, run
from .session import (
    DEFAULT_MINUTES,
    Session,
    active_session,
    all_sessions,
    format_clock,
    new_session,
    workspace_for,
)

SOLUTIONS_DIR = ROOT / "solutions"


# ---------------------------------------------------------------------------
# helpers


def _fail(message: str) -> int:
    print(render.red(f"error: {message}"), file=sys.stderr)
    return 1


def _require_session() -> Session | None:
    session = active_session()
    if session is None:
        print(render.yellow("No active session. Start one with:"))
        print("  ./pfs start file_hosting")
        return None
    return session


def _resolve(session: Session | None, key: str | None) -> tuple[Problem, Path] | None:
    if key:
        problem = get_problem(key)
        path = (
            Path(session.solution_path)
            if session and session.problem == problem.key
            else workspace_for(problem.key)
        )
        return problem, path
    if session is None:
        print(render.yellow("No active session and no problem given."))
        return None
    return get_problem(session.problem), Path(session.solution_path)


def _clock_banner(session: Session) -> str:
    if not session.timed:
        return render.dim(
            "untimed" if session.active
            else f"session finished · {format_clock(session.elapsed_s)} used"
        )
    remaining = session.remaining_s
    if not session.active:
        return render.dim(f"session finished · {format_clock(session.elapsed_s)} used")
    if remaining <= 0:
        return render.red(render.bold(f"TIME UP · {format_clock(-remaining)} over budget"))
    paint = render.green if remaining > 900 else render.yellow if remaining > 300 else render.red
    return f"{render.bold('Time left')} {paint(format_clock(remaining))}"


def _live(session: Session | None, problem: Problem) -> bool:
    """Is this problem's clock actually running?

    Review-only views (`--all`, `--reveal`, a locked level's stubs) must refuse
    while it is. The web UI enforces this server-side; the CLI has to as well, or
    the two front ends disagree about the one rule the rig exists to keep.
    """
    return bool(
        session
        and session.active
        and not session.expired
        and session.problem == problem.key
    )


def _refuse_during_attempt(what: str) -> int:
    return _fail(
        f"{what} would reveal levels you have not unlocked, and your clock is running.\n"
        "       Run `./pfs finish` first — retakes are unlimited. (`--force` overrides.)"
    )


def _close_if_expired(session: Session | None) -> Session | None:
    """An expired session is over. Treat it that way everywhere, not just on the clock.

    Otherwise the answer key opens at 90:00 while runs still unlock levels, and the
    session records clears earned after time was up.
    """
    if session and session.active and session.expired:
        session.finished_at = time.time()
        session.save()
        session.log("session_end", abandoned=False, auto_closed=True)
    return session


# ---------------------------------------------------------------------------
# commands


def cmd_list(args: argparse.Namespace) -> int:
    problems = all_problems()
    loader_broken = dict(BROKEN)
    if not problems:
        return _fail("no problems found under problems/")
    print(render.rule("problem bank"))
    print()
    rows = []
    for problem in problems.values():
        rows.append(
            [
                render.bold(problem.key),
                problem.title,
                f"{len(problem.cases)} cases",
                render.dim(problem.source),
            ]
        )
    print(render.table(rows, ["key", "title", "size", "provenance"]))
    # A problem whose module fails to import is skipped by the loader so that one
    # broken problem cannot take the bank down. Skipped silently, though, it simply
    # vanishes -- which at this size you notice and at a hundred problems you do not.
    if loader_broken:
        print()
        print(render.red(render.bold(f"  {len(loader_broken)} problem(s) failed to load:")))
        for name, why in sorted(loader_broken.items()):
            print(f"    {render.red(name)}  {render.dim(why)}")
    print()
    print(render.dim("  ./pfs start <key>     begin a timed 90-minute attempt"))
    print(render.dim("  ./pfs spec <key> --all   read every level (after your attempt)"))
    return 1 if loader_broken else 0


def cmd_start(args: argparse.Namespace) -> int:
    try:
        problem = get_problem(args.problem)
    except KeyError as exc:
        return _fail(str(exc))

    existing = active_session()
    if existing and existing.active:
        if existing.expired:
            # The clock ran out and it was never closed. Close it rather than
            # blocking the next attempt on a session that is already over.
            existing.finished_at = time.time()
            existing.save()
            existing.log("session_end", abandoned=True, auto_closed=True)
            print(render.dim(f"  (closed the expired session {existing.id})"))
        elif not args.force:
            return _fail(
                f"session {existing.id} is still running "
                f"({format_clock(existing.remaining_s)} left).\n"
                "       Finish it with `./pfs finish`, then start again. "
                "Retakes are unlimited.\n"
                "       To abandon it and restart right now: ./pfs start "
                f"{problem.key} --force"
            )

    attempt = 1 + sum(1 for s in all_sessions() if s.problem == problem.key)

    path = workspace_for(problem.key)
    archived = None
    resuming = args.resume and path.exists()
    if resuming:
        written, message = False, "resuming"
    else:
        if path.exists():
            archived = scaffold.archive(path)
        written, message = scaffold.write_starter(
            problem, path, upto_level=args.level, force=True
        )
    if not written and not path.exists():
        return _fail(message)

    # Untimed unless the problem simulates a clock. `--minutes` still overrides, so a
    # deliberately timed drill session is possible; it is just not the default.
    minutes = args.minutes if args.minutes is not None else (
        DEFAULT_MINUTES if problem.timed else None
    )
    session = new_session(
        problem.key,
        path,
        minutes=minutes,
        max_level=problem.max_level,
        start_level=args.level,
        blind=args.blind,
    )

    print()
    print(render.rule(f"{problem.title}  ·  attempt {attempt}"))
    print()
    print(f"  {problem.opening}")
    print()
    print(f"  {render.bold('Your file')}   {path.relative_to(ROOT)}")
    if archived is not None:
        print(
            render.dim(
                f"              previous attempt saved to "
                f"{archived.relative_to(ROOT)}"
            )
        )
    elif not written:
        print(render.dim("              (resuming your existing file)"))
    print(f"  {render.bold('Budget')}      {args.minutes} minutes, {problem.max_level} levels")
    if args.blind:
        print(
            f"  {render.bold('Mode')}        "
            + render.yellow("exam — failures give a test number and your own output, nothing else")
        )
    print()
    print(render.bold("  What to do now"))
    print("    1. Open " + render.blue(str(path.relative_to(ROOT))) + " in your editor")
    print("    2. Implement the level-1 methods (the stubs are already there)")
    print(f"    3. Run {render.blue('./pfs test')} — passing every level-1 case unlocks level 2")
    print(f"    4. Repeat to level 4, then {render.blue('./pfs finish')}")
    print()
    print(render.dim("    ./pfs spec       re-read the current level"))
    print(render.dim("    ./pfs contract   exact types and return values (allowed)"))
    print(render.dim("    ./pfs status     time left"))
    print()
    print("  " + _clock_banner(session))
    print()
    _print_statement(problem, args.level)
    return 0


def _print_statement(problem: Problem, level: int, *, examples: bool = True) -> None:
    body = problem.statement_body(level)
    if not body.strip():
        print(render.red(f"missing statement for level {level}"))
        return
    print(body.rstrip())
    if problem.lesson_path is not None:
        print()
        print(render.dim(
            f"  the idioms this practises: {problem.lesson_path.relative_to(ROOT)}"
        ))
    if examples:
        print(render.render_examples(problem, level))
    print()


def cmd_spec(args: argparse.Namespace) -> int:
    session = active_session()
    resolved = _resolve(session, args.problem)
    if resolved is None:
        return 1
    problem, _ = resolved

    if args.all:
        if _live(session, problem) and not args.force:
            return _refuse_during_attempt("`spec --all`")
        # The statement files are cumulative, so the last one is the whole question.
        _print_statement(problem, problem.max_level, examples=False)
        for level in problem.levels:
            print(render.rule(f"level {level.number} examples · {level.title}"))
            print(render.render_examples(problem, level.number))
        return 0

    level = args.level
    if level is None:
        if session is None or session.problem != problem.key:
            level = 1
        else:
            level = session.unlocked_level
            if session.active and level > session.unlocked_level:
                return _fail(f"level {level} is not unlocked yet")

    if session and session.active and session.problem == problem.key and level > session.unlocked_level:
        return _fail(
            f"level {level} is locked. Clear level {session.unlocked_level} first "
            "(or use `--all` after the session)."
        )

    spec = problem.level(level)
    print(render.rule(f"level {level} · {spec.title}"))
    print(render.dim(f"  suggested budget: {spec.budget_minutes[0]}-{spec.budget_minutes[1]} minutes"))
    print()
    _print_statement(problem, level)
    if session and session.active:
        print(_clock_banner(session))
    return 0


def cmd_contract(args: argparse.Namespace) -> int:
    session = active_session()
    resolved = _resolve(session, args.problem)
    if resolved is None:
        return 1
    problem, _ = resolved
    if not (problem.directory / "CONTRACT.md").exists():
        return _fail(f"no CONTRACT.md for {problem.key}")

    # Only ever describe the levels that are unlocked -- see harness/contract.py.
    if args.all:
        if _live(session, problem) and not args.force:
            return _refuse_during_attempt("`contract --all`")
        upto = problem.max_level
    elif session and session.active and session.problem == problem.key:
        upto = session.unlocked_level
    else:
        upto = problem.max_level

    print(contract_mod.gated(problem, (problem.directory / "CONTRACT.md").read_text(), upto).rstrip())
    if upto < problem.max_level:
        print()
        print(render.dim(f"  (showing levels 1-{upto}; the rest unlocks as you clear them)"))
    return 0


def cmd_stubs(args: argparse.Namespace) -> int:
    session = active_session()
    resolved = _resolve(session, args.problem)
    if resolved is None:
        return 1
    problem, path = resolved
    level = args.level or (session.unlocked_level if session else 1)

    if _live(session, problem) and level > session.unlocked_level:
        return _fail(
            f"level {level} is locked — its method signatures are part of what "
            f"level {session.unlocked_level} is asking you to design for."
        )

    if args.append:
        ok, message = scaffold.append_level(problem, path, level)
        print(render.green(message) if ok else render.yellow(message))
        return 0 if ok else 1

    print(scaffold.level_stubs(problem, level))
    print(render.dim(f"  Paste into {path.name}, or run: ./pfs stubs --level {level} --append"))
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    session = _close_if_expired(active_session())
    resolved = _resolve(session, args.problem)
    if resolved is None:
        return 1
    problem, path = resolved
    live = _live(session, problem)

    if live and args.reveal:
        return _refuse_during_attempt("`--reveal`")
    if live and args.all:
        return _refuse_during_attempt("`--all`")
    if live and args.level and args.level > session.unlocked_level:
        return _fail(
            f"level {args.level} is locked. Clear level {session.unlocked_level} first."
        )
    # A run against a different problem must never touch this session's record.
    record = live and session.problem == problem.key
    # Exam mode only binds while this problem's own clock is running: after
    # `./pfs finish` the whole point is to read the cases you could not see.
    blind = bool(record and session.blind)

    if args.all:
        max_level, only = problem.max_level, None
    elif args.level is not None:
        max_level, only = args.level, args.level
    else:
        max_level = session.unlocked_level if session else problem.max_level
        only = None

    result = run(
        problem,
        path,
        max_level=max_level,
        only_level=only,
        tag=args.tag,
        case_ids=set(args.case) if args.case else None,
        op_timeout=args.timeout,
    )

    unlocked = session.unlocked_level if session else problem.max_level
    print(
        render.render_run(
            result,
            unlocked=unlocked,
            verbose=args.verbose,
            reveal=args.reveal,
            blind=blind,
        )
    )

    if result.load_error:
        return 1

    total = sum(level.total for level in result.levels)
    passed = sum(level.passed for level in result.levels)
    failing = [
        case_result.case
        for level in result.levels
        for case_result in level.cases
        if not case_result.passed
    ]
    failing_tags = sorted({tag for entry in failing for tag in entry.tags})

    print()
    print(render.rule())
    fraction = passed / total if total else 0.0
    verdict = render.green("ALL PASS") if passed == total and total else render.red(f"{total - passed} failing")
    print(f"  {render.bar(fraction)}  {passed}/{total} cases   {verdict}")
    if args.all or only is None:
        print(f"  {render.score_line(result)}")

    # Printed before the score, because "every case passes but you hand-rolled join"
    # is the outcome this whole feature exists to tell you about.
    for line in render.constraint_report(result):
        print(line)

    lenient = [
        case_result
        for level in result.levels
        for case_result in level.cases
        if case_result.outcome is Outcome.LENIENT
    ]
    # The real grader fails a wrong return type without telling you it was only a
    # type, so exam mode does not either.
    if lenient and not blind:
        print()
        print(
            render.yellow(
                f"  {len(lenient)} case(s) are logically correct but return the wrong type."
            )
        )
        print(render.dim("  The real grader fails these too. Check the stub type hints."))

    if record:
        session.log(
            "run",
            level_reached=result.highest_clean_level,
            passed=passed,
            total=total,
            score=result.score()[0],
            failing=[entry.id for entry in failing],
            tags=failing_tags,
            filtered=bool(args.tag or args.case or args.level or args.all),
        )
        print()
        print("  " + _clock_banner(session))

    # Unlocking only happens on an honest, unfiltered run of the unlocked levels.
    if (
        record
        and not (args.tag or args.case or args.level or args.all)
        and passed == total
        and total > 0
        and session.unlocked_level < session.max_level
    ):
        next_level = session.unlocked_level + 1
        session.unlocked_level = next_level
        session.level_cleared_at.setdefault(str(next_level - 1), time.time())
        session.save()
        session.log("level_cleared", level=next_level - 1)
        spec = problem.level(next_level)
        print()
        print(render.green(render.bold(f"  ✦ Level {next_level} unlocked — {spec.title}")))
        print(render.dim(f"    budget {spec.budget_minutes[0]}-{spec.budget_minutes[1]} min · ./pfs spec"))
        print(render.dim(f"    new stubs: ./pfs stubs --append"))
    elif (
        record
        and passed == total
        and total > 0
        and session.unlocked_level >= session.max_level
        and not (args.tag or args.case or args.level or args.all)
    ):
        session.level_cleared_at.setdefault(str(session.max_level), time.time())
        session.save()
        session.log("level_cleared", level=session.max_level)
        print()
        print(render.green(render.bold(
            f"  ✦ All {session.max_level} levels clear. Run `./pfs finish`."
        )))

    return 0 if passed == total and total > 0 else 1


def cmd_status(args: argparse.Namespace) -> int:
    session = _require_session()
    if session is None:
        return 0
    problem = get_problem(session.problem)
    print()
    print(render.rule(f"{problem.title} · {session.id}"))
    print()
    print(f"  {_clock_banner(session)}")
    print(f"  {render.bold('Level')}      {session.unlocked_level} of {session.max_level}")
    if session.blind:
        print(f"  {render.bold('Mode')}       {render.yellow('exam (--blind)')}")
    print(f"  {render.bold('File')}       {Path(session.solution_path).relative_to(ROOT)}")
    runs = [event for event in session.events() if event.get("kind") == "run"]
    print(f"  {render.bold('Runs')}       {len(runs)}")
    if runs:
        last = runs[-1]
        print(
            f"  {render.bold('Last run')}   {last['passed']}/{last['total']} cases "
            f"{render.dim('at ' + format_clock(last['elapsed_s']))}"
        )
    print()
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    session = _require_session()
    if session is None:
        return 0
    session.finished_at = time.time()
    session.save()
    session.log("session_end", abandoned=args.abandon)

    problem = get_problem(session.problem)
    built = report_mod.build(session)
    print()
    print(report_mod.render_session(built, problem.levels))
    print(render.rule("what to read next"))
    print()
    print(f"  {render.bold('Decisions')}  ./pfs decisions {problem.key}")
    print(render.dim("             every tie-break the hidden tests encode, and why"))
    print(f"  {render.bold('Playbook')}   docs/PLAYBOOK.md")
    print(f"  {render.bold('Stats')}      ./pfs stats")
    print()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    sessions = all_sessions()
    if not sessions:
        return _fail("no sessions recorded yet")
    if args.session:
        matches = [s for s in sessions if args.session in s.id]
        if not matches:
            return _fail(f"no session matching {args.session!r}")
        session = matches[-1]
    else:
        session = sessions[-1]
    problem = get_problem(session.problem)
    print()
    print(report_mod.render_session(report_mod.build(session), problem.levels))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    sessions = all_sessions()
    reports = [report_mod.build(s) for s in sessions]
    print()
    print(report_mod.render_stats(reports))
    print()
    return 0


def cmd_decisions(args: argparse.Namespace) -> int:
    resolved = _resolve(active_session(), args.problem)
    if resolved is None:
        return 1
    problem, _ = resolved
    session = active_session()
    if (
        session
        and session.active
        and session.problem == problem.key
        and not session.expired
        and not args.force
    ):
        return _fail(
            "DECISIONS.md is the answer key for the hidden tests and your session is "
            "still live. Run `./pfs finish` first (or --force if you are reviewing "
            "someone else's attempt)."
        )
    path = problem.directory / "DECISIONS.md"
    if not path.exists():
        return _fail(f"no DECISIONS.md for {problem.key}")
    print(path.read_text().rstrip())
    return 0


def cmd_answer(args: argparse.Namespace) -> int:
    resolved = _resolve(active_session(), args.problem)
    if resolved is None:
        return 1
    problem, _ = resolved
    session = active_session()
    if (
        session
        and session.active
        and session.problem == problem.key
        and not session.expired
        and not args.force
    ):
        return _fail(
            "a worked solution is the whole answer and your session is still live.\n"
            "       Run `./pfs finish` first — retakes are unlimited. (`--force` overrides.)"
        )

    level = args.level
    if level is not None and not 1 <= level <= problem.max_level:
        return _fail(f"{problem.key} has levels 1-{problem.max_level}, not {level}")

    found = answer_mod.resolve(problem, level)
    if found is None:
        if answer_mod.solution_path(problem) is None:
            return _fail(
                f"no worked solution for {problem.key}.\n"
                f"       Put one at solutions/{problem.key}.py (gitignored) — see "
                "solutions/README.md.\n"
                "       `./pfs validate` then re-checks the suite against it automatically."
            )
        return _fail(
            f"solutions/{problem.key}.py has no `# Level N` banners and there are no "
            f"per-level snapshots in solutions/{problem.key}/, so it cannot be shown "
            "one level at a time. Drop --level to print the whole file."
        )

    source, provenance, path = found
    shown = f"levels 1-{level}" if level is not None else "all levels"
    print()
    print(render.rule(f"{problem.title} · worked solution · {shown}"))
    print()
    print(source.rstrip())
    print()
    if provenance == "slice":
        # Say so. A slice is the finished solution with later sections cut out, so
        # earlier levels may already be written the way level 4 needed them.
        print(render.yellow(
            "  sliced from the finished solution — earlier levels may already be "
            "shaped by later ones."
        ))
    if level is not None and level < problem.max_level:
        print(render.dim(
            f"  levels {level + 1}-{problem.max_level} withheld — "
            f"./pfs answer {problem.key} --level {level + 1}"
        ))
    print(render.dim(f"  source: {path.relative_to(ROOT)}"))
    print(render.dim(f"  ./pfs validate {problem.key}   re-runs the suite against it"))
    print()
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    keys = [args.problem] if args.problem else list(all_problems())
    exit_code = 0
    # Surfaced here as well as in `list`, because validate is the gate a change has to
    # pass, and "one problem no longer imports" must fail it rather than be skipped.
    if BROKEN:
        print(render.rule("failed to load"))
        for name, why in sorted(BROKEN.items()):
            print(f"  {render.red('err ')}  {name}: {why}")
        exit_code = 1
    for key in keys:
        problem = get_problem(key)
        errors, warnings = validate_mod.structural(problem)
        print(render.rule(problem.key))
        for warning in warnings:
            print(f"  {render.yellow('warn')}  {warning}")
        for error in errors:
            print(f"  {render.red('err ')}  {error}")
            exit_code = 1

        reference = None
        if args.against:
            reference = Path(args.against)
        else:
            # `solution_key` for a drill points at its unit's oracle, since all the
            # drills split out of one unit share one file. Without this every drill
            # reported "no reference solution" and the differential gate silently did
            # not run for them -- the one gate this command exists to apply.
            candidate = answer_mod.solution_path(problem)
            if candidate is not None:
                reference = candidate
        if reference is not None:
            print(render.dim(f"  differential against {reference}"))
            issues = validate_mod.differential(problem, reference)
            for issue in issues:
                print(f"  {render.red('diff')}  {issue}")
                exit_code = 1
            if not issues:
                print(f"  {render.green('ok  ')}  every case agrees with the reference")
        else:
            print(
                render.dim(
                    "  no reference solution -- expected values are hand-derived and "
                    "unverified by execution. See solutions/README.md."
                )
            )
        if not errors and not warnings:
            print(f"  {render.green('ok  ')}  structure clean")
        print()
    return exit_code


def cmd_ui(args: argparse.Namespace) -> int:
    """Launch the browser IDE. Shares its session and workspace with this CLI."""
    sys.path.insert(0, str(ROOT))
    from webui.server import serve

    print()
    print(render.rule("practice IDE"))
    print()
    serve(port=args.port, open_browser=not args.no_open)
    return 0


def cmd_dispute(args: argparse.Namespace) -> int:
    """Record a claim that a test case is wrong. Reviewed during the walkthrough."""
    session = active_session()
    entry = {
        "t": time.time(),
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session": session.id if session else None,
        "problem": args.problem or (session.problem if session else None),
        "case": args.case,
        "claim": args.claim,
    }
    path = ROOT / "sessions" / "disputes.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
    print(render.green(f"Logged a dispute against {args.case}."))
    print(render.dim(f"  {path.relative_to(ROOT)}"))
    print(render.dim("  Keep going — do not stop the clock to argue with the harness."))
    return 0


# ---------------------------------------------------------------------------
# argument parsing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pfs",
        description="Practice harness for CodeSignal-style progressive-level assessments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ui", help="open the browser IDE (recommended)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-open", action="store_true", help="do not launch a browser")
    p.set_defaults(func=cmd_ui)

    p = sub.add_parser("list", help="list the problem bank")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("start", help="begin a timed attempt")
    p.add_argument("problem")
    p.add_argument("--minutes", type=int, default=None,
                   help="override the clock; timed problems default to 90, others to untimed")
    p.add_argument("--level", type=int, default=1, help="start at a later level (drill mode)")
    p.add_argument(
        "--blind",
        action="store_true",
        help="exam mode: failures give a test number and your own output, nothing else",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="keep the code already in your workspace instead of starting from stubs",
    )
    p.add_argument("--force", action="store_true", help="abandon a running session and restart")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("spec", help="print the current level's statement")
    p.add_argument("problem", nargs="?")
    p.add_argument("--level", type=int)
    p.add_argument("--all", action="store_true", help="print all four levels (after the attempt)")
    p.add_argument("--force", action="store_true", help="allow --all during a live attempt")
    p.set_defaults(func=cmd_spec)

    p = sub.add_parser("contract", help="print the precise type/return contract")
    p.add_argument("problem", nargs="?")
    p.add_argument("--all", action="store_true", help="all four levels (after the attempt)")
    p.add_argument("--force", action="store_true", help="allow --all during a live attempt")
    p.set_defaults(func=cmd_contract)

    p = sub.add_parser("stubs", help="print (or append) the stubs for a level")
    p.add_argument("problem", nargs="?")
    p.add_argument("--level", type=int)
    p.add_argument("--append", action="store_true")
    p.set_defaults(func=cmd_stubs)

    p = sub.add_parser("test", help="run the tests; clearing all unlocked levels unlocks the next")
    p.add_argument("problem", nargs="?")
    p.add_argument("--level", type=int, help="run only this level (does not unlock)")
    p.add_argument("--all", action="store_true", help="run every level (does not unlock)")
    p.add_argument("--tag", help="run only cases carrying this tag")
    p.add_argument("--case", action="append", help="run only this case id (repeatable)")
    p.add_argument("-v", "--verbose", action="store_true", help="show passing cases too")
    p.add_argument("--reveal", action="store_true", help="show hidden cases' operations (after the attempt)")
    p.add_argument("--timeout", type=float, default=4.0, help="per-operation seconds")
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("submit", help="alias for test")
    p.add_argument("problem", nargs="?")
    p.add_argument("--level", type=int)
    p.add_argument("--all", action="store_true")
    p.add_argument("--tag")
    p.add_argument("--case", action="append")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--reveal", action="store_true")
    p.add_argument("--timeout", type=float, default=4.0)
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("status", help="time left and current level")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("finish", help="stop the clock and print the debrief")
    p.add_argument("--abandon", action="store_true")
    p.set_defaults(func=cmd_finish)

    p = sub.add_parser("report", help="re-print a session debrief")
    p.add_argument("session", nargs="?")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("stats", help="cross-session trends and weakest concepts")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("decisions", help="the answer key for ambiguous spec points")
    p.add_argument("problem", nargs="?")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_decisions)

    p = sub.add_parser("answer", help="a worked solution (refuses while a session is live)")
    p.add_argument("problem", nargs="?")
    p.add_argument(
        "--level",
        type=int,
        help="show only levels 1..N, so peeking at level 2 does not spoil level 4",
    )
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_answer)

    p = sub.add_parser("validate", help="self-check the problem bank")
    p.add_argument("problem", nargs="?")
    p.add_argument("--against", help="reference solution to run every case against")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("dispute", help="log a claim that a test case is wrong")
    p.add_argument("case")
    p.add_argument("claim")
    p.add_argument("--problem")
    p.set_defaults(func=cmd_dispute)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyError as exc:
        return _fail(str(exc).strip("'"))
    except KeyboardInterrupt:
        print()
        return 130
