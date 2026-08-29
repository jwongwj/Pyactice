"""Test cases for the file hosting service.

Authoring rules (see .claude/skills/harness-engineering):
  * Every case is a fresh instance. No shared state.
  * Keep cases short. A case that fails should point at one idea, not five.
  * Any expectation that is not obvious from the statement carries a `why=`.
  * `visible=True` cases are printed in the level statement, so they are the
    channel through which the candidate learns the tie-breaks. Every genuinely
    ambiguous rule must be demonstrated by at least one visible case.
"""

from __future__ import annotations

from harness.model import case, op

# --------------------------------------------------------------------------
# helpers


def _uploads(pairs, *, at=None, ttl=None):
    """Build a run of uploads. `at=None` uses the level-1 signature."""
    out = []
    for name, size in pairs:
        if at is None:
            out.append(op("FILE_UPLOAD", name, size))
        elif ttl is None:
            out.append(op("FILE_UPLOAD_AT", at, name, size))
        else:
            out.append(op("FILE_UPLOAD_AT", at, name, size, ttl))
    return out


def _numbered(prefix: str, count: int, size_of=lambda i: i, pad: int = 2):
    return [(f"{prefix}{i:0{pad}d}.txt", size_of(i)) for i in range(1, count + 1)]


# ==========================================================================
# Level 1 - initial design & basic functions
# ==========================================================================

