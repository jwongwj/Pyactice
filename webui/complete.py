"""Python code intelligence for the practice editor.

Completions and signature help derived from the candidate's actual code, not from
matching words in the buffer. The buffer is parsed with `ast` and **never
executed** -- the only things that get imported are standard-library modules the
candidate has explicitly imported, checked against `sys.stdlib_module_names`.

What it understands:

  * the class under construction: its methods (with real signatures and
    docstrings) and the attributes assigned to `self` anywhere in it
  * the enclosing function: its parameters and its local variables
  * literal types, so `self.files = {}` makes `self.files.` offer dict methods
    and not list ones
  * builtins, keywords, and members of imported standard-library modules
  * which parameter you are currently typing, for the signature hint

Deliberately, completions are computed from the buffer alone. Nothing is sourced
from the problem's method table, so a locked level's operations cannot appear in
the list however the rest of the rig changes.
"""

from __future__ import annotations

import ast
import builtins
import importlib
import inspect
import keyword
import sys
from typing import Any

_STDLIB = getattr(sys, "stdlib_module_names", frozenset())

_LITERAL_CALLS = {
    "dict": dict, "list": list, "set": set, "tuple": tuple,
    "str": str, "int": int, "float": float, "bool": bool,
    "frozenset": frozenset, "bytearray": bytearray, "sorted": list,
}


# ---------------------------------------------------------------------------
# parsing


def _safe_parse(code: str, line: int) -> ast.AST | None:
    """Parse the buffer, tolerating the half-typed line the cursor sits on."""
    try:
        return ast.parse(code)
    except SyntaxError:
        pass
    lines = code.splitlines()
    if 0 < line <= len(lines):
        original = lines[line - 1]
        indent = original[: len(original) - len(original.lstrip())]
        # Blanking the line outright leaves `def f():` with no body, which is a
        # fresh SyntaxError -- so stand a `pass` in its place at the same indent.
        for filler in (indent + "pass", indent + "pass  # ", ""):
            lines[line - 1] = filler
            try:
                return ast.parse("\n".join(lines))
            except SyntaxError:
                continue
        lines[line - 1] = original

    head = lines[: max(0, line - 1)]
    while head:
        try:
            return ast.parse("\n".join(head))
        except SyntaxError:
            last = head[-1]
            indent = last[: len(last) - len(last.lstrip())]
            try:
                return ast.parse("\n".join(head + [indent + "    pass"]))
            except SyntaxError:
                head = head[:-1]
    return None


def _contains(node: ast.AST, line: int) -> bool:
    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", None)
    return start is not None and end is not None and start <= line <= end


def _enclosing(tree: ast.AST, line: int):
    """The innermost class and function containing `line`."""
    found_class = found_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and _contains(node, line):
            found_class = node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _contains(node, line):
            if found_func is None or node.lineno > found_func.lineno:
                found_func = node
    return found_class, found_func


# ---------------------------------------------------------------------------
# types


def _infer(node: ast.AST | None) -> type | None:
    if node is None:
        return None
    if isinstance(node, ast.Dict) or isinstance(node, ast.DictComp):
        return dict
    if isinstance(node, ast.List) or isinstance(node, ast.ListComp):
        return list
    if isinstance(node, ast.Set) or isinstance(node, ast.SetComp):
        return set
    if isinstance(node, ast.Tuple):
        return tuple
    if isinstance(node, ast.JoinedStr):
        return str
    if isinstance(node, ast.Constant) and node.value is not None:
        return type(node.value)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return _LITERAL_CALLS.get(node.func.id)
    if isinstance(node, ast.BinOp):
        return _infer(node.left) or _infer(node.right)
    return None


def _annotation_type(node: ast.AST | None) -> type | None:
    if node is None:
        return None
    try:
        text = ast.unparse(node)
    except Exception:
        return None
    head = text.split("|")[0].split("[")[0].strip()
    return _LITERAL_CALLS.get(head)


# ---------------------------------------------------------------------------
# rendering


def _signature(fn: ast.FunctionDef, *, drop_self: bool) -> str:
    args = fn.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults: list[Any] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parts: list[str] = []
    for index, (arg, default) in enumerate(zip(positional, defaults)):
        if drop_self and index == 0 and arg.arg in ("self", "cls"):
            continue
        piece = arg.arg
        if arg.annotation is not None:
            piece += f": {ast.unparse(arg.annotation)}"
        if default is not None:
            piece += f" = {ast.unparse(default)}"
        parts.append(piece)
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        piece = arg.arg
        if default is not None:
            piece += f" = {ast.unparse(default)}"
        parts.append(piece)
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    rendered = f"({', '.join(parts)})"
    if fn.returns is not None:
        rendered += f" -> {ast.unparse(fn.returns)}"
    return rendered


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    for line in text.strip().splitlines():
        if line.strip():
            return line.strip()[:120]
    return ""


