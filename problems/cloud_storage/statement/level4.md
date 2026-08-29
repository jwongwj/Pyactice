# Scenario

Your task is to implement a simplified version of a cloud storage service.
All operations that should be supported are listed below. Partial credit will be granted for each test passed, so
run the tests often to receive partial credit for passed tests. Please check tests for requirements
and argument types.

### Implementation Tips

Read the question all the way through before you start coding, but implement the operations and complete the
levels one by one, not all together, keeping in mind that you will need to refactor to support additional functionality.
Please, do not change the existing method signatures.

## Task

Files are stored by name. Names may look like paths, but the storage is flat:

```plaintext
/file-1.zip            4321
/dir-a/dir-c/file-2.txt 1100
/dir-a/dir-c/file-3.csv 2122
/dir-b/file-4.mdx       3378
```

## Level 1 – Initial Design & Basic Functions

- **ADD_FILE(name, size)**
  - Add a new file to the storage. Returns whether the file was added.
  - If a file with the same name already exists, the operation fails.
- **GET_FILE_SIZE(name)**
  - Returns the size of the file, or nothing if the file doesn't exist.
- **DELETE_FILE(name)**
  - Removes the file and returns its size, or nothing if the file doesn't exist.

## Level 2 – Data Structures & Data Processing

- **GET_N_LARGEST(prefix, n)**
  - Returns the names of the top `n` files starting with the provided prefix, ordered by their size in
    descending order, and in case of a tie by file name.
  - Returns nothing if there are no matching files.

## Level 3 – Refactoring & Encapsulation

The storage should now support multiple users. Each user is given a storage capacity, and all files a user
adds count against it. Files added through `ADD_FILE` belong to the system and are not charged to any user.

- **ADD_USER(user_id, capacity)**
  - Registers a new user with the given storage capacity. Returns whether the user was added.
- **ADD_FILE_BY(user_id, name, size)**
  - Adds a file owned by the user. Returns the user's remaining capacity, or nothing if the file could
    not be added.
- **MERGE_USER(user_id_1, user_id_2)**
  - Merges `user_id_2` into `user_id_1`: the second user's files and capacity are transferred to the
    first, and the second user is removed. Returns the first user's remaining capacity.

## Level 4 – Extending Design & Functionality

- **BACKUP_USER(user_id)**
  - Saves the state of the user's current files. Returns the number of files that were backed up.
- **RESTORE_USER(user_id)**
  - Restores the state of the user's files to the latest backup. Returns the number of files restored.
  - If a file from the backup has since been added by another user, it is not restored.
