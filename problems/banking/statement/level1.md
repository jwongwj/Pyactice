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
