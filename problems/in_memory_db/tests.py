"""Test cases for the in-memory key-value database.

Deliberate contrasts with file_hosting, because a bank of near-identical problems
trains recall rather than skill:

  * the timestamp argument comes LAST here, not first
  * scan returns "field(value)" strings, not bare names
  * level 4 is backup/restore against explicit snapshots, not a rollback over
    history -- and its "recalculate the ttls" means something genuinely different
"""

from __future__ import annotations

from harness.expect import Exactly
from harness.model import case, op

# ==========================================================================
# Level 1
# ==========================================================================

LEVEL_1 = [
    case(
        "l1_set_get_delete",
        1,
        [
            op("SET", "A", "B", "E"),
            op("GET", "A", "B", ret="E"),
            op("DELETE", "A", "B", ret=True),
            op("GET", "A", "B", ret=None),
            op("DELETE", "A", "B", ret=False, why="nothing left to delete"),
        ],
        tags=["basics"],
        visible=True,
        doc="Set a field on a record, read it, delete it.",
    ),
    case(
        "l1_absent_key_and_field",
        1,
        [
            op("SET", "A", "B", "E"),
            op("GET", "A", "C", ret=None, why="right record, wrong field"),
            op("GET", "X", "B", ret=None, why="no such record"),
            op("DELETE", "X", "B", ret=False),
        ],
        tags=["basics", "edge-values"],
        visible=True,
        doc="Missing records and missing fields both read as nothing.",
    ),
    case(
        "l1_set_overwrites",
        1,
        [
            op("SET", "A", "B", "E"),
            op("SET", "A", "B", "F"),
            op("GET", "A", "B", ret="F"),
        ],
        tags=["basics", "overwrite"],
    ),
    case(
        "l1_fields_are_independent",
        1,
        [
            op("SET", "A", "B", "1"),
            op("SET", "A", "C", "2"),
            op("DELETE", "A", "B", ret=True),
            op("GET", "A", "B", ret=None),
            op("GET", "A", "C", ret="2", why="deleting one field must not clear the record"),
        ],
        tags=["basics"],
    ),
    case(
        "l1_records_are_independent",
        1,
        [
            op("SET", "A", "B", "1"),
            op("SET", "X", "B", "2"),
            op("GET", "A", "B", ret="1"),
            op("GET", "X", "B", ret="2"),
            op("DELETE", "A", "B", ret=True),
            op("GET", "X", "B", ret="2"),
        ],
        tags=["basics"],
    ),
    case(
        "l1_empty_string_is_a_value",
        1,
        [
            op("SET", "A", "B", ""),
            op(
                "GET",
                "A",
                "B",
                ret=Exactly(""),
                why="an empty value is present; None would mean absent",
            ),
            op("DELETE", "A", "B", ret=True),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_values_stay_strings",
        1,
        [
            op("SET", "A", "B", "0"),
            op("GET", "A", "B", ret=Exactly("0"), why="values are opaque strings, not numbers"),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_keys_and_fields_are_case_sensitive",
        1,
        [
            op("SET", "A", "B", "1"),
            op("GET", "a", "B", ret=None),
            op("GET", "A", "b", ret=None),
            op("SET", "a", "b", "2"),
            op("GET", "A", "B", ret="1"),
            op("GET", "a", "b", ret="2"),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_resurrect_after_delete",
        1,
        [
            op("SET", "A", "B", "1"),
            op("DELETE", "A", "B", ret=True),
            op("SET", "A", "B", "2"),
            op("GET", "A", "B", ret="2"),
        ],
        tags=["basics"],
    ),
    case(
        "l1_delete_returns_whether_it_removed_something",
        1,
        [
            op("DELETE", "A", "B", ret=False),
            op("SET", "A", "B", "1"),
            op("DELETE", "A", "B", ret=True),
            op("DELETE", "A", "B", ret=False),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_many_fields_on_one_record",
        1,
        [
            *[op("SET", "R", f"f{i}", str(i)) for i in range(1, 8)],
            op("GET", "R", "f1", ret="1"),
            op("GET", "R", "f7", ret="7"),
            op("GET", "R", "f8", ret=None),
        ],
        tags=["basics"],
    ),
]


# ==========================================================================
# Level 2
# ==========================================================================

LEVEL_2 = [
    case(
        "l2_scan_and_scan_by_prefix",
        2,
        [
            op("SET", "A", "BC", "E"),
            op("SET", "A", "BD", "F"),
            op("SET", "A", "C", "G"),
            op("SCAN", "A", ret=["BC(E)", "BD(F)", "C(G)"]),
            op("SCAN_BY_PREFIX", "A", "B", ret=["BC(E)", "BD(F)"]),
        ],
        tags=["scan", "ordering"],
        visible=True,
        doc="Fields come back as field(value), ordered by field name ascending.",
    ),
    case(
        "l2_nothing_to_scan",
        2,
        [
            op("SCAN", "nope", ret=[]),
            op("SET", "A", "B", "1"),
            op("DELETE", "A", "B", ret=True),
            op("SCAN", "A", ret=[], why="the record is empty, not missing -- same answer"),
            op("SCAN_BY_PREFIX", "A", "z", ret=[]),
        ],
        tags=["scan", "edge-values"],
        visible=True,
        doc="An empty or missing record scans to an empty list.",
    ),
    case(
        "l2_field_order_is_lexicographic_not_numeric",
        2,
        [
            op("SET", "A", "f1", "a"),
            op("SET", "A", "f10", "b"),
            op("SET", "A", "f2", "c"),
            op(
                "SCAN",
                "A",
                ret=["f1(a)", "f10(b)", "f2(c)"],
                why="string order puts f10 before f2",
            ),
        ],
        tags=["scan", "ordering", "tie-break"],
    ),
    case(
        "l2_empty_prefix_matches_every_field",
        2,
        [
            op("SET", "A", "b", "1"),
            op("SET", "A", "a", "2"),
            op("SCAN_BY_PREFIX", "A", "", ret=["a(2)", "b(1)"]),
        ],
        tags=["scan", "edge-values"],
    ),
    case(
        "l2_prefix_is_case_sensitive",
        2,
        [
            op("SET", "A", "Ab", "1"),
            op("SET", "A", "ab", "2"),
            op("SCAN_BY_PREFIX", "A", "A", ret=["Ab(1)"]),
            op("SCAN_BY_PREFIX", "A", "a", ret=["ab(2)"]),
        ],
        tags=["scan", "edge-values"],
    ),
    case(
        "l2_prefix_equal_to_the_whole_field",
        2,
        [
            op("SET", "A", "field", "v"),
            op("SCAN_BY_PREFIX", "A", "field", ret=["field(v)"]),
        ],
        tags=["scan", "edge-values"],
    ),
    case(
        "l2_scan_sees_overwrites_and_deletes",
        2,
        [
            op("SET", "A", "x", "1"),
            op("SET", "A", "y", "2"),
            op("SET", "A", "x", "9"),
            op("SCAN", "A", ret=["x(9)", "y(2)"]),
            op("DELETE", "A", "y", ret=True),
            op("SCAN", "A", ret=["x(9)"]),
        ],
        tags=["scan", "overwrite"],
    ),
    case(
        "l2_scan_is_per_record",
        2,
        [
            op("SET", "A", "x", "1"),
            op("SET", "B", "y", "2"),
            op("SCAN", "A", ret=["x(1)"]),
            op("SCAN", "B", ret=["y(2)"]),
        ],
        tags=["scan"],
    ),
    case(
        "l2_value_is_pasted_verbatim",
        2,
        [
            op("SET", "A", "f", "x(y)"),
            op("SET", "A", "g", ""),
            op(
                "SCAN",
                "A",
                ret=["f(x(y))", "g()"],
                why="the format is a plain concatenation; values are not escaped",
            ),
        ],
        tags=["scan", "edge-values"],
    ),
    case(
        "l2_prefix_does_not_match_the_middle",
        2,
        [
            op("SET", "A", "abc", "1"),
            op("SET", "A", "xabc", "2"),
            op("SCAN_BY_PREFIX", "A", "abc", ret=["abc(1)"]),
        ],
        tags=["scan", "edge-values"],
    ),
    case(
        "l2_level1_still_works",
        2,
        [
            op("SET", "A", "B", "E"),
            op("GET", "A", "B", ret="E"),
            op("DELETE", "A", "B", ret=True),
            op("GET", "A", "B", ret=None),
            op("SCAN", "A", ret=[]),
        ],
        tags=["regression"],
    ),
]


# ==========================================================================
# Level 3
# ==========================================================================

LEVEL_3 = [
    case(
        "l3_ttl_expiry_boundary",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "B", "E", 0, 10),
            op("GET_AT", "A", "B", 5, ret="E"),
            op(
                "GET_AT",
                "A",
                "B",
                10,
                ret=None,
                why="a ttl of 10 covers [0, 10); at exactly 10 it is gone",
            ),
        ],
        tags=["ttl", "boundaries"],
        visible=True,
        doc="A ttl of n covers [timestamp, timestamp + n). Note the timestamp comes last.",
    ),
    case(
        "l3_plain_calls_are_timestamp_zero",
        3,
        [
            op("SET", "A", "B", "E"),
            op("GET_AT", "A", "B", 1000, ret="E", why="a plain SET never expires"),
            op("GET", "A", "B", ret="E"),
            op("SCAN_AT", "A", 1000, ret=["B(E)"]),
        ],
        tags=["refactor", "regression"],
        visible=True,
        doc="The level-1 and level-2 calls are the timestamped ones at t=0 with no ttl.",
    ),
    case(
        "l3_scan_at_hides_expired_fields",
        3,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("SET_AT_WITH_TTL", "A", "y", "2", 0, 5),
            op("SCAN_AT", "A", 1, ret=["x(1)", "y(2)"]),
            op("SCAN_AT", "A", 5, ret=["x(1)"]),
            op("SCAN_BY_PREFIX_AT", "A", "y", 5, ret=[]),
        ],
        tags=["ttl", "scan"],
        visible=True,
        doc="Scans report only fields that are alive at the given timestamp.",
    ),
    case(
        "l3_setting_a_field_replaces_its_lifetime",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "B", "E", 0, 5),
            op("SET_AT_WITH_TTL", "A", "B", "F", 3, 5),
            op("GET_AT", "A", "B", 7, ret="F", why="the second set restarts the clock: [3, 8)"),
            op("GET_AT", "A", "B", 8, ret=None),
        ],
        tags=["ttl", "overwrite"],
        visible=True,
        doc="Setting an existing field replaces its value and its lifetime.",
    ),
    case(
        "l3_set_without_ttl_makes_a_field_permanent",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "B", "E", 0, 5),
            op("SET_AT", "A", "B", "F", 3),
            op("GET_AT", "A", "B", 1000, ret="F"),
        ],
        tags=["ttl", "overwrite"],
    ),
    case(
        "l3_delete_at_on_an_expired_field",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "B", "E", 0, 5),
            op("DELETE_AT", "A", "B", 5, ret=False, why="already gone, so nothing was deleted"),
            op("DELETE_AT", "A", "B", 6, ret=False),
        ],
        tags=["ttl", "boundaries"],
    ),
    case(
        "l3_delete_at_on_a_live_field",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "B", "E", 0, 5),
            op("DELETE_AT", "A", "B", 4, ret=True),
            op("GET_AT", "A", "B", 4, ret=None),
        ],
        tags=["ttl", "basics"],
    ),
    case(
        "l3_zero_ttl_is_dead_on_arrival",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "B", "E", 0, 0),
            op("GET_AT", "A", "B", 0, ret=None, why="[0, 0) contains nothing"),
            op("SCAN_AT", "A", 0, ret=[]),
        ],
        tags=["ttl", "boundaries", "edge-values"],
    ),
    case(
        "l3_fields_expire_independently",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "a", "1", 0, 10),
            op("SET_AT_WITH_TTL", "A", "b", "2", 0, 5),
            op("SET_AT", "A", "c", "3", 0),
            op("SCAN_AT", "A", 4, ret=["a(1)", "b(2)", "c(3)"]),
            op("SCAN_AT", "A", 5, ret=["a(1)", "c(3)"]),
            op("SCAN_AT", "A", 10, ret=["c(3)"]),
        ],
        tags=["ttl", "scan"],
    ),
    case(
        "l3_a_record_whose_fields_all_expired_scans_empty",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "a", "1", 0, 3),
            op("SET_AT_WITH_TTL", "A", "b", "2", 0, 3),
            op("SCAN_AT", "A", 3, ret=[]),
            op("GET_AT", "A", "a", 3, ret=None),
        ],
        tags=["ttl", "scan", "edge-values"],
    ),
    case(
        "l3_scan_by_prefix_at_filters_and_expires",
        3,
        [
            op("SET_AT", "A", "px", "1", 0),
            op("SET_AT_WITH_TTL", "A", "py", "2", 0, 5),
            op("SET_AT", "A", "qz", "3", 0),
            op("SCAN_BY_PREFIX_AT", "A", "p", 1, ret=["px(1)", "py(2)"]),
            op("SCAN_BY_PREFIX_AT", "A", "p", 5, ret=["px(1)"]),
        ],
        tags=["ttl", "scan"],
    ),
    case(
        "l3_expired_field_can_be_set_again",
        3,
        [
            op("SET_AT_WITH_TTL", "A", "B", "E", 0, 5),
            op("GET_AT", "A", "B", 5, ret=None),
            op("SET_AT", "A", "B", "F", 5),
            op("GET_AT", "A", "B", 6, ret="F"),
        ],
        tags=["ttl", "overwrite"],
    ),
    case(
        "l3_level2_scan_still_works",
        3,
        [
            op("SET", "A", "b", "1"),
            op("SET_AT", "A", "a", "2", 0),
            op("SCAN", "A", ret=["a(2)", "b(1)"]),
            op("SCAN_BY_PREFIX", "A", "a", ret=["a(2)"]),
        ],
        tags=["regression", "refactor"],
    ),
    case(
        "l3_level1_delete_still_works",
        3,
        [
            op("SET_AT", "A", "B", "E", 0),
            op("DELETE", "A", "B", ret=True),
            op("GET_AT", "A", "B", 5, ret=None),
            op("DELETE", "A", "B", ret=False),
        ],
        tags=["regression", "refactor"],
    ),
]


