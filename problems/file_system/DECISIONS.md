# Decisions — Hierarchical File System

The answer key. **Locked during an attempt** (`./pfs decisions` refuses while a session is
live). Every entry is a place where the statement admits more than one reading; each one
names the reading the grader uses, what else a candidate plausibly does, and which case
pins it down.

---

## 1. `LS` of a file returns the file's own name

**Chosen:** `LS("/readme.md")` → `["readme.md"]`.
**Alternatives:** `[]`, or `None`, or the file's content split somehow.
**Why:** this is LeetCode 588's behaviour and the shape the whole family inherits. It is
also the only reading under which `LS` never needs the caller to know in advance whether
a path is a file.
**Pinned by:** `l1_ls_of_a_file_is_its_own_name` (visible).
**Failure mode:** returning `[]` looks right until a test lists a file directly, which
candidates never write themselves.

## 2. `MKDIR` is not `mkdir -p`

**Chosen:** the parent must already exist; `MKDIR("/a/b")` on an empty tree fails and
creates nothing — not even `/a`.
**Alternatives:** create intermediates; or create intermediates but return `False`.
**Why:** stated outright in level 1, and the partial-creation variant is the one that
silently corrupts later levels.
**Pinned by:** `l1_parent_must_exist` (visible).

## 3. `""` is content, `None` is absence

**Chosen:** `READ_FILE` on a file created with `""` returns `""`, compared with `Exactly`
so leniency cannot wave it through.
**Alternatives:** `None`, via `return self.files.get(path) or None`.
**Why:** the contract types the return as `str | None`, and a zero-length file is a file.
**Pinned by:** `l1_empty_content_is_a_value`.
**Failure mode:** `or None` and truthiness checks on `content`. This is the single most
common one-character bug in the family.

## 4. `RM` counts files, not entries

**Chosen:** directories and links are not files. `RM` of a directory holding two files and
three subdirectories returns `2`. `RM` of an empty directory returns `0` **and still
removes it**.
**Alternatives:** count every removed entry; count directories too; treat `0` as failure
and leave the directory in place.
**Why:** "returns the number of files removed" is the statement's wording, and the return
value is information, not a success flag — every other operation here signals failure with
`False` or `None`, not with `0`.
**Pinned by:** `l2_rm_counts_the_files_in_the_subtree` and
`l2_rm_of_an_empty_directory_returns_zero` (both visible, because a `0` that means success
is exactly the kind of thing nobody guesses).

## 5. `MV` never overwrites, and cannot move a directory into itself

**Chosen:** `MV` fails if anything exists at `dest`, if `dest`'s parent is missing, if
`source` is missing, if `source` is the root, or if `dest` is at or below `source`.
`MV("/a", "/a")` fails under that last rule.
**Alternatives:** overwrite the destination (the `mv(1)` behaviour); allow the self-move as
a no-op returning `True`; detect the cycle by string prefix, which wrongly rejects
`MV("/a", "/ab")`.
**Why:** the statement says a directory cannot be moved to a path inside itself, and
`/ab` is not inside `/a`. The prefix bug is in the mutation catalogue.
**Pinned by:** `l2_a_directory_cannot_move_inside_itself` (visible), `l2_mv_will_not_overwrite`.

## 6. `FIND` includes the start path and matches directories

**Chosen:** "at or below `path`" includes `path` itself, and matching is on the last path
component of any entry — file, directory, or link.
**Alternatives:** files only; strict descendants only; substring matching instead of
equality.
**Why:** the statement says "every entry at or below `path`", and says nothing to
distinguish files from directories.
**Pinned by:** `l2_find_matches_directories_and_the_start_path` (visible),
`l2_find_only_matches_the_last_component`.

## 7. Permissions resolve to the deepest explicit grant, and `""` is a real grant

**Chosen:** walk from the entry up to the root; the first entry carrying a record for that
user decides. No record anywhere means no permissions. `CHMOD(path, user, "")` records an
explicit empty permission, which therefore beats any ancestor's grant.
**Alternatives:** union of every ancestor's grant (so a deeper `""` cannot take anything
away); nearest grant but treating `""` as "no record" (same effect); shallowest wins.
**Why:** "gives `user` exactly the permissions in `perms`" plus "a grant made further down
the tree replaces whatever an ancestor granted" only works if `""` is a value.
**Pinned by:** `l3_a_deeper_grant_replaces_the_ancestors` (visible),
`l3_a_later_grant_replaces_the_earlier_one`.

## 8. A grant is attached to the entry, not to the path string

**Chosen:** moving a directory carries its permission records, and its descendants', with
it. After `CHMOD("/a", "bob", "r")` and `MV("/a", "/b/a")`, bob can still read
`/b/a/f`.
**Alternatives:** keep a `dict[path, dict[user, perms]]` so a move silently orphans every
grant; or rewrite the keys on move, which is the same decision implemented painfully.
**Why:** this is the level-3 half of the design trap. Both readings are defensible from the
prose alone, which is exactly why it gets a visible case rather than a hidden one.
**Pinned by:** `l3_a_grant_travels_with_a_moved_directory` (visible).
**Failure mode:** a path-keyed permission table clears every other level-3 case and fails
only this one — the signature of a level-1 design choice coming due.

