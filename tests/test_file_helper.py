"""Operation-level evidence for the scoped FileHelper foundation."""

from dataclasses import FrozenInstanceError
import errno
import os
from pathlib import Path, PureWindowsPath
import subprocess
from types import SimpleNamespace

import pytest

from specify_cli.file_helper import (
    FileHelper,
    FileHelperError,
    PathEscapeError,
    SymlinkDeniedError,
    UnsupportedPathError,
)


@pytest.fixture
def root(tmp_path):
    path = tmp_path / "project"
    path.mkdir()
    return path


@pytest.fixture
def link(root):
    """Skip link-specific tests only on hosts unable to create symlinks."""
    probe = root / "probe"
    try:
        probe.symlink_to(root, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    probe.unlink()

    def create(path, target):
        path.symlink_to(target, target_is_directory=Path(target).is_dir())
        return path

    return create


@pytest.mark.parametrize("allow", [False, True])
def test_plain_operations(root, allow):
    files = FileHelper(root, allow_symlinks=allow)
    files.mkdir("nested/child", parents=True)
    files.mkdir("nested/child", exist_ok=True)
    files.create_text("nested/child/text", "caf\u00e9\n")
    assert files.read_text("nested/child/text") == "caf\u00e9\n"
    files.write_text("nested/child/text", "updated")
    assert files.read_bytes(root / "nested/child/text") == b"updated"
    files.write_bytes("nested/child/new", b"\x00\xff")
    assert files.read_bytes("nested/child/new") == b"\x00\xff"
    files.create_bytes("binary", b"\xff", mode=0o600)
    files.delete("binary")
    assert not (root / "binary").exists()
    files.delete("nested", recursive=True)
    assert list(root.iterdir()) == []


@pytest.mark.parametrize("operation", ["read_bytes", "write_bytes", "create_bytes", "mkdir", "delete"])
@pytest.mark.parametrize("kind", ["leaf", "parent", "dangling"])
def test_deny_rejects_accessed_links_without_mutation(root, link, operation, kind):
    target = root / "target"
    target.mkdir()
    (target / "file").write_bytes(b"old")
    if kind == "parent":
        path = link(root / "alias", target) / "file"
    else:
        path = link(root / "alias", target / ("missing" if kind == "dangling" else "file"))
    files = FileHelper(root)
    args = (path, b"new") if operation in ("write_bytes", "create_bytes") else (path,)
    with pytest.raises(SymlinkDeniedError, match="symlink"):
        getattr(files, operation)(*args)
    assert (root / "alias").is_symlink()
    assert (target / "file").read_bytes() == b"old"
    assert not (target / "missing").exists()


def test_allow_read_and_atomic_update_preserve_chain_and_target(root, link, monkeypatch):
    target = root / "target"
    target.write_bytes(b"old")
    first = link(root / "first", "target")
    second = link(root / "second", "first")
    files = FileHelper(root, allow_symlinks=True)
    assert files.read_text(second) == "old"
    replacements = []
    replace = os.replace

    def observe(source, destination):
        replacements.append((Path(source), destination))
        assert first.is_symlink() and second.is_symlink()
        assert target.read_bytes() == b"old"
        replace(source, destination)

    monkeypatch.setattr("specify_cli.file_helper.os.replace", observe)
    files.write_text(second, "new")
    assert len(replacements) == 1
    assert replacements[0][0].parent == target.parent
    assert replacements[0][1] == target
    assert os.readlink(first) == "target"
    assert os.readlink(second) == "first"
    assert target.read_bytes() == b"new"
    assert sorted(p.name for p in root.iterdir()) == ["first", "second", "target"]


def test_allow_operations_through_linked_parent(root, link):
    target = root / "target"
    target.mkdir()
    alias = link(root / "alias", target)
    files = FileHelper(root, allow_symlinks=True)
    files.mkdir(alias / "created/child", parents=True)
    files.create_text(alias / "created/file", "old")
    assert files.read_text(alias / "created/file") == "old"
    files.write_text(alias / "created/file", "new")
    assert (target / "created/file").read_text() == "new"
    files.delete(alias / "created", recursive=True)
    assert alias.is_symlink() and target.is_dir()
    assert list(target.iterdir()) == []


def test_delete_through_parent_link_removes_real_file_not_parent_link(root, link):
    target = root / "target"
    target.mkdir()
    (target / "file").write_text("delete")
    alias = link(root / "alias", target)
    FileHelper(root, allow_symlinks=True).delete(alias / "file")
    assert alias.is_symlink()
    assert target.is_dir()
    assert not (target / "file").exists()


@pytest.mark.parametrize("allow", [False, True])
def test_empty_directory_nonrecursive_delete(root, allow):
    files = FileHelper(root, allow_symlinks=allow)
    files.mkdir("empty")
    files.delete("empty")
    assert not (root / "empty").exists()


@pytest.mark.parametrize("operation", ["mkdir", "create_bytes", "write_bytes", "delete"])
def test_dangling_parent_cannot_be_used_for_mutation(root, link, operation):
    alias = link(root / "alias", root / "missing")
    files = FileHelper(root, allow_symlinks=True)
    path = alias / "child"
    args = (path, b"bad") if operation in ("create_bytes", "write_bytes") else (path,)
    with pytest.raises(FileNotFoundError):
        getattr(files, operation)(*args)
    assert alias.is_symlink()
    assert not (root / "missing").exists()


def test_multi_link_cycle_and_excessive_chain_fail_explicitly(root, link):
    link(root / "first", "second")
    link(root / "second", "first")
    files = FileHelper(root, allow_symlinks=True)
    with pytest.raises(UnsupportedPathError, match="cycle"):
        files.read_bytes("first")
    (root / "target").write_text("ok")
    for index in reversed(range(41)):
        link(root / f"chain-{index}", "target" if index == 40 else f"chain-{index + 1}")
    with pytest.raises(UnsupportedPathError, match="excessive chain"):
        files.read_bytes("chain-0")


@pytest.mark.parametrize("operation", ["read_bytes", "write_bytes", "mkdir", "create_bytes", "delete"])
def test_external_parent_is_never_traversed(root, link, operation):
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"old")
    alias = link(root / "alias", outside)
    files = FileHelper(root, allow_symlinks=True)
    path = alias / "file"
    args = (path, b"new") if operation in ("write_bytes", "create_bytes") else (path,)
    with pytest.raises(PathEscapeError):
        getattr(files, operation)(*args)
    assert (outside / "file").read_bytes() == b"old"
    assert alias.is_symlink()


