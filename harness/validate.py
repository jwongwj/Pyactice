"""Self-checks for the problem bank.

Two layers:

  structural   Cheap, always available. Catches typos, unknown operation names,
               cases that use a level-3 method inside a level-2 case, missing
               statements, untested methods, undocumented tags.

  differential `--against <solution.py>` runs every case against a known-good
               implementation. Any failure means the *test suite* is wrong, not
               the solution. This is the only way to be sure a hand-authored
               expected value is right, so it is the gate that must run before
               the bank is trusted. It stays unused until a reference solution
               exists in `solutions/`.
"""

from __future__ import annotations

from pathlib import Path

from .model import KIND_DRILL, KIND_PROGRESSIVE, Problem
from .runner import Outcome, run


def structural(problem: Problem) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors = list(problem.validate())
    warnings: list[str] = []

    directory = problem.directory
    if directory is None:
        errors.append("problem has no directory")
        return errors, warnings

    progressive = problem.kind == KIND_PROGRESSIVE

    for level in problem.levels:
        statement = problem.statement_path(level.number)
        if statement is None:
            # A split drill's statement is generated, not filed. There is no path to
            # check, but an empty one would leave the learner with no task at all.
            if not problem.statement_body(level.number).strip():
                errors.append(f"level {level.number} generates an empty statement")
            continue
        if not statement.exists():
            errors.append(f"missing statement: {statement.relative_to(directory.parent.parent)}")

    # CONTRACT.md and DECISIONS.md exist to manage progressive disclosure: types for
    # levels you have unlocked, and a ledger of ambiguities the levels create. A
    # one-level problem discloses everything at once, so requiring them would only
    # produce two ceremonial files per problem. What it needs instead is teaching
    # prose, and that is what APPROACH.md and EXPLANATION.md are for.
    if progressive:
        required = ("CONTRACT.md", "DECISIONS.md")
    elif problem.kind == KIND_DRILL:
        # A drill's teaching artifact is its unit's LESSON.md, shared by every drill
        # split out of that unit. Demanding an approach and an explanation per drill as
        # well would mean writing three documents to introduce `enumerate`.
        required = ()
    else:
        required = ("APPROACH.md", "EXPLANATION.md")
    for name in required:
        if not (directory / name).exists():
            errors.append(f"missing {name}")

    exercised = {
        operation.name
        for entry in problem.cases
        for operation in entry.ops
    }
    for method in problem.methods:
        if method.display not in exercised:
            errors.append(f"operation {method.display} is never exercised by a case")

    # The quality floor is per kind, because the shapes are not comparable. A level of
    # a progressive problem is one continuous system probed from many angles, so it
    # wants many hidden cases. A drill unit is a dozen independent one-idiom drills,
    # where three or four cases each is plenty because the CONSTRAINT carries the
    # teaching -- judging it by the same number would demand a hundred cases per unit.
    if problem.kind == KIND_DRILL:
        by_method: dict[str, list] = {m.display: [] for m in problem.methods}
        for entry in problem.cases:
            for operation in entry.ops:
                if operation.name in by_method:
                    by_method[operation.name].append(entry)
        for display, owned in by_method.items():
            if len(owned) < 2:
                errors.append(
                    f"drill {display} has {len(owned)} case(s); it needs at least 2 "
                    "so a hardcoded answer cannot pass"
                )
            elif len(owned) < 3:
                warnings.append(
                    f"drill {display} has 2 cases; 3+ (including an edge value) is the target"
                )
            if owned and not any(not c.visible for c in owned):
                warnings.append(f"drill {display} has no hidden case")
        for method in problem.methods:
            if not method.constraints and not method.checkpoint:
                warnings.append(
                    f"drill {method.display} has no constraint, so it only grades the "
                    "answer and not the idiom it is meant to teach"
                )
    else:
        for level in problem.levels:
            cases = problem.cases_for(level.number)
            hidden = [c for c in cases if not c.visible]
            # The message used to say "aim for 8+" while the check fired below 4, so
            # nine of twenty existing levels missed the target with no signal at all.
            if len(hidden) < 8:
                warnings.append(
                    f"level {level.number} has {len(hidden)} hidden cases; aim for 8+ so "
                    "passing requires understanding rather than pattern-matching"
                )
            visible = [c for c in cases if c.visible]
            if len(visible) > 6:
                warnings.append(
                    f"level {level.number} has {len(visible)} visible cases; every visible "
                    "case is a rule given away, so keep it to the genuinely ambiguous ones"
                )
        introduced = {m.display for m in problem.methods_for(level.number)}
        touched = {op.name for c in cases for op in c.ops}
        if introduced and not (introduced & touched):
            errors.append(f"level {level.number} never calls its own new operations")

    # Every level above 1 should re-exercise earlier operations, otherwise the
    # suite cannot catch the regressions that refactoring introduces. Only the
    # progressive format has earlier levels to regress.
    for level in problem.levels if progressive else ():
        if level.number == 1:
            continue
        earlier = {m.display for m in problem.methods if m.level < level.number}
        touched = {op.name for c in problem.cases_for(level.number) for op in c.ops}
        if earlier and not (earlier & touched):
            warnings.append(
                f"level {level.number} cases never call level-{level.number - 1} "
                "operations; refactoring regressions will not be caught here"
            )

    return errors, warnings


def differential(problem: Problem, reference: Path) -> list[str]:
    """Run every case against a reference solution. Any failure is a suite bug."""
    result = run(problem, reference, max_level=problem.max_level, op_timeout=10.0)
    if result.load_error:
        return [f"could not load reference: {result.load_error.strip().splitlines()[-1]}"]

    problems: list[str] = []
    for level in result.levels:
        for case_result in level.cases:
            if case_result.passed:
                continue
            failing = case_result.failing_op
            where = failing.op.render() if failing else "?"
            expected = failing.op.expect if failing else None
            actual = failing.actual if failing else None
            if case_result.outcome is Outcome.NOT_IMPLEMENTED:
                problems.append(
                    f"{case_result.case.id}: reference does not implement {where} "
                    "(incomplete reference, not necessarily a suite bug)"
                )
                continue
            problems.append(
                f"{case_result.case.id} [{case_result.outcome.value}] at {where}: "
                f"suite expects {expected!r}, reference produced {actual!r}"
            )
    return problems
