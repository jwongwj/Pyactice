# Decisions — In-Memory File Hosting Service

**Answer key. Read after `./pfs finish`, not during.**

The published statement is genuinely under-specified in several places. Real
candidates hit exactly these gaps and lose time deciding. Below is every point
where this suite had to choose, what it chose, why, and what else was defensible.
Each one is demonstrated by a *visible* sample case, so an attentive candidate can
learn the rule from the examples rather than guess — which is also how the real
assessment communicates it.

---

## 1. What does `FILE_SEARCH` return?

**Chosen:** a `list[str]` of file names, largest first.

The statement says "find top 10 files" without saying what a "file" looks like in
the output. Circulating variants return `"name(size)"` strings or `(name, size)`
tuples. Names-only is the most common form in reports of the real question and is
the least fussy to test. The contract states it, and the level-2 sample shows it.

**Also defensible:** returning sizes alongside names. If the real assessment you
sit returns tuples, the sample tests will say so on the first run — read them.

---

## 2. "in case of a tie by file name" — which direction?

**Chosen:** ascending, ordinary string comparison.

Descending would be perverse, and no source reports it. The important trap is not
the direction but that it is *lexicographic*: `"/a10" < "/a2"`. The hidden case
`l2_tie_break_is_lexicographic_not_numeric` exists solely to catch a natural-sort
implementation. In Python the whole thing is one line:

```python
sorted(matches, key=lambda name: (-sizes[name], name))[:10]
```

Sorting by size descending and then re-sorting by name is the common wrong answer;
it destroys the first sort unless you rely on stability in the right order.

---

## 3. Is `prefix` a path prefix or a string prefix?

**Chosen:** a plain string prefix. `"/dirAB/y"` matches the prefix `"/dirA"`.

The example file tree in the statement is decorative — the service stores flat
names that happen to contain slashes. There are no directory objects;
`FILE_GET("/dir-a")` is `None` even when `/dir-a/dir-c/file-2.txt` exists.
Covered by `l2_prefix_is_a_string_not_a_directory` and
`l1_nested_paths_are_just_names`.

---

## 4. TTL interval: `[t, t+n)` or `[t, t+n]`?

**Chosen:** half-open, `[t, t + n)`. At exactly `t + n` the file is gone.

