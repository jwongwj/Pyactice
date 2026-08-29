"""Test cases for the cloud file storage service.

The level-3 turn here is ownership and capacity rather than time, and level 4 is
backup/restore per user with name collisions in the way. That makes it the problem
in this bank where "what does a failed operation leave behind?" matters most --
a rejected add that has already debited capacity is invisible until much later.
"""

from __future__ import annotations

from harness.model import case, op

# ==========================================================================
# Level 1
# ==========================================================================

LEVEL_1 = [
    case(
        "l1_add_get_delete",
        1,
        [
            op("ADD_FILE", "/dir/file.txt", 100, ret=True),
            op("GET_FILE_SIZE", "/dir/file.txt", ret=100),
            op("DELETE_FILE", "/dir/file.txt", ret=100, why="delete hands back the size"),
            op("GET_FILE_SIZE", "/dir/file.txt", ret=None),
            op("DELETE_FILE", "/dir/file.txt", ret=None),
        ],
        tags=["basics"],
        visible=True,
        doc="Add a file, read its size, delete it.",
    ),
    case(
        "l1_duplicate_add_is_rejected",
        1,
        [
            op("ADD_FILE", "/a", 5, ret=True),
            op("ADD_FILE", "/a", 9, ret=False, why="rejected, not overwritten"),
            op("GET_FILE_SIZE", "/a", ret=5),
        ],
        tags=["basics", "rejection"],
        visible=True,
        doc="Adding an existing name fails and changes nothing.",
    ),
    case(
        "l1_zero_size_is_not_absent",
        1,
        [
            op("ADD_FILE", "/empty", 0, ret=True),
            op("GET_FILE_SIZE", "/empty", ret=0, why="0 is a size; None would mean missing"),
            op("DELETE_FILE", "/empty", ret=0),
            op("GET_FILE_SIZE", "/empty", ret=None),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_name_is_free_again_after_delete",
        1,
        [
            op("ADD_FILE", "/a", 5, ret=True),
            op("DELETE_FILE", "/a", ret=5),
            op("ADD_FILE", "/a", 7, ret=True),
            op("GET_FILE_SIZE", "/a", ret=7),
        ],
        tags=["basics"],
    ),
    case(
        "l1_names_are_case_sensitive",
        1,
        [
            op("ADD_FILE", "/A", 1, ret=True),
            op("GET_FILE_SIZE", "/a", ret=None),
            op("ADD_FILE", "/a", 2, ret=True),
            op("GET_FILE_SIZE", "/A", ret=1),
            op("GET_FILE_SIZE", "/a", ret=2),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_nested_paths_are_just_names",
        1,
        [
            op("ADD_FILE", "/dir-a/dir-c/file-2.txt", 1100, ret=True),
            op("ADD_FILE", "/dir-b/file-4.mdx", 3378, ret=True),
            op("GET_FILE_SIZE", "/dir-a/dir-c/file-2.txt", ret=1100),
            op("GET_FILE_SIZE", "/dir-a", ret=None, why="directories are not files"),
            op("DELETE_FILE", "/dir-a", ret=None),
        ],
        tags=["basics", "paths"],
    ),
    case(
        "l1_files_are_independent",
        1,
        [
            *[op("ADD_FILE", f"/f{i}", i * 10, ret=True) for i in range(1, 6)],
            op("DELETE_FILE", "/f3", ret=30),
            op("GET_FILE_SIZE", "/f2", ret=20),
            op("GET_FILE_SIZE", "/f3", ret=None),
            op("GET_FILE_SIZE", "/f4", ret=40),
        ],
        tags=["basics"],
    ),
    case(
        "l1_delete_missing_returns_nothing",
        1,
        [
            op("DELETE_FILE", "/never", ret=None),
            op("ADD_FILE", "/never", 1, ret=True),
        ],
        tags=["basics", "edge-values"],
    ),
]


# ==========================================================================
# Level 2
# ==========================================================================

LEVEL_2 = [
    case(
        "l2_n_largest_by_prefix",
        2,
        [
            op("ADD_FILE", "/dir/a", 100, ret=True),
            op("ADD_FILE", "/dir/b", 200, ret=True),
            op("ADD_FILE", "/dir/c/d", 300, ret=True),
            op("ADD_FILE", "/other", 400, ret=True),
            op("GET_N_LARGEST", "/dir", 10, ret=["/dir/c/d", "/dir/b", "/dir/a"]),
            op("GET_N_LARGEST", "/nope", 5, ret=[]),
        ],
        tags=["query", "ordering"],
        visible=True,
        doc="Largest first, and fewer than n results if fewer match.",
    ),
    case(
        "l2_ties_break_by_name_and_n_caps",
        2,
        [
            op("ADD_FILE", "/f2", 50, ret=True),
            op("ADD_FILE", "/f1", 50, ret=True),
            op("ADD_FILE", "/f3", 90, ret=True),
            op("GET_N_LARGEST", "/", 2, ret=["/f3", "/f1"], why="equal sizes order by name"),
        ],
        tags=["query", "tie-break", "top-n"],
        visible=True,
        doc="Ties go to the smaller name; n limits the result.",
    ),
    case(
        "l2_n_greater_than_the_matches",
        2,
        [
            op("ADD_FILE", "/a", 1, ret=True),
            op("ADD_FILE", "/b", 2, ret=True),
            op("GET_N_LARGEST", "/", 100, ret=["/b", "/a"]),
        ],
        tags=["query", "top-n"],
    ),
    case(
        "l2_n_of_zero",
        2,
        [
            op("ADD_FILE", "/a", 1, ret=True),
            op("GET_N_LARGEST", "/", 0, ret=[]),
        ],
        tags=["query", "top-n", "edge-values"],
    ),
    case(
        "l2_prefix_is_a_string_not_a_directory",
        2,
        [
            op("ADD_FILE", "/dirA/x", 10, ret=True),
            op("ADD_FILE", "/dirAB/y", 20, ret=True),
            op("ADD_FILE", "/dirB/z", 30, ret=True),
            op("GET_N_LARGEST", "/dirA", 10, ret=["/dirAB/y", "/dirA/x"]),
        ],
        tags=["query", "paths", "edge-values"],
    ),
    case(
        "l2_prefix_does_not_match_the_middle",
        2,
        [
            op("ADD_FILE", "/abc", 1, ret=True),
            op("ADD_FILE", "/x/abc", 2, ret=True),
            op(
                "GET_N_LARGEST",
                "/abc",
                10,
                ret=["/abc"],
                why="/x/abc contains /abc but does not start with it",
            ),
        ],
        tags=["query", "edge-values"],
    ),
    case(
        "l2_prefix_is_case_sensitive",
        2,
        [
            op("ADD_FILE", "/Abc", 5, ret=True),
            op("ADD_FILE", "/abc", 6, ret=True),
            op("GET_N_LARGEST", "/A", 10, ret=["/Abc"]),
        ],
        tags=["query", "edge-values"],
    ),
    case(
        "l2_tie_break_is_lexicographic_not_numeric",
        2,
        [
            *[op("ADD_FILE", f"/a{i}", 5, ret=True) for i in range(1, 12)],
            op(
                "GET_N_LARGEST",
                "/a",
                10,
                ret=["/a1", "/a10", "/a11", "/a2", "/a3", "/a4", "/a5", "/a6", "/a7", "/a8"],
                why="string order puts /a10 and /a11 before /a2, so /a9 falls off",
            ),
        ],
        tags=["query", "tie-break", "top-n"],
    ),
    case(
        "l2_query_reflects_deletes",
        2,
        [
            op("ADD_FILE", "/a", 10, ret=True),
            op("ADD_FILE", "/b", 20, ret=True),
            op("DELETE_FILE", "/b", ret=20),
            op("GET_N_LARGEST", "/", 10, ret=["/a"]),
        ],
        tags=["query"],
    ),
    case(
        "l2_empty_prefix_matches_everything",
        2,
        [
            op("ADD_FILE", "/a", 1, ret=True),
            op("ADD_FILE", "b", 2, ret=True),
            op("GET_N_LARGEST", "", 10, ret=["b", "/a"]),
        ],
        tags=["query", "edge-values"],
    ),
    case(
        "l2_zero_size_still_listed",
        2,
        [
            op("ADD_FILE", "/z", 0, ret=True),
            op("ADD_FILE", "/y", 1, ret=True),
            op("GET_N_LARGEST", "/", 10, ret=["/y", "/z"]),
        ],
        tags=["query", "edge-values"],
    ),
    case(
        "l2_query_on_empty_storage",
        2,
        [op("GET_N_LARGEST", "/", 5, ret=[])],
        tags=["query", "edge-values"],
    ),
    case(
        "l2_level1_still_works",
        2,
        [
            op("ADD_FILE", "/a", 10, ret=True),
            op("ADD_FILE", "/a", 11, ret=False),
            op("GET_FILE_SIZE", "/a", ret=10),
            op("GET_N_LARGEST", "/a", 5, ret=["/a"]),
            op("DELETE_FILE", "/a", ret=10),
        ],
        tags=["regression"],
    ),
]


# ==========================================================================
# Level 3
# ==========================================================================

LEVEL_3 = [
    case(
        "l3_capacity_is_enforced",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 40, ret=60, why="the remaining capacity, not the used"),
            op("ADD_FILE_BY", "u1", "/b", 70, ret=None, why="70 will not fit in the 60 that is left"),
            op("GET_FILE_SIZE", "/b", ret=None, why="a rejected add stores nothing"),
            op("ADD_FILE_BY", "u1", "/b", 60, ret=0, why="an exact fit is allowed"),
        ],
        tags=["users", "capacity", "rejection"],
        visible=True,
        doc="ADD_FILE_BY returns what is left, or nothing if the file will not fit.",
    ),
    case(
        "l3_names_are_global_across_users",
        3,
        [
            op("ADD_FILE", "/x", 999999, ret=True),
            op("ADD_USER", "u1", 10, ret=True),
            op("ADD_FILE_BY", "u1", "/x", 1, ret=None, why="the name is taken, whoever owns it"),
            op("ADD_FILE_BY", "u1", "/y", 10, ret=0),
            op("ADD_FILE", "/y", 1, ret=False),
        ],
        tags=["users", "rejection"],
        visible=True,
        doc="One namespace for everybody. Files added with ADD_FILE cost no user capacity.",
    ),
    case(
        "l3_merge_moves_files_and_capacity",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_USER", "u2", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 40, ret=60),
            op("ADD_FILE_BY", "u2", "/b", 50, ret=50),
            op("MERGE_USER", "u1", "u2", ret=110, why="capacity 200, used 90"),
            op("GET_FILE_SIZE", "/b", ret=50, why="u2's file survives, it just changed owner"),
            op("ADD_FILE_BY", "u2", "/c", 1, ret=None, why="u2 no longer exists"),
        ],
        tags=["users", "merge", "capacity"],
        visible=True,
        doc="Merging adds the capacities and moves the files; the second user is gone.",
    ),
    case(
        "l3_duplicate_user_is_rejected",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_USER", "u1", 500, ret=False),
            op("ADD_FILE_BY", "u1", "/a", 200, ret=None, why="still the original capacity"),
        ],
        tags=["users", "rejection"],
    ),
    case(
        "l3_unknown_user_cannot_add",
        3,
        [
            op("ADD_FILE_BY", "ghost", "/a", 1, ret=None),
            op("GET_FILE_SIZE", "/a", ret=None),
            op("ADD_FILE_BY", "admin", "/a", 1, ret=None, why="admin is implicit, not addressable"),
        ],
        tags=["users", "rejection"],
    ),
    case(
        "l3_delete_gives_capacity_back",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 60, ret=40),
            op("DELETE_FILE", "/a", ret=60),
            op("ADD_FILE_BY", "u1", "/b", 100, ret=0, why="the whole capacity is free again"),
        ],
        visible=True,
        doc="Deleting a file gives its owner the capacity back.",
        tags=["users", "capacity"],
    ),
    case(
        "l3_a_rejected_add_costs_nothing",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/big", 200, ret=None),
            op("ADD_FILE_BY", "u1", "/a", 100, ret=0, why="the failed add must not have debited"),
        ],
        tags=["users", "capacity", "rejection"],
    ),
    case(
        "l3_zero_capacity_user",
        3,
        [
            op("ADD_USER", "u1", 0, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 1, ret=None),
            op("ADD_FILE_BY", "u1", "/b", 0, ret=0, why="a zero-byte file fits in nothing"),
        ],
        tags=["users", "capacity", "edge-values"],
    ),
    case(
        "l3_merge_needs_two_real_and_different_users",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("MERGE_USER", "u1", "ghost", ret=None),
            op("MERGE_USER", "ghost", "u1", ret=None),
            op("MERGE_USER", "u1", "u1", ret=None, why="merging a user into itself is not a merge"),
            op("ADD_FILE_BY", "u1", "/a", 100, ret=0, why="none of those did anything"),
        ],
        tags=["users", "merge", "rejection"],
    ),
    case(
        "l3_merge_into_an_empty_user",
        3,
        [
            op("ADD_USER", "u1", 50, ret=True),
            op("ADD_USER", "u2", 30, ret=True),
            op("ADD_FILE_BY", "u2", "/b", 20, ret=10),
            op("MERGE_USER", "u1", "u2", ret=60, why="capacity 80, used 20"),
            op("ADD_FILE_BY", "u1", "/c", 60, ret=0),
        ],
        tags=["users", "merge", "capacity"],
    ),
    case(
        "l3_plain_files_never_touch_user_capacity",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE", "/free", 1000000, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 100, ret=0, why="the huge plain file cost u1 nothing"),
        ],
        tags=["users", "capacity"],
    ),
    case(
        "l3_query_spans_all_owners",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_USER", "u2", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/p/a", 10, ret=90),
            op("ADD_FILE_BY", "u2", "/p/b", 30, ret=70),
            op("ADD_FILE", "/p/c", 20, ret=True),
            op("GET_N_LARGEST", "/p", 10, ret=["/p/b", "/p/c", "/p/a"]),
        ],
        tags=["regression", "users", "query"],
    ),
    case(
        "l3_level1_still_works",
        3,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("GET_FILE_SIZE", "/a", ret=10),
            op("ADD_FILE", "/a", 1, ret=False),
            op("DELETE_FILE", "/a", ret=10),
            op("GET_FILE_SIZE", "/a", ret=None),
        ],
        tags=["regression"],
    ),
]


