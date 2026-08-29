"""A local CodeSignal-style IDE for the practice harness.

Runs on the standard library alone. Single-threaded on purpose: the runner arms a
per-operation `SIGALRM` timeout, which only works on the main thread, and there is
exactly one candidate.

The web UI and the `./pfs` CLI share everything — the same session file, the same
workspace file, the same runner. You can start a session in the browser and finish
it from the terminal, or the other way round.

What the browser is never told: hidden cases' operations, expected values, or
actual values; the contents of any level that has not been unlocked; anything from
DECISIONS.md before the session ends. Those omissions are the point of the exercise,
so they are enforced here rather than hidden in the front end.
"""

from __future__ import annotations

import json
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness import answer as answer_mod  # noqa: E402
from harness import report as report_mod  # noqa: E402
from harness import scaffold  # noqa: E402
from harness.contract import for_level as contract_for_level  # noqa: E402
from harness.examples import examples_for  # noqa: E402
from harness.loader import ROOT, all_problems, get_problem  # noqa: E402
from curriculum import graph as curriculum  # noqa: E402
from harness.runner import Outcome, run  # noqa: E402
from harness.session import (  # noqa: E402
    ACTIVE_POINTER,
    DEFAULT_MINUTES,
    active_session,
    all_sessions,
    new_session,
    workspace_for,
)
from webui.markdown import to_html  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
INDEX = Path(__file__).resolve().parent / "index.html"


def _source_fingerprint() -> str:
    """Hash of the Python this server would import right now.

    The server imports its modules once at startup, so editing them leaves a
    process running stale code that still answers requests -- it looks alive and
    silently behaves like the old version. Comparing the fingerprint taken at
    import against the files on disk turns that into a visible banner instead of
    an afternoon of confusion.
    """
    import hashlib

    digest = hashlib.sha256()
    for source in sorted((ROOT / "harness").glob("*.py")) + sorted((ROOT / "webui").glob("*.py")):
        digest.update(source.read_bytes())
    return digest.hexdigest()[:16]


_BOOT_FINGERPRINT = _source_fingerprint()


def _asset_fingerprint() -> str:
    """Hash of what the browser would download right now.

    The server can be fresh while the tab is still running HTML loaded before an
    edit. Nothing on screen says so, and the symptom is a feature that visibly
    does not exist -- which is indistinguishable from a bug.
    """
    import hashlib

    digest = hashlib.sha256(INDEX.read_bytes())
    for asset in sorted(STATIC.glob("*")):
        digest.update(asset.read_bytes())
    return digest.hexdigest()[:16]

_OUTCOME_LABEL = {
    Outcome.PASS: "pass",
    Outcome.LENIENT: "wrong type",
    Outcome.FAIL: "wrong answer",
    Outcome.ERROR: "crashed",
    Outcome.NOT_IMPLEMENTED: "not implemented",
    Outcome.MISSING_METHOD: "method missing",
    Outcome.TIMEOUT: "timed out",
}


# ---------------------------------------------------------------------------
# payload builders


def _levels_payload(problem, session):
    unlocked = session.unlocked_level if session else problem.max_level
    return [
        {
            "number": level.number,
            "title": level.title,
            "budget": list(level.budget_minutes),
            "unlocked": level.number <= unlocked,
            "cleared": str(level.number) in (session.level_cleared_at if session else {}),
        }
        for level in problem.levels
    ]


def _statement_payload(problem, upto_level: int):
    # statement_body answers from generated text for a split-out drill, and from the
    # file otherwise. The two are deliberately different documents: the statement says
    # what to do, the lesson teaches the idiom, and the worked answer stays behind the
    # Solution tab. Putting all three in one pane is how a lesson hands over the answer.
    body = problem.statement_body(upto_level)
    lesson = problem.lesson_path
    return {
        "html": to_html(body) if body.strip() else "",
        "lesson_html": to_html(lesson.read_text()) if lesson is not None else "",
        "unit": list(problem.unit) if problem.unit else None,
        "examples": [
            {"level": n, "cases": examples_for(problem, n)}
            for n in range(1, upto_level + 1)
        ],
    }


