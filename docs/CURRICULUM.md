# Curriculum design — a ladder, not a bank

**Status:** built — categories 1 and 4, the prerequisite graph, and the curriculum view in
the browser. Categories 2 and 3 are designed and unwritten. Supersedes the framing in
`docs/PLATFORM_PLAN.md`, which planned a *bank of verified problems*. A bank is a test
suite. This describes the learning structure that sits on top of it.

`curriculum/graph.py` is the executable form of this file and wins any disagreement with
it. `docs/CATALOGUE.md` holds the drill-by-drill catalogue and the reason each rung
exists; `docs/BANK.md` is the generated ledger of what is actually authored.

---

## The problem with the previous framing

`PLATFORM_PLAN.md` got the engineering right and the pedagogy wrong. It planned problems
grouped by category and difficulty, which is a filing system — you can browse it, but it
cannot answer the only question a learner actually has: **what should I do next?**

Two more specific failures:

**A "tips and tricks" drill cannot be graded on its answer alone.** Ask for the top three
elements and a nested loop returns the right list. The learner passes, feels fine, and
never meets `heapq.nlargest`. The lesson was the *idiom*, and the test measured the
output. Every "know this trick" exercise has this shape, and it is the whole of the first
category.

**Difficulty is not a curriculum.** `easy / medium / hard` tells you nothing about
readiness. "Easy" graph problems are harder than "medium" string problems for someone who
has never built an adjacency list. Ordering has to come from *prerequisites*, not from a
difficulty label.

---

## The ladder

Four categories. Each is a different kind of learning, not just a harder version of the
last. The numbering (`1.1`, `2.7`) is stable, and is what URLs and session logs carry.

**43 subtopics, 98 exercises written and 135 planned — 233 in total.** Those counts are
not maintained by hand: `graph.py:validate()` proves the prerequisites are acyclic, that
every problem key the ladder names is in the bank, and that nothing in the bank is missing
from the ladder, so the ladder and the bank cannot drift apart.

### 1. Basic Python

*"I know the language does this for me."* Micro-drills, one idiom each, seconds to a few
minutes. The point is always the idiom, never an algorithm. Eight subtopics, 92 drills,
314 cases — all written.

| subtopic | drills | cases | usually after |
| --- | --- | --- | --- |
| 1.1 For loops and comprehensions | 12 | 40 | — |
| 1.2 String manipulation | 15 | 49 | 1.1 |
| 1.3 Int and number manipulation | 16 | 59 | — |
| 1.4 Functions, lambda and `key=` | 13 | 42 | 1.1 |
| 1.5 Unpacking and assignment | 9 | 28 | 1.1 |
| 1.6 Truthiness, None and conditionals | 10 | 36 | — |
| 1.7 Sorting | 8 | 28 | 1.1, 1.4 |
| 1.8 Errors and context managers | 9 | 32 | — |

### 2. Data Structures

*"I know what to reach for."* Two shapes per subtopic: **use** it to solve something, and
**build** it from scratch — using a stack teaches nothing about stacks. Twelve subtopics,
90 exercises designed, all 90 written — every subtopic, including the build half.

list · tuple · dict · set · stack · queue and deque · heap · linked list · tree · trie ·
graph · union-find.

| subtopic | drills | cases | usually after |
| --- | --- | --- | --- |
| 2.1 List | 9 | 41 | 1.1 |
| 2.2 Tuple | 6 | 24 | 1.1 |
| 2.3 Dict | 9 | 40 | 1.1, 1.6 |
| 2.4 Set | 7 | 32 | 1.1, 1.6 |
| 2.5 Stack | 6 | 36 | 2.1 |
| 2.6 Queue and deque | 6 | 40 | 2.1 |
| 2.7 Heap | 7 | 38 | 1.7, 2.3 |
| 2.8 Linked list | 6 | 32 | 2.1 |
| 2.9 Tree | 7 | 34 | 2.6 |
| 2.10 Trie | 4 | 29 | 2.3, 2.9 |
| 2.11 Graph | 6 | 38 | 2.3, 2.6 |
| 2.12 Union-Find | 5 | 41 | 2.3, 2.6 |

The **use** half is written as drill units, exactly like category 1. The **build** half is
not, and cannot be: a MinStack, a dynamic array, an LRU cache and a hash map with chaining
are classes with several methods and internal state, which is a `design` problem, not a
one-function drill. Splitting them into drills would destroy the thing being taught, since
the point is that the methods share a representation. They stay counted as `planned` in
`curriculum/graph.py` until they arrive in their own directories.

