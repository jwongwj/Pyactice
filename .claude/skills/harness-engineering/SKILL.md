---
name: harness-engineering
description: Extend and maintain the pfs practice harness - add a problem to the bank, author test cases, verify expected values against an oracle, mutation-test a suite, or change the runner/CLI. Use when adding or fixing a problem, when a test case is disputed, or when working on anything under harness/, problems/ or tools/.
---

# Harness engineering

The harness exists to make a practice attempt tell the truth. Everything here
follows from that: a suite that passes broken code, or fails correct code, is worse
than no practice at all because it trains the wrong reflex.

## Repo map

```
pfs                     entry point; ./pfs <cmd>
harness/
  model.py              Problem, Level, Method, Case, Op  + structural validation
  expect.py             ANY / Raises / Unordered / OneOf and the comparison engine
  runner.py             executes cases; per-op timeout; missing-method and stub detection
  loader.py             imports problems/<key>/problem.py; tolerates broken siblings
  session.py            the 90-minute clock, unlocking, append-only event log
  report.py             debrief + cross-session analytics (this is the loop's telemetry)
  render.py             terminal output, failure rendering, auto-rendered examples
  scaffold.py           starter-file generation from Method signatures
  validate.py           structural + differential self-checks
  cli.py                command surface
problems/<key>/
  problem.py            Problem definition (methods, levels, tags, metadata)
  tests.py              the cases
  statement/level1..4.md  CUMULATIVE statements, in the real assessment's voice
  CONTRACT.md           types/returns - available to the candidate DURING an attempt
  DECISIONS.md          the answer key for every ambiguity - locked during an attempt
tools/mutation_check.py catalogue of classic candidate bugs per problem
solutions/              deliberately empty; see solutions/README.md
```

## The three-document split

This is the design decision everything else hangs off. Each problem says the same
thing three times, at three different levels of disclosure:

| File | Contains | Available during an attempt? |
| --- | --- | --- |
| `statement/levelN.md` | the question, in the real assessment's terse and slightly under-specified voice | yes |
| `CONTRACT.md` | types, return shapes, error convention, scale | yes — it stands in for the starter code's type hints |
| `DECISIONS.md` | every ambiguity, the chosen reading, the alternatives, the failure modes | no — `./pfs decisions` refuses while a session is live |

Do not migrate content up this table to be helpful. Over-specifying the statement
removes the exact skill the assessment tests, which is committing to a defensible
reading under time pressure and adapting when a test disagrees.

## Adding a problem

1. `mkdir -p problems/<key>/statement && touch problems/<key>/__init__.py`
2. Write `problem.py`: `Method` per operation, `Level` per level, `tag_glossary`,
   and a `PROBLEM = Problem(...)`. **Level weights must sum to 600** — that is the
   real assessment's scale and `validate` enforces it.
3. Write cumulative statements. `level3.md` contains levels 1–3.
4. Write `tests.py`, then `CONTRACT.md`, then `DECISIONS.md`.
5. Run the verification gate below. It is not optional.
6. Add the problem's mutation catalogue to `tools/mutation_check.py`.

`Method(display="FILE_UPLOAD", ...)` maps automatically to the Python method
`file_upload`. Signatures are emitted verbatim into the starter file, so they are
simultaneously the scaffold and the type contract — get them exactly right.

## Authoring cases

```python
case(
    "l2_ties_break_by_name_ascending",
    2,
    [
        op("FILE_UPLOAD", "/b.txt", 50),
        op("FILE_SEARCH", "/", ret=["/c.txt", "/a.txt", "/b.txt"]),
    ],
    tags=["search", "ordering", "tie-break"],
    visible=True,
    doc="Equal sizes are ordered by name, ascending.",
)
```

- `ret` defaults to `ANY`, so void operations need no annotation. Use `raises=True`
  for operations that must throw.
- **One idea per case.** A failing case should point at one rule. Long cases turn a
  wrong answer into a debugging session.