@pytest.mark.parametrize("kind", ["external", "dangling", "cycle"])
@pytest.mark.parametrize("operation", ["read_bytes", "write_bytes"])
def test_allow_reads_and_updates_reject_invalid_targets(root, link, kind, operation):
    if kind == "external":
        target = root.parent / "outside"
        target.write_bytes(b"old")
        error = PathEscapeError
    elif kind == "dangling":
        target = root / "missing"
        error = FileNotFoundError
    else:
        target = root / "alias"
        error = UnsupportedPathError
    alias = link(root / "alias", target)
    args = (alias, b"new") if operation == "write_bytes" else (alias,)
    with pytest.raises(error):
        getattr(FileHelper(root, allow_symlinks=True), operation)(*args)
    assert alias.is_symlink()
    if kind == "external":
        assert target.read_bytes() == b"old"
    if kind == "dangling":
        assert not target.exists()


@pytest.mark.parametrize("kind", ["file", "directory", "external", "dangling", "cycle"])
@pytest.mark.parametrize("recursive", [False, True])
def test_allow_leaf_delete_unlinks_only_link(root, link, kind, recursive):
    target = root / "target"
    if kind == "file":
        target.write_bytes(b"keep")
    elif kind == "directory":
        target.mkdir()
        (target / "keep").write_bytes(b"keep")
    elif kind == "external":
        target = root.parent / "outside"
        target.write_bytes(b"keep")
    elif kind == "cycle":
        target = root / "alias"
    alias = link(root / "alias", target)
    FileHelper(root, allow_symlinks=True).delete(alias, recursive=recursive)
    assert not os.path.lexists(alias)
    if kind in ("file", "external"):
        assert target.read_bytes() == b"keep"
    elif kind == "directory":
        assert (target / "keep").read_bytes() == b"keep"


def test_recursive_deny_preflight_leaves_entire_tree_untouched(root, link):
    tree = root / "tree"
    tree.mkdir()
    (tree / "a-file").write_bytes(b"keep")
    (tree / "b-dir").mkdir()
    (tree / "b-dir/keep").write_bytes(b"keep")
    alias = link(tree / "z-link", root / "missing")
    with pytest.raises(SymlinkDeniedError):
        FileHelper(root).delete(tree, recursive=True)
    assert (tree / "a-file").read_bytes() == b"keep"
    assert (tree / "b-dir/keep").read_bytes() == b"keep"
    assert alias.is_symlink()


