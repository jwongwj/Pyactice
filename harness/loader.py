"""Discovers problem definitions under `problems/`."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from dataclasses import replace
from pathlib import Path

from .model import Problem

ROOT = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = ROOT / "problems"
CURRICULUM_DIR = ROOT / "curriculum"


def _import_problem(directory: Path) -> Problem | None:
    """Import `problems/<name>/problem.py` as a real package module.

    Package-relative imports (`from .tests import ...`) only work if the module is
    loaded under its true dotted name, so `problems/` and each problem directory
    carry an `__init__.py` and we import by name rather than by path.
    """
    if not (directory / "problem.py").exists():
        return None

    package_root = str(ROOT)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)

    module = importlib.import_module(f"problems.{directory.name}.problem")
    problem = getattr(module, "PROBLEM", None)
    if problem is None:
        raise AttributeError(f"{directory / 'problem.py'} defines no PROBLEM")
    return replace(problem, directory=directory)


def _import_unit(path: pathlib.Path) -> tuple[Problem, ...]:
    """Load a curriculum module by file path.

    Two shapes live under `curriculum/`:
      <category>/<subtopic>/unit.py            a drill unit
      <category>/<subtopic>/<problem>/problem.py   one problem beside those drills

    Not by dotted name, because the directories are numbered for legibility
    (`1-basic-python/01-for-loops/`) and those are not importable identifiers. A unit
    is therefore self-contained -- absolute `from harness.model import ...` only, no
    package-relative imports -- which is why its cases live in the same file.
    """
    module_name = "_pfs_unit_" + "_".join(path.parts[-4:-1]).replace("-", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return ()
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    # PROBLEMS (plural) wins: a drill unit authors one Problem and exports the N
    # per-drill problems it splits into.
    several = getattr(module, "PROBLEMS", None)
    if several:
        return tuple(replace(p, directory=path.parent) for p in several)
    problem = getattr(module, "PROBLEM", None)
    if problem is None:
        raise AttributeError(f"{path} defines no PROBLEM or PROBLEMS")
    return (replace(problem, directory=path.parent),)


BROKEN: dict[str, str] = {}

# all_problems() re-imports and rebuilds the whole bank on every call, and the web UI
# calls it several times per request (once for the state payload, again inside each
# get_problem). At five problems that was 3 ms and invisible; at fourteen it is ~13 ms a
# call, and it started showing up as intermittent timeouts in the test suite. Memoise on
# a cheap signature of the source tree so an edit is still picked up immediately.
_CACHE: dict[str, Problem] | None = None
_CACHE_SIGNATURE: tuple | None = None
_CACHE_BROKEN: dict[str, str] = {}


def _signature() -> tuple:
    """Cheap fingerprint of the problem sources: (path, mtime, size) for each."""
    entries = []
    for root, pattern in ((PROBLEMS_DIR, "*/*.py"), (CURRICULUM_DIR, "*/*/*.py"),
                          (CURRICULUM_DIR, "*/*/*/*.py")):
        if not root.exists():
            continue
        for path in sorted(root.glob(pattern)):
            try:
                stat = path.stat()
            except OSError:
                continue
            entries.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(entries)


def invalidate() -> None:
    """Drop the cache. For tests, and for anything that writes a problem file."""
    global _CACHE, _CACHE_SIGNATURE
    _CACHE, _CACHE_SIGNATURE = None, None


def all_problems() -> dict[str, Problem]:
    """Import every problem, skipping (and recording) any that fail to load.

    One malformed problem must not take the whole bank down -- that would make the
    harness unusable exactly when someone is midway through adding a problem.

    Memoised on the source tree's mtimes, so editing a problem is picked up on the next
    call while an unchanged bank costs one stat per file instead of a full re-import.
    """
    global _CACHE, _CACHE_SIGNATURE
    signature = _signature()
    if _CACHE is not None and signature == _CACHE_SIGNATURE:
        BROKEN.clear()
        BROKEN.update(_CACHE_BROKEN)
        return dict(_CACHE)

    found: dict[str, Problem] = {}
    BROKEN.clear()
    if not PROBLEMS_DIR.exists():
        return found
    candidates: list[tuple[str, Path]] = []
    for directory in sorted(PROBLEMS_DIR.iterdir()):
        if directory.is_dir() and not directory.name.startswith((".", "_")):
            candidates.append(("problem", directory))
    if CURRICULUM_DIR.exists():
        for unit in sorted(CURRICULUM_DIR.glob("*/*/unit.py")):
            candidates.append(("unit", unit))
        # A problem that lives inside a subtopic, next to that subtopic's drills.
        # Loaded by path like a unit, so its cases live in problem.py rather than a
        # sibling tests.py -- numbered directories are not importable packages.
        for problem_file in sorted(CURRICULUM_DIR.glob("*/*/*/problem.py")):
            candidates.append(("unit", problem_file))

    for kind, target in candidates:
        directory = target if kind == "problem" else target.parent
        try:
            if kind == "problem":
                one = _import_problem(directory)
                loaded = (one,) if one is not None else ()
            else:
                loaded = _import_unit(target)
        # BaseException, not Exception: a problem module with a stray `sys.exit()` or a
        # KeyboardInterrupt at import time would otherwise take the whole bank down --
        # the opposite of what this loop is for.
        except BaseException as exc:  # noqa: BLE001
            BROKEN[directory.name] = f"{type(exc).__name__}: {exc}"
            continue
        for problem in loaded:
            if problem is not None:
                found[problem.key] = problem

    _CACHE, _CACHE_SIGNATURE = dict(found), signature
    _CACHE_BROKEN.clear()
    _CACHE_BROKEN.update(BROKEN)
    return dict(found)


def get_problem(key: str) -> Problem:
    problems = all_problems()
    if key in problems:
        return problems[key]
    matches = [k for k in problems if k.startswith(key)]
    if len(matches) == 1:
        return problems[matches[0]]
    known = ", ".join(sorted(problems)) or "(none)"
    if len(matches) > 1:
        raise KeyError(f"{key!r} is ambiguous: {', '.join(sorted(matches))}")
    raise KeyError(f"unknown problem {key!r}. Known problems: {known}")
