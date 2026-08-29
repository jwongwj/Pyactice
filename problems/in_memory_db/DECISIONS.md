# Decisions — In-Memory Key-Value Database

**Answer key. Read after `./pfs finish`, not during.**

Every point where the statement was open, what this suite chose, why, what else was
defensible, and which case pins it down. Every ambiguous rule has a *visible* case, so
it is learnable from the examples rather than guessable.

---

## 1. `timestamp` is the last argument here

Not a decision so much as a warning. The sources for this problem consistently report
`SET_AT(key, field, value, timestamp)` — timestamp last — while the file hosting problem
in this bank puts it first. Both are kept as reported.

This is worth a deliberate ten seconds in the real thing. Argument order errors between
two `str` parameters, or between two `int` parameters, do not raise; they silently
produce wrong answers that look like logic bugs. Read the stub signature, do not assume.

---

## 2. Scan output format

**Chosen:** `"<field>(<value>)"`, plain concatenation, ordered by field name ascending.

`l2_value_is_pasted_verbatim` checks that nothing is escaped: a value of `"x(y)"`
produces `"f(x(y))"`, and an empty value produces `"g()"`. If you reached for a regex or
a quoting rule, you did more work than the problem wanted.

Ordering is lexicographic on the *field name*, so `"f10"` comes before `"f2"`
(`l2_field_order_is_lexicographic_not_numeric`). Same trap as every other problem in
this family, and it is worth internalising once: these problems never mean numeric order.

---

## 3. Is `""` a value or an absence?

**Chosen:** a value. `GET` returns `""` for a field set to `""`, and `None` only when the
field is not there. `DELETE` on it returns `True`.

The whole point of returning `None` rather than a falsy value is to distinguish the two,
and a database that cannot store an empty string is a broken database. This is the
`l1_empty_string_is_a_value` case, and the harness compares it strictly — the usual
"both mean nothing" leniency is disabled for that one expectation.

The corresponding bug is `if not value:` or `return self.data.get(key, {}).get(field) or None`.

---

## 4. TTL interval

**Chosen:** half-open, `[t, t + n)`. At exactly `t + n` the field is gone.

Same convention as `file_hosting` in this bank, deliberately — learn it once. "Available
for n seconds" means a duration of n, and a closed interval would give n+1 live instants.
`l3_ttl_expiry_boundary` is visible; `l3_zero_ttl_is_dead_on_arrival` follows from it.

**Also defensible:** inclusive. If you assumed it, you failed one visible sample and the
fix is one character.

---

## 5. Does setting an existing field restart its lifetime?

**Chosen:** yes. A `SET` replaces the field entirely — value *and* lifetime.

`SET_AT_WITH_TTL(A, B, "E", 0, 5)` then `SET_AT_WITH_TTL(A, B, "F", 3, 5)` gives a field
alive on `[3, 8)`, not `[0, 5)`. Visible in
`l3_setting_a_field_replaces_its_lifetime`.

It follows that `SET_AT` (no ttl) over a field that had one makes it permanent
(`l3_set_without_ttl_makes_a_field_permanent`). "Set" means set, not "update the value
and keep the old expiry".

**Also defensible:** preserving the original expiry on update. Nobody reports it, and it
would make `SET_AT` unable to ever clear a ttl.

---

## 6. Are the level-1 methods a separate store?

**Chosen:** no. `SET(key, field, value)` is `SET_AT(key, field, value, 0)`.

The statement says the new methods "inherit all functionality" of the old ones. The
intended level-3 refactor is one delegating line per old method:

```python
def set(self, key, field, value):
    return self.set_at(key, field, value, 0)
```

Keeping two stores is the level-3 disaster — levels 1 and 2 go red the moment you add
timestamps. Visible in `l3_plain_calls_are_timestamp_zero`, and enforced by every
`regression` tagged case.

---

## 7. `BACKUP` counts what, exactly?

**Chosen:** the number of **records** (keys) holding at least one field that is alive at
that timestamp. Not fields, and not keys that merely exist.

The statement's phrase is "non-empty non-expired records". A record whose fields have all
been deleted does not count (`l4_backup_ignores_emptied_records`); nor does one whose
fields have all expired (`l4_backup_ignores_expired_records`). A key that was created and
emptied is not a record for this purpose.

---

## 8. `RESTORE` — the level-4 crux

**Chosen:** `RESTORE(timestamp, timestamp_to_restore)` replaces the **entire** database
with the contents of the most recent backup taken at or before `timestamp_to_restore`,
and each restored field's **remaining** lifetime is re-anchored to `timestamp`.

Concretely: a field written at `0` with `ttl = 10` has `5` seconds left when backed up at
`t = 5`. Restoring it at `t = 100` gives it `[100, 105)` — not its original `[0, 10)`, and
not a fresh `10` seconds.

Visible in `l4_restore_re_anchors_remaining_lifetimes`.

**This is the interesting contrast in the whole bank.** The file hosting problem's
`ROLLBACK` says "all ttls should be recalculated accordingly" and the right answer there
is that expiry times *do not move*. This problem says almost the same words and the right
answer is that they *do*. The difference is that a rollback returns you to a past instant,
so remaining lifetimes measured from it are unchanged; a restore drops a preserved
snapshot into the present, so its lifetimes have to be re-anchored or the fields would
arrive already dead.

The lesson is not the rule, it is the habit: work out what "recalculated" can mean *for
this operation*, and check it against the sample.

**Also defensible:** restoring the original absolute expiry times. Under that reading, a
backup restored long enough after the fact restores nothing but corpses, which makes the
feature pointless — which is why it is not the chosen reading.

---

## 9. Does `RESTORE` keep records created after the backup?

**Chosen:** no. It is a replacement, not a merge (`l4_restore_discards_later_writes`).

---

## 10. `RESTORE` when no backup qualifies

**Chosen:** no-op. The database is left exactly as it was
(`l4_restore_with_no_earlier_backup_does_nothing`).

Stated in `CONTRACT.md` so it is knowable rather than a trap. The alternatives — clearing
the database, or raising — are both worse: this operation returns nothing, so it has no
way to tell you it failed.

---

## 11. Are all backups kept, or only the latest?

**Chosen:** all of them. `RESTORE` searches for the latest backup at or before the given
timestamp, which is meaningless if you only keep one.

`l4_restore_picks_the_latest_backup_at_or_before` and `l4_restore_at_an_earlier_backup`
are the pair that distinguishes this: the first restores the newer of two backups, the
second deliberately skips it for the older one. `l4_restore_twice` then checks that both
are still available afterwards.

---

## 12. Snapshots must not alias live state

Not an ambiguity, a bug class. `l4_a_backup_is_a_snapshot_not_a_view` writes to a field
after backing it up and then restores; if the backup shared the inner dict, the write
would have reached into it and the restore would return `"999"`.

`copy.deepcopy` is the one-line answer. A dict comprehension one level deep is not.

---

## Where the time actually goes

1. **Argument order.** Timestamp last here, and it does not raise when you get it wrong.
2. **Two stores at level 3**, taking levels 1 and 2 down with it.
3. **Re-anchoring at level 4.** Most people restore absolute expiry times, pass the
   obvious cases, and fail the one that restores long after the backup.
4. **`or None` on `GET`**, which quietly breaks empty-string values.
5. **A single backup slot**, which passes until a test restores the older of two.
