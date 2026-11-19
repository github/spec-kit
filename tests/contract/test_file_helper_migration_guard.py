"""Tests for the FileHelper migration I/O guard."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".github" / "scripts" / "check_file_helper_migration.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("file_helper_migration_guard", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load migration guard")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = load_guard()


@pytest.mark.parametrize("expression", ["stack.resolve(bundle_id)", "cached_at.replace(tzinfo=timezone.utc)"])
def test_guard_ignores_non_filesystem_method_names(expression):
    assert guard.scan_added_calls(expression, "src/specify_cli/domain.py", {1}) == []


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ("import os\nos.access(path, os.R_OK)", "os.access"),
        ("from os import chdir as set_directory\nset_directory(path)", "os.chdir"),
        ("import os as fs\nfs.utime(path, None)", "os.utime"),
        ("from os import path as fs_path\nfs_path.getsize(path)", "os.path.getsize"),
        ("import os\nos.path.samefile(path, other)", "os.path.samefile"),
        ("from os.path import samefile as same\nsame(path, other)", "os.path.samefile"),
        ("from pathlib import Path\nPath(path).readlink()", "file-path.readlink"),
        ("from pathlib import Path as LocalPath\nLocalPath(path).samefile(other)", "file-path.samefile"),
        ("from pathlib import Path\nPath(path).hardlink_to(other)", "file-path.hardlink_to"),
        ("from pathlib import Path\nPath(path).owner()", "file-path.owner"),
        ("from pathlib import Path\nPath(path).group()", "file-path.group"),
        ("from pathlib import Path\nPath(path).is_mount()", "file-path.is_mount"),
        ("from pathlib import Path\nPath(path).walk()", "file-path.walk"),
        ("import glob\nglob.glob(pattern)", "glob.glob"),
        ("from glob import iglob as scan\nscan(pattern)", "glob.iglob"),
        ("import os\nos.removedirs(path)", "os.removedirs"),
        ("import os\nos.renames(path, other)", "os.renames"),
        ("import os\nos.fwalk(path)", "os.fwalk"),
        ("import shutil\nshutil.make_archive(path, 'zip')", "shutil.make_archive"),
        ("import shutil\nshutil.unpack_archive(path)", "shutil.unpack_archive"),
        ("import os\nos.path.getatime(path)", "os.path.getatime"),
        ("import os\nos.path.getctime(path)", "os.path.getctime"),
        ("import os\nos.path.getmtime(path)", "os.path.getmtime"),
    ],
)
def test_guard_detects_filesystem_probes_and_mutations(statement, expected):
    assert guard.scan_added_calls(statement, "src/specify_cli/domain.py", {2}) == [(2, expected)]


def test_guard_evaluates_lambda_defaults_before_masking_body_parameters():
    source = """from pathlib import Path
path = Path('manifest')
callback = lambda open, path=path.read_text(), /: (open('value'), path.replace('a', 'b'))
callback = lambda *, open=open('manifest'): open('value')
path.exists()
open('manifest')
"""
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {3, 4, 5, 6}) == [
        (3, "file-path.read_text"), (4, "open"), (5, "file-path.exists"), (6, "open"),
    ]


def test_guard_uses_class_scope_for_method_signatures_but_not_bodies():
    source = """from pathlib import Path
class Reader:
    LocalPath = Path
    directory = Path('data')
    def open(self):
        pass
    @decorate(directory.exists())
    def read(self, file: LocalPath = directory / 'manifest', handler=open('value')):
        directory.replace('a', 'b')
        return file.read_text(), open('manifest').read()
