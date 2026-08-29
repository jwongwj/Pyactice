# Queue from two stacks

Implement a first-in-first-out queue using only stack operations — append and pop from the
end of a list. No `deque`, no `pop(0)`, no indexing into the middle.

```python
class TwoStackQueue:
    def enqueue(self, value: int) -> None: ...
    def dequeue(self) -> int | None: ...
    def peek(self) -> int | None: ...
    def size(self) -> int: ...
```

- `dequeue` and `peek` return `None` on an empty queue rather than raising.
- Operations should be **O(1) amortised** — a single call may be slower, but n calls must
  cost O(n) in total.