def test_recursive_allow_does_not_descend_through_links(root, link):
    tree = root / "tree"
    tree.mkdir()
    target = root / "retained"
    target.mkdir()
    (target / "keep").write_bytes(b"keep")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "keep").write_bytes(b"keep")
    link(tree / "internal", target)
    link(tree / "external", outside)
    link(tree / "dangling", root / "missing")
    link(tree / "cycle", tree)
    (tree / "ordinary").write_bytes(b"delete")
    FileHelper(root, allow_symlinks=True).delete(tree, recursive=True)
    assert not tree.exists()
    assert (target / "keep").read_bytes() == b"keep"
    assert (outside / "keep").read_bytes() == b"keep"


def test_deletion_rechecks_parents_after_preflight(root, link, monkeypatch):
    tree = root / "tree"
    (tree / "nested").mkdir(parents=True)
    (tree / "nested/file").write_text("keep")
    plan = FileHelper._deletion_plan

    def exchange(self, path, *, recursive):
        result = plan(self, path, recursive=recursive)
        if path == tree:
            (tree / "nested").rename(root / "retained")
            link(tree / "nested", root / "retained")
        return result

    monkeypatch.setattr(FileHelper, "_deletion_plan", exchange)
    with pytest.raises(FileHelperError, match="changed during deletion"):
        FileHelper(root, allow_symlinks=True).delete(tree, recursive=True)
    assert (root / "retained/file").read_text() == "keep"
    assert (tree / "nested").is_symlink()


@pytest.mark.parametrize("allow", [False, True])
def test_unrelated_symlink_is_outside_operation_scope(root, link, allow):
    link(root / "unrelated", root.parent / "missing")
    files = FileHelper(root, allow_symlinks=allow)
    files.create_text("selected", "works")
    assert files.read_text("selected") == "works"
    files.delete("selected")
    assert (root / "unrelated").is_symlink()


@pytest.mark.parametrize("allow", [False, True])
def test_trusted_root_alias_and_os_ancestors_are_not_rejected(root, link, allow):
    alias = link(root.parent / "root-alias", root)
    ancestor = link(root.parent / "ancestor-alias", root.parent)
    for supplied in (alias, ancestor / root.name):
        files = FileHelper(supplied, allow_symlinks=allow)
        files.write_text("file", "works")
        assert files.read_text(supplied / "file") == "works"
        assert files.read_text(root / "file") == "works"


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("relative_root", [False, True])
def test_operations_derived_from_trusted_parent_traversal_root(root, monkeypatch, allow, relative_root):
    anchor = root.parent / "anchor"
    anchor.mkdir()
    if relative_root:
        monkeypatch.chdir(anchor)
        supplied = Path("../project")
    else:
        supplied = anchor / ".." / root.name
    files = FileHelper(supplied, allow_symlinks=allow)
    assert ".." in files.root.parts
    directory = files.root / "created"
    files.mkdir(directory)
    files.create_text(directory / "file", "old")
    assert files.read_text(directory / "file") == "old"
    files.write_text(directory / "file", "new")
    assert (root / "created/file").read_text() == "new"
    assert files.read_text(root.resolve() / "created/file") == "new"
    files.delete(directory / "file")
    files.write_bytes(directory / "new", b"new")
    files.delete(directory, recursive=True)
    assert not (root / "created").exists()
    with pytest.raises(FileHelperError, match="established root"):
        files.delete(files.root, recursive=True)
    assert root.is_dir()


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("relative_root", [False, True])
def test_trusted_parent_traversal_root_does_not_permit_operation_suffix_traversal(
    root, monkeypatch, allow, relative_root
):
    anchor = root.parent / "anchor"
    anchor.mkdir()
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "keep").write_bytes(b"keep")
    if relative_root:
        monkeypatch.chdir(anchor)
        supplied = Path("../project")
    else:
        supplied = anchor / ".." / root.name
    files = FileHelper(supplied, allow_symlinks=allow)
    for path in (files.root / "../outside/keep", Path("../outside/keep"),
                 files.root / "inside/../../outside/keep"):
        for operation in (
            lambda: files.read_bytes(path),
            lambda: files.write_bytes(path, b"bad"),
            lambda: files.create_bytes(path, b"bad"),
            lambda: files.mkdir(path, parents=True),
            lambda: files.delete(path),
        ):
            with pytest.raises(PathEscapeError, match="Parent traversal"):
                operation()
    assert (outside / "keep").read_bytes() == b"keep"
    assert list(root.iterdir()) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink/parent traversal semantics required")
