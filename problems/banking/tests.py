"""Test cases for the banking system.

The odd one out in this bank, and deliberately so. Levels 3 and 4 are not about
expiry: level 3 introduces a *deferred* effect (cashback that lands a day later)
and level 4 wants balances at arbitrary past instants. Between them they force a
different refactor from the `*_at` pattern -- every operation has to advance the
world to its own timestamp before doing anything, and every balance change has to
be remembered rather than overwritten.
"""

from __future__ import annotations

from harness.model import case, op

DAY = 86_400_000  # milliseconds


# ==========================================================================
# Level 1
# ==========================================================================

LEVEL_1 = [
    case(
        "l1_create_deposit_transfer",
        1,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "a", ret=False, why="already exists"),
            op("CREATE_ACCOUNT", 3, "b", ret=True),
            op("DEPOSIT", 4, "a", 100, ret=100, why="deposit returns the new balance"),
            op("DEPOSIT", 5, "a", 50, ret=150),
            op("TRANSFER", 6, "a", "b", 70, ret=80, why="transfer returns the SOURCE's balance"),
            op("DEPOSIT", 7, "b", 0, ret=70, why="a zero deposit is a way to read a balance"),
        ],
        tags=["basics"],
        visible=True,
        doc="Accounts, deposits, and a transfer that reports the source's new balance.",
    ),
    case(
        "l1_transfers_that_must_be_refused",
        1,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 100, ret=100),
            op("TRANSFER", 4, "a", "ghost", 10, ret=None, why="no such target"),
            op("TRANSFER", 5, "ghost", "a", 10, ret=None, why="no such source"),
            op("TRANSFER", 6, "a", "a", 10, ret=None, why="a transfer to yourself is not a transfer"),
            op("TRANSFER", 7, "a", "b", 101, ret=None, why="insufficient funds"),
            op("DEPOSIT", 8, "a", 0, ret=100, why="none of those moved a cent"),
        ],
        tags=["basics", "rejection"],
        visible=True,
        doc="A refused transfer changes nothing.",
    ),
    case(
        "l1_deposit_into_an_unknown_account",
        1,
        [
            op("DEPOSIT", 1, "ghost", 100, ret=None),
            op("CREATE_ACCOUNT", 2, "ghost", ret=True),
            op("DEPOSIT", 3, "ghost", 0, ret=0, why="the earlier deposit did not happen"),
        ],
        tags=["basics", "rejection"],
    ),
    case(
        "l1_transfer_of_the_whole_balance",
        1,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 100, ret=100),
            op("TRANSFER", 4, "a", "b", 100, ret=0, why="exactly enough is enough"),
            op("DEPOSIT", 5, "b", 0, ret=100),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_zero_balance_is_not_a_missing_account",
        1,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 0, ret=0, why="0 is a balance; None would mean no account"),
        ],
        tags=["basics", "edge-values"],
    ),
    case(
        "l1_failed_create_keeps_the_balance",
        1,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 500, ret=500),
            op("CREATE_ACCOUNT", 3, "a", ret=False),
            op("DEPOSIT", 4, "a", 0, ret=500, why="the rejected create must not have reset it"),
        ],
        tags=["basics", "rejection"],
    ),
    case(
        "l1_accounts_are_independent",
        1,
        [
            *[op("CREATE_ACCOUNT", i, f"acct{i}", ret=True) for i in range(1, 5)],
            op("DEPOSIT", 5, "acct1", 10, ret=10),
            op("DEPOSIT", 6, "acct3", 30, ret=30),
            op("DEPOSIT", 7, "acct2", 0, ret=0),
            op("DEPOSIT", 8, "acct4", 0, ret=0),
        ],
        tags=["basics"],
    ),
    case(
        "l1_account_ids_are_case_sensitive",
        1,
        [
            op("CREATE_ACCOUNT", 1, "A", ret=True),
            op("CREATE_ACCOUNT", 2, "a", ret=True),
            op("DEPOSIT", 3, "A", 10, ret=10),
            op("DEPOSIT", 4, "a", 0, ret=0),
        ],
        tags=["basics", "edge-values"],
    ),
]


# ==========================================================================
# Level 2
# ==========================================================================

