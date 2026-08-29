# Build state

Working notes for whoever picks this up — including a future Claude session that has
lost all context. **Update this file as work proceeds.** Everything below is checkable
by running the commands given.

Last updated: 2026-08-09.

## The constraint that shapes everything

Jayden is preparing for a real, proctored CodeSignal Industry Coding Framework
assessment. He sits the practice tests himself; the walkthrough happens *afterwards*.

**No reference solutions in this repo.** Not in `solutions/`, not in `problems/`, not
anywhere. Verification oracles are written outside the repo and deleted after use. See
`solutions/README.md` and `.claude/skills/harness-engineering/SKILL.md`.

## Status: complete and verified

**Harness** (`harness/`, `pfs`) — stdlib only, Python 3.10+, no dependencies.

| module | what it does |
| --- | --- |
| `model.py` `expect.py` | Problem/Level/Method/Case/Op; three-way comparison (exact / lenient / mismatch); `Exactly()` to disable leniency where `""` is a real value |
| `runner.py` | fresh instance per case, per-op timeout, distinguishes stub vs missing method vs wrong answer |
| `session.py` `report.py` | 90-minute clock, level unlocking, append-only event log, debrief + cross-session stats |
| `render.py` | failure rendering; **auto-renders `visible=True` cases into the statement as worked examples**, so examples cannot drift from the grader |
| `scaffold.py` | starter file generated from `Method.signature` |
| `validate.py` | structural + differential self-check |
| `cli.py` | `list start spec contract stubs test submit status finish report stats decisions validate dispute` |

Verified end to end: level gating, unlock-on-clear, locked `spec`/`decisions` during a
live session, stub detection, examples rendering, score estimate, dispute logging,
debrief, cross-session stats.

**Problem bank — all five authored and through both gates.**

| key | cases | differential | mutants | notes |
| --- | --- | --- | --- | --- |
| `file_hosting` | 58 | all agree | 14/14 | CodeSignal's published sample, wording verbatim |
| `cloud_storage` | 46 | all agree | 19/19 | users, capacity, merge, collision-aware restore |
| `in_memory_db` | 50 | all agree | 15/15 | timestamp is the LAST argument; restore re-anchors TTLs |
| `banking` | 41 | all agree | 23/23 | deferred cashback, historical balances, merge |
| `file_system` | 60 | all agree | 27/27 | a real tree; permissions inherited downwards, then symlinks |

Deliberate variation across the bank so it cannot be memorised as one pattern:
timestamp-first vs timestamp-last, raising vs returning `None` on failure, and five
different level-4 turns (rollback / re-anchored restore / collision-aware restore /
merge / symbolic links).

**`file_system` is the difficulty ceiling and exists for one reason.** The other four
are flat `name -> value` maps, so a candidate cannot make a *wrong* level-1 design
decision — which means the bank could not exercise the one pressure the real
progressive format is built around ("your level-1 design constrains level 4"). This one
can be done at level 1 with `dict[path]` and then charges for it twice: `DECISIONS.md`
#8 (permissions keyed by path are orphaned by the first `MV`) and #12/#14 (link
resolution is a traversal step, not a string rewrite). Both have dedicated mutants —
"permissions keyed by path, so a move orphans every grant" is caught by exactly one
case, deliberately.

Calibration note (2026-08-14): sourced from the Meta/Coinbase/Anthropic progressive-
workspace re-skins, whose reported escalation is create-read → paths → permissions →
symlinks, plus LeetCode 588/1166 for the tree shape. `LS` of a file returning its own
name is 588's behaviour and is inherited on purpose.

**`webui/`** — a local CodeSignal-style IDE, `./pfs ui`. Stdlib `http.server` plus a
vendored CodeMirror 5 in `webui/static/` (checked in so it works offline). Single
threaded on purpose: the runner arms `SIGALRM` per operation, which needs the main
thread.