@pytest.mark.parametrize("allow", [False, True])
def test_trusted_root_parent_traversal_is_not_lexically_collapsed(root, link, allow):
    container = root.parent / "different/container"
    container.mkdir(parents=True)
    selected = root.parent / "different/project"
    selected.mkdir()
    alias = link(root.parent / "root-entry", container)
    files = FileHelper(alias / "../project", allow_symlinks=allow)
    files.create_text(files.root / "file", "selected")
    assert (selected / "file").read_text() == "selected"
    assert list(root.iterdir()) == []
    assert alias.is_symlink()


@pytest.mark.parametrize("path", ["../escape", "inside/../escape"])
def test_operation_parent_traversal_is_rejected(root, path):
    with pytest.raises(PathEscapeError):
        FileHelper(root).mkdir(path, parents=True)
    assert list(root.iterdir()) == []


def test_absolute_escape_and_root_deletion_rejected(root):
    files = FileHelper(root)
    with pytest.raises(PathEscapeError):
        files.write_text(root.parent / "outside", "bad")
    with pytest.raises(FileHelperError, match="established root"):
        files.delete(".", recursive=True)
    assert root.is_dir()


def test_relative_link_targets_are_walked_without_losing_evidence(root, link):
    directory = root / "directory"
    directory.mkdir()
    (root / "file").write_text("ok")
    link(directory / "valid", "../file")
    files = FileHelper(root, allow_symlinks=True)
    assert files.read_text("directory/valid") == "ok"
    link(directory / "escape", "../../outside")
    with pytest.raises(PathEscapeError):
        files.read_text("directory/escape")
    link(root / "inner", root.parent)
    link(root / "indirect", "inner/project/file")
    with pytest.raises(PathEscapeError):
        files.read_text("indirect")
    link(root / "invalid", "file/../file")
    with pytest.raises(NotADirectoryError):
        files.read_text("invalid")


def test_intermediate_target_link_is_checked(root, link):
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "file").write_text("bad")
    link(root / "indirection", outside)
    link(root / "alias", root / "indirection/file")
    with pytest.raises(PathEscapeError):
        FileHelper(root, allow_symlinks=True).read_text("alias")


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("entry", ["file", "alias", "dangling"])
def test_exclusive_create_never_overwrites_file_or_link(root, link, allow, entry):
    (root / "file").write_bytes(b"keep")
    alias = link(root / "alias", root / "file")
    dangling = link(root / "dangling", root / "missing")
    files = FileHelper(root, allow_symlinks=allow)
    path = root / entry
    error = SymlinkDeniedError if path.is_symlink() and not allow else FileExistsError
    with pytest.raises(error):
        files.create_bytes(path, b"bad")
    assert (root / "file").read_bytes() == b"keep"
    assert alias.is_symlink() and dangling.is_symlink()
    assert not (root / "missing").exists()


@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("cyclic", [False, True])
def test_exclusive_create_rejects_existing_leaf_before_open(
    root, link, monkeypatch, operation, cyclic
):
    target = root / "target"
    target.write_bytes(b"keep")
    alias = link(root / "alias", root / "alias" if cyclic else target)
    original_target = os.readlink(alias)
    opened = []
    real_open = os.open

    def recording_open(path, flags, mode):
        opened.append(Path(path))
        return real_open(path, flags, mode)

    monkeypatch.setattr("specify_cli.file_helper.os.open", recording_open)
    content = b"bad" if operation == "create_bytes" else "bad"
    with pytest.raises(FileExistsError) as error:
        getattr(FileHelper(root, allow_symlinks=True), operation)(alias, content)
    assert error.value.errno == errno.EEXIST
    assert opened == []
    assert alias.is_symlink()
    assert os.readlink(alias) == original_target
    assert target.read_bytes() == b"keep"


@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("external", [False, True])
def test_exclusive_create_rejects_dangling_leaf_with_windows_backend(
    root, link, monkeypatch, operation, external
):
    target = root.parent / "external-missing" if external else root / "missing"
    alias = link(root / "alias", target)
    original_target = os.readlink(alias)
    opened = []
    real_open = os.open
    monkeypatch.delattr("specify_cli.file_helper.os.O_NOFOLLOW", raising=False)

    def windows_open(path, flags, mode):
        opened.append(Path(path))
        assert flags & os.O_CREAT and flags & os.O_EXCL
        return real_open(Path(os.readlink(path)), flags, mode)

    monkeypatch.setattr("specify_cli.file_helper.os.open", windows_open)
    content = b"bad" if operation == "create_bytes" else "bad"
    with pytest.raises(FileExistsError) as error:
        getattr(FileHelper(root, allow_symlinks=True), operation)(alias, content)
    assert error.value.errno == errno.EEXIST
    assert opened == []
    assert alias.is_symlink()
    assert os.readlink(alias) == original_target
    assert not os.path.lexists(target)