- **`visible=True` cases are the disclosure channel.** They are auto-rendered into
  the statement as worked examples by `render.render_examples`, which is why the
  examples can never drift from the grader. Every genuinely ambiguous rule must have
  one. If a rule is only discoverable from a hidden case, the problem is unfair —
  the candidate cannot deduce it and cannot see it.
- **Tag everything.** Tags are the loop's curriculum; an untagged case teaches
  nothing after the session. Every tag must appear in `tag_glossary`.
- **Every level above 1 needs a `regression` case** that re-runs earlier operations.
  Breaking level 1 while building level 3 is the most common real failure, and a
  suite that cannot catch it is not simulating the assessment.
- Any expectation not obvious from the statement carries a `why=`, which is printed
  on failure and in the rendered examples.

Target roughly 12–16 cases per level: 3–4 visible, the rest hidden.

## The verification gate

Hand-authored expected values are guesses until something executes them. Two gates,
in order.

**Gate 1 — differential.** Write a reference implementation *outside the repo* (the
session scratchpad), naively and obviously correct — full replay, recompute from
scratch, no cleverness. Then:

```bash
./pfs validate <key> --against /path/outside/repo/oracle.py
```

Iterate to "every case agrees with the reference". When the oracle and a case
disagree, decide which is wrong **from the statement**, not by making the test match
the oracle. Roughly a third of the time the oracle is the one that is wrong, and
that is exactly the ambiguity that belongs in `DECISIONS.md`.

**Gate 2 — mutation.** Gate 1 proves the suite is consistent with correct code. It
does not prove the suite is useful; a suite of trivial cases is also consistent with
correct code. So break the reference the way real candidates break it and confirm
the suite notices.

For an **industry problem**, from the hand-written catalogue of classic bugs:

```bash
python3 tools/mutation_check.py <key> /path/outside/repo/oracle.py
```

For a **drill unit**, generated mechanically — a hundred one-function drills cannot each
carry a hand-written catalogue, and do not need one, because at that size the classic
bugs *are* the mechanical ones:

```bash
python3 tools/drill_mutation.py <unit-key> /path/outside/repo/oracle.py
```

It applies one mutation at a time, scoped to the drill's own function: comparison swaps,
integer literals off by one, guards forced true and false, `and`/`or` flipped, a dropped
unary minus, boolean keywords inverted. Two things about reading its output:

- **A survivor is not automatically a defect.** It means either the cases are too weak or
  the mutation was semantically null. `while i < j` versus `i <= j` in a two-pointer swap
  is null — the middle element swaps with itself. **Do not judge by reading.** Pass
  `--triage N` and the tool fuzzes each survivor against the oracle and prints the input
  where they disagree, ready to become a case. On the first eight units that turned 44
  survivors-to-eyeball into 11 real gaps, every one with a counterexample.

- **Triage says when it cannot help.** A `Node`, a tree or any custom argument shape is
  one the generator cannot build, and it reports those survivors as **UNJUDGED** rather
  than as null. That distinction is load-bearing: before it existed, the linked-list unit
  reported "0 counterexamples" having silently tested nothing but the empty chain, and two
  real gaps were hiding behind it. When you see UNJUDGED, write the differential check by
  hand.

- **Declare the drill's precondition** with `Method.fuzz` or triage will invent inputs the
  drill never promised to handle and call the disagreement a gap. Handing an unsorted list
  to a binary search proves nothing. The vocabulary is `"sorted"`, `"unique"`, `"rotated"`,
  `"nonneg"`, `"positive"`, `"binary"` and `"grid"`; it is never shown to the learner,
  because the statement already says it in prose. Every early "gap" in the binary-search
  and BFS units was a probe outside the domain.

  Sometimes the right response is not a `fuzz` rule but a **decision**: if the fuzzer keeps
  finding inputs the statement does not cover, the statement is under-specified. Union-Find
  gained "a pair naming a member outside the range is ignored" that way, and is a better
  problem for it.

