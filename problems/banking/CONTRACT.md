# Contract — Banking System

Types and shapes, the way the starter code's type hints and the visible samples would
tell you. **Available during an attempt** (`./pfs contract`).

## Class

```python
class BankingSystem:
    def __init__(self) -> None: ...
```

A fresh `BankingSystem()` per test case.

## Types

| Operation | Signature | Returns |
| --- | --- | --- |
| `CREATE_ACCOUNT` | `(timestamp: int, account_id: str) -> bool` | whether it was created |
| `DEPOSIT` | `(timestamp: int, account_id: str, amount: int) -> int \| None` | new balance, or `None` |
| `TRANSFER` | `(timestamp: int, source_id: str, target_id: str, amount: int) -> int \| None` | the **source's** new balance, or `None` |
| `TOP_SPENDERS` | `(timestamp: int, n: int) -> list[str]` | `["<account_id>(<total outgoing>)", ...]` |
| `PAY` | `(timestamp: int, account_id: str, amount: int) -> str \| None` | `"payment<n>"`, or `None` |
| `GET_PAYMENT_STATUS` | `(timestamp: int, account_id: str, payment: str) -> str \| None` | a status string, or `None` |
| `MERGE_ACCOUNTS` | `(timestamp: int, account_id_1: str, account_id_2: str) -> bool` | whether they merged |
| `GET_BALANCE` | `(timestamp: int, account_id: str, time_at: int) -> int \| None` | balance at `time_at`, or `None` |

Notes that follow from the signatures:

* **Every operation takes `timestamp` first**, including the level-1 ones. There is no
  untimed variant to refactor away — unlike the other problems in this bank, the time
  parameter is there from the start. What arrives at level 3 is not time, it is *delayed
  effects*.
* `TRANSFER` returns the **source's** balance. Not the target's, not a bool.
* Amounts and balances are `int`. `0` is a balance, not an absence — `DEPOSIT` of `0` is
  a legal way to read a balance, and the tests use it that way.
* `GET_PAYMENT_STATUS` returns exactly `"IN_PROGRESS"` or `"CASHBACK_RECEIVED"`.
* `TOP_SPENDERS` returns `list[str]`, formatted by plain concatenation. Empty is `[]`.

## Time

* Timestamps are integer **milliseconds** and are **strictly increasing** across calls,
  except that `GET_BALANCE`'s `time_at` may point anywhere at or before `timestamp`.
<!-- level: 3 -->
* 24 hours is `86400000` milliseconds.
* Cashback is `2%` of the paid amount, **rounded down**, credited exactly `86400000` ms
  after the payment. At that exact millisecond it has already landed.
<!-- /level -->

## Rules stated here so they are not guesswork

* A refused operation changes nothing: no partial transfer, no balance moved.
<!-- level: 3 -->
* A refused operation also consumes no payment id.
<!-- /level -->
<!-- level: 3 -->
* Payment ids are assigned across the whole bank, not per account: the first successful
  `PAY` anywhere is `"payment1"`.
* `TOP_SPENDERS` includes accounts that have never sent anything, with a total of `0`.
* Money received, and money deposited, are not spending.
<!-- /level -->

## Scale

A handful of accounts and a few dozen operations. Nothing needs an index.