"""
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {7, 8, 9, 10}) == [
        (7, "file-path.exists"), (10, "file-path.read_text"), (10, "open"),
    ]


@pytest.mark.parametrize("method", ["read_text", "exists"])
def test_guard_tracks_expanded_paths(method):
    source = f"from pathlib import Path\nPath('~/manifest').expanduser().{method}()\n"
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {2}) == [(2, f"file-path.{method}")]


@pytest.mark.parametrize("annotation", ["", ": str"])
def test_guard_visits_assignment_target(annotation):
    source = f"from pathlib import Path\ncache[Path('manifest').read_text()]{annotation} = value\n"
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {2}) == [(2, "file-path.read_text")]


@pytest.mark.parametrize("iterator", ["iterdir()", "glob('*')", "rglob('*')"])
def test_guard_tracks_path_iteration_targets(iterator):
    source = (
        "from pathlib import Path\n"
        "def read(root: Path, files):\n"
        f"    for child in root.{iterator}:\n"
        "        child.read_text()\n"
        f"    for child in files.{iterator}:\n"
        "        child.read_text()\n"
    )
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {4, 6}) == [(4, "file-path.read_text")]


@pytest.mark.parametrize(
    "expression",
    ["[{value} {clauses}]", "{{{value} {clauses}}}", "{{{value}: 1 {clauses}}}", "({value} {clauses})"],
)
def test_guard_tracks_comprehension_bindings_and_restores_outer_scope(expression):
    source = (
        "from pathlib import Path\n"
        "def scan(root: Path, child: Path):\n"
        "    scoped = " + expression.format(
            value="entry.read_text()", clauses="for directory in root.iterdir() for entry in directory.glob('*') if entry.is_file()"
        ) + "\n"
        "    shadowed = " + expression.format(value="child.replace('a', 'b')", clauses="for child in ['a']") + "\n"
        "    return child.read_text()\n"
    )
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {3, 4, 5}) == [
        (3, "file-path.glob"), (3, "file-path.is_file"), (3, "file-path.iterdir"),
        (3, "file-path.read_text"), (5, "file-path.read_text"),
    ]


def test_guard_does_not_infer_paths_from_shadowed_sorted():
    source = (
        "from pathlib import Path\n"
        "def scan(root: Path, sorted):\n"
        "    for child in sorted(root.iterdir()):\n"
        "        child.replace('a', 'b')\n"
    )
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {4}) == []


def test_guard_tracks_constructor_paths_across_methods():
    source = (
        "from pathlib import Path\n"
        "class Resolver:\n"
        "    def scan(self):\n"
        "        return self.directory.exists(), self.label.replace('a', 'b')\n"
        "    def __init__(instance, root: Path):\n"
        "        instance.directory = root / 'templates'\n"
        "        instance.label = 'a'\n"
        "class Other:\n"
        "    def scan(self):\n"
        "        return self.directory.replace('a', 'b')\n"
    )
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {4, 10}) == [(4, "file-path.exists")]


@pytest.mark.parametrize(
    "source",
    [
        "import tempfile\nwith tempfile.TemporaryFile() as stream:\n    stream.write(b'x')\n",
        "from tempfile import TemporaryFile as staging\nwith staging() as stream:\n    stream.write(b'x')\n",
    ],
)
def test_guard_catches_temporary_file_creation(source):
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {2}) == [
        (2, "tempfile.TemporaryFile")
    ]


@pytest.mark.parametrize("path_first", [False, True])
def test_guard_catches_path_binding_on_either_branch(path_first):
    branches = ["Path(root)", "FileHelper(root)"]
    if not path_first:
        branches.reverse()
    source = f"""from pathlib import Path
from specify_cli.file_helper import FileHelper
def load(root, scoped):
    if scoped:
        owner = {branches[0]}
    else:
        owner = {branches[1]}
    return owner.read_text("manifest")
