# Trie

Implement a prefix tree.

```python
class Trie:
    def insert(self, word: str) -> bool: ...      # False if already stored
    def search(self, word: str) -> bool: ...      # exact word
    def starts_with(self, prefix: str) -> bool: ...
    def count_with(self, prefix: str) -> int: ...
    def delete(self, word: str) -> bool: ...
    def words(self) -> list[str]: ...             # sorted
    def node_count(self) -> int: ...              # excluding the root
```

- `search` asks whether a **word** ends there. `starts_with` asks only whether the **path**
  exists. A stored word is a prefix of itself.
- The **empty word** can be stored, and adds no nodes.
- The empty prefix matches every stored word.
- `delete` must remove nodes that nothing else needs, and **only** those — a shared path,
  or a node marking a shorter word, has to survive.
