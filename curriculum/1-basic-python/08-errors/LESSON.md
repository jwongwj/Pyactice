# 1.8 Errors and context managers

Read this first. One screen, then nine small functions.

## Catch one thing, on purpose

```python
try:
    return int(text)
except ValueError:
    return None
```

`except ValueError` says what you expected to go wrong. `except Exception` — or a bare
`except:` — says "anything at all", which includes the `AttributeError` from the typo you
have not found yet, the `KeyError` from a rename three files away, and next year's bug.
Those get swallowed and returned as your tidy default, and you never hear about them.

The rule: name the exception you are handling. If you cannot name it, you do not yet know
what you are handling.

## Guard what you can test; catch what you cannot

```python
None if b == 0 else a / b          # a cheap test — just test it
```

versus

```python
try:
    return int(text)               # no cheap test exists
except ValueError:
    return None
```

Parsing is the classic "you cannot know without trying" case. `text.isdigit()` looks like
the test and is wrong for `"-3"`, for `" 7 "`, and for non-ASCII digits. Division by zero,
by contrast, is one comparison.

## Defaults without exceptions

```python
data.get(key, "unknown")
```

One lookup, one expression. `if key in data: data[key] else ...` is two lookups, and
`try/except KeyError` is a lot of machinery for a question the dict will answer directly.

Note it distinguishes *absent* from *falsy*: `{"a": 0}.get("a", "unknown")` is `0`.

## Failure per item

When one bad element should not sink the batch, the handler goes **inside** the loop:

```python
for item in items:
    try:
        return int(item)
    except ValueError:
        continue
```

Outside the loop, the first bad item ends everything.

## Raising well

```python
raise ValueError(f"expected a positive value, got {value}")
```

Include the value. "Invalid input" costs the next person a debugging session that the
number would have saved.

**Do not use `assert` for validation.** Assertions are removed entirely when Python runs
with `-O`, so an `assert` you rely on can simply not be there in production.

## `finally` runs on both paths

```python
try:
    ...
finally:
    log.append("end")
```

`finally` runs whether the body succeeded, raised, or returned. That is the only way to
guarantee cleanup, and one drill here checks it by raising halfway through.

## `with` is `finally`, packaged

```python
with open(path) as handle:
    ...
```

The file closes when the block ends, including when the body raises. Writing
`handle.close()` at the end of the block does not close it on the exception path — which
is the case that matters, because that is when you are leaking handles.

A missing file raises `OSError` (of which `FileNotFoundError` is a subclass), so the `with`
goes inside the `try`.

## How this unit is graded

```
✓ as_int         correct
○ divide         correct, but
                   You used `try`.
                   → None if b == 0 else a / b
```

`○` costs you no test case. The checkpoint, `load_config`, has **no constraints** — it
needs a guard, a `partition`, a per-item `try`, and line numbering, all at once.
