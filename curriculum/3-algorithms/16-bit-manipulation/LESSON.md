# 3.16 Bit manipulation

Three cues, and they are quite different from each other:

| the question involves | reach for |
| --- | --- |
| everything appearing twice except one thing | XOR |
| a set of yes/no flags, or "every subset" | an integer as a bit field |
| counting bits, or powers of two | `x & (x - 1)` |

## The operators

```python
a & b      both
a | b      either
a ^ b      exactly one
~a         inverted
a << n     multiply by 2**n
a >> n     divide by 2**n, flooring
```

Two Python-specific facts that trip people up: integers are **arbitrary precision**, so
there is no word size to overflow; and negatives behave as if they had infinitely many
leading ones, so `~x` is `-x - 1` and right-shifting a negative floors towards minus
infinity. Neither matches C, so a bit trick copied from a C answer may not survive.

## XOR

Three properties, and every XOR question is one of them:

```python
x ^ x == 0          # a value cancels itself
x ^ 0 == x          # 0 is the identity
```

...and it is commutative, so order does not matter. Fold a list with `^` and everything
appearing an even number of times disappears, leaving the odd one out — in O(1) memory,
where counting would take O(n).

Watch the falsiness trap: the answer may itself be `0`, which is indistinguishable from
"nothing found" if you test truthiness rather than returning the fold.

XOR also swaps without a temporary, and finds the single differing bit between two values
(`a ^ b`, then isolate its lowest set bit with `d & -d`).

## Counting and clearing bits

```python
value & (value - 1)     # clears the LOWEST set bit
value & -value          # isolates the lowest set bit
```

The first is why a popcount loop runs once per **set** bit rather than once per bit:

```python
while value:
    value &= value - 1
    count += 1
```

`bin(x).count("1")` is the right answer in real code — and `int.bit_count()` from 3.10 is
better still. The loop is worth writing once because the identity behind it appears
everywhere else.

## Powers of two and four

`value & (value - 1) == 0` proves at most one bit is set — so with a positive value, it is
a power of two. **Zero passes that test**, so guard it separately; that is the case people
miss.

A power of *four* is a power of two whose single bit sits at an even position, which one
mask settles:

```python
value > 0 and value & (value - 1) == 0 and value & 0x5555...
```

Avoid `log(x, 4)` — floating point gives wrong answers for large values, and a loop of
divisions is slower than two bit tests.

## An integer is a subset

2ⁿ subsets, 2ⁿ integers. Bit i answers "is items[i] in":

```python
[item for i, item in enumerate(items) if mask >> i & 1]
```

This is what makes bitmask enumeration and bitmask DP available: a set of up to ~20 items
becomes a dict key or an array index, and "which subsets have I already solved" becomes a
lookup. Recognising the correspondence is the useful part.

## Counting modulo something other than two

XOR is addition mod 2 per bit position. When values appear **three** times, count each
position mod 3 instead, and whatever is left over belongs to the lonely value:

```python
for position in range(64):
    total = sum(value >> position & 1 for value in nums)
    if total % 3:
        result |= 1 << position
```

Generalising XOR that way is the idea worth taking, more than the specific problem.

## Where to reach for which

| the question says | you want |
| --- | --- |
| one value appears once, others twice | XOR fold |
| ...others three times | count bits mod 3 |
| how many 1 bits | `x & (x - 1)` loop, or `bit_count()` |
| is it a power of two | `x > 0 and x & (x - 1) == 0` |
| every subset of a small set | iterate 0 to `2**n` |
| a set as a dict key or array index | a bitmask |
| flags | named constants and `&` / `|` |