def _picker_progress() -> dict[str, dict]:
    """Attempts and cleared-ness per problem, in ONE pass over sessions/.

    The picker needs both: attempts for the card's meta line, cleared for the tick on a
    nested drill row and the "3/12 cleared" count on its unit. `_problem_progress` also
    answers this, but it opens every session's event log to find a best score, which the
    picker does not show -- and calling both made the payload read sessions/ twice, which
    is the regression the test below this guards.

    The shape this replaced was `sum(1 for s in all_sessions() if s.problem == p.key)`
    *inside* the per-problem comprehension, so every problem re-parsed every session file
    on disk. Five problems and twenty sessions hid it; ninety-eight problems and a few
    hundred sessions is tens of thousands of JSON parses per home-screen load.
    """
    problems = all_problems()
    out: dict[str, dict] = {
        key: {"attempts": 0, "cleared": False} for key in problems
    }
    for session in all_sessions():
        entry = out.get(session.problem)
        if entry is None:
            continue          # a session for a problem no longer in the bank
        entry["attempts"] += 1
        if len(session.level_cleared_at) >= problems[session.problem].max_level:
            entry["cleared"] = True
    return out


def _has_work(problem) -> bool:
    """Is there unfinished work in this problem's workspace file?

    True when the file exists and differs from the starter the scaffold would write.
    Starting a problem archives that file and lays down fresh stubs, which is right for
    a deliberate cold retake and a trap when you meant to carry on -- so the front end
    needs to know, and offer Resume instead of Start.
    """
    path = workspace_for(problem.key)
    if not path.exists():
        return False
    try:
        current = path.read_text()
    except OSError:
        return False
    if not current.strip():
        return False
    fresh = scaffold.starter_source(problem, 1)
    return current.strip() != fresh.strip()


def _problem_cards() -> list[dict]:
    progress = _picker_progress()
    return [
        {
            "key": problem.key,
            "title": problem.title,
            # The short form, for when the unit is already named around it.
            "label": problem.label,
            # (key, title) of the unit this was split out of, or None. The picker groups
            # on this: ninety-two drills listed flat is a wall, and the twelve buttons a
            # single subtopic used to spray overflowed the row four times over.
            "unit": list(problem.unit) if problem.unit else None,
            "blurb": problem.opening,
            "cases": len(problem.cases),
            "kind": problem.kind,
            "difficulty": problem.difficulty,
            "levels": len(problem.levels),
            "timed": problem.timed,
            "has_work": _has_work(problem),
            "attempts": progress.get(problem.key, {}).get("attempts", 0),
            "cleared": progress.get(problem.key, {}).get("cleared", False),
        }
        for problem in all_problems().values()
    ]


# ---------------------------------------------------------------------------
# curriculum


def _problem_progress() -> dict[str, dict]:
    """Per problem: attempted, cleared, best score. One pass over sessions/."""
    problems = all_problems()
    out: dict[str, dict] = {
        key: {"attempts": 0, "cleared": False, "best": 0, "last": 0.0}
        for key in problems
    }
    for session in all_sessions():
        entry = out.get(session.problem)
        if entry is None:
            continue          # a session for a problem no longer in the bank
        problem = problems[session.problem]
        entry["attempts"] += 1
        entry["last"] = max(entry["last"], session.started_at)
        # Cleared means every level was cleared, which is what the session records as
        # it happens. Deriving it from a run's score instead would count a filtered or
        # a --force run, neither of which earned anything.
        if len(session.level_cleared_at) >= problem.max_level:
            entry["cleared"] = True
        for event in session.events():
            if event.get("kind") == "run":
                entry["best"] = max(entry["best"], int(event.get("score") or 0))
    return out


