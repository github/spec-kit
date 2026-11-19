#!/usr/bin/env python3
"""Reject newly added direct source-package filesystem I/O outside low-level boundaries."""

import argparse
import ast
from difflib import SequenceMatcher
from pathlib import Path
import subprocess
import sys
from typing import Iterable


LOW_LEVEL_BOUNDARY_ALLOWLIST = {
    "src/specify_cli/file_helper.py",
    "src/specify_cli/_file_handles.py",
    "src/specify_cli/_file_policy.py",
}

DIRECT_PATH_AND_FILE_METHODS = {
    "chmod",
    "chown",
    "exists",
    "glob",
    "group",
    "hardlink_to",
    "is_dir",
    "is_file",
    "is_mount",
    "is_symlink",
    "iterdir",
    "lstat",
    "mkdir",
    "open",
    "owner",
    "read_bytes",
    "read_text",
    "readlink",
    "rename",
    "replace",
    "resolve",
    "rglob",
    "rmdir",
    "samefile",
    "stat",
    "symlink_to",
    "touch",
    "unlink",
    "walk",
    "write_bytes",
    "write_text",
}

DIRECT_MODULE_FUNCTIONS = {
    "builtins.open",
    "glob.glob",
    "glob.iglob",
    "io.open",
    "os.access",
    "os.chdir",
    "os.chmod",
    "os.chown",
    "os.fdopen",
    "os.fwalk",
    "os.link",
    "os.listdir",
    "os.lstat",
    "os.makedirs",
    "os.mkdir",
    "os.open",
    "os.path.exists",
    "os.path.getatime",
    "os.path.getctime",
    "os.path.getmtime",
    "os.path.getsize",
    "os.path.isfile",
    "os.path.isdir",
    "os.path.islink",
    "os.path.lexists",
    "os.path.realpath",
    "os.path.samefile",
    "os.readlink",
    "os.remove",
    "os.removedirs",
    "os.rename",
    "os.renames",
    "os.replace",
    "os.rmdir",
    "os.scandir",
    "os.stat",
    "os.symlink",
    "os.truncate",
    "os.unlink",
    "os.utime",
    "os.walk",
    "shutil.copy",
    "shutil.copy2",
    "shutil.copyfile",
    "shutil.copymode",
    "shutil.copystat",
    "shutil.copytree",
    "shutil.make_archive",
    "shutil.move",
    "shutil.rmtree",
    "shutil.unpack_archive",
    "tempfile.NamedTemporaryFile",
    "tempfile.SpooledTemporaryFile",
    "tempfile.TemporaryDirectory",
    "tempfile.TemporaryFile",
    "tempfile.mkstemp",
    "tempfile.mkdtemp",
}

ZERO_SHA = "0" * 40
PATH_TYPES = {"pathlib.Path", "pathlib.PosixPath", "pathlib.WindowsPath"}
PATH_RESULTS = {"absolute", "expanduser", "joinpath", "resolve", "with_name", "with_stem", "with_suffix"}
PATH_ITERATORS = {"glob", "iterdir", "rglob"}
PATH_VALUE = ":path"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="surrogateescape",
    ).stdout


def _unchanged_lines(before: str, after: str) -> dict[int, int]:
    matcher = SequenceMatcher(None, before.split("\n"), after.split("\n"), autojunk=False)
    return {
        new + offset + 1: old + offset + 1
        for old, new, size in matcher.get_matching_blocks()
        for offset in range(size)
    }


def _root_name(node: ast.AST) -> str | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


