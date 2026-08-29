# Contract — Cloud File Storage

Types and shapes, the way the starter code's type hints and the visible samples would
tell you. **Available during an attempt** (`./pfs contract`).

## Class

```python
class CloudStorage:
    def __init__(self) -> None: ...
```

A fresh `CloudStorage()` per test case.

## Types

| Operation | Signature | Returns |
| --- | --- | --- |
| `ADD_FILE` | `(name: str, size: int) -> bool` | whether it was added |
| `GET_FILE_SIZE` | `(name: str) -> int \| None` | size, or `None` |
| `DELETE_FILE` | `(name: str) -> int \| None` | the deleted size, or `None` |
| `GET_N_LARGEST` | `(prefix: str, n: int) -> list[str]` | file **names** |
| `ADD_USER` | `(user_id: str, capacity: int) -> bool` | whether it was created |
| `ADD_FILE_BY` | `(user_id: str, name: str, size: int) -> int \| None` | **remaining** capacity, or `None` |
| `MERGE_USER` | `(user_id_1: str, user_id_2: str) -> int \| None` | user 1's remaining capacity, or `None` |
| `BACKUP_USER` | `(user_id: str) -> int \| None` | count, or `None` if unknown user |
| `RESTORE_USER` | `(user_id: str) -> int \| None` | count, or `None` if unknown user |

Notes that follow from the signatures:

* `ADD_FILE` returns a `bool`; it does not raise and it does not overwrite.
* `size` is an `int`; `0` is a legal size and is not "absent".
* Nothing in this problem raises. Failure is always a return value.
* `ADD_FILE_BY` returns **remaining** capacity, not used capacity. Adding a 40-byte file
  for a user with 100 returns `60`. An exact fit returns `0`, which is a success — do not
  confuse it with `None`.
* `None` from `ADD_FILE_BY` is overloaded: unknown user, taken name, and "will not fit"
  all look the same. You cannot tell them apart, and you do not need to.
* `GET_N_LARGEST` returns a list of names. No sizes. Empty result is `[]`.
* `size` is an `int`; `0` is a legal size and is not "absent".

<!-- level: 3 -->
## Rules that are not negotiable, so they are stated here

* **One namespace.** File names are unique across the whole service, whoever owns them.
* **Files added with `ADD_FILE` are not charged to any user.**
* `"admin"` is not a real user id — `ADD_FILE_BY("admin", ...)` returns `None` like any
  other unknown user.
* `DELETE_FILE` works on any file regardless of owner. It returns the **deleted file's
  size** (as at level 1) and refunds that size to whichever user was holding it, so the
  capacity becomes available again.
<!-- level: 4 -->
* Files added with `ADD_FILE` are not part of any user's backup.
* `RESTORE_USER` for a user who has never been backed up leaves everything unchanged and
  returns `0`.
* Each user has at most one backup; taking a new one replaces the old.
<!-- /level -->
<!-- /level -->

## Scale

Tens of files, and nothing here needs an index. Write the clear version first.

<!-- level: 3 -->
Recomputing a user's used space by scanning is fast enough at this size — but consider
what a fifth level would ask for.
<!-- /level -->
