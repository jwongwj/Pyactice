# UI plan — a path you can step off

The tension to design around: a **learning path** is the whole value (nobody wants to
choose from 230 exercises), but the moment someone thinks *"I have a Heap interview on
Thursday"*, a path that will not let them jump straight to Heap is worse than no path.

So the governing rule, which is the same one already used for drill constraints:

> **Prerequisites advise. They never lock.**

Everything below follows from that. There is no greyed-out card anywhere in this design.
A subtopic you are not ready for says *why*, and still has a button.

---

## Three screens

Not four — the existing problem view is kept exactly as it is.

```
HOME            the path, plus every way of stepping off it
CATEGORY        browse one of the four, with progress
UNIT            lesson + drill checklist + editor + results        (new shape)
PROBLEM         statement + editor + results                       (exists, unchanged)
```

---

## 1. Home

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Practice                             search  [ heap____________ ]           │
├────────────────────┬─────────────────────────────────────────────────────────┤
│                    │  CONTINUE                                               │
│ ▸ 1 Basic Python   │  ┌───────────────────────────────────────────────────┐  │
│   ████████░░  6/8  │  │  2.3 Dict · drill 4 of 10                         │  │
│                    │  │  group records by a field              [ Resume ] │  │
│ ▸ 2 Data Structures│  └───────────────────────────────────────────────────┘  │
│   ███░░░░░░░  3/12 │                                                         │
│                    │  NEXT ON YOUR PATH                                      │
│ ▸ 3 Algorithms     │  ┌───────────────────────────────────────────────────┐  │
│   ░░░░░░░░░░  0/18 │  │  2.4 Set        ready   6 drills      ~12 min     │  │
│                    │  │  2.5 Stack      ready   4 + MinStack  ~25 min     │  │
│ ▸ 4 Industry       │  │  3.1 Binary search  ready  4 problems ~40 min     │  │
│   ██░░░░░░░░  1/5  │  └───────────────────────────────────────────────────┘  │
│                    │                                                         │
│  ────────────────  │  WEAK SPOTS            from your last 12 sessions       │
│  ⚑ Weak spots      │   ████████████  edge-values (8)   →  1.6 Truthiness     │
│  ↻ Revisit         │   ██████████    tie-break (4)     →  1.7 Sorting        │
│  ⏱ Timed attempt   │   ███████       paths (6)         →  1.2 Strings        │
└────────────────────┴─────────────────────────────────────────────────────────┘
```

Four ways in, deliberately:

| | for |
| --- | --- |
| **Continue** | the 90% case — one click back to exactly where you stopped |
| **Next on your path** | the *frontier*, not a single next step. Every subtopic whose prerequisites are cleared, ordered by the graph. Several choices keeps it a path rather than a rail |
| **Category rail** | *"I want Heap"*. Always visible, on every screen |
| **Search** | *"I want Dijkstra and I do not care where it lives"*. Matches subtopic, problem title, algorithm name and idiom, so `rpartition` finds `1.2 Strings` |

**Weak spots** is the one piece of genuine intelligence: `./pfs stats` already computes
failing tags across sessions (`report.tag_failures`), and mapping a tag to the subtopic
that teaches it turns "you keep failing tie-breaks" into "go do 1.7 Sorting". That is a
recommendation nothing else on the screen can make.

---

## 2. Category

```
2  Data Structures                                          3 of 12 cleared
┌──────────────────────────────────────────────────────────────────────────────┐
│ ✓ 2.1  List           ██████████  7/7    use 6 · build 1        [ Review ]   │
│ ✓ 2.2  Tuple          ██████████  5/5    use 5                  [ Review ]   │
│ ▸ 2.3  Dict           ██████░░░░  6/10   use 9 · build 1        [ Continue ] │
│   2.4  Set            ░░░░░░░░░░  0/6    use 6                  [ Start ]    │
│   2.5  Stack          ░░░░░░░░░░  0/6    use 4 · build 1 · P 1  [ Start ]    │
│   2.6  Queue & deque  ░░░░░░░░░░  0/6    use 4 · build 2        [ Start ]    │
│   2.7  Heap           ░░░░░░░░░░  0/7    use 6 · build 1                     │
│        ⚠ usually done after 1.7 Sorting          [ 1.7 first ] [ Start ]     │
│   2.8  Linked list    ░░░░░░░░░░  0/7    use 5 · build 2        [ Start ]    │
│   ...                                                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

The Heap row is the whole design in miniature. It is not disabled. It states the
prerequisite, offers the shortcut to satisfy it, and offers to start regardless. The label
is **"usually done after"**, not "locked" or "requires" — because the claim is statistical,
not structural, and pretending otherwise is a lie the learner will resent.

