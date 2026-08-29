"""Worked examples, derived from the `visible=True` cases.

Both the terminal (`render.render_examples`) and the web IDE read from here, so the
examples a candidate sees can never drift from the cases the grader runs. That is
the whole reason examples are generated rather than written by hand: a visible case
is how an ambiguous rule gets communicated, and a stale example would communicate
the wrong rule.
"""

from __future__ import annotations

from typing import Any

from .expect import ANY, Raises, describe
from .model import Problem


def _expected_text(expect: Any) -> str | None:
    if expect is ANY:
        return None
    if isinstance(expect, Raises):
        return "throws"
    return describe(expect)


def examples_for(problem: Problem, level: int) -> list[dict]:
    """The worked examples for one level: docs and operations, no case ids.

    No consumer renders the id, and shipping it to the browser put case names in a
    payload whose contract is that it carries none -- which is how exam mode's
    "nothing identifies a test" invariant first sprang a leak.
    """
    out: list[dict] = []
    for entry in problem.cases_for(level):
        if not entry.visible:
            continue
        out.append(
            {
                "doc": entry.doc,
                "ops": [
                    {
                        "call": operation.render(),
                        "expected": _expected_text(operation.expect),
                        "why": operation.why,
                    }
                    for operation in entry.ops
                ],
            }
        )
    return out