# ==========================================================================
# Level 4
# ==========================================================================

LEVEL_4 = [
    case(
        "l4_backup_then_restore",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("ADD_FILE_BY", "u1", "/b", 20, ret=70),
            op("BACKUP_USER", "u1", ret=2),
            op("DELETE_FILE", "/a", ret=10),
            op("ADD_FILE_BY", "u1", "/c", 30, ret=50),
            op("RESTORE_USER", "u1", ret=2),
            op("GET_FILE_SIZE", "/a", ret=10, why="deleted, then brought back"),
            op("GET_FILE_SIZE", "/b", ret=20),
            op("GET_FILE_SIZE", "/c", ret=None, why="added after the backup, so it is gone"),
        ],
        tags=["backup", "restore"],
        visible=True,
        doc="Restore replaces the user's files with the backed-up set.",
    ),
    case(
        "l4_restore_skips_names_someone_else_took",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_USER", "u2", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("ADD_FILE_BY", "u1", "/b", 20, ret=70),
            op("BACKUP_USER", "u1", ret=2),
            op("DELETE_FILE", "/a", ret=10),
            op("ADD_FILE_BY", "u2", "/a", 5, ret=95),
            op("RESTORE_USER", "u1", ret=1, why="only /b came back; /a belongs to u2 now"),
            op("GET_FILE_SIZE", "/a", ret=5, why="u2's file is not disturbed"),
            op("GET_FILE_SIZE", "/b", ret=20),
        ],
        tags=["restore", "collision"],
        visible=True,
        doc="A restore never takes a name back from another user.",
    ),
    case(
        "l4_restore_with_no_backup_does_nothing",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("RESTORE_USER", "u1", ret=0),
            op("GET_FILE_SIZE", "/a", ret=10, why="no backup means no change, not a wipe"),
        ],
        tags=["restore", "edge-values"],
    ),
    case(
        "l4_backup_and_restore_need_a_real_user",
        4,
        [
            op("BACKUP_USER", "ghost", ret=None),
            op("RESTORE_USER", "ghost", ret=None),
        ],
        tags=["backup", "restore", "rejection"],
    ),
    case(
        "l4_backup_of_a_user_with_no_files",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("BACKUP_USER", "u1", ret=0),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("RESTORE_USER", "u1", ret=0, why="the backup was empty, so the user ends up empty"),
            op("GET_FILE_SIZE", "/a", ret=None),
        ],
        tags=["backup", "restore", "edge-values"],
    ),
    case(
        "l4_a_second_backup_replaces_the_first",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("BACKUP_USER", "u1", ret=1),
            op("ADD_FILE_BY", "u1", "/b", 20, ret=70),
            op("BACKUP_USER", "u1", ret=2),
            op("DELETE_FILE", "/a", ret=10),
            op("DELETE_FILE", "/b", ret=20),
            op("RESTORE_USER", "u1", ret=2, why="the newer backup, not the first"),
            op("GET_FILE_SIZE", "/b", ret=20),
        ],
        tags=["backup", "restore"],
    ),
    case(
        "l4_a_backup_is_a_snapshot_not_a_view",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("BACKUP_USER", "u1", ret=1),
            op("ADD_FILE_BY", "u1", "/b", 20, ret=70),
            op(
                "RESTORE_USER",
                "u1",
                ret=1,
                why="a shallow copy would have let /b leak into the backup",
            ),
            op("GET_FILE_SIZE", "/b", ret=None),
        ],
        tags=["backup", "restore", "aliasing"],
    ),
    case(
        "l4_restore_puts_capacity_back",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 60, ret=40),
            op("BACKUP_USER", "u1", ret=1),
            op("DELETE_FILE", "/a", ret=60),
            op("ADD_FILE_BY", "u1", "/b", 90, ret=10),
            op("RESTORE_USER", "u1", ret=1),
            op("GET_FILE_SIZE", "/b", ret=None),
            op("ADD_FILE_BY", "u1", "/c", 40, ret=0, why="used is back to 60 out of 100"),
        ],
        tags=["restore", "capacity"],
    ),
    case(
        "l4_restore_twice_is_stable",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("BACKUP_USER", "u1", ret=1),
            op("ADD_FILE_BY", "u1", "/b", 20, ret=70),
            op("RESTORE_USER", "u1", ret=1),
            op("RESTORE_USER", "u1", ret=1, why="restoring again is not a no-op, it is idempotent"),
            op("GET_FILE_SIZE", "/a", ret=10),
        ],
        tags=["restore"],
    ),
    case(
        "l4_merge_takes_the_absorbed_user_away_entirely",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_USER", "u2", 100, ret=True),
            op("ADD_FILE_BY", "u2", "/x", 10, ret=90),
            op("BACKUP_USER", "u2", ret=1),
            op("MERGE_USER", "u1", "u2", ret=190),
            op("RESTORE_USER", "u2", ret=None, why="u2 is gone, and so is its backup"),
            op("GET_FILE_SIZE", "/x", ret=10),
        ],
        tags=["merge", "restore", "backup"],
    ),
    case(
        "l4_restore_after_a_merge_uses_the_survivors_backup",
        4,
        [
            op("ADD_USER", "u1", 100, ret=True),
            op("ADD_USER", "u2", 100, ret=True),
            op("ADD_FILE_BY", "u1", "/a", 10, ret=90),
            op("BACKUP_USER", "u1", ret=1),
            op("ADD_FILE_BY", "u2", "/b", 20, ret=80),
            op("MERGE_USER", "u1", "u2", ret=170),
            op(
                "RESTORE_USER",
                "u1",
                ret=1,
                why="u1's backup predates the merge, so /b is dropped",
            ),
            op("GET_FILE_SIZE", "/b", ret=None),
            op("GET_FILE_SIZE", "/a", ret=10),
        ],
        tags=["merge", "restore", "backup"],
    ),
    case(
        "l4_all_levels_together",
        4,
        [
            op("ADD_FILE", "/shared", 500, ret=True),
            op("ADD_USER", "u1", 200, ret=True),
            op("ADD_USER", "u2", 200, ret=True),
            op("ADD_FILE_BY", "u1", "/p/a", 100, ret=100),
            op("ADD_FILE_BY", "u2", "/p/b", 150, ret=50),
            op("GET_N_LARGEST", "/p", 10, ret=["/p/b", "/p/a"]),
            op("BACKUP_USER", "u1", ret=1),
            op("ADD_FILE_BY", "u1", "/p/c", 100, ret=0),
            op("GET_N_LARGEST", "/p", 2, ret=["/p/b", "/p/a"], why="/p/a and /p/c tie at 100"),
            op("MERGE_USER", "u1", "u2", ret=50, why="capacity 400, used 350"),
            op("RESTORE_USER", "u1", ret=1),
            op("GET_FILE_SIZE", "/p/c", ret=None),
            op("GET_FILE_SIZE", "/p/b", ret=None, why="/p/b became u1's in the merge, so it went too"),
            op("GET_FILE_SIZE", "/shared", ret=500, why="the plain file was never u1's"),
            op("ADD_FILE_BY", "u1", "/p/d", 300, ret=0, why="capacity 400, used 100"),
        ],
        tags=["regression", "merge", "restore", "capacity", "query"],
    ),
]


ALL_CASES = tuple(LEVEL_1 + LEVEL_2 + LEVEL_3 + LEVEL_4)
