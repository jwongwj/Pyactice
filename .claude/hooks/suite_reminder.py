#!/usr/bin/env python3
"""Remind that harness/ and webui/ edits owe a test run.

CLAUDE.md makes tests/run_all.sh mandatory after touching either tree, and notes
that every UI bug this rig has shipped was a geometry bug -- a control outside the
viewport, a pane collapsed to zero height -- which no presence-only test catches.
That is exactly the run that gets skipped, so it is worth saying out loud.

A reminder, never a block: run_all.sh launches real Chrome and moves sessions/ and
workspace/ aside, which is too heavy to fire on a one-line edit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WATCHED = ("harness", "webui")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        raw = (payload.get("tool_input") or {}).get("file_path", "")
        if not raw:
            return 0
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT / path
        rel = path.resolve().relative_to(ROOT).as_posix()
    except Exception:
        return 0

    top = rel.split("/")[0]
    if top not in WATCHED:
        return 0

    note = f"Touched {top}/ -- run tests/run_all.sh before calling this done."
    if top == "webui":
        note += " The browser layer asserts on geometry; presence-only checks miss it."

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": note,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
