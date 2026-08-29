# Scenario

Your task is to implement a simplified version of an in-memory database.
All operations that should be supported are listed below. Partial credit will be granted for each test passed, so
run the tests often to receive partial credit for passed tests. Please check tests for requirements
and argument types.

### Implementation Tips

Read the question all the way through before you start coding, but implement the operations and complete the
levels one by one, not all together, keeping in mind that you will need to refactor to support additional functionality.
Please, do not change the existing method signatures.

## Task

The database holds **records**. Each record is identified by a key and contains any number of
**fields**, and each field holds a value:

```plaintext
{
  "user-1": { "name": "Ada",  "role": "admin", "team": "core" },
  "user-2": { "name": "Grace" }
}
```

## Level 1 – Initial Design & Basic Functions

- **SET(key, field, value)**
  - Insert a field-value pair into the record associated with the key.
  - If the field already exists, its value is replaced.
- **GET(key, field)**
  - Returns the value of the field, or nothing if the record or the field doesn't exist.
- **DELETE(key, field)**
  - Removes the field from the record. Returns whether a field was removed.

## Level 2 – Data Structures & Data Processing

- **SCAN(key)**
  - Returns a list of the record's fields and values in the form `"<field>(<value>)"`, sorted by field name.
- **SCAN_BY_PREFIX(key, prefix)**
  - Same as SCAN, but only fields whose name starts with the given prefix.

## Level 3 – Refactoring & Encapsulation

Fields now might have a specified time to live. Implement extensions of existing methods which inherit
all functionality but also with an additional parameter to include a timestamp for the operation, and new
fields might specify the time to live - no ttl means lifetime being infinite.

- **SET_AT(key, field, value, timestamp)**
- **SET_AT_WITH_TTL(key, field, value, timestamp, ttl)**
  - The field is available for ttl seconds.
- **DELETE_AT(key, field, timestamp)**
- **GET_AT(key, field, timestamp)**
- **SCAN_AT(key, timestamp)**
- **SCAN_BY_PREFIX_AT(key, prefix, timestamp)**
  - Results should only include fields that are still "alive".

## Level 4 – Extending Design & Functionality

- **BACKUP(timestamp)**
  - Saves the state of the database at the given timestamp, including the remaining time to live for
    all records and fields.
  - Returns the number of non-empty non-expired records in the database.
- **RESTORE(timestamp, timestamp_to_restore)**
  - Restores the database from the latest backup taken before or at `timestamp_to_restore`.
  - All ttls should be recalculated accordingly.
