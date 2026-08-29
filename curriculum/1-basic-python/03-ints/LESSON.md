# 1.3 Int and number manipulation

Read this first. One screen, then sixteen small functions.

## The idea

Integer arithmetic in Python is mostly one call you did not know about, plus two
behaviours that look like bugs and are not. This unit covers both.

## Quotient and remainder together

```python
boxes, left = divmod(total, per_box)
```

One operation for both. Writing `total // per_box` and `total % per_box` separately works
and gives two places for the operands to drift apart when you edit one.

Applied twice, it converts units — outermost unit last:

```python
minutes, sec = divmod(seconds, 60)
hours, minutes = divmod(minutes, 60)
```

## Two divisions, and a trap

```python
7 / 2      # 3.5   true division, ALWAYS a float
7 // 2     # 3     floor division, an int
8 / 2      # 4.0   still a float
```

Now the trap. **`//` rounds towards minus infinity, not towards zero:**

```python
 7 // 2    #  3
-7 // 2    # -4     <-- not -3
```

C, Java, Go and Rust all give `-3` here. Python gives `-4`, consistently with its `%`.
If you want truncation towards zero you have to ask for it:

```python
q = abs(a) // abs(b)
q if (a >= 0) == (b >= 0) else -q
```

The upside of the same rule: `%` is never negative for a positive modulus, so wrapping an
index needs no special case:

```python
-1 % 5     # 4
```

## Digits without strings

```python
while number:
    number, digit = divmod(number, 10)
```

Watch `0`: the loop body never runs, so zero has to be handled before you start. "Zero is
one digit, not no digits" is the case people miss.

## Where floats lie

This is the part that matters outside interviews.

```python
0.1 + 0.2            # 0.30000000000000004
f"{22.125:.2f}"      # "22.12"  <-- not "22.13"
```

Neither is a rounding-mode choice. `0.1`, `0.2` and `.125` have no exact binary
representation, so the value actually stored for `22.125` is a hair *below* the tie and
rounds down. No amount of `round()` fixes it, because `round()` returns another float.

**For money, hold integer cents.** Add and subtract ints; format only at the edge. If you
genuinely need decimal fractions, `decimal.Decimal` is exact and slow, and that trade is
usually the right one for money.

Formatting is a format spec, not arithmetic:

```python
f"{amount:.2f}"
```

## Bases

```python
f"{5:b}"        # "101"        binary, no prefix
bin(5)          # "0b101"      with the prefix
int("ff", 16)   # 255          the second argument is the base
int("0xFF", 16) # 255          the prefix is tolerated
```

## Bit tricks worth knowing

```python
n > 0 and n & (n - 1) == 0    # exactly one bit set: a power of two
n.bit_count()                 # how many 1 bits (Python 3.10+)
```

`n & (n - 1)` clears the lowest set bit, so a power of two becomes zero. Note that this
says "yes" for `n == 0` on its own, which is why the positivity test is there.

## Exactness

```python
math.isqrt(n)      # exact integer square root
n ** 0.5           # a float, and wrong for large n
```

`(10**30) ** 0.5` does not give `10**15`. `isqrt` does.

```python
sum(numbers)       # 0 for an empty list
math.prod(numbers) # 1 for an empty list
```

Both return the identity of their operation for an empty input, which is the answer that
makes them composable.

## How this unit is graded

```
✓ split_total    correct
○ digits         correct, but
                   You called `str`.
                   → repeatedly take number % 10, then number //= 10
```

`○` costs you no test case. The checkpoint, `human_bytes`, has **no constraints**.
