# Platform plan — from one problem shape to a practice platform

**Status:** partly implemented. Written 2026-08-18; the Progress table at the bottom is
the record of what has landed since.
**Companion:** `docs/STATE.md` records what exists. This file records where it is going
and what must be true before each step counts as done. `docs/CURRICULUM.md` supersedes the
pedagogy here — problems grouped by category and difficulty is a filing system, not a
curriculum — and carries the ladder's own build order.

---

## Context

The rig currently hosts exactly one *shape* of problem: the CodeSignal Industry Coding
Framework format — one problem, four progressive levels, a class of methods, a 90-minute
clock, 600 points. Five problems, 255 cases, all through both verification gates.

The goal is to host the other shapes developers actually prepare against — LeetCode-style
single functions, data-structure design, algorithm drills — and, for every problem, to
serve not just a worked solution but the **approach** and an **explanation**, because a
developer who cannot yet solve it also cannot yet read the solution.

Two things make this more than "add more problems":

1. **Correctness at scale.** The rig's central discipline is that no case ships unless it
   has passed a differential gate against a reference implementation and a mutation gate.
   That discipline is currently *unreproducible for three of the five existing problems*,
   because policy deletes the oracle after use. At 200 problems, an unverifiable suite is
   a platform that lies.
2. **The front end is a single 1,153-line file** with a hardcoded five-card picker and no
   search. It is well-commented and coherent, but there is no seam to grow along.

---

## What we have (verified by exploration, 2026-08-18)

Only **three** hard couplings to the progressive shape exist. Nothing anywhere hardcodes
"four levels" — `Problem.max_level` is derived.

| Coupling | Where | Cost to open |
| --- | --- | --- |
| Class-with-methods dispatch | `harness/runner.py:185,220-228`; `Problem.class_name` `model.py:133` | ~15 lines: replace `load_solution(path, class_name)` with a **subject factory** — a class instance for class kinds, the *module itself* for function kinds. `getattr(subject, name)` then finds a top-level function unchanged. |
| The 600 constant | `model.py:215-217` (a hard validation error), `runner.py:147` (literal) | Add `Problem.total_points: int = 600`, gate the rule on kind. |
| No representation for "untimed" | `session.py:56-66` — `budget_minutes * 60 - elapsed`, so `--minutes 0` expires instantly | `budget_minutes: int | None`, `expired` returns `False` when `None`. |

**Reusable verbatim, no changes:** `harness/expect.py` (the whole comparison engine),
`harness/examples.py`, `harness/contract.py` (self-neutralising when there is one level),
`scaffold.archive`, `scaffold.defined_methods`, `report.stuck_streaks`,
`report.tag_failures`, `validate.differential`, the per-operation `SIGALRM` timeout
(`runner.py:158-182` — wraps a callable, knows nothing about shape).

**Progressive-only by design:** `scaffold.py`'s header/stub templates, `validate.py`'s
per-level structural rules, `report.py`'s level-budget table, the unlock logic in
`cli.py:441-470`.

---

## Bugs found during exploration — fix before scaling

These are defects in what exists, not consequences of the new direction. Ordered by what
the new direction actually triggers.

