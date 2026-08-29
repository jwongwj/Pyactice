# 1.2 String manipulation

Read this first. One screen, then fifteen small functions.

## The idea

Almost every string problem has a method that already does it. The hand-rolled version is
longer *and* wrong at an edge — usually the edge where the thing you're looking for isn't
there. This unit is a tour of the methods worth knowing by name.

## Trimming and affixes

`strip()` removes whitespace from both ends. `lstrip()` / `rstrip()` do one end.

For a known prefix or suffix, **do not slice**:

```python
name[4:]                     # wrong the moment "tmp_" isn't there
name.removeprefix("tmp_")    # a no-op when absent
name.removesuffix(".bak")
```

Slicing by a hardcoded length silently eats four real characters when the prefix is
missing. `removeprefix` cannot.

## Building strings

```python
" ".join(words)
```

`join` is one allocation. `result += word` inside a loop copies the whole string every
time — O(n²) for what should be O(n). This is the single most common performance mistake
in beginner Python.

## Splitting: three different tools

```python
line.split(",")           # all the pieces
line.partition("=")       # exactly once, from the LEFT  -> (before, sep, after)
path.rpartition("/")      # exactly once, from the RIGHT
```

`partition` and `rpartition` always return **three** parts, which is what makes them safe:

```python
key, sep, value = line.partition("=")
# "a=b=c" -> ("a", "=", "b=c")
# "flag"  -> ("flag", "", "")      <- sep is "" so you can tell
```

Compare `split("=")[1]`, which raises `IndexError` when there's no `=`.

The classic pair, and both appear as drills:

```python
path.rpartition(".")[2]   # extension
path.rpartition("/")[2]   # basename
```

Watch the no-separator case. `"README".split(".")[-1]` returns `"README"` — claiming a
file with no extension has the extension `README`. `rpartition` lets you see that the
separator was absent and answer `""`.

## Comparing

```python
a.casefold() == b.casefold()
```

`casefold` is `lower` done properly — it handles cases `lower()` misses, like German `ß`
folding to `ss`. Reach for it by default when comparing.

## Prefix and suffix tests take tuples

```python
name.endswith((".png", ".jpg", ".gif"))
```

One call, no `or` chain. `startswith` does the same.

## Formatting instead of arithmetic

Padding and precision are format specs, not code you write:

```python
str(n).zfill(5)        # "00042"
f"{n:05d}"             # the same
f"{name:<8}{v:.2f}"    # left-pad to 8, then two decimals
```

A note you will meet again in unit 1.3: `f"{22.125:.2f}"` is `"22.12"`, not `"22.13"`.
`.125` has no exact binary representation, so the value stored is a hair below the tie and
rounds down. That is floating point, not formatting.

## Bulk character removal

```python
text.translate(str.maketrans("", "", string.punctuation))
```

One pass. A chain of `.replace()` calls is one pass *each*.

## Searching

```python
text.find(needle)     # -1 when absent
text.index(needle)    # raises ValueError when absent
```

Pick by what you want to happen when it isn't there.

## How this unit is graded

Two verdicts, never conflated:

```
✓ trimmed        correct
○ extension      correct, but
                   You called `split`.
                   → rpartition splits once from the right
```

`○` costs you no test case. Each drill states its constraint in the docstring before you
write anything. The checkpoint, `parse_log`, has **no constraints** — choosing the tools
is the point.