LEVEL_2 = [
    case(
        "l2_ranked_by_money_sent",
        2,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("CREATE_ACCOUNT", 3, "c", ret=True),
            op("DEPOSIT", 4, "a", 100, ret=100),
            op("DEPOSIT", 5, "b", 100, ret=100),
            op("DEPOSIT", 6, "c", 100, ret=100),
            op("TRANSFER", 7, "a", "b", 30, ret=70),
            op("TRANSFER", 8, "b", "c", 50, ret=80),
            op(
                "TOP_SPENDERS",
                9,
                3,
                ret=["b(50)", "a(30)", "c(0)"],
                why="c has spent nothing but is still ranked",
            ),
        ],
        tags=["ranking", "ordering"],
        visible=True,
        doc="Ranked by total sent, descending. Accounts that never spent are included.",
    ),
    case(
        "l2_ties_and_the_cap",
        2,
        [
            op("CREATE_ACCOUNT", 1, "b", ret=True),
            op("CREATE_ACCOUNT", 2, "a", ret=True),
            op("CREATE_ACCOUNT", 3, "c", ret=True),
            op("DEPOSIT", 4, "a", 100, ret=100),
            op("DEPOSIT", 5, "b", 100, ret=100),
            op("TRANSFER", 6, "b", "c", 20, ret=80),
            op("TRANSFER", 7, "a", "c", 20, ret=80),
            op(
                "TOP_SPENDERS",
                8,
                2,
                ret=["a(20)", "b(20)"],
                why="equal totals order by id, not by when the account was made",
            ),
        ],
        tags=["ranking", "tie-break", "top-n"],
        visible=True,
        doc="Ties go to the smaller account id; n limits the result.",
    ),
    case(
        "l2_receiving_and_depositing_are_not_spending",
        2,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 500, ret=500),
            op("TRANSFER", 4, "a", "b", 100, ret=400),
            op("DEPOSIT", 5, "b", 900, ret=1000),
            op("TOP_SPENDERS", 6, 5, ret=["a(100)", "b(0)"]),
        ],
        tags=["ranking"],
    ),
    case(
        "l2_spending_accumulates",
        2,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 500, ret=500),
            op("TRANSFER", 4, "a", "b", 100, ret=400),
            op("TRANSFER", 5, "a", "b", 250, ret=150),
            op("TOP_SPENDERS", 6, 5, ret=["a(350)", "b(0)"]),
        ],
        tags=["ranking"],
    ),
    case(
        "l2_refused_transfers_do_not_count",
        2,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 50, ret=50),
            op("TRANSFER", 4, "a", "b", 500, ret=None),
            op("TOP_SPENDERS", 5, 5, ret=["a(0)", "b(0)"]),
        ],
        tags=["ranking", "rejection"],
    ),
    case(
        "l2_id_tie_break_is_lexicographic",
        2,
        [
            op("CREATE_ACCOUNT", 1, "acct2", ret=True),
            op("CREATE_ACCOUNT", 2, "acct10", ret=True),
            op("CREATE_ACCOUNT", 3, "acct1", ret=True),
            op(
                "TOP_SPENDERS",
                4,
                3,
                ret=["acct1(0)", "acct10(0)", "acct2(0)"],
                why="string order puts acct10 before acct2, whatever order they were made in",
            ),
        ],
        tags=["ranking", "tie-break"],
    ),
    case(
        "l2_n_larger_than_the_number_of_accounts",
        2,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("TOP_SPENDERS", 2, 100, ret=["a(0)"]),
        ],
        tags=["ranking", "top-n"],
    ),
    case(
        "l2_no_accounts_at_all",
        2,
        [op("TOP_SPENDERS", 1, 5, ret=[])],
        tags=["ranking", "edge-values"],
    ),
    case(
        "l2_n_of_zero",
        2,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("TOP_SPENDERS", 2, 0, ret=[]),
        ],
        tags=["ranking", "top-n", "edge-values"],
    ),
    case(
        "l2_level1_still_works",
        2,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "a", ret=False),
            op("DEPOSIT", 3, "a", 10, ret=10),
            op("TRANSFER", 4, "a", "a", 1, ret=None),
            op("TOP_SPENDERS", 5, 1, ret=["a(0)"]),
        ],
        tags=["regression"],
    ),
]


# ==========================================================================
# Level 3
# ==========================================================================

