# Doubly linked list

Implement a list with links in both directions, so that a node you already have a reference
to can be removed in constant time.

```python
class DoublyLinkedList:
    def push_front(self, value: int) -> int: ...    # returns a handle
    def push_back(self, value: int) -> int: ...     # returns a handle
    def remove(self, handle: int) -> bool: ...      # O(1); False if unknown or spent
    def items(self) -> list[int]: ...               # front to back
    def reversed_items(self) -> list[int]: ...      # back to front, via the backward links
    def size(self) -> int: ...
```

- A **handle** identifies one node. Handles start at 0 and count up; they are **never
  reused**, so a handle for a removed node stays invalid forever.
- `remove` must not search the list.
- `reversed_items` must walk the backward links, not reverse the forward walk.
