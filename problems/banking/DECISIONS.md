# Decisions — Banking System

**Answer key. Read after `./pfs finish`, not during.**

---

## 1. The level-3 refactor is not what you expect

The other three problems in this bank turn level 3 into "add a timestamp to everything".
This one already has timestamps everywhere. What level 3 adds is an effect that happens
**later than the call that caused it**.

That changes the shape of the refactor. Instead of `do_thing → do_thing_at`, you need
every single operation to begin by advancing the world to its own timestamp:

```python
def _advance(self, timestamp):
    # pay out every cashback due at or before `timestamp`, oldest first
```

Miss this and the symptom is bizarre: balances are correct whenever a cashback happens to
coincide with an operation and wrong otherwise. `l3_cashback_arrives_before_the_operation_that_notices_it`
is the case that forces it — a `PAY` that only succeeds because the cashback landed on the
same millisecond, before the payment is judged.

The general lesson is worth more than the specific rule: **when a system has scheduled
effects, "now" has to be pushed forward before anything is read or written.** Every
operation is a barrier.

---

## 2. Cashback timing and rounding

**Chosen:** `amount * 2 // 100`, floored, credited at exactly `payment_timestamp + 86400000`.
At that millisecond it has arrived; one millisecond earlier it has not.

`l3_cashback_lands_on_the_exact_millisecond` pins the boundary,
`l3_cashback_is_rounded_down` pins the arithmetic — including a payment of `49`, whose
2% is `0.98` and whose cashback is therefore `0`. A zero cashback is still a cashback: the
payment's status becomes `CASHBACK_RECEIVED` when its time comes.

**Also defensible:** rounding to nearest. Nothing reports it, and floor is what integer
division gives you for free.

---

## 3. Does paying count as spending?

**Chosen:** yes. `PAY` adds to the account's outgoing total exactly like `TRANSFER`
(`l3_paying_counts_as_spending`). The statement says the withdrawn amount counts, and it
is money leaving the account.

**And the cashback does not take it back** (`l3_cashback_does_not_reduce_what_you_spent`).
The refund is income. An account that pays `100` has spent `100` forever, even after the
`2` comes back.

---

## 4. Payment ids

**Chosen:** one global counter, incremented only on success.

Two consequences the cases pin down. The counter is not per account, so `a` paying then
`b` paying gives `payment1` and `payment2` (`l3_payment_ids_are_global_and_owned`). And a
refused payment does not burn an id — after three failures, the first success is still
`payment1` (`l3_payments_that_must_be_refused`).

A payment also **belongs** to one account. `GET_PAYMENT_STATUS` returns `None` when asked
about someone else's payment, which is a different thing from the payment not existing —
but both look the same to the caller, deliberately.

---

## 5. `TOP_SPENDERS` includes accounts that never spent

**Chosen:** yes, with a total of `0`. Visible in `l2_ranked_by_money_sent`, where `c` is
ranked last with `c(0)` despite never sending anything.

**Also defensible:** filtering them out. But "top n spenders" with fewer than n results
when n accounts exist reads as a bug, and the reported format has no way to express
"absent" versus "zero".

The tie-break trap here is the same one every problem in this family has, with an extra
sting: because Python's `sort` is stable, forgetting the tie-break gives you *creation
order*, which looks alphabetical in most hand-written tests. `l2_ties_and_the_cap` and
`l2_id_tie_break_is_lexicographic` deliberately create accounts out of order so that
stability cannot rescue a missing tie-break.

---

## 6. Merge: what moves?

**Chosen:** balance, outgoing total, and any in-flight cashback all move to
`account_id_1`. `account_id_2` is deleted, and its id becomes available again.

Visible in `l4_merge_combines_money_and_history` and
`l4_merge_carries_a_pending_cashback`. The second is the interesting one: `b` pays, then
is merged into `a`, and a day later the `2` lands in `a`. If your pending cashbacks are
keyed by account id and you delete the account without redirecting them, the money simply
vanishes — and nothing fails for 24 simulated hours.

`GET_PAYMENT_STATUS` for that payment must now be asked of `a`; asking `b` returns `None`
because `b` no longer exists.

---

## 7. Merge and history

**Chosen:** `account_id_1` keeps its own history. `GET_BALANCE(t, "a", before_the_merge)`
returns what `a` alone held then, not the combined figure
(`l4_history_before_a_merge_is_the_survivors_own`).

And the absorbed account is gone completely — `GET_BALANCE` for it returns `None` even for
instants when it demonstrably existed (`l4_the_absorbed_account_is_gone_for_good`).

**Also defensible:** keeping `b`'s history queryable, or back-filling `a`'s history with
the sum. Both require deciding what the merged history of two accounts even means at a
moment when they were separate, and neither is reported. The chosen rule is the one you
get by storing history per live account and deleting it with the account.

Note the id becomes free again afterwards, and re-creating it starts a fresh history from
zero.

---

## 8. `GET_BALANCE` semantics

**Chosen:** the balance as of the *last change at or before* `time_at`. Changes made
exactly at `time_at` are included (`l4_balance_at_the_current_instant`). A `time_at`
before the account was created returns `None`, not `0`
(`l4_balance_at_a_past_instant`).

Cashback that landed at or before `time_at` counts; cashback that lands later does not,
even if `timestamp` is past it (`l4_balance_history_sees_cashback_when_it_lands`). This is
the case that catches an implementation that advances the clock and then reports the
*current* balance regardless of `time_at`.

Refused operations leave no history entry (`l4_history_ignores_refused_operations`), and
a transfer writes a history entry for **both** sides
(`l4_history_records_transfers_on_both_sides`) — forgetting the target is easy, because
the return value only concerns the source.

---

## 9. Failure is a return value, not an exception

Nothing here raises. `CREATE_ACCOUNT` and `MERGE_ACCOUNTS` return `False`; everything else
returns `None`. As in `cloud_storage` and unlike `file_hosting` — read the stub's return
type before deciding how to signal failure.

---

## Where the time actually goes

1. **Not advancing pending cashback at the start of every operation.** The single
   defining mistake of this problem. Symptoms are intermittent and look like arithmetic
   bugs.
2. **Overwriting balances instead of appending to a history**, which makes level 4 a
   rewrite rather than a query.
3. **A missing tie-break hidden by sort stability**, so the ranking looks right until the
   accounts are created out of alphabetical order.
4. **Losing an absorbed account's pending cashback** on merge — silent, and 24 simulated
   hours late.
5. **Recording only the source side of a transfer** in the history.
