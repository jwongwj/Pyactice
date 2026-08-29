# Contract — In-Memory Key-Value Database

Types and shapes only, the way the starter code's type hints and the visible sample
cases would tell you. **Available during an attempt** (`./pfs contract`). It does not
resolve the interesting ambiguities — those you settle from the samples and the tests,
same as the real thing.

## Class

```python
class InMemoryDB:
    def __init__(self) -> None: ...
```

A fresh `InMemoryDB()` per test case.

## Types

| Operation | Signature | Returns |
| --- | --- | --- |
| `SET` | `(key: str, field: str, value: str) -> None` | nothing |
| `GET` | `(key: str, field: str) -> str \| None` | the value, or `None` |
| `DELETE` | `(key: str, field: str) -> bool` | whether a field was removed |
| `SCAN` | `(key: str) -> list[str]` | `["<field>(<value>)", ...]` |
| `SCAN_BY_PREFIX` | `(key: str, prefix: str) -> list[str]` | same, filtered |
| `SET_AT` | `(key: str, field: str, value: str, timestamp: int) -> None` | nothing |
| `SET_AT_WITH_TTL` | `(key: str, field: str, value: str, timestamp: int, ttl: int) -> None` | nothing |
| `DELETE_AT` | `(key: str, field: str, timestamp: int) -> bool` | whether a field was removed |
| `GET_AT` | `(key: str, field: str, timestamp: int) -> str \| None` | the value, or `None` |
| `SCAN_AT` | `(key: str, timestamp: int) -> list[str]` | `["<field>(<value>)", ...]` |
| `SCAN_BY_PREFIX_AT` | `(key: str, prefix: str, timestamp: int) -> list[str]` | same, filtered |
| `BACKUP` | `(timestamp: int) -> int` | number of records saved |
| `RESTORE` | `(timestamp: int, timestamp_to_restore: int) -> None` | nothing |

<!-- level: 3 -->
**`timestamp` is the LAST argument**, not the first. This is the opposite of the file
hosting problem in this bank, and it is what the sources report for this one. Getting it
backwards produces silent nonsense rather than a `TypeError`, so check it once and move on.
<!-- /level -->

Other notes that follow from the signatures:

* Values are opaque **strings**. `""` is a value and is not the same as absent — `GET`
  returns `""` for a field set to `""`, and `None` for a field that is not there.
* `DELETE` returns a `bool`, not the removed value.
* Scan results are `list[str]`, formatted `"<field>(<value>)"` by plain concatenation —
  values are not escaped or quoted. An empty result is `[]`, never `None`.
* `ttl` is not optional on `SET_AT_WITH_TTL`; "no ttl" is a different method, `SET_AT`.
* `BACKUP` returns an `int`. `RESTORE` returns nothing.

<!-- level: 3 -->
## Time

* Timestamps are integer seconds supplied by the caller. There is no wall clock.
* **Timestamps are non-decreasing across calls.** You will not be asked about the past
  except through `RESTORE`.
* A field written at `t` with `ttl = n` is alive on `[t, t + n)` — gone at exactly `t + n`.
  Written without a ttl, it is alive forever.
* The level-1 and level-2 operations are the timestamped ones at `timestamp = 0` with no
  ttl. They share one store with the `_AT` operations.
* `RESTORE` with no backup at or before `timestamp_to_restore` leaves the database
  unchanged.
<!-- /level -->

## Scale

Tens of records and fields. Nothing here needs an index or a heap.
