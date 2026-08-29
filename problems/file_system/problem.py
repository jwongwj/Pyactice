"""A hierarchical file system: the design-trap problem in this bank.

Every other filesystem problem here is a flat `name -> value` map, which means a
candidate cannot make a wrong level-1 design decision. This one can be done at
level 1 with a flat dict of paths -- and level 2 (subtree removal, moves that must
refuse to move a directory inside itself) then makes that choice expensive, and
level 4 (symlinks resolved mid-path) makes it untenable. That is the skill the
real progressive format is testing and no other problem here exercises it.
"""

from __future__ import annotations

from harness.model import Level, Method, Problem

from .tests import ALL_CASES

METHODS = (
    Method(
        display="MKDIR",
        signature="(self, path: str) -> bool",
        level=1,
        doc="Create a directory. The parent must already exist.",
    ),
    Method(
        display="CREATE_FILE",
        signature="(self, path: str, content: str) -> bool",
        level=1,
        doc="Create a file with the given content. The parent must already exist.",
    ),
    Method(
        display="READ_FILE",
        signature="(self, path: str) -> str | None",
        level=1,
        doc="Return the file's content, or None if there is no file there.",
    ),
    Method(
        display="LS",
        signature="(self, path: str) -> list[str]",
        level=1,
        doc="List the immediate child names of a directory, ordered lexicographically.",
    ),
    Method(
        display="MV",
        signature="(self, source: str, dest: str) -> bool",
        level=2,
        doc="Move a file or a whole directory to a new path.",
    ),
    Method(
        display="RM",
        signature="(self, path: str) -> int",
        level=2,
        doc="Remove a file, or a directory and everything under it. Returns files removed.",
    ),
    Method(
        display="FIND",
        signature="(self, path: str, name: str) -> list[str]",
        level=2,
        doc="Full paths at or below path whose last component is exactly name.",
    ),
    Method(
        display="CHMOD",
        signature="(self, path: str, user: str, perms: str) -> bool",
        level=3,
        doc="Set one user's permissions on a path and everything below it.",
    ),
    Method(
        display="READ_FILE_AS",
        signature="(self, user: str, path: str) -> str | None",
        level=3,
        doc="READ_FILE performed as a user, who needs read permission.",
    ),
    Method(
        display="CREATE_FILE_AS",
        signature="(self, user: str, path: str, content: str) -> bool",
        level=3,
        doc="CREATE_FILE performed as a user, who needs write permission on the parent.",
    ),
    Method(
        display="RM_AS",
        signature="(self, user: str, path: str) -> int",
        level=3,
        doc="RM performed as a user, who needs write permission on everything removed.",
    ),
    Method(
        display="SYMLINK",
        signature="(self, path: str, target: str) -> bool",
        level=4,
        doc="Create a symbolic link at path pointing at the target path.",
    ),
    Method(
        display="RESOLVE",
        signature="(self, path: str) -> str | None",
        level=4,
        doc="The real path a path denotes once every link is followed, or None.",
    ),
)

LEVELS = (
    Level(1, "Initial Design & Basic Functions", (10, 15), 100, "a tree, or a flat map you regret"),
    Level(2, "Data Structures & Data Processing", (15, 20), 140, "subtree moves and searches"),
    Level(3, "Refactoring & Encapsulation", (20, 30), 180, "permissions inherited downwards"),
    Level(4, "Extending Design & Functionality", (20, 25), 180, "symbolic links"),
)

TAG_GLOSSARY = {
    "basics": "core mkdir/create/read/ls behaviour",
    "rejection": "operations that fail and must change nothing",
    "edge-values": "empty content, empty directories, root, case sensitivity",
    "paths": "path parsing and the parent-must-exist rule",
    "listing": "what LS returns and in what order",
    "nesting": "depth beyond one level",
    "move": "MV semantics",
    "cycles": "moving a directory into its own subtree",
    "remove": "RM and what its count means",
    "subtree": "operations that span a whole subtree",
    "search": "FIND matching and ordering",
    "ordering": "lexicographic ordering of results",
    "permissions": "CHMOD and the read/write checks",
    "inheritance": "which ancestor's permission entry wins",
    "revocation": "an explicit empty permission overriding a grant",
    "atomicity": "a rejected operation must leave no trace",
    "admin": "the unchecked operations still bypassing permissions",
    "symlinks": "creating and resolving links",
    "resolution": "following links, including mid-path",
    "loops": "links that point at each other",
    "dangling": "links whose target does not exist",
    "regression": "earlier levels still working after a refactor",
}

PROBLEM = Problem(
    key="file_system",
    title="Hierarchical File System",
    blurb=(
        "Implement a simplified hierarchical file system: directories, files and "
        "listings; then moving, removing and searching whole subtrees; then "
        "per-user permissions inherited down the tree; then symbolic links."
    ),
    class_name="FileSystem",
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source=(
        "Reconstructed from the CodeSignal progressive-workspace filesystem family "
        "(Meta/Coinbase/Anthropic re-skins): create-read -> paths -> permissions -> "
        "symlinks. Closest public analogues are LeetCode 588 and 1166."
    ),
)
