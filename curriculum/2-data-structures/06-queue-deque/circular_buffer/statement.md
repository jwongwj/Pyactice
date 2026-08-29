# Circular buffer

Implement a fixed-size queue that overwrites its oldest entry when full, and allocates
nothing after it is sized.

```python
class CircularBuffer:
    def resize(self, capacity: int) -> None: ...   # discards everything
    def write(self, value: int) -> bool: ...       # False iff something was overwritten
    def read(self) -> int | None: ...              # the oldest value
    def items(self) -> list[int]: ...              # oldest first, non-destructive
    def is_full(self) -> bool: ...
    def size(self) -> int: ...
```

- Writing to a full buffer **overwrites the oldest value** and returns `False`.
- A capacity of 0 or less holds nothing: every write is refused, and the buffer is
  always full.
- A buffer that has not been sized behaves as one sized 0.
- The storage must not grow. Use indices and modular arithmetic.