def _weak_spots(limit: int = 4) -> list[dict]:
    """Failing concept tags across sessions, mapped to the subtopic that teaches them.

    This is the only genuinely useful recommendation on the home screen: the tag counts
    already exist for `./pfs stats`, and the graph knows which subtopic covers a tag, so
    "you keep failing tie-breaks" becomes "go and do 1.7 Sorting".
    """
    reports = [report_mod.build(session) for session in all_sessions()]
    counts = report_mod.tag_failures(reports)
    out: list[dict] = []
    for tag, sessions in counts.most_common():
        teaches = curriculum.subtopics_for_tag(tag)
        if not teaches:
            continue
        out.append({
            "tag": tag,
            "sessions": sessions,
            "subtopic": teaches[0].id,
            "subtopic_title": teaches[0].title,
        })
        if len(out) >= limit:
            break
    return out


def _curriculum_payload():
    progress = _problem_progress()

    def state(subtopic):
        keys = subtopic.problems
        done = sum(1 for k in keys if progress.get(k, {}).get("cleared"))
        started = sum(1 for k in keys if progress.get(k, {}).get("attempts"))
        available = len(keys) > 0
        cleared = available and done == len(keys) and subtopic.planned == 0
        return done, started, available, cleared

    computed = {s.id: state(s) for s in curriculum.all_subtopics()}
    # A prerequisite with nothing authored yet cannot be cleared, so requiring it would
    # block its dependants for ever. Treat "does not exist yet" as satisfied rather than
    # showing a frontier that is permanently empty.
    satisfied = {
        sid for sid, (_d, _s, available, cleared) in computed.items()
        if cleared or not available
    }

    categories = []
    for category in curriculum.CATEGORIES:
        subtopics = []
        for subtopic in category.subtopics:
            done, started, available, cleared = computed[subtopic.id]
            # Two different questions, deliberately answered separately:
            #   `missing` is what to TELL the learner -- every prerequisite they have
            #     not cleared, including ones not written yet, because "usually done
            #     after 1.7 Sorting" is useful advice even when 1.7 is unwritten.
            #   `ready` is whether to put it on the frontier, which treats an unwritten
            #     prerequisite as satisfied -- nobody can clear what does not exist, and
            #     requiring it would leave the frontier permanently empty.
            cleared_ids = {
                sid for sid, (_d, _s, _a, c) in computed.items() if c
            }
            # Only ACTIONABLE advice. "Usually done after 1.7 Sorting" is useful when
            # 1.7 exists and you have not cleared it; when 1.7 has not been written yet
            # it is a instruction you cannot follow, and it appeared on the very rows the
            # frontier had just declared ready -- which reads as a contradiction.
            missing = [
                {"id": r.id, "title": r.title, "written": r.authored}
                for r in curriculum.missing_requirements(subtopic, cleared_ids)
                if r.authored
            ]
            blocking = curriculum.missing_requirements(subtopic, satisfied)
            subtopics.append({
                "id": subtopic.id,
                "slug": subtopic.slug,
                "title": subtopic.title,
                "requires": list(subtopic.requires),
                "missing": missing,
                "ready": not blocking,
                "available": available,
                "problems": list(subtopic.problems),
                "planned": subtopic.planned,
                "total": subtopic.total,
                "done": done,
                "started": started,
                "cleared": cleared,
                "minutes": list(subtopic.minutes),
                "tags": list(subtopic.tags),
            })
        categories.append({
            "number": category.number,
            "slug": category.slug,
            "title": category.title,
            "blurb": category.blurb,
            "cleared": sum(1 for s in subtopics if s["cleared"]),
            "available": sum(1 for s in subtopics if s["available"]),
            "total": len(subtopics),
            "subtopics": subtopics,
        })

    # Where to pick up: the most recently touched problem that is not yet cleared.
    resume = None
    unfinished = [
        (data["last"], key) for key, data in progress.items()
        if data["attempts"] and not data["cleared"]
    ]
    if unfinished:
        _when, key = max(unfinished)
        subtopic = curriculum.subtopic_for_problem(key)
        problem = all_problems().get(key)
        resume = {
            "problem": key,
            "title": problem.title if problem else key,
            "subtopic": subtopic.id if subtopic else "",
            "subtopic_title": subtopic.title if subtopic else "",
            "best": progress[key]["best"],
        }

    resume_subtopic = resume["subtopic"] if resume else ""
    frontier = [
        s.id for s in curriculum.frontier(satisfied)
        if computed[s.id][2]                 # only offer what actually exists
        and s.id != resume_subtopic          # Continue already offers this one
    ]

    return {
        "categories": categories,
        "resume": resume,
        "frontier": frontier,
        "weak": _weak_spots(),
        "authored": sum(len(s.problems) for s in curriculum.all_subtopics()),
        "planned": sum(s.planned for s in curriculum.all_subtopics()),
    }


