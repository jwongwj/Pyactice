# Layout — what you look at, and what you never need to

Three kinds of directory, and it is worth knowing which is which before reading the tree:

| | |
| --- | --- |
| **yours** | you edit these; they are gitignored and archived, never deleted |
| **read** | you read these while practising — lessons, statements, and after the fact, answers |
| **machinery** | you never open these unless you are extending the platform |

---

## The tree

```
Pyactice/
│
├── pfs                          the only entry point. `./pfs ui` opens the browser IDE
│
├── curriculum/                  READ · the ladder, ordered
│   ├── graph.py                 the graph: subtopics, prerequisites, and the problem
│   │                            keys each subtopic owns. One file
│   │
│   ├── 1-basic-python/          ✓ written — 8 units, 92 drills, 314 cases
│   │   ├── 01-for-loops/        ✓ 12 drills, 40 cases
│   │   │   ├── LESSON.md        ← read this first. One per unit, shared by every
│   │   │   │                      drill the unit splits into
│   │   │   └── unit.py          the drills, their constraints and their cases, one
│   │   │                        self-contained file. `PROBLEMS = split(UNIT)` at the
│   │   │                        foot of it is what makes twelve problems out of one unit
│   │   ├── 02-strings/          ✓ 15 drills, 49 cases
│   │   ├── 03-ints/             ✓ 16 drills, 59 cases
│   │   ├── 04-functions-lambda/ ✓ 13 drills, 42 cases
│   │   ├── 05-unpacking/        ✓ 9 drills, 28 cases
│   │   ├── 06-truthiness/       ✓ 10 drills, 36 cases
│   │   ├── 07-sorting/          ✓ 8 drills, 28 cases
│   │   └── 08-errors/           ✓ 9 drills, 32 cases
│   │
│   ├── 2-data-structures/       planned — `graph.py` already carries the ladder, the
│   │   ├── 01-list/             directories arrive with the content. The shape each takes:
│   │   │   ├── LESSON.md
│   │   │   ├── unit.py               the "use it" drills and their cases
│   │   │   └── build-dynamic-array/  ← "build it" problems get their own directory
│   │   │       ├── problem.py        its cases live here, not in a sibling tests.py:
│   │   │       │                     a numbered directory is not an importable package
│   │   │       ├── statement.md
│   │   │       ├── APPROACH.md       how to think about it
│   │   │       └── EXPLANATION.md    the solution, line by line
│   │   ├── 02-tuple/
│   │   ├── 03-dict/         (+ build-hash-map/)
│   │   ├── 04-set/
│   │   ├── 05-stack/        (+ build-min-stack/)
│   │   ├── 06-queue-deque/  (+ build-circular-buffer/)
│   │   ├── 07-heap/         (+ build-median-stream/)
│   │   ├── 08-linked-list/  (+ build-lru-cache/)
│   │   ├── 09-tree/         (+ build-bst/)
│   │   ├── 10-trie/         (+ build-trie/)
│   │   ├── 11-graph/
│   │   └── 12-union-find/   (+ build-union-find/)
│   │
│   └── 3-algorithms/            planned, bar one
│       ├── 01-binary-search/
│       │   ├── LESSON.md             ← the recognition cue for this algorithm
│       │   ├── classic-search/
│       │   ├── first-last-occurrence/
│       │   ├── rotated-array/
│       │   └── min-ship-capacity/    binary search on the answer
│       ├── 02-two-pointers/
│       │   └── two_sum_pairs/        ✓ written — 15 cases. problem.py, statement.md,
│       │                               APPROACH.md, EXPLANATION.md
│       ├── 03-sliding-window/
│       ├── 04-dfs/
│       ├── 05-bfs/
│       ├── 06-backtracking/
│       ├── 07-dijkstra/
│       ├── 08-a-star/
│       ├── 09-topological-sort/
│       ├── 10-dynamic-programming/
│       ├── 11-greedy/
│       ├── 12-sorting-algorithms/
│       ├── 13-prefix-sums/
│       ├── 14-kadane/
│       ├── 15-monotonic-stack/
│       ├── 16-bit-manipulation/
│       ├── 17-floyd-cycle/
│       └── 18-intervals/
│
├── problems/                    READ · 4. Industry practices only
│   ├── file_hosting/            90 minutes, four progressive levels
│   ├── cloud_storage/
│   ├── in_memory_db/
│   ├── banking/
│   └── file_system/
│
├── workspace/                   YOURS · gitignored, one directory per problem key
│   ├── strings.extension/
│   │   ├── solution.py               ← the one drill you are on. Fill in the stub
│   │   └── previous-attempts/        every retake archived, never deleted
│   ├── sorting.standings/            the unit's checkpoint, keyed like any other drill
│   │   └── solution.py
│   ├── two_sum_pairs/solution.py
│   └── file_hosting/solution.py
│
├── solutions/                   READ (after) · gitignored. `./pfs answer` serves these
│   ├── for_loops.py  strings.py  ints.py  functions_lambda.py  unpacking.py
│   ├── truthiness.py  sorting.py  errors.py     one per UNIT, not one per drill
│   ├── two_sum_pairs.py  cloud_storage.py  file_system.py
│   └── file_system/level1..4.py                per-level snapshots
│
├── docs/                        READ
│   ├── CATALOGUE.md             the whole ladder: 4 categories, 233 designed exercises
│   ├── CURRICULUM.md            how the platform is designed to teach
│   ├── BANK.md                  GENERATED. Coverage and gaps, never hand-edited
│   ├── PLAYBOOK.md              how to attack the industry-practice format
│   ├── ASSESSMENT_BRIEF.md      what the real CodeSignal assessment is
│   └── LAYOUT.md                this file
│
├── harness/                     MACHINERY · model, loader, units, constraints, runner,
│                                session, CLI
├── webui/                       MACHINERY · the browser IDE
├── tools/                       MACHINERY · bank_report.py, mutation_check.py
├── tests/                       MACHINERY · run_all.sh + backend + browser suites
└── sessions/                    MACHINERY · your event log. Feeds `./pfs stats`
```

