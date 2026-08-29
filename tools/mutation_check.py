#!/usr/bin/env python3
"""Mutation testing for a problem's test suite.

`./pfs validate --against ref.py` proves the suite is *consistent* with a correct
implementation. It does not prove the suite is *useful*: a suite of trivial cases
also agrees with a correct implementation. Mutation testing closes that gap by
breaking the reference in the specific ways real candidates break it and checking
that the suite notices.

    python3 tools/mutation_check.py file_hosting path/to/reference.py

Every mutant must be caught. A missed mutant is a hole in the suite: some real bug
would pass all four levels, which means the practice is lying to you.

The catalogues below double as a study list -- each entry is a mistake somebody
actually makes under time pressure.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent

# problem key -> {label: [(find, replace), ...]}
# A mutant applies if at least one of its edits matched. Keep the `find` strings
# short and structural so they survive light refactoring of the reference.
CATALOGUES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "file_hosting": {
        "inclusive ttl (<= instead of <)": [
            ("timestamp < expiry", "timestamp <= expiry"),
        ],
        "no name tie-break": [
            ("(-live[name], name)", "(-live[name],)"),
            ("(-size, name)", "(-size,)"),
        ],
        "forgot the top-10 cap": [
            ("[:10]", "[:]"),
        ],
        "prefix matches anywhere in the name": [
            ("name.startswith(prefix)", "prefix in name"),
        ],
        "re-sorting instead of one compound key": [
            (
                "matches.sort(key=lambda name: (-live[name], name))",
                "matches.sort()\n        matches.sort(reverse=True, key=lambda name: (live[name], name))",
            ),
        ],
        # Needs all three edits: the replay filter, the aliveness test and the
        # live-set test each enforce the lower bound independently, so mutating
        # only one of them is silently unobservable.
        "a file exists at timestamps before its own upload": [
            ("if start <= timestamp:", "if True:"),
            ("if start <= timestamp < expiry:", "if timestamp < expiry:"),
            (
                "return entry if start <= timestamp < expiry else None",
                "return entry if timestamp < expiry else None",
            ),
        ],
        "copy gets a fresh ttl instead of inheriting the source's": [
            ("size, _start, expiry = entry", "size, _start, expiry = entry\n        expiry = INF"),
        ],
        "truthiness on size (a 0-byte file reads as absent)": [
            ("is None else entry[0]", "is None or not entry[0] else entry[0]"),
        ],
        "rollback is a no-op": [
            ("self.log = [entry for entry in self.log if entry[0] <= timestamp]", "pass"),
        ],
        "rollback keeps only one snapshot": [
            (
                "self.log = [entry for entry in self.log if entry[0] <= timestamp]",
                "self.log = self.log[:1] if timestamp else self.log",
            ),
        ],
        "rollback forgets expiry times": [
            (
                "self.log = [entry for entry in self.log if entry[0] <= timestamp]",
                "self.log = [(a, b, c, INF) for (a, b, c, d) in self.log if a <= timestamp]",
            ),
        ],
        "duplicate upload does not raise": [
            ('raise RuntimeError(f"{file_name} already exists")', "return"),
        ],
        "copy from a missing source does not raise": [
            ('raise RuntimeError(f"{file_from} does not exist")', "return"),
        ],
        "copy refuses to overwrite an existing destination": [
            (
                "self.log.append((timestamp, file_to, size, expiry))",
                "if self._entry_at(timestamp, file_to) is None:\n"
                "            self.log.append((timestamp, file_to, size, expiry))",
            ),
        ],
    },
    "in_memory_db": {
        "inclusive ttl (<= instead of <)": [
            ("timestamp >= entry[1]", "timestamp > entry[1]"),
            ("timestamp < expiry and", "timestamp <= expiry and"),
        ],
        "`or None` on get, so an empty-string value reads as absent": [
            ("return entry[0]", "return entry[0] or None"),
        ],
        "scan does not sort by field name": [
            ("return sorted(", "return list("),
        ],
        "prefix matches anywhere in the field, not just the start": [
            ("field.startswith(prefix)", "prefix in field"),
        ],
        "setting an existing field keeps its old expiry": [
            (
                "self.data.setdefault(key, {})[field] = (value, timestamp + ttl)",
                "_r = self.data.setdefault(key, {})\n"
                "        _r[field] = (value, _r[field][1] if field in _r else timestamp + ttl)",
            ),
        ],
        "delete succeeds on an already-expired field": [
            (
                "if entry is None or timestamp >= entry[1]:\n"
                "            return False\n"
                "        del self.data[key][field]",
                "if entry is None:\n"
                "            return False\n"
                "        del self.data[key][field]",
            ),
        ],
        "backup counts fields instead of records": [
            ("return len(snapshot)", "return sum(len(r) for r in snapshot.values())"),
        ],
        "backup counts empty records": [
            ("if live:\n                snapshot[key] = live", "snapshot[key] = live"),
        ],
        "backup includes expired fields": [
            ("                if timestamp < expiry\n            }", "            }"),
        ],
        "restore does not re-anchor remaining lifetimes": [
            ("(value, expiry - timestamp)", "(value, expiry)"),
            ("(value, timestamp + remaining)", "(value, remaining)"),
        ],
        "restore merges instead of replacing": [
            (
                "_, snapshot = max(eligible, key=lambda b: b[0])",
                "_, snapshot = max(eligible, key=lambda b: b[0])\n        _keep = dict(self.data)",
            ),
            (
                "            for key, record in copy.deepcopy(snapshot).items()\n        }",
                "            for key, record in copy.deepcopy(snapshot).items()\n        }\n"
                "        self.data = {**_keep, **self.data}",
            ),
        ],
        "only the most recent backup is kept": [
            (
                "self.backups.append((timestamp, copy.deepcopy(snapshot)))",
                "self.backups = [(timestamp, copy.deepcopy(snapshot))]",
            ),
        ],
        "the backup aliases live state instead of copying it": [
            (
                "self.backups.append((timestamp, copy.deepcopy(snapshot)))",
                "self.backups.append((timestamp, {k: v for k, v in self.data.items() if v}))",
            ),
        ],
        "restore with no eligible backup clears the database": [
            (
                "        if not eligible:\n            return",
                "        if not eligible:\n            self.data = {}\n            return",
            ),
        ],
        "separate store for the level-1 methods": [
            (
                "return self.set_at(key, field, value, 0)",
                "self.plain = getattr(self, 'plain', {})\n"
                "        self.plain.setdefault(key, {})[field] = value",
            ),
        ],
    },
    "cloud_storage": {
        "adding an existing name overwrites instead of failing": [
            ("if name in self.files:\n            return False", "if False:\n            return False"),
        ],
        # Several entries carry a second anchor: references in this family differ
        # in whether they keep a `_used` helper or sum the owned files inline, and
        # an edit that matches neither reports SKIP, which reads like a suite hole
        # when it is only a shape mismatch.
        "add_file_by returns used capacity instead of remaining": [
            (
                "self.files[name] = (size, user_id)\n        return self._remaining(user_id)",
                "self.files[name] = (size, user_id)\n        return self._used(user_id)",
            ),
            (
                "self.files[name] = (size, user_id)\n        # REMAINING capacity",
                "self.files[name] = (size, user_id)\n"
                "        return sum(self._owned(user_id).values())\n"
                "        # REMAINING capacity",
            ),
        ],
        "an exact fit is rejected": [
            ("if size > self._remaining(user_id)", "if size >= self._remaining(user_id)"),
        ],
        "capacity is never checked": [
            (
                "if size > self._remaining(user_id):\n            return None",
                "if False:\n            return None",
            ),
        ],
        "delete returns a flag instead of the size": [
            (
                "entry = self.files.pop(name, None)\n        return None if entry is None else entry[0]",
                "entry = self.files.pop(name, None)\n        return entry is not None",
            ),
            (
                "        return None if entry is None else entry[0]\n\n    # ====",
                "        return entry is not None\n\n    # ====",
            ),
        ],
        "no name tie-break in the ranked query": [
            ("(-self.files[name][0], name)", "(-self.files[name][0],)"),
        ],
        "forgot the n cap": [
            ("return matches[:n]", "return matches"),
        ],
        "prefix matches anywhere in the name": [
            ("name.startswith(prefix)", "prefix in name"),
        ],
        "duplicate add_user overwrites the capacity": [
            ("if user_id in self.users:\n            return False", "if False:\n            return False"),
        ],
        "merge keeps only the first user's capacity": [
            ("self.users[user_id_1] += self.users[user_id_2]", "self.users[user_id_1] += 0"),
        ],
        "merge does not move the files": [
            ("                self.files[name] = (size, user_id_1)", "                pass"),
            ("            self.files[name] = (size, user_id_1)", "            pass"),
        ],
        "merge leaves the absorbed user alive": [
            ("del self.users[user_id_2]", "_ = user_id_2"),
        ],
        "merging a user into itself succeeds": [
            (
                "if user_id_1 == user_id_2:\n            return None",
                "if False:\n            return None",
            ),
        ],
        "backup saves every file, not just the user's": [
            (
                "snapshot = self._owned(user_id)",
                "snapshot = {n: s for n, (s, o) in self.files.items()}",
            ),
        ],
        "backup saves nothing": [
            ("self.backups[user_id] = dict(snapshot)", "self.backups[user_id] = {}"),
        ],
        "restore does not clear the user's current files first": [
            (
                "for name in list(self._owned(user_id)):\n            del self.files[name]",
                "for name in []:\n            del self.files[name]",
            ),
        ],
        "restore seizes names owned by other users": [
            ("if name in self.files:\n                continue", "if False:\n                continue"),
        ],
        "restore with no backup wipes the user": [
            (
                "if user_id not in self.backups:\n            return 0",
                "if user_id not in self.backups:\n            self.backups[user_id] = {}",
            ),
        ],
        "backup/restore report 0 rather than None for an unknown user": [
            (
                "if user_id not in self.users:\n            return None\n        snapshot",
                "if user_id not in self.users:\n            return 0\n        snapshot",
            ),
        ],
    },
    "banking": {
        "a transfer to yourself is allowed": [
            (
                "if source_id == target_id:\n            return None",
                "if False:\n            return None",
            ),
        ],
        "overdrafts are allowed": [
            (
                "if self.accounts[source_id] < amount:\n            return None",
                "if False:\n            return None",
            ),
        ],
        "transfer reports the target's balance": [
            ("return self.accounts[source_id]", "return self.accounts[target_id]"),
        ],
        "duplicate create_account succeeds": [
            (
                "if account_id in self.accounts:\n            return False",
                "if False:\n            return False",
            ),
        ],
        "outgoing is credited to the target, not the source": [
            ("self.outgoing[source_id] += amount", "self.outgoing[target_id] += amount"),
        ],
        "no account-id tie-break in the ranking": [
            ("(-self.outgoing[a], a)", "(-self.outgoing[a],)"),
        ],
        "forgot the n cap": [
            ("ranked[:n]", "ranked"),
        ],
        "accounts that never spent are left out of the ranking": [
            (
                "ranked = sorted(self.accounts,",
                "ranked = sorted([a for a in self.accounts if self.outgoing[a]],",
            ),
        ],
        "paying does not count towards spending": [
            ("self.outgoing[account_id] += amount", "self.outgoing[account_id] += 0"),
        ],
        "cashback rounds up instead of down": [
            ("amount * 2 // 100", "-(-amount * 2 // 100)"),
        ],
        "cashback lands one millisecond late": [
            ("timestamp + DAY", "timestamp + DAY + 1"),
        ],
        "pending cashback is never applied": [
            ("while True:", "while False:"),
        ],
        "cashback moves the balance without recording history": [
            ("self._record(account_id, when)", "pass"),
        ],
        "payment ids skip numbers": [
            ("self.next_payment += 1", "self.next_payment += 2"),
        ],
        "payment status ignores who owns the payment": [
            (
                "if self.payments.get(payment) != account_id:\n            return None",
                "if payment not in self.payments:\n            return None",
            ),
        ],
        "merge does not combine the spending totals": [
            (
                "self.outgoing[account_id_1] += self.outgoing[account_id_2]",
                "self.outgoing[account_id_1] += 0",
            ),
        ],
        "merging an account into itself succeeds": [
            (
                "if account_id_1 == account_id_2:\n            return False",
                "if False:\n            return False",
            ),
        ],
        "merge leaves the absorbed account alive": [
            ("del self.accounts[account_id_2]", "_ = account_id_2"),
        ],
        "merge drops the absorbed account's pending cashback": [
            (
                "(when, account_id_1 if owner == account_id_2 else owner, amount, pid)",
                "(when, owner, amount, pid)",
            ),
        ],
        "get_balance ignores time_at and returns the current balance": [
            (
                "return self._balance_at(account_id, time_at)",
                "return self.accounts[account_id]",
            ),
        ],
        "get_balance excludes changes made exactly at time_at": [
            ("if when <= time_at:", "if when < time_at:"),
        ],
        "get_balance returns 0 for a time before the account existed": [
            ("found = None", "found = 0"),
        ],
        "a transfer is not recorded in the target's history": [
            ("self._record(target_id, timestamp)", "pass"),
        ],
    },
    # The two that matter most here are "permissions keyed by path" and "no loop
    # detection": both are level-1 design decisions that only present as a bug two
    # levels later, which is the whole reason this problem exists.
    "file_system": {
        "LS of a file returns nothing": [
            ("return [parts[-1]] if parts else []", "return []"),
        ],
        "LS does not sort the children": [
            ("return sorted(node.children)", "return list(node.children)"),
        ],
        "truthiness on content, so an empty file reads as absent": [
            (
                "node = self._node(path)\n"
                '        if node is None or node.kind != "file":\n'
                "            return None\n"
                "        return node.content",
                "node = self._node(path)\n"
                '        if node is None or node.kind != "file":\n'
                "            return None\n"
                "        return node.content or None",
            ),
        ],
        "MKDIR creates the intermediate directories": [
            (
                "def mkdir(self, path):\n"
                "        parent, name = self._parent_and_name(path)\n"
                "        if parent is None or name in parent.children:\n"
                "            return False",
                "def mkdir(self, path):\n"
                "        parts = self._split(path)\n"
                "        if not parts:\n"
                "            return False\n"
                "        node = self.root\n"
                "        for _nm in parts[:-1]:\n"
                "            if _nm not in node.children:\n"
                '                node.children[_nm] = Node("dir")\n'
                "            node = node.children[_nm]\n"
                "        parent, name = node, parts[-1]\n"
                "        if name in parent.children:\n"
                "            return False",
            ),
        ],
        "the file count includes directories": [
            (
                "return sum(FileSystem._count_files(c) for c in node.children.values())",
                "return 1 + sum(FileSystem._count_files(c) for c in node.children.values())",
            ),
        ],
        "the file count includes symlinks": [
            (
                'if node.kind == "link":\n            return 0',
                'if node.kind == "link":\n            return 1',
            ),
        ],
        "removing an empty directory is treated as a failure": [
            (
                "        return self._count_files(parent.children.pop(name))\n\n    def find",
                "        if self._count_files(parent.children[name]) == 0:\n"
                "            return 0\n"
                "        return self._count_files(parent.children.pop(name))\n\n    def find",
            ),
        ],
        "the root can be removed": [
            (
                "def rm(self, path):\n        parent, name = self._parent_and_name(path)",
                "def rm(self, path):\n"
                '        if path == "/":\n'
                "            _n = self._count_files(self.root)\n"
                '            self.root = Node("dir")\n'
                "            return _n\n"
                "        parent, name = self._parent_and_name(path)",
            ),
        ],
        "MV overwrites an existing destination": [
            (
                "d_parent, d_name = self._parent_and_name(dest)\n"
                "        if d_parent is None or d_name in d_parent.children:",
                "d_parent, d_name = self._parent_and_name(dest)\n"
                "        if d_parent is None or False:",
            ),
        ],
        "the move cycle check is a string prefix, so /ab counts as inside /a": [
            (
                "if d_real[: len(s_real)] == s_real:",
                "if self._join(d_real).startswith(self._join(s_real)):",
            ),
        ],
        "MV follows a trailing link and moves the target": [
            (
                "s_parent, s_name = self._parent_and_name(source)\n"
                "        if s_parent is None or s_name not in s_parent.children:",
                "_sp = self._resolve_parts(self._split(source))\n"
                "        s_parent = self._lookup_exact(_sp[:-1]) if _sp else None\n"
                "        s_name = _sp[-1] if _sp else None\n"
                "        if s_parent is None or s_name not in s_parent.children:",
            ),
        ],
        "RM follows a trailing link and removes the target": [
            (
                "def rm(self, path):\n"
                "        parent, name = self._parent_and_name(path)\n"
                "        if parent is None or name not in parent.children:",
                "def rm(self, path):\n"
                "        _rp = self._resolve_parts(self._split(path))\n"
                "        parent = self._lookup_exact(_rp[:-1]) if _rp else None\n"
                "        name = _rp[-1] if _rp else None\n"
                "        if parent is None or name not in parent.children:",
            ),
        ],
        "READ_FILE does not follow a trailing link": [
            (
                "def read_file(self, path):\n        node = self._node(path)",
                "def read_file(self, path):\n"
                "        _p, _n = self._parent_and_name(path)\n"
                "        node = None if _p is None else _p.children.get(_n)",
            ),
        ],
        "FIND excludes the path it started from": [
            (
                "found = []\n"
                "        self._walk(node, parts, name, found)\n"
                "        return sorted(found)",
                "found = []\n"
                '        if node.kind == "dir":\n'
                "            for _cn, _c in node.children.items():\n"
                "                self._walk(_c, parts + [_cn], name, found)\n"
                "        return sorted(found)",
            ),
        ],
        "FIND matches files only": [
            (
                "if parts and parts[-1] == name:",
                'if parts and parts[-1] == name and node.kind == "file":',
            ),
        ],
        "FIND does not sort its results": [
            ("        return sorted(found)", "        return found"),
        ],
        "FIND walks through symlinks": [
            (
                '        if node.kind == "dir":\n'
                "            for child_name, child in node.children.items():\n"
                "                self._walk(child, parts + [child_name], name, found)",
                '        if node.kind == "link":\n'
                "            _t = self._resolve_parts(self._split(node.target))\n"
                "            _tn = None if _t is None else self._lookup_exact(_t)\n"
                '            if _tn is not None and _tn.kind == "dir":\n'
                "                for _cn, _c in _tn.children.items():\n"
                "                    self._walk(_c, parts + [_cn], name, found)\n"
                '        if node.kind == "dir":\n'
                "            for child_name, child in node.children.items():\n"
                "                self._walk(child, parts + [child_name], name, found)",
            ),
        ],
        "no loop detection, so a link cycle spins forever": [
            (
                "if hops > MAX_HOPS:\n                return None",
                "if False:\n                return None",
            ),
        ],
        "permissions keyed by path, so a move orphans every grant": [
            (
                "for entry in reversed(chain):\n"
                "            if user in entry.perms:\n"
                "                return entry.perms[user]\n"
                '        return ""',
                '_table = getattr(self, "_table", {})\n'
                "        for _i in range(len(real_parts), -1, -1):\n"
                "            _k = (self._join(real_parts[:_i]), user)\n"
                "            if _k in _table:\n"
                "                return _table[_k]\n"
                '        return ""',
            ),
            (
                "node.perms[user] = perms\n        return True",
                'if not hasattr(self, "_table"):\n'
                "            self._table = {}\n"
                "        self._table[(self._join(parts), user)] = perms\n"
                "        return True",
            ),
        ],
        "an explicit empty grant is treated as no grant": [
            (
                "if user in entry.perms:\n                return entry.perms[user]",
                "if entry.perms.get(user):\n                return entry.perms[user]",
            ),
        ],
        "permissions are the union of every ancestor's grant": [
            (
                "for entry in reversed(chain):\n"
                "            if user in entry.perms:\n"
                "                return entry.perms[user]\n"
                '        return ""',
                "_out = set()\n"
                "        for entry in chain:\n"
                "            if user in entry.perms:\n"
                "                _out |= set(entry.perms[user])\n"
                '        return "".join(sorted(_out))',
            ),
        ],
        "the shallowest grant wins instead of the deepest": [
            ("for entry in reversed(chain):", "for entry in chain:"),
        ],
        "grants are stamped eagerly and never inherited at lookup time": [
            (
                "for entry in reversed(chain):\n"
                "            if user in entry.perms:\n"
                "                return entry.perms[user]\n"
                '        return ""',
                'return chain[-1].perms.get(user, "")',
            ),
            (
                "node.perms[user] = perms\n        return True",
                "_stack = [node]\n"
                "        while _stack:\n"
                "            _n = _stack.pop()\n"
                "            _n.perms[user] = perms\n"
                '            if _n.kind == "dir":\n'
                "                _stack.extend(_n.children.values())\n"
                "        return True",
            ),
        ],
        "RM_AS removes whatever it is allowed to instead of nothing": [
            (
                "if not self._all_writable(node, real, user):\n"
                "            return 0\n"
                "        return self._count_files(parent.children.pop(name))",
                "if not self._all_writable(node, real, user):\n"
                "            _removed = 0\n"
                '            if node.kind == "dir":\n'
                "                for _cn in list(node.children):\n"
                "                    _removed += self.rm_as(user, self._join(real + [_cn]))\n"
                "            return _removed\n"
                "        return self._count_files(parent.children.pop(name))",
            ),
        ],
        "RM_AS does not check the directories it removes": [
            (
                "def _all_writable(self, node, parts, user):\n"
                '        if "w" not in self._perm(parts, user):',
                "def _all_writable(self, node, parts, user):\n"
                '        if node.kind != "dir" and "w" not in self._perm(parts, user):',
            ),
        ],
        "CREATE_FILE_AS checks read on the parent instead of write": [
            (
                'if "w" not in self._perm(parent_parts, user):',
                'if "r" not in self._perm(parent_parts, user):',
            ),
        ],
        "CHMOD does not follow a trailing link": [
            (
                "def chmod(self, path, user, perms):\n"
                "        parts = self._resolve_parts(self._split(path))",
                "def chmod(self, path, user, perms):\n"
                "        parts = self._real_parts(path)",
            ),
        ],
    },
}


def run_mutant(problem_key: str, source: str) -> list[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        handle.write(source)
        path = handle.name
    try:
        result = subprocess.run(
            [sys.executable, "-m", "harness", "validate", problem_key, "--against", path],
            capture_output=True,
            text=True,
            cwd=REPO,
            env=dict(os.environ, NO_COLOR="1"),
        )
        # Match the runner's finding lines ("diff  <case_id> ..."), NOT the header
        # line ("differential against <path>"). Matching on the "diff" prefix alone
        # counted the header as a finding and reported every mutant as caught --
        # a checker that always says yes is worse than no checker.
        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip().startswith("diff ")
        ]
    finally:
        os.unlink(path)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    problem_key, reference = argv
    catalogue = CATALOGUES.get(problem_key)
    if not catalogue:
        print(f"no mutation catalogue for {problem_key!r}. Known: {', '.join(CATALOGUES)}")
        return 2

    original = pathlib.Path(reference).read_text()
    missed: list[str] = []

    for label, edits in catalogue.items():
        mutated, applied = original, 0
        for find, replace in edits:
            if find in mutated:
                mutated = mutated.replace(find, replace)
                applied += 1
        if applied == 0:
            print(f"  SKIP    {label}  (no edit matched this reference)")
            missed.append(label)
            continue
        caught = run_mutant(problem_key, mutated)
        if caught:
            ids = sorted({line.split()[1] for line in caught})
            print(f"  caught  {label}")
            print(f"          by {len(ids)}: {', '.join(ids[:3])}{' ...' if len(ids) > 3 else ''}")
        else:
            print(f"  MISSED  {label}")
            missed.append(label)

    print()
    print(f"{len(catalogue) - len(missed)}/{len(catalogue)} mutants caught")
    if missed:
        print("\nA missed mutant means the suite would pass code containing that bug.")
        print("Add a case that distinguishes it, then re-run.")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
