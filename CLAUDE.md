# Repo guide

A practice rig for the CodeSignal Industry Coding Framework assessment: 90 minutes,
one problem, four progressive levels. `./pfs` is the whole interface. Python 3.10+,
**stdlib only** — adding a dependency would teach a habit the real assessment rejects.

## Before you help with anything, check the mode

```bash
./pfs status
```

**If a session is live, a human is being measured.** Do not give them algorithms,
data structures, code, edits to their solution file, what a failing case expects, or
anything from `DECISIONS.md` or `problems/*/tests.py`. Python syntax and
standard-library reference *is* allowed — the real assessment permits exactly that.
Point them at `./pfs dispute` if they think a case is wrong, and at `./pfs finish`
when they want to talk. The `icf-coach` agent encodes this properly.

Once `./pfs finish` has run, everything is open: walkthroughs, solutions, teaching.

## Layout

```
pfs                  entry point; `./pfs ui` opens the browser IDE
harness/             the rig (model, runner, session clock, reporting, CLI)
webui/               local CodeSignal-style IDE: server.py (stdlib http.server),
                     index.html, markdown.py, static/ (vendored CodeMirror)
problems/<key>/      problem.py, tests.py, statement/level1..4.md, CONTRACT.md, DECISIONS.md
tools/               mutation_check.py
tests/               run_all.sh, api_test.py (backend), ui.test.js (real Chrome)
docs/                ASSESSMENT_BRIEF.md (what the test is), PLAYBOOK.md (how to attack it)
workspace/           the candidate's code — gitignored
sessions/            append-only event logs — gitignored
solutions/           intentionally empty; see solutions/README.md
```

## The rules that matter

**Three levels of disclosure per problem, and content must not drift upward.**
`statement/` is terse and deliberately under-specified, like the real thing.
`CONTRACT.md` gives types and return shapes and is available during an attempt.
`DECISIONS.md` is the answer key and is locked during an attempt. Making the
statement clearer to be helpful removes the skill being tested.

**Visible cases are the disclosure channel.** `visible=True` cases are auto-rendered
into the statement as worked examples, so they cannot drift from the grader. Every
ambiguous rule must be demonstrated by one — a rule only discoverable from a hidden
case is unfair.

**Run `tests/run_all.sh` after touching `harness/` or `webui/`.** UI changes especially:
every UI bug this rig has shipped was a geometry bug (a control outside the viewport, a
pane collapsed to zero height), invisible to any test that only checks for presence.

**Never ship a test case that has not passed both gates.** Differential
(`./pfs validate <key> --against <oracle outside the repo>`) and mutation
(`python3 tools/mutation_check.py <key> <oracle>`). Full method in
`.claude/skills/harness-engineering/SKILL.md`.

**No reference solutions in the repo.** Oracles live outside it and get deleted.
Once a human has solved a problem, their solution goes in `solutions/<key>.py` and
`./pfs validate` picks it up automatically.

**Level weights sum to 600.** That is the real assessment's scale; `validate`
enforces it.

## Skills

- `.claude/skills/harness-engineering/` — adding problems, authoring cases, the
  verification gates, runner internals. Read before touching `harness/` or
  `problems/`.
- `.claude/skills/loop-engineering/` — the practice loop and how to read
  `./pfs stats`. Read before advising on what to practise next.

## Style

Comments explain why, never what. Plain prose, no filler. Match the surrounding
code — `harness/` uses dataclasses, `from __future__ import annotations`, and keeps
terminal rendering out of logic modules.
