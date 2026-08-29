"""Session state: the 90-minute clock, level unlocking, and the event log.

The event log is the whole point of the practice loop. A run that fails is not
interesting; *twelve* runs that fail the same case for nine minutes is. Everything
`pfs report` and `pfs stats` say is derived from these events, so the runner writes
one append-only JSON line per meaningful moment and never mutates history.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .loader import ROOT

SESSIONS_DIR = ROOT / "sessions"
WORKSPACE_DIR = ROOT / "workspace"
ACTIVE_POINTER = SESSIONS_DIR / "active.json"

DEFAULT_MINUTES = 90


@dataclass
class Session:
    id: str
    problem: str
    solution_path: str
    started_at: float
    # None means untimed. A drill is sixty seconds of work; a clock on it is noise,
    # and `--minutes 0` could not express it because 0 makes `expired` true at once.
    budget_minutes: int | None = DEFAULT_MINUTES
    unlocked_level: int = 1
    max_level: int = 4
    finished_at: float | None = None
    level_cleared_at: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    # Exam mode: while this session is live, failures report an opaque test number
    # and the candidate's own stdout, and nothing else. The default-off feedback in
    # this rig (case names, tags, operation shapes) is a crutch the real assessment
    # does not give you, so practising with it trains the wrong debugging reflex.
    blind: bool = False

    # ---- derived -------------------------------------------------------

    @property
    def path(self) -> Path:
        return SESSIONS_DIR / f"{self.id}.json"

    @property
    def events_path(self) -> Path:
        return SESSIONS_DIR / f"{self.id}.events.jsonl"

    @property
    def elapsed_s(self) -> float:
        end = self.finished_at if self.finished_at else time.time()
        return end - self.started_at

    @property
    def timed(self) -> bool:
        return self.budget_minutes is not None

    @property
    def remaining_s(self) -> float:
        if self.budget_minutes is None:
            return float("inf")
        return self.budget_minutes * 60 - self.elapsed_s

    @property
    def expired(self) -> bool:
        if self.budget_minutes is None:
            return False
        return self.remaining_s <= 0

    @property
    def active(self) -> bool:
        return self.finished_at is None

    # ---- persistence ---------------------------------------------------

    def save(self) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(self), indent=2) + "\n")

    def log(self, kind: str, **payload: Any) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        record = {
            "t": round(time.time(), 3),
            "elapsed_s": round(self.elapsed_s, 3),
            "kind": kind,
            **payload,
        }
        with self.events_path.open("a") as handle:
            handle.write(json.dumps(record) + "\n")

    def events(self) -> Iterator[dict]:
        if not self.events_path.exists():
            return iter(())
        lines = self.events_path.read_text().splitlines()
        return (json.loads(line) for line in lines if line.strip())

    def make_active(self) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        ACTIVE_POINTER.write_text(json.dumps({"id": self.id}) + "\n")


def _load(path: Path) -> Session:
    data = json.loads(path.read_text())
    return Session(**data)


def new_session(
    problem_key: str,
    solution_path: Path,
    *,
    minutes: int | None = DEFAULT_MINUTES,
    max_level: int = 4,
    start_level: int = 1,
    blind: bool = False,
) -> Session:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    # Two starts in the same second would otherwise share an id, so the second
    # would overwrite the first's record and interleave both event logs.
    session_id = f"{stamp}-{problem_key}"
    suffix = 2
    while (SESSIONS_DIR / f"{session_id}.json").exists():
        session_id = f"{stamp}-{suffix}-{problem_key}"
        suffix += 1
    session = Session(
        id=session_id,
        problem=problem_key,
        solution_path=str(solution_path),
        started_at=time.time(),
        budget_minutes=minutes,
        unlocked_level=start_level,
        max_level=max_level,
        blind=blind,
    )
    session.save()
    session.make_active()
    session.log(
        "session_start",
        problem=problem_key,
        minutes=minutes,
        start_level=start_level,
        blind=blind,
    )
    return session


def active_session() -> Session | None:
    override = os.environ.get("PFS_SESSION")
    if override:
        path = SESSIONS_DIR / f"{override}.json"
        return _load(path) if path.exists() else None
    if not ACTIVE_POINTER.exists():
        return None
    try:
        pointer = json.loads(ACTIVE_POINTER.read_text())
    except json.JSONDecodeError:
        return None
    path = SESSIONS_DIR / f"{pointer.get('id', '')}.json"
    return _load(path) if path.exists() else None


def all_sessions() -> list[Session]:
    if not SESSIONS_DIR.exists():
        return []
    sessions = []
    for path in sorted(SESSIONS_DIR.glob("*.json")):
        if path.name == "active.json":
            continue
        try:
            sessions.append(_load(path))
        except (json.JSONDecodeError, TypeError):
            continue
    return sessions


def workspace_for(problem_key: str) -> Path:
    return WORKSPACE_DIR / problem_key / "solution.py"


def format_clock(seconds: float) -> str:
    if seconds == float("inf"):
        return "untimed"
    sign = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    return f"{sign}{seconds // 60:02d}:{seconds % 60:02d}"
