# 2.8 Linked list

You will almost never build one in Python. It is worth drilling anyway, because the
questions are not about the structure — they are about manipulating references without
losing the rest of the chain, and about the two-pointer tricks a chain makes natural.

```python
class Node:
    def __init__(self, value, next=None):
        self.value = value
        self.next = next
```

An empty chain is `None`, not a node. Every function has to handle that as its first
thought, and half the bugs in this unit are a missing `if head is None`.

## Walking one

There is no `len()` and no indexing. You find out by walking:

```python
node = head
while node is not None:
    ...
    node = node.next
```

`while node:` also works but is not the same test — it calls `__bool__`, and a node whose
value is falsy is still a node. `is not None` says what you mean.

**Iterate, do not recurse.** The recursive walk is prettier and dies on a long chain:
Python's default recursion limit is around 1000, and a chain of ten thousand is not
unusual. Every drill here that could be recursive has a reason not to be.

## Re-pointing: the three names

Reversing is the canonical exercise, and the whole difficulty is in one line:

```python
previous, node = None, head
while node is not None:
    following = node.next      # SAVE it first
    node.next = previous       # ...because this destroys the only reference to it
    previous = node
    node = following
return previous                # the new head, not `node` -- node is None here
```

Overwriting `node.next` before saving it strands the rest of the chain with no way back.
Two other details worth committing: the *old* head ends up pointing at `None`, which
happens automatically because `previous` starts as `None`; and the return is `previous`,
because the loop only stops once `node` has walked off the end.

## Floyd: two pointers at different speeds

To detect a cycle, a set of visited nodes works and costs O(n) memory. The answer the
question is looking for costs O(1):

```python
slow = fast = head
while fast is not None and fast.next is not None:
    slow = slow.next
    fast = fast.next.next
    if slow is fast:
        return True
return False
```

If there is a cycle, the fast pointer laps the slow one and they meet. If there is not,
the fast pointer runs off the end.

Two things that are load-bearing. The loop condition checks **both** `fast` and
`fast.next`, because `fast.next.next` reads two links ahead and either could be `None` —
a one-node chain crashes without it. And the comparison is `is`, not `==`: with the
value-based `__eq__` these drills use, `==` would compare the chains and report a false
meeting.

Advance the pointers *before* comparing, or they start equal and every chain looks cyclic.

## Two pointers at a fixed offset

"Remove the nth node from the end" without knowing the length. Send one pointer n steps
ahead, then walk both until the leader reaches the end — the follower is now exactly n
from the end:

```python
lead = head
for _ in range(n):
    if lead is None:
        return head            # n was larger than the chain
    lead = lead.next
if lead is None:
    return head.next           # n == length, so the HEAD is the one to remove
trail = head
while lead.next is not None:
    lead, trail = lead.next, trail.next
trail.next = trail.next.next
return head
```

The case that catches people is `n == length`: the node to remove is the head itself, so
the answer starts at a different node and no `trail.next` assignment can express that.
Handle it separately, or use a dummy node in front of the head so the head has a
predecessor like everything else.

## The dummy head

Whenever a function might change which node is first — merging, removing, inserting at the
front — a throwaway node in front removes the special case:

```python
dummy = Node(0)
tail = dummy
...                            # splice everything onto tail, uniformly
return dummy.next              # whatever ended up first
```

It costs one allocation and deletes an entire branch. Merging two sorted chains is the
clearest example: without a dummy, the first splice has to choose the head separately from
every later one.

## Where to reach for which

| the question says | you want |
| --- | --- |
| reverse it | three names, re-point in place |
| does it loop | slow and fast pointers |
| the middle node | slow and fast — slow lands on the middle |
| the nth from the end | two pointers, n apart |
| merge two sorted chains | a dummy head and a splice |
| the head might change | a dummy head |