`use` / `build` / `P` counts are visible because they predict what the session is like.
Six one-minute drills and one forty-minute build-a-median-stream are the same "7" and
completely different evenings.

---

## 3. Unit — superseded by the split

**This screen was designed before drills were split out of units, and the split replaced
most of it.** It assumed one session per unit and one workspace file holding eleven stubs;
`harness/units.py` now gives every drill its own key, session and file. What survives is
the drill list and the four-state reporting; what is gone is the reason the list had to
live *inside* a session.

The list moved to the picker instead. A unit is one row that collapses to a single action
plus a `3/12 ⌄` disclosure, and expanding it reveals its drills nested underneath — each
with its own tick, its own blurb and its own Start. Kept below for the reporting design
and the states table, which still hold.


```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2.3 Dict     ✓✓✓✓✓✓ ▸ ○ · ·   6/10          untimed        ⌘↵  ▶ Run        │
├───────────────────────────┬──────────────────────────────────────────────────┤
│  Lesson │ Drills │ Answer │  1   def group_by_field(records, field):          │
│  ────────────────────────  │  2       """Group records by the value of field. │
│                           │  3                                               │
│  ✓ 1  get with a default  │  4       Constraints: no `if key in`             │
│  ✓ 2  setdefault          │  5       """                                     │
│  ✓ 3  defaultdict         │  6       raise NotImplementedError("GROUP_BY")   │
│  ▸ 4  group by a field    │                                                  │
│  ○ 5  Counter             ├──────────────────────────────────────────────────┤
│    6  most_common         │  ✓ get_with_default     correct                  │
│    7  merge with          │  ✓ setdefault           correct                  │
│       precedence          │  ✗ group_by_field       correct — but not the     │
│    8  invert a mapping    │                         point of this drill       │
│    9  first non-repeating │                         You used `if key in`.     │
│                           │                         Try defaultdict(list).    │
│  ────────────────────────  │  · counter              not implemented          │
│  ⚑ Checkpoint             │                                                  │
│     index records 2 ways  │  Results │ Output                                │
└───────────────────────────┴──────────────────────────────────────────────────┘
```

### The drill list does three jobs — two of them still

