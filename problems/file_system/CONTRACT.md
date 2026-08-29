# Contract — Hierarchical File System

Types and shapes, the way the starter code's type hints and the visible samples would
tell you. **Available during an attempt** (`./pfs contract`).

## Class

```python
class FileSystem:
    def __init__(self) -> None: ...
```

A fresh `FileSystem()` per test case. The root directory `/` exists before you are called.

## Types

| Operation | Signature | Returns |
| --- | --- | --- |
| `MKDIR` | `(path: str) -> bool` | whether it was created |
| `CREATE_FILE` | `(path: str, content: str) -> bool` | whether it was created |
| `READ_FILE` | `(path: str) -> str \| None` | the content, or `None` |
| `LS` | `(path: str) -> list[str]` | child **names**, not paths |
| `MV` | `(source: str, dest: str) -> bool` | whether it moved |
| `RM` | `(path: str) -> int` | how many **files** were removed |
| `FIND` | `(path: str, name: str) -> list[str]` | full **paths** |
| `CHMOD` | `(path: str, user: str, perms: str) -> bool` | whether the path exists |
| `READ_FILE_AS` | `(user: str, path: str) -> str \| None` | the content, or `None` |
| `CREATE_FILE_AS` | `(user: str, path: str, content: str) -> bool` | whether it was created |
| `RM_AS` | `(user: str, path: str) -> int` | how many **files** were removed |
| `SYMLINK` | `(path: str, target: str) -> bool` | whether it was created |
| `RESOLVE` | `(path: str) -> str \| None` | a path, or `None` |

Notes that follow from the signatures:

* Nothing in this problem raises. Failure is always a return value.
* `content` is a `str`; `""` is legal content and is **not** the same as `None`.
* An empty list is `[]`, never `None`.
* `LS` returns bare child names. `FIND` returns full absolute paths. They are not the
  same shape and one is not a convenience wrapper for the other.

## Paths

* Always absolute, always `/`-separated, and they never contain `.` or `..`.
* No trailing slash, except the root, which is exactly `"/"`.
* Names are case-sensitive.
* Ordering, wherever a list is returned, is plain string ordering — the same thing
  Python's `sorted()` does.

<!-- level: 2 -->
## Subtrees

* A count of "files" is a count of files. Directories are containers, not files, and a
  removal that reports `0` may still have removed a directory.
* The root cannot be moved or removed.
<!-- /level -->

<!-- level: 3 -->
## Permissions

* `perms` is a string built from the characters `r` and `w`. `""`, `"r"`, `"w"`, `"rw"`
  and `"wr"` are the only values you will be given, and `"wr"` means the same as `"rw"`.
* A grant sets a user's permissions to exactly that value. It is not additive, and there
  is no separate revoke.
* Permissions belong to the entry, not to the path text that currently names it.
* The operations from levels 1 and 2 are administrative and are never checked.
<!-- /level -->

<!-- level: 4 -->
## Links

* A link stores the target as given, as text. The target need not exist, and the link is
  not updated if the target later moves away.
* An unresolvable path — a loop, a missing target, a non-directory in the middle — is
  reported the same way any missing path is reported. Nothing raises.
<!-- /level -->

## Scale

Tens of entries, and a depth in single digits. Nothing here needs an index; write the
clear version first.

<!-- level: 2 -->
Walking the tree on every call is fast enough at this size. Whether it stays clear enough
is the part worth thinking about.
<!-- /level -->
