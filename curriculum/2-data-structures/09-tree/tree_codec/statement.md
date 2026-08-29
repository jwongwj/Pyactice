# Serialise and deserialise a tree

Turn a binary tree into a string and back.

```python
class TreeCodec:
    def build(self, values: list[int | None]) -> None: ...  # from a level-order list
    def encode(self) -> str: ...
    def decode(self, text: str) -> bool: ...                # False if invalid
    def pre_order(self) -> list[int]: ...
    def in_order(self) -> list[int]: ...
    def size(self) -> int: ...
```

The encoding is **pre-order** — node, then left, then right — with values separated by
commas and every absent child written as `#`:

```
    1          ->  "1,2,#,#,3,#,#"
   / \
  2   3
```

- An empty tree encodes as `"#"`. The empty string is **not** a valid encoding.
- `decode` returns `False` for anything that is not a valid encoding — text that runs out
  early, text left over at the end, or a token that is neither a number nor `#`. A rejected
  decode leaves the tree **empty**.
- `build` takes a level-order list where `None` marks an absent child, and replaces
  whatever was there.
