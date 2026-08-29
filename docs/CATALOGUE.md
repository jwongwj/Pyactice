# Catalogue — four categories, difficulty rising inside each

```
1. Basic Python        the language does more than you are using
2. Data Structures     one per structure: use it, then build it
3. Algorithms          by name, the ones that actually come up
4. Industry practices  the 90-minute multi-level project
```

Difficulty **1**–**5** rises within every subtopic. Ordering across categories is by
prerequisite, not by label.

Exercise types: **D** drill (one idiom, seconds to minutes, constraint-checked) ·
**U** use a structure · **B** build a structure from scratch · **P** pattern problem.

---

# 1. Basic Python

Short drills. Each has an explicit constraint so the *idiom* is what gets practised, not
just the answer — a nested loop that returns the right list has missed the point.

All eight subtopics are written: 92 drills, 8 of them checkpoints. A subtopic is authored
as one `unit.py` and practised one drill at a time, so every drill below is its own
problem in the bank, keyed `<unit>.<function>` — `for_loops.numbered`,
`strings.extension`, `unpacking.head_tail`. The **C** row of each subtopic is that unit's
checkpoint and is keyed the same way. `./pfs list` prints the keys; this document is the
ladder, not the index.

## 1.1 For loops and comprehensions

| # | task | idiom | diff |
| --- | --- | --- | --- |
| D1 | uppercase every name | `[f(x) for x in xs]` | 1 |
| D2 | keep only `.py` files | comprehension with `if` | 1 |
| D3 | index alongside value | `enumerate` — forbid `range(len(...))` | 1 |
| D4 | walk two lists together | `zip` | 2 |
| D5 | last to first | `reversed` | 2 |
| D6 | every other item | slice step `[::2]` | 2 |
| D7 | invert a mapping | dict comprehension | 2 |
| D8 | flatten one level | nested comprehension | 3 |
| D9 | first match, else a default | `next(..., default)` — forbid `break` | 3 |
| D10 | consecutive pairs | `zip(xs, xs[1:])` | 3 |
| D11 | when a plain loop is clearer | *require* a `for` statement | 3 |
| **C** | summarise a list of rows into report lines | | 3 |

D11 is deliberate. A unit that only rewards comprehensions produces four-clause monsters.

## 1.2 String manipulation

| # | task | idiom | diff |
| --- | --- | --- | --- |
| D1 | trim whitespace both ends | `strip` | 1 |
| D2 | drop a known prefix and suffix | `removeprefix` / `removesuffix` | 1 |
| D3 | build a sentence from words | `join` — forbid `+=` in a loop | 1 |
| D4 | split a CSV line | `split` | 1 |
| D5 | filename and extension | `rpartition('.')` — forbid `split` | 2 |
| D6 | directory and basename | `rpartition('/')` | 2 |
| D7 | split once from the left | `partition` | 2 |
| D8 | swap a substring | `replace`, with a count | 2 |
| D9 | case-insensitive compare | `casefold` — forbid `lower` | 2 |
| D10 | test many prefixes at once | `startswith(tuple)` | 3 |
| D11 | pad and align for a table | f-string `:>8`, `:.2f` | 3 |
| D12 | zero-pad a number | `zfill` | 2 |
| D13 | strip punctuation | `str.translate` + `maketrans` | 4 |
| D14 | find with a not-found answer | `find` vs `index` | 3 |
| **C** | parse a log line into typed fields | | 4 |

## 1.3 Int and number manipulation

| # | task | idiom | diff |
| --- | --- | --- | --- |
| D1 | quotient and remainder together | `divmod` | 1 |
| D2 | seconds → h:m:s | `divmod` twice | 2 |
| D3 | floor vs true division | `//` and `/` | 1 |
| D4 | wrap an index around | `%` | 2 |
| D5 | negative-number floor division (the trap) | `//` with negatives | 3 |
| D6 | digits of a number | `%10` and `//10` — forbid `str()` | 3 |
| D7 | round to 2 decimals for money | an f-string format spec, and why floats lie | 3 |
| D8 | exact money | integer cents — forbid `float` and `round` | 4 |
| D9 | clamp to a range | `max(lo, min(hi, x))` | 2 |
| D10 | to binary | `bin`, minus the prefix | 3 |
| D11 | from hex | `int(s, 16)` — the second argument is the base | 3 |
| D12 | is a power of two | `n & (n - 1) == 0` | 4 |
| D13 | count set bits | `int.bit_count` | 3 |
| D14 | integer square root | `math.isqrt` — forbid `**0.5` | 3 |
| D15 | sum and product of a list | `sum`, `math.prod` | 1 |
| **C** | format a byte count as KB/MB/GB | | 4 |