"""
    assert guard.scan_added_calls(source, "src/specify_cli/domain.py", {8}) == [
        (8, "file-path.read_text")
    ]


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def init_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    (repo / "src" / "specify_cli").mkdir(parents=True)
    run_git(repo, "init", "-q")
    base_file = repo / "src" / "specify_cli" / "domain.py"
    base_file.write_text(
        "from pathlib import Path\n"
        "def existing():\n"
        "    return Path('existing.txt').read_text()\n",
        encoding="utf-8",
    )
    run_git(repo, "add", ".")
    base = run_git(repo, "write-tree").strip()
    return repo, base


def test_guard_checks_new_io_under_unchanged_sorted_loop(tmp_path):
    repo, _ = init_repo(tmp_path)
    path = "src/specify_cli/domain.py"
    loop = "from pathlib import Path\ndef scan(root: Path):\n    for child in sorted(root.iterdir()):\n"
    revisions = []
    for body in ("        pass\n", "        child.read_text()\n"):
        (repo / path).write_text(loop + body, encoding="utf-8")
        run_git(repo, "add", path)
        revisions.append(run_git(repo, "write-tree").strip())
    assert guard.check(repo, *revisions) == [(path, 4, "file-path.read_text")]


@pytest.mark.parametrize("kind", ["unchanged", "new-io", "from-exempt"])
def test_guard_checks_renames_without_losing_following_record(tmp_path, kind):
    repo, _ = init_repo(tmp_path)
    prefix = "src/specify_cli/"
    old = prefix + ("_file_handles.py" if kind == "from-exempt" else "original.py")
    new = prefix + "renamed.py"
    source = "open('legacy')\n" + "\n".join(f"# padding line {i}" for i in range(10)) + "\n"
    (repo / old).write_text(source, encoding="utf-8")
    run_git(repo, "add", old)
    base = run_git(repo, "write-tree").strip()
    (repo / old).rename(repo / new)
    if kind == "new-io":
        (repo / new).write_text(source + "open('new')\n", encoding="utf-8")
    following = prefix + "zzz.py"
    (repo / following).write_text("open('following')\n", encoding="utf-8")
    run_git(repo, "add", "-A")
    head = run_git(repo, "write-tree").strip()
    assert f"\0{old}\0{new}\0A\0{following}\0" in run_git(
        repo, "diff", "--name-status", "--find-renames", "-z", base, head
    )
    expected = {"unchanged": [], "new-io": [(new, 12, "open")], "from-exempt": [(new, 1, "open")]}
    assert guard.check(repo, base, head) == [*expected[kind], (following, 1, "open")]


def test_guard_checks_direct_io_in_integration_state():
    assert guard.scan_added_calls(
        "open('state')\n", "src/specify_cli/integration_state.py", {1}
    ) == [(1, "open")]


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        ("FileHelper(root)", "Path(root)", [(6, "file-path.read_text")]),
        ("Path(root)", "FileHelper(root)", []),
        ("Path(root)", "Path(other)", []),
    ],
)
def test_guard_checks_reclassification_of_unchanged_calls(tmp_path, before, after, expected):
    repo, _ = init_repo(tmp_path)
    path = "src/specify_cli/domain.py"
    source = (
        "from pathlib import Path\n"
        "from specify_cli.file_helper import FileHelper\n\n"
        "def load(root, other):\n"
        "    owner = {binding}\n"
        "    return owner.read_text('manifest')\n"
    )
    snapshots = []
    for binding in (before, after):
        (repo / path).write_text(source.format(binding=binding), encoding="utf-8")
        run_git(repo, "add", path)
        snapshots.append(run_git(repo, "write-tree").strip())
    assert guard.check(repo, *snapshots) == [(path, line, label) for line, label in expected]


def test_guard_detects_new_path_and_builtin_open_calls():
    source = """from pathlib import Path
def migrate():
    Path("a.txt").read_text()
    open("b.txt", "w").write("x")
"""
    violations = guard.scan_added_calls(source, "src/specify_cli/domain.py", {3, 4})
    labels = {label for _, label in violations}
    assert "file-path.read_text" in labels
    assert "open" in labels


def test_guard_detects_os_shutil_tempfile_and_alias_calls():
    source = """import os as filesystem
import shutil as shell_io
import tempfile
from os import unlink as remove_entry

