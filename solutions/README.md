# solutions/ — worked solutions, gitignored

No reference solutions **ship** with this repo — `solutions/*.py` is gitignored.
That is deliberate: a solution sitting one directory away from a problem you are
about to attempt cold changes how you attempt it, even if you never open the file.

What lives here locally is yours. `./pfs answer <problem>` reads it, and refuses
while that problem's session is live, so having it costs you nothing during an
attempt. It is also the only place an answer survives `./pfs start`, which archives
your workspace and writes fresh stubs every time.

    ./pfs answer file_system              # the whole thing
    ./pfs answer file_system --level 2    # levels 1-2 only, so level 4 stays yours

Two layouts, and the first is better:

    solutions/<key>/levelN.py   a real snapshot of the file at that level
    solutions/<key>.py          the finished solution, sliced at its `# Level N` banners

A snapshot is what the file honestly looked like then. A slice is the finished
article with later sections cut out, so its earlier levels may already be shaped by
decisions that came later — `./pfs answer` says so when it is showing you one.

## What this costs, and how it is covered

Expected values in `problems/*/tests.py` are hand-authored. Hand-authored
expectations are guesses until something executes them, so each suite was verified
before shipping by writing a throwaway reference implementation **outside this
repo**, running

```bash
./pfs validate <problem> --against /path/outside/repo/oracle.py
```

until every case agreed, then mutation-testing the suite

```bash
python3 tools/mutation_check.py <problem> /path/outside/repo/oracle.py
```

until every classic candidate bug was caught by at least one case — and then
deleting the oracle. `file_hosting` passed both gates: 57/57 cases agreed, 14/14
mutants caught.

## When you will want this directory

After a walkthrough. Once you have solved a problem yourself, put your solution here
as `solutions/<problem_key>.py` with the problem's class name, and `./pfs validate`
will pick it up automatically and re-run the differential gate on every future
change to the suite:

```bash
./pfs validate                 # uses solutions/<key>.py if it exists
```

That is the point at which having a reference is useful rather than corrosive.

`solutions/*.py` is gitignored.
