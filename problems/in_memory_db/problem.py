"""In-memory key-value database with TTL and backups.

The second most widely reported CodeSignal ICF problem after the file hosting
service. Two things about it differ from file_hosting on purpose, because both are
reported that way and because a bank of near-identical problems teaches recall:
the timestamp argument comes last, and level 4 restores explicit snapshots rather
than replaying history.
"""

from __future__ import annotations

from harness.model import Level, Method, Problem

from .tests import ALL_CASES

METHODS = (
    Method(
        display="SET",
        signature="(self, key: str, field: str, value: str) -> None",
        level=1,
        doc="Insert or update a field/value pair on the record at key.",
    ),
    Method(
        display="GET",
        signature="(self, key: str, field: str) -> str | None",
        level=1,
        doc="Return the value of the field, or None if it is not set.",
    ),
    Method(
        display="DELETE",
        signature="(self, key: str, field: str) -> bool",
        level=1,
        doc="Remove the field. True if something was removed, False otherwise.",
    ),
    Method(
        display="SCAN",
        signature="(self, key: str) -> list[str]",
        level=2,
        doc='Return ["<field>(<value>)", ...] for the record, ordered by field name.',
    ),
    Method(
        display="SCAN_BY_PREFIX",
        signature="(self, key: str, prefix: str) -> list[str]",
        level=2,
        doc="Like SCAN, restricted to fields whose name starts with prefix.",
    ),
    Method(
        display="SET_AT",
        signature="(self, key: str, field: str, value: str, timestamp: int) -> None",
        level=3,
        doc="SET as of a timestamp. The field never expires.",
    ),
    Method(
        display="SET_AT_WITH_TTL",
        signature=(
            "(self, key: str, field: str, value: str, timestamp: int, ttl: int) -> None"
        ),
        level=3,
        doc="SET as of a timestamp; the field lives for ttl seconds.",
    ),
    Method(
        display="DELETE_AT",
        signature="(self, key: str, field: str, timestamp: int) -> bool",
        level=3,
        doc="DELETE as of a timestamp. False if the field was absent or expired.",
    ),
    Method(
        display="GET_AT",
        signature="(self, key: str, field: str, timestamp: int) -> str | None",
        level=3,
        doc="GET as of a timestamp.",
    ),
    Method(
        display="SCAN_AT",
        signature="(self, key: str, timestamp: int) -> list[str]",
        level=3,
        doc="SCAN as of a timestamp, excluding expired fields.",
    ),
    Method(
        display="SCAN_BY_PREFIX_AT",
        signature="(self, key: str, prefix: str, timestamp: int) -> list[str]",
        level=3,
        doc="SCAN_BY_PREFIX as of a timestamp, excluding expired fields.",
    ),
    Method(
        display="BACKUP",
        signature="(self, timestamp: int) -> int",
        level=4,
        doc=(
            "Save the database state, including every field's remaining lifetime. "
            "Return the number of records that are neither empty nor expired."
        ),
    ),
    Method(
        display="RESTORE",
        signature="(self, timestamp: int, timestamp_to_restore: int) -> None",
        level=4,
        doc=(
            "Restore from the most recent backup taken at or before "
            "timestamp_to_restore. Lifetimes are recalculated."
        ),
    ),
)

LEVELS = (
    Level(1, "Initial Design & Basic Functions", (10, 15), 100, "nested dict"),
    Level(2, "Data Structures & Data Processing", (15, 20), 140, "sorted projection"),
    Level(3, "Refactoring & Encapsulation", (20, 30), 180, "time and expiry"),
    Level(4, "Extending Design & Functionality", (20, 25), 180, "snapshots and re-anchored ttls"),
)

TAG_GLOSSARY = {
    "basics": "core set/get/delete behaviour",
    "overwrite": "setting a field that already exists",
    "edge-values": "empty strings, zero ttl, missing keys, case sensitivity",
    "scan": "projecting a record's fields",
    "ordering": "field-name ordering",
    "tie-break": "lexicographic rather than numeric ordering",
    "ttl": "lifetimes and expiry",
    "boundaries": "the exact instant a field expires",
    "refactor": "level-1/2 calls re-expressed through the timestamped ones",
    "regression": "earlier levels still working after a refactor",
    "backup": "taking a snapshot and counting what it holds",
    "restore": "putting a snapshot back",
    "history": "keeping every backup, not just the last",
    "aliasing": "snapshots that share structure with live state",
}

PROBLEM = Problem(
    key="in_memory_db",
    title="In-Memory Key-Value Database",
    blurb=(
        "Implement a simplified in-memory database of records, each holding "
        "field/value pairs: set, read and delete fields; then project a record with "
        "filters; then make every operation time-aware with expiry; then support "
        "backups and restoring one."
    ),
    class_name="InMemoryDB",
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Reconstructed from widely reported CodeSignal ICF variant; see docs/PROBLEM_BRIEFS.md",
)