filesystem.unlink("a")
shell_io.rmtree("b")
tempfile.TemporaryDirectory()
remove_entry("c")
"""
    violations = guard.scan_added_calls(
        source, "src/specify_cli/domain.py", {6, 7, 8, 9}
    )
    labels = {label for _, label in violations}
    assert labels == {
        "os.unlink",
        "shutil.rmtree",
        "tempfile.TemporaryDirectory",
    }


def test_guard_distinguishes_filehelper_handoffs_from_direct_path_io():
    source = """from contextlib import ExitStack
from pathlib import Path
from ..file_helper import FileHelper as ScopedFiles
from .._file_policy import project_files as policy_files
from .._project import resolve_specify_project_files

class Consumer:
    def __init__(self, owner: ScopedFiles | None):
        self.owner = owner

    def read(self):
        return self.owner.read_text("directly scoped")

def migrate(root: Path, incoming: "ScopedFiles"):
    incoming.write_bytes("incoming", b"x")
    ScopedFiles(root).read_bytes("inline")
    with policy_files(root) as scoped:
        scoped.write_text("managed", "x")
        scoped = root / "plain"
        scoped.read_text()
    with ExitStack() as owners:
        managed = owners.enter_context(resolve_specify_project_files())
        managed.read_text("current")
        Path.write_bytes(root / "direct", b"x")
"""
    assert guard.scan_added_calls(
        source, "src/specify_cli/workflows/domain.py", range(1, 26)
    ) == [(20, "file-path.read_text"), (24, "file-path.write_bytes")]


def test_guard_ignores_safe_operations_without_allowing_multiline_path_io():
    source = """from pathlib import Path as LocalPath

def migrate(root: LocalPath, stack, text: str, open):
    open("custom callback")
    text.replace(old="a", new="b")
    text.replace("a", "b").replace("c", "d")
    stack.resolve("version")
    LocalPath("dir") / "assigned"
    root.parent.replace(target="staged")
    root.write_text(
        "new text",
    )
"""
    assert guard.scan_added_calls(
        source, "src/specify_cli/domain.py", {*range(4, 10), 11}
    ) == [(9, "file-path.replace"), (10, "file-path.write_text")]


def test_guard_ignores_allowlisted_low_level_module():
    source = 'open("a.txt", "w").write("x")\n'
    assert guard.scan_added_calls(
        source, "src/specify_cli/file_helper.py", {1}
    ) == []


def test_guard_ignores_comments_strings_and_unadded_lines():
    source = """from pathlib import Path
def migrate():
    # open("comment.txt", "w")
    text = 'Path("string").write_text("x")'
    Path("added.txt").write_text("x")
