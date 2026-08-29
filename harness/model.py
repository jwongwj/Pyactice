"""The data model for a progressive-level problem.

A problem is four levels of one continuous system. Each level adds operations and
must not break the ones before it -- which is why `Case.level` gates *when* a case
first runs, and why the runner always re-runs every case at or below the current
level. Regressions into level 1 while building level 3 are the single most common
way candidates lose points.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .expect import ANY, Raises

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


@dataclass(frozen=True)
class Op:
    """A single call in a test case."""

    name: str
    args: tuple
    expect: Any = ANY
    why: str = ""
    # Keyword arguments, so a **kwargs operation can actually be exercised. A frozen
    # dataclass cannot hold a dict safely as a default, hence the tuple of pairs.
    kwargs: tuple[tuple[str, Any], ...] = ()

    def render(self) -> str:
        parts = [repr(a) for a in self.args]
        parts += [f"{k}={v!r}" for k, v in self.kwargs]
        return f"{self.name}({', '.join(parts)})"


def op(
    name: str,
    *args: Any,
    ret: Any = ANY,
    raises: Any = None,
    why: str = "",
    kw: dict[str, Any] | None = None,
) -> Op:
    """Build an `Op`.

    `ret` defaults to ANY so that void operations need no annotation -- matching the
    real assessment, which does not care what your `file_upload` returns.
    Pass `raises=True` (or an exception class) for operations that must throw.
    """
    if raises is not None:
        if raises is True:
            expect: Any = Raises()
        elif isinstance(raises, type):
            expect = Raises(raises)
        else:
            expect = raises
    else:
        expect = ret
    return Op(
        name=name,
        args=tuple(args),
        expect=expect,
        why=why,
        kwargs=tuple(sorted((kw or {}).items())),
    )


@dataclass(frozen=True)
class Case:
    """One test case: a sequence of operations against a fresh instance."""

    id: str
    level: int
    ops: tuple[Op, ...]
    tags: tuple[str, ...] = ()
    visible: bool = False
    doc: str = ""
    weight: int = 1

    def __post_init__(self) -> None:
        if not self.ops:
            raise ValueError(f"case {self.id!r} has no operations")
        if self.level < 1:
            raise ValueError(f"case {self.id!r} has invalid level {self.level}")


def case(
    id: str,
    level: int,
    ops: Sequence[Op],
    *,
    tags: Iterable[str] = (),
    visible: bool = False,
    doc: str = "",
    weight: int = 1,
) -> Case:
    return Case(
        id=id,
        level=level,
        ops=tuple(ops),
        tags=tuple(tags),
        visible=visible,
        doc=doc,
        weight=weight,
    )


@dataclass(frozen=True)
class Method:
    """One operation in the problem's public interface.

    `signature` is emitted verbatim into the starter file, so it doubles as the
    type contract the candidate is expected to read.
    """

    display: str
    signature: str
    level: int = 1
    doc: str = ""
    python_name: str = ""
    # Constraints on HOW this is written, checked against the AST. A drill teaches an
    # idiom, and a grader that only looks at the return value lets a nested loop pass
    # while missing the entire point. See harness/constraints.py.
    constraints: tuple = ()
    # One line, shown to the learner in the stub docstring. A constraint they could not
    # have known about is a trick question.
    constraint_note: str = ""
    # The drill's PRECONDITION on its inputs, for the fuzzer in tools/drill_mutation.py.
    # Never shown to the learner and never enforced at run time -- the statement already
    # says "an ascending list with no duplicates" in prose. This exists because the
    # fuzzer was inventing inputs the drill never promised to handle and reporting the
    # resulting disagreements as suite gaps, which would have sent me chasing phantoms.
    # Vocabulary: "sorted", "unique", "rotated", "nonneg", "positive", "binary",
    # "grid", "edges", "ordered-pairs", "disjoint-sorted", "paired-lists",
    # "paired-ordered", "colors" -- plus "opaque", which is about the RETURN rather than
    # the input: it marks a value the statement leaves up to the implementation, so the
    # sequence fuzzer must not treat two different-but-valid answers as a disagreement.
    fuzz: tuple[str, ...] = ()
    # The unit's checkpoint: several idioms at once, deliberately unconstrained because
    # choosing the tools yourself is the point. Exempt from the "every drill needs a
    # constraint" rule -- which used to be decided by matching the name against
    # "REPORT", a heuristic that would silently stop working on the next unit.
    checkpoint: bool = False

    def resolved_name(self) -> str:
        return self.python_name or default_python_name(self.display)


def default_python_name(display: str) -> str:
    """FILE_UPLOAD_AT -> file_upload_at;  scanByPrefix -> scan_by_prefix."""
    if display.isupper() or "_" in display:
        return display.lower()
    return _CAMEL_BOUNDARY.sub("_", display).lower()


@dataclass(frozen=True)
class Level:
    number: int
    title: str
    # Defaulted so a single-level problem does not have to invent a time band or a
    # share of a points total that only the progressive format has.
    budget_minutes: tuple[int, int] = (0, 0)
    weight: int = 0
    theme: str = ""


# How a solution is called, which is the only thing the runner needs to know.
#
#   progressive  a class whose methods grow level by level (the CodeSignal ICF shape)
#   design       a class, all of its methods at once, one level (LRU cache, MinStack)
#   function     one top-level function per operation, one level (LeetCode shape)
#
# `progressive` and `design` are both instantiated and called through the instance;
# `function` uses the module itself as the subject, so `getattr(subject, name)` finds
# a top-level `def` with no other change.
KIND_PROGRESSIVE = "progressive"
KIND_DESIGN = "design"
KIND_FUNCTION = "function"
# A drill unit: many tiny top-level functions in one file, each one idiom, each with
# its own constraints. Function-shaped, one level, untimed.
KIND_DRILL = "drill"
CLASS_KINDS = (KIND_PROGRESSIVE, KIND_DESIGN)
FUNCTION_KINDS = (KIND_FUNCTION, KIND_DRILL)


@dataclass(frozen=True)
class Problem:
    key: str
    title: str
    blurb: str
    # Empty for `function` problems, which have no class to instantiate.
    class_name: str
    levels: tuple[Level, ...]
    methods: tuple[Method, ...]
    cases: tuple[Case, ...]
    tag_glossary: dict[str, str] = field(default_factory=dict)
    source: str = ""
    directory: Any = None
    kind: str = KIND_PROGRESSIVE
    # The progressive format scores out of 600 because that is the real assessment's
    # scale. Nothing else has to.
    total_points: int = 600
    category: str = ""
    difficulty: str = ""
    topics: tuple[str, ...] = ()
    # A generated statement, used instead of reading a file. A drill split out of a unit
    # has no statement file of its own -- its task is its signature, its docstring and
    # its constraints, which are all already here.
    # Source emitted into the starter file below the header, and shown in the statement.
    # A linked-list or tree drill cannot state its signature without a node type, and the
    # learner needs the identical definition to construct one. Authored ONCE in the unit
    # and exec'd there to build the cases, so the two cannot drift apart.
    preamble: str = ""
    statement_text: str = ""
    # `title` is fully qualified so it stands alone in a flat list and a session header.
    # Nested under its unit that reads as "1.1 For loops · 3. NUMBERED" inside a box
    # already headed "1.1 For loops", so a drill also carries the short form.
    short_title: str = ""
    # The unit this came from, when it was split out of one: (unit key, unit title).
    # Lets the UI group drills and offer the unit's lesson beside them.
    unit: tuple[str, str] = ()
    # A filename in `directory` holding the teaching material for this problem's unit.
    lesson: str = ""
    # Where the worked solution lives, when it is not `solutions/<key>.py` -- a drill
    # shares its unit's oracle rather than having 92 near-identical files.
    solution_key: str = ""

    @property
    def opening(self) -> str:
        """The blurb's first clause — what level 1 alone is about.

        A progressive `blurb` names every level, which is right for the README and
        wrong for anything a candidate sees during an attempt: the starter file's
        docstring and the problem picker would otherwise hand over the whole arc
        before the first line of code is written.

        Non-progressive problems have nothing to withhold — there is one level — and
        splitting on a semicolon there would truncate an ordinary sentence.
        """
        if self.kind != KIND_PROGRESSIVE:
            return self.blurb.strip()
        return self.blurb.split(";")[0].strip()

    @property
    def is_class_kind(self) -> bool:
        return self.kind in CLASS_KINDS

    @property
    def timed(self) -> bool:
        """Only the progressive format is against a clock.

        That is what it is simulating -- ninety minutes is the assessment's own
        constraint. A drill or a single function is work, not an exam, and putting a
        countdown on it measures nothing.
        """
        return self.kind == KIND_PROGRESSIVE

    def level(self, number: int) -> Level:
        for entry in self.levels:
            if entry.number == number:
                return entry
        raise KeyError(f"{self.key} has no level {number}")

    @property
    def max_level(self) -> int:
        return max(entry.number for entry in self.levels)

    def methods_for(self, level: int) -> tuple[Method, ...]:
        return tuple(m for m in self.methods if m.level == level)

    def method_map(self) -> dict[str, Method]:
        return {m.display: m for m in self.methods}

    def cases_for(self, level: int) -> tuple[Case, ...]:
        return tuple(c for c in self.cases if c.level == level)

    def cases_upto(self, level: int) -> tuple[Case, ...]:
        return tuple(c for c in self.cases if c.level <= level)

    @property
    def label(self) -> str:
        """What to call this problem when its unit is already named around it."""
        return self.short_title or self.title

    @property
    def lesson_path(self):
        """The unit's teaching material, if this problem has any."""
        if not self.lesson or self.directory is None:
            return None
        path = self.directory / self.lesson
        return path if path.exists() else None

    def statement_body(self, level: int) -> str:
        """The statement to show, from generated text or from the file."""
        if self.statement_text:
            return self.statement_text
        path = self.statement_path(level)
        return path.read_text() if path is not None and path.exists() else ""

    def statement_path(self, level: int):
        # A generated statement has no file. Checked first, because a split drill is
        # still KIND_DRILL and the branch below would hand back the unit's LESSON.md --
        # serving the teaching as the task, and the answer with it.
        if self.statement_text:
            return None
        # An unsplit drill unit's statement IS its lesson -- the idioms, one screen, read before
        # anything else. Routing it here means the CLI's `spec`, the browser's Task pane
        # and the validator all pick it up with no special cases anywhere else.
        if self.kind == KIND_DRILL:
            return self.directory / "LESSON.md"
        # A one-level problem has one statement, so it does not need a directory with a
        # single `level1.md` in it. Progressive problems keep the numbered form, because
        # theirs really are cumulative -- level3.md contains levels 1 to 3.
        single = self.directory / "statement.md"
        if self.kind != KIND_PROGRESSIVE and single.exists():
            return single
        return self.directory / "statement" / f"level{level}.md"

    def all_tags(self) -> tuple[str, ...]:
        seen: dict[str, None] = {}
        for entry in self.cases:
            for tag in entry.tags:
                seen[tag] = None
        return tuple(seen)

    def validate(self) -> list[str]:
        """Structural self-check. Returns a list of problems found."""
        errors: list[str] = []
        known = self.method_map()
        seen_ids: set[str] = set()

        for entry in self.cases:
            if entry.id in seen_ids:
                errors.append(f"duplicate case id {entry.id!r}")
            seen_ids.add(entry.id)
            if entry.level > self.max_level:
                errors.append(f"{entry.id}: level {entry.level} exceeds max {self.max_level}")
            for index, operation in enumerate(entry.ops):
                method = known.get(operation.name)
                if method is None:
                    errors.append(
                        f"{entry.id} op[{index}]: unknown operation {operation.name!r}"
                    )
                    continue
                if method.level > entry.level:
                    errors.append(
                        f"{entry.id} op[{index}]: uses {operation.name} "
                        f"(level {method.level}) inside a level-{entry.level} case"
                    )

        for level in self.levels:
            if not self.cases_for(level.number):
                errors.append(f"level {level.number} has no cases")
            if not any(c.visible for c in self.cases_for(level.number)):
                errors.append(f"level {level.number} has no visible sample case")

        if self.kind not in (KIND_PROGRESSIVE, KIND_DESIGN, KIND_FUNCTION, KIND_DRILL):
            errors.append(f"unknown kind {self.kind!r}")
        if self.is_class_kind and not self.class_name:
            errors.append(f"{self.kind} problems need a class_name")
        if self.kind in FUNCTION_KINDS and self.class_name:
            errors.append(f"{self.kind} problems must not declare a class_name")

        # Only the progressive format apportions a fixed points total across levels.
        if self.kind == KIND_PROGRESSIVE:
            total_weight = sum(level.weight for level in self.levels)
            if total_weight != self.total_points:
                errors.append(
                    f"level weights sum to {total_weight}, expected {self.total_points}"
                )
        if self.kind != KIND_PROGRESSIVE and len(self.levels) != 1:
            errors.append(f"{self.kind} problems have exactly one level, not {len(self.levels)}")

        for entry in self.cases:
            for tag in entry.tags:
                if tag not in self.tag_glossary:
                    errors.append(f"{entry.id}: tag {tag!r} missing from tag_glossary")

        return errors