LEVEL_1 = [
    case(
        "l1_upload_get_copy",
        1,
        [
            op("FILE_UPLOAD", "/dir/file.txt", 100),
            op("FILE_GET", "/dir/file.txt", ret=100),
            op("FILE_COPY", "/dir/file.txt", "/dir/copy.txt"),
            op("FILE_GET", "/dir/copy.txt", ret=100),
            op("FILE_GET", "/dir/missing.txt", ret=None),
        ],
        tags=["basics"],
        visible=True,
        doc="Upload, read back, copy, and miss.",
    ),
    case(
        "l1_duplicate_upload_raises",
        1,
        [
            op("FILE_UPLOAD", "/a.txt", 5),
            op("FILE_UPLOAD", "/a.txt", 9, raises=True),
        ],
        tags=["basics", "errors"],
        visible=True,
        doc="Re-uploading an existing name is an error.",
    ),
    case(
        "l1_copy_missing_source_raises",
        1,
        [op("FILE_COPY", "/ghost.txt", "/x.txt", raises=True)],
        tags=["errors"],
        visible=True,
        doc="Copying a file that does not exist is an error.",
    ),
    case(
        "l1_copy_overwrites_destination",
        1,
        [
            op("FILE_UPLOAD", "/a.txt", 10),
            op("FILE_UPLOAD", "/b.txt", 20),
            op("FILE_COPY", "/a.txt", "/b.txt"),
            op("FILE_GET", "/b.txt", ret=10, why="copy overwrites, it does not error"),
            op("FILE_GET", "/a.txt", ret=10, why="the source survives the copy"),
        ],
        tags=["basics", "overwrite"],
    ),
    case(
        "l1_zero_size_is_not_absent",
        1,
        [
            op("FILE_UPLOAD", "/empty.txt", 0),
            op(
                "FILE_GET",
                "/empty.txt",
                ret=0,
                why="0 is a size; returning None here means you tested truthiness",
            ),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_failed_upload_leaves_original",
        1,
        [
            op("FILE_UPLOAD", "/a.txt", 10),
            op("FILE_UPLOAD", "/a.txt", 99, raises=True),
            op("FILE_GET", "/a.txt", ret=10, why="the rejected upload must not have written"),
        ],
        tags=["errors", "atomicity"],
    ),
    case(
        "l1_copy_onto_itself",
        1,
        [
            op("FILE_UPLOAD", "/a.txt", 10),
            op("FILE_COPY", "/a.txt", "/a.txt"),
            op("FILE_GET", "/a.txt", ret=10, why="delete-then-write ordering would lose the file"),
        ],
        tags=["overwrite", "edge-values"],
    ),
    case(
        "l1_names_are_case_sensitive",
        1,
        [
            op("FILE_UPLOAD", "/A.txt", 1),
            op("FILE_GET", "/a.txt", ret=None),
            op("FILE_UPLOAD", "/a.txt", 2),
            op("FILE_GET", "/A.txt", ret=1),
            op("FILE_GET", "/a.txt", ret=2),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_copy_chain",
        1,
        [
            op("FILE_UPLOAD", "/a.txt", 7),
            op("FILE_COPY", "/a.txt", "/b.txt"),
            op("FILE_COPY", "/b.txt", "/c.txt"),
            op("FILE_GET", "/c.txt", ret=7),
        ],
        tags=["basics"],
    ),
    case(
        "l1_failed_copy_writes_nothing",
        1,
        [
            op("FILE_COPY", "/ghost.txt", "/x.txt", raises=True),
            op("FILE_GET", "/x.txt", ret=None),
        ],
        tags=["errors", "atomicity"],
    ),
    case(
        "l1_nested_paths_are_just_names",
        1,
        [
            *_uploads(
                [
                    ("/file-1.zip", 4321),
                    ("/dir-a/dir-c/file-2.txt", 1100),
                    ("/dir-a/dir-c/file-3.csv", 2122),
                    ("/dir-b/file-4.mdx", 3378),
                ]
            ),
            op("FILE_GET", "/dir-a/dir-c/file-3.csv", ret=2122),
            op("FILE_GET", "/dir-a/dir-c", ret=None, why="directories are not files"),
            op("FILE_GET", "/dir-a", ret=None),
        ],
        tags=["basics", "paths"],
    ),
    case(
        "l1_many_files_independent",
        1,
        [
            *_uploads(_numbered("/f", 6, size_of=lambda i: i * 11)),
            op("FILE_GET", "/f01.txt", ret=11),
            op("FILE_GET", "/f04.txt", ret=44),
            op("FILE_GET", "/f06.txt", ret=66),
        ],
        tags=["basics"],
    ),
    case(
        "l1_copy_then_duplicate_upload_raises",
        1,
        [
            op("FILE_UPLOAD", "/a.txt", 3),
            op("FILE_COPY", "/a.txt", "/b.txt"),
            op("FILE_UPLOAD", "/b.txt", 4, raises=True, why="the copy really created /b.txt"),
        ],
        tags=["errors", "overwrite"],
    ),
]


# ==========================================================================
# Level 2 - data structures & data processing
# ==========================================================================

LEVEL_2 = [
    case(
        "l2_search_orders_by_size_desc",
        2,
        [
            *_uploads(
                [
                    ("/dir/file1.txt", 100),
                    ("/dir/file2.txt", 200),
                    ("/dir/deep/file3.txt", 300),
                    ("/other/file.txt", 400),
                ]
            ),
            op(
                "FILE_SEARCH",
                "/dir",
                ret=["/dir/deep/file3.txt", "/dir/file2.txt", "/dir/file1.txt"],
            ),
            op("FILE_SEARCH", "/nope", ret=[]),
        ],
        tags=["search", "ordering"],
        visible=True,
        doc="Largest first; non-matching prefixes give an empty result.",
    ),
    case(
        "l2_ties_break_by_name_ascending",
        2,
        [
            *_uploads([("/b.txt", 50), ("/a.txt", 50), ("/c.txt", 90)]),
            op("FILE_SEARCH", "/", ret=["/c.txt", "/a.txt", "/b.txt"]),
        ],
        tags=["search", "ordering", "tie-break"],
        visible=True,
        doc="Equal sizes are ordered by name, ascending.",
    ),
    case(
        "l2_caps_at_ten",
        2,
        [
            *_uploads(_numbered("/f", 12)),
            op(
                "FILE_SEARCH",
                "/f",
                ret=[
                    "/f12.txt",
                    "/f11.txt",
                    "/f10.txt",
                    "/f09.txt",
                    "/f08.txt",
                    "/f07.txt",
                    "/f06.txt",
                    "/f05.txt",
                    "/f04.txt",
                    "/f03.txt",
                ],
                why="12 files match; only the 10 largest come back",
            ),
        ],
        tags=["search", "top-n"],
        visible=True,
        doc="At most ten results.",
    ),
    case(
        "l2_empty_prefix_matches_everything",
        2,
        [
            *_uploads([("/a", 1), ("b", 2), ("/c", 3)]),
            op("FILE_SEARCH", "", ret=["/c", "b", "/a"]),
        ],
        tags=["search", "edge-values"],
    ),
    case(
        "l2_prefix_is_a_string_not_a_directory",
        2,
        [
            *_uploads([("/dirA/x", 10), ("/dirAB/y", 20), ("/dirB/z", 30)]),
            op(
                "FILE_SEARCH",
                "/dirA",
                ret=["/dirAB/y", "/dirA/x"],
                why="/dirAB/y starts with the string /dirA, so it matches",
            ),
        ],
        tags=["search", "paths", "edge-values"],
    ),
    case(
        "l2_search_sees_copies",
        2,
        [
            op("FILE_UPLOAD", "/a", 10),
            op("FILE_COPY", "/a", "/ab"),
            op("FILE_SEARCH", "/a", ret=["/a", "/ab"], why="same size, so name order wins"),
        ],
        tags=["search", "tie-break"],
    ),
    case(
        "l2_search_sees_overwrites",
        2,
        [
            *_uploads([("/a", 10), ("/b", 99)]),
            op("FILE_COPY", "/a", "/b"),
            op("FILE_SEARCH", "/", ret=["/a", "/b"], why="/b is now 10 too"),
        ],
        tags=["search", "overwrite"],
    ),
    case(
        "l2_prefix_does_not_match_the_middle",
        2,
        [
            *_uploads([("/abc", 1), ("/x/abc", 2)]),
            op(
                "FILE_SEARCH",
                "/abc",
                ret=["/abc"],
                why="/x/abc contains /abc but does not start with it",
            ),
        ],
        tags=["search", "edge-values"],
    ),
    case(
        "l2_prefix_is_case_sensitive",
        2,
        [
            *_uploads([("/Abc", 5), ("/abc", 6)]),
            op("FILE_SEARCH", "/A", ret=["/Abc"]),
            op("FILE_SEARCH", "/a", ret=["/abc"]),
        ],
        tags=["search", "edge-values"],
    ),
    case(
        "l2_search_on_empty_storage",
        2,
        [op("FILE_SEARCH", "/", ret=[])],
        tags=["search", "edge-values"],
    ),
    case(
        "l2_exactly_ten_matches",
        2,
        [
            *_uploads(_numbered("/g", 10)),
            op(
                "FILE_SEARCH",
                "/g",
                ret=[f"/g{i:02d}.txt" for i in range(10, 0, -1)],
            ),
        ],
        tags=["search", "top-n"],
    ),
    case(
        "l2_tie_break_is_lexicographic_not_numeric",
        2,
        [
            *_uploads([(f"/a{i}", 5) for i in range(1, 12)]),
            op(
                "FILE_SEARCH",
                "/a",
                ret=["/a1", "/a10", "/a11", "/a2", "/a3", "/a4", "/a5", "/a6", "/a7", "/a8"],
                why=(
                    "all eleven are size 5, so name order decides; string order puts "
                    "/a10 and /a11 before /a2, and /a9 falls off the end"
                ),
            ),
        ],
        tags=["search", "tie-break", "top-n"],
    ),
    case(
        "l2_mixed_sizes_and_ties",
        2,
        [
            *_uploads([("/p/x", 300), ("/p/y", 300), ("/p/z", 100), ("/p/w", 500)]),
            op("FILE_SEARCH", "/p", ret=["/p/w", "/p/x", "/p/y", "/p/z"]),
        ],
        tags=["search", "ordering", "tie-break"],
    ),
    case(
        "l2_prefix_equal_to_whole_name",
        2,
        [
            op("FILE_UPLOAD", "/exact.txt", 3),
            op("FILE_SEARCH", "/exact.txt", ret=["/exact.txt"]),
        ],
        tags=["search", "edge-values"],
    ),
    case(
        "l2_zero_size_still_listed",
        2,
        [
            *_uploads([("/z", 0), ("/y", 1)]),
            op("FILE_SEARCH", "/", ret=["/y", "/z"], why="a 0-byte file is still a file"),
        ],
        tags=["search", "edge-values"],
    ),
    case(
        "l2_level1_still_works",
        2,
        [
            op("FILE_UPLOAD", "/a.txt", 10),
            op("FILE_GET", "/a.txt", ret=10),
            op("FILE_UPLOAD", "/a.txt", 11, raises=True),
            op("FILE_COPY", "/nope", "/x", raises=True),
            op("FILE_SEARCH", "/a", ret=["/a.txt"]),
        ],
        tags=["regression"],
    ),
]


# ==========================================================================
# Level 3 - refactoring & encapsulation
# ==========================================================================

LEVEL_3 = [
    case(
        "l3_ttl_expiry_boundary",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a.txt", 100),
            op("FILE_UPLOAD_AT", 0, "/b.txt", 200, 10),
            op("FILE_GET_AT", 5, "/b.txt", ret=200),
            op(
                "FILE_GET_AT",
                10,
                "/b.txt",
                ret=None,
                why="a ttl of 10 covers [0, 10); at exactly 10 the file is gone",
            ),
            op("FILE_GET_AT", 100, "/a.txt", ret=100, why="no ttl means forever"),
        ],
        tags=["ttl", "boundaries"],
        visible=True,
        doc="A ttl of n seconds means alive on [upload, upload + n).",
    ),
    case(
        "l3_plain_calls_are_timestamp_zero",
        3,
        [
            op("FILE_UPLOAD", "/legacy.txt", 42),
            op("FILE_GET_AT", 1000, "/legacy.txt", ret=42),
            op("FILE_GET", "/legacy.txt", ret=42),
            op("FILE_UPLOAD_AT", 0, "/legacy.txt", 7, raises=True),
        ],
        tags=["refactor", "regression"],
        visible=True,
        doc="The level-1 methods are the timestamped ones at t=0 with no ttl.",
    ),
    case(
        "l3_copy_inherits_the_source_expiry",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/src.txt", 50, 10),
            op("FILE_COPY_AT", 5, "/src.txt", "/dst.txt"),
            op("FILE_GET_AT", 9, "/dst.txt", ret=50),
            op(
                "FILE_GET_AT",
                10,
                "/dst.txt",
                ret=None,
                why="the copy dies when the source would have, not 10s after the copy",
            ),
        ],
        tags=["ttl", "copy-semantics"],
        visible=True,
        doc="A copy inherits the source's expiry time.",
    ),
    case(
        "l3_search_excludes_the_dead",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/f1", 100, 5),
            op("FILE_UPLOAD_AT", 0, "/f2", 200),
            op("FILE_SEARCH_AT", 1, "/f", ret=["/f2", "/f1"]),
            op("FILE_SEARCH_AT", 5, "/f", ret=["/f2"]),
        ],
        tags=["ttl", "search"],
        visible=True,
        doc="Search only reports files that are alive at the given timestamp.",
    ),
    case(
        "l3_reupload_after_expiry_is_allowed",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10, 5),
            op("FILE_GET_AT", 5, "/a", ret=None),
            op("FILE_UPLOAD_AT", 5, "/a", 20, why="the name is free once the file has expired"),
            op("FILE_GET_AT", 6, "/a", ret=20),
        ],
        tags=["ttl", "errors"],
    ),
    case(
        "l3_reupload_before_expiry_raises",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10, 5),
            op("FILE_UPLOAD_AT", 4, "/a", 20, raises=True),
            op("FILE_GET_AT", 4, "/a", ret=10),
        ],
        tags=["ttl", "errors"],
    ),
    case(
        "l3_copy_from_expired_source_raises",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10, 3),
            op("FILE_COPY_AT", 3, "/a", "/b", raises=True),
            op("FILE_GET_AT", 3, "/b", ret=None),
        ],
        tags=["ttl", "errors", "copy-semantics"],
    ),
    case(
        "l3_copy_overwrites_a_live_destination",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10),
            op("FILE_UPLOAD_AT", 0, "/b", 99),
            op("FILE_COPY_AT", 1, "/a", "/b"),
            op("FILE_GET_AT", 2, "/b", ret=10),
        ],
        tags=["copy-semantics", "overwrite"],
    ),
    case(
        "l3_copy_over_an_expired_destination",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10),
            op("FILE_UPLOAD_AT", 0, "/b", 20, 3),
            op("FILE_COPY_AT", 5, "/a", "/b"),
            op("FILE_GET_AT", 6, "/b", ret=10, why="/b was dead, the copy revives the name"),
        ],
        tags=["ttl", "copy-semantics", "overwrite"],
    ),
    case(
        "l3_file_does_not_exist_before_it_is_uploaded",
        3,
        [
            op("FILE_UPLOAD_AT", 10, "/a", 5),
            op(
                "FILE_GET_AT",
                5,
                "/a",
                ret=None,
                why="alive means [upload, upload + ttl); 5 is before the upload",
            ),
            op("FILE_GET_AT", 10, "/a", ret=5),
        ],
        tags=["ttl", "boundaries", "time-travel"],
    ),
    case(
        "l3_zero_ttl_is_dead_on_arrival",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10, 0),
            op("FILE_GET_AT", 0, "/a", ret=None, why="[0, 0) contains nothing"),
        ],
        tags=["ttl", "boundaries", "edge-values"],
    ),
    case(
        "l3_search_at_respects_top_ten_over_the_living",
        3,
        [
            *[op("FILE_UPLOAD_AT", 0, f"/g{i:02d}.txt", i) for i in range(1, 10)],
            *[op("FILE_UPLOAD_AT", 0, f"/g{i:02d}.txt", i, 5) for i in range(10, 13)],
            op(
                "FILE_SEARCH_AT",
                5,
                "/g",
                ret=[f"/g{i:02d}.txt" for i in range(9, 0, -1)],
                why="the three largest expired at t=5, leaving nine survivors",
            ),
            op(
                "FILE_SEARCH_AT",
                4,
                "/g",
                ret=[f"/g{i:02d}.txt" for i in range(12, 2, -1)],
                why="at t=4 all twelve are alive, so the cap applies",
            ),
        ],
        tags=["ttl", "search", "top-n"],
    ),
    case(
        "l3_interleaved_lifetimes",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 30, 10),
            op("FILE_UPLOAD_AT", 3, "/b", 20, 10),
            op("FILE_UPLOAD_AT", 6, "/c", 10),
            op("FILE_SEARCH_AT", 6, "/", ret=["/a", "/b", "/c"]),
            op("FILE_SEARCH_AT", 10, "/", ret=["/b", "/c"], why="/a died at 10"),
            op("FILE_SEARCH_AT", 13, "/", ret=["/c"], why="/b died at 13"),
            op("FILE_SEARCH_AT", 999, "/", ret=["/c"]),
        ],
        tags=["ttl", "search", "boundaries"],
    ),
    case(
        "l3_level2_search_still_works",
        3,
        [
            op("FILE_UPLOAD", "/a", 1),
            op("FILE_UPLOAD_AT", 0, "/b", 2),
            op("FILE_SEARCH", "/", ret=["/b", "/a"]),
            op("FILE_GET", "/b", ret=2),
        ],
        tags=["regression", "refactor"],
    ),
    case(
        "l3_level1_errors_still_work",
        3,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 1),
            op("FILE_UPLOAD", "/a", 2, raises=True),
            op("FILE_COPY", "/ghost", "/x", raises=True),
            op("FILE_COPY_AT", 1, "/ghost", "/x", raises=True),
        ],
        tags=["regression", "errors"],
    ),
]