## 1.4 Functions, lambda and `key=`

D1 a real default argument, not an `if` that fills it in · D2 the mutable-default trap ·
D3 `*args` · D4 `**kwargs` and `sorted` · D5 a compound `key=` in **one** `sorted` ·
D6 a lambda key returning a tuple, negating to reverse one part ·
D7 `operator.itemgetter` instead of a lambda · D8 `map` · D9 `filter` · D10 when a
comprehension beats `map` + `filter` with two lambdas · D11 `functools.partial` ·
D12 `functools.reduce` · **C** a leaderboard.

## 1.5 Unpacking and assignment

D1 swap two values, no temporary · D2 unpack in a comprehension header · D3 `first, *rest`
· D4 the last two, one slice · D5 `*middle` instead of slice arithmetic · D6 ignore with
`_` · D7 `zip(*rows)` to turn rows into columns · D8 `dict()` from an iterable of pairs ·
**C** regroup a list of records.

## 1.6 Truthiness, None and conditionals

D1 test the collection directly, not `len(...) > 0` · D2 `is None`, not `or` — an empty
name is a real name · D3 the same trap with numbers: a configured `0` is a real port ·
D4 `next` with a default and an `is not None` test · D5 chained comparison `a < b < c` ·
D6 conditional expression, no `if` statement · D7 `all` · D8 `any` · D9 guard with
`is None` rather than catching the `TypeError` · **C** validate a record and report the
first problem.

## 1.7 Sorting

D1 `sorted`, not `.sort()`, so the caller's list survives · D2 `reverse=True` rather than
sort-then-reverse · D3 compound key `(-score, name)` in **one** sort · D4 a key function,
not a decorated list · D5 `key=str.casefold` without lower-casing the values themselves ·
D6 lean on stability instead of adding the index to the key · D7 sort descending and take
a slice that survives a short list · **C** standings with three tie-breaks, one sort.

D3 is the highest-value drill in this whole category — sorting twice and losing the first
ordering is the most common real mistake here.

## 1.8 Errors and context managers

D1 catch `ValueError` specifically, never a bare `except` · D2 guard with a comparison
instead of catching `ZeroDivisionError` · D3 `dict.get` with a default, no `try` at all ·
D4 one `try` per item, so one bad value does not end the loop · D5 catch `TypeError` ·
D6 `raise ValueError` saying what was wrong · D7 `finally`, so cleanup runs on both paths
· D8 `with` for a file, catching `OSError` · **C** load a config file, skipping and
reporting bad lines.

---

# 2. Data Structures

One subtopic per structure. Each starts with **using** it and ends with **building** it —
using a stack teaches nothing about stacks; making `min()` O(1) forces you to discover the
idea.

## 2.1 List — **written** (9 drills, 41 cases, key `lists`)

1 INSERT_AT · 2 DROP_AT · 3 DROP_VALUE · 4 FLIPPED (two-pointer swap; `reversed` and
`.reverse` forbidden) · 5 DEDUPED (order kept; `count`/`index` forbidden) · 6 ROTATED
(one modulo, two slices, no loop) · 7 MERGE_SORTED (`sorted` forbidden) · 8 CHUNKED
(strided range) · 9 TOP_SCORES (checkpoint).

The cost material — `pop(0)` is O(n), append is amortised — is in the LESSON rather than a
drill: a function's return value cannot show its complexity. **B** DYNAMIC_ARRAY — **written**
(13 cases, key `dynamic_array`): slots, a used count and doubling. The capacity is
observable, which is the only thing separating a real answer from a wrapper around
`list.append`.

## 2.2 Tuple — **written** (6 drills, 24 cases, key `tuples`)

1 MIN_MAX (several returns) · 2 VISITS (the pair IS the key; joining to a string forbidden,
and a case proves why: `("a|b","mon")` and `("a","b|mon")` would collide) ·
3 BY_DEPT_THEN_PAY (one compound key, mixed direction) · 4 PEAK (`namedtuple` required) ·
5 UNIQUE_PAIRS · 6 LEADERBOARD (checkpoint).

## 2.3 Dict — **written** (9 drills, 40 cases, key `dicts`)

