#!/usr/bin/env python3
"""Enforce the disclosure firewall while a session is live.

CLAUDE.md and .claude/agents/icf-coach.md both state the rule; until this hook
existed it was enforced only by a model having read them and choosing to obey.
A subagent spawned without project context, a compaction that drops the rule, or
a stray `grep -r` defeated it silently -- and a leak nobody notices is the worst
kind, because the score still looks real.

The `./pfs` CLI is the sanctioned disclosure channel and already gates itself:
`spec` and `contract` only ever describe unlocked levels (cli.py:279, :308) and
refuse `--all` mid-attempt. Raw file reads bypass that gate entirely, so it is
the raw channel this blocks -- never the CLI. `./pfs test` reads tests.py in a
subprocess and its command string names no blocked path, so it passes untouched.

Contract: exit 0 allows, exit 2 blocks with the reason on stderr.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SESSIONS = ROOT / "sessions"

# Everything the CLI would otherwise gate by unlocked level, plus the answer key.
BLOCKED_DIRS = ("problems", "solutions")
ALLOWED = {"solutions/README.md"}

# Bash gets substring matching -- best effort, but it catches cat/sed/grep/less.
WRITE_ISH = re.compile(r">|\btee\b|\bsed\s+-i|\bcp\b|\bmv\b|\brm\b|\bdd\b")


def live_session() -> bool:
    """True only if a session exists and has not finished.

    `./pfs finish` does not clear the pointer -- session.active() is
    `finished_at is None` (session.py:69) -- so checking the pointer alone would
    wrongly block forever after the first attempt.
    """
    pointer = SESSIONS / "active.json"
    if not pointer.exists():
        return False
    session_id = json.loads(pointer.read_text()).get("id", "")
    path = SESSIONS / f"{session_id}.json"
    if not path.exists():
        return False
    return json.loads(path.read_text()).get("finished_at") is None


def relative(raw: str) -> str | None:
    """Repo-relative posix path, or None if it falls outside the repo."""
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    try:
        return candidate.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def blocked(rel: str | None) -> bool:
    if rel is None or rel in ALLOWED:
        return False
    return rel.split("/")[0] in BLOCKED_DIRS


def verdict(tool: str, data: dict) -> str | None:
    """The reason this call must be refused, or None to allow it."""
    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        rel = relative(data.get("file_path") or data.get("notebook_path") or "")
        if blocked(rel):
            return f"`{rel}` is sealed while the clock is running"
        # Their own solution file is theirs to write, not mine.
        if tool != "Read" and rel and rel.startswith("workspace/"):
            return "editing your solution file would make the measurement meaningless"

    elif tool in ("Grep", "Glob"):
        for key in ("path", "glob", "pattern"):
            value = data.get(key)
            if not isinstance(value, str):
                continue
            if blocked(relative(value)) or any(
                value.startswith(d + "/") or value == d for d in BLOCKED_DIRS
            ):
                return f"searching `{value}` would reach sealed files"

    elif tool == "Bash":
        command = data.get("command", "")
        for directory in BLOCKED_DIRS:
            if re.search(rf"(^|[\s'\"=/]){directory}/", command):
                return f"that command reaches into `{directory}/`, sealed while the clock is running"
        if "workspace/" in command and WRITE_ISH.search(command):
            return "editing your solution file would make the measurement meaningless"

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not live_session():
            return 0
    except Exception:
        # A broken guard that blocks every call is worse than none: outside a live
        # session there is nothing to protect, and CLAUDE.md still applies.
        return 0

    try:
        reason = verdict(payload.get("tool_name", ""), payload.get("tool_input") or {})
    except Exception:
        # Here we know a session IS live, so an unreadable call fails closed.
        reason = "could not prove this call is safe mid-attempt"

    if reason is None:
        return 0

    print(
        f"Blocked: {reason}.\n"
        "Not while the clock is running -- that is the whole measurement. "
        "Log it with `./pfs dispute` if you think a case is wrong, and keep going. "
        "Everything opens up the moment you run `./pfs finish`.\n"
        "Still allowed: `./pfs spec`, `./pfs contract`, `./pfs test`, and any Python "
        "syntax or standard-library reference.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