LEVEL_3 = [
    case(
        "l3_pay_then_cashback_a_day_later",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 1000, ret=1000),
            op("PAY", 3, "a", 100, ret="payment1"),
            op("GET_PAYMENT_STATUS", 4, "a", "payment1", ret="IN_PROGRESS"),
            op("DEPOSIT", 5, "a", 0, ret=900, why="the money leaves immediately"),
            op("GET_PAYMENT_STATUS", 3 + DAY, "a", "payment1", ret="CASHBACK_RECEIVED"),
            op("DEPOSIT", 3 + DAY, "a", 0, ret=902, why="2% of 100, refunded 24h after the pay"),
        ],
        tags=["payments", "cashback"],
        visible=True,
        doc="PAY withdraws now and refunds 2% exactly 86400000 ms later.",
    ),
    case(
        "l3_payments_that_must_be_refused",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("PAY", 2, "a", 1, ret=None, why="nothing in the account"),
            op("DEPOSIT", 3, "a", 100, ret=100),
            op("PAY", 4, "ghost", 1, ret=None),
            op("PAY", 5, "a", 101, ret=None, why="insufficient funds"),
            op("DEPOSIT", 6, "a", 0, ret=100),
            op("PAY", 7, "a", 100, ret="payment1", why="the first successful pay is still payment1"),
        ],
        tags=["payments", "rejection"],
        visible=True,
        doc="Refused payments take no money and consume no payment id.",
    ),
    case(
        "l3_payment_ids_are_global_and_owned",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 100, ret=100),
            op("DEPOSIT", 4, "b", 100, ret=100),
            op("PAY", 5, "a", 10, ret="payment1"),
            op("PAY", 6, "b", 10, ret="payment2", why="the counter is global, not per account"),
            op("GET_PAYMENT_STATUS", 7, "b", "payment1", ret=None, why="payment1 is not b's"),
            op("GET_PAYMENT_STATUS", 8, "a", "payment2", ret=None),
            op("GET_PAYMENT_STATUS", 9, "ghost", "payment1", ret=None),
            op("GET_PAYMENT_STATUS", 10, "a", "payment9", ret=None),
        ],
        tags=["payments", "rejection"],
        visible=True,
        doc="Payment ids count up across the whole bank, and belong to one account.",
    ),
    case(
        "l3_cashback_lands_on_the_exact_millisecond",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 1000, ret=1000),
            op("PAY", 3, "a", 100, ret="payment1"),
            op("GET_PAYMENT_STATUS", 3 + DAY - 1, "a", "payment1", ret="IN_PROGRESS"),
            op("DEPOSIT", 3 + DAY - 1, "a", 0, ret=900),
            op("GET_PAYMENT_STATUS", 3 + DAY, "a", "payment1", ret="CASHBACK_RECEIVED"),
            op("DEPOSIT", 3 + DAY, "a", 0, ret=902),
        ],
        tags=["cashback", "boundaries"],
    ),
    case(
        "l3_cashback_is_rounded_down",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 1000, ret=1000),
            op("PAY", 3, "a", 50, ret="payment1", why="2% of 50 is 1"),
            op("PAY", 4, "a", 49, ret="payment2", why="2% of 49 is 0.98, which floors to 0"),
            op("DEPOSIT", 5, "a", 0, ret=901),
            op("DEPOSIT", 4 + DAY, "a", 0, ret=902),
            op("GET_PAYMENT_STATUS", 4 + DAY, "a", "payment2", ret="CASHBACK_RECEIVED"),
        ],
        tags=["cashback", "edge-values"],
    ),
    case(
        "l3_cashback_arrives_before_the_operation_that_notices_it",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 100, ret=100),
            op("PAY", 3, "a", 100, ret="payment1"),
            op("PAY", 4, "a", 1, ret=None, why="balance is 0 until the cashback lands"),
            op(
                "PAY",
                3 + DAY,
                "a",
                2,
                ret="payment2",
                why="the cashback must be applied before this pay is judged",
            ),
            op("DEPOSIT", 3 + DAY, "a", 0, ret=0),
        ],
        tags=["cashback", "ordering", "payments"],
    ),
    case(
        "l3_several_cashbacks_land_in_order",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 1000, ret=1000),
            op("PAY", 3, "a", 100, ret="payment1"),
            op("PAY", 4, "a", 200, ret="payment2"),
            op("DEPOSIT", 5, "a", 0, ret=700),
            op("GET_PAYMENT_STATUS", 3 + DAY, "a", "payment1", ret="CASHBACK_RECEIVED"),
            op("GET_PAYMENT_STATUS", 3 + DAY, "a", "payment2", ret="IN_PROGRESS"),
            op("DEPOSIT", 3 + DAY, "a", 0, ret=702),
            op("DEPOSIT", 4 + DAY, "a", 0, ret=706, why="payment2's 4 arrives a millisecond later"),
        ],
        tags=["cashback", "ordering"],
    ),
    case(
        "l3_paying_counts_as_spending",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 100, ret=100),
            op("DEPOSIT", 4, "b", 100, ret=100),
            op("PAY", 5, "a", 30, ret="payment1"),
            op("TRANSFER", 6, "b", "a", 10, ret=90),
            op("TOP_SPENDERS", 7, 2, ret=["a(30)", "b(10)"]),
        ],
        tags=["payments", "ranking", "regression"],
    ),
    case(
        "l3_cashback_does_not_reduce_what_you_spent",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 1000, ret=1000),
            op("PAY", 3, "a", 100, ret="payment1"),
            op(
                "TOP_SPENDERS",
                3 + DAY,
                1,
                ret=["a(100)"],
                why="the refund is income, not a reduction in spending",
            ),
        ],
        tags=["cashback", "ranking"],
    ),
    case(
        "l3_paying_the_whole_balance",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 100, ret=100),
            op("PAY", 3, "a", 100, ret="payment1"),
            op("DEPOSIT", 4, "a", 0, ret=0),
        ],
        tags=["payments", "edge-values"],
    ),
    case(
        "l3_level1_still_works",
        3,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("CREATE_ACCOUNT", 3, "a", ret=False),
            op("DEPOSIT", 4, "a", 100, ret=100),
            op("TRANSFER", 5, "a", "b", 40, ret=60),
            op("TRANSFER", 6, "a", "b", 1000, ret=None),
            op("DEPOSIT", 7, "b", 0, ret=40),
        ],
        tags=["regression"],
    ),
]


