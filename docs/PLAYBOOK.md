# Playbook

> **Read this after your first cold attempt, not before.**
>
> The first attempt is the only clean measurement you get of where you actually
> are. Spending it having already been told the shape of the answer converts a
> diagnostic into a rehearsal. Run `./pfs start file_hosting` first, use the full
> 90 minutes, then come back.

This is about the *format*, not about any particular problem. Nothing here is the
answer to a problem in the bank.

---

## The one idea

Every level of this assessment is paid for at level 1.

Level 3 always adds a dimension to operations you have already written — usually
time. Level 4 always asks for a state you have already thrown away — usually a
previous version. If your level-1 state cannot express "as of when", level 3 is a
rewrite. If it overwrites without remembering, level 4 is a rewrite. Two rewrites
inside 90 minutes is how people finish at level 2 with 40 minutes of thrash behind
them.

So the highest-leverage five minutes of the whole test happen before you write any
code.

## The five-minute design budget

Before level 1, answer two questions.

**1. Can "now" be a parameter rather than mutable state?**

Level 3 will hand you a timestamp on every call. If your operations already compute
their answer *as of a given instant*, level 3 is one delegating line per method and
your earlier tests keep passing untouched. If instead you keep a mutable "current
state" that operations mutate in place, level 3 means threading a new concept
through every method you own.

**2. What am I about to overwrite?**

Every overwrite destroys a fact that level 4 may ask you to restore. Appending a
record of what happened costs almost nothing at this scale; reconstructing what you
overwrote costs the level.

That is the whole design decision. It takes five minutes and it decides the score.

## The four level shapes, and what each one wants

**Level 1 — basic CRUD, plus an error case or two.**
Everyone clears this. The only ways to lose here are spending twenty minutes on it,
or building state that cannot grow. Watch for: truthiness on numeric fields, so a
zero value reads as absent; and "rejected operation" cases, where a call that raises
must leave *no* trace.

**Level 2 — a ranked or filtered query.**
Almost always: filter by a prefix, order by a magnitude descending, break ties by
name ascending, cap at N. In Python that is one line, and writing it as one line is
the point:

```python
sorted(matches, key=lambda name: (-size[name], name))[:n]
```

The classic failure is sorting twice — by magnitude, then by name — which destroys
the first sort. The other classic failure is assuming the tie-break is numeric when
it is lexicographic: `"a10"` sorts before `"a2"`.

**Level 3 — the refactor.** This is where the assessment is decided.

New operations arrive that mirror the old ones with an extra parameter, and the
statement says they "inherit all functionality" of the originals. That sentence is
an instruction about your architecture: the new methods are the real implementation
and the old ones become thin delegations to them, sharing one store.

```python
def do_thing(self, *args):
    return self.do_thing_at(0, *args)
```

The trap — and it is the single most expensive mistake in this format — is adding
the new methods *beside* the old ones with their own storage. It looks faster for
ten minutes. Then your level-1 and level-2 tests go red, because the two stores
disagree, and you spend the rest of the session firefighting regressions in code you
had already finished.

TTL arrives with level 3 too. Settle the interval convention *once*, write it down,
and apply it everywhere: a lifetime of `n` starting at `t` means alive on `[t, t+n)`
— the item is gone at exactly `t+n`. Getting this backwards costs one test; noticing
it costs fifteen seconds; panicking about it and rewriting your expiry model costs
the level.

**Level 4 — history.** Rollback, backup/restore, or merge.

Two implementations, and the choice matters:

- *Snapshot*: copy the whole state on every write, restore the nearest one.
  Cheap to write, and it passes the obvious cases. It breaks the moment you are
  asked to go back twice, or to a point you never snapshotted.
- *Log*: append every write as `(when, what, value)`; the state at time `t` is a
  replay of everything at or before `t`. Slightly more to write, and it answers
  every level-4 question — including repeated rollbacks — for free.

If level 4 is a merge rather than a rollback, the question is instead: what do you
recompute versus what do you maintain incrementally? Keep a running total per entity
rather than recomputing by scanning, and merging becomes addition.

And if you snapshot at all: **deep copy**. A shallow copy of a dict of dicts means
your later writes quietly corrupt the backup you took.

## Working method during the 90 minutes

**Run the tests constantly.** Partial credit is per test. There is no prize for a
big submission and no penalty for a failed run.

**When a run fails, read the expected value before touching the code.** Three runs
in a row failing the same case means the last two were guesses. The harness measures
this and calls it a stuck streak, because it is the most common way sessions die.

**When the statement is ambiguous, pick the simplest testable reading and move.**
Do not try to satisfy both readings. If the tests disagree with you, believe the
tests immediately — your reading was a guess and theirs is the specification.

**Budget by the clock, not by the level.** If level 3 is not clearing by minute 60,
stop trying to finish it and make sure everything below it is green and clean.
Three clean levels beat four broken ones, on both the test score and the code review.

**Write the sort key, the interval convention, and the error rule as comments** as
you decide them. You will re-read your own rules at level 4, and re-deriving them
under time pressure is where sign errors come from.

## Python specifics worth having in your fingers

The real test allows language documentation, but not finding out that `sorted` is
stable in the middle of level 2.

```python
sorted(items, key=lambda x: (-x.size, x.name))     # compound key, one pass
collections.defaultdict(dict)                       # nested state without guards
copy.deepcopy(state)                                # snapshots that do not alias
bisect.bisect_right(times, t) - 1                   # latest entry at or before t
heapq.nlargest(n, items, key=...)                   # when n is small and items are many
d.get(k)                                            # returns None, which is usually the contract
```

Two habits that pay for themselves:

- Return `None` for "absent" and the value for "present". Do not overload `0`, `""`
  or `False` — the contract almost always distinguishes them, and the tests always do.
- Raise a plain `Exception` subclass where the statement says "throws". Do not return
  an error code; the tests call it as an error.

## What "good code" means here

The level titles say it: *Refactoring & Encapsulation*, *Extending Design &
Functionality*. The assessment is designed so that a good design makes levels 3 and
4 short. So the question to ask yourself at the end of each level is the one a
reviewer will ask:

> If a fifth level arrived now, how much of this would I rewrite?

If the honest answer is "most of it", that is the finding — and it is a finding about
level 1, not about level 5.
