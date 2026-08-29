# Explanation

## The shape of the answer

```python
class _Node:
    __slots__ = ("children", "is_word")
    def __init__(self):
        self.children = {}
        self.is_word = False


class Trie:
    def __init__(self):
        self.root = _Node()

    def _walk(self, text):
        node = self.root
        for character in text:
            node = node.children.get(character)
            if node is None:
                return None
        return node

    def insert(self, word):
        node = self.root
        for character in word:
            node = node.children.setdefault(character, _Node())
        if node.is_word:
            return False
        node.is_word = True
        return True

    def search(self, word):
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix):
        return self._walk(prefix) is not None

    def _collect(self, node, so_far, out):
        if node.is_word:
            out.append(so_far)
        for character, child in node.children.items():
            self._collect(child, so_far + character, out)

    def count_with(self, prefix):
        node = self._walk(prefix)
        if node is None:
            return 0
        out = []
        self._collect(node, "", out)
        return len(out)

    def words(self):
        out = []
        self._collect(self.root, "", out)
        return sorted(out)

    def node_count(self):
        total, stack = 0, [self.root]
        while stack:
            node = stack.pop()
            total += len(node.children)
            stack.extend(node.children.values())
        return total

    def delete(self, word):
        removed, _prune = self._delete(self.root, word, 0)
        return removed

    def _delete(self, node, word, depth):
        if depth == len(word):
            if not node.is_word:
                return False, False          # a path, not a word
            node.is_word = False
            return True, not node.children   # prune only if it is now a dead end
        character = word[depth]
        child = node.children.get(character)
        if child is None:
            return False, False
        removed, prune_child = self._delete(child, word, depth + 1)
        if prune_child:
            del node.children[character]
        # This node may go only if it is now childless AND is not a word itself.
        return removed, removed and not node.children and not node.is_word
```

## The two return values

`_delete` answers two different questions at once, and conflating them is the bug:

- **Was the word removed?** Propagates all the way up unchanged, and becomes the answer.
- **May this child be pruned?** Only true when the node has no children left *and* is not
  itself a word. It stops being true at the first node that is still needed, and the
  pruning stops there.

The second is deliberately `removed and ...` — if nothing was removed, nothing is pruned,
however childless the nodes look.

## What the cases are checking

| case | what it catches |
| --- | --- |
| `insert_and_search` | no `is_word` marker at all |
| `prefix_of_a_stored_word` | inserting a prefix failing to mark an existing node |
| `delete_leaves_siblings` | pruning a node another word still needs |
| `delete_keeps_a_prefix_word` | pruning past a node that is itself a word |
| `delete_prunes_dead_nodes` | not pruning, so `starts_with` finds a path to nowhere |
| `delete_absent` | deleting a path that is not a word |
| `empty_word` / `delete_empty_word` | a `for` loop that does nothing for `""` |
| `nodes_are_shared` | a node per word rather than per prefix |
| `count_after_delete` | a cached count not decremented |

`delete_keeps_a_prefix_word` and `delete_leaves_siblings` are the pair worth running by
hand. They are the two different reasons pruning must stop, and an implementation can easily
handle one and not the other.

## Complexity

| operation | cost |
| --- | --- |
| insert / search / starts_with | O(len(word)) |
| delete | O(len(word)) |
| count_with | O(len(prefix) + size of the subtree) |
| words | O(total characters stored) |

Independent of how many words are stored — which is the trie's whole advantage over a list,
and its parity with a hash set for exact lookup. The prefix queries are what a hash set
cannot do at all (unit 2.10).

Space is one node per distinct **prefix**, which is why words with common beginnings are
cheap and a set of unrelated words is not. For long sparse chains, a *radix* tree collapses
each run of single-child nodes into one edge holding a whole substring.