### 3. Algorithms

*"I can find the approach."* Patterns, each with the cue that should make you reach for
it. Eighteen subtopics, 62 exercises, one written: `two_sum_pairs` under 3.2.

binary search · two pointers · sliding window · DFS · BFS · backtracking · Dijkstra ·
A\* · topological sort · dynamic programming · greedy · sorting algorithms · prefix sums ·
Kadane · monotonic stack · bit manipulation · Floyd cycle detection · intervals.

### 4. Industry practices

*"I can design something that survives requirements I haven't read yet."* The **original
bank** — `file_hosting`, `cloud_storage`, `in_memory_db`, `banking`, `file_system`. Four
progressive levels, ninety minutes, a class you have to refactor.

The rig *started* at category 4: everything built first was the capstone. Category 1 is
now underneath it, and categories 2 and 3 are the remaining gap.

---

## A unit is authored; a drill is practised

Category 1 is 92 drills held in eight files. Both halves of that matter, and they pull in
opposite directions.

**Authoring is per unit.** Twelve one-idiom drills in twelve directories would be
forty-eight files holding twelve one-line exercises, and nobody would write that or browse
it. So a unit is one self-contained file — `curriculum/1-basic-python/01-for-loops/unit.py`
declares `UNIT = Problem(...)` with every drill as a `Method` and every case beside the
drill it belongs to.

**Practice is per drill.** A unit is the wrong thing to practise *against*: it has one
score, one session and one workspace file, so "I want to drill `enumerate`" means opening
a file of twelve functions, and progress could not say which drills had actually been
cleared. So the unit file ends with `PROBLEMS = split(UNIT)` (`harness/units.py`), and the
loader reads `PROBLEMS`. One authored unit becomes N problems, each with:

- its own key, `<unit>.<function name>` — `for_loops.numbered` — and therefore its own
  session, its own `workspace/for_loops.numbered/solution.py`, and its own progress record
- exactly one method, and only the cases that exercise it
- a **generated** statement: the signature, the task, the constraint, and nothing else
- a pointer back to the unit, so the UI can group the drills and offer the lesson beside
  them

The unsplit key is not a problem. `for_loops` names a unit, so `./pfs start for_loops`
reports it as ambiguous across the twelve drills rather than starting anything. The bank
is 98 problems: 92 drills, 5 progressive, 1 function.

Every drill in a unit shares the unit's one oracle, `solutions/<unit>.py`, because
ninety-two near-identical one-function files would be a filing system rather than a benefit.
`answer.extract_function` then pulls out the single function that was asked for — handing
over the unit's file would answer the other eleven drills.

---

## Three documents, three jobs

The split has a second half, and it is the pedagogical one. A drill has three pieces of
material and they must stay apart:

| document | says | where it is read |
| --- | --- | --- |
| `LESSON.md`, one per unit | teaches the idiom, shared by every drill in the unit | the **Lesson** tab |
| the generated statement | states this one task and its constraint | the **Task** tab |
| the worked answer | the idiomatic one-liner | `./pfs answer`, or the **Solution** tab once `./pfs finish` has run |

Mixing them is how a lesson ends up handing over the solution: teaching `enumerate` well
and then showing the drill that asks for `enumerate` leaves nothing to attempt. The tab
strip is therefore conditional — a drill shows **Task** and **Lesson**, an industry
problem shows **Task** and **Contract**, because a drill has no contract to give beyond
the signature already in its statement.

---

## The mechanism that makes category 1 possible: constraints

A drill declares what the answer must be **and how it must be reached**. Constraints are
checked against the AST — the code is parsed, never executed for this purpose, which is
the same discipline `webui/complete.py` already follows.

```python
Method(
    display="NUMBERED",
    signature="(lines: list[str]) -> list[str]",
    doc='["1. first", "2. second", ...] — one-based numbering.',
    constraint_note="use enumerate; do not index with range(len(...))",
    constraints=(
        ForbidCall(("range",), because="enumerate already gives you the index",
                   hint="for i, line in enumerate(lines, start=1)"),
        RequireCall(("enumerate",), because="this drill is about enumerate"),
    ),
)
```

Three constraint families cover everything category 1 needs, in five classes:

| family | classes | what it teaches |
| --- | --- | --- |
| **Forbid** a construct or call | `Forbid`, `ForbidCall` | that the idiom exists and replaces the manual version |
| **Require** a call or form | `RequireCall`, `RequireConstruct` | the specific tool the unit is about |
| **Budget** | `MaxStatements` | that the idiomatic version is dramatically shorter |

`Forbid` names constructs from an explicit map in `constraints.py` rather than reaching
for `getattr(ast, ...)`, so a typo is an authoring error at import instead of a constraint
that silently never fires. `and` and `or` are separate entries because "do not paper over
a missing value with `x or default`" is a real lesson and "do not use boolean operators"
is not.

A constraint failure is **not** the same as a wrong answer, and does not read like one:
its own section, its own mark, and only for drills whose cases actually passed — claiming
"correct, but" over a wrong answer would be a plain lie.

```
── not the point of the drill ──────────
  ○ NUMBERED   correct, but
      You called `range`.  (line 12)
      → for i, line in enumerate(lines, start=1)

  These do not cost you a case. They are what the drill is for.
```

That distinction is the entire pedagogical value. "Wrong" teaches nothing; "right, but
you've just hand-rolled something the standard library does in one call" teaches the
thing.

Constraints must be **declared in the drill and shown up front**. A hidden constraint is
a trick question, and the rig's existing rule — a rule only discoverable from a hidden
case is unfair — applies with more force here, not less.

---

## Unit shape

A unit is not a pile of exercises. It is:

```
LESSON.md      the tips and tricks themselves, ~1 screen, with runnable examples
unit.py        8-16 micro-drills and their cases, each drill one idiom from the lesson
               the last of them a CHECKPOINT: several idioms at once, no constraints
```

The lesson comes first and is *readable without solving anything*. This is the piece a
practice harness has no concept of: practice assumes you already learned the thing, and a
learning platform has to teach it.

The checkpoint is what makes a unit finishable. Without it, a unit is a list; with it,
there is a moment where you either can or cannot do the thing. It is marked
`checkpoint=True` rather than recognised by its name — the old heuristic matched the
display name against `"REPORT"`, which would have silently stopped working on the next
unit — and that flag is also what exempts it from the rule that every drill carries a
constraint. Choosing the tools yourself is the exercise there, so constraining the choice
would remove it. All eight written units end in exactly one: 84 constrained drills and 8
checkpoints, and `validate.py` warns about any drill carrying neither.

---

## Ordering comes from prerequisites

Declared in one place, `curriculum/graph.py`, not scattered across two hundred problem
files — ordering spread over two hundred files is ordering nobody can read or check:

```python
Subtopic("1.7", "sorting", "Sorting", requires=("1.1", "1.4"),
         problems=("sorting.alphabetical", ...), minutes=(20, 30),
         tags=("ordering", "tie-break", "top-n"))
Subtopic("2.7", "heap", "Heap / priority queue", requires=("1.7", "2.3"),
         planned=7, minutes=(30, 45), tags=("top-n",))
```

That gives the platform the one thing it needs to answer "what next?": `frontier()`, the
subtopics whose prerequisites are all cleared. A frontier rather than a single next step,
because one forced next is a rail and the point is that the path can be stepped off.

Two things the graph is careful about, and both are about not blocking anybody:

- **`requires` advises.** The UI says "usually done after 1.4" and offers the button
  anyway. A claim about the usual order is not a claim about capability, and "I have a
  heap interview on Thursday" has to remain possible.
- **A subtopic can be planned.** `problems=()` with `planned=6` says six exercises are
  designed and unwritten, so the ladder shows its real shape instead of pretending the
  unwritten half does not exist. An unwritten prerequisite counts as satisfied — it can
  never be cleared, so requiring it would block its dependants for ever.

`docs/BANK.md` is generated from the bank, and the graph is checked against it:
`validate()` proves the prerequisites are acyclic and that the ladder and the bank name
exactly the same problems in both directions.

---

## Progress and mastery

The existing session machinery turned out to fit, once the clock became optional and
progress became per drill:

- A ninety-minute clock and a debrief is absurd for a sixty-second drill, so drills are
  **untimed**: `Session.budget_minutes` is `int | None`, `remaining_s` is infinite and
  `expired` is `False` when it is `None`, and `Problem.timed` is true only for the
  progressive kind, which is the only one simulating a clock. The home screen hides the
  time-limit control when nothing in view is timed, rather than offering a setting that
  does nothing.
