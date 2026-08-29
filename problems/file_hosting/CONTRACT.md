# Contract — In-Memory File Hosting Service

This is the information the real assessment gives you through the starter code's
type hints and its visible sample tests. It is **fair game during an attempt** —
`./pfs contract` prints it. It states types and shapes only. It does not tell you
what the answers are, and it deliberately leaves the genuinely ambiguous points
alone; those you resolve the way you would in the real thing, by reading the
sample cases and the failures.

## Class

```python
class FileHost:
    def __init__(self) -> None: ...
```

The harness constructs a fresh `FileHost()` per test case. Nothing is shared
between cases.

## Types

| Operation | Signature | Returns |
| --- | --- | --- |
| `FILE_UPLOAD` | `(file_name: str, size: int) -> None` | nothing |
| `FILE_GET` | `(file_name: str) -> int \| None` | size, or `None` |
| `FILE_COPY` | `(source: str, dest: str) -> None` | nothing |
| `FILE_SEARCH` | `(prefix: str) -> list[str]` | file **names**, no sizes |
| `FILE_UPLOAD_AT` | `(timestamp: int, file_name: str, file_size: int, ttl: int \| None = None) -> None` | nothing |
| `FILE_GET_AT` | `(timestamp: int, file_name: str) -> int \| None` | size, or `None` |
| `FILE_COPY_AT` | `(timestamp: int, file_from: str, file_to: str) -> None` | nothing |
| `FILE_SEARCH_AT` | `(timestamp: int, prefix: str) -> list[str]` | file **names** |
| `ROLLBACK` | `(timestamp: int) -> None` | nothing |

Notes that follow from the signatures:

* `size` is an `int`, not a string. `0` is a legal size and is **not** the same
  as "absent".
<!-- level: 2 -->
* Search returns a `list[str]` of names — not `"name(size)"` strings, not tuples.
  An empty result is `[]`.
<!-- /level -->
<!-- level: 3 -->
* `timestamp` and `ttl` are `int` seconds. `ttl` is optional: the operation is
  called with three arguments when there is no ttl and four when there is, so
  your parameter needs a default.
<!-- /level -->
* Operations that return nothing may return anything; the harness does not check
  the return value of a void operation.

## Errors

Where the statement says "throws a runtime exception", raise any `Exception`
subclass. The harness accepts `RuntimeError`, `ValueError`, `KeyError`, a custom
class — anything, as long as it is not a `BaseException` that sits outside
`Exception`. It does **not** accept returning an error code instead of raising.

<!-- level: 3 -->
## Time

* Timestamps are integers and are supplied by the caller. There is no wall clock.
* A file with `ttl = n` uploaded at `t` is alive on the half-open interval
  `[t, t + n)`. With no ttl it is alive on `[t, ∞)`.
* The level-1 and level-2 operations are the timestamped operations at
  `timestamp = 0` with no ttl. `FILE_UPLOAD(name, size)` and
  `FILE_UPLOAD_AT(0, name, size)` are the same call, and either one will raise if
  the other already created that name.
* A file does not exist at timestamps before its upload.
<!-- /level -->

## Scale

Test cases stay small — tens of files, not millions. Nothing here needs a trie or
a heap to pass. Write the clear version first.
