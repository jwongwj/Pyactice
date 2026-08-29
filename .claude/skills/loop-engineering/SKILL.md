---
name: loop-engineering
description: Design and run the practice loop for the CodeSignal Industry Coding Framework assessment - cold attempts, debriefs, targeted drills, and rotation. Use when planning practice, deciding what to work on next, interpreting ./pfs stats or a session debrief, or when the user asks how to get better at this test rather than how to solve one problem.
---

# Loop engineering

Practice is a control system, not a pile of attempts. The loop has four stages and
they are not interchangeable. Most people do stage 1 repeatedly and wonder why they
plateau.

```
  cold attempt  ──▶  debrief  ──▶  targeted drill  ──▶  rotate
    (measure)       (diagnose)      (repair)         (generalise)
        ▲                                                  │
        └──────────────────────────────────────────────────┘
```

## 1. Cold attempt — the measurement

Full 90 minutes, one problem, no notes, no `DECISIONS.md`, no reading the harness
source, no AI. Anything less and the number you get back is not about you.

```bash
./pfs start file_hosting
```

The clock is not decoration. The whole difficulty of this assessment is that level 3
arrives when you are 40 minutes in and already committed to a data structure. You
cannot rehearse that feeling with the clock paused.

Rules that make the measurement valid:

- **Never stop the clock to think.** Thinking is the exercise.
- **Never fix the harness mid-attempt.** If a case looks wrong, log it and move on:
  `./pfs dispute <case_id> "why you think it is wrong"`. Arguing with the grader is
  how people lose twenty minutes to a case that turns out to be right.
- **Never read `DECISIONS.md` first.** It is the answer key. `./pfs decisions` refuses
  while a session is live, on purpose.
- **`./pfs contract` is allowed.** It is the information the real IDE gives you through
  type hints and sample tests. Reading it is not cheating; it is the skill.

## 2. Debrief — within ten minutes, while it is still fresh

```bash
./pfs finish          # stops the clock, prints the debrief, unlocks the answer key
./pfs decisions       # every ambiguity, what the suite chose, and why
```

The debrief reports three things. Read them in this order:

**Time-to-clear per level.** Compare against the budget. Level 1 over 15 minutes is
almost always a design problem, not a typing problem — you were inventing state you
did not need. Level 3 over 30 minutes is almost always the two-stores mistake.

**Stuck streaks.** Three or more consecutive runs failing the same case means the
runs after the first were guesses. This is the single highest-value number in the
report. The repair is behavioural, not technical: when a run fails, read the
expected value before you touch the code.

**Unresolved tags.** Which *concept* was still red at the end. This is the input to
stage 3.

Then read your own code and ask the one question the real graders also ask: *if a
fifth level arrived now, what would it cost?* The ICF explicitly scores whether later
levels were cheap extensions or rewrites.

## 3. Targeted drill — repair one thing

Drills are short and narrow. Do not re-attempt the whole problem; you would be
testing recall of the answer, not the skill.

```bash
./pfs test --tag ttl --reveal          # every case about lifetimes, operations shown
./pfs start file_hosting --level 3     # drop straight into the level that hurt
```

Pick the drill from the tag that was still failing, not from the level that felt
worst. Those are usually different: level 4 feels worst because you ran out of time,
but the cause was a level-1 state design that made rollback expensive.

Stop when the drill passes twice in a row. A third repetition teaches nothing.

## 4. Rotate — generalise

Never take the same problem cold twice in a row. Two days minimum, and a different
problem in between:

```bash
./pfs list
```

Four of the five rotate through the same skeletons — basic CRUD, a ranked query,
a time/TTL refactor, a snapshot-or-history feature. Rotating is what turns "I
remember the file hosting answer" into "I recognise the shape."

`file_system` is the exception and the hardest. It is the only problem in the bank
built on a **tree**, which makes it the only one where a level-1 data-structure choice
can cost you level 3 or 4. Save it for when the four flat ones feel comfortable — it is
the closest thing here to the reported difficulty ceiling, and failing it early teaches
less than failing it once the CRUD levels are automatic.

A workable five-week rotation, two sessions a week:

| Week | Session A | Session B |
| --- | --- | --- |
| 1 | `file_hosting` cold | drill weakest tag |
| 2 | `in_memory_db` cold | drill weakest tag |
| 3 | `cloud_storage` cold | `file_hosting` cold again — compare to week 1 |
| 4 | `banking` cold | whichever family is weakest, cold |
| 5 | `file_system` cold, `--blind` | walk through where the design bit |

## Exam mode

```bash
./pfs start <key> --blind
```

Reduces a failure to a test number, its outcome, and whatever your own code printed.
No case names, no tags, no operation shapes, no expected values — which is what the
real grader gives you.

Use it once the mechanics are automatic, not before. Early on, the case name is how you
learn which rules exist; `--blind` removes that teaching aid, so a cold blind attempt in
week 1 mostly teaches frustration. From roughly the point where you clear level 2
reliably, every cold attempt should be blind: the skill it trains — forming a hypothesis
about *your own* code from a bare pass/fail count and your own `print()` output — is the
one the default feedback lets you skip.

## Reading `./pfs stats`

```bash
./pfs stats
```

Cross-session, the bar chart of failing tags is the curriculum. Work the top row.
Tags fall into two kinds and they need different repairs:

- **Rule tags** (`tie-break`, `boundaries`, `ttl`) — you did not read carefully.
  Repair: slow down on the statement, and write the rule as a comment before coding.
- **Design tags** (`refactor`, `regression`, `rollback`, `history`) — your state was
  wrong. Repair: spend the first five minutes of the next attempt on state only,
  and ask "what does level 4 need?" before writing level 1.

Design tags matter more. A rule error costs one case; a design error costs a level.

## The five-minute design budget

The single highest-leverage habit for this format. Before writing any level-1 code,
spend five minutes deciding what you store, given that:

- level 3 will make every operation take a timestamp and add expiry, and
- level 4 will ask for history, snapshots, or a merge.

Two questions answer it almost every time:

1. **Can I represent "now" as a parameter instead of as mutable state?** If yes, the
   level-3 refactor is one delegating line per method.
2. **Am I overwriting anything?** Every overwrite is a fact level 4 may ask you to
   restore. Appending is cheap; un-overwriting is not.

Five minutes here routinely saves twenty at level 3. It is also the part of the
assessment that is graded on code quality rather than tests.

## Anti-patterns

| Anti-pattern | Why it fails | Instead |
| --- | --- | --- |
| Re-attempting the same problem immediately | tests recall of the answer | rotate, or drill a tag |
| Reading `DECISIONS.md` before attempting | removes the ambiguity that is the skill | read it in the debrief |
| Pausing the clock | removes the constraint that is the test | finish, then take the time |
| Fixing the harness mid-attempt | costs the level | `./pfs dispute`, keep going |
| Optimising for speed on level 1 | level 1 is not where the time goes | optimise the state design |
| Practising only level 1-2 because they feel good | they are 40% of the score | start at `--level 3` |
| Chasing a green run without reading the failure | produces stuck streaks | read the expected value first |

## When the loop is done

You are ready when, across two different problems taken cold: level 1 clears inside
12 minutes, level 3 does not break level 1, and no stuck streak exceeds two runs.
Score follows from those three; chasing the score directly does not work.
