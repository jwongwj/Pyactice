# Problem briefs — research provenance

> **All four are now authored and verified** — see `STATE.md`. This file is kept as the
> record of where their operation names and semantics came from, and of what was
> uncertain at the time. If you ever need to defend or revise a signature, start here.
> The authoritative statement of what each problem actually does is its own
> `CONTRACT.md` and `DECISIONS.md`.

Researched starting points for the reconstructed problems. These are
**briefs, not specifications**: the signatures below are what sources report, and each
needs re-checking against the web before authoring. What matters more than the exact
names is the list of ambiguities under each one — those are what `DECISIONS.md` has to
resolve, and getting them wrong makes the practice lie.

Author with `.claude/skills/harness-engineering/SKILL.md` and run both verification
gates. Provenance and confidence conventions: see `ASSESSMENT_BRIEF.md`.

---

## `cloud_storage` — Cloud File Storage with Users

Class `CloudStorage`. Reported at Ramp, Coinbase and others.

```
L1  ADD_FILE(name, size) -> bool                   false if the name is taken
    GET_FILE_SIZE(name) -> int | None
    DELETE_FILE(name) -> int | None                size of the deleted file
L2  GET_N_LARGEST(prefix, n) -> list[str]          size desc, ties by name asc; [] if none
L3  ADD_USER(user_id, capacity) -> bool
    ADD_FILE_BY(user_id, name, size) -> int | None remaining capacity, None if it will not fit
    MERGE_USER(user_id_1, user_id_2) -> int | None user_2's files and capacity move to
                                                   user_1; user_2 is deleted
L4  BACKUP_USER(user_id) -> int                    number of files backed up
    RESTORE_USER(user_id) -> int                   number of files restored
```

There is an implicit `admin` user with unlimited capacity owning everything added via
`ADD_FILE`.

**Ambiguities to resolve and document:**
- Capacity arithmetic on merge — do the two capacities add, and does used space carry?
- Does a rejected `ADD_FILE_BY` consume anything? (It must not; make it a case.)
- Does `DELETE_FILE` refund capacity to the owner?
- What does `RESTORE_USER` do to files the user created *after* the backup?
- On restore, what if a name has since been taken by a different user?
- Restoring a user who never backed up — no-op or error?
- Does `GET_N_LARGEST` see other users' files?

**Level-4 trap worth building a case for:** a shallow copy for the backup, so later
writes corrupt the snapshot.

---

## `in_memory_db` — In-Memory Key-Value Database

Class `InMemoryDB`. The most widely reported family after file hosting.

```
L1  SET(key, field, value) -> None
    GET(key, field) -> str | None
    DELETE(key, field) -> bool
L2  SCAN(key) -> list[str]                     ["<field>(<value>)", ...] sorted by field asc
    SCAN_BY_PREFIX(key, prefix) -> list[str]   same, restricted to fields with that prefix
L3  SET_AT(key, field, value, timestamp) -> None
    SET_AT_WITH_TTL(key, field, value, timestamp, ttl) -> None
    DELETE_AT(key, field, timestamp) -> bool
    GET_AT(key, field, timestamp) -> str | None
    SCAN_AT(key, timestamp) -> list[str]
    SCAN_BY_PREFIX_AT(key, prefix, timestamp) -> list[str]
L4  BACKUP(timestamp) -> int                   count of non-empty, non-expired records
    RESTORE(timestamp, timestamp_to_restore) -> None
```

**Note the argument order: `timestamp` comes LAST here**, unlike `file_hosting` where it
comes first. That is what the sources report and it is a genuine trap worth preserving —
state it explicitly in `CONTRACT.md`.

The return shape `"<field>(<value>)"` is also different from `file_hosting`'s bare names.
Keep it; varying the output shape across problems is part of what stops the bank from
being memorised.

**Ambiguities to resolve and document:**
- TTL interval — use `[t, t+ttl)`, consistent with `file_hosting`.
- Does `SET` on an existing field refresh its TTL or preserve it?
- Does a plain `SET` (no timestamp) mean timestamp 0 and no expiry?
- `RESTORE` is the level-4 crux: it restores the latest backup at or before
  `timestamp_to_restore`, and TTLs are *recalculated*. Decide precisely what that means —
  most readings re-anchor each surviving field's remaining lifetime to the restore
  timestamp — and demonstrate it with a **visible** case. Do not leave it to a hidden one.
- What happens to records created after the backup being restored?
- `BACKUP` counts "non-empty, non-expired records" — a record whose every field expired
  must not count.

---

## `banking` — Banking System

Class `BankingSystem`. Reported at Ramp, eBay and others. Timestamps are **milliseconds**
and strictly increasing across calls.