def _close_if_expired(session):
    """An expired session is finished. Without this the answer key opened at 90:00
    while runs kept unlocking levels, recording clears earned after time was up."""
    if session is not None and session.active and session.expired:
        session.finished_at = time.time()
        session.save()
        session.log("session_end", abandoned=False, auto_closed=True)
    return session


def _state_payload():
    session = _close_if_expired(active_session())
    if session is None:
        return {
            "active": False,
            "stale_server": _source_fingerprint() != _BOOT_FINGERPRINT,
            "build": _asset_fingerprint(),
            "problems": _problem_cards(),
        }

    problem = get_problem(session.problem)
    path = Path(session.solution_path)
    # The contract describes only unlocked levels; gating happens here, server-side,
    # so the browser is never sent a locked level's operations.
    contract_upto = problem.max_level if not session.active else session.unlocked_level
    contract_md = contract_for_level(problem, contract_upto)
    code = path.read_text() if path.exists() else ""
    # Offering "add stubs" when the file already defines them invites the user to
    # shadow their own implementation, so the button is driven from the file.
    stubs_pending = bool(
        problem.methods_for(session.unlocked_level)
    ) and not scaffold.defined_methods(problem, code, session.unlocked_level)
    return {
        "active": True,
        "stale_server": _source_fingerprint() != _BOOT_FINGERPRINT,
        "build": _asset_fingerprint(),
        "running": session.active and not session.expired,
        "problem": {
            "key": problem.key,
            "title": problem.title,
            "blurb": problem.opening,
            "class_name": problem.class_name,
            "max_level": problem.max_level,
        },
        "session": {
            "id": session.id,
            # None, not infinity: round(inf) raises OverflowError and json cannot
            # encode inf, so an untimed session could not even be serialised.
            "remaining_s": round(session.remaining_s) if session.timed else None,
            "timed": session.timed,
            "elapsed_s": round(session.elapsed_s),
            "budget_minutes": session.budget_minutes,
            "unlocked_level": session.unlocked_level,
            "finished": not session.active,
            "blind": bool(session.blind and session.active),
            "stubs_pending": stubs_pending,
            "attempt": sum(1 for s in all_sessions() if s.problem == problem.key),
        },
        "levels": _levels_payload(problem, session),
        # Review mode opens everything or nothing. Gating the statement while the
        # results reveal every hidden level-4 case let you read the tests but never
        # the question -- incoherent, and it reads as a leak.
        "statement": _statement_payload(problem, contract_upto),
        "review": not session.active,
        "contract_html": to_html(contract_md) if contract_md else "",
        "code": code,
        "path": str(path.relative_to(ROOT)),
    }


_MAX_OUTPUT = 4000


def _trim_output(text: str) -> str:
    if not text:
        return ""
    if len(text) <= _MAX_OUTPUT:
        return text
    return text[:_MAX_OUTPUT] + f"\n... [{len(text) - _MAX_OUTPUT} more characters]"