- **Progress is per drill, which is the whole reason for the split.** A subtopic is
  cleared when every problem it names is cleared and nothing in it is still planned, so
  "6 of 12" in 1.1 falls straight out of the per-drill session records. Against an
  unsplit unit that number could not exist.
- `report.stuck_streaks` and `report.tag_failures` were directly reusable and are the
  mastery signals. `tag_failures` crossed with `Subtopic.tags` is the one genuinely useful
  recommendation on the home screen: "you keep failing tie-breaks" becomes "go and do 1.7
  Sorting".

**Still outstanding: clearing does not yet respect constraints.** A drill whose cases all
pass is recorded as cleared even when its constraint was violated, so the progress display
currently overstates what was learned. It should count as attempted — the violation is
already computed and rendered, it just does not reach the session record.

Mastery should decay in the display, not in the record: a subtopic cleared six weeks ago
and never revisited is worth resurfacing. The session log already has timestamps for this.

---

## What this changes about `PLATFORM_PLAN.md`

**Still right:** the kind seam (done), `Satisfies`/set-comparison/mutated-argument
expectations (Step 2, still needed), generated documentation over hand-maintained tables.

**Reprioritised down:** backfilling oracles for the three category 4 problems. Still real
debt, still tracked by `tools/bank_report.py`, but it is maintenance on the capstone while
two categories of the ladder underneath it do not exist. Category 1 and 2 oracles are
near-free anyway — the oracle for a drill *is* the idiomatic one-liner.

**New and load-bearing:** the `drill` kind, the constraint checker, `LESSON.md`, the split
from unit to drill, the prerequisite graph, and the curriculum view that replaced the flat
picker. All of those have landed.

**Wrong in the old plan:** the "aim for 8+ hidden cases" quality floor. That is right for
a category 4 level and wrong for a drill, where three or four cases is plenty because the
constraint carries the teaching. The floor now varies by kind: for a drill, fewer than two
cases is an error, two is a warning, and no hidden case is a warning.

---

## Build order

Done:

1. **Constraint checker** (`harness/constraints.py`) — Forbid / Require / Budget over the
   AST, with failure messages that teach. Plus `kind="drill"` and a per-kind quality floor.
2. **One complete unit, end to end** — `1.1 for loops`, not `top_n`: smallest, no
   prerequisites, and it proved the unit shape before seven more were written to it.
3. **Curriculum graph** — `curriculum/graph.py`, with `validate()` and `frontier()`.
4. **Category 1 in full** — eight units, 92 drills.
5. **The split from unit to drill** — practice per drill, authoring per unit, and the
   three-way separation of lesson, task and answer that came with it.
6. **Curriculum view in the browser IDE**, replacing the flat picker: the category rail,
   the frontier, weak spots from failing tags, and search across subtopics and problems.

Remaining:

7. **Constraint-aware clearing** — a drill that passes while violating its constraint is
   attempted, not cleared.
8. **Code blocks inside list items** — the last of B10 that matters. Emphasis, ordered
   lists, `<hr>` and wrapped list items were fixed when the Lesson tab shipped and made
   the gaps visible; a corpus test now renders all 38 documents and fails on raw markup.
   A fenced block inside a numbered step still closes the list, which constrains how a
   worked example can sit inside one. No lesson needs it yet.
9. **`./pfs learn`** — the "what next" surface on the CLI. The browser has it; the
   terminal still lists a flat bank.
10. **Categories 2 and 3**, subtopic by subtopic, in the order `docs/CATALOGUE.md` gives.
    **The ladder is complete.** Forty-three subtopics, 279 exercises, both gates passed on
    every one. The twelve **build** exercises arrived last, as `design` problems rather
    than drills: a MinStack, a dynamic array, an LRU cache, a circular buffer, a hash map
    with chaining, a Trie, a BST, a tree codec, a streaming median, a doubly linked list,
    a two-stack queue and the union-find structure. Each is a class with several methods
    sharing internal state, which is exactly what a one-function drill cannot express. What remains besides the algorithms is every build
    exercise: a MinStack, a dynamic array, an LRU cache, a circular buffer, a hash map
    with chaining, a Trie, a BST, a streaming median and the union-find structure itself
    are *classes*, so they arrive as `design` problems rather than inside a drill unit.
    Twelve of them, and they are the reason category 2 reads 78 of 90 rather than 90 of 90.

Each step lands with tests and `tests/run_all.sh` green, as before.
