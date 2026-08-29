#!/usr/bin/env python3
"""Generate the bank ledger from the bank itself.

    python3 tools/bank_report.py            # print it
    python3 tools/bank_report.py --write    # write docs/BANK.md

The status table was maintained by hand in three places -- docs/STATE.md, and twice in
README.md, with a hand-counted case total -- and had already drifted: solutions/README.md
said file_hosting was 57 cases while the other two said 58. Three hand-copied tables is
a guarantee of being wrong within a week; at a hundred problems it is not even worth
attempting. So the numbers come from the bank, and only the prose is written.

What "verified" means here is deliberately narrow: an oracle exists at
solutions/<key>.py, so `./pfs validate` can re-run the differential gate on demand. It
does not claim the gate passed on this run -- run `./pfs validate` for that.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.loader import BROKEN, all_problems  # noqa: E402
from harness.model import KIND_DRILL, KIND_PROGRESSIVE  # noqa: E402

TEACHING = ("APPROACH.md", "EXPLANATION.md")
# A progressive problem discloses across four levels, so its teaching artifacts are the
# contract and the decision ledger. harness/validate.py requires exactly those of it and
# never asks it for an approach, on the reasoning that a walkthrough written before the
# attempt is the answer key. Measuring the capstones against TEACHING anyway reported all
# five as 0/2 against files nothing requires, nothing reads, and none should contain.
PROGRESSIVE_TEACHING = ("CONTRACT.md", "DECISIONS.md")


def rows():
    for key, problem in sorted(all_problems().items()):
        directory = problem.directory
        oracle = ROOT / "solutions" / f"{key}.py"
        snapshots = sorted((ROOT / "solutions" / key).glob("level*.py"))
        hidden = sum(1 for c in problem.cases if not c.visible)
        # Each kind teaches with a different artifact, so the ledger has to ask each for
        # what it actually owes. Counting one pair for all three reported every drill as
        # 0/2 while its lesson sat right there, and every capstone as 0/2 for a pair it is
        # deliberately not allowed to have. This mirrors the per-kind requirement in
        # harness/validate.py, which is the gate that enforces it.
        if problem.kind == KIND_DRILL:
            wanted = ("LESSON.md",)
        elif problem.kind == KIND_PROGRESSIVE:
            wanted = PROGRESSIVE_TEACHING
        else:
            wanted = TEACHING
        docs = [name for name in wanted if (directory / name).exists()]
        yield {
            "key": key,
            "kind": problem.kind,
            "category": problem.category or "-",
            "difficulty": problem.difficulty or "-",
            "levels": len(problem.levels),
            "cases": len(problem.cases),
            "hidden": hidden,
            "points": problem.total_points,
            "oracle": oracle.exists(),
            "snapshots": len(snapshots),
            "teaching": len(docs),
            "teaching_of": len(wanted),
        }


def render() -> str:
    data = list(rows())
    out: list[str] = []
    out.append("# Bank ledger")
    out.append("")
    out.append("**Generated** by `python3 tools/bank_report.py --write`. Do not edit by hand.")
    out.append("")
    out.append(
        f"{len(data)} problems, {sum(d['cases'] for d in data)} cases, "
        f"{sum(d['hidden'] for d in data)} of them hidden."
    )
    out.append("")
    out.append("| key | kind | category | diff | levels | cases | hidden | oracle | snapshots | teaching |")
    out.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for d in data:
        out.append(
            f"| `{d['key']}` | {d['kind']} | {d['category']} | {d['difficulty']} | "
            f"{d['levels']} | {d['cases']} | {d['hidden']} | "
            f"{'yes' if d['oracle'] else '**no**'} | {d['snapshots'] or '-'} | "
            f"{d['teaching']}/{d['teaching_of']} |"
        )
    out.append("")

    missing = [d["key"] for d in data if not d["oracle"]]
    if missing:
        out.append("## Not re-verifiable")
        out.append("")
        out.append(
            "No oracle at `solutions/<key>.py`, so `./pfs validate` cannot re-run the "
            "differential gate and the expected values cannot be re-checked after any "
            "change to the suite:"
        )
        out.append("")
        for key in missing:
            out.append(f"- `{key}`")
        out.append("")

    thin = [d["key"] for d in data if d["teaching"] < d["teaching_of"]]
    if thin:
        out.append("## Missing teaching material")
        out.append("")
        out.append("No `APPROACH.md` and/or `EXPLANATION.md`, so the platform can show the")
        out.append("answer but cannot explain it:")
        out.append("")
        for key in sorted(set(thin)):
            out.append(f"- `{key}`")
        out.append("")

    if BROKEN:
        out.append("## Failed to load")
        out.append("")
        for name, why in sorted(BROKEN.items()):
            out.append(f"- `{name}` — {why}")
        out.append("")

    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write docs/BANK.md")
    args = parser.parse_args(argv)
    text = render()
    if args.write:
        (ROOT / "docs" / "BANK.md").write_text(text)
        print(f"wrote docs/BANK.md ({len(text.splitlines())} lines)")
    else:
        print(text, end="")
    # Non-zero while anything is unverifiable, so this can gate a change.
    return 1 if BROKEN or any(not d["oracle"] for d in rows()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