def _member_entry(owner: Any, name: str, kind: str) -> dict:
    detail, doc = "", ""
    try:
        attribute = getattr(owner, name)
        doc = _first_line(inspect.getdoc(attribute))
        if callable(attribute):
            try:
                detail = str(inspect.signature(attribute))
            except (ValueError, TypeError):
                detail = "(...)"
    except Exception:
        pass
    return {"name": name, "kind": kind, "detail": detail, "doc": doc}


def _members(owner: Any, kind: str, want_private: bool) -> list[dict]:
    out = []
    for name in dir(owner):
        if name.startswith("_") and not want_private:
            continue
        out.append(_member_entry(owner, name, kind))
    return out


# ---------------------------------------------------------------------------
# scope


class Scope:
    def __init__(self, tree: ast.AST | None, line: int):
        self.methods: dict[str, ast.FunctionDef] = {}
        self.self_attrs: dict[str, type | None] = {}
        self.locals: dict[str, type | None] = {}
        self.module: dict[str, str] = {}      # name -> kind
        self.imports: dict[str, str] = {}     # local name -> module name
        self.class_node = self.func_node = None
        if tree is None:
            return

        self.class_node, self.func_node = _enclosing(tree, line)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports[alias.asname or alias.name.split(".")[0]] = alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    self.imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"

        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.module[node.name] = "function"
            elif isinstance(node, ast.ClassDef):
                self.module[node.name] = "class"
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.module[target.id] = "variable"

        if self.class_node is not None:
            for node in self.class_node.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.methods[node.name] = node
            for node in ast.walk(self.class_node):
                target = None
                if isinstance(node, ast.Assign):
                    target, value = node.targets[0] if node.targets else None, node.value
                elif isinstance(node, ast.AnnAssign):
                    target, value = node.target, node.value
                else:
                    continue
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    inferred = _infer(value)
                    if inferred is None and isinstance(node, ast.AnnAssign):
                        inferred = _annotation_type(node.annotation)
                    # First assignment wins unless a later one knows the type.
                    if target.attr not in self.self_attrs or inferred is not None:
                        self.self_attrs[target.attr] = inferred

        if self.func_node is not None:
            arguments = self.func_node.args
            for arg in list(arguments.posonlyargs) + list(arguments.args) + list(arguments.kwonlyargs):
                self.locals[arg.arg] = _annotation_type(arg.annotation)
            for node in ast.walk(self.func_node):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.locals[target.id] = _infer(node.value)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    self.locals[node.target.id] = _infer(node.value) or _annotation_type(node.annotation)
                elif isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                    self.locals.setdefault(node.target.id, None)
                elif isinstance(node, (ast.With, ast.AsyncWith)):
                    for item in node.items:
                        if isinstance(item.optional_vars, ast.Name):
                            self.locals.setdefault(item.optional_vars.id, None)

    def module_object(self, name: str):
        """Import an explicitly-imported standard-library module, nothing else."""
        dotted = self.imports.get(name)
        if not dotted:
            return None
        root = dotted.split(".")[0]
        if root not in _STDLIB:
            return None
        try:
            return importlib.import_module(dotted)
        except Exception:
            try:
                return importlib.import_module(root)
            except Exception:
                return None

    def resolve(self, expression: str):
        """What type is this dotted expression? Returns a type, module, or None."""
        parts = expression.split(".")
        head, rest = parts[0], parts[1:]

        current: Any = None
        if head == "self":
            if not rest:
                return "self"
            attr = rest[0]
            if attr in self.methods:
                return None
            current = self.self_attrs.get(attr)
            rest = rest[1:]
        elif head in self.locals:
            current = self.locals[head]
            rest = rest[1:]
        elif head in self.imports:
            current = self.module_object(head)
            rest = rest[1:]
        elif hasattr(builtins, head):
            current = getattr(builtins, head)
            rest = rest[1:]
        else:
            return None

        for step in rest:
            if current is None:
                return None
            try:
                current = getattr(current, step)
            except Exception:
                return None
        return current


# ---------------------------------------------------------------------------
# the cursor


def _line_prefix(code: str, line: int, col: int) -> str:
    lines = code.splitlines()
    if not (0 < line <= len(lines)):
        return ""
    return lines[line - 1][:col]


def _split_target(prefix: str) -> tuple[str, str]:
    """Return (dotted base, partial word) for the text before the cursor."""
    index = len(prefix)
    while index > 0 and (prefix[index - 1].isalnum() or prefix[index - 1] == "_"):
        index -= 1
    word = prefix[index:]
    if index > 0 and prefix[index - 1] == ".":
        base_end = index - 1
        start = base_end
        while start > 0 and (prefix[start - 1].isalnum() or prefix[start - 1] in "._"):
            start -= 1
        return prefix[start:base_end], word
    return "", word


