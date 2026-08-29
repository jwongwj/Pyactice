# Scenario

Your task is to implement a simplified version of a hierarchical file system.
All operations that should be supported are listed below. Partial credit will be granted for each test passed, so
run the tests often to receive partial credit for passed tests. Please check tests for requirements
and argument types.

### Implementation Tips

Read the question all the way through before you start coding, but implement the operations and complete the
levels one by one, not all together, keeping in mind that you will need to refactor to support additional functionality.
Please, do not change the existing method signatures.

## Task

The file system holds directories and files arranged in a tree. Paths are absolute, use `/` as a
separator, and never contain `.` or `..`. The root directory `/` always exists.

```plaintext
/
├── docs
│   ├── notes.txt        "hello"
│   └── img
│       └── logo.png     "PNG"
└── readme.md            "read me"
```

## Level 1 – Initial Design & Basic Functions

- **MKDIR(path)**
  - Creates a new directory. Returns whether it was created.
  - The parent directory must already exist; intermediate directories are not created for you.
  - Fails if anything already exists at that path.
- **CREATE_FILE(path, content)**
  - Creates a new file holding `content`. Returns whether it was created.
  - The parent directory must already exist.
  - Fails if anything already exists at that path.
- **READ_FILE(path)**
  - Returns the content of the file, or nothing if there is no file at that path.
- **LS(path)**
  - If the path is a directory, returns the names of its immediate children, ordered lexicographically.
  - If the path is a file, returns just that file's own name.
  - Returns nothing if the path does not exist.
