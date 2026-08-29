# 1.1 For loops and comprehensions

Read this first. It is one screen, and then you write twelve small functions.

## The idea

Most Python loops people write by hand are loops the language already has a shorter,
clearer form for. The tell is almost always this line:

```python
for i in range(len(names)):
    print(names[i])
```

That works. It also says, out loud, *"I want to iterate but I only know how to count."*
Every drill in this unit replaces one version of that with the form Python actually
provides.

## The forms

**Transform every element → a comprehension.**

```python
[name.upper() for name in names]
```

**Keep some → the same, with a condition.**

```python
[p for p in paths if p.endswith(".py")]
```

**Need the position → `enumerate`,** which hands you both. The second argument sets where
counting starts, which is how you get one-based numbering without adding 1 anywhere:

```python
for i, line in enumerate(lines, start=1):
    ...
```

**Two sequences in step → `zip`.** It stops at the shorter one, which is usually what you
want and occasionally a bug worth knowing about:

```python
for name, score in zip(names, scores):
    ...
```

**Backwards → `reversed`.** A `[::-1]` slice also works, but it builds a whole new list;
`reversed` is a lazy view:

```python
list(reversed(items))
```

**Every nth → the third slice argument.** No loop at all:

```python
items[::2]      # 0, 2, 4, …
items[1::2]     # 1, 3, 5, …
```

**Neighbouring pairs → `zip` with an offset copy.** This is the one worth memorising,
because the index version is where off-by-ones live:

```python
for a, b in zip(readings, readings[1:]):
    ...
```

**Stop at the first match → `next` with a default.** A `for` with a `break` and a flag
variable is three lines saying what this says in one, and the default is how you express
"there wasn't one" without an exception:

```python
next((u for u in users if u["role"] == "admin"), None)
```

**Flatten one level → a nested comprehension.** The clauses read left to right, exactly
the order you would have written the nested loops:

```python
[value for row in rows for value in row]
```

**Build a mapping → a dict comprehension.**

```python
{r["id"]: r["name"] for r in records}
```

## When a plain loop is the right answer

This matters as much as the rest of the unit.

A comprehension is for producing one value per input. The moment you need to **carry
state across iterations** — a running total, the best seen so far, anything that depends
on the previous step — a real loop is clearer, and a comprehension that reaches out and
mutates a variable is worse than the loop it replaced:

```python
best = None
out = []
for value in items:
    best = value if best is None else max(best, value)
    out.append(best)
```

One drill in this unit *requires* a `for` statement for exactly this reason. A unit that
only ever rewards comprehensions produces people who write four-clause monsters.

## How this unit is graded

Two verdicts, kept separate:

```
✓ shout          correct
○ py_files       correct, but
                   You used `for`.
                   → [p for p in paths if p.endswith(".py")]
```

`○` is not a failure. Your answer was right; you just did not use the tool the drill is
teaching. It costs you no test case, and each drill states its constraint in the docstring
before you write anything.

The last drill, `report`, has **no constraints** — choosing the right tool yourself is the
point of the checkpoint.