## 9. A grant covers entries created after it

**Chosen:** the grant applies to the subtree as it is at each check, not as it was when the
grant was made. `CHMOD("/", "bob", "rw")` on an empty tree covers everything made later.
**Alternatives:** stamp the permission onto every existing descendant at `CHMOD` time,
which is the natural implementation if you are storing permissions per entry and eagerly.
**Why:** "applies to everything beneath it" is a statement about the tree, not about a
moment.
**Pinned by:** `l3_a_grant_on_root_covers_paths_made_later`.

## 10. `RM_AS` is all-or-nothing

**Chosen:** check write permission on the path and on every entry in its subtree first;
if any is missing, remove nothing and return `0`.
**Alternatives:** remove what you can and return that count — the tempting recursive
implementation, which leaves a half-deleted tree behind.
**Why:** "if any part of it cannot be removed, nothing is removed" is stated, and the
bank's `atomicity` invariant says a rejected operation leaves no trace.
**Pinned by:** `l3_rm_as_is_all_or_nothing` (visible), `l3_rm_as_needs_write_on_the_path_itself`.

## 11. Levels 1 and 2 stay administrative

**Chosen:** `READ_FILE`, `CREATE_FILE`, `MKDIR`, `LS`, `MV`, `RM` and `FIND` never check
permissions, at any level.
**Alternatives:** retrofit checks onto them at level 3, which breaks every level-1 and
level-2 case at once.
**Why:** the same split as `ADD_FILE` / `ADD_FILE_BY` in `cloud_storage`, and stated in
level 3's preamble.
**Pinned by:** `l3_admin_operations_bypass_permissions`, and every level-1/2 regression case.

## 12. A trailing link is followed for reads and not for writes

**Chosen:** a link in the middle of a path is always followed. As the last component it is
followed by `READ_FILE`, `READ_FILE_AS`, `LS`, `FIND`'s start path and `CHMOD`; it is not
followed by `MKDIR`, `CREATE_FILE`, `CREATE_FILE_AS`, `SYMLINK`, `MV`, `RM` or `RM_AS`,
which act on the link entry itself.
**Alternatives:** follow it everywhere (so `RM("/link")` deletes the target — data loss);
follow it nowhere (so `READ_FILE("/link")` returns `None` and links are useless).
**Why:** these are POSIX semantics, and the statement spells the split out because guessing
it is not the skill being tested.
**Pinned by:** `l4_reads_follow_a_trailing_link_but_moves_do_not` (visible),
`l4_rm_removes_the_link_not_the_target` (visible).

## 13. A link is not a file

**Chosen:** `RM` of a link returns `0`; `RM` of a directory does not count links inside it.
**Alternatives:** count links as files, which makes every `RM` count that involves a link
one too high.
**Why:** decision 4 already established that "files" means files. A dangling link has no
content at all, so calling it a file cannot be made coherent.
**Pinned by:** `l4_rm_removes_the_link_not_the_target` (visible),
`l4_rm_of_a_directory_does_not_count_links`.

## 14. `FIND` does not walk through links

**Chosen:** `FIND` walks the real tree. A link is one entry, matched by its own name, and
never descended into.
**Alternatives:** follow links, which either duplicates results or loops forever on
`l4_loops_and_dangling_links_resolve_to_nothing`'s tree.
**Why:** termination. There is no bound on link depth otherwise.
**Pinned by:** `l4_find_does_not_descend_into_links` (visible).

## 15. Unresolvable is `None`, not an error

**Chosen:** loops, dangling targets and non-directories mid-path all make `RESOLVE` return
`None`, and make every read through that path behave exactly as it would for a missing
path — `READ_FILE` → `None`, `LS` → `[]`.
**Alternatives:** raise; return the partially-resolved path; recurse until Python's own
stack limit, which reports as a crash rather than a wrong answer.
**Why:** the contract says nothing here raises. Loop detection needs an explicit visited
set or a hop limit.
**Pinned by:** `l4_loops_and_dangling_links_resolve_to_nothing` (visible),
`l4_a_link_to_a_file_cannot_be_traversed`.

## 16. Permissions attach to the resolved real path

**Chosen:** `CHMOD` follows a trailing link and records the grant on the target entry, so
reading through either name sees the same permissions.
**Alternatives:** record the grant on the link entry, which then does nothing, because
every read resolves past it before checking.
**Why:** follows from decisions 8 and 12 together; there is no third option that is
self-consistent.
**Pinned by:** `l4_permissions_attach_to_the_real_path`.

---

## What this problem is for

The other three filesystem-family problems in this bank are flat maps. This one is the only
one where a level-1 design decision can cost you level 3 or 4, which is the thing the real
progressive format is built to measure. The two decisions that do it are **8** (permissions
keyed by path vs by entry) and **12/14** (resolution as a traversal step vs a string
rewrite). A candidate who reaches for `dict[str, ...]` keyed on the full path clears level 1
in five minutes and then pays for it twice.
