# What this assessment actually is

Research notes behind the harness. Claims are marked **[verified]** (read on a
primary or first-hand source), **[reported]** (consistent across several
second-hand sources) or **[uncertain]**. Sources at the bottom.

## The format

CodeSignal calls it the **Industry Coding Framework** (ICF), sometimes the
"Industry Coding Skills Evaluation Framework". Invitations often describe it as the
"Progressive Filesystem" question type, which is a description of its shape rather
than its subject — the subject is not always a filesystem.

**[verified]** One problem, four levels, 90 minutes. Each level unlocks when your
code passes all tests for the previous one. Every level extends the *same* class:
new operations arrive that assume the ones you already wrote, and you are told not
to change existing method signatures.

**[verified]** CodeSignal's own description of the four levels, from the ICA rules
page:

> - **The first level** requires basic implementation operations while accounting for
>   corner cases.
> - **The second level** introduces data processing functions, such as calculations or
>   exports.
> - **The third level** extends the previous functionality to support new advanced
>   features.
> - **The fourth level** culminates the project with a further extension of
>   functionality. Given the progressive nature of the requirements, candidates must
>   reuse, encapsulate, and refactor earlier code to maintain backward compatibility.

That last sentence is the whole assessment in one line: **backward compatibility is
stated policy, not an accident.** In practice the skeleton comes out as:

| Level | Sample question's title | What it is really testing |
| --- | --- | --- |
| 1 | Initial Design & Basic Functions | can you choose state that will survive level 3 |
| 2 | Data Structures & Data Processing | a ranked/filtered query with a compound sort key |
| 3 | Refactoring & Encapsulation | re-express everything through a new dimension, usually time + TTL |
| 4 | Extending Design & Functionality | history: rollback, backup/restore, or merge |

Recognising the skeleton is most of the preparation. Whatever the cover story —
files, a key-value store, bank accounts — level 3 makes every operation take a
timestamp and adds expiry, and level 4 asks for a previous state back.

**[verified]** Partial credit is awarded per passing test, so running the tests
often is strictly better than saving up a big submission.

## Time

**[verified]** The published per-level guidance sums to more than the time you are
given, and that is deliberate:

| Level | Expected time |
| --- | --- |
| 1 | 10–15 min |
| 2 | 20–30 min |
| 3 | 30–60 min |
| 4 | 30–60 min |

90–165 minutes of work in a 90-minute test. CodeSignal's stated reasoning is that
candidate drop-off rises sharply past two hours, and that *how far you get* is the
measurement — not completion. **Nobody is expected to finish all four levels.**

The practical consequence: level 1 and level 2 are not where you compete. Everyone
clears them. The score separates on whether level 3 cost you 20 minutes or 50, and
that is decided by the state you chose in level 1.

## Scoring

**[verified]** Scores run **200 to 600**. Only test-takers who submit nothing at all
receive 200 — it is the floor, not a failing grade you can land on by trying.

**[verified]** The score is two-tiered:

> **First tier** — base points earned by completing questions within a module. All
> modules are weighted relatively equally, to motivate completing as many questions as
> possible.
>
> **Second tier** — bonus points, awarded **only if you solve 100% of the questions
> within a module**. More bonus is allocated to modules that are harder and that better
> differentiate between candidates.

This has a direct tactical consequence, and it is the single most useful thing on this
page: **finishing a level completely is worth disproportionately more than making
partial progress on two levels.** If level 3 is not going to close, the right move at
minute 70 is to make everything below it fully green rather than to leave two levels
each 80% done. Spread progress collects base points and forfeits every bonus.

**[reported]** Company thresholds are not published by CodeSignal. Community bands put
480+ as competitive and 520–525+ as strong, and "three of four levels complete" is the
usual description of a good result. Treat any specific number as a band, not a bar.

## Retakes — of the real assessment

> This section is about CodeSignal's rules for the real test. **Practice in this repo is
> unlimited**; `./pfs start` as many times as you like.

**[verified]** The ICA can be retaken, but there is a cooldown: **two attempts within a
180-day rolling window, and only if you receive a new invitation from the company.**

Worth knowing before you sit it. There is no free practice run on the real thing — which
is the entire reason this repo exists.

**[reported]** Some employers run automated analysis over submitted code looking for
test-gaming patterns — hard-coded expected outputs, branching on the specific inputs
the tests use. This is worth stating plainly: gaming the tests is not a shortcut
with a downside, it is a disqualification risk that also produces the exact code
signature it is looking for.