"Available for ttl seconds" means the file is available for a duration of `n`
seconds, and a closed interval would give `n + 1` live instants. Every other
CodeSignal problem family in this bank (the in-memory database's TTL, the banking
system's scheduled payments) uses the same convention, which is a good reason to
learn it once.

Visible in `l3_ttl_expiry_boundary`. Also drives `l3_zero_ttl_is_dead_on_arrival`:
`ttl = 0` gives the empty interval `[0, 0)`, so the file is never alive.

**Also defensible:** inclusive. If you assumed inclusive, you failed exactly one
sample case and the fix is a `<` for a `<=`. That is a 15-second fix if you notice
it and a 15-minute fix if you start rewriting the expiry model.

---

## 5. Does a file exist *before* its upload timestamp?

**Chosen:** no. Alive means `[upload, upload + ttl)` — bounded on both ends.

Real test scripts feed timestamps in non-decreasing order, so this rarely comes
up; storing `(start, expiry)` rather than just `expiry` costs nothing and makes
rollback much easier to reason about. It is stated in CONTRACT.md so it is not a
gotcha, and `l3_file_does_not_exist_before_it_is_uploaded` checks it.

---

## 6. What TTL does a copy get?

**Chosen:** the copy inherits the **source's expiry instant**, not a fresh
lifetime measured from the copy.

`FILE_COPY_AT(5, src, dst)` where `src` was uploaded at `0` with `ttl = 10` gives
`dst` an expiry of `10` — not `15`. "Copy the source file" means the destination
is the same file: same size, same remaining life. Visible in
`l3_copy_inherits_the_source_expiry`.

**Also defensible:** the copy is a new upload and gets a fresh `ttl` window. This
is the single most-argued point in this problem. Both readings appear in
circulating solutions. It is visible precisely because guessing it is not a skill.

---

## 7. Are the level-1 methods separate from the `_AT` methods?

**Chosen:** no. They are the same store. `FILE_UPLOAD(name, size)` is exactly
`FILE_UPLOAD_AT(0, name, size)`.

The statement says the new methods "inherit all functionality" of the old ones.
Keeping two stores is the level-3 disaster: your level-1 and level-2 tests go red
the moment you add timestamps, and you spend the rest of the session firefighting
regressions. The intended refactor is one line per old method:

```python
def file_upload(self, file_name, size):
    return self.file_upload_at(0, file_name, size)
```

Visible in `l3_plain_calls_are_timestamp_zero`, and enforced by the `regression`
tagged cases at every level above 1.

---

## 8. `ROLLBACK` — destructive or not?

**Chosen: destructive.** `ROLLBACK(t)` restores the store to exactly the state a
query at time `t` would have observed. Files uploaded after `t` are gone. Files
overwritten after `t` are back to their pre-overwrite contents. Files that had
already expired at `t` stay gone.

This is the most contested point in the entire question. The published wording —
"rollback the state of the file storage to the state specified in the timestamp"
— is the plain destructive reading, but at least one widely-circulated practice
suite asserts the opposite (files created after the timestamp survive), and its
own issue tracker carries a complaint that its expectations are indistinguishable
from a `ROLLBACK` that does nothing at all.
See <https://github.com/PaulLockett/CodeSignal_Practice_Industry_Coding_Framework/issues/16>.

This suite takes the destructive reading because it is the only one under which
`ROLLBACK` is testable at all, and it makes it visible three times over
(`l4_rollback_drops_later_files`, `l4_rollback_undoes_an_overwriting_copy`,
`l4_rollback_keeps_expiry_times`) so nobody has to guess.

**If you sit the real assessment and the sample cases disagree with this,
believe the sample cases.** That is the whole lesson of level 4.

---

## 9. "All ttls should be recalculated accordingly" — recalculated to what?

**Chosen:** a surviving file keeps its original expiry instant. Its *remaining*
lifetime at `t` is `expiry - t`, and since queries after the rollback still use
absolute timestamps, re-anchoring that remainder to `t` yields the same expiry.
So the observable rule is: expiry times do not move.

The phrase is doing less work than it appears to. The thing it warns you about is
the implementation trap of restoring names and sizes but dropping the lifetimes —
which turns every ttl file into an immortal one. `l4_rollback_keeps_expiry_times`
is the check: `/t` must still die at `100`.

**Also defensible:** re-anchoring remaining lifetimes to the latest timestamp seen
so far. Nobody can implement that from the statement alone, and no reported test
requires it.

---

## 10. Does the state "at timestamp `t`" include operations that happened at
exactly `t`?

**Chosen:** yes. `ROLLBACK(5)` keeps a file uploaded at `5`.

Consistent with aliveness being `[t, …)`. Covered by
`l4_rollback_at_an_exact_upload_timestamp`.

---

## 11. Can you roll back twice?

**Chosen:** yes, and the second rollback can go further back than the first.

This forces you to keep an operation log (or a per-name version history) rather
than a single snapshot. `l4_rollback_twice_goes_further_back` is the case. It is
the one hidden case most likely to break an otherwise-correct level 4, because the
cheapest implementation — snapshot on every write, restore the nearest snapshot —
happens to work for a single rollback.

---

## Where the time actually goes

Reported and observed failure modes for this problem, in rough order of cost:

1. **Two stores at level 3.** Adding `_at` methods beside the level-1 ones instead
   of underneath them. Costs 10–20 minutes and usually takes level 1 down with it.
2. **Re-sorting instead of sorting once** at level 2, then not understanding why
   ties look random.
3. **Snapshot-per-write at level 4**, which passes the visible cases and dies on
   `l4_rollback_twice_goes_further_back`.
4. **Truthiness on size.** `if size:` treats a 0-byte file as missing.
5. **Boundary sign errors on ttl**, costing one case and, if you panic, the level.