def test_symlink_creation_requires_permission_and_contained_target(root, link):
    (root / "file").write_text("ok")
    with pytest.raises(SymlinkDeniedError):
        FileHelper(root).symlink("file", "denied")
    assert not os.path.lexists(root / "denied")
    files = FileHelper(root, allow_symlinks=True)
    files.symlink("file", "allowed")
    assert os.readlink(root / "allowed") == "file"
    assert files.read_text("allowed") == "ok"
    files.mkdir("directory")
    files.symlink("../file", "directory/relative")
    assert files.read_text("directory/relative") == "ok"
    files.symlink("directory", "directory-alias")
    assert (root / "directory-alias").is_dir()
    with pytest.raises(FileNotFoundError):
        files.symlink("missing", "dangling")
    with pytest.raises(PathEscapeError):
        files.symlink(root.parent / "outside", "escape")
    with pytest.raises(FileExistsError):
        files.symlink("file", "allowed")
    assert not os.path.lexists(root / "dangling")
    assert not os.path.lexists(root / "escape")


def test_missing_wrong_type_and_nonempty_failures(root):
    files = FileHelper(root)
    with pytest.raises(FileNotFoundError):
        files.read_bytes("missing")
    with pytest.raises(FileNotFoundError):
        files.delete("missing")
    with pytest.raises(FileNotFoundError):
        files.create_text("missing/file", "bad")
    with pytest.raises(FileNotFoundError):
        files.write_text("missing/file", "bad")
    files.mkdir("directory")
    files.create_text("directory/file", "keep")
    for operation in (lambda: files.read_bytes("directory"),
                      lambda: files.write_text("directory", "bad")):
        with pytest.raises(UnsupportedPathError):
            operation()
    with pytest.raises(NotADirectoryError):
        files.mkdir("directory/file/child", parents=True)
    with pytest.raises(OSError):
        files.delete("directory")
    assert files.read_text("directory/file") == "keep"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX special files required")
@pytest.mark.parametrize("allow", [False, True])
def test_special_objects_fail_before_read_update_or_recursive_mutation(root, allow):
    files = FileHelper(root, allow_symlinks=allow)
    files.mkdir("tree")
    files.create_text("tree/a-file", "keep")
    os.mkfifo(root / "tree/z-fifo")
    for operation in (lambda: files.read_bytes("tree/z-fifo"),
                      lambda: files.write_bytes("tree/z-fifo", b"bad"),
                      lambda: files.delete("tree", recursive=True)):
        with pytest.raises(UnsupportedPathError):
            operation()
    assert files.read_text("tree/a-file") == "keep"
    assert (root / "tree/z-fifo").exists()


def test_atomic_failure_cleans_temp_and_preserves_target(root, monkeypatch):
    files = FileHelper(root)
    files.create_text("file", "old")

    def fail(*args):
        raise PermissionError("replacement denied")

    monkeypatch.setattr("specify_cli.file_helper.os.replace", fail)
    with pytest.raises(PermissionError, match="replacement denied"):
        files.write_text("file", "new")
    assert files.read_text("file") == "old"
    assert list(root.iterdir()) == [root / "file"]


def test_native_permission_failure_is_not_suppressed(root, monkeypatch):
    files = FileHelper(root)

    def fail(*args, **kwargs):
        raise PermissionError("creation denied")

    monkeypatch.setattr("specify_cli.file_helper.os.open", fail)
    with pytest.raises(PermissionError, match="creation denied"):
        files.create_bytes("file", b"bad")
    assert list(root.iterdir()) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits required")
def test_atomic_target_replacement_uses_requested_mode(root, link):
    target = root / "target"
    target.write_text("old")
    alias = link(root / "alias", target)
    FileHelper(root, allow_symlinks=True).write_bytes(alias, b"new", mode=0o600)
    assert target.stat().st_mode & 0o777 == 0o600
    assert alias.is_symlink()


def test_atomic_write_rechecks_original_link(root, link, monkeypatch):
    first = root / "first"
    first.write_text("first")
    second = root / "second"
    second.write_text("second")
    alias = link(root / "alias", first)
    chmod = Path.chmod

    def exchange(path, mode, **kwargs):
        chmod(path, mode, **kwargs)
        alias.unlink()
        alias.symlink_to(second)

    monkeypatch.setattr(Path, "chmod", exchange)
    with pytest.raises(FileHelperError, match="changed during write"):
        FileHelper(root, allow_symlinks=True).write_text(alias, "bad")
    assert first.read_text() == "first"
    assert second.read_text() == "second"
    assert sorted(p.name for p in root.iterdir()) == ["alias", "first", "second"]


