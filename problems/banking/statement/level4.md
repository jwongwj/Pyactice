# Scenario

Your task is to implement a simplified version of a banking system.
All operations that should be supported are listed below. Partial credit will be granted for each test passed, so
run the tests often to receive partial credit for passed tests. Please check tests for requirements
and argument types.

### Implementation Tips

Read the question all the way through before you start coding, but implement the operations and complete the
levels one by one, not all together, keeping in mind that you will need to refactor to support additional functionality.
Please, do not change the existing method signatures.

## Task

All operations take a `timestamp` in **milliseconds**. Timestamps are strictly increasing across calls.

## Level 1 – Initial Design & Basic Functions

- **CREATE_ACCOUNT(timestamp, account_id)**
  - Creates a new account with the given identifier if it doesn't already exist. Returns whether the
    account was created.
- **DEPOSIT(timestamp, account_id, amount)**
  - Deposits the given amount into the account. Returns the balance after the operation, or nothing if
    the account doesn't exist.
- **TRANSFER(timestamp, source_id, target_id, amount)**
  - Transfers the given amount from one account to another. Returns the balance of `source_id` after the
    operation.
  - Returns nothing if either account doesn't exist, if `source_id` and `target_id` are the same, or if
    the source account has insufficient funds.

## Level 2 – Data Structures & Data Processing

- **TOP_SPENDERS(timestamp, n)**
  - Returns the identifiers of the top `n` accounts with the highest amount of money **transferred out**
    of the account, in the form `"<account_id>(<total outgoing>)"`, ordered by that total in descending
    order, and in case of a tie by account identifier.

## Level 3 – Refactoring & Encapsulation

The bank now supports payments with cashback.

- **PAY(timestamp, account_id, amount)**
  - Withdraws the given amount from the account. Returns a unique identifier for the payment in the form
    `"payment[ordinal number of the payment]"`, e.g. `"payment1"`, `"payment2"`.
  - Returns nothing if the account doesn't exist or has insufficient funds.
  - The withdrawn amount counts towards the account's total outgoing.
  - **2%** of the amount is refunded to the account as cashback **24 hours** after the payment
    (86400000 milliseconds). Cashback is rounded down to the nearest integer.
- **GET_PAYMENT_STATUS(timestamp, account_id, payment)**
  - Returns the status of the payment: `"IN_PROGRESS"` or `"CASHBACK_RECEIVED"`.
  - Returns nothing if the account doesn't exist, the payment doesn't exist, or the payment was not made
    by the given account.

## Level 4 – Extending Design & Functionality

- **MERGE_ACCOUNTS(timestamp, account_id_1, account_id_2)**
  - Merges `account_id_2` into `account_id_1`. Returns whether the accounts were merged.
  - The balances and the outgoing totals are combined, and `account_id_2` is removed.
  - Cashback that has not yet been paid out is still paid, into `account_id_1`.
- **GET_BALANCE(timestamp, account_id, time_at)**
  - Returns the balance of the account at the given `time_at`.
  - Returns nothing if the account doesn't exist, or did not exist at `time_at`.
