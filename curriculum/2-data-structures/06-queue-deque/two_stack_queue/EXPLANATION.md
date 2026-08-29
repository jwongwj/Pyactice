# Explanation

## The shape of the answer

```python
class TwoStackQueue:
    def __init__(self):
        self.incoming = []
        self.outgoing = []

    def _shift(self):
        if not self.outgoing:                 # ONLY when dry
            while self.incoming:
                self.outgoing.append(self.incoming.pop())

    def enqueue(self, value):
        self.incoming.append(value)

    def dequeue(self):
        self._shift()
        return self.outgoing.pop() if self.outgoing else None

    def peek(self):
        self._shift()
        return self.outgoing[-1] if self.outgoing else None

    def size(self):
        return len(self.incoming) + len(self.outgoing)
```

## Why `if not self.outgoing` and not `while True`

Suppose the output stack holds `[2]` — value 2 is next out — and 3 is then enqueued. If a
transfer happened now, 3 would be pushed on top of 2 and come out **first**. The queue
would be wrong, and only for inputs that interleave adds and removes.

Waiting until the output stack is dry means everything in it is strictly older than
everything in the input stack, so the two never interleave.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `interleaved_adds_and_removes` | transferring while the output stack is non-empty |
| `transfer_only_when_dry` | the same, over several rounds |
| `peek_triggers_transfer` | `peek` reading the wrong stack |
| `size_counts_both_stacks` | counting only one stack after a transfer |
| `drain_then_refill` | state left behind by an emptied queue |
| `negatives_and_zero` | using falsiness to test emptiness |

## Complexity

| operation | worst case | amortised |
| --- | --- | --- |
| enqueue | O(1) | O(1) |
| dequeue / peek | O(n) | **O(1)** |
| size | O(1) | O(1) |

## Why you would ever do this

In Python you would not — `collections.deque` is O(1) at both ends and is the right answer
(unit 2.6). The exercise exists because:

- it is the standard demonstration of **amortised** analysis, which is a genuinely
  different idea from worst case;
- the same reverse-twice trick appears in immutable and functional queues, where it is the
  *only* way to get O(1) amortised behaviour;
- and "build X out of Y" questions test whether you understand what X actually guarantees.