def test_policy_is_immutable_and_helpers_are_independent(root, link):
    (root / "file").write_text("ok")
    link(root / "alias", "file")
    deny = FileHelper(root)
    allow = FileHelper(root, allow_symlinks=True)
    with pytest.raises(FrozenInstanceError):
        deny.allow_symlinks = True
    assert allow.read_text("alias") == "ok"
    with pytest.raises(SymlinkDeniedError):
        deny.read_text("alias")


def test_root_must_be_existing_directory(root):
    with pytest.raises(FileNotFoundError):
        FileHelper(root / "missing")
    (root / "file").write_text("file")
    with pytest.raises(NotADirectoryError):
        FileHelper(root / "file")


@pytest.mark.parametrize("spelling", ["/outside/file", r"\outside\file", "C:outside/file", "C:"])
def test_windows_anchored_relative_forms_rejected_portably(root, spelling):
    path = PureWindowsPath(spelling)
    assert path.anchor and not path.is_absolute()
    with pytest.raises(PathEscapeError):
        FileHelper(root)._parts(path)


@pytest.mark.parametrize("spelling", ["inside/file", r"inside\file", "."])
def test_windows_unanchored_relative_forms_are_root_relative(root, spelling):
    path = PureWindowsPath(spelling)
    assert FileHelper(root)._parts(path) == path.parts


@pytest.mark.parametrize("spelling", ["C:/outside/file", r"\\server\share\outside"])
def test_windows_true_absolute_forms_do_not_bypass_scoped_matching(root, spelling):
    with pytest.raises(PathEscapeError):
        FileHelper(root)._parts(PureWindowsPath(spelling))


@pytest.mark.parametrize(
    "spelling",
    ["D:/project/inside/file", "d:/PROJECT/inside/file", r"\\server\share\project\inside\file"],
)
def test_windows_contained_absolute_forms_match_roots_portably(spelling):
    boundary = SimpleNamespace(
        root=PureWindowsPath("D:/project"),
        _canonical_root=PureWindowsPath(r"\\server\share\project"),
    )
    assert FileHelper._parts(boundary, PureWindowsPath(spelling)) == ("inside", "file")


@pytest.mark.parametrize(
    "spelling",
    ["D:/project2/file", "D:/outside/file", "C:/project/file", r"\\server\share\project2\file"],
)
def test_windows_absolute_forms_outside_declared_roots_rejected_portably(spelling):
    boundary = SimpleNamespace(
        root=PureWindowsPath("D:/project"),
        _canonical_root=PureWindowsPath(r"\\server\share\project"),
    )
    with pytest.raises(PathEscapeError):
        FileHelper._parts(boundary, PureWindowsPath(spelling))


@pytest.mark.parametrize("unc", [False, True])
@pytest.mark.parametrize("root_extended", [False, True])
@pytest.mark.parametrize("target_extended", [False, True])
def test_windows_extended_contained_targets_match_roots_portably(
    unc, root_extended, target_extended
):
    plain = r"\\server\share\project" if unc else r"D:\project"
    extended = r"\\?\UNC\server\share\project" if unc else r"\\?\D:\project"
    root_path = PureWindowsPath(extended if root_extended else plain)
    target = PureWindowsPath(extended if target_extended else plain) / "inside/file"
    boundary = SimpleNamespace(root=root_path, _canonical_root=root_path)
    assert FileHelper._parts(boundary, target) == ("inside", "file")


@pytest.mark.parametrize("marker", ["unc", "uNc", "UnC", "UNC"])
@pytest.mark.parametrize("prefixed_root", [False, True])
def test_windows_mixed_case_unc_prefixes_preserve_contained_targets(marker, prefixed_root):
    plain = r"\\Server\Share\Project"
    prefixed = "\\\\?\\" + marker + r"\Server\Share\Project"
    root_path = PureWindowsPath(prefixed if prefixed_root else plain)
    boundary = SimpleNamespace(root=root_path, _canonical_root=root_path)
    target = PureWindowsPath(prefixed + r"\ChIlD\FiLe")
    assert FileHelper._parts(boundary, target) == ("ChIlD", "FiLe")


@pytest.mark.parametrize("marker", ["unc", "uNc", "UnC", "UNC"])
def test_windows_mixed_case_unc_prefixes_do_not_allow_external_targets(marker):
    root_path = PureWindowsPath(r"\\Server\Share\Project")
    boundary = SimpleNamespace(root=root_path, _canonical_root=root_path)
    target = PureWindowsPath("\\\\?\\" + marker + r"\Server\Share\ProjectSibling\file")
    with pytest.raises(PathEscapeError):
        FileHelper._parts(boundary, target)