def _blind_case_payload(case_result, ordinal: int):
    """Exam mode: an opaque test number, the outcome, and the candidate's own output.

    No id, no tags, no doc, no operation names, no expected value. A crash is still
    reported in full -- that is the candidate's own exception on their own line, and
    withholding it just means staring at the word "crashed".
    """
    payload = {
        "id": f"test {ordinal}",
        "visible": False,
        "blind": True,
        "level": case_result.case.level,
        "outcome": case_result.outcome.value,
        "label": _OUTCOME_LABEL[case_result.outcome],
        "passed": case_result.passed,
        "tags": [],
        "doc": "",
        "step": 0,
        "ops": [],
        "detail": "",
        "traceback": "",
        "stdout": _trim_output(case_result.stdout),
    }
    failing = case_result.failing_op
    if not case_result.passed and failing is not None and failing.outcome in (
        Outcome.MISSING_METHOD,
        Outcome.TIMEOUT,
        Outcome.NOT_IMPLEMENTED,
        Outcome.ERROR,
    ):
        payload["detail"] = failing.detail
        payload["traceback"] = failing.traceback_text
    return payload


def _case_payload(case_result, reveal: bool):
    entry = case_result.case
    visible = entry.visible or reveal
    payload = {
        "id": entry.id,
        "visible": visible,
        "level": entry.level,
        "outcome": case_result.outcome.value,
        "label": _OUTCOME_LABEL[case_result.outcome],
        "passed": case_result.passed,
        "tags": list(entry.tags),
        "doc": entry.doc if visible else "",
        "step": case_result.failing_index + 1 if not case_result.passed else 0,
        "ops": [],
        "detail": "",
        "traceback": "",
        # The candidate's own print() output. Shown for hidden cases too: it is
        # their instrumentation, printing their own arguments, and print-debugging
        # is how anyone inspects state. The real assessment shows it as well.
        "stdout": _trim_output(case_result.stdout),
    }
    if case_result.passed:
        return payload

    failing = case_result.failing_op
    if not visible:
        # Hidden cases never reveal what was expected or what you returned. They do
        # report a crash in full: the exception, the message and the candidate's own
        # line. That is their bug in their code -- withholding it just means staring
        # at the word "crashed", which is what happened to a real user.
        if failing is not None and failing.outcome in (
            Outcome.MISSING_METHOD,
            Outcome.TIMEOUT,
            Outcome.NOT_IMPLEMENTED,
            Outcome.ERROR,
        ):
            payload["detail"] = failing.detail
            payload["traceback"] = failing.traceback_text
        # The sequence of operation NAMES, with no arguments and no expected values.
        # Names are public -- they are listed in the statement -- so this leaks nothing,
        # while "wrong answer at step 5" on its own gave the candidate nothing to think
        # with. Seeing "upload, upload, copy, get, get" points at the concept under test.
        payload["shape"] = [operation.name for operation in entry.ops]
        return payload

    index = case_result.failing_index
    for position, op_result in enumerate(case_result.ops):
        item = {"call": op_result.op.render(), "past": position < index}
        if position >= index:
            from harness.expect import describe

            expected = describe(op_result.op.expect)
            item["expected"] = None if expected == "<not checked>" else expected
            item["actual"] = (
                repr(op_result.actual)
                if op_result.outcome in (Outcome.FAIL, Outcome.LENIENT)
                else None
            )
            item["detail"] = op_result.detail
            item["why"] = op_result.op.why
            item["traceback"] = op_result.traceback_text
        payload["ops"].append(item)
        if position >= index:
            break
    if failing is not None:
        payload["detail"] = failing.detail
    return payload


def _run_payload(problem, result, session, reveal: bool, blind: bool = False):
    levels = []
    for level in result.levels:
        if blind:
            cases = [
                _blind_case_payload(c, ordinal)
                for ordinal, c in enumerate(level.cases, start=1)
            ]
        else:
            cases = [_case_payload(c, reveal) for c in level.cases]
        levels.append(
            {
                "level": level.level,
                "title": problem.level(level.level).title,
                "passed": level.passed,
                "total": level.total,
                "clean": level.clean,
                "cases": cases,
            }
        )
    earned, total = result.score()
    return {
        "load_error": result.load_error,
        "blind": blind,
        "levels": levels,
        "passed": sum(l.passed for l in result.levels),
        "total": sum(l.total for l in result.levels),
        "score": earned,
        "score_max": total,
        "unlocked_level": session.unlocked_level if session else problem.max_level,
    }