"""
    assert guard.scan_added_calls(
        source, "src/specify_cli/domain.py", {3, 4}
    ) == []
    assert len(guard.scan_added_calls(
        source, "src/specify_cli/domain.py", {5}
    )) == 1


def test_guard_check_rejects_direct_io_in_new_domain_diff(tmp_path):
    repo, base = init_repo(tmp_path)
    domain = repo / "src" / "specify_cli" / "domain.py"
    domain.write_text(
        "from pathlib import Path\n"
        "def existing():\n"
        "    return 1\n"
        "\n"
        "def migrate():\n"
        "    Path('new.txt').read_text()\n",
        encoding="utf-8",
    )
    run_git(repo, "add", ".")
    head = run_git(repo, "write-tree").strip()

    violations = guard.check(repo, base, head)
    assert [(path, line, qualified) for path, line, qualified in violations] == [
        ("src/specify_cli/domain.py", 6, "file-path.read_text")
    ]


def test_guard_check_ignores_unchanged_io_and_allowlisted_change(tmp_path):
    repo, base = init_repo(tmp_path)
    domain = repo / "src" / "specify_cli" / "domain.py"
    domain.write_text(
        "from pathlib import Path\n"
        "# Moving the existing call down must not count as new I/O.\n"
        "def existing():\n"
        "    return Path('existing.txt').read_text()\n",
        encoding="utf-8",
    )
    low_level = repo / "src" / "specify_cli" / "file_helper.py"
    low_level.write_text(
        "def primitive():\n"
        "    open('primitive.tmp', 'w').write('x')\n",
        encoding="utf-8",
    )
    run_git(repo, "add", ".")
    head = run_git(repo, "write-tree").strip()

    assert guard.check(repo, base, head) == []


def test_guard_checks_new_file_with_non_ascii_path(tmp_path, monkeypatch):
    repo, base = init_repo(tmp_path)
    path = "src/specify_cli/caf\u00e9.py"
    (repo / path).write_text("open('caf\u00e9')\n", encoding="utf-8")
    run_git(repo, "add", path)
    head = run_git(repo, "write-tree").strip()

    def run_with_ascii_default(*args, **kwargs):
        kwargs.setdefault("encoding", "ascii")
        return real_run(*args, **kwargs)

    real_run = subprocess.run
    with monkeypatch.context() as patch:
        patch.setattr(guard.subprocess, "run", run_with_ascii_default)
        assert guard.check(repo, base, head) == [(path, 1, "open")]


@pytest.mark.skipif(os.name == "nt" or shutil.which("bash") is None, reason="Lint runs in Bash on Linux")
@pytest.mark.parametrize("event", ["pull_request", "push"])
def test_lint_step_uses_correct_base_when_main_has_drifted(tmp_path, event):
    repo, tree = init_repo(tmp_path)
    run_git(repo, "config", "user.name", "Guard Test")
    run_git(repo, "config", "user.email", "guard@example.invalid")
    ancestor = run_git(repo, "commit-tree", tree, "-m", "Ancestor with legacy I/O").strip()
    (repo / "unrelated.txt").write_text("PR change\n", encoding="utf-8")
    run_git(repo, "add", "unrelated.txt")
    pr_tree = run_git(repo, "write-tree").strip()
    pr_head = run_git(repo, "commit-tree", pr_tree, "-p", ancestor, "-m", "Unrelated PR").strip()
    run_git(repo, "read-tree", "--reset", "-u", tree)
    path = repo / "src/specify_cli/domain.py"
    path.write_text("def existing():\n    return 'migrated elsewhere'\n", encoding="utf-8")
    run_git(repo, "add", ".")
    base = run_git(repo, "commit-tree", run_git(repo, "write-tree").strip(), "-p", ancestor, "-m", "Migrate main").strip()
    (repo / "unrelated.txt").write_text("PR change\n", encoding="utf-8")
    run_git(repo, "add", ".")
    merged_tree = run_git(repo, "write-tree").strip()
    merge = run_git(repo, "commit-tree", merged_tree, "-p", base, "-p", pr_head, "-m", "Test merge").strip()
    run_git(repo, "checkout", "--detach", merge)
    run_git(repo, "remote", "add", "origin", ".")
    script = repo / SCRIPT.relative_to(REPO)
    script.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPT, script)

    config = yaml.safe_load((REPO / ".github/workflows/lint.yml").read_text(encoding="utf-8"))
    step = next(step for step in config["jobs"]["checks"]["steps"] if step.get("name") == "Check FileHelper migration boundaries")
    env = {
        **os.environ,
        "GITHUB_EVENT_NAME": event,
        "FILE_HELPER_DIFF_BASE": base,
        "FILE_HELPER_DIFF_HEAD": pr_head if event == "pull_request" else merge,
        "PATH": os.pathsep.join((str(Path(sys.executable).parent), os.environ["PATH"])),
    }

    assert guard.check(repo, base, pr_head)
    result = subprocess.run(["bash", "-c", step["run"]], cwd=repo, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    path.write_text("open('new-file')\n", encoding="utf-8")
    run_git(repo, "add", ".")
    introduced = run_git(repo, "commit-tree", run_git(repo, "write-tree").strip(), "-p", base, "-p", pr_head, "-m", "New I/O").strip()
    run_git(repo, "checkout", "--detach", introduced)
    if event == "push":
        env["FILE_HELPER_DIFF_HEAD"] = introduced
    result = subprocess.run(["bash", "-c", step["run"]], cwd=repo, env=env, capture_output=True, text=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "src/specify_cli/domain.py:1: open" in result.stdout