```
L1  CREATE_ACCOUNT(timestamp, account_id) -> bool
    DEPOSIT(timestamp, account_id, amount) -> int | None            new balance
    TRANSFER(timestamp, source_id, target_id, amount) -> int | None source's new balance
L2  TOP_SPENDERS(timestamp, n) -> list[str]    ["<account_id>(<total_outgoing>)", ...]
                                                outgoing desc, ties by account_id asc
L3  PAY(timestamp, account_id, amount) -> str | None    returns "payment1", "payment2", ...
    GET_PAYMENT_STATUS(timestamp, account_id, payment) -> str | None
                                                "IN_PROGRESS" / "CASHBACK_RECEIVED"
L4  MERGE_ACCOUNTS(timestamp, account_id_1, account_id_2) -> bool
    GET_BALANCE(timestamp, account_id, time_at) -> int | None       balance at a past instant
```

2% cashback on `PAY`, refunded 24 hours later (86_400_000 ms).

This is the odd one out and the most interesting: level 3 introduces **deferred effects**
rather than expiry. Cashback must land even if nothing else happens, so every operation
has to advance pending cashbacks to the current timestamp before doing its own work. That
is a different refactor from the `*_at` pattern and worth having in the bank for exactly
that reason.

**Ambiguities to resolve and document:**
- Cashback rounding — floor of `amount * 2 // 100`.
- Ordering at the same timestamp: does cashback land before or after the current
  operation? (Before. Make it visible.)
- Does `TOP_SPENDERS` include accounts with zero outgoing? (Yes.)
- Does a merged-away account's outgoing total count toward the survivor?
- Does pending cashback for the absorbed account pay into the survivor?
- Is a transfer to self rejected?
- Does `GET_BALANCE` at a time before the account existed return `None`?
- Does `PAY` count as outgoing for `TOP_SPENDERS`? Does the cashback reduce it?

---

## `file_system` — Hierarchical File System

Class `FileSystem`. Added 2026-08-14 to raise the bank's ceiling. Reported at Meta
(the progressive OA that replaced their four-separate-questions format), Coinbase and
Anthropic; all three appear to draw on the same CodeSignal progressive-workspace
template, re-skinned. Closest public analogues for the shape are LeetCode 588 (Design
In-Memory File System) and 1166 (Design File System).

```
L1  MKDIR(path) -> bool                            parent must exist; no mkdir -p
    CREATE_FILE(path, content) -> bool
    READ_FILE(path) -> str | None
    LS(path) -> list[str]                          child NAMES, sorted; a file lists itself
L2  MV(source, dest) -> bool                       no overwrite; not into your own subtree
    RM(path) -> int                                number of FILES removed
    FIND(path, name) -> list[str]                  full PATHS, sorted, at or below path
L3  CHMOD(path, user, perms) -> bool               perms from "rw"; applies to the subtree
    READ_FILE_AS(user, path) -> str | None         needs r
    CREATE_FILE_AS(user, path, content) -> bool    needs w on the parent
    RM_AS(user, path) -> int                       needs w on everything, or removes nothing
L4  SYMLINK(path, target) -> bool                  target need not exist
    RESOLVE(path) -> str | None                    None on a loop or a dangling link
```

Reported escalation, which this follows: create/read → paths → permissions → symlinks.
Level 3 is where multiple candidates reported getting stuck.

**Why it is in the bank.** Every other problem here is a flat `name -> value` map, so
level 1 has no wrong answer and the format's central pressure — a level-1 design
decision coming due at level 3 — cannot be exercised. Here a flat `dict[path]` clears
most of level 1 and then loses to two things: permissions keyed by path are orphaned by
the first `MV`, and link resolution has to happen inside every traversal rather than as
a string rewrite.

**Ambiguities resolved and documented** — the full list with reasoning is
`problems/file_system/DECISIONS.md`; the ones most worth knowing:
- `LS` of a file returns `["<its own name>"]` (588's behaviour), not `[]`.
- `RM` counts files only, so an empty directory returns `0` *and is still removed*.
  `0` is information, not a failure flag.
- The move cycle check must be component-wise: `/ab` is not inside `/a`.
- `FIND` includes the start path if its own name matches, and matches directories.
- `CHMOD(path, user, "")` is a real grant that overrides an ancestor's, not a no-op.
- Permissions attach to the entry, so they travel with `MV`. **Visible case**, because
  the prose supports both readings.
- A trailing link is followed by `READ_FILE`, `LS`, `FIND` and `CHMOD`, and not by
  `MKDIR`, `CREATE_FILE`, `SYMLINK`, `MV` or `RM`. Stated outright in the statement:
  guessing POSIX from scratch is not the skill under test.
- A symlink is not a file, so `RM` never counts one.
- `FIND` does not descend into links — otherwise it does not terminate.
