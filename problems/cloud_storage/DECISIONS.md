# Decisions — Cloud File Storage

**Answer key. Read after `./pfs finish`, not during.**

---

## 1. `ADD_FILE_BY` returns remaining capacity, not used

`ADD_FILE_BY("u1", "/a", 40)` for a user with capacity 100 returns `60`.

Visible in `l3_capacity_is_enforced`. The trap is that an exact fit returns `0`, and `0`
is a *success*. Code that does `return remaining or None`, or that checks
`if not result:` at the call site, treats a full user as a failed add.

---

## 2. Failure is a return value, not an exception

Unlike the file hosting problem in this bank, nothing here raises. `ADD_FILE` returns
`False`, `ADD_FILE_BY` returns `None`. Two problems, two conventions, both as reported —
read the stub's return type before deciding how to signal failure.

`None` from `ADD_FILE_BY` covers three distinct situations (unknown user, name already
taken, will not fit) and the caller cannot distinguish them. That is deliberate and it is
stated in `CONTRACT.md`.

---

## 3. A rejected operation must leave nothing behind

**Chosen:** an add that fails changes no state at all — no partial file, and no capacity
debited.

This is the most valuable habit this problem teaches, because the damage is invisible.
Code that debits capacity and then discovers the file will not fit leaves the user
permanently poorer, and nothing fails until several operations later.
`l3_a_rejected_add_costs_nothing` is the case; `l1_duplicate_add_is_rejected` is the
level-1 version.

---

## 4. One namespace for everybody

**Chosen:** file names are globally unique. A user cannot add `/x` if another user — or
`ADD_FILE` — already owns that name.

Visible in `l3_names_are_global_across_users`. The alternative, per-user namespaces,
would make `GET_FILE_SIZE(name)` ambiguous, and the level-1 signature has no user
parameter — so the statement settles this even though it never says it.

---

## 5. What owns files added by `ADD_FILE`?

**Chosen:** an implicit system owner with no capacity limit. Those files cost no user
anything, never appear in a user's backup, and can still be read and deleted by name.

`"admin"` is a convenient name for this owner, but it is not addressable:
`ADD_FILE_BY("admin", ...)` returns `None` like any unknown user
(`l3_unknown_user_cannot_add`). Making it addressable would force `ADD_FILE_BY` to return
an infinite remaining capacity, which has no sensible `int` value.

**Also defensible:** a real `admin` user created up front with a huge finite capacity.
Reports differ. The observable behaviour that matters — plain files do not consume user
capacity — is the same either way, and `l3_plain_files_never_touch_user_capacity` checks it.

---

## 6. Capacity arithmetic on merge

**Chosen:** capacities add, used space adds, files change owner. Merging a user with
capacity 100 (40 used) into one with capacity 100 (50 used) gives capacity 200, used 90,
and returns `110`.

Visible in `l3_merge_moves_files_and_capacity`.

**Rejected:** keeping only the first user's capacity, which would let a merge silently
overflow the survivor. Nothing in the statement suggests discarding capacity.

A merge into oneself returns `None` rather than succeeding trivially
(`l3_merge_needs_two_real_and_different_users`) — otherwise `MERGE_USER("u1", "u1")`
would double `u1`'s capacity out of nothing.

---

## 7. Does `DELETE_FILE` refund capacity?

**Chosen:** yes, to the owner (`l3_delete_gives_capacity_back`).

Storage that is deleted but still charged is not storage. Falls out for free if you
compute used space by summing the owner's files rather than maintaining a counter — and
that is the design hint for level 4, where restore has to recompute it anyway.

---

## 8. `RESTORE_USER` — what exactly does it restore?

**Chosen:** it *replaces* the user's file set. Concretely: delete every file the user
currently owns, then re-add each file in the backup whose name is free. Return how many
were re-added.

Visible in `l4_backup_then_restore`. Two consequences the cases pin down:

- Files the user added after the backup disappear (`/c` in the visible case).
- Restoring twice gives the same answer both times (`l4_restore_twice_is_stable`) — it is
  idempotent, not a no-op.

---

## 9. What if a backed-up name now belongs to someone else?

**Chosen:** skip it, do not count it, and leave the other user's file alone.

Visible in `l4_restore_skips_names_someone_else_took`: `u1` backs up `/a` and `/b`, `/a`
is deleted and re-added by `u2`, and the restore returns `1`. A restore that seized `/a`
back would let one user destroy another's data, which no storage service does.

This is the case that makes the return value meaningful — without collisions,
`RESTORE_USER` would always return the backup's size and there would be nothing to count.

---

## 10. Restoring with no backup

**Chosen:** no-op, return `0`. The user keeps everything they have
(`l4_restore_with_no_backup_does_nothing`).

Stated in `CONTRACT.md` so it is knowable. The alternative — treating "no backup" as an
empty backup and wiping the user — is a data-loss footgun, and a candidate who chose it
would be right to be annoyed at being marked wrong, so it is not left to guesswork.

Note the contrast with `l4_backup_of_a_user_with_no_files`: an *empty backup* is a real
backup, and restoring it does wipe the user. "No backup" and "a backup of nothing" are
different things.

---

## 11. Does a merge carry the absorbed user's backup?

**Chosen:** no. `u2`'s backup dies with `u2`; `u1` keeps its own.

`l4_merge_takes_the_absorbed_user_away_entirely` and
`l4_restore_after_a_merge_uses_the_survivors_backup` are the pair. The second is worth
reading twice: `u1` backs up, then absorbs `u2`, then restores — and `u2`'s files vanish,
because they became `u1`'s and `u1`'s backup predates them. That is surprising, correct,
and exactly the kind of interaction level 4 is built to probe.

**Also defensible:** merging the two backups. Nothing supports it, and it would mean a
merge silently rewrote history the first user had already saved.

---

## 12. Snapshots must not alias live state

`l4_a_backup_is_a_snapshot_not_a_view`: back up, add a file, restore. If the backup held
a reference to the live file set rather than a copy, the new file would have leaked in.

`dict(...)` is enough here because the values are integers; a nested structure would need
`copy.deepcopy`. Knowing which one you need is the point.

---

## Where the time actually goes

1. **`0` treated as failure** from `ADD_FILE_BY`. Costs a level-3 case and is invisible
   until an exact fit shows up.
2. **Capacity debited before validation**, so a rejected add permanently shrinks a user.
3. **Maintaining a `used` counter** instead of deriving it, then forgetting to fix it in
   `DELETE_FILE`, `MERGE_USER` and `RESTORE_USER` — three places, and the third only
   fails in one hidden case.
4. **Restore that seizes names back** from other users.
5. **Confusing "no backup" with "an empty backup"**, which wipes data.