It shares the session file, workspace file and runner with the CLI — you can start in
the browser and finish in the terminal. **The no-leak rules are enforced server-side**,
not in the front end: hidden cases' operations, expected values and actual values are
never serialised; locked levels' statements are never sent; `/api/decisions` returns 403
while a session is live. Verified by inspecting the JSON, not by reading the UI code.

**`.claude/`** — `agents/icf-coach.md` (proctor, debrief and walkthrough modes, with the
no-leak rule), `skills/loop-engineering/`, `skills/harness-engineering/`.

**`docs/`** — `ASSESSMENT_BRIEF.md` (what the test is; official CodeSignal quotes with
confidence markers), `PLAYBOOK.md` (how to attack it; headed "read after your first cold
attempt"), `PROBLEM_BRIEFS.md` (research provenance for the four reconstructed problems).

**`tools/mutation_check.py`** — mutation catalogues for all five problems. Dormant until
a reference implementation exists to mutate; run it whenever a suite changes.

## Exam mode (`--blind`)

`./pfs start <key> --blind`, or the checkbox on the picker. Sets `Session.blind`, and
while that session is live a failure reports an **opaque test number**, its outcome, the
candidate's own `print()` output and their own traceback — nothing else. No case id, no
tags, no operation shape, no expected value, and no "this was only a type" hint. It stops
binding the moment `./pfs finish` runs, because reading the cases you could not see is
the point of the debrief.

Why it exists: the default feedback in this rig (case names, tags, operation shapes) is
strictly more than the real assessment gives, so practising with it trains a debugging
reflex that will not be available on the day.

Touch points, if this needs changing: `Session.blind`, `render._render_blind` /
`render.blind_detail`, `cli.cmd_test`'s `blind` flag, `server._blind_case_payload`, and
`index.html`'s `#blind` checkbox plus the `c.blind` branches in `renderResults`/`termHtml`.
`harness/examples.py` no longer ships case ids to the browser — that was found by the new
backend check, not by review.

## Test suite

`tests/run_all.sh` — structural (5 problems) + backend (60 checks) + browser (44 checks
in real Chrome). All green as of 2026-08-14. It backs up `sessions/` and `workspace/` and
restores them, so it is safe to run during a live attempt.

The browser layer asserts on **element geometry**, not just presence. Every UI bug this
rig shipped was invisible to a content-only test: a Run button pushed outside a narrow
viewport, an editor collapsed to zero height by a grid row that grew with its results, a
dead backend that looked exactly like a frozen page.

Full four-level progression verified end to end for `file_hosting` (13 → 29 → 44 → 58
cases, 100 → 240 → 420 → 600 score, all four unlocks, debrief, answer key) and for
`file_system` (13 → 30 → 45 → 60 cases, same score curve). The drivers and their
solutions live outside the repo and are deleted after use — see `solutions/README.md`.

## Bugs found and fixed on 2026-08-09

A four-lens adversarial review plus the new test suites found these. All fixed and
regression-tested unless marked.

**Invariant 1 — locked levels must stay locked**
- `./pfs spec --all`, `contract --all`, `stubs --level N`, `test --level N`, `test --reveal`
  all bypassed the lock during a live attempt. The web UI gated correctly; the CLI did not.
  Now all refuse while the clock runs (`--force` overrides), and reopen after `finish`.
- `harness/contract.py` used a boolean, so a nested `<!-- level: 1 -->` inside a locked
  block re-opened it and everything after the inner close leaked. Now a stack.
- The starter file's docstring printed all four levels (`Problem.blurb`); so did the
  problem picker. Both now use `Problem.opening`.
- `cloud_storage` described level 4's backups to a level-3 candidate; `file_hosting`
  described level-2 search in its level-1 contract. Both re-marked.

**Invariant 3 / 4 — the clock**
- At 90:00 the answer key opened *while runs still unlocked levels*. Expiry now finishes
  the session everywhere, on both surfaces, and the UI announces TIME UP.

**Invariant 5 — never lose work**
- `+ stubs` appended a level's stubs over methods the file already defined. Python keeps
  the last definition, so a working solution silently started raising `NotImplementedError`.
  Now refused, and the button is disabled when there is nothing to add.
- `resume` archived nothing and then overwrote the file anyway — the opposite of its label.
- `/api/save` and `/api/run` defaulted a missing `code` field to `""`, truncating the
  solution. Now a 400.
- `scaffold.archive` used a second-resolution stamp with `rename`, so two retakes in one
  second destroyed the first. Session ids had the same collision. Both now uniquified.

**Measurement integrity**
- `level_cleared_at` was re-stamped by every later passing run, so re-running after
  clearing level 4 reported it cleared 25 minutes late and "over budget". Stamped once now.
- `./pfs test <other-problem>` logged runs into, and unlocked levels in, the *live*
  session for a different problem. Now only records when the problem matches.

**Robustness**
- `do_GET` had no exception handler, so an unreadable workspace file returned a closed
  connection, which the UI reported as "the server is not running" — a false diagnosis the
  user could not act on.
- Syntax errors dumped a harness traceback; now a file/line/caret pointing at their code.
- `webui/markdown.py` split table rows on bare `|`, mangling every signature containing
  `int \| None`.

**Known and not fixed** (recorded rather than silently left):
- Two browser tabs, or a long run racing a `finish`, can clobber the session file
  (last-writer-wins). Single-tab use is unaffected.
- The browser autosave can overwrite edits made in an external editor; the two front ends
  share one file with no version check.
- No CSRF protection on the local API. It binds to 127.0.0.1 only.
- Hidden-case rows print their tag list, which can reconstruct the masked case id.

## Two bugs the mutation gate caught, worth remembering

1. **`mutation_check.py` matched `startswith("diff")`**, which also matched the
   `differential against ...` header line — so every mutant was reported as caught. A
   checker that always says yes is worse than no checker. Now matches `"diff "`.
2. Once fixed, it found two genuine holes: `cloud_storage` never tested that a prefix
   must match at the *start* of a name, and `banking`'s tie-break cases created accounts
   in already-alphabetical order, so Python's stable sort passed them without any
   tie-break at all. Both fixed with new cases.

## Open question, recorded rather than guessed at

CodeSignal's KB groups the ICA under "single function questions", which suggests the real
starter may be **one dispatch function taking a list of query lists**
(`solution(queries) -> list`). The framework brief instead speaks of "methods" and "do not
change the existing method signatures", suggesting **a class of stub methods**. No page
found shows the live ICA starter.

This rig assumes the class-of-methods shape. If the dispatch shape turns out to be what
Jayden faces, the fix is small and localised: test cases are already declarative op
sequences, so only `runner.py`'s dispatch (`getattr(instance, name)`) and `scaffold.py`
would need an alternative mode. **Do not rewrite the problem bank for it.**

## Verifying the current state

```bash
./pfs list                 # five problems, 255 cases
./pfs validate             # structural check of every problem
./pfs start file_hosting   # end-to-end smoke test
```

To re-run the differential and mutation gates you need a reference implementation, which
the repo deliberately does not ship. Write one outside the repo (or use a solution from a
walkthrough, in `solutions/<key>.py`), then:

```bash
./pfs validate <key> --against <path>
python3 tools/mutation_check.py <key> <path>
```

## Notes for a fresh session

- `support.codesignal.com` is behind Cloudflare; WebFetch returns 403. Use the
  `r.jina.ai` text proxy.
- `curl` the raw GitHub files for problem statements — WebFetch summarises instead of
  reproducing verbatim.
- `/usr/bin/python3` on this machine needs Xcode CLT and fails; use
  `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`, or just `./pfs`.
- Background workflows are expensive and hit a session usage limit on 2026-08-08, losing
  a three-problem authoring run entirely. The problems were then authored inline, which
  was cheaper and produced better-verified results. Prefer inline.