| # | Bug | Anchor | Why it matters now |
| --- | --- | --- | --- |
| **B1** | **Case arguments are shared across every run.** `Op` is frozen with `args: tuple` and `ALL_CASES` is module-level, so the *same objects* are passed to every case in the process. A solution that mutates its input (`nums.sort()`, in-place `rotate`) corrupts every later case — permanently, in the long-running `./pfs ui`. | `model.py:22-32`; `runner.py:323-325` | Zero mutable args in the bank today. **LeetCode problems land this immediately** — in-place mutation is a whole problem genre. Deep-copy args before the call. |
| **B2** | Operator-precedence bug in the signature-mismatch heuristic: `"positional argument" in message or "argument" in message and bound.__name__ in message` parses as `A or (B and C)`. And `bound.__name__` raises `AttributeError` for a callable without one, escaping the `except TypeError` and **aborting the whole run**. | `runner.py:342` | Function-shaped problems make the no-`__name__` callable much more likely. |
| **B3** | `loader.BROKEN` is written and **never read anywhere**. A problem whose module fails to import silently vanishes from the bank. Also catches `Exception`, so a `BaseException` in one problem takes the bank down. | `loader.py:37,55-56` | At five problems you notice. At two hundred it is silent data loss. |
| **B4** | `answer.py`'s `_LEVEL_BANNER` cannot tell a section banner from a prose comment. `solutions/file_system.py:107` contains `# Level 4 is entirely about…`, so `slice_upto(src, 1..3)` **silently drops `_resolve` and `_locate`** — every method calls them. The output still parses, so `./pfs answer --level 2` would serve confidently-broken code. | `answer.py:33,89-114` | Masked only because `resolve()` prefers snapshots. Any problem with prose banners and no snapshots hits it. |
| **B5** | Picker payload is O(problems × sessions) **disk reads** — `all_sessions()` is called inside the per-problem comprehension, and it JSON-parses every file in `sessions/`. | `webui/server.py:149` | 100 problems × 500 sessions = 50,000 parses per picker load. Two-line fix. |
| **B6** | `_source_fingerprint` hashes `harness/` and `webui/` but **not `problems/`**, while `loader.py:30` returns `sys.modules`-cached modules. Editing a test case while the server runs silently does nothing, with no stale banner. | `webui/server.py:63` | Authoring problems becomes the main activity. The staleness guard is blind to the files being edited most. |
| **B7** | Stale-detection banners only fire on responses whose *top level* is a state payload. `/api/run` and `/api/finish` nest it under `state`. | `index.html:335-336` | A user who starts a session then only runs tests never sees a banner. |
| **B8** | `cli.py:470` prints **"✦ All four levels clear."** for any problem that clears its last level. | `cli.py:470` | Wrong the moment a one-level problem exists. |
| **B9** | `.gitignore` ignores `/solutions/*.py` but **not `solutions/<key>/`** — the per-level snapshot layout `answer.py` *prefers*. | `.gitignore:3` | Contradicts `solutions/README.md:3` and `STATE.md:14`. One `git init` from leaking answers. |
| **B10** | ~~`markdown.py` has no ordered lists, no italics, no blockquotes, no `<hr>`, and a fenced code block inside a list item closes the list.~~ **Mostly fixed.** Emphasis, ordered lists, `<hr>` and wrapped list items all render; a wrapped item used to end the list early and split a `**bold**` span across the break. Backslash escapes were added later, when a lesson about A* had no way to write its own name. Still missing: blockquotes, and a fenced code block inside a list item. Nothing in the bank uses either. | `webui/markdown.py` | The Lesson tab forced this: 69 `*emphasis*` spans across the eight lessons reached the reader as asterisks, and the answer keys rendered 50 literal `<p>---</p>`. Both are now covered by a corpus test over all 38 rendered documents. |

---

## The correctness problem, and the policy change it forces

The rig's rule is: write the oracle outside the repo, run both gates, **delete the
oracle** (`SKILL.md:147`, `STATE.md:14`, `solutions/README.md:3`).

The consequence, measurable today:

- `./pfs validate` runs the differential gate for **2 of 5** problems. For `banking`,
  `file_hosting` and `in_memory_db` it prints *"no reference solution — expected values
  are hand-derived and unverified by execution."*
- `tools/mutation_check.py` holds **98 hand-written `(find, replace)` pairs quoting
  oracles that no longer exist**. Run against a fresh oracle it degrades to all-SKIP.
  It is unre-runnable by construction.

That was a defensible trade at five problems authored by the person being tested. It does
not survive a platform whose promise is correct solutions, and it directly contradicts
"ensure completeness and correctness of the solutions."

**Proposed change:** solutions become **permanent, gitignored oracles**. `solutions/` is
already gitignored and `./pfs validate` already picks them up automatically. Keeping them
means every suite stays verifiable forever, and CI-style re-validation of the whole bank
becomes one command. The original worry — "an answer one directory away changes how you
attempt a problem cold" — is now handled properly by `./pfs answer`'s live-session
refusal, which did not exist when that rule was written.

**Second change:** replace the per-problem textual mutation catalogue with a **two-tier
mutation engine**. Exploration found ~20 recurring categories covering ~85 of the 98
hand-written mutants:

boundary flips (`<`↔`<=`), missing/reversed tie-break, dropped sort, forgotten top-N cap,
`startswith`→`in`, truthiness on a value so `0`/`""` reads absent, duplicate-create
overwrites, single-generation snapshot, shallow-copy snapshot, restore merges instead of
replacing, restore-with-no-backup wipes, rejected op leaves state changed, return
semantics inverted, failure convention flipped, self-referential op allowed, partial
merge, missing ownership check, counting the wrong entity, silent no-op, off-by-one in an
id sequence, rounding direction, string containment, no cycle detection.

