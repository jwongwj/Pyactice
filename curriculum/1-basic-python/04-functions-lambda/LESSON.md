# 1.4 Functions, lambda and `key=`

Read this first. One screen, then thirteen small functions.

## The one that matters most: `key=`

`sorted`, `min`, `max`, `heapq.nlargest` and `heapq.nsmallest` all take a `key`. Learn it
once and you have learned all of them.

`key` is a function applied to each element to decide its *ordering*, without changing the
element:

```python
sorted(words, key=len)                       # shortest first
sorted(rows, key=lambda r: r["score"])       # by a field
```

**Two directions in one sort.** Return a tuple, and negate the part you want reversed:

```python
sorted(rows, key=lambda r: (-r["score"], r["name"]))
```

Score descending, then name ascending. This is the single highest-value line in the unit,
because sorting twice — once per field — throws away the first ordering, and it is the
mistake people make under time pressure.

`reverse=True` flips the *whole* comparison, so it cannot express "one field down, another
up". The negated tuple can.

**When the key is just "field n", say so:**

```python
sorted(pairs, key=operator.itemgetter(1))
```

## Default arguments, and the famous trap

```python
def greet(name, greeting="Hello"): ...
```

Now the trap. **A default is evaluated once, when the function is defined** — not on each
call. So a mutable default is shared by every call that omits it:

```python
def collect(item, into=[]):      # WRONG
    into.append(item)
    return into

collect(1)   # [1]
collect(2)   # [1, 2]   <- the same list, still there
```

The fix is always the same shape:

```python
def collect(item, into=None):
    into = [] if into is None else into
```

This one is worth remembering because it does not fail in tests that call the function
once. It fails in production, days later, and looks like data corruption.

## Any number of arguments

```python
def tally(*values):      # a tuple
    return sum(values)

def settings(**options): # a dict
    return [f"{k}={options[k]}" for k in sorted(options)]
```

Note the `sorted`: a dict preserves *insertion* order, which is not alphabetical order.

## map, filter, and when neither is right

```python
list(map(lambda n: n * 2, numbers))
list(filter(lambda n: n > 0, numbers))
```

Both return lazy iterators, so wrap them in `list()` when you want a list.

But when you need to transform **and** filter, a comprehension says it better than nesting
two calls with two lambdas:

```python
[w.upper() for w in words if len(w) > 3]                  # clear
list(map(str.upper, filter(lambda w: len(w) > 3, words)))  # not
```

One drill in this unit *forbids* `map` and `filter` for exactly that reason.

## functools

```python
functools.partial(round, ndigits=2)      # a function with an argument pre-bound
functools.reduce(lambda a, b: a + b, xs, 0)  # fold a sequence to one value
```

`partial` is for handing a configured function to something that will call it — `map`,
`sorted(key=...)`, a callback. `reduce` is worth knowing so you recognise a fold, but in
real code `sum`, `math.prod`, `"".join` and `max` already are the folds you want.

## How this unit is graded

```
✓ by_length      correct
○ doubled        correct, but
                   This drill wants `map`.
```

`○` costs you no test case. The checkpoint, `leaderboard`, has **no constraints** — it
needs filtering, a compound key and a slice together, and choosing them is the point.
