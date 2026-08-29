# Streaming median

Track the median of a stream of values as they arrive.

```python
class StreamingMedian:
    def add(self, value: int) -> None: ...
    def median(self) -> int | None: ...
    def lower_half_size(self) -> int: ...
    def count(self) -> int: ...
    def smallest(self) -> int | None: ...
```

- With an **even** count the median is the average of the two middle values, using integer
  division **towards negative infinity** — so `-3` and `-2` give `-3`, not `-2`.
- With an **odd** count the lower half holds one more value than the upper half.
- `median` and `smallest` return `None` before anything is added.
- `add` should be O(log n). Re-sorting on every insertion is not acceptable.