1 LOOKUP_OR (`get` with a default; a stored `0` must beat the fallback, which is the case
`get(k) or default` fails) · 2 APPEND_TO (`setdefault` required) · 3 GROUPED (`defaultdict`
required) · 4 TALLY (`Counter` required) · 5 TOP_ITEMS (`most_common` breaks ties by
insertion order, NOT alphabetically — a visible case pins this) · 6 MERGED (later wins) ·
7 INVERTED (collisions collected, not overwritten) · 8 FIRST_UNIQUE (two passes) ·
9 SUBARRAY_SUM_COUNT (checkpoint: prefix sums with a count, not a set).

**B** HASH_MAP — **written** (19 cases, key `hash_map`): buckets, chains and a load
factor. The hash is SPECIFIED rather than Python's, because `hash()` is salted per process
and no bucket number would otherwise be reproducible.

## 2.4 Set — **written** (7 drills, 32 cases, key `sets`)

1 UNIQUE_SORTED · 2 UNIQUE_STABLE (`dict.fromkeys`; `sorted` forbidden, and a case with
descending input proves `sorted(set(...))` is a different answer) · 3 COMMON ·
4 ONLY_IN_FIRST (a case pins that difference is not symmetric) · 5 IN_ALL_THREE (a case
where every pair overlaps but nothing is in all three) · 6 TAG_GROUPS (`frozenset`
required) · 7 OVERLAP_REPORT (checkpoint).

## 2.5 Stack — **written** (6 drills, 36 cases, key `stacks`)

1 BALANCED (`replace`/`count` forbidden; a visible case shows "([)]" has the right counts
and the wrong order) · 2 EVAL_RPN (`eval` and recursion forbidden; a visible case pins
truncation towards zero, where `//` floors) · 3 APPLY_UNDO · 4 NEXT_GREATER (monotonic
stack) · 5 DAILY_WAIT (the same stack answering in distances) · 6 LARGEST_RECTANGLE
(checkpoint).

**B** MIN_STACK — **written** (12 cases, key `min_stack`): a parallel stack of minima.
A visible case pins the duplicate-minimum trap.

## 2.6 Queue and deque — **written** (6 drills, 40 cases, key `queues`)

1 SERVED_ORDER (`deque` required) · 2 LAST_N (`maxlen`; slicing forbidden) ·
3 ROTATED_QUEUE (`deque.rotate`, which handles k > len and negative k where the slice
version does not) · 4 BFS_STEPS (`deque` required — DFS finds *a* path, not the shortest) ·
5 WINDOW_MAX (monotonic deque; `max` forbidden) · 6 TASK_ROUNDS (checkpoint).

**B** TWO_STACK_QUEUE — **written** (11 cases, key `two_stack_queue`): O(1)
amortised, and the transfer-only-when-dry rule. **B** CIRCULAR_BUFFER — **written**
(14 cases, key `circular_buffer`): fixed slots, and the empty-versus-full ambiguity.

## 2.7 Heap / priority queue — **written** (7 drills, 38 cases, key `heaps`)

1 K_SMALLEST · 2 K_LARGEST (returns descending, so no reversal) · 3 DRAIN_ORDER
(`heappop` required — draining a heap IS heapsort) · 4 K_CLOSEST (`nsmallest` with a key;
squared distance orders identically, so no `sqrt`) · 5 MAX_HEAP_ORDER (the negation trick;
`heapq` has no max-heap) · 6 MERGE_K (`heapq.merge`) · 7 TOP_K_FREQUENT (checkpoint).

The "when `sorted` is the better choice" judgement is in the LESSON rather than a drill —
a return value cannot show that k ≈ n makes the heap the wrong tool. **B** STREAMING_MEDIAN —
**written** (14 cases, key `streaming_median`): two heaps facing each other, and a
visible descending-input case that falsifies the intuitive design.

## 2.8 Linked list — **written** (6 drills, 32 cases, key `linked_lists`)

1 LENGTH · 2 TO_LIST · 3 REVERSED_CHAIN (re-point in place; building new nodes forbidden) ·
4 HAS_CYCLE (Floyd; a `set` of seen nodes forbidden) · 5 MERGE_CHAINS · 6 DROP_NTH_FROM_END
(checkpoint).