@pytest.mark.parametrize(
    "spelling",
    [
        r"\\?\D:\project2\file",
        r"\\?\D:\outside\file",
        r"\\?\C:\project\file",
        r"\\?\UNC\server\share\project2\file",
        r"\\?\UNC\other\share\project\file",
        r"\\?\GLOBALROOT\Device\HarddiskVolume1\file",
        r"\\?\C:relative\file",
    ],
)
def test_windows_extended_external_or_unsupported_targets_rejected_portably(spelling):
    boundary = SimpleNamespace(
        root=PureWindowsPath("D:/project"),
        _canonical_root=PureWindowsPath(r"\\server\share\project"),
    )
    with pytest.raises(PathEscapeError):
        FileHelper._parts(boundary, PureWindowsPath(spelling))


def test_windows_extended_comparison_preserves_accessed_hierarchy_portably():
    boundary = SimpleNamespace(
        root=PureWindowsPath("D:/project"),
        _canonical_root=PureWindowsPath("D:/project"),
    )
    assert FileHelper._parts(
        boundary, PureWindowsPath(r"\\?\D:\project\linked\..\file")
    ) == ("linked", "..", "file")


@pytest.mark.skipif(os.name == "nt", reason="POSIX literal backslash filename semantics required")
def test_posix_windows_like_filenames_are_not_reinterpreted(root, link):
    name = r"\\?\D:\literal"
    files = FileHelper(root, allow_symlinks=True)
    files.create_text(name, "old")
    files.symlink(name, "alias")
    assert files.read_text("alias") == "old"
    files.write_text("alias", "new")
    assert (root / name).read_text() == "new"
    assert (root / "alias").is_symlink()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows symlink semantics required")
@pytest.mark.parametrize("root_extended", [False, True])
@pytest.mark.parametrize("external", [False, True])
def test_native_windows_extended_symlink_read_update_and_creation(
    root, link, root_extended, external
):
    target = root.parent / "outside" if external else root / "target"
    target.write_text("old")

    def extended(path):
        raw = str(path)
        return "\\\\?\\UNC\\" + raw[2:] if raw.startswith("\\\\") else "\\\\?\\" + raw

    alias = link(root / "alias", extended(target))
    original_target = os.readlink(alias)
    files = FileHelper(Path(extended(root)) if root_extended else root, allow_symlinks=True)
    if external:
        with pytest.raises(PathEscapeError):
            files.read_text("alias")
        with pytest.raises(PathEscapeError):
            files.write_text("alias", "bad")
        with pytest.raises(PathEscapeError):
            files.symlink(extended(target), "new")
        assert target.read_text() == "old"
        assert not os.path.lexists(root / "new")
    else:
        assert files.read_text("alias") == "old"
        files.write_text("alias", "new")
        assert target.read_text() == "new"
        assert alias.is_symlink()
        assert os.readlink(alias) == original_target
        files.symlink(extended(target), "created")
        assert files.read_text("created") == "new"
    files.delete("alias")
    assert not os.path.lexists(alias)
    assert target.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows path semantics required")
@pytest.mark.parametrize("spelling", ["/outside/file", r"\outside\file", "C:outside/file", "C:"])
@pytest.mark.parametrize("operation", ["read_bytes", "create_bytes", "write_bytes", "mkdir", "delete"])
@pytest.mark.parametrize("allow", [False, True])
def test_native_windows_anchored_relative_operations_rejected(root, spelling, operation, allow):
    args = (spelling, b"bad") if operation in ("create_bytes", "write_bytes") else (spelling,)
    with pytest.raises(PathEscapeError):
        getattr(FileHelper(root, allow_symlinks=allow), operation)(*args)
    assert list(root.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="Native Windows path semantics required")
@pytest.mark.parametrize("spelling", ["/outside/file", r"\outside\file", "C:outside/file", "C:"])
def test_native_windows_invalid_link_targets_rejected(root, link, monkeypatch, spelling):
    (root / "file").write_text("keep")
    alias = link(root / "alias", root / "file")
    files = FileHelper(root, allow_symlinks=True)
    with pytest.raises(PathEscapeError):
        files.symlink(spelling, "new")
    monkeypatch.setattr("specify_cli.file_helper.os.readlink", lambda path: spelling)
    with pytest.raises(PathEscapeError):
        files.read_text(alias)
    with pytest.raises(PathEscapeError):
        files.write_text(alias, "bad")
    assert (root / "file").read_text() == "keep"
    assert not os.path.lexists(root / "new")