# ==========================================================================
# Level 4
# ==========================================================================

LEVEL_4 = [
    case(
        "l4_merge_combines_money_and_history",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 100, ret=100),
            op("DEPOSIT", 4, "b", 50, ret=50),
            op("TRANSFER", 5, "a", "b", 20, ret=80),
            op("MERGE_ACCOUNTS", 6, "a", "b", ret=True),
            op("DEPOSIT", 7, "a", 0, ret=150, why="80 + 70"),
            op("DEPOSIT", 8, "b", 0, ret=None, why="b is gone"),
            op("TOP_SPENDERS", 9, 5, ret=["a(20)"], why="the spending totals merged too"),
        ],
        tags=["merge"],
        visible=True,
        doc="Merging folds balances and spending into the first account and removes the second.",
    ),
    case(
        "l4_balance_at_a_past_instant",
        4,
        [
            op("CREATE_ACCOUNT", 10, "a", ret=True),
            op("DEPOSIT", 20, "a", 100, ret=100),
            op("DEPOSIT", 30, "a", 50, ret=150),
            op("GET_BALANCE", 40, "a", 10, ret=0, why="just created"),
            op("GET_BALANCE", 40, "a", 25, ret=100, why="between the two deposits"),
            op("GET_BALANCE", 40, "a", 30, ret=150),
            op("GET_BALANCE", 40, "a", 9, ret=None, why="the account did not exist yet"),
            op("GET_BALANCE", 40, "ghost", 20, ret=None),
        ],
        tags=["history"],
        visible=True,
        doc="GET_BALANCE answers for any instant at or before now.",
    ),
    case(
        "l4_merge_carries_a_pending_cashback",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "b", 1000, ret=1000),
            op("PAY", 4, "b", 100, ret="payment1"),
            op("MERGE_ACCOUNTS", 5, "a", "b", ret=True),
            op(
                "GET_PAYMENT_STATUS",
                6,
                "a",
                "payment1",
                ret="IN_PROGRESS",
                why="b's payment is a's problem now",
            ),
            op("GET_PAYMENT_STATUS", 7, "b", "payment1", ret=None),
            op("DEPOSIT", 4 + DAY, "a", 0, ret=902, why="900 came over, then the 2 landed"),
        ],
        tags=["merge", "cashback", "payments"],
        visible=True,
        doc="An in-flight cashback follows the money into the surviving account.",
    ),
    case(
        "l4_merges_that_must_be_refused",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 100, ret=100),
            op("MERGE_ACCOUNTS", 3, "a", "ghost", ret=False),
            op("MERGE_ACCOUNTS", 4, "ghost", "a", ret=False),
            op("MERGE_ACCOUNTS", 5, "a", "a", ret=False, why="merging an account into itself"),
            op("DEPOSIT", 6, "a", 0, ret=100, why="none of those doubled anything"),
        ],
        tags=["merge", "rejection"],
    ),
    case(
        "l4_the_absorbed_account_is_gone_for_good",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "b", 50, ret=50),
            op("MERGE_ACCOUNTS", 4, "a", "b", ret=True),
            op("GET_BALANCE", 5, "b", 3, ret=None, why="not even historically queryable"),
            op("TRANSFER", 6, "a", "b", 1, ret=None),
            op("TOP_SPENDERS", 7, 5, ret=["a(0)"]),
            op("CREATE_ACCOUNT", 8, "b", ret=True, why="the id is free again"),
            op("DEPOSIT", 9, "b", 0, ret=0),
        ],
        tags=["merge", "history"],
    ),
    case(
        "l4_history_before_a_merge_is_the_survivors_own",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 10, ret=10),
            op("DEPOSIT", 4, "b", 90, ret=90),
            op("MERGE_ACCOUNTS", 5, "a", "b", ret=True),
            op("GET_BALANCE", 6, "a", 3, ret=10, why="a's own balance then, not the merged total"),
            op("GET_BALANCE", 6, "a", 5, ret=100),
        ],
        tags=["merge", "history"],
    ),
    case(
        "l4_balance_history_sees_cashback_when_it_lands",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 1000, ret=1000),
            op("PAY", 3, "a", 100, ret="payment1"),
            op("GET_BALANCE", 3 + DAY, "a", 3 + DAY - 1, ret=900),
            op("GET_BALANCE", 3 + DAY, "a", 3 + DAY, ret=902),
        ],
        tags=["history", "cashback", "boundaries"],
    ),
    case(
        "l4_balance_at_the_current_instant",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 42, ret=42),
            op("GET_BALANCE", 2, "a", 2, ret=42),
        ],
        tags=["history", "boundaries"],
    ),
    case(
        "l4_history_records_transfers_on_both_sides",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("DEPOSIT", 3, "a", 100, ret=100),
            op("TRANSFER", 4, "a", "b", 30, ret=70),
            op("GET_BALANCE", 5, "a", 3, ret=100),
            op("GET_BALANCE", 5, "a", 4, ret=70),
            op("GET_BALANCE", 5, "b", 3, ret=0),
            op("GET_BALANCE", 5, "b", 4, ret=30),
        ],
        tags=["history"],
    ),
    case(
        "l4_history_ignores_refused_operations",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("DEPOSIT", 2, "a", 50, ret=50),
            op("TRANSFER", 3, "a", "ghost", 10, ret=None),
            op("PAY", 4, "a", 500, ret=None),
            op("GET_BALANCE", 5, "a", 4, ret=50),
        ],
        tags=["history", "rejection"],
    ),
    case(
        "l4_merged_spending_totals_add",
        4,
        [
            op("CREATE_ACCOUNT", 1, "a", ret=True),
            op("CREATE_ACCOUNT", 2, "b", ret=True),
            op("CREATE_ACCOUNT", 3, "c", ret=True),
            op("DEPOSIT", 4, "a", 100, ret=100),
            op("DEPOSIT", 5, "b", 100, ret=100),
            op("TRANSFER", 6, "a", "c", 10, ret=90),
            op("TRANSFER", 7, "b", "c", 25, ret=75),
            op("MERGE_ACCOUNTS", 8, "a", "b", ret=True),
            op("TOP_SPENDERS", 9, 5, ret=["a(35)", "c(0)"]),
        ],
        tags=["merge", "ranking"],
    ),
    case(
        "l4_all_levels_together",
        4,
        [
            op("CREATE_ACCOUNT", 1, "alice", ret=True),
            op("CREATE_ACCOUNT", 2, "bob", ret=True),
            op("DEPOSIT", 3, "alice", 500, ret=500),
            op("DEPOSIT", 4, "bob", 300, ret=300),
            op("TRANSFER", 5, "alice", "bob", 100, ret=400),
            op("PAY", 6, "bob", 200, ret="payment1"),
            op("TOP_SPENDERS", 7, 5, ret=["bob(200)", "alice(100)"]),
            op("GET_PAYMENT_STATUS", 8, "bob", "payment1", ret="IN_PROGRESS"),
            op("MERGE_ACCOUNTS", 9, "alice", "bob", ret=True),
            op("DEPOSIT", 10, "alice", 0, ret=600, why="400 + 200"),
            op("TOP_SPENDERS", 11, 5, ret=["alice(300)"]),
            op("GET_BALANCE", 12, "alice", 5, ret=400, why="alice alone, before the merge"),
            op("GET_BALANCE", 12, "bob", 5, ret=None),
            op("GET_PAYMENT_STATUS", 6 + DAY, "alice", "payment1", ret="CASHBACK_RECEIVED"),
            op("DEPOSIT", 6 + DAY, "alice", 0, ret=604, why="2% of 200"),
            op("TOP_SPENDERS", 6 + DAY, 5, ret=["alice(300)"]),
        ],
        tags=["regression", "merge", "cashback", "history", "ranking"],
    ),
]


ALL_CASES = tuple(LEVEL_1 + LEVEL_2 + LEVEL_3 + LEVEL_4)