---

## What you actually touch

**One file per drill.** A drill is one function, so the workspace file holds that one
function's stub and nothing else:

```python
# workspace/strings.extension/solution.py

def extension(path: str) -> str:
    """The part after the LAST dot, or "" when there is no dot."""
    raise NotImplementedError("EXTENSION")
```

Authoring and practising disagree about the unit boundary on purpose. Fifteen one-idiom
drills as fifteen directories would be sixty files holding fifteen one-line exercises,
and nobody would ever browse it — so a unit is authored as a single `Problem` in a single
`unit.py`, its cases beside the drills they belong to. But a unit is the wrong thing to
practise *against*: one score, one session and one file of fifteen functions, so
"I want to drill `rpartition`" means opening all fifteen, and progress cannot say which
drills you have actually cleared.

So `harness/units.py` closes the gap. `split(UNIT)` turns the one authored unit into N
problems — one per drill, keyed `<unit>.<function>` (`strings.extension`,
`sorting.standings`) — each holding exactly one method, only the cases that exercise it,
and its own session, workspace file and progress record. The loader reads `PROBLEMS`, so
the unsplit key is not in the bank: there is no `strings` to start, only its fifteen
drills.

**The constraint is in the task, never hidden.** The stub carries the docstring; the task
carries the signature, the docstring and the constraint, generated from the drill itself
so it cannot drift from what the grader checks. Read it with `./pfs spec <drill>` or the
browser's Task tab. A constraint you could not have known about is a trick question,
which is the same rule the industry problems already follow about hidden test cases.

**The lesson belongs to the unit, not the drill.** `LESSON.md` sits beside `unit.py`, and
every drill split out of that unit points back at it — the Lesson tab in the browser, a
path printed under `./pfs spec`. Three separate documents on purpose: the lesson teaches
the idiom, the task states the job, the worked answer stays behind `./pfs answer`.
Collapsing any two of them is how a lesson ends up handing over the solution.