@pytest.mark.skipif(os.name != "nt", reason="Native Windows path semantics required")
def test_native_windows_absolute_and_relative_scoping(root):
    files = FileHelper(root)
    files.write_text(root / "absolute", "ok")
    files.write_text("relative", "ok")
    assert files.read_text(root / "absolute") == "ok"
    assert files.read_text("relative") == "ok"
    with pytest.raises(PathEscapeError):
        files.write_text(root.parent / "outside", "bad")


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("recursive", [False, True])
def test_directory_reparse_entries_rejected_before_traversal_portably(
    root, monkeypatch, allow, recursive
):
    (root / "tree").mkdir()
    (root / "tree/a-file").write_text("keep")
    junction = root / "tree/z-junction"
    junction.mkdir()
    (junction / "keep").write_text("keep")
    lstat = Path.lstat

    def directory_reparse(path, **kwargs):
        result = lstat(path, **kwargs)
        if path == junction:
            return SimpleNamespace(
                st_mode=result.st_mode,
                st_file_attributes=0x400,
                st_reparse_tag=0xA0000003,
            )
        return result

    monkeypatch.setattr(Path, "lstat", directory_reparse)
    files = FileHelper(root, allow_symlinks=allow)
    for operation in (
        lambda: files.read_bytes(junction / "keep"),
        lambda: files.write_bytes(junction / "keep", b"bad"),
        lambda: files.create_bytes(junction / "new", b"bad"),
        lambda: files.mkdir(junction / "new-directory"),
        lambda: files.delete(junction, recursive=recursive),
        lambda: files.delete("tree", recursive=True),
    ):
        with pytest.raises(UnsupportedPathError, match="reparse"):
            operation()
    assert (root / "tree/a-file").read_text() == "keep"
    assert (junction / "keep").read_text() == "keep"
    assert not (junction / "new").exists()
    assert not (junction / "new-directory").exists()


@pytest.mark.parametrize("allow", [False, True])
def test_symlink_reparse_entries_retain_normal_symlink_policy_portably(root, link, monkeypatch, allow):
    (root / "file").write_text("keep")
    alias = link(root / "alias", root / "file")
    lstat = Path.lstat

    def symlink_reparse(path, **kwargs):
        result = lstat(path, **kwargs)
        if path == alias:
            return SimpleNamespace(
                st_mode=result.st_mode, st_file_attributes=0x400, st_reparse_tag=0xA000000C,
            )
        return result

    monkeypatch.setattr(Path, "lstat", symlink_reparse)
    files = FileHelper(root, allow_symlinks=allow)
    if allow:
        assert files.read_text(alias) == "keep"
        files.write_text(alias, "updated")
        assert (root / "file").read_text() == "updated"
        files.delete(alias)
        assert not os.path.lexists(alias)
    else:
        with pytest.raises(SymlinkDeniedError):
            files.read_text(alias)
        with pytest.raises(SymlinkDeniedError):
            files.delete(alias)
        assert alias.is_symlink()
        assert (root / "file").read_text() == "keep"


@pytest.fixture
def junction(root):
    if os.name != "nt":
        pytest.skip("Native Windows junction creation required")

    def create(path, target):
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(path), str(target)],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if result.returncode:
            pytest.skip(f"Windows junction creation unavailable: {result.stderr or result.stdout}")
        return path

    return create


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("external", [False, True])
def test_native_windows_junctions_never_traversed_or_deleted(root, junction, allow, external):
    target = root.parent / "outside" if external else root / "target"
    target.mkdir()
    (target / "keep").write_text("keep")
    tree = root / "tree"
    tree.mkdir()
    (tree / "a-file").write_text("keep")
    alias = junction(tree / "z-junction", target)
    files = FileHelper(root, allow_symlinks=allow)
    for operation in (
        lambda: files.read_text(alias / "keep"),
        lambda: files.write_text(alias / "keep", "bad"),
        lambda: files.create_text(alias / "new", "bad"),
        lambda: files.mkdir(alias / "new-directory"),
        lambda: files.delete(alias / "keep"),
        lambda: files.delete(alias),
        lambda: files.delete(alias, recursive=True),
        lambda: files.delete(tree, recursive=True),
    ):
        with pytest.raises(UnsupportedPathError, match="reparse"):
            operation()
    assert alias.exists()
    assert (target / "keep").read_text() == "keep"
    assert (tree / "a-file").read_text() == "keep"
    assert sorted(p.name for p in target.iterdir()) == ["keep"]