def _debrief_payload(session, problem):
    built = report_mod.build(session)
    rows = []
    previous = 0.0
    for spec in problem.levels:
        cleared = built.cleared_at.get(spec.number)
        low, high = spec.budget_minutes
        if cleared is None:
            rows.append(
                {
                    "level": spec.number,
                    "title": spec.title,
                    "cleared": False,
                    "cleared_at": None,
                    "took": None,
                    "budget": [low, high],
                    "on_budget": None,
                }
            )
            continue
        took = cleared - previous
        previous = cleared
        rows.append(
            {
                "level": spec.number,
                "title": spec.title,
                "cleared": True,
                "cleared_at": round(cleared),
                "took": round(took),
                "budget": [low, high],
                "on_budget": took <= high * 60,
            }
        )
    return {
        "session_id": session.id,
        "elapsed_s": round(session.elapsed_s),
        "budget_minutes": session.budget_minutes,
        "runs": built.run_count,
        "score": built.final_score,
        "final_level": built.final_level,
        "levels": rows,
        "streaks": [
            {"case": case_id, "runs": count, "seconds": round(seconds)}
            for case_id, count, seconds in report_mod.stuck_streaks(built)
        ],
        "unresolved_tags": sorted(built.runs[-1].tags) if built.runs else [],
    }


# ---------------------------------------------------------------------------
# HTTP