- **A `design` problem is a class**, so its cases are SEQUENCES of operations against one
  instance, and `--triage` fuzzes sequences rather than arguments for them. Two things that
  only apply here: a method whose return the statement leaves open (which member is a
  group's root) must be marked `fuzz=("opaque",)`, or two correct implementations are
  reported as disagreeing; and the mutation gate covers **private helpers** as well as
  declared methods, because that is where the logic usually is — the whole correctness
  argument for the two-stack queue lives in `_shift`.

- **A shared type goes in `Problem.preamble`**, not in each drill. It is emitted into the
  starter file and shown in the statement, and the unit `exec`s that same source to build
  its cases — one definition, so the learner's nodes and the tests' nodes cannot drift.
  Check it against the leak test: the first `Node.__eq__` written this way spelled out,
  character for character, the loop header one of the drills was asking for.
- **"No mutants generated" is a real result, not silence.** A one-liner delegating to
  `sorted(set(...))` has no branch to break, so this gate has nothing to say about it and
  Gate 1 plus its constraint are the whole guard. The tool lists those drills for exactly
  that reason.

A note on where the sequence fuzzer stops: it draws its calls from the problem's own cases,
so it explores histories the author did not write but only from operations the author did.
It found "every case starts with RESET, so nothing tests a freshly built instance" four
times across the twelve build exercises; it will not invent an operation nobody used.

A third check applies to drill units only, and runs in `tests/api_test.py` rather than as
a command: **every oracle must produce zero constraint violations**. A constraint that
fires on its own answer forbids the thing it is teaching. Two have been caught this way,
both by forbidding `subscript` for an idiom that needs indexing.

Every mutant must be caught. A missed mutant is a hole: some real bug would clear
all four levels, and the practice would be lying. Add a case, re-run both gates.

The classic mutations, which generalise across every problem in this family:

- inclusive vs exclusive TTL boundary (`<=` for `<`)
- missing or reversed tie-break; re-sorting instead of one compound key
- forgetting the top-N cap
- truthiness on a numeric field, so `0` reads as absent
- a separate store for the pre-refactor methods (breaks every earlier level)
- shallow copy for a snapshot, so later writes corrupt the backup
- a single snapshot, so a second rollback/restore cannot go further back
- state not restored after a rejected operation (capacity, balance, name)
- a containment check done on strings, so `/ab` counts as inside `/a`
- state keyed by a path or name that a later operation renames, orphaning it
- no cycle detection on a self-referential structure, so the case hangs instead of
  answering (the per-op timeout catches it, which still reads as a diff)

**Delete the oracle when done.** The repo ships with no solutions; that is the point
of `solutions/README.md`.

## Runner behaviour worth knowing

- A fresh instance per case. Never share state between cases.
- `NotImplementedError` reports as *not implemented*, not as a wrong answer, so an
  untouched stub reads as "not done" instead of "broken".
- A missing method is reported by name — forgetting the level-3 `*_at` variants
  otherwise turns the whole run red for no visible reason.
- Per-operation timeout raises a `BaseException` subclass so candidate code cannot
  swallow it with `except Exception`.
- `expect.py` grades three ways, not two: `EXACT`, `LENIENT` (right answer, wrong
  representation — `"100"` for `100`, `[]` for `None`) and `MISMATCH`. Lenient still
  fails, because the real grader fails it, but it is labelled so nobody loses ten
  minutes to a type coercion. Do not "fix" this by making comparison lenient.

## Handling a dispute

`./pfs dispute` appends to `sessions/disputes.jsonl`. During review, for each entry:

1. Re-derive the expected value from the statement alone.
2. If the case is wrong, fix it and re-run **both** gates.
3. If the case is right but the rule was not discoverable, that is still a defect —
   promote a case to `visible=True` or add the rule to `CONTRACT.md`.
4. If the case is right and discoverable, record the reasoning in `DECISIONS.md`
   under the relevant ambiguity. The dispute is evidence that the point is genuinely
   contested, which is worth writing down.

## House style

Stdlib only, no dependencies, Python 3.10-compatible syntax — the real assessment
runs 3.10.6 with no third-party libraries, and the practice environment should not
teach habits the real one rejects. Comments explain why, never what.
