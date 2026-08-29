"""Starter-file generation.

Mirrors the real assessment: you are handed a class with typed stubs and told not
to change the signatures. Only the *unlocked* levels' stubs are written, because
seeing all four levels' methods up front changes how you design level 1 -- and
being ambushed by level 3 is precisely the skill under test.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from .model import KIND_PROGRESSIVE, Problem

_CLASS_HEADER = '''"""{title}

{blurb}

Rules of the exercise:
  * Do not rename the methods or change their signatures.
  * Implement one level at a time; run `./pfs test` often.
  * You will need to refactor. Later levels extend this same class.
"""

from __future__ import annotations


class {class_name}:
    def __init__(self) -> None:
        # Your state goes here. Think about what level 3 and level 4 will need
        # before you settle on it -- you get one chance to design this cheaply.
        pass
'''

# A `function` problem has no class and no later levels to design for, so its
# preamble says the two things that actually matter instead: the signature is fixed,
# and the tests call it directly.
_MODULE_HEADER = '''"""{title}

{blurb}

Rules of the exercise:
  * Do not rename the functions or change their signatures.
  * Run `./pfs test` often; partial credit is per test.
"""

from __future__ import annotations
'''

_LEVEL_BANNER = '''
    # ----------------------------------------------------------------------
    # Level {level} - {title}
    # ----------------------------------------------------------------------
'''

_CLASS_STUB = '''
    def {name}{signature}:
        """{doc}"""
        raise NotImplementedError("{display}")
'''

# Same body, no indent and no `self` -- the signature for a function problem is
# authored without it.
_FUNCTION_STUB = '''

def {name}{signature}:
    """{doc}"""
    raise NotImplementedError("{display}")
'''

_APPEND_BANNER = '''
    # ==========================================================================
    # Level {level} unlocked -- {title}
    # ==========================================================================
'''


def starter_source(problem: Problem, upto_level: int) -> str:
    if problem.is_class_kind:
        parts = [
            _CLASS_HEADER.format(
                title=problem.title,
                blurb=problem.opening,
                class_name=problem.class_name,
            )
        ]
    else:
        parts = [_MODULE_HEADER.format(title=problem.title, blurb=problem.opening)]

    # The shared types the signatures refer to. Emitted verbatim, and identical to the
    # definition the cases were built with, so a node the learner creates and a node the
    # test passes in are the same shape.
    if problem.preamble:
        parts.append("\n" + problem.preamble.strip("\n") + "\n")

    # Only the progressive format reveals itself a level at a time, so only it needs
    # the per-level banners; one level with a banner over it is just noise.
    banner = problem.kind == KIND_PROGRESSIVE
    for level in range(1, upto_level + 1):
        if banner:
            parts.append(_LEVEL_BANNER.format(level=level, title=problem.level(level).title))
        parts.extend(_stubs_for(problem, level))
    return "".join(parts)


def _stubs_for(problem: Problem, level: int) -> list[str]:
    template = _CLASS_STUB if problem.is_class_kind else _FUNCTION_STUB
    return [
        template.format(
            name=method.resolved_name(),
            signature=method.signature,
            doc=method.doc.replace('"""', "'''").strip() or method.display,
            display=method.display,
        )
        for method in problem.methods_for(level)
    ]


def level_stubs(problem: Problem, level: int) -> str:
    spec = problem.level(level)
    # "Level 1 unlocked" is only meaningful where levels unlock one at a time.
    parts = (
        [_APPEND_BANNER.format(level=level, title=spec.title)]
        if problem.kind == KIND_PROGRESSIVE
        else []
    )
    parts.extend(_stubs_for(problem, level))
    return "".join(parts)


def archive(path: Path) -> Path | None:
    """Move a previous attempt aside so a retake starts genuinely cold.

    Never deletes. A second attempt that begins with the first attempt's code is
    not a second attempt, but nobody wants their work thrown away either.
    """
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    folder = path.parent / "previous-attempts"
    folder.mkdir(parents=True, exist_ok=True)
    # rename() overwrites on POSIX and the stamp is second-resolution, so two
    # retakes inside one second silently destroyed the first attempt.
    destination = folder / f"{stamp}-{path.name}"
    suffix = 2
    while destination.exists():
        destination = folder / f"{stamp}-{suffix}-{path.name}"
        suffix += 1
    path.rename(destination)
    return destination


def write_starter(problem: Problem, path: Path, upto_level: int, *, force: bool) -> tuple[bool, str]:
    if path.exists() and not force:
        return False, f"{path} already exists (use --force to overwrite)"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(starter_source(problem, upto_level))
    return True, str(path)


def defined_methods(problem: Problem, text: str, level: int) -> list[str]:
    """Which of this level's methods the file already defines."""
    found = []
    for method in problem.methods_for(level):
        name = method.resolved_name()
        if re.search(rf"^\s*def\s+{re.escape(name)}\s*\(", text, re.M):
            found.append(name)
    return found


def append_level(problem: Problem, path: Path, level: int) -> tuple[bool, str]:
    if not path.exists():
        return False, f"no solution file at {path}"
    text = path.read_text()

    if f"Level {level} unlocked" in text:
        return False, f"level {level} stubs are already in {path.name}"

    # Appending a stub for a method the file already defines silently shadows the
    # candidate's implementation -- Python keeps the last definition, so their
    # working code starts raising NotImplementedError with no error anywhere.
    already = defined_methods(problem, text, level)
    if already:
        return False, (
            f"{path.name} already defines {', '.join(already)}. "
            "Appending these stubs again would shadow your implementation, so nothing was written."
        )

    with path.open("a") as handle:
        handle.write(level_stubs(problem, level))
    return True, f"appended level {level} stubs to {path}"