Tier 1 is an AST mutator driven by that registry, applied automatically to every problem's
oracle. Tier 2 is a short per-problem list for genuinely novel rules. This turns ~24,000
projected lines of brittle string literals into a shared engine.

---

## Problem taxonomy

### Kinds (the execution shape)

| kind | interface | levels | timing | status |
| --- | --- | --- | --- | --- |
| `progressive` | class of methods, grows per level | 4 | 90 min | **exists** — 5 problems |
| `function` | one top-level function, many I/O cases | 1 | per-problem target, untimed by default | new |
| `design` | class of methods, all at once (LRU, MinStack, Trie, RateLimiter) | 1 | per-problem target | new |

`design` reuses the existing class dispatch unchanged; it is `progressive` with one level.
`function` is the only kind needing the subject-factory seam.

### Categories

**Python fluency** — the "can you actually write Python" tier that interviews assume and
most prep skips: string and list manipulation, dict/set idioms, slicing, unpacking,
`sorted(key=…)` with compound keys, comprehensions, `collections` (`defaultdict`,
`Counter`, `deque`), `itertools`, generators, `dataclasses`, context managers.

**Data structures** — arrays, strings, hash maps, stacks, queues, heaps, linked lists,
binary trees, tries, graphs, union-find.

**Algorithms** — two pointers, sliding window, binary search (including on the answer),
recursion and backtracking, dynamic programming, greedy, BFS/DFS, topological sort,
intervals, prefix sums, bit manipulation.

**Industry / practical** — the CodeSignal flavour and the closest transfer to real work:
parsing and tokenising, date and time arithmetic, path and file-name manipulation, log
processing, tabular reshaping, config merging, retry and backoff, rate limiting,
pagination, deduplication and diffing.

Each problem carries `kind`, `category`, `difficulty` (easy/medium/hard), and topic tags.
Existing `tag_glossary` stays what it is — *per-case concept* tags, which is a different
axis and the one the practice loop already reads.

---

## Teaching artifacts — the Solution / Approach / Explanation requirement

Three tabs, three sources, all review-gated exactly as `DECISIONS.md` is:

| tab | source | content |
| --- | --- | --- |
| **Solution** | `solutions/<key>.py` | the verified oracle; already built and gated |
| **Approach** | `problems/<key>/APPROACH.md` (new) | the idea before the code: what to notice, why this data structure, the invariant, complexity, and what the naive attempt gets wrong |
| **Explanation** | `problems/<key>/EXPLANATION.md` (new) | a walkthrough of the solution as written, in the order a reader meets it, plus the traps |

Today the approach narrative is smuggled into the module docstrings of gitignored solution
files — and `answer.py:67-86` **actively strips those docstrings when serving**. Real
teaching prose is generated, hidden, then thrown away by the code that serves it. These
two files fix that.

No longer blocked on **B10**: numbered steps, emphasis, horizontal rules and wrapped list
items all render now. Code inside a list item still does not, which constrains how a
worked example can be laid out inside a numbered step but does not prevent the prose.

---

## Build order

Each step lands with tests, and nothing counts as done until `tests/run_all.sh` is green.

**Step 0 — stop the bleeding.** B1 (arg copying), B2, B3, B8. Pure bug fixes to the
existing rig, no new concepts. Add regression tests, especially a case whose solution
mutates its input.

**Step 1 — the kind seam.** `Problem.kind`, `total_points`, defaults on `Case.level`,
`Method.level`, `Level.budget_minutes`, `Level.weight`, `class_name`. Subject factory in
`runner.py`. Gate `validate.py`'s per-level rules on kind. Per-kind scaffold templates.
`budget_minutes: int | None`. All five existing problems must remain byte-identical in
behaviour — this is the invariant to test hardest.

**Step 2 — expectation primitives for algorithm problems.** `Satisfies(predicate)` for
"any valid answer", set comparison in `Unordered`, and a way to assert on **mutated
arguments** — currently only the return value is graded (`runner.py:380`), which cannot
score `rotate`, `moveZeroes`, `sortColors` at all.