# ==========================================================================
# Level 4 - extending design & functionality
# ==========================================================================

LEVEL_4 = [
    case(
        "l4_rollback_drops_later_files",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 100),
            op("FILE_UPLOAD_AT", 10, "/b", 200),
            op("ROLLBACK", 5),
            op("FILE_GET_AT", 20, "/a", ret=100),
            op("FILE_GET_AT", 20, "/b", ret=None, why="/b was uploaded after t=5"),
            op("FILE_SEARCH_AT", 20, "/", ret=["/a"]),
        ],
        tags=["rollback"],
        visible=True,
        doc="Rollback restores the exact state the storage had at that timestamp.",
    ),
    case(
        "l4_rollback_keeps_expiry_times",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/t", 50, 100),
            op("FILE_UPLOAD_AT", 10, "/u", 60),
            op("ROLLBACK", 5),
            op("FILE_GET_AT", 99, "/t", ret=50),
            op("FILE_GET_AT", 100, "/t", ret=None, why="/t still dies at its original expiry"),
            op("FILE_GET_AT", 6, "/u", ret=None),
        ],
        tags=["rollback", "ttl"],
        visible=True,
        doc="Surviving files keep the lifetime they had; the clock is not restarted.",
    ),
    case(
        "l4_rollback_undoes_an_overwriting_copy",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10),
            op("FILE_UPLOAD_AT", 0, "/b", 20),
            op("FILE_COPY_AT", 5, "/a", "/b"),
            op("FILE_GET_AT", 6, "/b", ret=10),
            op("ROLLBACK", 4),
            op("FILE_GET_AT", 6, "/b", ret=20, why="the copy happened after t=4, so it is undone"),
            op("FILE_GET_AT", 6, "/a", ret=10),
        ],
        tags=["rollback", "overwrite"],
        visible=True,
        doc="Rollback restores overwritten contents, not just deleted names.",
    ),
    case(
        "l4_rollback_to_zero_empties_storage",
        4,
        [
            op("FILE_UPLOAD_AT", 1, "/a", 1),
            op("ROLLBACK", 0),
            op("FILE_GET_AT", 5, "/a", ret=None),
            op("FILE_SEARCH_AT", 5, "/", ret=[]),
        ],
        tags=["rollback", "edge-values"],
    ),
    case(
        "l4_rollback_does_not_resurrect_the_expired",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10, 5),
            op("ROLLBACK", 8),
            op(
                "FILE_GET_AT",
                9,
                "/a",
                ret=None,
                why="at t=8 the file was already dead, so the restored state omits it",
            ),
        ],
        tags=["rollback", "ttl", "boundaries"],
    ),
    case(
        "l4_rollback_before_expiry_keeps_the_file",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 10, 5),
            op("ROLLBACK", 3),
            op("FILE_GET_AT", 4, "/a", ret=10),
            op("FILE_GET_AT", 5, "/a", ret=None),
        ],
        tags=["rollback", "ttl", "boundaries"],
    ),
    case(
        "l4_rollback_frees_the_name",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 1),
            op("FILE_UPLOAD_AT", 10, "/b", 2),
            op("ROLLBACK", 5),
            op("FILE_UPLOAD_AT", 6, "/b", 3, why="/b no longer exists, so this must not raise"),
            op("FILE_GET_AT", 7, "/b", ret=3),
        ],
        tags=["rollback", "errors"],
    ),
    case(
        "l4_rollback_twice_goes_further_back",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 1),
            op("FILE_UPLOAD_AT", 5, "/b", 2),
            op("FILE_UPLOAD_AT", 10, "/c", 3),
            op("ROLLBACK", 7),
            op("FILE_GET_AT", 11, "/c", ret=None),
            op("FILE_GET_AT", 11, "/b", ret=2),
            op("ROLLBACK", 2),
            op("FILE_GET_AT", 11, "/b", ret=None, why="history before the first rollback is still there"),
            op("FILE_GET_AT", 11, "/a", ret=1),
        ],
        tags=["rollback", "history"],
    ),
    case(
        "l4_rollback_to_the_future_changes_nothing",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 1),
            op("FILE_UPLOAD_AT", 2, "/b", 2),
            op("ROLLBACK", 100),
            op("FILE_GET_AT", 101, "/a", ret=1),
            op("FILE_GET_AT", 101, "/b", ret=2),
        ],
        tags=["rollback", "edge-values"],
    ),
    case(
        "l4_rollback_at_an_exact_upload_timestamp",
        4,
        [
            op("FILE_UPLOAD_AT", 5, "/a", 1),
            op("ROLLBACK", 5),
            op("FILE_GET_AT", 6, "/a", ret=1, why="the file is alive from t=5 inclusive"),
        ],
        tags=["rollback", "boundaries"],
    ),
    case(
        "l4_rollback_covers_plain_uploads",
        4,
        [
            op("FILE_UPLOAD", "/a", 1),
            op("FILE_UPLOAD_AT", 5, "/b", 2),
            op("ROLLBACK", 1),
            op("FILE_GET", "/a", ret=1),
            op("FILE_GET_AT", 6, "/b", ret=None),
        ],
        tags=["rollback", "regression", "refactor"],
    ),
    case(
        "l4_copy_after_rollback",
        4,
        [
            op("FILE_UPLOAD_AT", 0, "/a", 5),
            op("FILE_UPLOAD_AT", 10, "/b", 6),
            op("ROLLBACK", 3),
            op("FILE_COPY_AT", 4, "/a", "/c"),
            op("FILE_GET_AT", 5, "/c", ret=5),
            op("FILE_COPY_AT", 4, "/b", "/d", raises=True, why="/b was rolled away"),
        ],
        tags=["rollback", "copy-semantics", "errors"],
    ),
    case(
        "l4_rollback_then_search_top_ten",
        4,
        [
            *[op("FILE_UPLOAD_AT", i - 1, f"/s{i:02d}.txt", i) for i in range(1, 13)],
            op("ROLLBACK", 5),
            op(
                "FILE_SEARCH_AT",
                20,
                "/s",
                ret=[f"/s{i:02d}.txt" for i in range(6, 0, -1)],
                why="only the six files uploaded at t<=5 survive",
            ),
        ],
        tags=["rollback", "search", "top-n"],
    ),
    case(
        "l4_all_levels_together",
        4,
        [
            op("FILE_UPLOAD", "/base", 500),
            op("FILE_UPLOAD_AT", 1, "/temp", 400, 4),
            op("FILE_COPY_AT", 2, "/base", "/base-copy"),
            op("FILE_SEARCH_AT", 3, "/", ret=["/base", "/base-copy", "/temp"]),
            op("FILE_UPLOAD_AT", 6, "/late", 900),
            op("FILE_SEARCH_AT", 7, "/", ret=["/late", "/base", "/base-copy"]),
            op("ROLLBACK", 2),
            op("FILE_GET_AT", 7, "/late", ret=None),
            op("FILE_GET_AT", 7, "/base-copy", ret=500),
            op("FILE_GET_AT", 7, "/temp", ret=None, why="/temp expired at t=5"),
            op("FILE_SEARCH_AT", 3, "/", ret=["/base", "/base-copy", "/temp"]),
            op("FILE_UPLOAD", "/base", 1, raises=True),
        ],
        tags=["rollback", "regression", "search", "ttl"],
    ),
]


ALL_CASES = tuple(LEVEL_1 + LEVEL_2 + LEVEL_3 + LEVEL_4)