class Handler(BaseHTTPRequestHandler):
    server_version = "pfs-ide"

    def log_message(self, fmt, *args):  # quiet
        pass

    # -- helpers ---------------------------------------------------------

    def _send(self, code, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, code=200):
        self._send(code, json.dumps(payload).encode(), "application/json")

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length) or b"{}")

    # -- routes ----------------------------------------------------------

    def do_GET(self):
        try:
            return self._get(self.path.split("?")[0])
        except Exception as exc:
            import traceback
            return self._json(
                {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}, 500
            )

    def _get(self, path):
        if path in ("/", "/index.html"):
            page = INDEX.read_text().replace("__PFS_BUILD__", _asset_fingerprint())
            return self._send(200, page.encode(), "text/html; charset=utf-8")
        if path.startswith("/static/"):
            target = STATIC / path[len("/static/") :]
            if not target.is_file() or STATIC not in target.resolve().parents:
                return self._send(404, b"not found", "text/plain")
            kind = "text/css" if target.suffix == ".css" else "application/javascript"
            return self._send(200, target.read_bytes(), kind)
        if path == "/api/state":
            return self._json(_state_payload())
        if path == "/api/decisions":
            return self._decisions()
        if path == "/api/curriculum":
            return self._json(_curriculum_payload())
        if path == "/api/answer":
            from urllib.parse import parse_qs, urlparse
            return self._answer(parse_qs(urlparse(self.path).query))
        if path == "/favicon.ico":
            return self._send(204, b"", "image/x-icon")
        return self._send(404, b"not found", "text/plain")

    def do_POST(self):
        path = self.path.split("?")[0]
        routes = {
            "/api/start": self._start,
            "/api/save": self._save,
            "/api/run": self._run,
            "/api/stubs": self._stubs,
            "/api/finish": self._finish,
            "/api/abandon": self._abandon,
            "/api/check": self._check,
            "/api/complete": self._complete,
            "/api/dispute": self._dispute,
        }
        handler = routes.get(path)
        if handler is None:
            return self._send(404, b"not found", "text/plain")
        try:
            return handler(self._body())
        except Exception as exc:  # surface server bugs in the UI rather than a blank page
            import traceback

            return self._json(
                {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()},
                500,
            )

    # -- handlers --------------------------------------------------------

    def _start(self, body):
        problem = get_problem(body["problem"])
        # Untimed unless the problem is the kind that simulates a clock. A drill or a
        # single function is work, not an exam, and a countdown on it measures nothing.
        if not problem.timed:
            minutes = None
        else:
            minutes = int(body.get("minutes") or DEFAULT_MINUTES)
        resume = bool(body.get("resume"))

        existing = active_session()
        if existing and existing.active:
            existing.finished_at = time.time()
            existing.save()
            existing.log("session_end", abandoned=True, auto_closed=True)

        path = workspace_for(problem.key)
        if resume and path.exists():
            pass  # keep exactly what is there; that is what resume means
        else:
            if path.exists():
                scaffold.archive(path)
            scaffold.write_starter(problem, path, upto_level=1, force=True)
        new_session(
            problem.key,
            path,
            minutes=minutes,
            max_level=problem.max_level,
            blind=bool(body.get("blind")),
        )
        return self._json(_state_payload())

    def _save(self, body):
        session = active_session()
        if session is None:
            return self._json({"saved": False, "reason": "no session"})
        code = body.get("code")
        # Defaulting a missing field to "" would truncate the one file the user
        # cannot afford to lose. Refuse instead.
        if not isinstance(code, str):
            return self._json({"error": "no code supplied"}, 400)
        Path(session.solution_path).write_text(code)
        return self._json({"saved": True})

    def _run(self, body):
        session = _close_if_expired(active_session())
        if session is None:
            return self._json({"error": "no active session"}, 400)
        code = body.get("code")
        if not isinstance(code, str):
            return self._json({"error": "no code supplied"}, 400)
        problem = get_problem(session.problem)
        path = Path(session.solution_path)
        path.write_text(code)

        finished = not session.active
        # Review mode reveals unconditionally. Making it opt-in meant a client that
        # forgot the flag got the tests without the detail -- the same half-open
        # state that made level 4 look like a leak.
        reveal = finished
        # Exam mode binds only while the clock runs; finishing is what buys the detail.
        blind = bool(session.blind and not finished)
        max_level = problem.max_level if finished else session.unlocked_level

        result = run(problem, path, max_level=max_level, op_timeout=4.0)
        payload = _run_payload(problem, result, session, reveal, blind)

        if result.load_error:
            return self._json(payload)

        failing = [
            c.case
            for level in result.levels
            for c in level.cases
            if not c.passed
        ]
        if session.active:
            session.log(
                "run",
                level_reached=result.highest_clean_level,
                passed=payload["passed"],
                total=payload["total"],
                score=payload["score"],
                failing=[c.id for c in failing],
                tags=sorted({t for c in failing for t in c.tags}),
            )

        payload["newly_unlocked"] = None
        if (
            session.active
            and payload["total"] > 0
            and payload["passed"] == payload["total"]
        ):
            session.level_cleared_at.setdefault(str(session.unlocked_level), time.time())
            session.log("level_cleared", level=session.unlocked_level)
            if session.unlocked_level < session.max_level:
                session.unlocked_level += 1
                payload["newly_unlocked"] = session.unlocked_level
            else:
                payload["all_clear"] = True
            session.save()
            payload["unlocked_level"] = session.unlocked_level
        payload["state"] = _state_payload()
        return self._json(payload)

    def _stubs(self, body):
        session = active_session()
        if session is None:
            return self._json({"error": "no active session"}, 400)
        problem = get_problem(session.problem)
        level = int(body.get("level") or session.unlocked_level)
        if level > session.unlocked_level:
            return self._json({"error": "level is locked"}, 403)
        ok, message = scaffold.append_level(problem, Path(session.solution_path), level)
        return self._json(
            {"ok": ok, "message": message, "code": Path(session.solution_path).read_text()}
        )

    def _finish(self, body):
        session = active_session()
        if session is None:
            return self._json({"error": "no active session"}, 400)
        if session.active:
            session.finished_at = time.time()
            session.save()
            session.log("session_end", abandoned=bool(body.get("abandon")))
        problem = get_problem(session.problem)
        return self._json({"debrief": _debrief_payload(session, problem), "state": _state_payload()})

    def _abandon(self, body):
        """Close the current attempt and return to the problem picker.

        Clearing the active pointer is what distinguishes this from `finish`: a
        finished-but-still-active session keeps you in the review view, which is
        not what someone who wants to switch problems is asking for.
        """
        session = active_session()
        if session is not None and session.active:
            session.finished_at = time.time()
            session.save()
            session.log("session_end", abandoned=True)
        if ACTIVE_POINTER.exists():
            ACTIVE_POINTER.unlink()
        return self._json(_state_payload())

    def _complete(self, body):
        """Completions and signature help for the buffer, by static analysis."""
        from webui.complete import analyse

        code = body.get("code")
        if not isinstance(code, str):
            return self._json({"completions": [], "signature": None, "word": ""})
        try:
            line = max(1, int(body.get("line") or 1))
            col = max(0, int(body.get("col") or 0))
        except (TypeError, ValueError):
            return self._json({"completions": [], "signature": None, "word": ""})
        return self._json(analyse(code, line, col))

    def _check(self, body):
        """Compile the buffer and report syntax errors, without saving it.

        This is what makes the editor feel like an editor: the red underline
        appears while you type instead of after a run. It only ever compiles --
        nothing is executed, and the workspace file is untouched.
        """
        code = body.get("code")
        if not isinstance(code, str):
            return self._json({"errors": []})
        try:
            compile(code, "solution.py", "exec")
        except SyntaxError as exc:
            return self._json({"errors": [{
                "line": exc.lineno or 1,
                "col": exc.offset or 1,
                "msg": f"{type(exc).__name__}: {exc.msg}",
            }]})
        except ValueError as exc:  # e.g. source containing null bytes
            return self._json({"errors": [{"line": 1, "col": 1, "msg": str(exc)}]})
        return self._json({"errors": []})

    def _dispute(self, body):
        session = active_session()
        record = {
            "t": time.time(),
            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
            "session": session.id if session else None,
            "problem": session.problem if session else None,
            "case": body.get("case"),
            "claim": body.get("claim", ""),
        }
        target = ROOT / "sessions" / "disputes.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a") as handle:
            handle.write(json.dumps(record) + "\n")
        return self._json({"logged": True})

    def _decisions(self):
        session = active_session()
        if session is None:
            return self._json({"error": "no session"}, 400)
        if session.active and not session.expired:
            return self._json(
                {
                    "locked": True,
                    "reason": "This is the answer key and your session is still running.",
                },
                403,
            )
        problem = get_problem(session.problem)
        path = problem.directory / "DECISIONS.md"
        return self._json({"locked": False, "html": to_html(path.read_text())})

    def _answer(self, query):
        session = active_session()
        if session is None:
            return self._json({"error": "no session"}, 400)
        # Same gate as the answer key: a worked solution during a live attempt is
        # the whole measurement, gone.
        if session.active and not session.expired:
            return self._json(
                {
                    "locked": True,
                    "reason": "This is a worked solution and your session is still running.",
                },
                403,
            )
        problem = get_problem(session.problem)
        raw = (query.get("level") or [None])[0]
        try:
            level = int(raw) if raw not in (None, "", "all") else None
        except ValueError:
            return self._json({"error": "level must be a number"}, 400)
        if level is not None and not 1 <= level <= problem.max_level:
            return self._json({"error": f"level must be 1-{problem.max_level}"}, 400)

        found = answer_mod.resolve(problem, level)
        if found is None:
            return self._json(
                {
                    "locked": False,
                    "available": False,
                    "reason": f"No worked solution yet. Put one at solutions/{problem.key}.py.",
                }
            )
        source, provenance, path = found
        return self._json(
            {
                "locked": False,
                "available": True,
                "level": level,
                "max_level": problem.max_level,
                "provenance": provenance,
                "source": source,
                "path": str(path.relative_to(ROOT)),
                "snapshots": answer_mod.snapshot_levels(problem),
            }
        )


def serve(port: int = 8765, open_browser: bool = True) -> None:
    httpd = HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"  Practice IDE running at {url}")
    print("  Press Ctrl-C to stop.\n")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")


if __name__ == "__main__":
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
