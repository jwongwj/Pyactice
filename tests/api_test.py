#!/usr/bin/env python3
"""Backend tests for the practice IDE and harness.

Covers what the browser tests cannot reach cheaply: the exact shape of every JSON
payload, the invariants that must hold no matter what the front end does, and the
failure paths (syntax errors, infinite loops, dead sessions, path traversal).

    python3 tests/api_test.py

Runs against a throwaway server on a high port with the repo's own sessions/ and
workspace/ moved aside, so it never disturbs a live attempt.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PORT = 8791
BASE = f"http://127.0.0.1:{PORT}"
PY = sys.executable

sys.path.insert(0, str(REPO))

PASS, FAIL = [], []


def check(name):
    def wrap(fn):
        try:
            extra = fn()
            PASS.append(name)
            print(f"  \033[32m✓\033[0m {name}" + (f"  {extra}" if extra else ""))
        except AssertionError as exc:
            FAIL.append((name, str(exc)))
            print(f"  \033[31m✗ {name}\033[0m\n      {exc}")
        except Exception as exc:  # a crash is a failure, not an error in the runner
            FAIL.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"  \033[31m✗ {name}\033[0m\n      {type(exc).__name__}: {exc}")
        return fn
    return wrap


def api(path, body=None, expect_status=None):
    url = BASE + path
    if body is None:
        request = urllib.request.Request(url)
    else:
        request = urllib.request.Request(
            url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
    try:
        with urllib.request.urlopen(request) as response:
            status, payload = response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        status, payload = exc.code, json.loads(exc.read() or b"{}")
    if expect_status is not None:
        assert status == expect_status, f"{path} returned {status}, expected {expect_status}"
    return payload


def _port_answers() -> bool:
    try:
        urllib.request.urlopen(BASE + "/api/state", timeout=1)
        return True
    except Exception:
        return False


def start_server():
    # Refuse to run against a server this function did not start. The wait loop below
    # polls until the port answers, so a leftover process from an earlier run satisfies
    # it instantly and the whole suite then tests a STALE bank -- which is how four
    # newly-written units appeared in the test process and not in the picker, and read
    # as a bank bug rather than a zombie. This has cost the project a debugging session
    # twice now.
    if _port_answers():
        # A leftover `harness ui --port <our port>` is this suite's own debris from a run
        # that died before its cleanup -- identifiable, and safe to reap. Anything else
        # answering here is not ours to kill, and testing it would be worse than stopping.
        reaped = subprocess.run(
            ["pkill", "-f", f"harness ui --port {PORT}"], capture_output=True
        ).returncode == 0
        if reaped:
            for _ in range(20):
                time.sleep(0.15)
                if not _port_answers():
                    break
        if _port_answers():
            raise RuntimeError(
                f"something is already listening on {BASE} and it is not one of this "
                f"suite's servers. Refusing to run, because the suite would silently "
                f"test that process instead of this code."
            )

    # PYTHONDONTWRITEBYTECODE: `reset()` deletes every __pycache__ in the repo, and the
    # server then imports the whole bank and writes them back. That race produced an
    # intermittent failure where the server saw fewer problems than the test process --
    # seen three times, never reproducible on demand. Writing no bytecode at all leaves
    # nothing to be stale, half-written, or deleted underneath a running import.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen(
        [PY, "-m", "harness", "ui", "--port", str(PORT), "--no-open"],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env,
    )
    for _ in range(50):
        time.sleep(0.15)
        if _port_answers():
            return proc
    err = proc.stderr.read().decode()[-800:] if proc.stderr else ""
    raise RuntimeError(f"server never came up\n{err}")


# Same reasoning as tests/ui.test.js: these tests wipe sessions/ and workspace/,
# so whatever attempt is in progress gets stashed first and put back on exit.
_STASH = Path(tempfile.mkdtemp(prefix="pfs-stash-"))
_STASHED = False


def _stash():
    global _STASHED
    if _STASHED:
        return
    for name in ("sessions", "workspace"):
        source = REPO / name
        if source.exists():
            shutil.copytree(source, _STASH / name)
    _STASHED = True


def restore():
    global _STASHED
    if not _STASHED:
        return
    for name in ("sessions", "workspace"):
        shutil.rmtree(REPO / name, ignore_errors=True)
        if (_STASH / name).exists():
            shutil.copytree(_STASH / name, REPO / name)
    shutil.rmtree(_STASH, ignore_errors=True)
    _STASHED = False


def reset():
    _stash()
    for name in ("sessions", "workspace"):
        shutil.rmtree(REPO / name, ignore_errors=True)
    # Python's bytecode cache keys on mtime at one-second granularity, so a file
    # edited and tested inside the same second can be run from a stale .pyc. That
    # produced a phantom failure once already; clearing is cheaper than doubting
    # every red result.
    for cache in REPO.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


L1_GOOD = (REPO / "tests/fixtures/file_hosting_level1.py").read_text()


def main() -> int:
    reset()
    server = start_server()
    print("\n\033[1mPractice IDE — backend tests\033[0m\n")
    try:
        run_all()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        restore()

    print(f"\n  {len(PASS)}/{len(PASS) + len(FAIL)} checks passed")
    if FAIL:
        print("\n  \033[31mFAILURES\033[0m")
        for name, why in FAIL:
            print(f"   - {name}: {why}")
    print()
    return 1 if FAIL else 0


def run_all():
    # ---------------------------------------------------------------- picker

    @check("no session -> picker with the whole bank")
    def _():
        state = api("/api/state")
        assert state["active"] is False, "reported an active session on a clean slate"
        # A property, not a fixed list: asserting the exact five keys meant every new
        # problem failed this test, which is the wrong signal entirely.
        from harness.loader import BROKEN, all_problems
        keys = sorted(p["key"] for p in state["problems"])
        bank = sorted(all_problems())
        assert keys == bank, (
            f"picker and bank disagree\n      picker: {keys}\n      bank:   {bank}"
        )
        assert not BROKEN, f"problems failed to load: {BROKEN}"
        assert len(keys) >= 5, f"bank shrank unexpectedly: {keys}"
        return f"{len(keys)} problems, none broken"

    @check("picker blurbs describe level 1 only")
    def _():
        state = api("/api/state")
        banned = ["prefix", "capacity", "merge", "backup", "restore", "ttl",
                  "rollback", "cashback", "spender", "scan",
                  "permission", "symlink", "symbolic", "subtree"]
        for problem in state["problems"]:
            # Only a multi-level problem can leak a later level. A drill has one level,
            # so every word in its blurb is level 1 by definition.
            if problem["levels"] < 2:
                continue
            hits = [w for w in banned if w in problem["blurb"].lower()]
            assert not hits, f"{problem['key']} blurb leaks {hits}: {problem['blurb']}"
        return "clean"

    # ---------------------------------------------------------------- start

    @check("start creates a session at level 1")
    def _():
        state = api("/api/start", {"problem": "file_hosting", "minutes": 90})
        assert state["active"], "session not active after start"
        assert state["session"]["unlocked_level"] == 1, state["session"]
        assert state["session"]["remaining_s"] > 5300, state["session"]["remaining_s"]
        unlocked = [l["number"] for l in state["levels"] if l["unlocked"]]
        assert unlocked == [1], f"levels unlocked at start: {unlocked}"
        return f"attempt {state['session']['attempt']}"

    @check("the statement sent to the browser holds level 1 only")
    def _():
        html = api("/api/state")["statement"]["html"]
        assert "Level 1" in html, "level 1 heading missing"
        for n in (2, 3, 4):
            assert f"Level {n}" not in html, f"level {n} leaked into the statement"
        return "level 1 only"

    @check("the contract sent to the browser holds level 1 only")
    def _():
        from harness.loader import get_problem
        html = api("/api/state")["contract_html"]
        locked = [m.display for m in get_problem("file_hosting").methods
                  if m.level > 1 and m.display in html]
        assert not locked, f"contract leaks locked operations: {locked}"
        for word in ("ttl", "rollback", "timestamp"):
            assert word not in html.lower(), f"contract leaks the concept '{word}'"
        return "clean"

    @check("only level 1's examples are sent")
    def _():
        examples = api("/api/state")["statement"]["examples"]
        levels = [group["level"] for group in examples]
        assert levels == [1], f"examples sent for levels {levels}"
        return f"{len(examples[0]['cases'])} worked examples"

    @check("the starter file is written with level 1 stubs only")
    def _():
        code = api("/api/state")["code"]
        assert "def file_upload" in code, "level 1 stub missing"
        assert "def file_search" not in code, "a level 2 stub was written"
        assert "NotImplementedError" in code, "stubs do not raise"
        return f"{len(code.splitlines())} lines"

    # ---------------------------------------------------------------- running

    @check("a failing run reports per-case results")
    def _():
        result = api("/api/run", {"code": "class FileHost:\n    pass\n"})
        assert not result["load_error"], result["load_error"]
        assert result["total"] == 13, f"expected 13 level-1 cases, got {result['total']}"
        assert result["passed"] == 0, result["passed"]
        assert result["newly_unlocked"] is None, "unlocked a level on a failing run"
        return f"{result['passed']}/{result['total']}"

    @check("hidden cases expose no operations, expectations or values")
    def _():
        result = api("/api/run", {"code": "class FileHost:\n    pass\n"})
        hidden = [c for lv in result["levels"] for c in lv["cases"] if not c["visible"]]
        assert hidden, "no hidden cases in the payload to check"
        for case in hidden:
            assert case["ops"] == [], f"{case['id']} shipped {len(case['ops'])} operations"
            assert case["doc"] == "", f"{case['id']} shipped its description"
        return f"{len(hidden)} hidden cases, no detail"

    @check("a hidden failure shows its operation shape but no arguments or values")
    def _():
        result = api("/api/run", {"code": "class FileHost:\n    def __init__(self): self.f = {}\n"})
        hidden = [c for lv in result["levels"] for c in lv["cases"] if not c["visible"]]
        assert hidden, "no hidden cases to inspect"
        with_shape = [c for c in hidden if c.get("shape")]
        assert with_shape, "no hidden case carried a shape"
        for case in with_shape:
            for name in case["shape"]:
                # Operation names are public -- they are printed in the statement.
                assert name.isupper() or "_" in name, f"shape held something odd: {name}"
                assert "(" not in name, f"shape leaked arguments: {name}"
            assert case["ops"] == [], f"{case['id']} still shipped operations"
            blob = json.dumps(case)
            assert "expected" not in blob, f"{case['id']} leaked an expected value"
        return f"{len(with_shape)} shapes, names only"

    @check("visible cases do expose their operations")
    def _():
        result = api("/api/run", {"code": "class FileHost:\n    pass\n"})
        visible = [c for lv in result["levels"] for c in lv["cases"]
                   if c["visible"] and not c["passed"]]
        assert visible, "no failing visible cases"
        assert any(c["ops"] for c in visible), "visible cases shipped no operations"
        return f"{len(visible)} visible cases"

    @check("a syntax error is reported, not crashed on")
    def _():
        result = api("/api/run", {"code": "class FileHost:\ndef broken(\n"})
        error = result["load_error"]
        assert error, "a syntax error produced no load_error"
        assert "Error" in error.splitlines()[0], f"first line is not the error: {error[:80]}"
        assert "Traceback" not in error, "harness internals shown to the candidate"
        assert "runner.py" not in error, "harness frames shown to the candidate"
        assert "solution.py, line" in error, f"no line number given: {error[:120]}"
        return error.splitlines()[0][:60]

    @check("a missing class is reported by name")
    def _():
        result = api("/api/run", {"code": "class Wrong:\n    pass\n"})
        assert result["load_error"], "no error for a missing class"
        assert "FileHost" in result["load_error"], result["load_error"][:120]
        return "named"

    @check("an infinite loop is cut off rather than hanging the server")
    def _():
        started = time.time()
        result = api("/api/run", {"code": (
            "class FileHost:\n"
            "    def __init__(self): pass\n"
            "    def file_upload(self, n, s):\n"
            "        while True: pass\n"
        )})
        elapsed = time.time() - started
        assert not result["load_error"], result["load_error"]
        outcomes = {c["outcome"] for lv in result["levels"] for c in lv["cases"]}
        assert "timeout" in outcomes, f"no timeout reported; outcomes were {outcomes}"
        assert elapsed < 90, f"took {elapsed:.0f}s"
        return f"{elapsed:.0f}s, server alive"

    @check("the server still answers after a runaway solution")
    def _():
        assert api("/api/state")["active"], "server lost the session after a timeout"
        return "alive"

    # ---------------------------------------------------------------- stubs

    @check("REGRESSION: appending stubs refuses to shadow existing methods")
    def _():
        mine = (
            "from __future__ import annotations\n\n\n"
            "class FileHost:\n"
            "    def __init__(self) -> None:\n        self.f = {}\n\n"
            "    def file_upload(self, file_name, size):\n"
            "        self.f[file_name] = size   # my real work\n"
        )
        api("/api/save", {"code": mine})
        result = api("/api/stubs", {})
        assert result["ok"] is False, "appended stubs over methods that already exist"
        assert result["code"].count("def file_upload") == 1, "duplicated file_upload"
        assert "my real work" in result["code"], "the candidate's code was lost"
        return result["message"][:70]

    @check("the state tells the UI when there is nothing to append")
    def _():
        assert api("/api/state")["session"]["stubs_pending"] is False, \
            "offered stubs the file already has"
        return "button correctly disabled"

    # ---------------------------------------------------------------- unlock

    @check("clearing level 1 unlocks level 2 exactly once")
    def _():
        first = api("/api/run", {"code": L1_GOOD})
        assert first["passed"] == first["total"], f"{first['passed']}/{first['total']}"
        assert first["newly_unlocked"] == 2, first["newly_unlocked"]
        second = api("/api/run", {"code": L1_GOOD})
        assert second["newly_unlocked"] is None, "a repeat run unlocked another level"
        assert api("/api/state")["session"]["unlocked_level"] == 2, "level drifted"
        return "level 2, and stays there"

    @check("level 2 content appears only after the unlock")
    def _():
        state = api("/api/state")
        assert "Level 2" in state["statement"]["html"], "level 2 statement missing"
        assert "Level 3" not in state["statement"]["html"], "level 3 leaked"
        assert "FILE_SEARCH" in state["contract_html"], "level 2 contract missing"
        assert "ROLLBACK" not in state["contract_html"], "level 4 leaked"
        assert [g["level"] for g in state["statement"]["examples"]] == [1, 2]
        return "levels 1-2"

    @check("level 2's stubs can now be appended, once")
    def _():
        first = api("/api/stubs", {})
        assert first["ok"], first.get("message") or first.get("error")
        assert "def file_search" in first["code"], "stub not written"
        again = api("/api/stubs", {})
        assert again["ok"] is False, "appended level 2 stubs twice"
        assert first["code"].count("def file_search") == 1
        return "idempotent"

    @check("a locked level's stubs cannot be requested")
    def _():
        result = api("/api/stubs", {"level": 4}, expect_status=403)
        assert "locked" in json.dumps(result).lower(), result
        return "403"

    # ---------------------------------------------------------------- answer key

    @check("the answer key is refused while the clock runs")
    def _():
        result = api("/api/decisions", expect_status=403)
        assert result.get("locked") is True, result
        return "403"

    # ---------------------------------------------------------------- durability

    @check("the clock and session survive a server restart")
    def _():
        nonlocal_server = api("/api/state")["session"]
        before = nonlocal_server["remaining_s"]
        subprocess.run(["pkill", "-f", f"harness ui --port {PORT}"], capture_output=True)
        time.sleep(0.6)
        globals()["_restarted"] = start_server()
        after = api("/api/state")["session"]
        assert after["id"] == nonlocal_server["id"], "session identity changed"
        assert after["unlocked_level"] == 2, "unlocked level was lost"
        assert after["remaining_s"] <= before, "clock went backwards"
        assert before - after["remaining_s"] < 30, "clock jumped"
        return f"{after['id']} intact"

    @check("saved code survives a restart")
    def _():
        assert "def file_search" in api("/api/state")["code"], "code was lost"
        return "intact"

    # ---------------------------------------------------------------- finish

    @check("finish produces a debrief with per-level timings")
    def _():
        result = api("/api/finish", {})
        debrief = result["debrief"]
        assert debrief["runs"] >= 3, debrief["runs"]
        levels = {l["level"]: l for l in debrief["levels"]}
        assert levels[1]["cleared"] is True, "level 1 not recorded as cleared"
        assert levels[3]["cleared"] is False, "level 3 wrongly cleared"
        assert debrief["score"] > 0, debrief["score"]
        return f"score {debrief['score']}, {debrief['runs']} runs"

    @check("the answer key opens once the session is finished")
    def _():
        result = api("/api/decisions")
        assert result.get("locked") is False, result
        assert "ROLLBACK" in result["html"] or "rollback" in result["html"].lower()
        return f"{len(result['html'])} chars"

    @check("review mode opens everything, or nothing")
    def _():
        state = api("/api/state")
        assert state["session"]["finished"] is True, "expected a finished session here"
        assert state.get("review") is True, "review flag not set"
        statement = state["statement"]["html"]
        assert "Level 4" in statement, "review mode still hides the level-4 question"
        groups = [g["level"] for g in state["statement"]["examples"]]
        assert groups == [1, 2, 3, 4], f"examples sent for {groups}"
        result = api("/api/run", {"code": "class FileHost:\n    pass\n"})
        levels = [lv["level"] for lv in result["levels"]]
        assert levels == [1, 2, 3, 4], f"review mode ran {levels}"
        hidden = [c for lv in result["levels"] for c in lv["cases"] if not c["visible"]]
        assert not hidden, f"{len(hidden)} cases still hidden in review mode"
        return "statement, contract, tests and key all open"

    @check("a finished session reveals the whole contract")
    def _():
        html = api("/api/state")["contract_html"]
        assert "ROLLBACK" in html, "contract still gated after finishing"
        return "all four levels"

    # ---------------------------------------------------------------- navigation

    @check("abandon returns to the picker")
    def _():
        state = api("/api/abandon", {})
        assert state["active"] is False, "still in a session after abandoning"
        from harness.loader import all_problems
        assert len(state["problems"]) == len(all_problems()), (
            f"picker has {len(state['problems'])} problems, bank has {len(all_problems())}"
        )
        return "back at the picker"

    @check("a fresh attempt starts from stubs and archives the old code")
    def _():
        state = api("/api/start", {"problem": "file_hosting"})
        assert "NotImplementedError" in state["code"], "stubs not restored"
        assert "self.files[dest]" not in state["code"], "previous attempt leaked in"
        assert state["session"]["attempt"] == 2, state["session"]["attempt"]
        archived = list((REPO / "workspace/file_hosting/previous-attempts").glob("*.py"))
        assert archived, "the previous attempt was not archived"
        return f"attempt 2, {len(archived)} archived"

    @check("a live session opens none of it")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_hosting"})
        state = api("/api/state")
        assert state.get("review") is False, "a live session reports review mode"
        assert "Level 2" not in state["statement"]["html"], "live statement leaked level 2"
        assert [g["level"] for g in state["statement"]["examples"]] == [1]
        result = api("/api/run", {"code": "class FileHost:\n    pass\n"})
        assert [lv["level"] for lv in result["levels"]] == [1], "a live run left level 1"
        assert any(not c["visible"] for lv in result["levels"] for c in lv["cases"]), \
            "hidden cases were revealed during a live attempt"
        return "everything gated"

    @check("resume keeps the existing code")
    def _():
        api("/api/save", {"code": "# keep me\nclass FileHost:\n    pass\n"})
        state = api("/api/start", {"problem": "file_hosting", "resume": True})
        assert "# keep me" in state["code"], "resume discarded the code"
        return "kept"

    # ---------------------------------------------------------------- resume vs start over

    @check("unfinished work is advertised, so the UI can offer Resume")
    def _():
        api("/api/abandon", {})
        # Fresh stubs are not "work" -- otherwise every problem you glanced at would
        # claim to have something worth resuming.
        api("/api/start", {"problem": "file_hosting"})
        api("/api/abandon", {})
        cards = {p["key"]: p for p in api("/api/state")["problems"]}
        assert cards["file_hosting"]["has_work"] is False, "untouched stubs counted as work"

        api("/api/start", {"problem": "file_hosting"})
        api("/api/save", {"code": "class FileHost:\n    pass  # my real work\n"})
        api("/api/abandon", {})
        cards = {p["key"]: p for p in api("/api/state")["problems"]}
        assert cards["file_hosting"]["has_work"] is True, "edited file not reported as work"
        return "stubs no, edits yes"

    @check("resume keeps the file; starting over archives it and writes stubs")
    def _():
        mine = "class FileHost:\n    pass  # do not lose me\n"
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_hosting"})
        api("/api/save", {"code": mine})
        api("/api/abandon", {})

        kept = api("/api/start", {"problem": "file_hosting", "resume": True})
        assert "do not lose me" in kept["code"], "resume did not keep the file"
        api("/api/abandon", {})

        wiped = api("/api/start", {"problem": "file_hosting"})
        assert "do not lose me" not in wiped["code"], "start over kept the old file"
        assert "NotImplementedError" in wiped["code"], "start over did not write stubs"
        # Nothing is ever deleted -- it must be recoverable from the archive.
        archives = list((REPO / "workspace/file_hosting/previous-attempts").glob("*.py"))
        assert any("do not lose me" in a.read_text() for a in archives), \
            "the overwritten file was not archived anywhere"
        return f"kept on resume, archived on start over ({len(archives)} archives)"

    @check("a non-timed problem starts untimed, whatever minutes the client sends")
    def _():
        api("/api/abandon", {})
        state = api("/api/start", {"problem": "two_sum_pairs", "minutes": 90})
        assert state["session"]["budget_minutes"] is None, (
            f"function problem got a clock: {state['session']['budget_minutes']}"
        )
        assert state["session"]["remaining_s"] is None or state["session"]["remaining_s"] > 10**6, \
            f"untimed session reports a countdown: {state['session']['remaining_s']}"
        # And it must not silently expire, which is what --minutes 0 used to do.
        assert state["session"]["finished"] is False, "untimed session started finished"
        cards = {p["key"]: p for p in api("/api/state").get("problems", [])} if False else {}
        api("/api/abandon", {})
        return "untimed"

    @check("a progressive problem still gets its clock")
    def _():
        state = api("/api/start", {"problem": "file_hosting", "minutes": 90})
        assert state["session"]["budget_minutes"] == 90, state["session"]["budget_minutes"]
        assert state["session"]["remaining_s"] > 5300, state["session"]["remaining_s"]
        api("/api/abandon", {})
        return "90 minutes"

    @check("only timed problems advertise a clock")
    def _():
        cards = {p["key"]: p for p in api("/api/state")["problems"]}
        assert cards["file_hosting"]["timed"] is True, "progressive problem not timed"
        assert cards["two_sum_pairs"]["timed"] is False, "function problem claims a clock"
        return "file_hosting timed, two_sum_pairs not"

    # ---------------------------------------------------------------- drills and constraints

    @check("constraints are scoped to their own drill, not the whole file")
    def _():
        # The bug this guards: a twelve-drill file meant every constraint saw every
        # other drill's code, so a correct comprehension was reported as "you used for"
        # because an unrelated drill above it had a loop.
        from harness.constraints import Forbid, check as ccheck
        src = (
            "def uses_a_loop(xs):\n"
            "    out = []\n"
            "    for x in xs:\n"
            "        out.append(x)\n"
            "    return out\n"
            "\n"
            "def is_a_comprehension(xs):\n"
            "    return [x for x in xs]\n"
        )
        rule = (Forbid(("for",), because="use a comprehension"),)
        assert ccheck(src, "uses_a_loop", rule).violations, "missed a real for loop"
        clean = ccheck(src, "is_a_comprehension", rule)
        assert clean.ok, f"false positive from another drill's code: {clean.violations}"
        # A missing function reports nothing; the runner already says it is missing.
        assert ccheck(src, "not_here", rule).ok, "complained about a function that is absent"
        return "scoped"

    @check("every unit oracle produces no violations on any of its drills")
    def _():
        from harness.loader import all_problems
        from harness.runner import run as run_cases
        drills = [p for p in all_problems().values() if p.solution_key]
        assert len(drills) > 50, f"only {len(drills)} drills found; the split did not run"
        cases = bad = 0
        for problem in drills:
            oracle = REPO / "solutions" / f"{problem.solution_key}.py"
            if not oracle.exists():
                continue
            result = run_cases(problem, oracle, max_level=1, op_timeout=10.0)
            for level in result.levels:
                for case in level.cases:
                    cases += 1
                    if not case.passed:
                        bad += 1
                        print(f"        {problem.key}: {case.name}")
            assert not result.violations, (
                f"false positive on the {problem.key} oracle: {result.violations}"
            )
        assert bad == 0, f"{bad} oracle cases fail"
        return f"{len(drills)} drills, {cases} cases, zero violations"

    @check("a correct-but-unidiomatic drill is flagged without losing a case")
    def _():
        from harness.loader import get_problem
        from harness.runner import run as run_cases
        import tempfile, pathlib as _p
        oracle = (REPO / "solutions" / "for_loops.py").read_text()
        hand_rolled = oracle.replace(
            "def shout(names):\n    return [name.upper() for name in names]",
            "def shout(names):\n"
            "    out = []\n"
            "    for name in names:\n"
            "        out.append(name.upper())\n"
            "    return out",
        )
        assert hand_rolled != oracle, "could not rewrite shout for the probe"
        with tempfile.TemporaryDirectory() as d:
            path = _p.Path(d) / "sol.py"
            path.write_text(hand_rolled)
            result = run_cases(get_problem("for_loops.shout"), path,
                               max_level=1, op_timeout=10.0)
        passed = sum(1 for l in result.levels for c in l.cases if c.passed)
        total = sum(len(l.cases) for l in result.levels)
        assert total, "the SHOUT drill owns no cases"
        assert passed == total, "an idiom violation cost a test case; it must not"
        assert "SHOUT" in result.violations, "the hand-rolled loop was not flagged"
        assert len(result.violations) == 1, f"flagged more than SHOUT: {list(result.violations)}"
        return f"{total} cases pass, SHOUT flagged"

    @check("a wrong drill is not also called correct")
    def _():
        from harness import render
        from harness.loader import get_problem
        from harness.runner import run as run_cases
        import tempfile, pathlib as _p
        broken = (REPO / "solutions" / "for_loops.py").read_text().replace(
            "def shout(names):\n    return [name.upper() for name in names]",
            "def shout(names):\n"
            "    out = []\n"
            "    for name in names:\n"
            "        out.append(name.lower())\n"
            "    return out",
        )
        with tempfile.TemporaryDirectory() as d:
            path = _p.Path(d) / "sol.py"
            path.write_text(broken)
            result = run_cases(get_problem("for_loops.shout"), path,
                               max_level=1, op_timeout=10.0)
        assert "SHOUT" in result.violations, "the loop itself was not detected"
        report = "\n".join(render.constraint_report(result))
        assert "SHOUT" not in report, (
            "a failing drill was reported as 'correct, but' — which is simply untrue"
        )
        return "wrong stays wrong"

    @check("the picker payload carries what the UI needs to nest a drill in its unit")
    def _():
        state = api("/api/state")
        cards = {c["key"]: c for c in state["problems"]}
        drills = [c for c in cards.values() if c["unit"]]
        assert len(drills) > 50, f"only {len(drills)} cards claim a unit"

        units = {}
        for card in drills:
            key, title = card["unit"]
            units.setdefault(key, set()).add(title)
            # The short label is what a nested row shows. The full title repeats the
            # unit, which reads badly inside a box already headed with it.
            assert card["label"] != card["title"], f"{card['key']} has no short label"
            assert card["label"] in card["title"], (
                f"{card['key']}: label {card['label']!r} is not part of {card['title']!r}"
            )
            assert key not in cards, f"the unsplit unit {key} is offered as a problem"
        for key, titles in units.items():
            assert len(titles) == 1, f"unit {key} reports {len(titles)} different titles"

        # A standalone problem must NOT claim a unit, or it would be filed under one.
        for card in cards.values():
            if not card["unit"]:
                assert card["label"] == card["title"], f"{card['key']} has a stray label"
        # Counted from the bank rather than hardcoded: this used to assert 8 and broke
        # the moment category 2 arrived, which is a test measuring the wrong thing.
        expected = len({card["unit"][0] for card in cards.values() if card["unit"]})
        assert len(units) == expected, f"{len(units)} units grouped, {expected} in the bank"
        assert len(units) >= 8, f"only {len(units)} units; the bank shrank unexpectedly"
        return f"{len(drills)} drills across {len(units)} units"

    # ---------------------------------------------------------------- the split

    @check("a unit splits into one problem per drill, each owning its own cases")
    def _():
        from harness import units
        from harness.loader import _import_unit, all_problems
        bank = all_problems()
        path = REPO / "curriculum/1-basic-python/01-for-loops/unit.py"
        unit = None
        import importlib.util as _u
        spec = _u.spec_from_file_location("probe_unit", path)
        module = _u.module_from_spec(spec)
        spec.loader.exec_module(module)
        unit = module.UNIT
        drills = units.split(unit)
        assert len(drills) == len(unit.methods), (
            f"{len(unit.methods)} drills authored, {len(drills)} problems produced"
        )
        # Every case is claimed exactly once: a case owned by nobody is dead weight,
        # and one owned twice is graded twice under two different titles.
        counted = sum(len(d.cases) for d in drills)
        assert counted == len(unit.cases), (
            f"{len(unit.cases)} cases authored but {counted} distributed"
        )
        for drill in drills:
            assert len(drill.methods) == 1, f"{drill.key} carries {len(drill.methods)} methods"
            name = drill.methods[0].display
            for case in drill.cases:
                assert all(op.name == name for op in case.ops), (
                    f"{drill.key} owns a case for another drill"
                )
            assert drill.key in bank, f"{drill.key} is not in the bank"
            assert drill.unit == (unit.key, unit.title)
            assert drill.solution_key == unit.key
            assert unit.key not in bank, "the unsplit unit is still offered as a problem"
        return f"{len(drills)} drills, {counted} cases, none shared"

    @check("a drill's statement states the task and never the answer")
    def _():
        from harness.answer import extract_function
        from harness.loader import all_problems
        leaks = []
        for problem in all_problems().values():
            if not problem.solution_key:
                continue
            body = problem.statement_body(1)
            assert body.strip(), f"{problem.key} has an empty statement"
            assert problem.methods[0].display in body, (
                f"{problem.key} does not name the drill it is asking for"
            )
            assert f"def {problem.methods[0].resolved_name()}" in body, (
                f"{problem.key} does not give the signature"
            )
            if problem.methods[0].constraint_note:
                assert "Constraint" in body, f"{problem.key} hides its constraint"
            oracle = REPO / "solutions" / f"{problem.solution_key}.py"
            if not oracle.exists():
                continue
            answer = extract_function(oracle.read_text(), problem.methods[0].resolved_name())
            # The answer's body, minus its signature and docstring: if any line of real
            # code from the oracle appears in the statement, the statement is the answer.
            for line in answer.splitlines():
                line = line.strip()
                if len(line) < 18 or line.startswith(("def ", "#", '"', "'", "import ", "from ")):
                    continue
                if line in body:
                    leaks.append(f"{problem.key}: {line}")
        assert not leaks, "statements leak the answer:\n        " + "\n        ".join(leaks)
        return "no statement contains a line of its own answer"

    @check("a drill's answer is its own function, not the whole unit")
    def _():
        import ast
        from harness import answer as answermod
        from harness.loader import get_problem
        problem = get_problem("for_loops.numbered")
        got = answermod.resolve(problem, 1)
        assert got is not None, "no answer for a drill whose unit has an oracle"
        source, provenance, path = got
        assert provenance == "drill", provenance
        assert path.name == "for_loops.py", "a drill should read its unit's oracle"
        tree = ast.parse(source)
        defs = [n.name for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assert defs == ["numbered"], f"expected only numbered(), got {defs}"
        whole = ast.parse(path.read_text())
        siblings = [n.name for n in whole.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assert len(siblings) > 1, "the unit oracle has only one function; test is vacuous"
        return f"1 of {len(siblings)} functions extracted"

    @check("a drill is untimed and serves the unit's lesson separately")
    def _():
        from harness.loader import get_problem
        problem = get_problem("for_loops.numbered")
        assert problem.timed is False, "a drill got a clock"
        lesson = problem.lesson_path
        assert lesson is not None and lesson.exists(), "no LESSON.md for the unit"
        assert lesson.name == "LESSON.md", lesson
        text = lesson.read_text()
        # The lesson is the unit's, not the drill's: shared by all twelve.
        assert get_problem("for_loops.shout").lesson_path == lesson
        # A drill has no contract or answer key of its own; both would be the answer.
        assert not (problem.directory / "CONTRACT.md").exists(), (
            "a drill has a CONTRACT.md; for a one-function drill that is the answer"
        )
        assert problem.statement_body(1) != text, "the lesson is being served as the task"
        return f"untimed, LESSON.md ({len(text)} chars) beside the task"

    @check("the bank is cached but still notices an edited problem")
    def _():
        from harness import loader
        # Counted, not timed. The property is "the files are read once"; a wall-clock
        # ratio measures the machine's mood as much as the cache, and did fail here on
        # a run where nothing was wrong.
        real = loader._import_unit
        reads = []
        loader._import_unit = lambda path: (reads.append(path), real(path))[1]
        try:
            loader.invalidate()
            loader.all_problems()
            cold = len(reads)
            assert cold > 0, "the cold read imported no unit files at all"
            for _ in range(20):
                loader.all_problems()
            assert len(reads) == cold, (
                f"{len(reads) - cold} unit files re-read across 20 cached calls"
            )
        finally:
            loader._import_unit = real

        # An edit must invalidate it, or authoring a problem would need a restart.
        target = REPO / "curriculum/1-basic-python/01-for-loops/unit.py"
        key = "for_loops.shout"
        before = dict(loader.all_problems())
        original = target.read_text()
        try:
            target.write_text(original.replace(
                'title="1.1 For loops and comprehensions"',
                'title="1.1 EDITED"', 1))
            after = loader.all_problems()
            assert after[key].title.startswith("1.1 EDITED"), (
                f"an edited problem was served from the cache: {after[key].title}"
            )
        finally:
            target.write_text(original)
            loader.invalidate()
        assert loader.all_problems()[key].title == before[key].title
        return f"{cold} unit files read once, then 0 across 20 calls; edits seen"

    # ---------------------------------------------------------------- curriculum

    @check("the curriculum graph is structurally sound and places every problem")
    def _():
        from curriculum import graph
        from harness.loader import all_problems
        errors = graph.validate(set(all_problems()))
        assert not errors, "; ".join(errors[:4])
        subs = graph.all_subtopics()
        assert len(graph.CATEGORIES) == 4, f"{len(graph.CATEGORIES)} categories"
        return f"{len(subs)} subtopics, {sum(s.total for s in subs)} exercises"

    @check("the frontier only offers what exists, and never what is cleared")
    def _():
        from curriculum import graph
        payload = api("/api/curriculum")
        index = {s["id"]: s for c in payload["categories"] for s in c["subtopics"]}
        for sid in payload["frontier"]:
            assert index[sid]["available"], f"{sid} is on the frontier with nothing written"
            assert not index[sid]["cleared"], f"{sid} is cleared but still on the frontier"
            assert index[sid]["ready"], f"{sid} is on the frontier but not ready"
        return f"{len(payload['frontier'])} offered"

    @check("prerequisite advice is actionable: only written, uncleared subtopics")
    def _():
        payload = api("/api/curriculum")
        index = {s["id"]: s for c in payload["categories"] for s in c["subtopics"]}
        for sub in index.values():
            for m in sub["missing"]:
                assert m["written"], (
                    f"{sub['id']} advises {m['id']}, which has nothing written — "
                    "an instruction the learner cannot follow"
                )
                assert not index[m["id"]]["cleared"], f"{sub['id']} advises a cleared {m['id']}"
        return "all advice actionable"

    @check("an unwritten prerequisite never blocks readiness")
    def _():
        payload = api("/api/curriculum")
        index = {s["id"]: s for c in payload["categories"] for s in c["subtopics"]}
        # 4.5 file_system requires 2.9 Tree, which has nothing written. If an unwritten
        # prerequisite blocked, nothing in the bank would ever be startable.
        blocked = [
            s["id"] for s in index.values()
            if s["available"] and not s["ready"]
            and all(not index[m["id"]]["available"] for m in s["missing"])
        ]
        assert not blocked, f"blocked by prerequisites that do not exist: {blocked}"
        return "advisory only"

    @check("weak spots map a failing tag to a subtopic that teaches it")
    def _():
        from curriculum import graph
        payload = api("/api/curriculum")
        for entry in payload["weak"]:
            sub = graph.by_id(entry["subtopic"])
            assert sub is not None, f"weak spot points at unknown subtopic {entry['subtopic']}"
            assert entry["tag"] in sub.tags, f"{sub.id} does not teach {entry['tag']}"
        return f"{len(payload['weak'])} mapped" if payload["weak"] else "none yet (clean slate)"

    @check("the picker counts sessions once, not once per problem")
    def _():
        # Regression: attempts used to be `sum(... for s in all_sessions())` inside the
        # per-problem comprehension, re-reading every session file for every problem.
        import harness.session as sess
        calls = {"n": 0}
        original = sess.all_sessions

        def counting(*a, **k):
            calls["n"] += 1
            return original(*a, **k)

        import webui.server as server
        server.all_sessions = counting
        try:
            server._problem_cards()
        finally:
            server.all_sessions = original
        assert calls["n"] == 1, f"read sessions/ {calls['n']} times for one picker payload"
        return "one pass"

    # ---------------------------------------------------------------- runner invariants

    @check("a solution that mutates its argument cannot corrupt later cases")
    def _():
        # Op.args is built once at import and shared by every run in the process, so
        # without a per-call copy an in-place sort would poison the argument for every
        # subsequent case -- and permanently, inside the long-running ui server.
        from harness.expect import ANY
        from harness.model import Problem, Level, Method, case, op
        from harness.runner import run as run_cases
        import tempfile, pathlib as _p

        shared = [3, 1, 2]
        problem = Problem(
            key="_mutate_probe", title="probe", blurb="probe",
            class_name="Probe",
            levels=(Level(1, "only", (0, 0), 600),),
            methods=(Method(display="SEEN", signature="(self, xs: list) -> list", level=1),),
            cases=tuple(
                case(f"c{n}", 1, [op("SEEN", shared, ret=[3, 1, 2])], visible=True)
                for n in range(3)
            ),
        )
        src = "class Probe:\n    def seen(self, xs):\n        xs.sort()\n        return xs\n"
        with tempfile.TemporaryDirectory() as d:
            path = _p.Path(d) / "sol.py"
            path.write_text(src)
            result = run_cases(problem, path, max_level=1, op_timeout=5.0)
        outcomes = [c.outcome.value for lv in result.levels for c in lv.cases]
        # Every case sees [3,1,2] and returns it sorted, so all three fail identically.
        # Before the fix, case 0 failed and cases 1-2 "passed" on the mutated input.
        assert len(set(outcomes)) == 1, f"cases diverged, so state leaked between them: {outcomes}"
        assert shared == [3, 1, 2], f"the shared argument itself was mutated: {shared}"
        return f"3 cases, identical outcome {outcomes[0]}, argument intact"

    @check("a TypeError from the solution's own logic is not mislabelled")
    def _():
        # `"positional argument" in m or "argument" in m and name in m` parsed as
        # A or (B and C), so any TypeError mentioning "argument" became "signature
        # mismatch" regardless of origin.
        result = api("/api/run", {"code":
            "class FileHost:\n"
            "    def file_upload(self, name, size):\n"
            "        raise TypeError('bad argument supplied to my own helper')\n"})
        blob = json.dumps(result)
        assert "signature mismatch" not in blob, "own-logic TypeError reported as a signature mismatch"
        return "attributed correctly"

    @check("a problem that fails to import is reported, not silently dropped")
    def _():
        import subprocess
        probe = REPO / "problems" / "_probe_broken"
        probe.mkdir(parents=True, exist_ok=True)
        try:
            (probe / "__init__.py").write_text("")
            (probe / "problem.py").write_text("raise RuntimeError('deliberately broken')\n")
            # The loader skips directories starting with "_", so use a real-looking name.
            broken = REPO / "problems" / "zzprobe"
            broken.mkdir(parents=True, exist_ok=True)
            (broken / "__init__.py").write_text("")
            (broken / "problem.py").write_text("raise RuntimeError('deliberately broken')\n")
            out = subprocess.run(
                [PY, "-m", "harness", "list"], cwd=REPO, capture_output=True, text=True,
                env=dict(os.environ, NO_COLOR="1"),
            )
            assert "zzprobe" in out.stdout, f"broken problem not named:\n{out.stdout[-400:]}"
            assert "failed to load" in out.stdout, "no failure banner"
            assert out.returncode != 0, "exit code was 0 despite a broken problem"
            return "named and non-zero exit"
        finally:
            import shutil as _sh
            _sh.rmtree(probe, ignore_errors=True)
            _sh.rmtree(REPO / "problems" / "zzprobe", ignore_errors=True)
            for cache in REPO.rglob("__pycache__"):
                _sh.rmtree(cache, ignore_errors=True)

    # ---------------------------------------------------------------- worked solutions

    @check("a worked solution is refused while the session is live")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_system"})
        payload = api("/api/answer", expect_status=403)
        assert payload.get("locked") is True, f"answer was served live: {payload}"
        return "403 while running"

    @check("finishing opens the worked solution, sliced by level")
    def _():
        api("/api/finish", {})
        whole = api("/api/answer")
        assert whole["available"] is True, whole
        assert "class FileSystem" in whole["source"], "not the solution"
        one = api("/api/answer?level=1")
        assert one["level"] == 1, one
        assert len(one["source"]) < len(whole["source"]), "level 1 was not smaller"
        return f"{one['provenance']}, {len(one['source'])} vs {len(whole['source'])} chars"

    @check("a level-N solution never names an operation from a later level")
    def _():
        from harness.loader import get_problem
        import re as _re
        problem = get_problem("file_system")
        for level in range(1, problem.max_level + 1):
            payload = api(f"/api/answer?level={level}")
            if not payload.get("available"):
                continue
            leaks = [
                m.display for m in problem.methods
                if m.level > level and _re.search(rf"\b{m.display}\b", payload["source"])
            ]
            assert not leaks, f"level {level} solution leaks {leaks}"
        return "levels 1-4 clean"

    @check("a bad level is rejected rather than silently clamped")
    def _():
        api("/api/answer?level=9", expect_status=400)
        api("/api/answer?level=abc", expect_status=400)
        return "400 on both"

    # ---------------------------------------------------------------- exam mode

    @check("exam mode: a live run gives numbered tests and nothing else")
    def _():
        api("/api/abandon", {})
        state = api("/api/start", {"problem": "file_hosting", "blind": True})
        assert state["session"]["blind"] is True, "blind flag not recorded on the session"
        result = api("/api/run", {"code": "class FileHost:\n"
                                          "    def file_upload(self, name, size):\n"
                                          "        print('trace:', name, size)\n"})
        assert result["blind"] is True, "run payload did not report exam mode"
        cases = [c for lv in result["levels"] for c in lv["cases"]]
        assert cases, "no cases came back"
        ids = [c["id"] for c in cases]
        assert ids == [f"test {n}" for n in range(1, len(cases) + 1)], ids[:4]
        assert not any(c["tags"] for c in cases), "tags leaked in exam mode"
        assert not any(c["ops"] for c in cases), "operations leaked in exam mode"
        assert not any(c["doc"] for c in cases), "case docs leaked in exam mode"
        assert not any("shape" in c for c in cases), "operation shape leaked in exam mode"
        # Operation names are published by the statement, so they are fair game
        # there; what exam mode governs is the results. Case ids are fair game
        # nowhere -- the whole response must be free of them.
        results_blob = json.dumps(result["levels"])
        for token in ("FILE_UPLOAD", "FILE_GET", "FILE_COPY"):
            assert token not in results_blob, f"{token!r} leaked into the exam-mode results"
        assert "l1_" not in json.dumps(result), "a case id rode along in the response"
        assert any(c["stdout"] for c in cases), "the candidate's own print() was dropped"
        return f"{len(cases)} numbered tests, nothing named"

    @check("exam mode still reports the candidate's own exception")
    def _():
        result = api("/api/run", {"code": "class FileHost:\n"
                                          "    def file_upload(self, name, size):\n"
                                          "        raise ValueError('mine')\n"})
        detail = " ".join(
            (c["detail"] or "") + (c["traceback"] or "")
            for lv in result["levels"] for c in lv["cases"]
        )
        assert "ValueError" in detail, "a crash in the candidate's own code was withheld"
        return "traceback preserved"

    @check("finishing an exam-mode session opens everything")
    def _():
        api("/api/finish", {})
        result = api("/api/run", {"code": "class FileHost:\n    pass\n"})
        assert result["blind"] is False, "exam mode still binding after finish"
        ids = [c["id"] for lv in result["levels"] for c in lv["cases"]]
        assert any(i.startswith("l1_") for i in ids), f"case names still withheld: {ids[:3]}"
        assert api("/api/state")["session"]["blind"] is False, "state still reports exam mode"
        return "reveals on finish"

    @check("a session started without exam mode is unaffected")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_hosting"})
        result = api("/api/run", {"code": L1_GOOD})
        assert result["blind"] is False, "a plain session came back blind"
        visible = [c for lv in result["levels"] for c in lv["cases"] if c["visible"]]
        assert visible, "no visible cases in a plain run"
        return "unchanged"

    # ---------------------------------------------------------------- invariants under stress

    @check("a body with no code field is refused, not treated as empty")
    def _():
        api("/api/start", {"problem": "file_hosting"})
        api("/api/save", {"code": "class FileHost:\n    pass  # mine\n"})
        api("/api/save", {}, expect_status=400)
        api("/api/run", {}, expect_status=400)
        assert "# mine" in api("/api/state")["code"], "the solution file was truncated"
        return "400, file intact"

    @check("an expired session is over: no more unlocking, and the key opens")
    def _():
        import harness.session as sess
        state = api("/api/state")
        path = Path(REPO / "sessions" / f"{state['session']['id']}.json")
        data = json.loads(path.read_text())
        data["started_at"] -= (data["budget_minutes"] * 60 + 120)   # 2 minutes past time
        path.write_text(json.dumps(data))

        after = api("/api/state")
        assert after["session"]["finished"] is True, "an expired session still reports as live"
        run_result = api("/api/run", {"code": L1_GOOD})
        assert run_result.get("newly_unlocked") is None, "unlocked a level after time was up"
        assert api("/api/decisions").get("locked") is False, "the key stayed shut on a dead session"
        return "closed, no unlock, key open"

    @check("contract gating survives nested level markers")
    def _():
        from harness.contract import gated
        from harness.loader import get_problem
        problem = get_problem("file_hosting")
        source = (
            "public one\n"
            "<!-- level: 3 -->\n"
            "SECRET-A\n"
            "<!-- level: 1 -->\n"
            "nested public\n"
            "<!-- /level -->\n"
            "SECRET-B\n"
            "<!-- /level -->\n"
            "public two\n"
        )
        out = gated(problem, source, 1)
        assert "SECRET-A" not in out, "outer locked block leaked"
        assert "SECRET-B" not in out, "an inner close re-opened the outer locked block"
        assert "public one" in out and "public two" in out, "public text was dropped"
        return "nesting handled"

    @check("no locked concept survives in any problem's level-1 contract")
    def _():
        import re as _re
        from harness.contract import gated
        from harness.loader import all_problems
        words = {
            "file_hosting": ["ttl", "rollback", "search", "prefix"],
            "cloud_storage": ["capacity", "merge", "backup", "user"],
            "in_memory_db": ["ttl", "backup", "restore", "prefix"],
            "banking": ["cashback", "payment", "merge", "spender"],
            "file_system": ["permission", "symlink", "grant", "subtree"],
        }
        checked = 0
        for key, problem in all_problems().items():
            contract = problem.directory / "CONTRACT.md"
            # Only progressive problems gate a contract by level; the others disclose
            # everything at once and have no CONTRACT.md at all.
            if not contract.exists():
                continue
            text = gated(problem, contract.read_text(), 1)
            # Missing vocabulary must not silently pass, and must not KeyError either.
            assert key in words, f"{key} has no leak vocabulary in this check"
            hits = [w for w in words[key] if _re.search(rf"\b{w}\b", text, _re.I)]
            assert not hits, f"{key} level-1 contract leaks {hits}"
            checked += 1
        return f"{checked} gated contracts clean"

    @check("cloud_storage does not describe level 4 to a level-3 candidate")
    def _():
        import re as _re
        from harness.contract import gated
        from harness.loader import get_problem
        problem = get_problem("cloud_storage")
        text = gated(problem, (problem.directory / "CONTRACT.md").read_text(), 3)
        hits = [w for w in ("backup", "restore") if _re.search(rf"\b{w}\b", text, _re.I)]
        assert not hits, f"level-3 contract leaks {hits}"
        return "clean at level 3"

    @check("archiving twice in one second keeps both attempts")
    def _():
        from harness.scaffold import archive
        folder = REPO / "workspace/_archive_probe"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "solution.py"
        target.write_text("# ONE")
        first = archive(target)
        target.write_text("# TWO")
        second = archive(target)
        assert first != second, f"both attempts archived to {first}"
        assert first.read_text() == "# ONE" and second.read_text() == "# TWO"
        shutil.rmtree(folder, ignore_errors=True)
        return f"{first.name} and {second.name}"

    @check("markdown renders a signature containing an escaped pipe")
    def _():
        from webui.markdown import to_html
        html = to_html("| Op | Sig |\n| --- | --- |\n| `FILE_GET` | `(n: str) -> int \\| None` |")
        assert html.count("<td>") == 2, f"row split into {html.count('<td>')} cells"
        assert "int | None" in html, "the escaped pipe was mangled"
        return "2 cells"

    @check("an empty dict subclass is exact, but a real representation error is not")
    def _():
        from collections import Counter, OrderedDict, defaultdict
        from harness.expect import compare
        # Regression: the empty-value branch demanded an exact type match, so a solution
        # returning a Counter passed `Counter(["a"])` (the dict branch uses isinstance)
        # and failed only on empty input. Same code, two verdicts, for a reason nothing
        # to do with its logic.
        for actual in (Counter(), defaultdict(list), OrderedDict()):
            verdict = compare({}, actual)
            assert verdict.grade.value == "exact", (
                f"empty {type(actual).__name__} for {{}} graded {verdict.grade.value}"
            )
        assert compare({"a": 2}, Counter({"a": 2})).grade.value == "exact"
        # What the branch exists for must survive: these mean 'nothing' in different
        # shapes, and the real grader distinguishes them.
        for expected, actual, label in [
            (None, [], "list for None"), ([], None, "None for list"),
            ([], "", "str for list"), ([], (), "tuple for list"),
            ([], set(), "set for list"), ({}, [], "list for dict"),
        ]:
            verdict = compare(expected, actual)
            assert verdict.grade.value == "lenient", (
                f"{label} graded {verdict.grade.value}; it is a representation error"
            )
        return "subclasses exact, representation errors lenient"

    @check("markdown renders emphasis without eating asterisks that are not emphasis")
    def _():
        from webui.markdown import to_html
        cases = [
            ("A *rejected* value", "<em>rejected</em>", None),
            # Bold runs first, so a nested span arrives as a tag, not asterisks.
            ('It means *"the name is **falsy**."* So', "<em>", "*"),
            ("Maths: 3 * 4 * 5 stays", None, "<em>"),
            ("Use `*args` and `**kwargs` here", None, "<em>"),
            ("a*b*c inside a word", None, "<em>"),
            ("`*x*` in code is literal", "<code>*x*</code>", "<em>"),
        ]
        for source, wanted, unwanted in cases:
            html = to_html(source)
            if wanted:
                assert wanted in html, f"{source!r} -> {html!r}: missing {wanted}"
            if unwanted:
                assert unwanted not in html, f"{source!r} -> {html!r}: unwanted {unwanted}"
        return f"{len(cases)} cases"

    @check("markdown keeps a wrapped list item in one piece")
    def _():
        from webui.markdown import to_html
        html = to_html("* `OP` works. It returns the **deleted file's\n"
                       "  size** (as at level 1) and refunds it.\n"
                       "* next item")
        assert html.count("<li>") == 2, f"{html.count('<li>')} items, expected 2"
        assert "<p>" not in html, f"a continuation line became a paragraph: {html}"
        assert "<strong>deleted file&#x27;s size</strong>" in html, (
            f"a bold span across the line break was broken: {html}"
        )
        return "2 items, bold intact"

    @check("markdown renders ordered lists and horizontal rules")
    def _():
        from webui.markdown import to_html
        html = to_html("1. first\n2. second\n\n---\n\n- a\n- b")
        assert html.count("<ol>") == 1 and html.count("<ul>") == 1, html
        assert html.count("<li>") == 4, html
        assert "<hr>" in html and "<p>---</p>" not in html, html
        # A rule must not be read as a list item, nor a list as a rule.
        assert to_html("***").strip() == "<hr>", to_html("***")
        return "ol, ul and hr"

    @check("no document the reader sees renders raw markup")
    def _():
        import glob, re
        from webui.markdown import to_html
        # Every one of these is read by somebody: statements and contracts mid-attempt,
        # lessons beside a drill, DECISIONS and the teaching prose at debrief.
        files = (sorted(glob.glob(str(REPO / "curriculum/*/*/LESSON.md")))
                 + sorted(glob.glob(str(REPO / "problems/*/statement/*.md")))
                 + sorted(glob.glob(str(REPO / "problems/*/*.md"))))
        assert len(files) > 30, f"only {len(files)} documents found"
        bad = []
        for path in files:
            html = to_html(open(path).read())
            problems = []
            # Asterisks inside code are literal and correct; anywhere else they are
            # markup the reader was not supposed to see.
            outside = re.sub(r"<pre.*?</pre>|<code>.*?</code>", "", html, flags=re.S)
            # An asterisk the source deliberately escaped renders as an asterisk, and is
            # not a rendering failure -- `A\*` is how the algorithm's name is written.
            # Only count more strays than the source asked for.
            source = open(path).read()
            intended = source.count("\\*")
            if outside.count("*") > intended:
                problems.append("raw asterisk")
            if "<p>---</p>" in html:
                problems.append("literal ---")
            if re.search(r"<p>\d+\. ", html):
                problems.append("unrendered ordered list")
            if problems:
                bad.append(f"{path.split('/')[-2]}/{path.split('/')[-1]} ({', '.join(problems)})")
        assert not bad, "raw markup reaches the reader in: " + "; ".join(bad)
        return f"{len(files)} documents clean"

    # ---------------------------------------------------------------- security

    @check("static file route rejects path traversal")
    def _():
        for attack in ("/static/../../harness/cli.py", "/static/../server.py"):
            try:
                with urllib.request.urlopen(BASE + attack) as response:
                    body = response.read()
                assert b"import" not in body[:400], f"{attack} served source"
            except urllib.error.HTTPError as exc:
                assert exc.code == 404, f"{attack} returned {exc.code}"
        return "404 on traversal"

    @check("unknown routes 404 rather than crash")
    def _():
        try:
            urllib.request.urlopen(BASE + "/api/nope")
            raise AssertionError("no error for an unknown route")
        except urllib.error.HTTPError as exc:
            assert exc.code == 404, exc.code
        return "404"

    @check("a crash in your own code is reported, hidden case or not")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "cloud_storage"})
        result = api("/api/run", {"code": (
            "class CloudStorage:\n"
            "    def __init__(self):\n        self.files = {}\n"
            "    def add_file(self, name, size):\n"
            "        print(self.filetests)   # no such attribute\n"
            "        return True\n"
            "    def get_file_size(self, name): return self.files.get(name)\n"
            "    def delete_file(self, name): return self.files.pop(name, None)\n"
        )})
        crashed = [c for lv in result["levels"] for c in lv["cases"] if c["outcome"] == "error"]
        assert crashed, "the AttributeError produced no error outcome"
        hidden = [c for c in crashed if not c["visible"]]
        assert hidden, "no hidden case crashed, so this proves nothing"
        for case in hidden:
            assert "AttributeError" in case["detail"], \
                f"{case['id']} says only {case['detail']!r} — no exception type"
            assert "filetests" in case["detail"], "the message was withheld"
            assert case["traceback"], f"{case['id']} carried no line number"
            assert "solution.py" in case["traceback"], "traceback does not point at their file"
            # Still no leak: a crash must not reveal the case's expectations.
            assert case["ops"] == [], "a hidden case exposed its operations"
        return f"{len(hidden)} hidden crashes reported with type, message and line"

    @check("completions come from the buffer, with types and signatures")
    def _():
        code = (
            "class FileHost:\n"
            "    def __init__(self):\n"
            "        self.files = {}\n"
            "        self.names = []\n"
            "    def helper(self, key: str) -> int:\n"
            '        """Find something."""\n'
            "        return 0\n"
            "    def file_upload(self, file_name, size):\n"
            "        self.\n"
        )
        r = api("/api/complete", {"code": code, "line": 9, "col": 13})
        by_name = {c["name"]: c for c in r["completions"]}
        assert "files" in by_name and by_name["files"]["detail"] == "dict", by_name.get("files")
        assert "names" in by_name and by_name["names"]["detail"] == "list", by_name.get("names")
        assert "helper" in by_name, "own method not offered"
        assert "key: str" in by_name["helper"]["detail"], by_name["helper"]["detail"]
        assert by_name["helper"]["doc"] == "Find something.", by_name["helper"]["doc"]
        return f"{len(r['completions'])} completions with types and signatures"

    @check("member completions respect the inferred type")
    def _():
        code = ("class FileHost:\n    def __init__(self):\n        self.files = {}\n"
                "        self.names = []\n    def x(self):\n        self.files.\n")
        names = [c["name"] for c in api("/api/complete",
                                        {"code": code, "line": 6, "col": 19})["completions"]]
        assert "get" in names and "items" in names, names[:10]
        assert "append" not in names, "list methods offered on a dict"
        code2 = code.replace("self.files.", "self.names.")
        names2 = [c["name"] for c in api("/api/complete",
                                         {"code": code2, "line": 6, "col": 19})["completions"]]
        assert "append" in names2 and "get" not in names2, names2[:10]
        return "dict and list kept apart"

    @check("signature help tracks the active argument")
    def _():
        code = ("class FileHost:\n    def __init__(self):\n        pass\n"
                "    def file_upload(self, file_name, size):\n        pass\n"
                "    def go(self):\n        self.file_upload('a', \n")
        sig = api("/api/complete", {"code": code, "line": 7, "col": 30})["signature"]
        assert sig, "no signature help inside a call"
        assert "file_name" in sig["label"] and "size" in sig["label"], sig["label"]
        assert sig["active"] == 1, f"active argument was {sig['active']}, expected 1"
        return f"{sig['label']} active={sig['active']}"

    @check("completions never include a locked level's operations")
    def _():
        from harness.loader import all_problems
        code = ("class FileHost:\n    def __init__(self):\n        self.files = {}\n"
                "    def file_upload(self, n, s):\n        self.\n")
        names = {c["name"] for c in api("/api/complete",
                                        {"code": code, "line": 5, "col": 13})["completions"]}
        locked = set()
        for problem in all_problems().values():
            locked |= {m.resolved_name() for m in problem.methods if m.level > 1}
        overlap = names & locked
        assert not overlap, f"completions offered locked operations: {sorted(overlap)}"
        return f"{len(names)} completions, none of {len(locked)} locked operations"

    @check("the analyser never executes the buffer")
    def _():
        marker = REPO / "sessions" / "SHOULD_NOT_EXIST"
        code = (f"import pathlib\npathlib.Path({str(marker)!r}).write_text('boom')\n"
                "class FileHost:\n    def __init__(self):\n        self.\n")
        api("/api/complete", {"code": code, "line": 5, "col": 13})
        api("/api/check", {"code": code})
        assert not marker.exists(), "the analyser executed the candidate's module"
        return "parsed, not run"

    @check("the syntax checker reports errors without saving or running")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_hosting"})
        good = "class FileHost:\n    def __init__(self):\n        self.f = {}\n"
        api("/api/save", {"code": good})
        assert api("/api/check", {"code": good})["errors"] == [], "clean code reported errors"

        bad = api("/api/check", {"code": "class FileHost:\n    def broken(self)\n        pass\n"})
        assert len(bad["errors"]) == 1, bad
        assert bad["errors"][0]["line"] == 2, bad["errors"][0]
        assert "Error" in bad["errors"][0]["msg"], bad["errors"][0]

        # It must not have touched the workspace file, and must not execute anything.
        assert api("/api/state")["code"] == good, "the checker overwrote the saved file"
        boom = api("/api/check", {"code": "raise SystemExit('should never run')\n"})
        assert boom["errors"] == [], "the checker executed the module instead of compiling it"
        return "compile-only, file untouched"

    @check("print() output reaches the candidate")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_hosting"})
        result = api("/api/run", {"code": (
            "class FileHost:\n"
            "    def __init__(self):\n"
            "        self.f = {}\n"
            "        print('MARKER init', vars(self))\n"
            "    def file_upload(self, file_name, size):\n"
            "        print('MARKER upload', file_name, size)\n"
            "        self.f[file_name] = size\n"
        )})
        with_output = [c for lv in result["levels"] for c in lv["cases"] if c.get("stdout")]
        assert with_output, "no case carried the candidate's print() output"
        assert any("MARKER init" in c["stdout"] for c in with_output), "print() was swallowed"
        # Hidden cases carry it too: it is the candidate's own instrumentation.
        hidden = [c for c in with_output if not c["visible"]]
        assert hidden, "hidden cases dropped the candidate's own output"
        return f"{len(with_output)} cases carry output"

    @check("the page carries a build id that matches the server's")
    def _():
        import urllib.request as _u
        page = _u.urlopen(BASE + "/").read().decode()
        assert "__PFS_BUILD__" not in page.split("const PAGE_BUILD")[1][:60], \
            "the build placeholder was served unsubstituted"
        build = api("/api/state")["build"]
        assert build and build in page, "page build id does not match /api/state"
        return build

    @check("editing the page changes the build id, so an old tab can tell")
    def _():
        before = api("/api/state")["build"]
        page_file = REPO / "webui" / "index.html"
        original = page_file.read_bytes()
        try:
            page_file.write_bytes(original + b"\n<!-- touched -->\n")
            after = api("/api/state")["build"]
            assert after != before, "an edited page kept the same build id"
        finally:
            page_file.write_bytes(original)
        assert api("/api/state")["build"] == before, "build id did not settle back"
        return f"{before} -> changed -> {before}"

    @check("a server running stale code says so instead of misbehaving quietly")
    def _():
        assert api("/api/state").get("stale_server") is False, "reported stale on a fresh boot"
        watched = REPO / "harness" / "render.py"
        original = watched.read_bytes()
        try:
            watched.write_bytes(original + b"\n# touched by the test suite\n")
            assert api("/api/state").get("stale_server") is True, \
                "edited a module the server imported and it did not notice"
        finally:
            watched.write_bytes(original)
        assert api("/api/state").get("stale_server") is False, "stayed stale after the revert"
        return "detected and cleared"

    # ---------------------------------------------------------------- CLI parity

    def cli(*args):
        return subprocess.run([PY, "-m", "harness", *args], cwd=REPO,
                              capture_output=True, text=True, env=dict(os.environ, NO_COLOR="1"))

    @check("CLI review-only views refuse during a live attempt")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_hosting"})
        blocked = {
            "spec --all": cli("spec", "--all"),
            "contract --all": cli("contract", "--all"),
            "test --reveal": cli("test", "--reveal"),
            "test --all": cli("test", "--all"),
            "stubs --level 4": cli("stubs", "--level", "4"),
            "test --level 4": cli("test", "--level", "4"),
        }
        leaked = []
        for label, result in blocked.items():
            combined = result.stdout + result.stderr
            if result.returncode == 0:
                leaked.append(f"{label} succeeded")
            elif "ROLLBACK" in combined or "FILE_SEARCH" in combined:
                leaked.append(f"{label} printed a locked operation")
        assert not leaked, "; ".join(leaked)
        return f"{len(blocked)} views refused"

    @check("CLI review-only views open again once the attempt is over")
    def _():
        cli("finish")
        result = cli("spec", "--all")
        assert result.returncode == 0, result.stderr[:120]
        assert "ROLLBACK" in result.stdout, "level 4 still hidden after finishing"
        return "open after finish"

    @check("testing another problem does not touch the live session")
    def _():
        api("/api/abandon", {})
        api("/api/start", {"problem": "file_hosting"})
        before = api("/api/state")["session"]
        (REPO / "workspace/cloud_storage").mkdir(parents=True, exist_ok=True)
        (REPO / "workspace/cloud_storage/solution.py").write_text(
            "class CloudStorage:\n"
            "    def __init__(self): self.f = {}\n"
            "    def add_file(self, name, size):\n"
            "        if name in self.f: return False\n"
            "        self.f[name] = size; return True\n"
            "    def get_file_size(self, name): return self.f.get(name)\n"
            "    def delete_file(self, name): return self.f.pop(name, None)\n"
        )
        cli("test", "cloud_storage")
        after = api("/api/state")["session"]
        assert after["unlocked_level"] == before["unlocked_level"], \
            "another problem's run unlocked a level in this session"
        runs = [e for e in json.loads(json.dumps(
            [json.loads(l) for l in (REPO / "sessions" / f"{before['id']}.events.jsonl").read_text().splitlines() if l.strip()]
        )) if e.get("kind") == "run"]
        assert not runs, f"another problem's run was logged into this session ({len(runs)} runs)"
        return "session untouched"

    @check("a malformed request body is an error, not a crash")
    def _():
        request = urllib.request.Request(
            BASE + "/api/run", data=b"not json", headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(request)
        except urllib.error.HTTPError as exc:
            assert exc.code == 500, exc.code
            assert b"error" in exc.read(), "no error message returned"
        assert api("/api/state") is not None, "server died on bad input"
        return "handled, server alive"


if __name__ == "__main__":
    sys.exit(main())
