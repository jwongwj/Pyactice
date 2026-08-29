"""A small Markdown-to-HTML converter for the problem statements.

Covers exactly the subset the statements, contracts and lessons use: ATX headings,
fenced code, unordered lists, pipe tables, bold, emphasis, and inline code. Written
rather than installed because the rest of this repo has no dependencies and a practice
rig that needs `pip install` to show you a problem is a practice rig you will not use.

Backslash escapes are supported for the characters this subset gives meaning to, which is
how a document writes a literal asterisk: the A* lesson would otherwise have no way to
name its own algorithm.

Blockquotes and code blocks nested inside list items are still unsupported. Nothing in
the bank uses either, and both are written around rather than freed.
"""

from __future__ import annotations

import html
import re

_BOLD = re.compile(r"\*\*(.+?)\*\*")
# Applied after bold, so `**x**` is already a <strong> and leaves no asterisks behind.
# `<` and `>` are excluded so a span can never straddle a tag emitted just above --
# `<code>a * b</code>` next to a real *emphasis* would otherwise splice the two.
# The inner guards are what stop `3 * 4 * 5` becoming `3 <em> 4 </em> 5`: an opening
# star must be followed by non-space and a closing one preceded by it. The outer ones
# leave `a*b*c` and `*args, **kwargs` alone, which the unpacking and lambda lessons
# both discuss in prose.
_EMPHASIS = re.compile(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])")
_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
_ORDERED = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
_RULE = re.compile(r"^\s*(?:-{3,}|_{3,}|\*{3,})\s*$")


def _emphasise(match: re.Match) -> str:
    """`*...*`, unless the span straddles a tag emitted a moment ago.

    Bold runs first, so a legitimate span may contain `<strong>`; an illegitimate one
    has swallowed only half of a tag, which unbalanced angle brackets reveal.
    """
    body = match.group(1)
    if body.count("<") != body.count(">"):
        return match.group(0)
    return f"<em>{body}</em>"


# A backslash before a markup character means the character itself. `A\*` is the reason
# this exists: the algorithm's name genuinely ends in an asterisk, and without an escape
# there is no way to write it that is not either emphasis or a stray `*` on the page.
_ESCAPED = re.compile(r"\\([\\`*_\[\]])")


def _inline(text: str) -> str:
    out = html.escape(text)

    # Lifted out before anything else can interpret them, and put back at the very end
    # alongside the code spans.
    escapes: list[str] = []

    def hide(match: re.Match) -> str:
        escapes.append(match.group(1))
        return f"\x01{len(escapes) - 1}\x01"

    out = _ESCAPED.sub(hide, out)

    # Code spans are lifted out before anything else runs, and put back last. An
    # asterisk inside `*args` is not emphasis and an underscore inside a name is not
    # anything, but a regex reading left to right cannot tell -- so it never sees them.
    spans: list[str] = []

    def stash(match: re.Match) -> str:
        spans.append(match.group(1))
        return f"\x00{len(spans) - 1}\x00"

    out = _CODE.sub(stash, out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _EMPHASIS.sub(_emphasise, out)
    out = _LINK.sub(r'<a href="\2" target="_blank" rel="noopener">\1</a>', out)
    for index, code in enumerate(spans):
        out = out.replace(f"\x00{index}\x00", f"<code>{code}</code>")
    for index, character in enumerate(escapes):
        out = out.replace(f"\x01{index}\x01", character)
    return out


def _split_row(line: str) -> list[str]:
    r"""Split a table row on unescaped pipes.

    Signatures in the contracts contain `int \| None`, and a naive split on "|"
    blew those rows into extra columns with a dangling backtick.
    """
    cells, current, index = [], [], 0
    text = line.strip().strip("|")
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            current.append(text[index + 1])
            index += 2
            continue
        if text[index] == "|":
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(text[index])
        index += 1
    cells.append("".join(current).strip())
    return cells


def _is_table_divider(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and set(stripped) <= set("|-: ")


def to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    index = 0
    list_tag: str | None = None

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def open_list(tag: str) -> None:
        nonlocal list_tag
        if list_tag != tag:
            close_list()
            out.append(f"<{tag}>")
            list_tag = tag

    while index < len(lines):
        line = lines[index]

        if line.strip().startswith("```"):
            close_list()
            language = line.strip()[3:].strip()
            index += 1
            body: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                body.append(lines[index])
                index += 1
            index += 1
            css = f' class="lang-{html.escape(language)}"' if language else ""
            out.append(f"<pre{css}><code>{html.escape(chr(10).join(body))}</code></pre>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if (
            line.strip().startswith("|")
            and index + 1 < len(lines)
            and _is_table_divider(lines[index + 1])
        ):
            close_list()
            header = _split_row(line)
            index += 2
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(_split_row(lines[index]))
                index += 1
            head = "".join(f"<th>{_inline(c)}</th>" for c in header)
            body = "".join(
                "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>"
                for row in rows
            )
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue

        # Before the bullet rule: `***` is a rule, not a list item, and `---` would
        # otherwise be swept into the paragraph below it.
        if _RULE.match(line):
            close_list()
            out.append("<hr>")
            index += 1
            continue

        bullet = _BULLET.match(line) or _ORDERED.match(line)
        if bullet:
            open_list("ol" if _ORDERED.match(line) else "ul")
            depth = len(bullet.group(1)) // 2
            css = ' class="nested"' if depth else ""
            # An item may wrap onto indented continuation lines. They are joined to the
            # bullet BEFORE the inline pass, not rendered separately: cloud_storage's
            # contract wraps a `**bold**` span across the break, and rendering line by
            # line ended the list early and left the asterisks on the page.
            item = [bullet.group(2)]
            index += 1
            while index < len(lines):
                nxt = lines[index]
                if not nxt.strip() or not nxt[:1].isspace():
                    break
                if _BULLET.match(nxt) or _ORDERED.match(nxt) or _RULE.match(nxt) \
                        or nxt.strip().startswith(("```", "|", "#")):
                    break
                item.append(nxt.strip())
                index += 1
            out.append(f"<li{css}>{_inline(' '.join(item))}</li>")
            continue

        if not line.strip():
            close_list()
            index += 1
            continue

        close_list()
        paragraph = [line]
        index += 1
        while (
            index < len(lines)
            and lines[index].strip()
            and not lines[index].strip().startswith(("#", "-", "*", "|", "```"))
            and not _ORDERED.match(lines[index])
        ):
            paragraph.append(lines[index])
            index += 1
        out.append(f"<p>{_inline(' '.join(l.strip() for l in paragraph))}</p>")

    close_list()
    return "\n".join(out)