def _open_call(prefix: str) -> tuple[str, int] | None:
    """The innermost unclosed call before the cursor: (callee, active parameter)."""
    depth = 0
    commas = 0
    index = len(prefix) - 1
    quote = None
    while index >= 0:
        char = prefix[index]
        if quote:
            if char == quote and (index == 0 or prefix[index - 1] != "\\"):
                quote = None
            index -= 1
            continue
        if char in "\"'":
            quote = char
        elif char in ")]}":
            depth += 1
        elif char == "(":
            if depth == 0:
                end = index
                start = end
                while start > 0 and (prefix[start - 1].isalnum() or prefix[start - 1] in "._"):
                    start -= 1
                callee = prefix[start:end]
                return (callee, commas) if callee else None
            depth -= 1
        elif char in "[{":
            depth -= 1
        elif char == "," and depth == 0:
            commas += 1
        index -= 1
    return None


# ---------------------------------------------------------------------------
# public entry point


def analyse(code: str, line: int, col: int) -> dict:
    tree = _safe_parse(code, line)
    scope = Scope(tree, line)
    prefix = _line_prefix(code, line, col)
    base, word = _split_target(prefix)
    want_private = word.startswith("_")
    items: list[dict] = []

    if base:
        resolved = scope.resolve(base)
        if resolved == "self":
            for name, node in scope.methods.items():
                items.append({
                    "name": name, "kind": "method",
                    "detail": _signature(node, drop_self=True),
                    "doc": _first_line(ast.get_docstring(node)),
                })
            for name, kind in scope.self_attrs.items():
                items.append({
                    "name": name, "kind": "attribute",
                    "detail": kind.__name__ if kind else "", "doc": "",
                })
        elif inspect.ismodule(resolved):
            items = _members(resolved, "module", want_private)
        elif isinstance(resolved, type):
            items = _members(resolved, resolved.__name__, want_private)
        elif resolved is not None:
            items = _members(type(resolved), type(resolved).__name__, want_private)
    else:
        for name, node in scope.methods.items():
            items.append({
                "name": name, "kind": "method",
                "detail": _signature(node, drop_self=True),
                "doc": _first_line(ast.get_docstring(node)),
            })
        for name, kind in scope.locals.items():
            items.append({
                "name": name, "kind": "local",
                "detail": kind.__name__ if kind else "", "doc": "",
            })
        for name, kind in scope.module.items():
            items.append({"name": name, "kind": kind, "detail": "", "doc": ""})
        for name in scope.imports:
            items.append({"name": name, "kind": "module", "detail": "", "doc": ""})
        for name in keyword.kwlist:
            items.append({"name": name, "kind": "keyword", "detail": "", "doc": ""})
        for name in dir(builtins):
            if name.startswith("_") and not want_private:
                continue
            items.append(_member_entry(builtins, name, "builtin"))

    seen: set[str] = set()
    filtered: list[dict] = []
    for item in items:
        if not item["name"].startswith(word) or item["name"] in seen:
            continue
        seen.add(item["name"])
        filtered.append(item)

    order = {"attribute": 0, "method": 0, "local": 1, "function": 2, "class": 2,
             "module": 3, "keyword": 4, "builtin": 5}
    filtered.sort(key=lambda entry: (order.get(entry["kind"], 3), entry["name"]))

    return {
        "completions": filtered[:200],
        "signature": _signature_help(scope, prefix),
        "word": word,
    }


def _signature_help(scope: Scope, prefix: str) -> dict | None:
    call = _open_call(prefix)
    if not call:
        return None
    callee, active = call

    if callee.startswith("self."):
        node = scope.methods.get(callee[len("self."):])
        if node is not None:
            return {
                "label": f"{callee}{_signature(node, drop_self=True)}",
                "active": active,
                "doc": _first_line(ast.get_docstring(node)),
            }
        return None

    target = scope.resolve(callee) if "." in callee else None
    if target is None and "." not in callee:
        if callee in scope.methods:
            node = scope.methods[callee]
            return {"label": f"{callee}{_signature(node, drop_self=False)}",
                    "active": active, "doc": _first_line(ast.get_docstring(node))}
        target = getattr(builtins, callee, None)
    if target is None or not callable(target):
        return None
    try:
        label = f"{callee}{inspect.signature(target)}"
    except (ValueError, TypeError):
        label = f"{callee}(...)"
    return {"label": label, "active": active, "doc": _first_line(inspect.getdoc(target))}
