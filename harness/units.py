"""Splitting a drill unit into one problem per drill.

A unit is authored as a single `Problem` with many methods, because twelve one-idiom
drills in twelve directories would be forty-eight files to hold twelve one-line
exercises, and nobody would ever browse it. But a unit is the wrong thing to *practise*
against: it has one score, one session and one workspace file, so "I want to drill
`enumerate`" means opening a file of twelve functions, and progress cannot say which
drills you have actually cleared.

So authoring stays per unit and practice is per drill. `split(unit)` turns one authored
unit into N problems, each with:

  * its own key, `<unit>.<drill>`, so it has its own session, workspace file and progress
  * exactly one method, and only the cases that exercise it
  * a GENERATED statement -- the task and its constraints, and nothing else. This is the
    other half of the split: the unit's LESSON teaches the idiom, the statement states
    the task, and the worked answer stays behind `./pfs answer`. Mixing the three is how
    a lesson ends up handing over the solution.
  * a pointer back to the unit, so the UI can group them and offer the lesson alongside
  * a shared `solution_key`, so all twelve drills read the unit's one oracle file
"""

from __future__ import annotations

from dataclasses import replace

from .model import Level, Problem


def _statement(problem: Problem, method) -> str:
    """The task, in the learner's terms. Never the answer."""
    lines = [f"# {method.display}", ""]
    if problem.preamble:
        # The signature below names a type; the learner has to be able to read its
        # definition, and it is already in their starter file.
        lines.append("Your file already defines:")
        lines.append("")
        lines.append(f"```python\n{problem.preamble.strip()}\n```")
        lines.append("")
    lines.append(f"```python\ndef {method.resolved_name()}{method.signature}\n```")
    lines.append("")
    if method.doc:
        lines.append(method.doc)
        lines.append("")
    if method.constraint_note:
        # Stated up front, always. A constraint the learner could not have known about
        # is a trick question, and this is the only place they will read it.
        lines.append("**Constraint**")
        lines.append("")
        lines.append(method.constraint_note)
        lines.append("")
    if method.checkpoint:
        lines.append(
            "This is the unit's **checkpoint**: no constraints, several ideas at once. "
            "Choosing the right tools is the exercise."
        )
        lines.append("")
    if problem.lesson:
        lines.append(
            f"The idioms this drill practises are in the **Lesson** tab."
        )
    return "\n".join(lines).rstrip() + "\n"


def split(unit: Problem, *, lesson: str = "LESSON.md") -> tuple[Problem, ...]:
    """One problem per drill, in the order the unit declares them."""
    out: list[Problem] = []
    for index, method in enumerate(unit.methods, start=1):
        owned = tuple(
            entry for entry in unit.cases
            if any(operation.name == method.display for operation in entry.ops)
        )
        if not owned:
            raise ValueError(f"{unit.key}: drill {method.display} has no cases")

        drill = replace(
            unit,
            key=f"{unit.key}.{method.resolved_name()}",
            # Numbered so the order is visible wherever they are listed, and so a
            # learner can see how far through the unit they are.
            title=f"{unit.title} · {index}. {method.display}",
            short_title=f"{index}. {method.display}",
            blurb=method.doc or method.display,
            methods=(replace(method, level=1),),
            cases=owned,
            levels=(Level(1, method.display),),
            unit=(unit.key, unit.title),
            lesson=lesson,
            # Every drill in a unit shares the unit's oracle file.
            solution_key=unit.key,
            statement_text="",
        )
        out.append(replace(drill, statement_text=_statement(drill, method)))
    return tuple(out)