**Step 3 — first `function` problems, one per category.** Four problems, fully gated, to
prove the seam before volume. Plus `APPROACH.md` and `EXPLANATION.md` for each, which
forced most of B10 already.

**Step 4 — the mutation engine.** Tier-1 AST mutator over the category registry; port the
five existing catalogues onto it; keep the residue as tier 2.

**Step 5 — scale the surfaces.** Lazy `PROBLEM_META` index (B3, B5, B6), a problem browser
with search and filters, and tests that are **properties over the bank** rather than
hardcoded key lists — `api_test.py:160-165` asserts the exact five keys, and
`api_test.py:641-650` holds a hand-written per-problem leak vocabulary that `KeyError`s on
any new problem.

**Step 6 — volume**, in category batches, each batch through both gates.

---

## Progress

`docs/BANK.md` is generated (`python3 tools/bank_report.py --write`) and is the
authoritative count. This section tracks the steps.

| step | state | notes |
| --- | --- | --- |
| 0 — stop the bleeding | **done** | B1, B2, B3, B8, B9 fixed with regression tests. B10 mostly fixed (blockquotes and code-in-list-item remain, both unused). B5, B6, B7 outstanding. |
| 1 — the kind seam | **done** | `kind`, `total_points`, `category`, `difficulty`, `topics`; subject factory; kind-gated validation and scaffolding; kind-aware scoring. All five existing problems byte-identical in behaviour, both oracles still agree. |
| 2 — expectation primitives | not started | `Satisfies(predicate)`, set comparison, asserting on mutated arguments. |
| 3 — first problems | **1 of 8–12** | `two_sum_pairs` (function, algorithms, easy) — 15 cases, gate 1 clean, `APPROACH.md` + `EXPLANATION.md`. |
| 4 — mutation engine | not started | Tier-1 AST mutator over the ~20 recurring categories. |
| 5 — scale the surfaces | partly | Test assertions are now properties over the bank rather than hardcoded key lists. Lazy index and problem browser outstanding. |
| 6 — volume | not started | |

### Debt this created, recorded rather than forgotten

- **Three problems have no oracle** (`banking`, `file_hosting`, `in_memory_db`), so their
  suites cannot be re-verified. `tools/bank_report.py` exits non-zero while that is true.
- **No problem has teaching material except `two_sum_pairs`.** The five progressive
  problems need `APPROACH.md` and `EXPLANATION.md` too; `validate.py` only requires them
  for non-progressive kinds so far, which is a deliberate staging choice, not a judgement
  that they are optional.
- **`banking` and `cloud_storage` level 1 have 6 hidden cases** against a target of 8.
  Previously invisible: the warning fired below 4 while its own text said "aim for 8+".
- **Mutation catalogues are still per-problem text.** `two_sum_pairs` has none.

## Verification

Per problem, before it ships:

```bash
./pfs validate <key> --against solutions/<key>.py     # differential: every case agrees
python3 tools/mutate <key>                            # mutation: every mutant caught
```

Per change to the rig:

```bash
tests/run_all.sh          # structural + backend + browser
./pfs validate            # every problem, differential where an oracle exists
```

The bank status table must be **generated**, not hand-maintained. It is currently
duplicated in three places (`STATE.md:38-44`, `README.md:138-144`, `README.md:183-189`)
with a hand-counted total at `README.md:151`, and has **already drifted** —
`solutions/README.md:42` says `file_hosting` is 57 cases, the other two say 58.

---

## Decisions taken (2026-08-18)

1. **Oracle policy — solutions are permanent, gitignored oracles.** `solutions/<key>.py`
   stays for every problem, forever. This supersedes "delete the oracle when done"
   (`SKILL.md:147`) and the "no reference solutions anywhere" line in `STATE.md:14`; both
   must be rewritten, and `.gitignore` must cover `solutions/<key>/` too (**B9**).
   Backfill required for `banking`, `file_hosting`, `in_memory_db` — the three whose
   differential gate is currently dormant.
2. **Kinds in the first pass — `function` + `design`.** `design` is a one-level class
   problem, so it needs no new dispatch; `function` needs the subject-factory seam.
3. **First pass — 8–12 problems, breadth-first**, two or three per category, each fully
   gated and each with `APPROACH.md` and `EXPLANATION.md`. Surfaces (browser, lazy index)
   come after, since the current picker holds to roughly fifteen problems.
4. **Language — Python only, standard library only**, matching the existing rig.
