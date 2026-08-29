"""Level-gating for CONTRACT.md.

The contract is readable during an attempt — it stands in for the type hints and
sample tests the real IDE gives you. But it must only describe the levels you have
actually unlocked. A contract that lists level 3's operations while you are designing
level 1 hands you the answer to the only question level 1 asks.

Two mechanisms, belt and braces:

  * any line naming an operation you have not unlocked is dropped automatically, so
    a new operation cannot leak through an author forgetting a marker;
  * `<!-- level: N -->` … `<!-- /level -->` wraps prose that is level-N knowledge
    without naming an operation ("capacity", "ttl", "backup").
"""

from __future__ import annotations

import re

from .model import Problem

_OPEN = re.compile(r"^\s*<!--\s*level:\s*(\d+)\s*-->\s*$")
_CLOSE = re.compile(r"^\s*<!--\s*/level\s*-->\s*$")
_HEADING = re.compile(r"^\s*#{1,6}\s")


_BULLET = re.compile(r"^\s*[-*]\s")


def gated(problem: Problem, text: str, upto_level: int) -> str:
    locked = {m.display for m in problem.methods if m.level > upto_level}
    lines = text.splitlines()
    kept: list[str] = []
    # A stack, not a boolean: with a boolean, a nested `<!-- level: 1 -->` inside a
    # locked block re-opened it, and the inner `<!-- /level -->` unlocked everything
    # that followed. Blocks nest, so the state has to.
    stack: list[bool] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        opened = _OPEN.match(line)
        if opened:
            stack.append(int(opened.group(1)) > upto_level)
            index += 1
            continue
        if _CLOSE.match(line):
            if stack:
                stack.pop()
            index += 1
            continue
        if any(stack):
            index += 1
            continue

        if any(name in line for name in locked):
            # Drop the whole bullet, not just the line that named the operation --
            # otherwise its wrapped continuation lines survive as orphaned prose.
            index += 1
            if _BULLET.match(line):
                while index < len(lines) and _is_continuation(lines[index]):
                    index += 1
            continue

        kept.append(line)
        index += 1

    return _tidy(kept)


def _is_continuation(line: str) -> bool:
    return bool(line.strip()) and line.startswith((" ", "\t")) and not _BULLET.match(line)


def _tidy(lines: list[str]) -> str:
    """Drop headings left empty by gating, and collapse the blank lines it leaves."""
    out: list[str] = []
    for index, line in enumerate(lines):
        if _HEADING.match(line):
            rest = lines[index + 1 :]
            has_body = any(
                l.strip() and not _HEADING.match(l) for l in _until_next_heading(rest)
            )
            if not has_body:
                continue
        out.append(line)

    collapsed: list[str] = []
    for line in out:
        if not line.strip() and collapsed and not collapsed[-1].strip():
            continue
        collapsed.append(line)
    return "\n".join(collapsed).strip() + "\n"


def _until_next_heading(lines: list[str]) -> list[str]:
    body: list[str] = []
    for line in lines:
        if _HEADING.match(line):
            break
        body.append(line)
    return body


def for_level(problem: Problem, upto_level: int) -> str:
    path = problem.directory / "CONTRACT.md"
    if not path.exists():
        return ""
    return gated(problem, path.read_text(), upto_level)
