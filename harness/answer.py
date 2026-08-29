"""Worked solutions: locating them, and showing only as much as you asked for.

`solutions/<key>.py` is the one place an answer can live that `./pfs start` will
not archive out from under you — the workspace is rewritten with fresh stubs on
every attempt, which is correct for practice and useless for study.

Showing only levels 1..N matters more than it sounds. "Show me the answer" is
rarely what somebody means: stuck on level 2 of four, they want level 2, and
level 4's refactor spoils the two levels they were still going to earn.

There are two ways to serve a level, and the first is much better:

  solutions/<key>/levelN.py   a real snapshot of the file at that level
  solutions/<key>.py          the finished solution, sliced at its level banners

A snapshot is honest — it is what the file actually looked like then. A slice is a
best effort: the code below the banner goes, but the module docstring was written
to describe the finished article, so it is replaced rather than trusted.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from .loader import ROOT
from .model import Problem

SOLUTIONS_DIR = ROOT / "solutions"

# The banner every worked solution in this bank uses to separate its levels.
_LEVEL_BANNER = re.compile(r"^\s*#\s*Level\s+(\d+)\b", re.IGNORECASE)


def solution_path(problem: Problem) -> Path | None:
    """The file holding this problem's worked solution.

    A drill split out of a unit shares the unit's oracle -- ninety-two near-identical
    one-function files would be a filing system, not a benefit -- so `solution_key`
    redirects here and `resolve` extracts the one function afterwards.
    """
    key = problem.solution_key or problem.key
    path = SOLUTIONS_DIR / f"{key}.py"
    return path if path.exists() else None


def extract_function(source: str, name: str) -> str:
    """Just one function from a file of many, with the imports it might need.

    Showing a drill's answer should show that drill's answer. Handing over the whole
    unit's oracle answers the eleven drills the learner has not attempted yet.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    lines = source.splitlines()

    header: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            header.extend(lines[node.lineno - 1:(node.end_lineno or node.lineno)])

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = min(
                [node.lineno] + [d.lineno for d in node.decorator_list]
            ) - 1
            body = lines[start:(node.end_lineno or node.lineno)]
            return "\n".join(([*header, ""] if header else []) + body).rstrip() + "\n"
    return ""


def snapshot_path(problem: Problem, level: int) -> Path | None:
    path = SOLUTIONS_DIR / problem.key / f"level{level}.py"
    return path if path.exists() else None


def snapshot_levels(problem: Problem) -> list[int]:
    directory = SOLUTIONS_DIR / problem.key
    if not directory.is_dir():
        return []
    found = []
    for path in directory.glob("level*.py"):
        match = re.fullmatch(r"level(\d+)", path.stem)
        if match:
            found.append(int(match.group(1)))
    return sorted(found)


def levels_present(source: str) -> list[int]:
    found = {
        int(match.group(1))
        for match in (_LEVEL_BANNER.match(line) for line in source.splitlines())
        if match
    }
    return sorted(found)


def _strip_module_docstring(source: str) -> str:
    """Drop the module docstring, which describes the FINISHED solution.

    Slicing removes level 4's code but not the header that announced it, so a
    candidate asking for level 1 would still read the names of every operation in
    the problem. Dropping it is cheap; rewriting it to be level-accurate is not.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    if not (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        return source
    end = tree.body[0].end_lineno or 0
    lines = source.splitlines()[end:]
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines) + "\n"


def slice_upto(source: str, level: int) -> str:
    """Everything up to and including `level`, dropping later level sections.

    A section runs from its banner to the next banner. Whatever precedes the first
    banner -- imports, the class statement, shared helpers -- is always kept, since
    without it the result would not be readable code.
    """
    lines = source.splitlines()
    kept: list[str] = []
    current: int | None = None

    for line in lines:
        match = _LEVEL_BANNER.match(line)
        if match:
            current = int(match.group(1))
            # The banner is usually the middle line of a three-line "# ====" box;
            # drop the rule above it too, or the box is left with no lid.
            if current > level and kept and kept[-1].lstrip().startswith("# ="):
                kept.pop()
        if current is not None and current > level:
            continue
        kept.append(line)

    while kept and not kept[-1].strip():
        kept.pop()
    return _strip_module_docstring("\n".join(kept) + "\n")


def resolve(problem: Problem, level: int | None) -> tuple[str, str, Path] | None:
    """(source, provenance, path) for the requested view, or None if unavailable."""
    # A drill: pull its one function out of the unit's oracle.
    if problem.solution_key and problem.methods:
        whole = solution_path(problem)
        if whole is None:
            return None
        one = extract_function(whole.read_text(), problem.methods[0].resolved_name())
        return (one, "drill", whole) if one else None

    if level is not None:
        snapshot = snapshot_path(problem, level)
        if snapshot is not None:
            return snapshot.read_text(), "snapshot", snapshot

    whole = solution_path(problem)
    if whole is None:
        return None
    source = whole.read_text()
    if level is None:
        return source, "full", whole
    if not levels_present(source):
        return None
    return slice_upto(source, level), "slice", whole
