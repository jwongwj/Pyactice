"""Banking system with scheduled cashback and historical balances.

Reported at Ramp, eBay and others. Kept in the bank because its level-3 and level-4
turns are unlike the other three problems: nothing expires here, but effects are
*deferred*, and every balance change has to stay queryable afterwards.
"""

from __future__ import annotations

from harness.model import Level, Method, Problem

from .tests import ALL_CASES

METHODS = (
    Method(
        display="CREATE_ACCOUNT",
        signature="(self, timestamp: int, account_id: str) -> bool",
        level=1,
        doc="Create an account. False if that id already exists.",
    ),
    Method(
        display="DEPOSIT",
        signature="(self, timestamp: int, account_id: str, amount: int) -> int | None",
        level=1,
        doc="Add money. Return the new balance, or None if there is no such account.",
    ),
    Method(
        display="TRANSFER",
        signature=(
            "(self, timestamp: int, source_id: str, target_id: str, amount: int) -> int | None"
        ),
        level=1,
        doc=(
            "Move money between two different accounts. Return the source's new "
            "balance, or None if the transfer cannot happen."
        ),
    ),
    Method(
        display="TOP_SPENDERS",
        signature="(self, timestamp: int, n: int) -> list[str]",
        level=2,
        doc=(
            'Return ["<account_id>(<total outgoing>)", ...] for the n biggest '
            "spenders, largest first, ties broken by account id ascending."
        ),
    ),
    Method(
        display="PAY",
        signature="(self, timestamp: int, account_id: str, amount: int) -> str | None",
        level=3,
        doc=(
            "Withdraw money and schedule 2% cashback 24 hours later. Return the "
            "payment id, or None if the payment cannot happen."
        ),
    ),
    Method(
        display="GET_PAYMENT_STATUS",
        signature="(self, timestamp: int, account_id: str, payment: str) -> str | None",
        level=3,
        doc=(
            'Return "IN_PROGRESS" or "CASHBACK_RECEIVED", or None if the account or '
            "payment does not exist or the payment is not that account's."
        ),
    ),
    Method(
        display="MERGE_ACCOUNTS",
        signature="(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool",
        level=4,
        doc="Fold account 2 into account 1 and remove account 2.",
    ),
    Method(
        display="GET_BALANCE",
        signature="(self, timestamp: int, account_id: str, time_at: int) -> int | None",
        level=4,
        doc=(
            "The account's balance as of time_at, or None if the account does not "
            "exist or did not exist then."
        ),
    ),
)

LEVELS = (
    Level(1, "Initial Design & Basic Functions", (10, 15), 100, "accounts and balances"),
    Level(2, "Data Structures & Data Processing", (15, 20), 140, "ranked query"),
    Level(3, "Refactoring & Encapsulation", (20, 30), 180, "deferred effects"),
    Level(4, "Extending Design & Functionality", (20, 25), 180, "merge and time travel"),
)

TAG_GLOSSARY = {
    "basics": "accounts, deposits and transfers",
    "rejection": "operations that fail and must change nothing",
    "edge-values": "zero amounts, exact balances, case sensitivity",
    "ranking": "the top-spenders query",
    "ordering": "outgoing-total ordering",
    "tie-break": "account-id ordering within equal totals",
    "top-n": "the n-result cap",
    "payments": "PAY and payment ids",
    "cashback": "the deferred 2% refund",
    "boundaries": "the exact millisecond cashback lands",
    "merge": "folding one account into another",
    "history": "balances at past instants",
    "regression": "earlier levels still working after a refactor",
}

PROBLEM = Problem(
    key="banking",
    title="Banking System",
    blurb=(
        "Implement a simplified banking system: accounts, deposits and transfers; "
        "then rank accounts by spending; then payments with cashback that arrives a "
        "day later; then account merging and balances at any past instant."
    ),
    class_name="BankingSystem",
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Reconstructed from widely reported CodeSignal ICF variant; see docs/PROBLEM_BRIEFS.md",
)
