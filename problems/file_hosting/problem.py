"""In-memory file hosting service.

This is the canonical CodeSignal Industry Coding Framework sample question. The
level statements reproduce the published wording; everything the wording leaves
open is recorded in DECISIONS.md and demonstrated by a visible sample case.
"""

from __future__ import annotations

from harness.model import Level, Method, Problem

from .tests import ALL_CASES

METHODS = (
    Method(
        display="FILE_UPLOAD",
        signature="(self, file_name: str, size: int) -> None",
        level=1,
        doc="Upload a file. Raises if a file with that name already exists.",
    ),
    Method(
        display="FILE_GET",
        signature="(self, file_name: str) -> int | None",
        level=1,
        doc="Return the size of the file, or None if it does not exist.",
    ),
    Method(
        display="FILE_COPY",
        signature="(self, source: str, dest: str) -> None",
        level=1,
        doc="Copy source to dest, overwriting dest. Raises if source is missing.",
    ),
    Method(
        display="FILE_SEARCH",
        signature="(self, prefix: str) -> list[str]",
        level=2,
        doc=(
            "Return the names of at most 10 files whose name starts with prefix, "
            "largest first, ties broken by name ascending."
        ),
    ),
    Method(
        display="FILE_UPLOAD_AT",
        signature=(
            "(self, timestamp: int, file_name: str, file_size: int, "
            "ttl: int | None = None) -> None"
        ),
        level=3,
        doc="Upload at a timestamp. The file lives for ttl seconds; None means forever.",
    ),
    Method(
        display="FILE_GET_AT",
        signature="(self, timestamp: int, file_name: str) -> int | None",
        level=3,
        doc="Size of the file as of timestamp, or None if it is not alive then.",
    ),
    Method(
        display="FILE_COPY_AT",
        signature="(self, timestamp: int, file_from: str, file_to: str) -> None",
        level=3,
        doc="Copy as of timestamp. Raises if file_from is not alive then.",
    ),
    Method(
        display="FILE_SEARCH_AT",
        signature="(self, timestamp: int, prefix: str) -> list[str]",
        level=3,
        doc="Like FILE_SEARCH, restricted to files alive at timestamp.",
    ),
    Method(
        display="ROLLBACK",
        signature="(self, timestamp: int) -> None",
        level=4,
        doc="Restore the storage to the state it had at timestamp.",
    ),
)

LEVELS = (
    Level(1, "Initial Design & Basic Functions", (10, 15), 100, "dict of name -> size"),
    Level(2, "Data Structures & Data Processing", (15, 20), 140, "sorting with a compound key"),
    Level(3, "Refactoring & Encapsulation", (20, 30), 180, "time and expiry"),
    Level(4, "Extending Design & Functionality", (20, 25), 180, "history and restore"),
)

TAG_GLOSSARY = {
    "basics": "core create/read/copy behaviour",
    "errors": "operations that must raise",
    "atomicity": "a rejected operation must leave no trace",
    "overwrite": "destination-overwriting semantics",
    "edge-values": "zero, empty, identical, case-sensitive inputs",
    "paths": "names that look like directories but are not",
    "search": "prefix search",
    "ordering": "size-descending order",
    "tie-break": "name-ascending order within equal sizes",
    "top-n": "the ten-result cap",
    "ttl": "lifetimes and expiry",
    "boundaries": "the exact instant a file appears or disappears",
    "time-travel": "queries at timestamps before an upload",
    "copy-semantics": "what a copy inherits from its source",
    "refactor": "level-1/2 methods re-expressed through the timestamped ones",
    "regression": "earlier levels still working after a refactor",
    "rollback": "restoring a previous state",
    "history": "keeping enough past to roll back more than once",
}

PROBLEM = Problem(
    key="file_hosting",
    title="In-Memory File Hosting Service",
    blurb=(
        "Implement a simplified file hosting service: upload, read and copy files; "
        "then search by prefix; then make every operation time-aware with expiry; "
        "then support rolling the whole store back to an earlier instant."
    ),
    class_name="FileHost",
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="CodeSignal ICF published sample (wording reproduced verbatim)",
)