1. **Progress** — six ticks is visible achievement inside a single sitting, which a bare
   file of eleven stubs never gives you. Still true, but it is now the unit's `3/12
   cleared` and the ticks on its nested rows in the picker, not a sidebar in a session.
2. **Navigation** — ~~clicking a drill scrolls the editor to that function and focuses
   it.~~ Moot: one drill is one file with one function, so there is nothing to scroll to.
3. **State** at a glance, and the states are deliberately four, not two:

| | meaning |
| --- | --- |
| `✓` | correct, constraints satisfied |
| `○` | correct, **constraint violated** — the distinction this platform exists for |
| `·` | not implemented |
| `✗` | wrong answer |

`○` must never look like `✗`. It is the difference between *you have not learned this yet*
and *you got this right the long way round*, and collapsing them destroys the teaching.

### Lesson first, and not modal about it

The **Lesson** tab is selected by default on a unit you have never opened, and the editor
still sits there ready. No "you must read this" gate, no dismissable overlay — the lesson
is just the first thing in front of you, and skipping it costs one click. People who
already know `defaultdict` should not have to dismiss a tutorial.

### The checkpoint is separated

It sits below a divider and is the only thing that reports as **cleared** rather than
passed, because clearing a unit requires the checkpoint to pass *with* its constraints
satisfied. Available at any time; it just will not be interesting before the drills.

---

## Progress model

Derived from `sessions/`, never stored twice.

```
drill      done | attempted (constraint violated) | not started
unit       drills done / total,  checkpoint cleared yes/no
subtopic   cleared = checkpoint cleared, or every problem passed for a problem subtopic
category   subtopics cleared / total
```

**Cleared is strict, deliberately.** A drill that passes while violating its constraint
counts as *attempted*. Otherwise the progress bar claims you learned an idiom you never
typed, which makes the whole display worthless — and the weak-spot recommendations
downstream of it wrong.

**Staleness, not decay.** A subtopic cleared six weeks ago stays cleared; it appears under
**Revisit** on the home screen. Un-clearing something a person earned is punitive and they
will stop trusting the number.

---

## What the front end needs before any of this

The exploration of `webui/index.html` (1,153 lines, one file, no build step) found the
specific things that make this expensive if done in the wrong order.

**0. Nesting drills under their unit — done, and it was a geometry bug.** The subtopic
row rendered `sub.problems.map(startButtons)`, which was correct while a subtopic held one
problem and became a wall when a unit held twelve: twelve full-width buttons in a
`white-space:nowrap` flex row pushed the home column to **5545px inside a 1204px
viewport**, each labelled with the unit title repeated in full. A unit now collapses to
one action plus a `3/12 ⌄` disclosure, and its drills nest under the row via
`grid-column:1/-1`. Two details worth keeping: the nested name column is a **fixed**
width, because each drill row is its own grid and `auto` sized per row and left the
blurbs on a ragged edge; and the browser test asserts `scrollWidth <= clientWidth`
rather than the presence of the rows, because presence is exactly what the broken version
also had.

**1. Make the tab strip data-driven.** This advice was written as "do it first, before
adding a fifth tab", and then the Lesson tab was added without doing it — editing exactly
the five predicted places: the markup, `renderDoc`'s `if`-chain, the visibility block in
`paint()`, the duplicated visibility block in `bootDocWindow`, and the review-tab reset
list. The prediction held, so the debt is now a six-tab strip with two copy-paste
visibility twins instead of a five-tab one. A `TABS` array of `{id, label, when, render}`
still collapses all five, and the next tab should pay for it.

**2. Replace `renderStart`.** **Done.** The centred single column became the category
rail and home grid, and a card now reports its own level count rather than a hardcoded
`4 levels` — which was already a lie for 93 of the 98 problems in the bank.

**3. Fix the picker's disk reads.** **Done.** `_attempts_by_problem` (`server.py:133`)
buckets by problem key in one pass over `sessions/`, instead of re-parsing every file for
every problem. One `all_sessions()` call per single-problem payload remains at
`server.py:405`, which is one problem's attempt number and not a scaling concern.

**4. A metadata index.** **Solved differently, and more cheaply.** Rather than splitting
metadata out, `all_problems()` is memoised on a `(path, mtime_ns, size)` signature over the
bank (`loader.py:118`), so the modules are compiled once and an edit still invalidates —
27.4 ms cold to 1.92 ms warm. This was not a nicety: the un-memoised version re-imported
the bank several times per request and was the real cause of an intermittent picker failure
first misdiagnosed as stale bytecode. A test counts the imports rather than timing them.

A `PROBLEM_META` index is still the answer if the bank grows enough that the *cold* read
hurts; at 98 problems it does not.

**5. The markdown renderer.** **Mostly done**, and the Lesson tab is what forced it:
`LESSON.md` needs prose, and 69 `*emphasis*` spans across the eight lessons were reaching
the reader as literal asterisks. Emphasis, ordered lists, `<hr>` and wrapped list items
now render; the answer keys no longer show 50 literal `<p>---</p>`. A fenced code block
inside a list item still closes the list, and blockquotes are still unsupported — nothing
in the bank uses either. A corpus test renders all 38 documents and fails on raw markup,
so the next gap is found by the suite rather than by a reader mid-attempt.

---

## API

One new endpoint; the rest exists.

```
GET /api/curriculum          the graph + progress, for the home and category screens
    → { categories: [ { n, title, cleared, total, subtopics: [ {
          id, title, cleared, done, total, kinds: {use, build, problem},
          requires: [...], ready: bool, estimate_min } ] } ],
        continue: { subtopic, drill, label } | null,
        frontier: [ subtopic_id, ... ],
        weak: [ { tag, sessions, subtopic } ] }
```

`GET /api/state` gains `unit` when the session is a drill unit: the ordered drill list
with per-drill status, so the checklist renders from one payload rather than N requests.

Everything else — `/api/run`, `/api/save`, `/api/answer`, `/api/complete`, `/api/check` —
is unchanged. That is the payoff for drills being ordinary `Problem`s with methods.

---

## Build order

1. **Data-driven tabs** — pure refactor, no new behaviour, tests stay green. Doing this
   after adding Lesson costs the refactor twice.
2. **`/api/curriculum` + `curriculum/graph.py`** — CLI first (`./pfs learn`), so the graph
   is proven before any pixels depend on it.
3. **Home screen**, replacing `renderStart`. Category rail + Continue + frontier + search.
4. **Unit view** — the drill checklist, the four-state icons, lesson-first.
5. **Markdown gaps**, which `LESSON.md` forces.
6. **Metadata index and the `all_sessions()` fix**, when the bank passes ~30 exercises and
   the home screen starts to feel it.

Steps 1–2 have no visual output at all, which is the point: the graph and the tab system
are what everything else stands on, and both are cheaper to get right before there is a
screen depending on them.

Browser tests follow the existing discipline — assert on **geometry**, not just presence.
Every UI bug this rig has shipped was a layout bug that a content-only test passed: a Run
button pushed outside a narrow viewport, an editor collapsed to zero height. The drill
checklist is a new sidebar inside an already-tight three-pane layout, so it is exactly the
shape of thing that breaks at 1100px.
