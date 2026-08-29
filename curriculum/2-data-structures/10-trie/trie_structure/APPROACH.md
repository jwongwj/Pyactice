# Approach

## The node

```python
class _Node:
    def __init__(self):
        self.children = {}       # character -> node
        self.is_word = False
```

A dict per node keyed by one character. A list of 26 would also work and assumes an
alphabet; the dict does not, and is what to write unless the question fixes the alphabet.

## `is_word` is the whole design

Without it, "cat is stored" and "ca is on the way to something" are the same state, and
`search` cannot be written at all. The marker is what separates the two questions, and it
is the first thing to put in.

It also means a word can be stored on a node that already exists — inserting "ca" when
"cat" is present adds **no nodes**, only a flag.

## The three lookups are one walk

```python
def _walk(self, text):
    node = self.root
    for character in text:
        node = node.children.get(character)
        if node is None:
            return None
    return node
```

- `search` — walk, then check `is_word`.
- `starts_with` — walk, then check it arrived at all.
- `count_with` — walk, then count the words in that subtree.

Write the walk once.

For `count_with`, either walk the subtree each time, or keep a `passing` count on every node
and maintain it on insert and delete. The count makes queries O(len(prefix)) instead of
O(subtree); the trade is that **delete has to decrement it**, which is easy to forget.

## Delete is the exercise

Three things must all happen, and each has a case:

1. **Clear the marker.** If the word is not there — including when the path exists but is
   not a word — return False and change nothing.
2. **Prune upwards** from the deepest node, removing any node that now has no children and
   is not itself a word.
3. **Stop pruning** at the first node that is still needed. `delete("cat")` with `"ca"`
   stored must stop at the `a`; with `"car"` stored it must stop there too, because the
   node has another child.

The tidiest form is recursive, returning whether the child may be removed:

```python
def _delete(node, word, depth):
    if depth == len(word):
        if not node.is_word:
            return False, False          # not found; do not prune
        node.is_word = False
        return True, not node.children   # prune iff no children left
    ...
```

An iterative version works too: record the path on the way down and walk it back up.

## The empty word

Stored as `is_word` on the **root**. It adds no nodes, and deleting it clears the root's
flag and prunes nothing — the root is never removed. Both directions are worth testing,
because a `for character in word` loop does nothing at all for `""` and it is easy to end
up special-casing it wrongly.

## Order of work

1. The node, `insert`, and the shared walk.
2. `search` and `starts_with` on top of it — get the marker distinction right here.
3. `words` and `node_count`, which make everything else visible.
4. `count_with`.
5. `delete`, in the order above: clear, prune, stop.