# ==========================================================================
# Level 4
# ==========================================================================

LEVEL_4 = [
    case(
        "l4_backup_counts_live_records",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("SET_AT", "B", "y", "2", 0),
            op("BACKUP", 1, ret=2, why="two records hold at least one live field"),
        ],
        tags=["backup"],
        visible=True,
        doc="BACKUP returns the number of records that are neither empty nor expired.",
    ),
    case(
        "l4_restore_discards_later_writes",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("BACKUP", 1, ret=1),
            op("SET_AT", "A", "y", "2", 2),
            op("SET_AT", "C", "z", "3", 3),
            op("RESTORE", 4, 1),
            op("GET_AT", "A", "x", 5, ret="1"),
            op("GET_AT", "A", "y", 5, ret=None, why="written after the backup"),
            op("GET_AT", "C", "z", 5, ret=None),
        ],
        tags=["restore"],
        visible=True,
        doc="RESTORE replaces the whole database with the backup's contents.",
    ),
    case(
        "l4_restore_re_anchors_remaining_lifetimes",
        4,
        [
            op("SET_AT_WITH_TTL", "A", "x", "1", 0, 10),
            op("BACKUP", 5, ret=1, why="at t=5 the field has 5 seconds left"),
            op("RESTORE", 100, 5),
            op(
                "GET_AT",
                "A",
                "x",
                104,
                ret="1",
                why="the 5 remaining seconds now run from the restore instant: [100, 105)",
            ),
            op("GET_AT", "A", "x", 105, ret=None),
        ],
        tags=["restore", "ttl", "boundaries"],
        visible=True,
        doc="Restored fields keep the time they had LEFT, measured from the restore.",
    ),
    case(
        "l4_backup_ignores_expired_records",
        4,
        [
            op("SET_AT_WITH_TTL", "A", "x", "1", 0, 5),
            op("SET_AT", "B", "y", "2", 0),
            op("BACKUP", 5, ret=1, why="A's only field died at t=5"),
        ],
        tags=["backup", "ttl"],
    ),
    case(
        "l4_backup_ignores_emptied_records",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("DELETE_AT", "A", "x", 1, ret=True),
            op("SET_AT", "B", "y", "2", 1),
            op("BACKUP", 2, ret=1),
        ],
        tags=["backup"],
    ),
    case(
        "l4_backup_on_an_empty_database",
        4,
        [op("BACKUP", 0, ret=0)],
        tags=["backup", "edge-values"],
    ),
    case(
        "l4_restore_picks_the_latest_backup_at_or_before",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("BACKUP", 1, ret=1),
            op("SET_AT", "A", "y", "2", 2),
            op("BACKUP", 3, ret=1),
            op("SET_AT", "A", "z", "3", 4),
            op("RESTORE", 10, 3, why="the t=3 backup, which had x and y"),
            op("SCAN_AT", "A", 11, ret=["x(1)", "y(2)"]),
        ],
        tags=["restore", "history"],
    ),
    case(
        "l4_restore_at_an_earlier_backup",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("BACKUP", 1, ret=1),
            op("SET_AT", "A", "y", "2", 2),
            op("BACKUP", 3, ret=1),
            op("RESTORE", 10, 1, why="skip the newer backup and take the t=1 one"),
            op("SCAN_AT", "A", 11, ret=["x(1)"]),
        ],
        tags=["restore", "history"],
    ),
    case(
        "l4_restore_with_no_earlier_backup_does_nothing",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("BACKUP", 5, ret=1),
            op("RESTORE", 10, 3, why="no backup at or before t=3, so the state is untouched"),
            op("GET_AT", "A", "x", 11, ret="1"),
        ],
        tags=["restore", "edge-values"],
    ),
    case(
        "l4_a_backup_is_a_snapshot_not_a_view",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("BACKUP", 1, ret=1),
            op("SET_AT", "A", "x", "999", 2),
            op("RESTORE", 3, 1),
            op(
                "GET_AT",
                "A",
                "x",
                4,
                ret="1",
                why="a shallow copy would have let the t=2 write reach into the backup",
            ),
        ],
        tags=["backup", "restore", "aliasing"],
    ),
    case(
        "l4_permanent_fields_survive_a_restore",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("BACKUP", 5, ret=1),
            op("RESTORE", 100, 5),
            op("GET_AT", "A", "x", 100000, ret="1", why="no ttl stays no ttl"),
        ],
        tags=["restore", "ttl"],
    ),
    case(
        "l4_restore_twice",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("BACKUP", 1, ret=1),
            op("SET_AT", "A", "y", "2", 2),
            op("BACKUP", 3, ret=1),
            op("RESTORE", 4, 3),
            op("SCAN_AT", "A", 5, ret=["x(1)", "y(2)"]),
            op("RESTORE", 6, 1),
            op("SCAN_AT", "A", 7, ret=["x(1)"], why="both backups are still available"),
        ],
        tags=["restore", "history"],
    ),
    case(
        "l4_backup_after_restore",
        4,
        [
            op("SET_AT", "A", "x", "1", 0),
            op("SET_AT", "B", "y", "2", 0),
            op("BACKUP", 1, ret=2),
            op("SET_AT", "C", "z", "3", 2),
            op("RESTORE", 3, 1),
            op("BACKUP", 4, ret=2, why="C is gone again"),
        ],
        tags=["backup", "restore"],
    ),
    case(
        "l4_all_levels_together",
        4,
        [
            op("SET", "cfg", "mode", "fast"),
            op("SET_AT_WITH_TTL", "cfg", "flag", "on", 1, 10),
            op("SET_AT", "log", "line1", "hello", 2),
            op("SCAN_AT", "cfg", 3, ret=["flag(on)", "mode(fast)"]),
            op("BACKUP", 3, ret=2),
            op("DELETE_AT", "cfg", "mode", 4, ret=True),
            op("SET_AT", "extra", "k", "v", 5),
            op("SCAN_AT", "cfg", 6, ret=["flag(on)"]),
            op("RESTORE", 20, 3),
            op("GET_AT", "extra", "k", 21, ret=None),
            op("GET_AT", "cfg", "mode", 21, ret="fast", why="the delete is undone"),
            op(
                "GET_AT",
                "cfg",
                "flag",
                27,
                ret="on",
                why="8 seconds were left at t=3, so it now runs [20, 28)",
            ),
            op("GET_AT", "cfg", "flag", 28, ret=None),
            op("SCAN_AT", "log", 21, ret=["line1(hello)"]),
        ],
        tags=["regression", "restore", "ttl", "scan"],
    ),
]


ALL_CASES = tuple(LEVEL_1 + LEVEL_2 + LEVEL_3 + LEVEL_4)
