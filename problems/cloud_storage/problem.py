"""Cloud file storage with users, capacity and per-user backups.

Reported at Ramp, Coinbase and others. The level-3 turn is ownership rather than
time, which makes it the useful counterweight to the two TTL problems in this bank:
the same four-level skeleton, a completely different refactor.
"""

from __future__ import annotations

from harness.model import Level, Method, Problem

from .tests import ALL_CASES

METHODS = (
    Method(
        display="ADD_FILE",
        signature="(self, name: str, size: int) -> bool",
        level=1,
        doc="Add a file. False if a file with that name already exists.",
    ),
    Method(
        display="GET_FILE_SIZE",
        signature="(self, name: str) -> int | None",
        level=1,
        doc="Return the size of the file, or None if it does not exist.",
    ),
    Method(
        display="DELETE_FILE",
        signature="(self, name: str) -> int | None",
        level=1,
        doc="Delete the file and return its size, or None if it does not exist.",
    ),
    Method(
        display="GET_N_LARGEST",
        signature="(self, prefix: str, n: int) -> list[str]",
        level=2,
        doc=(
            "Names of the n largest files starting with prefix, largest first, "
            "ties broken by name ascending."
        ),
    ),
    Method(
        display="ADD_USER",
        signature="(self, user_id: str, capacity: int) -> bool",
        level=3,
        doc="Create a user with a storage capacity. False if the user already exists.",
    ),
    Method(
        display="ADD_FILE_BY",
        signature="(self, user_id: str, name: str, size: int) -> int | None",
        level=3,
        doc=(
            "Add a file owned by the user. Return the user's remaining capacity, "
            "or None if the user is unknown, the name is taken, or it will not fit."
        ),
    ),
    Method(
        display="MERGE_USER",
        signature="(self, user_id_1: str, user_id_2: str) -> int | None",
        level=3,
        doc=(
            "Move user 2's files and capacity into user 1 and delete user 2. "
            "Return user 1's remaining capacity, or None if the merge is not possible."
        ),
    ),
    Method(
        display="BACKUP_USER",
        signature="(self, user_id: str) -> int | None",
        level=4,
        doc=(
            "Save the user's current set of files. Return how many were saved, "
            "or None if the user is unknown."
        ),
    ),
    Method(
        display="RESTORE_USER",
        signature="(self, user_id: str) -> int | None",
        level=4,
        doc=(
            "Replace the user's files with their backup. Return how many were "
            "restored, or None if the user is unknown."
        ),
    ),
)

LEVELS = (
    Level(1, "Initial Design & Basic Functions", (10, 15), 100, "dict of name -> size"),
    Level(2, "Data Structures & Data Processing", (15, 20), 140, "ranked query"),
    Level(3, "Refactoring & Encapsulation", (20, 30), 180, "ownership and capacity"),
    Level(4, "Extending Design & Functionality", (20, 25), 180, "snapshots with collisions"),
)

TAG_GLOSSARY = {
    "basics": "core add/get/delete behaviour",
    "rejection": "operations that fail and must change nothing",
    "edge-values": "zero sizes, zero capacity, empty prefixes, case sensitivity",
    "paths": "names that look like directories but are not",
    "query": "the n-largest-by-prefix query",
    "ordering": "size-descending order",
    "tie-break": "name-ascending order within equal sizes",
    "top-n": "the n-result cap",
    "users": "ownership and the user registry",
    "capacity": "capacity accounting, including refunds and failed adds",
    "merge": "folding one user into another",
    "backup": "taking a per-user snapshot",
    "restore": "putting a snapshot back",
    "collision": "restoring a name another user has since taken",
    "aliasing": "snapshots that share structure with live state",
    "regression": "earlier levels still working after a refactor",
}

PROBLEM = Problem(
    key="cloud_storage",
    title="Cloud File Storage",
    blurb=(
        "Implement a simplified cloud storage service: add, size and delete files; "
        "then query the largest files under a prefix; then introduce users with "
        "storage capacity and the ability to merge them; then per-user backup and "
        "restore."
    ),
    class_name="CloudStorage",
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Reconstructed from widely reported CodeSignal ICF variant; see docs/PROBLEM_BRIEFS.md",
)