The node type is the unit's `preamble`: authored once, exec'd to build the cases, and
emitted verbatim into the starter file so a node the learner builds compares equal to one a
test passes in. **B** DOUBLY_LINKED_LIST — **written** (13 cases,
key `doubly_linked_list`): sentinels, and O(1) unlink by handle. **B** LRU_CACHE —
**written** (15 cases, key `lru_cache`): a dict of nodes plus that list, all O(1).

## 2.9 Tree — **written** (7 drills, 34 cases, key `trees`)

1 IN_ORDER · 2 PRE_ORDER · 3 POST_ORDER (a visible case shows post-order is NOT reversed
pre-order once the tree is bigger than three nodes) · 4 MAX_DEPTH · 5 LEVEL_ORDER
(recursion forbidden — depth-first cannot produce a level at a time) · 6 IS_BST (bounds
carried down; a visible case has every node correct against its own children and the tree
still not a search tree) · 7 DIAMETER (checkpoint).

`TreeNode` is the unit's preamble, same arrangement as 2.8. **B** BST — **written** (14 cases,
key `bst`): the delete with three cases. **B** TREE_CODEC — **written** (15 cases, key
`tree_codec`): pre-order with markers, and why in-order alone cannot round-trip.

## 2.10 Trie — **written** (4 drills, 29 cases, key `tries`)

1 WITH_PREFIX · 2 COUNT_PREFIXES (`startswith` forbidden — many queries against one word
list is where the structure pays) · 3 LONGEST_COMMON_PREFIX · 4 AUTOCOMPLETE (checkpoint).

Written against plain word lists rather than a Trie type on purpose: the skill is
recognising when to build one, and two of these are questions where you should not. **B** TRIE — **written**
(15 cases, key `trie_structure`): the end-of-word marker, and the delete with two
separate reasons to stop pruning.

## 2.11 Graph — **written** (6 drills, 38 cases, key `graphs`)

1 ADJACENCY · 2 DEGREES · 3 COMPONENTS (recursion forbidden) · 4 HAS_CYCLE_DIRECTED (three
states, not a visited set; a visible diamond case shows why) · 5 IS_BIPARTITE (a visible
case has a good first component and an odd ring second, so colouring from one start misses
it) · 6 REACHABLE_WITHIN (checkpoint).

List versus matrix is in the LESSON: it is a judgement, and a return value cannot show it.

## 2.12 Union-Find — **written** (5 drills, 41 cases, key `union_find`)

1 GROUP_COUNT · 2 SAME_GROUP (roots, not parents) · 3 REDUNDANT_EDGE (falls straight out of
what `union` returns) · 4 ISLANDS · 5 ACCOUNTS_MERGE (checkpoint).

Islands is deliberately here as well as under DFS: one problem with two correct algorithms
is its own skill. **B** UNION_FIND — **written** (14 cases, key
`union_find_structure`): path compression, union by size, and `find` returning the ROOT.

---

# 3. Algorithms

By name. Each carries the **recognition cue** — the thing in the question that should make
you reach for it — and three problems: obvious, disguised, then only-this-works.