The **build-it** problems and every algorithm problem use the familiar shape instead: one
problem, one statement, one `solution.py`.

---

## Reading order, per unit

```
1. LESSON.md              the idioms, one screen, runnable examples
2. ./pfs start <drill>    writes the stub file; `./pfs spec` prints the task
3. ./pfs test             pass/fail for that drill, plus the constraint verdict
4. the unit's last drill  its checkpoint: no constraints, several idioms at once
5. ./pfs answer <drill>   that one function, lifted out of the unit's oracle
```

Step 3 is where the platform differs from every other practice site. Two separate
verdicts, never conflated — the cases say whether it works, the constraints say whether
it was the point:

```
── not the point of the drill ──────────────────────────────────────────

  ○ SENTENCE   correct, but
      This drill wants `join`.
      → " ".join(words)
      You used `augassign`.  (line 5)
      → building a string with += copies it every time

  These do not cost you a case. They are what the drill is for.
```

A violated constraint never blocks you and never costs a case: a drill clears when its
cases pass, and a unit is cleared when every drill in it has, its checkpoint included.
The violation is still reported every run, because a drill you passed by hand-rolling the
loop taught you nothing about the idiom it exists for.

---

## Commands you need

```bash
./pfs ui                             the browser IDE — start here
./pfs list                           the whole bank, drills included
./pfs start <key>                    begin an attempt; drills are untimed
./pfs spec <key>                     the task, its constraint and its examples
./pfs test                           run the current drill or problem
./pfs answer <key> [--level N]       worked solution; refuses while a clock is running
./pfs stats                          weakest concepts across every session
```

`./pfs list` is long now — ninety-eight keys — which is what the prerequisite graph in
`curriculum/graph.py` is for: it answers "what next" instead of making you choose from a
list of a hundred. The browser IDE reads that graph; the CLI takes the key it gives you.

---

## Three decisions in this layout worth stating

**Drills are authored per unit and practised per drill.** One `unit.py` per subtopic keeps
the drills and their cases in one browsable file; `split(UNIT)` gives each drill the key,
session and progress record it needs to be practised on its own. The two shapes disagree,
and `harness/units.py` is the whole of the disagreement — nothing downstream of the loader
knows a unit was ever one object. Anything with a statement and an approach worth writing
down — every build-it, every algorithm problem — gets its own directory instead.

**Categories 2 and 3 mix both shapes, on purpose.** `2-data-structures/07-heap/` will have
the "use it" drills in `unit.py` and `build-median-stream/` as a full problem beside them.
Using a heap and building one are different exercises, and they belong in the same place
because they are the same subtopic.

**The five industry problems stay in `problems/` for now.** Moving them under
`curriculum/4-industry-practices/` would be tidier and is the eventual intent, but it
touches problem-key resolution, `solutions/` paths, every session record and both test
suites at once. That is a migration to do deliberately, on its own, not as a side effect
of adding category 1. `graph.py` can place them in the ladder without moving a file.

---

## For whoever extends this

Adding a unit or a problem means: write the content, then pass both gates before it
counts. Two subagents exist for exactly this and keep the oracle out of the main
session's context:

- **`oracle-verifier`** — runs the differential and mutation gates and reports a per-gate
  verdict.
- **`disclosure-auditor`** — checks that every tie-break in `DECISIONS.md` is demonstrated
  by a visible case, and that nothing has drifted upward from statement to answer key.

A unit's oracle is one file for the whole unit — `solution_key` points every drill at it
and `harness/answer.py` extracts the single function — so ninety-two drills need eight
oracle files, not ninety-two.

`python3 tools/bank_report.py` regenerates `docs/BANK.md` and exits non-zero while
anything is unverifiable, so it can gate a change. The status tables are never
hand-maintained: they were, in three places, and had already drifted.
