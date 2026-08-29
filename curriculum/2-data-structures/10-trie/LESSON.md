# 2.10 Trie

A trie is a tree keyed by the characters of a word. The root is the empty string, each edge
is a character, and a path from the root spells a prefix.

```python
from collections import defaultdict

def make():
    return {"children": defaultdict(make_node), "is_word": False, "count": 0}
```

In practice a nested dict is enough, and is what most people write under time pressure:

```python
root = {}
for word in words:
    node = root
    for character in word:
        node = node.setdefault(character, {})
    node["$"] = True          # a sentinel marking "a word ends here"
```

The sentinel matters. Without it you cannot tell "cat is a stored word" from "cat is merely
a prefix of cattle". Use a key that cannot be a character — `"$"`, or a separate `is_word`
flag if the node is an object.

## When it pays, and when it does not

This is the actual lesson of the unit, and the drills are arranged around it.

| the question | reach for |
| --- | --- |
| is this exact word present | a `set` — O(1), one line |
| which words start with this prefix (asked once) | `startswith` in a comprehension |
| **many prefix queries against one fixed word list** | a trie, or a prefix-count dict |
| the longest prefix common to all words | neither — walk the columns |
| autocomplete, ranked | a trie with counts, or count-then-sort |

Building a trie costs O(total characters). Answering one prefix query with `startswith`
costs O(number of words). So a trie only wins when you will ask **many** queries, or when
you need to walk the prefixes themselves. Building one to answer a single question is more
code doing more work.

For counting prefixes there is a shortcut worth knowing — every prefix of every word,
counted into a dict:

```python
counts = defaultdict(int)
for word in words:
    for end in range(len(word) + 1):
        counts[word[:end]] += 1
```

Same asymptotic cost as a trie for this job, a fraction of the code, and it answers each
query with one dict lookup. The trie's real advantage is that it can also enumerate what
lies *below* a prefix, which a flat dict of counts cannot.

## The longest common prefix is not a trie question

It looks like one — the answer is the path from the root until it branches — and building a
trie to find it is a lot of work for something you can do by walking the words together:

```python
first = words[0]
for index, character in enumerate(first):
    for other in words[1:]:
        if index >= len(other) or other[index] != character:
            return first[:index]
return first
```

The `index >= len(other)` check is the whole difficulty. Whichever word is shortest caps
the answer, and it is not necessarily `words[0]` — if the first word is the *longest*, the
loop will run off the end of another word and raise `IndexError`. Test both arrangements.

The other trap is the repeated-shortening approach: take a candidate, test it against every
word with `startswith`, drop a character, repeat. It is correct and quadratic in the prefix
length.

## Autocomplete

Two steps, and they are separate concerns: **find** the words with the prefix, then **rank**
them.

```python
uses = Counter()
for word, count in entries:
    if word.startswith(prefix):
        uses[word] += count
ranked = sorted(uses.items(), key=lambda item: (-item[1], item[0]))
return [word for word, _ in ranked[:k]]
```

The tie-break is where these go wrong. `Counter.most_common` orders equal counts by
insertion, not alphabetically — see unit 2.3. If the question says "ties alphabetically",
sort with the compound key `(-count, word)` yourself.

Also: a count of zero is still a match. Filtering with `if count:` silently drops words
that exist and have never been used, which is not the same question.

In a real system the counts live *on the trie nodes*, so the prefix walk arrives at a
subtree already knowing what is beneath it. That is the version worth describing out loud
in an interview even when you write the simpler one.

## Cost

| | trie | set of words |
| --- | --- | --- |
| build | O(total characters) | O(total characters) |
| exact lookup | O(length of word) | O(1) average |
| prefix query | O(length of prefix) | O(number of words) |
| space | one node per distinct prefix | one entry per word |

A trie shares storage between words with common prefixes, which is why it is the structure
behind dictionaries, routing tables and autocomplete — and why it is overkill for a
thousand words and one question.