**[uncertain]** Whether code quality is scored separately from tests varies by
employer. The level titles ("Refactoring & Encapsulation", "Extending Design &
Functionality") make it clear that extensibility is at least the design intent, and
it costs nothing to write code that reads well.

## Proctoring

**[verified, from the invitation]** Screen, camera and microphone are shared.
Submissions undergo an integrity review.

Allowed: web search for **language documentation and syntax references only** —
Python docs, MDN.

Not allowed: AI tools, external code, books, other people, copying or saving any
part of the assessment, and writing or running code anywhere outside the CodeSignal
editor. That last one matters more than people expect: no scratch REPL, no local
editor, no browser console. If you habitually debug with a side terminal, practise
without one.

## Known problem families

Four families are well attested. The harness ships all four.

| Family | L1 | L2 | L3 | L4 |
| --- | --- | --- | --- | --- |
| File hosting **[verified]** | upload / get / copy | search by prefix, top 10 | timestamps + TTL | rollback to a timestamp |
| Cloud storage with users **[reported]** | add / get / delete | n largest by prefix | users, capacity, merge | backup / restore |
| In-memory key-value DB **[reported]** | set / get / delete | scan, scan by prefix | timestamps + TTL | backup / restore |
| Banking **[reported]** | create / deposit / transfer | top spenders | scheduled payments + cashback | merge accounts, historical balance |

Other families circulate in prep material (package manager, build system, text
editor) but are **[uncertain]** — they appear mainly in third-party guides without
first-hand confirmation, and some read as invented. They are not in the bank.

## The under-specification is the exercise

Published statements are terse and genuinely ambiguous in places. This is not sloppy
question-writing; deciding quickly under ambiguity is part of what is measured.

The clearest documented case is `ROLLBACK` in the file hosting problem. The
statement says "rollback the state of the file storage to the state specified in the
timestamp. All ttls should be recalculated accordingly." It does not say whether
files created *after* that timestamp survive. A widely-used practice repo asserts
that they do, and its own issue tracker carries a complaint that its expectations
are indistinguishable from a `ROLLBACK` that does nothing at all.

The working method under ambiguity, and the one this harness trains:

1. Pick the simplest reading that makes the operation testable.
2. Implement it, and run the tests immediately.
3. If the sample tests disagree, **believe the tests** and adapt. Do not defend your
   reading.

Every ambiguity in this bank is resolved in the problem's `DECISIONS.md`, with the
alternatives and the reasoning — locked until you finish a session.

## One thing nobody could pin down

**[uncertain]** What the starter file actually looks like.

CodeSignal's own knowledge base groups the ICA under *single-function questions*, which
would imply one entry function receiving a list of query lists —
`solution(queries) -> list`. But the framework brief talks about "methods", "helper
methods and classes", and instructs you not to change "the existing method signatures",
which implies a class of stubs. No page found shows the live ICA starter, and the
dispatch-function shape used by the best-known community practice repo is that author's
own invention rather than CodeSignal's.

This rig assumes a class of stub methods. If you sit the real test and find a single
dispatch function instead, nothing about the *thinking* changes — the operations, the
ordering rules, the TTL semantics and the refactor are identical. Only the plumbing at
the boundary differs, and it is ten lines. Do not let it throw you.

## Sources

- CodeSignal, *What are the Industry Coding Assessment (ICA) rules?* — structure, the
  four level descriptions, proctoring, cooldown, and the 200–600 score range —
  <https://support.codesignal.com/hc/en-us/articles/19116922232983-What-are-the-Industry-Coding-Assessment-ICA-rules>
  (behind Cloudflare; direct fetching returns 403)
- CodeSignal, *Understanding Assessment Score* — the two-tier base/bonus scoring —
  <https://support.codesignal.com/hc/en-us/articles/13261190299287-Understanding-Assessment-Score>
- CodeSignal, *Industry Coding Skills Evaluation Framework* technical brief —
  <https://discover.codesignal.com/rs/659-AFH-023/images/Industry-Coding-Skills-Evaluation-Framework-CodeSignal-Skills-Evaluation-Lab-Short.pdf>
- CodeSignal, *Industry Coding Framework* — <https://codesignal.com/resource/industry-coding-framework/>
- PaulLockett, *CodeSignal_Practice_Industry_Coding_Framework* — the file-hosting
  statement reproduced in `problems/file_hosting/statement/` comes from here, and the
  per-level time table it cites originates with
  <https://yanirseroussi.com/2023/05/26/how-hackable-are-automated-coding-assessments/> —
  <https://github.com/PaulLockett/CodeSignal_Practice_Industry_Coding_Framework>
- The `ROLLBACK` ambiguity, argued in public —
  <https://github.com/PaulLockett/CodeSignal_Practice_Industry_Coding_Framework/issues/16>
- In-memory database variant, with signatures —
  <https://csoahelp.com/2025/02/09/codesignal-in-memory-database-industry-oa/>
- Cloud-storage-with-users variant and scoring bands —
  <https://interviewfox.ai/interview-questions/ramp-codesignal-oa-guide/>
- Format and scoring summary (third-party, treat as reported) —
  <https://www.sundeepteki.org/advice/anthropic-codesignal-assessment-guide>
- First-hand candidate reports — LeetCode Discuss and Blind threads on
  "CodeSignal Industry Coding Assessment".