class _Calls(ast.NodeVisitor):
    """Recognize direct module calls and locally traceable pathlib receivers."""

    def __init__(self):
        self.symbols: dict[str, str] = {"open": "open", "sorted": "builtins.sorted"}
        self.calls: list[tuple[int, int, str]] = []

    def _symbol(self, node: ast.AST) -> str:
        name = _root_name(node)
        if name is None:
            return ""
        if name in self.symbols:
            return self.symbols[name]
        first, dot, suffix = name.partition(".")
        symbol = self.symbols.get(first, "")
        return f"{symbol}{dot}{suffix}" if symbol and symbol != PATH_VALUE else ""

    def _annotation(self, node: ast.AST | None) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                node = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return ""
        if node is None:
            return ""
        if self._symbol(node) in PATH_TYPES:
            return PATH_VALUE
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return self._annotation(node.left) or self._annotation(node.right)
        if isinstance(node, ast.Subscript) and self._symbol(node.value) == "typing.Optional":
            return self._annotation(node.slice)
        return ""

    def _value(self, node: ast.AST) -> str:
        if isinstance(node, ast.Call):
            symbol = self._symbol(node.func)
            owner, _, method = symbol.rpartition(".")
            if symbol in PATH_TYPES or owner in PATH_TYPES and method in {"cwd", "home"}:
                return PATH_VALUE
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in PATH_RESULTS
                and self._value(node.func.value) == PATH_VALUE
            ):
                return PATH_VALUE
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return PATH_VALUE if PATH_VALUE in (self._value(node.left), self._value(node.right)) else ""
        if isinstance(node, ast.IfExp):
            return PATH_VALUE if PATH_VALUE in (self._value(node.body), self._value(node.orelse)) else ""
        if isinstance(node, ast.Attribute) and node.attr == "parent" and self._value(node.value) == PATH_VALUE:
            return PATH_VALUE
        return self._symbol(node)

    def _bind(self, target: ast.AST, symbol: str) -> None:
        if isinstance(target, (ast.List, ast.Tuple)):
            for item in target.elts:
                self._bind(item, "")
            return
        if isinstance(target, ast.Starred):
            self._bind(target.value, "")
            return
        name = _root_name(target)
        if name is not None:
            self.symbols[name] = symbol

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            first = alias.name.split(".", 1)[0]
            self.symbols[alias.asname or first] = alias.name if alias.asname else first

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.symbols[alias.asname or alias.name] = (
                f"{node.module}.{alias.name}" if not node.level and node.module else ""
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        symbol = self._value(node.value)
        for target in node.targets:
            self.visit(target)
            self._bind(target, symbol)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
        self.visit(node.target)
        value = self._value(node.value) if node.value is not None else ""
        self._bind(node.target, value or self._annotation(node.annotation))

    def _element(self, iterator: ast.AST) -> str:
        if not isinstance(iterator, ast.Call):
            return ""
        if self._symbol(iterator.func) == "builtins.sorted" and iterator.args:
            return self._element(iterator.args[0])
        if (
            isinstance(iterator.func, ast.Attribute)
            and iterator.func.attr in PATH_ITERATORS
            and self._value(iterator.func.value) == PATH_VALUE
        ):
            return PATH_VALUE
        return ""

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self.visit(node.target)
        original = self.symbols.copy()
        self._bind(node.target, self._element(node.iter))
        for statement in node.body:
            self.visit(statement)
        self._merge_symbols(original)
        for statement in node.orelse:
            self.visit(statement)

    def _visit_comprehension(self, generators: list[ast.comprehension], *results: ast.expr) -> None:
        outer = self.symbols
        self.symbols = outer.copy()
        for generator in generators:
            self.visit(generator.iter)
            self.visit(generator.target)
            self._bind(generator.target, self._element(generator.iter))
            for condition in generator.ifs:
                self.visit(condition)
        for result in results:
            self.visit(result)
        self.symbols = outer

    def visit_ListComp(self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp) -> None:
        self._visit_comprehension(node.generators, node.elt)

    visit_SetComp = visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension(node.generators, node.key, node.value)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        original = self.symbols.copy()
        for statement in node.body:
            self.visit(statement)
        body = self.symbols
        self.symbols = original
        for statement in node.orelse:
            self.visit(statement)
        self._merge_symbols(body)

    def _merge_symbols(self, other: dict[str, str]) -> None:
        for name in other.keys() | self.symbols.keys():
            left, right = other.get(name, ""), self.symbols.get(name, "")
            self.symbols[name] = left if left == right else PATH_VALUE if PATH_VALUE in (left, right) else ""

    def visit_With(self, node: ast.With | ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._bind(item.optional_vars, self._value(item.context_expr))
        for statement in node.body:
            self.visit(statement)

    visit_AsyncWith = visit_With

    def _parameters(self, args: ast.arguments) -> dict[str, str]:
        for expression in [*args.defaults, *args.kw_defaults]:
            if expression is not None:
                self.visit(expression)
        bindings = {}
        for argument in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]:
            if argument is not None:
                if argument.annotation is not None:
                    self.visit(argument.annotation)
                bindings[argument.arg] = self._annotation(argument.annotation)
        return bindings

    def visit_Lambda(self, node: ast.Lambda) -> None:
        parameters = self._parameters(node.args)
        outer = self.symbols
        self.symbols = outer | parameters
        self.visit(node.body)
        self.symbols = outer

    def _signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        for decorator in node.decorator_list:
            self.visit(decorator)
        parameters = self._parameters(node.args)
        if node.returns is not None:
            self.visit(node.returns)
        return parameters

    def _visit_function_body(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, parameters: dict[str, str],
        attributes: tuple[str, ...] = (),
    ) -> tuple[str, ...]:
        outer = self.symbols
        self.symbols = outer | parameters
        positional = node.args.posonlyargs + node.args.args
        receiver = ""
        if positional and not any(
            _root_name(decorator) in {"staticmethod", "classmethod", "builtins.staticmethod", "builtins.classmethod"}
            for decorator in node.decorator_list
        ):
            receiver = positional[0].arg + "."
            self.symbols.update({receiver + name: PATH_VALUE for name in attributes})
        for statement in node.body:
            self.visit(statement)
        known_paths = tuple(
            name.removeprefix(receiver) for name, kind in self.symbols.items()
            if receiver and name.startswith(receiver) and kind == PATH_VALUE
        ) if node.name == "__init__" else ()
        self.symbols = outer
        return known_paths

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        parameters = self._signature(node)
        self.symbols[node.name] = ""
        self._visit_function_body(node, parameters)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        outer = self.symbols
        for expression in [*node.decorator_list, *node.bases, *node.keywords]:
            self.visit(expression)
        self.symbols = outer.copy()
        methods = []
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append((statement, self._signature(statement)))
                self.symbols[statement.name] = ""
            else:
                self.visit(statement)
        self.symbols = outer
        outer[node.name] = ""
        attributes: tuple[str, ...] = ()
        for method, parameters in methods:
            if method.name == "__init__":
                attributes = self._visit_function_body(method, parameters)
        for method, parameters in methods:
            if method.name != "__init__":
                self._visit_function_body(method, parameters, attributes)

    def visit_Call(self, call: ast.Call) -> None:
        symbol = self._symbol(call.func)
        if isinstance(call.func, ast.Attribute) and call.func.attr in DIRECT_PATH_AND_FILE_METHODS:
            if symbol.rpartition(".")[0] in PATH_TYPES or self._value(call.func.value) == PATH_VALUE:
                symbol = f"file-path.{call.func.attr}"
        if symbol == "open" or symbol in DIRECT_MODULE_FUNCTIONS or symbol.startswith("file-path."):
            self.calls.append((call.lineno, call.end_lineno or call.lineno, symbol))
        self.generic_visit(call)


def _scan_calls(source: str, path: str) -> list[tuple[int, int, str]]:
    if path in LOW_LEVEL_BOUNDARY_ALLOWLIST:
        return []
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise RuntimeError(f"Cannot parse changed Python file {path}: {exc}") from exc

    scanner = _Calls()
    scanner.visit(tree)
    return scanner.calls


def scan_added_calls(source: str, path: str, added_lines: Iterable[int]) -> list[tuple[int, str]]:
    selected = set(added_lines)
    return sorted({
        (start, name) for start, end, name in _scan_calls(source, path)
        if selected.intersection(range(start, end + 1))
    })


def check(repo: Path, base: str = "", head: str = "HEAD") -> list[tuple[str, int, str]]:
    if not base or base == ZERO_SHA:
        return []
    changes = _git(
        repo,
        "diff",
        "--name-status",
        "--find-renames",
        "--diff-filter=AMR",
        "-z",
        "--no-ext-diff",
        base,
        head,
        "--",
        "src/specify_cli",
    ).split("\0")
    entries = iter(changes[:-1])
    violations = set()
    for status in entries:
        old_path = path = next(entries)
        if status.startswith("R"):
            path = next(entries)
        if not path.endswith(".py") or path in LOW_LEVEL_BOUNDARY_ALLOWLIST:
            continue
        after = _git(repo, "show", f"{head}:{path}")
        before = (
            "" if status == "A" or not old_path.endswith(".py")
            else _git(repo, "show", f"{base}:{old_path}")
        )
        unchanged = _unchanged_lines(before, after)
        old_calls = set(_scan_calls(before, old_path))
        for start, end, name in _scan_calls(after, path):
            old_start = unchanged.get(start, 0)
            old_end = old_start + end - start
            if (old_start, old_end, name) not in old_calls or any(
                unchanged.get(line) != old_start + line - start for line in range(start, end + 1)
            ):
                violations.add((path, start, name))
    return sorted(violations)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    try:
        violations = check(args.repo.resolve(), args.base, args.head)
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"FileHelper migration guard could not run: {exc}", file=sys.stderr)
        return 2
    if violations:
        print("Direct filesystem I/O added outside the FileHelper migration boundary:")
        for path, line, qualified in violations:
            print(f"  {path}:{line}: {qualified}")
        print(
            "Migrate the operation to FileHelper or extend the documented low-level "
            "boundary explicitly."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