| # | algorithm | cue | ladder |
| --- | --- | --- | --- |
| 3.1 | **Binary search** — **written** (6 drills, 44 cases, key `binary_search`) | sorted input, or a monotonic answer | FIND_INDEX · INSERT_POSITION (bisect_left, written not imported) · FIRST_OCCURRENCE · LAST_OCCURRENCE · ROTATED_MIN (compare the midpoint to the RIGHT end) · MIN_CAPACITY (checkpoint: **on the answer**) |
| 3.2 | **Two pointers** — **written** (5 drills + `two_sum_pairs`, 37 cases, key `two_pointers`) | sorted, find a pair or triple | PAIR_SUM · SORTED_SQUARES · MOST_WATER · THREE_SUM (skipping duplicates twice over) · SORT_COLORS (checkpoint, Dutch flag). `two_sum_pairs` beside it is the UNSORTED version, which wants a dict — telling them apart is the skill |
| 3.3 | **Sliding window** — **written** (5 drills, 36 cases, key `sliding_window`) | "contiguous" + "longest/shortest" | MAX_SUM_K (fixed) · LONGEST_UNIQUE · LONGEST_ONES (the same window, different validity test) · ANAGRAM_STARTS (counts, and the zero-key trap) · MIN_WINDOW (checkpoint) |
| 3.4 | **DFS** — **written** (5 drills, 37 cases, key `dfs`) | explore fully, or "all paths" | FLOOD_FILL · ISLAND_SIZES · ALL_PATHS (carry the route, undo on the way back) · HAS_PATH (mark on push, or a cycle never ends) · LONGEST_REGION (checkpoint, memoised DFS) |
| 3.5 | **BFS** — **written** (5 drills, 46 cases, key `bfs`) | fewest steps, unweighted | DISTANCES_FROM · ROT_TIME (multi-source, every start seeded at 0) · LADDER_LENGTH (an implicit graph of generated words) · NEAREST_EXIT · MIN_MULTIPLY (checkpoint) |
| 3.6 | **Backtracking** — **written** (5 drills, 27 cases, key `backtracking`) | "all possible", "every combination" | SUBSETS · PERMUTATIONS · COMBINATION_SUM (reuse by recursing at the same index) · PARTITION_EQUAL (prune on an odd total) · N_QUEENS (checkpoint) |
| 3.7 | **Dijkstra** — **written** (5 drills, 34 cases, key `dijkstra`) | shortest path, weighted, non-negative | SHORTEST_COSTS · SHORTEST_TO (the first pop is final) · SLOWEST_ARRIVAL (a maximum over minima) · MAX_PROBABILITY (the same algorithm maximising) · CHEAPEST_WITH_STOPS (checkpoint: where settle-once stops being valid) |
| 3.8 | **A\*** — **written** (5 drills, 32 cases, key `a_star`) | shortest path with a usable heuristic | MANHATTAN · GRID_PATH_COST · EXPANDED_COUNT (the payoff, measured) · IS_ADMISSIBLE · PATH_WITH_HEURISTIC (checkpoint: three weights on one maze, showing an overestimate reporting 10 where the truth is 8) |
| 3.9 | **Topological sort** — **written** (5 drills, 34 cases, key `topological`) | dependencies, ordering | IN_DEGREES · TOPO_ORDER (Kahn's) · CAN_FINISH (the cycle check is free) · DEPTH_LEVELS (the build time with unlimited parallelism) · ALIEN_ORDER (checkpoint: infer the dependencies first) |
| 3.10 | **Dynamic programming** — **written** (5 drills, 36 cases, key `dynamic_programming`) | overlapping subproblems | CLIMB_WAYS · HOUSE_ROBBER · COIN_CHANGE (a visible case shows the greedy giving 3 where the answer is 2) · LONGEST_INCREASING (subsequence, not subarray) · EDIT_DISTANCE (checkpoint) |
| 3.11 | **Greedy** — **written** (5 drills, 41 cases, key `greedy`) | a locally safe choice, provably | CAN_JUMP · MIN_JUMPS · GAS_STATION (proving a whole prefix can be skipped) · MAX_MEETINGS (sort by END) · MIN_PLATFORMS (checkpoint) |
| 3.12 | **Sorting algorithms** — **written** (5 drills, 34 cases, key `sorting_algorithms`) | you are asked *how* sort works | MERGE_SORT · PARTITION (three-way, so duplicates do not degrade it) · QUICKSELECT · COUNTING_SORT (sidesteps the comparison bound) · STABLE_BY_KEY (checkpoint) |
| 3.13 | **Prefix sums** — **written** (5 drills, 38 cases, key `prefix_sums`) | repeated range queries | RUNNING_SUM · RANGE_SUMS · PIVOT_INDEX · PRODUCT_EXCEPT_SELF (no division, so a zero needs no special case) · REGION_SUM (checkpoint, 2-D inclusion-exclusion). "Subarray sum equals k" is unit 2.3's checkpoint, deliberately |
| 3.14 | **Kadane** — **written** (5 drills, 34 cases, key `kadane`) | max contiguous subarray | MAX_SUBARRAY · MIN_SUBARRAY · MAX_SUBARRAY_RANGE (the start index moves only on a restart) · MAX_PRODUCT (carry the minimum too) · MAX_CIRCULAR (checkpoint, where the all-negative case breaks the clever half) |
| 3.15 | **Monotonic stack** — **written** (5 drills, 35 cases, key `monotonic_stack`) | "next greater/smaller" | PREVIOUS_SMALLER (answered on the way in) · NEXT_SMALLER_INDEX (on the way out) · TRAPPED_WATER · STOCK_SPAN (next-greater in disguise) · MAX_OF_MINS (checkpoint) |
| 3.16 | **Bit manipulation** — **written** (5 drills, 33 cases, key `bits`) | pairs cancelling, subsets, flags | LONELY_VALUE (XOR) · COUNT_BITS (`x & (x-1)`) · IS_POWER_OF_FOUR · SUBSET_AT (an integer IS a subset) · SINGLE_OF_THREE (checkpoint: counting bits mod 3) |
| 3.17 | **Floyd cycle detection** — **written** (5 drills, 27 cases, key `floyd`) | a cycle with O(1) space | CYCLE_LENGTH · CYCLE_START (the second phase) · FIND_DUPLICATE (a cycle in a function, with no list in sight) · MEETING_POINT (a visible case proves the meeting is NOT the entrance) · HAPPY_NUMBER (checkpoint) |
| 3.18 | **Intervals** — **written** (5 drills, 44 cases, key `intervals`) | ranges that may overlap | MERGE_INTERVALS · INSERT_INTERVAL · MIN_ROOMS (starts and ends sorted separately) · ERASE_OVERLAPS (sort by END; a visible case shows sorting by start giving 2 where the answer is 1) · FREE_SLOTS (checkpoint) |

Some problems appear in two places on purpose — "subarray sum equals k" under both Dict
and Prefix sums, "number of islands" under both DFS and Union-Find. Recognising that two
algorithms solve one problem is a separate skill from knowing either.

---

# 4. Industry practices

The existing bank. Ninety minutes, four progressive levels, a class you must keep
refactoring as requirements arrive. This is where everything above gets used at once under
a clock.

| problem | cases | the level-4 turn | diff |
| --- | --- | --- | --- |
| `banking` | 41 | merge accounts + historical balances | 4 |
| `cloud_storage` | 46 | collision-aware restore | 4 |
| `in_memory_db` | 50 | backup/restore with re-anchored TTLs | 4 |
| `file_hosting` | 58 | rollback | 4 |
| `file_system` | 60 | symbolic links resolved mid-path | 5 |

`file_system` last: the only one built on a tree, so the only one where a level-1
data-structure choice costs you level 3.

---

## Totals

| category | subtopics | exercises | written |
| --- | --- | --- | --- |
| 1. Basic Python | 8 | 92 drills, 8 of them checkpoints | 92 |
| 2. Data Structures | 12 | 90 | 90 |
| 3. Algorithms | 18 | 92 | 92 |
| 4. Industry practices | 5 | 5 × 4 levels | 5 |

279 exercises designed, and every one of them written — which is the number of keys `./pfs list`
prints, because a drill is a problem in its own right. Every one earns its place by
introducing something the one before it did not, and the prerequisite order means you
never face a rung you have no business standing on.

The counts here are the design. `curriculum/graph.py` is what the platform actually reads,
and `docs/BANK.md` — generated, never hand-edited — is what is in the bank today.

## Prerequisites, in one place

```
1.1 for loops        → (nothing)
1.2 strings          → 1.1
1.3 ints             → (nothing)
1.4 functions/lambda → 1.1
1.5 unpacking        → 1.1
1.6 truthiness       → (nothing)
1.7 sorting          → 1.1, 1.4
1.8 errors           → (nothing)
2.1 list, 2.2 tuple  → 1.1
2.3 dict, 2.4 set    → 1.1, 1.6
2.5 stack, 2.6 queue → 2.1
2.7 heap             → 1.7, 2.3
2.8 linked list      → 2.1
2.9 tree             → 2.8, 3.6 (recursion)
2.10 trie            → 2.3, 2.9
2.11 graph, 2.12 uf  → 2.3, 2.6
3.1 binary search    → 1.7
3.2, 3.3             → 2.1, 2.3
3.4 dfs, 3.5 bfs     → 2.11
3.7 dijkstra         → 3.5, 2.7
3.8 a*               → 3.7
3.9 topo sort        → 3.4, 2.6
3.10 dp              → 3.6
4.* industry         → 2.3, 2.7, 1.7
```

## Build order

1. ✓ **all of category 1** — smallest, no prerequisites, and it proved the drill shape:
   authored per unit, split into one problem per drill.
2. ✓ **3.2 two pointers**, one problem — proved that a full problem can live inside a
   subtopic directory beside its drills.
3. **2.3 dict** and **2.4 set** — the highest-leverage structures in interviews, and the
   first "use it, then build it" pair.
4. **3.1 binary search** — the first algorithm authored as a set, and the cue is
   unambiguous.
5. Outward from there along the prerequisite graph.
