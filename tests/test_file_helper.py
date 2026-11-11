"""Operation-level evidence for the scoped FileHelper foundation."""

from dataclasses import FrozenInstanceError
import errno
import gc
from contextlib import contextmanager, nullcontext
import os
from pathlib import Path, PureWindowsPath
import shutil
import stat
import subprocess
import sys
from types import SimpleNamespace
import weakref

import pytest

from specify_cli import file_helper
from specify_cli._file_handles import _WindowsFileIdentity
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


@pytest.fixture
def windows_delete_model(monkeypatch):
    locations = {}
    next_handle = 0

    @contextmanager
    def opened(path, *, parent=None):
        nonlocal next_handle
        actual = path if parent is None else locations[parent] / path
        next_handle += 1
        handle = next_handle
        locations[handle] = actual
        try:
            yield handle
        finally:
            del locations[handle]

    @contextmanager
    def entry(parent, name, *, deleting=False):
        with opened(Path(name), parent=parent) as handle:
            yield handle

    def mode(handle):
        return FileHelper._entry_mode(locations[handle])

    def names(handle):
        with os.scandir(locations[handle]) as entries:
            return [item.name for item in entries]

    def remove(handle):
        if stat.S_ISDIR(mode(handle)):
            os.rmdir(locations[handle])
        else:
            os.unlink(locations[handle])

    monkeypatch.setattr(file_helper, "_windows_entry", entry)
    monkeypatch.setattr(file_helper, "_windows_mode", mode)
    monkeypatch.setattr(file_helper, "_windows_readlink", lambda handle: os.readlink(locations[handle]))
    monkeypatch.setattr(file_helper, "_windows_directory_names", names)
    monkeypatch.setattr(file_helper, "_windows_delete", remove)
    return SimpleNamespace(
        opened=opened, locations=locations, names=names, remove=remove,
    )


def _before_windows_removal(monkeypatch, name, before):
    selected = set()
    original_entry = file_helper._windows_entry
    original_delete = file_helper._windows_delete

    @contextmanager
    def entry(parent, child, *, deleting=False):
        with original_entry(parent, child, deleting=deleting) as handle:
            if deleting and child == name:
                selected.add(handle)
            try:
                yield handle
            finally:
                selected.discard(handle)

    def remove(handle):
        if handle in selected:
            before()
        original_delete(handle)

    monkeypatch.setattr(file_helper, "_windows_entry", entry)
    monkeypatch.setattr(file_helper, "_windows_delete", remove)


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


@pytest.mark.skipif(os.name == "nt", reason="POSIX shared directory traversal")
@pytest.mark.parametrize("operation", ["read_bytes", "create_bytes", "overwrite_text"])
def test_posix_operations_share_parent_walk_and_preserve_leaf_flags(root, monkeypatch, operation):
    parent = root / "parent/nested"
    parent.mkdir(parents=True)
    selected = parent / "file"
    if operation != "create_bytes":
        selected.write_bytes(b"inside")
    files = FileHelper(root)
    parents = []
    opened = []
    original_walk = FileHelper._posix_directory
    original_open = os.open

    @contextmanager
    def observe_walk(self, directory, **kwargs):
        parents.append(directory)
        with original_walk(self, directory, **kwargs) as fd:
            yield fd

    def observe_open(path, flags, *args, **kwargs):
        opened.append((path, flags, args, kwargs))
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(FileHelper, "_posix_directory", observe_walk)
    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "open": observe_open}))
    cloexec = getattr(os, "O_CLOEXEC", 0)
    if operation == "read_bytes":
        assert files.read_bytes(selected) == b"inside"
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | cloexec
        mode = ()
    elif operation == "create_bytes":
        files.create_bytes(selected, b"new")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        mode = (0o644,)
    else:
        files.overwrite_text(selected, "new")
        flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | cloexec
        mode = (0o666,)
    assert parents == [parent.resolve()]
    directory_calls = [call for call in opened if call[1] & os.O_DIRECTORY]
    assert len(directory_calls) == 3
    assert len({call[1] for call in directory_calls}) == 1
    assert all(call[1] & os.O_NOFOLLOW for call in directory_calls)
    leaf_calls = [call for call in opened if not call[1] & os.O_DIRECTORY]
    assert len(leaf_calls) == 1
    assert leaf_calls[0][:3] == ("file", flags, mode)
    assert leaf_calls[0][3]["dir_fd"] is not None
    assert selected.read_bytes() == (b"inside" if operation == "read_bytes" else b"new")
    files.close()


@pytest.mark.skipif(os.name == "nt", reason="POSIX shared directory cleanup")
@pytest.mark.parametrize("operation", ["read_bytes", "create_bytes", "overwrite_text"])
@pytest.mark.parametrize("failure", ["root", "parent", "leaf"])
def test_posix_parent_walk_closes_descriptors_after_open_failures(root, monkeypatch, operation, failure):
    parent = root / "parent/nested"
    parent.mkdir(parents=True)
    selected = parent / "file"
    if operation != "create_bytes":
        selected.write_bytes(b"inside")
    original_open = os.open
    original_close = os.close
    live = set()
    failed = []

    def observe_open(path, flags, *args, **kwargs):
        fail_here = (
            (failure == "root" and Path(path) == root.resolve())
            or (failure == "parent" and path == "nested")
            or (failure == "leaf" and path == "file")
        )
        if fail_here:
            failed.append(path)
            raise PermissionError("injected open failure")
        fd = original_open(path, flags, *args, **kwargs)
        live.add(fd)
        return fd

    def observe_close(fd):
        original_close(fd)
        live.remove(fd)

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{
        **vars(os), "open": observe_open, "close": observe_close,
    }))
    with pytest.raises(PermissionError, match="injected"):
        if operation == "read_bytes":
            FileHelper(root).read_bytes(selected)
        elif operation == "create_bytes":
            FileHelper(root).create_bytes(selected, b"new")
        else:
            FileHelper(root).overwrite_text(selected, "new")
    assert len(failed) == 1
    assert live == set()
    if operation == "create_bytes":
        assert not selected.exists()
    else:
        assert selected.read_bytes() == b"inside"


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("operation", ["read_bytes", "read_text"])
@pytest.mark.parametrize("kind", ["leaf", "parent", "resolved-link"])
def test_read_does_not_follow_replacements_after_validation(
    root, link, monkeypatch, allow, operation, kind
):
    if kind == "resolved-link" and not allow:
        pytest.skip("Contained links require allow mode")
    directory = root / "directory"
    directory.mkdir()
    (directory / "file").write_bytes(b"inside")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside-secret")
    selected = directory / "file"
    if kind == "resolved-link":
        selected = link(root / "alias", selected)
    original_path = FileHelper._path

    def exchange(self, path, **kwargs):
        destination = original_path(self, path, **kwargs)
        if kind == "parent":
            directory.rename(root / "retained")
            link(directory, outside)
        else:
            destination.unlink()
            link(destination, outside / "file")
        return destination

    monkeypatch.setattr(FileHelper, "_path", exchange)
    try:
        content = getattr(FileHelper(root, allow_symlinks=allow), operation)(selected)
    except (OSError, FileHelperError):
        pass
    else:
        assert content in (b"inside", "inside")


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("kind", ["leaf", "parent"])
def test_read_uses_opened_file_after_replacement(root, link, monkeypatch, allow, kind):
    directory = root / "directory"
    directory.mkdir()
    selected = directory / "file"
    selected.write_bytes(b"inside")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside-secret")
    original_fstat = os.fstat
    swapped = False
    files = FileHelper(root, allow_symlinks=allow)

    def exchange(fd):
        nonlocal swapped
        info = original_fstat(fd)
        if swapped:
            return info
        if kind == "leaf":
            source, replacement = selected, outside / "file"
        else:
            source, replacement = directory, outside
        if os.name == "nt":
            with pytest.raises(OSError):
                source.rename(root / "retained")
        else:
            source.rename(root / "retained")
            link(source, replacement)
        swapped = True
        return info

    monkeypatch.setattr("specify_cli.file_helper.os.fstat", exchange)
    with files:
        assert files.read_bytes(selected) == b"inside"
    assert swapped
    if os.name == "nt":
        source = selected if kind == "leaf" else directory
        source.rename(root / "retained")


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor-relative open regression")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("phase", ["parent", "leaf"])
def test_read_rejects_replacement_during_open(root, link, monkeypatch, allow, phase):
    directory = root / "directory"
    directory.mkdir()
    selected = directory / "file"
    selected.write_bytes(b"inside")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside-secret")
    original_open = os.open
    swapped = False

    def exchange(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == ("directory" if phase == "parent" else "file"):
            source = directory if phase == "parent" else selected
            source.rename(root / "retained")
            link(source, outside if phase == "parent" else outside / "file")
            swapped = True
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {exchange})
    monkeypatch.setattr("specify_cli.file_helper.os.open", exchange)
    with pytest.raises(OSError):
        FileHelper(root, allow_symlinks=allow).read_bytes(selected)
    assert swapped


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor-relative open regression")
def test_read_pins_parent_before_opening_leaf(root, link, monkeypatch):
    directory = root / "directory"
    directory.mkdir()
    (directory / "file").write_bytes(b"inside")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside-secret")
    original_open = os.open
    swapped = False

    def exchange(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == "file":
            directory.rename(root / "retained")
            link(directory, outside)
            swapped = True
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {exchange})
    monkeypatch.setattr("specify_cli.file_helper.os.open", exchange)
    assert FileHelper(root).read_bytes("directory/file") == b"inside"
    assert swapped


@pytest.mark.parametrize("failure", [None, "parent", "leaf", "duplicate", "fstat"])
def test_windows_read_pins_entire_resolved_hierarchy(root, monkeypatch, failure):
    directory = root / "directory"
    directory.mkdir()
    selected = directory / "file"
    selected.write_bytes(b"inside")
    pinned = []
    seen = []

    @contextmanager
    def pin(path, *, directory, parent=None, traverse=False):
        if parent is None:
            assert directory and path == root.resolve()
            actual = path
        else:
            assert parent == len(pinned) + 10
            assert path.parts == (path.name,)
            actual = pinned[-1] / path
        if actual.name == {"parent": "directory", "leaf": "file"}.get(failure):
            raise OSError("injected handle failure")
        if directory:
            assert traverse
        pinned.append(actual)
        seen.append((actual, directory))
        try:
            yield len(pinned) + 10
        finally:
            assert pinned.pop() == actual

    @contextmanager
    def duplicate(handle):
        assert handle == 13
        assert pinned == [root.resolve(), directory.resolve(), selected.resolve()]
        if failure == "duplicate":
            raise OSError("injected duplicate failure")
        fd = os.open(selected, os.O_RDONLY | getattr(os, "O_BINARY", 0))
        try:
            yield fd
        finally:
            os.close(fd)

    def no_path_open(*args, **kwargs):
        assert pinned == [root.resolve(), directory.resolve(), selected.resolve()]
        pytest.fail("Windows reads must duplicate the validated handle, not reopen its path")

    def checked_fstat(fd):
        assert pinned == [root.resolve(), directory.resolve(), selected.resolve()]
        if failure == "fstat":
            raise OSError("injected fstat failure")
        return os.fstat(fd)

    windows_os = SimpleNamespace(
        name="nt",
        O_RDONLY=os.O_RDONLY,
        O_BINARY=getattr(os, "O_BINARY", 0),
        open=no_path_open,
        close=os.close,
        fdopen=os.fdopen,
        fstat=checked_fstat,
    )
    files = FileHelper(root)
    monkeypatch.setattr(file_helper, "os", windows_os)
    monkeypatch.setattr(file_helper, "_windows_handle", pin)
    monkeypatch.setattr(file_helper, "windows_read_fd", duplicate, raising=False)
    with files:
        if failure:
            with pytest.raises(OSError, match="injected"):
                files.read_bytes(selected)
        else:
            assert files.read_bytes(selected) == b"inside"
            assert seen == [
                (root.resolve(), True),
                (directory.resolve(), True),
                (selected.resolve(), False),
            ]
    assert pinned == []


@pytest.mark.skipif(os.name == "nt", reason="Portable replacement model; native reparse coverage is separate")
@pytest.mark.parametrize("allow", [False, True])
def test_windows_read_keeps_validated_object_when_path_changes(root, link, monkeypatch, allow):
    selected = root / "file"
    selected.write_bytes(b"inside")
    outside = root.parent / "outside"
    outside.write_bytes(b"outside")
    changed = False

    @contextmanager
    def pin(path, *, directory, parent=None, traverse=False):
        nonlocal changed
        if directory:
            assert parent is None and traverse
            yield 1
        else:
            assert parent == 1 and path == Path("file")
            fd = os.open(selected, os.O_RDONLY | getattr(os, "O_BINARY", 0))
            try:
                # Model reparse changes after validation without changing the opened object.
                selected.unlink()
                link(selected, outside)
                changed = True
                yield fd
            finally:
                os.close(fd)

    @contextmanager
    def duplicate(handle):
        fd = os.dup(handle)
        try:
            yield fd
        finally:
            os.close(fd)

    files = FileHelper(root, allow_symlinks=allow)
    monkeypatch.setattr(file_helper, "os", SimpleNamespace(
        name="nt", open=os.open, O_RDONLY=os.O_RDONLY,
        O_BINARY=getattr(os, "O_BINARY", 0), close=os.close,
        fstat=os.fstat, fdopen=os.fdopen,
    ))
    monkeypatch.setattr(file_helper, "_windows_handle", pin)
    monkeypatch.setattr(file_helper, "windows_read_fd", duplicate, raising=False)
    with files:
        assert files.read_bytes(selected) == b"inside"
    assert changed


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions required")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("restricted", ["root", "parent"])
@pytest.mark.parametrize("older_darwin_sdk", [
    False,
    pytest.param(True, marks=pytest.mark.skipif(sys.platform != "darwin", reason="Darwin SDK regression")),
])
def test_read_through_search_only_directories(root, monkeypatch, allow, restricted, older_darwin_sdk):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory permission checks")
    if older_darwin_sdk:
        for flag in ("O_SEARCH", "O_PATH", "O_EXEC"):
            monkeypatch.delattr(os, flag, raising=False)
    directory = root / "directory"
    directory.mkdir()
    selected = directory / "file"
    selected.write_bytes(b"inside")
    limited = root if restricted == "root" else directory
    previous_mode = limited.stat().st_mode & 0o777
    limited.chmod(0o111)
    try:
        assert selected.read_bytes() == b"inside"
        with pytest.raises(PermissionError):
            list(limited.iterdir())
        assert FileHelper(root, allow_symlinks=allow).read_bytes(selected) == b"inside"
    finally:
        limited.chmod(previous_mode)


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions required")
@pytest.mark.parametrize("restricted", ["root", "parent"])
@pytest.mark.parametrize("after_validation", [False, True])
def test_read_rejects_non_searchable_directories(root, monkeypatch, restricted, after_validation):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory permission checks")
    directory = root / "directory"
    directory.mkdir()
    selected = directory / "file"
    selected.write_bytes(b"inside")
    expected = selected.resolve()
    files = FileHelper(root)
    limited = root if restricted == "root" else directory
    previous_mode = limited.stat().st_mode & 0o777
    checked = []
    opened = []
    original_check = FileHelper._require_file
    original_open = os.open

    def revoke(path):
        original_check(path)
        checked.append(path)
        limited.chmod(0)

    def recording_open(*args, **kwargs):
        opened.append((args, kwargs))
        return original_open(*args, **kwargs)

    if after_validation:
        monkeypatch.setattr(FileHelper, "_require_file", staticmethod(revoke))
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {recording_open})
        monkeypatch.setattr(os, "open", recording_open)
    else:
        limited.chmod(0)
    try:
        with pytest.raises(PermissionError):
            files.read_bytes(selected)
        if after_validation:
            assert checked == [expected]
            assert opened
            if restricted == "parent":
                assert any(kwargs.get("dir_fd") is not None for args, kwargs in opened)
    finally:
        limited.chmod(previous_mode)


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor limits required")
@pytest.mark.parametrize("allow", [False, True])
def test_read_deep_path_with_small_descriptor_limit(root, allow):
    directory = root
    for _ in range(96):
        directory /= "d"
        directory.mkdir()
    selected = directory / "file"
    selected.write_bytes(b"inside")
    result = subprocess.run(
        [sys.executable, "-c", """
import resource
import sys
from pathlib import Path
from specify_cli.file_helper import FileHelper

root, selected = map(Path, sys.argv[1:3])
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
limit = 64 if soft == resource.RLIM_INFINITY else min(64, soft)
resource.setrlimit(resource.RLIMIT_NOFILE, (limit, hard))
assert selected.read_bytes() == b"inside"
assert FileHelper(root, allow_symlinks=sys.argv[3] == "True").read_bytes(selected) == b"inside"
""", str(root), str(selected), str(allow)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor cleanup regression")
@pytest.mark.parametrize("failure", ["parent", "leaf", "fstat", "fdopen", "read"])
def test_read_closes_descriptors_on_failure(root, monkeypatch, failure):
    (root / "directory").mkdir()
    selected = root / "directory/file"
    selected.write_bytes(b"inside")
    opened = []
    opened_leaves = []
    original_open = os.open

    def recording_open(path, flags, *args, **kwargs):
        if str(path) == {"parent": "directory", "leaf": "file"}.get(failure):
            raise PermissionError("injected open failure")
        fd = original_open(path, flags, *args, **kwargs)
        opened.append(fd)
        if str(path) == "file":
            opened_leaves.append(fd)
        return fd

    def fail(*args, **kwargs):
        raise OSError("injected read failure")

    class FailedRead:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        read = fail

    with FileHelper(root) as files, monkeypatch.context() as patch:
        patch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {recording_open})
        patch.setattr(os, "open", recording_open)
        if failure in ("fstat", "fdopen"):
            patch.setattr(os, failure, fail)
        elif failure == "read":
            patch.setattr(os, "fdopen", lambda *args, **kwargs: FailedRead())
        with pytest.raises(OSError, match="injected"):
            files.read_bytes(selected)
    assert opened
    if failure in ("fstat", "fdopen", "read"):
        assert len(opened_leaves) == 1
    for fd in opened:
        with pytest.raises(OSError) as error:
            os.fstat(fd)
        assert error.value.errno == errno.EBADF


@pytest.mark.skipif(os.name == "nt", reason="POSIX special-file replacement regression")
def test_read_checks_opened_type_without_blocking_on_fifo(root, monkeypatch):
    selected = root / "file"
    selected.write_bytes(b"inside")
    original_check = FileHelper._require_file

    def exchange(path):
        original_check(path)
        path.unlink()
        os.mkfifo(path)

    monkeypatch.setattr(FileHelper, "_require_file", staticmethod(exchange))
    with pytest.raises(UnsupportedPathError, match="regular file"):
        FileHelper(root).read_bytes(selected)


@pytest.mark.skipif(os.name == "nt", reason="POSIX capability refusal regression")
@pytest.mark.parametrize("capability", ["O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK", "supports_dir_fd"])
def test_read_refuses_unsafe_platform_fallback(root, monkeypatch, capability):
    (root / "file").write_bytes(b"inside")
    monkeypatch.setattr(os, capability, set() if capability == "supports_dir_fd" else 0)
    with pytest.raises(OSError) as error:
        FileHelper(root).read_bytes("file")
    assert error.value.errno == errno.ENOTSUP


@pytest.mark.parametrize("allow", [False, True])
def test_overwrite_text_preserves_inode_and_native_text_behavior(root, allow):
    files = FileHelper(root, allow_symlinks=allow)
    files.overwrite_text("config", "caf\u00e9\n")
    path = root / "config"
    inode = path.stat().st_ino
    assert path.read_bytes() == ("caf\u00e9" + os.linesep).encode("utf-8")
    path.chmod(0o600)
    files.overwrite_text("config", "updated\n")
    assert path.stat().st_ino == inode
    assert path.read_text() == "updated\n"
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("kind", ["leaf", "parent", "dangling"])
def test_overwrite_text_deny_preflights_links(root, link, kind):
    target = root / "target"
    target.mkdir()
    (target / "file").write_text("old")
    if kind == "parent":
        path = link(root / "alias", target) / "file"
    else:
        path = link(root / "alias", target / ("missing" if kind == "dangling" else "file"))
    with pytest.raises(SymlinkDeniedError):
        FileHelper(root).overwrite_text(path, "new")
    assert (target / "file").read_text() == "old"
    assert not (target / "missing").exists()


def test_overwrite_text_allow_updates_target_not_link(root, link):
    target = root / "target"
    target.write_text("old")
    alias = link(root / "alias", target)
    chain = link(root / "chain", "alias")
    FileHelper(root, allow_symlinks=True).overwrite_text(chain, "new")
    assert alias.is_symlink() and chain.is_symlink()
    assert target.read_text() == "new"


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("kind", ["dangling", "external", "cycle"])
def test_overwrite_text_rejects_unsafe_link_targets(root, link, allow, kind):
    outside = root.parent / "outside"
    outside.write_text("unchanged")
    if kind == "external":
        target = outside
    elif kind == "cycle":
        target = root / "alias"
    else:
        target = root / "missing"
    alias = link(root / "alias", target)
    expected = (FileHelperError, FileNotFoundError)
    with pytest.raises(expected):
        FileHelper(root, allow_symlinks=allow).overwrite_text(alias, "new")
    assert outside.read_text() == "unchanged"
    assert not (root / "missing").exists()
    assert alias.is_symlink()


@pytest.mark.parametrize("allow", [False, True])
def test_overwrite_text_through_contained_parent(root, link, allow):
    (root / "directory").mkdir()
    alias = link(root / "alias", root / "directory")
    files = FileHelper(root, allow_symlinks=allow)
    if allow:
        files.overwrite_text(alias / "new", "content")
        assert (root / "directory/new").read_text() == "content"
    else:
        with pytest.raises(SymlinkDeniedError):
            files.overwrite_text(alias / "new", "content")
        assert not (root / "directory/new").exists()


@pytest.mark.parametrize("allow", [False, True])
def test_overwrite_text_encoding_errors_propagate(root, allow):
    files = FileHelper(root, allow_symlinks=allow)
    with pytest.raises(LookupError):
        files.overwrite_text("new", "text", encoding="invalid-encoding")
    assert not (root / "new").exists()
    with pytest.raises(UnicodeEncodeError):
        files.overwrite_text("new", "caf\u00e9", encoding="ascii")


@pytest.mark.parametrize("allow", [False, True])
def test_overwrite_text_io_errors_propagate(root, monkeypatch, allow):
    files = FileHelper(root, allow_symlinks=allow)
    calls = []
    real_open = os.open

    def denied(*args, **kwargs):
        if not args[1] & os.O_WRONLY:
            return real_open(*args, **kwargs)
        assert Path(args[0]).name == "new"
        assert args[1] & os.O_CREAT
        assert not args[1] & os.O_TRUNC
        calls.append(args[0])
        raise PermissionError("denied")

    if os.name == "nt":
        def denied_windows(path):
            assert path == root / "new"
            calls.append(path)
            raise PermissionError("denied")

        monkeypatch.setattr(file_helper, "_windows_overwrite_fd", denied_windows)
    else:
        monkeypatch.setattr("specify_cli.file_helper.os.open", denied)
    with files:
        with pytest.raises(PermissionError, match="denied"):
            files.overwrite_text("new", "text")
    assert len(calls) == 1
    assert not (root / "new").exists()


@pytest.mark.parametrize("path", ["../escape", "directory"])
@pytest.mark.parametrize("allow", [False, True])
def test_overwrite_text_rejects_invalid_destination(root, path, allow):
    (root / "directory").mkdir()
    with pytest.raises(FileHelperError):
        FileHelper(root, allow_symlinks=allow).overwrite_text(path, "new")
    assert (root / "directory").is_dir()


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

    def exchange(self, path, *, recursive, **kwargs):
        result = plan(self, path, recursive=recursive, **kwargs)
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
@pytest.mark.parametrize("kind", ["file", "directory", "recursive-file", "recursive-directory"])
def test_delete_parent_exchange_at_removal(root, link, monkeypatch, allow, kind):
    tree = root / "tree"
    parent = tree / "parent"
    parent.mkdir(parents=True)
    outside = root.parent / "outside"
    outside.mkdir()
    victim = parent / "victim"
    external = outside / "victim"
    directory = kind in ("directory", "recursive-directory")
    if directory:
        victim.mkdir()
        external.mkdir()
    else:
        external.write_text("keep")
        victim.write_text("selected")
    retained = root / "retained"
    primitive = "rmdir" if directory else "unlink"
    remove = getattr(os, primitive)
    attempted = False

    def exchange_parent():
        nonlocal attempted
        if not attempted:
            attempted = True
            try:
                parent.rename(retained)
            except PermissionError:
                if os.name != "nt":
                    raise
            else:
                link(parent, outside)
    def exchange(path, *args, **kwargs):
        if Path(path) == victim or str(path) == victim.name:
            exchange_parent()
        return remove(path, *args, **kwargs)

    if os.name == "nt":
        _before_windows_removal(monkeypatch, victim.name, exchange_parent)
    else:
        monkeypatch.setattr(os, primitive, exchange)
    try:
        FileHelper(root, allow_symlinks=allow).delete(
            tree if kind.startswith("recursive-") else victim,
            recursive=kind.startswith("recursive-"),
        )
    except (FileHelperError, OSError):
        # A later recursive entry may reject the exchanged parent.
        if not attempted:
            raise
    assert attempted
    if directory:
        assert external.is_dir()
    else:
        assert external.read_text() == "keep"
    if retained.exists():
        assert not os.path.lexists(retained / "victim")


@pytest.mark.parametrize("allow", [False, True])
def test_recursive_delete_parent_exchange_at_scan(root, link, monkeypatch, allow):
    tree = root / "tree"
    tree.mkdir()
    (tree / "selected").write_text("selected")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "keep").write_text("keep")
    retained = root / "retained"
    scan = os.scandir
    attempted = False
    observed = []

    def exchange_parent():
        nonlocal attempted
        if not attempted:
            attempted = True
            try:
                tree.rename(retained)
            except PermissionError:
                if os.name != "nt":
                    raise
            else:
                link(tree, outside)
    def exchange(path):
        exchange_parent()
        entries = scan(path)
        # Capture enumeration as well as removal: no outside entry is visited.
        with entries:
            children = list(entries)
        observed.extend(entry.name for entry in children)
        return scanned(children)

    @contextmanager
    def scanned(entries):
        yield iter(entries)

    if os.name == "nt":
        native_names = file_helper._windows_directory_names

        def exchange_native(handle):
            exchange_parent()
            names = native_names(handle)
            observed.extend(names)
            return names

        monkeypatch.setattr(file_helper, "_windows_directory_names", exchange_native)
    else:
        monkeypatch.setattr(os, "scandir", exchange)
    try:
        FileHelper(root, allow_symlinks=allow).delete(tree, recursive=True)
    except (FileHelperError, OSError):
        if not attempted:
            raise
    assert attempted
    assert observed == ["selected"]
    assert (outside / "keep").read_text() == "keep"


@pytest.mark.parametrize("recursive", [False, True])
def test_delete_link_parent_exchange_at_removal(root, link, monkeypatch, recursive):
    parent = root / "parent"
    parent.mkdir()
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "victim").write_text("keep")
    link(parent / "victim", outside / "victim")
    retained = root / "retained"
    unlink = os.unlink
    attempted = False

    def exchange_parent():
        nonlocal attempted
        if not attempted:
            attempted = True
            try:
                parent.rename(retained)
            except PermissionError:
                if os.name != "nt":
                    raise
            else:
                link(parent, outside)
    def exchange(path, *args, **kwargs):
        exchange_parent()
        return unlink(path, *args, **kwargs)

    if os.name == "nt":
        _before_windows_removal(monkeypatch, "victim", exchange_parent)
    else:
        monkeypatch.setattr(os, "unlink", exchange)
    FileHelper(root, allow_symlinks=True).delete(parent / "victim", recursive=recursive)
    assert attempted
    assert (outside / "victim").read_text() == "keep"
    assert not os.path.lexists((retained if retained.exists() else parent) / "victim")


@pytest.mark.parametrize("allow", [False, True])
def test_delete_exchange_after_final_validation(root, link, monkeypatch, allow):
    parent = root / "parent"
    parent.mkdir()
    (parent / "victim").write_text("selected")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "victim").write_text("keep")
    retained = root / "retained"
    check = FileHelper._deletion_entry_mode
    checks = 0

    def exchange(self, path, **kwargs):
        nonlocal checks
        result = check(self, path, **kwargs)
        checks += 1
        if checks == 2:
            try:
                parent.rename(retained)
            except PermissionError:
                if os.name != "nt":
                    raise
            else:
                link(parent, outside)
        return result

    if os.name == "nt":
        def after_validation():
            nonlocal checks
            checks += 1
            try:
                parent.rename(retained)
            except PermissionError:
                pass
            else:
                link(parent, outside)

        _before_windows_removal(monkeypatch, "victim", after_validation)
    else:
        monkeypatch.setattr(FileHelper, "_deletion_entry_mode", exchange)
    with FileHelper(root, allow_symlinks=allow) as files:
        files.delete(parent / "victim")
    assert checks == (1 if os.name == "nt" else 2)
    assert (outside / "victim").read_text() == "keep"
    assert not ((retained if retained.exists() else parent) / "victim").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor traversal")
@pytest.mark.parametrize("allow", [False, True])
def test_delete_exchange_during_parent_open(root, link, monkeypatch, allow):
    parent = root / "parent"
    parent.mkdir()
    (parent / "victim").write_text("selected")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "victim").write_text("keep")
    retained = root / "retained"
    open_directory = os.open

    def exchange(path, flags, *args, **kwargs):
        if path == "parent":
            parent.rename(retained)
            link(parent, outside)
        return open_directory(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", exchange)
    with pytest.raises(OSError):
        FileHelper(root, allow_symlinks=allow).delete(parent / "victim")
    assert (outside / "victim").read_text() == "keep"
    assert (retained / "victim").read_text() == "selected"


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor lifetime")
@pytest.mark.parametrize("stage", ["preflight", "mutation", "delete"])
@pytest.mark.parametrize("depth", [80, 160])
@pytest.mark.parametrize("allow", [False, True])
def test_recursive_delete_with_low_descriptor_limit(root, stage, depth, allow):
    import resource

    if resource.getrlimit(resource.RLIMIT_NOFILE)[1] < 64:
        pytest.skip("Hard descriptor limit is below the regression budget")
    deepest = root / "tree"
    for _ in range(depth):
        deepest /= "d"
    deepest.mkdir(parents=True)
    (deepest / "direct").write_text("control")
    (deepest / "victim").write_text("selected")
    if allow:
        (root / "alias").symlink_to(".", target_is_directory=True)
    script = """
import os
from pathlib import Path
import resource
import sys
from specify_cli.file_helper import FileHelper

root, deepest = map(Path, sys.argv[1:3])
stage, allow = sys.argv[3], sys.argv[4] == "True"
_, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
(deepest / "direct").unlink()
original_open, original_close = os.open, os.close
active = set()
peak = 0

def observe_open(*args, **kwargs):
    global peak
    fd = original_open(*args, **kwargs)
    active.add(fd)
    peak = max(peak, len(active))
    return fd

def observe_close(fd):
    original_close(fd)
    active.discard(fd)

with FileHelper(root, allow_symlinks=allow) as files:
    with files._deletion_root() as anchor:
        if stage == "mutation":
            plan = files._deletion_plan(root / "tree", recursive=True, parent=anchor)
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, hard))
        os.open, os.close = observe_open, observe_close
        try:
            if stage == "preflight":
                files._deletion_plan(root / "tree", recursive=True, parent=anchor)
            elif stage == "mutation":
                files._delete_plan(plan, parent=anchor)
            else:
                files.delete("alias/tree" if allow else "tree", recursive=True)
        finally:
            os.open, os.close = original_open, original_close
        assert not active, active
        assert peak <= 12, peak
assert (root / "tree").exists() == (stage == "preflight")
if allow:
    assert (root / "alias").is_symlink()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(root), str(deepest), stage, str(allow)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (deepest / "victim").exists() == (stage == "preflight")


@pytest.mark.skipif(os.name == "nt", reason="POSIX bounded directory cache")
def test_recursive_cache_eviction_reacquires_without_following_replacement(root, link):
    branch = root / "branch"
    deepest = branch.joinpath(*("d" for _ in range(20)))
    deepest.mkdir(parents=True)
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "victim").write_text("keep")
    with FileHelper(root) as files, files._deletion_root() as anchor:
        assert isinstance(anchor, int)
        with file_helper.ExitStack() as resources:
            directories = file_helper._DeletionDirectories(
                root, anchor, files._directory_flags(), resources
            )
            directories.directory(deepest)
            assert branch not in directories.opened
            branch.rename(root / "retained")
            link(branch, outside)
            with pytest.raises(OSError):
                directories.directory(branch)
    assert (outside / "victim").read_text() == "keep"


@pytest.mark.skipif(os.name == "nt", reason="POSIX bounded recursive preflight")
def test_recursive_cache_eviction_keeps_deny_preflight_before_any_removal(root, link):
    tree = root / "tree"
    deepest = tree.joinpath(*("d" for _ in range(20)))
    deepest.mkdir(parents=True)
    (tree / "a-first").write_text("keep")
    outside = root.parent / "outside"
    outside.write_text("keep")
    alias = link(deepest / "link", outside)
    with FileHelper(root) as files:
        with pytest.raises(SymlinkDeniedError):
            files.delete(tree, recursive=True)
    assert alias.is_symlink()
    assert (tree / "a-first").read_text() == "keep"
    assert outside.read_text() == "keep"


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor lifetime")
@pytest.mark.parametrize("stage", ["resolve", "anchor", "delete"])
@pytest.mark.parametrize("allow", [False, True])
def test_deep_nonrecursive_delete_with_low_descriptor_limit(root, stage, allow):
    import resource

    if resource.getrlimit(resource.RLIMIT_NOFILE)[1] < 64:
        pytest.skip("Hard descriptor limit is below the regression budget")
    deepest = root / "tree"
    for _ in range(80):
        deepest /= "d"
    deepest.mkdir(parents=True)
    (deepest / "direct").write_text("control")
    (deepest / "victim").write_text("selected")
    script = """
import os
from pathlib import Path
import resource
import sys
from specify_cli.file_helper import FileHelper

root, deepest = map(Path, sys.argv[1:3])
stage, allow = sys.argv[3], sys.argv[4] == "True"
_, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (64, hard))
(deepest / "direct").unlink()
with FileHelper(root, allow_symlinks=allow) as files:
    if stage == "resolve":
        with files._deletion_root() as anchor:
            assert files._path(deepest / "victim", follow_leaf=False, root_handle=anchor) == deepest / "victim"
        files.delete(deepest / "victim")
    elif stage == "anchor":
        with files._deletion_root() as anchor:
            with files._deletion_directory(deepest, root=anchor) as parent:
                os.unlink("victim", dir_fd=parent)
    else:
        files.delete(deepest / "victim")
assert not (deepest / "victim").exists()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(root), str(deepest), stage, str(allow)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (deepest / "direct").exists()
    assert not (deepest / "victim").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor lifetime")
@pytest.mark.parametrize("target_kind", ["absolute", "parent-traversal"])
def test_deep_contained_link_delete_with_low_descriptor_limit(root, link, target_kind):
    import resource

    if resource.getrlimit(resource.RLIMIT_NOFILE)[1] < 64:
        pytest.skip("Hard descriptor limit is below the regression budget")
    deepest = root / "tree"
    for _ in range(80):
        deepest /= "d"
    deepest.mkdir(parents=True)
    (deepest / "victim").write_text("selected")
    target = deepest if target_kind == "absolute" else (
        deepest.relative_to(root) / ".." / "d"
    )
    alias = link(root / "alias", target)
    script = """
from pathlib import Path
import resource
import sys
from specify_cli.file_helper import FileHelper

root = Path(sys.argv[1])
_, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (64, hard))
with FileHelper(root, allow_symlinks=True) as files:
    files.delete("alias/victim")
assert (root / "alias").is_symlink()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(root)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert alias.is_symlink()
    assert not (deepest / "victim").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor-relative parent traversal")
def test_link_parent_traversal_reanchors_after_directory_moves_outside_root(root, link, monkeypatch):
    branch = root / "branch"
    branch.mkdir()
    (root / "selected").mkdir()
    (root / "selected/victim").write_text("selected")
    outside = root.parent / "outside"
    (outside / "selected").mkdir(parents=True)
    (outside / "selected/victim").write_text("keep")
    alias = link(root / "alias", "branch/../selected")
    original = os.open
    attempted = False

    def move_after_open(path, flags, *args, **kwargs):
        nonlocal attempted
        fd = original(path, flags, *args, **kwargs)
        if path == "branch" and not attempted:
            attempted = True
            branch.rename(outside / "moved")
        return fd

    monkeypatch.setattr(os, "open", move_after_open)
    with FileHelper(root, allow_symlinks=True) as files:
        files.delete(alias / "victim")
    assert attempted
    assert not (root / "selected/victim").exists()
    assert (outside / "selected/victim").read_text() == "keep"
    assert alias.is_symlink()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor lifetime")
def test_recursive_delete_preserves_deep_tree_support(root):
    import resource

    depth = 550
    if resource.getrlimit(resource.RLIMIT_NOFILE)[0] < depth + 100:
        pytest.skip("Descriptor ceiling is too low for the deep-tree fixture")
    tree = root / "deep"
    tree.mkdir()
    parent = os.open(tree, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for _ in range(depth):
            os.mkdir("d", dir_fd=parent)
            child = os.open("d", os.O_RDONLY | os.O_DIRECTORY, dir_fd=parent)
            os.close(parent)
            parent = child
    finally:
        os.close(parent)
    try:
        with FileHelper(root) as files:
            files.delete(tree, recursive=True)
        assert not tree.exists()
    finally:
        if tree.exists():
            shutil.rmtree(tree)


@pytest.mark.skipif(sys.platform != "darwin", reason="Native Darwin search-only fallback")
@pytest.mark.parametrize("operation", ["read_text", "overwrite_text", "create_text", "mkdir", "delete"])
def test_legacy_darwin_establishes_write_search_only_root(root, monkeypatch, operation):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory permission checks")
    (root / "victim").write_text("selected")
    monkeypatch.delattr(os, "O_PATH", raising=False)
    monkeypatch.delattr(os, "O_SEARCH", raising=False)
    root.chmod(0o300)
    try:
        with FileHelper(root) as files:
            if operation == "read_text":
                assert files.read_text("victim") == "selected"
            elif operation == "overwrite_text":
                files.overwrite_text("victim", "updated")
                assert (root / "victim").read_text() == "updated"
            elif operation == "create_text":
                files.create_text("new", "created")
                assert (root / "new").read_text() == "created"
            elif operation == "mkdir":
                files.mkdir("new")
                assert (root / "new").is_dir()
            else:
                files.delete("victim")
                assert not (root / "victim").exists()
    finally:
        root.chmod(0o700)


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor lifetime")
@pytest.mark.parametrize("depth", [8, 32, 64, 160])
@pytest.mark.parametrize("recursive", [False, True])
def test_delete_directory_open_work_and_live_descriptors_stay_bounded(
    root, monkeypatch, depth, recursive
):
    tree = root / "tree"
    deepest = tree.joinpath(*("d" for _ in range(depth)))
    deepest.mkdir(parents=True)
    (deepest / "victim").write_text("selected")
    open_directory = os.open
    close_directory = os.close
    opened = 0
    active = set()
    peak = 0

    def observe(*args, **kwargs):
        nonlocal opened, peak
        fd = open_directory(*args, **kwargs)
        opened += 1
        active.add(fd)
        peak = max(peak, len(active))
        return fd

    def close(fd):
        close_directory(fd)
        active.discard(fd)

    monkeypatch.setattr(os, "open", observe)
    monkeypatch.setattr(os, "close", close)
    with FileHelper(root) as files:
        files.delete(tree if recursive else deepest / "victim", recursive=recursive)
    assert not (deepest / "victim").exists()
    assert not active
    assert peak <= 12
    budget = 4 * depth + depth * depth // 8 + 32 if recursive else 8 * depth + 16
    assert opened <= budget


@pytest.mark.skipif(os.name == "nt", reason="POSIX retained root after unlink")
def test_delete_does_not_rebind_when_root_identity_is_reused(root, monkeypatch):
    files = FileHelper(root)
    root.rmdir()
    root.mkdir()
    (root / "victim").write_text("keep")
    monkeypatch.setattr(os.path, "samestat", lambda *args: True)
    with pytest.raises((FileNotFoundError, FileHelperError)):
        files.delete("victim")
    assert (root / "victim").read_text() == "keep"
    files.close()


@pytest.mark.parametrize("failure", [False, True])
def test_file_helper_context_releases_root_and_rejects_reuse(root, failure):
    expected = pytest.raises(RuntimeError, match="operation failed") if failure else nullcontext()
    with expected:
        with FileHelper(root) as files:
            files.create_text("victim", "selected")
            files.delete("victim")
            assert files._root_cleanup.alive
            if failure:
                raise RuntimeError("operation failed")
    assert not files._root_cleanup.alive
    files.close()
    for operation in (lambda: files.read_text("victim"), lambda: files.delete("victim")):
        with pytest.raises(FileHelperError, match="closed"):
            operation()
    renamed = root.parent / "renamed"
    root.rename(renamed)
    renamed.rename(root)


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor lifetime")
def test_file_helper_finalizer_does_not_retain_helper_or_leak_root(root):
    files = FileHelper(root)
    descriptor = files._root_anchor
    assert isinstance(descriptor, int)
    reference = weakref.ref(files)
    del files
    gc.collect()
    assert reference() is None
    with pytest.raises(OSError) as exc:
        os.fstat(descriptor)
    assert exc.value.errno == errno.EBADF


@pytest.mark.skipif(os.name == "nt", reason="POSIX retained root descriptor")
def test_file_helper_reuses_root_handle_across_deletions(root, monkeypatch):
    open_directory = os.open
    roots = []
    for name in ("first", "second"):
        (root / name).write_text("selected")

    def observe(path, *args, **kwargs):
        fd = open_directory(path, *args, **kwargs)
        if path == root:
            roots.append(fd)
        return fd

    monkeypatch.setattr(os, "open", observe)
    with FileHelper(root) as files:
        for name in ("first", "second"):
            files.delete(name)
        assert len(roots) == 1
        assert os.fstat(roots[0]).st_ino == root.stat().st_ino
    with pytest.raises(OSError) as exc:
        os.fstat(roots[0])
    assert exc.value.errno == errno.EBADF


@pytest.mark.skipif(os.name == "nt", reason="POSIX search-flag fallback")
def test_delete_without_search_flags_supports_readable_parents(root, monkeypatch):
    monkeypatch.delattr(os, "O_SEARCH", raising=False)
    monkeypatch.delattr(os, "O_PATH", raising=False)
    with FileHelper(root) as files:
        files.mkdir("tree/nested", parents=True)
        files.create_text("tree/nested/victim", "selected")
        files.delete("tree", recursive=True)
    assert not (root / "tree").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX search-flag fallback")
def test_delete_without_search_flags_reports_unreadable_parent(root, monkeypatch):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory read permissions")
    monkeypatch.delattr(os, "O_SEARCH", raising=False)
    monkeypatch.delattr(os, "O_PATH", raising=False)
    monkeypatch.setattr(file_helper, "sys", SimpleNamespace(platform="generic-posix"))
    parent = root / "parent"
    parent.mkdir()
    (parent / "victim").write_text("keep")
    with FileHelper(root) as files:
        parent.chmod(0o300)
        try:
            with pytest.raises(PermissionError):
                files.delete(parent / "victim")
            assert (parent / "victim").read_text() == "keep"
        finally:
            parent.chmod(0o700)


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor lifetime")
@pytest.mark.parametrize("depth", [2, 20])
@pytest.mark.parametrize(
    ("recursive", "failure"),
    [(False, None), (False, "unlink"), (True, None), (True, "unlink"), (True, "scan")],
)
def test_delete_closes_directory_descriptors(root, monkeypatch, depth, recursive, failure):
    parent = root / "parent"
    deepest = parent.joinpath(*("d" for _ in range(depth)))
    deepest.mkdir(parents=True)
    victim = deepest / "victim"
    victim.write_text("selected")
    opened = []
    root_opens = []
    open_directory = os.open
    scan_directory = os.scandir
    scans = 0

    def observe(*args, **kwargs):
        fd = open_directory(*args, **kwargs)
        opened.append(fd)
        if args[0] == root.resolve():
            root_opens.append(fd)
        return fd

    def denied(*args, **kwargs):
        raise PermissionError("removal denied")

    def scan(path):
        nonlocal scans
        scans += 1
        if scans == min(depth + 1, 12):
            raise PermissionError("removal denied")
        return scan_directory(path)

    monkeypatch.setattr(os, "open", observe)
    if failure == "unlink":
        monkeypatch.setattr(os, "unlink", denied)
    elif failure == "scan":
        monkeypatch.setattr(os, "scandir", scan)
    with FileHelper(root) as files:
        expected = pytest.raises(PermissionError, match="removal denied") if failure else nullcontext()
        with expected:
            files.delete(parent if recursive else victim, recursive=recursive)
    if failure:
        assert victim.read_text() == "selected"
    else:
        assert not victim.exists()
    assert len(root_opens) == 1
    assert len(opened) >= 2
    for fd in opened:
        with pytest.raises(OSError) as exc:
            os.fstat(fd)
        assert exc.value.errno == errno.EBADF


@pytest.mark.skipif(os.name == "nt", reason="POSIX capability check")
def test_delete_unsupported_backend_does_not_remove(root, monkeypatch):
    (root / "victim").write_text("keep")
    monkeypatch.setattr("specify_cli.file_helper._DELETE_DIR_FD_SUPPORTED", False)
    with pytest.raises(OSError) as exc:
        FileHelper(root).delete("victim")
    assert exc.value.errno == errno.ENOTSUP
    assert (root / "victim").read_text() == "keep"


@pytest.mark.skipif(os.name == "nt", reason="POSIX root descriptor acquisition")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("recursive", [False, True])
def test_delete_rejects_root_ancestor_exchange_at_open(root, link, monkeypatch, allow, recursive):
    ancestor = root / "ancestor"
    project = ancestor / "project"
    project.mkdir(parents=True)
    (project / "tree").mkdir()
    (project / "tree/victim").write_text("selected")
    outside = root / "outside"
    (outside / "project/tree").mkdir(parents=True)
    (outside / "project/tree/victim").write_text("keep")
    retained = root / "retained"
    open_directory = os.open
    attempted = False
    opened = []

    def exchange(path, flags, *args, **kwargs):
        nonlocal attempted
        if not attempted and path == project:
            attempted = True
            ancestor.rename(retained)
            link(ancestor, outside)
        fd = open_directory(path, flags, *args, **kwargs)
        opened.append(fd)
        return fd

    monkeypatch.setattr(os, "open", exchange)
    with pytest.raises(FileHelperError, match="root changed"):
        with FileHelper(project, allow_symlinks=allow) as files:
            files.delete("tree" if recursive else "tree/victim", recursive=recursive)
    assert attempted
    assert (outside / "project/tree/victim").read_text() == "keep"
    assert (retained / "project/tree/victim").read_text() == "selected"
    assert len(opened) == 1
    with pytest.raises(OSError) as exc:
        os.fstat(opened[0])
    assert exc.value.errno == errno.EBADF


@pytest.mark.skipif(os.name == "nt", reason="POSIX root descriptor lifetime")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("recursive", [False, True])
def test_delete_reuses_root_after_ancestor_exchange(root, link, monkeypatch, allow, recursive):
    ancestor = root / "ancestor"
    project = ancestor / "project"
    project.mkdir(parents=True)
    (project / "tree").mkdir()
    (project / "tree/victim").write_text("selected")
    outside = root / "outside"
    (outside / "project/tree").mkdir(parents=True)
    (outside / "project/tree/victim").write_text("keep")
    files = FileHelper(project, allow_symlinks=allow)
    retained = root / "retained"
    check = FileHelper._path
    attempted = False

    def exchange(self, path, **kwargs):
        nonlocal attempted
        result = check(self, path, **kwargs)
        if not attempted:
            attempted = True
            ancestor.rename(retained)
            link(ancestor, outside)
        return result

    monkeypatch.setattr(FileHelper, "_path", exchange)
    files.delete("tree" if recursive else "tree/victim", recursive=recursive)
    assert attempted
    assert (outside / "project/tree/victim").read_text() == "keep"
    assert not (retained / "project/tree/victim").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX retained-root path resolution")
@pytest.mark.parametrize("kind", ["file", "directory", "recursive-tree"])
@pytest.mark.parametrize("target", ["relative", "absolute", "chain", "parent-traversal"])
def test_delete_resolves_links_in_retained_root(root, link, monkeypatch, kind, target):
    ancestor = root / "ancestor"
    project = ancestor / "project"
    outside = root / "outside/project"
    for boundary in (project, outside):
        for name in ("selected", "unrelated"):
            directory = boundary / name
            directory.mkdir(parents=True)
            victim = directory / "victim"
            if kind == "file":
                victim.write_text("keep")
            else:
                victim.mkdir()
                if kind == "recursive-tree":
                    (victim / "child").write_text("keep")
    for boundary, selected in ((project, "selected"), (outside, "unrelated")):
        if target == "absolute":
            destination = boundary / selected
        elif target == "chain":
            link(boundary / "first", selected)
            destination = "first"
        elif target == "parent-traversal":
            (boundary / "nested").mkdir()
            destination = f"nested/../{selected}"
        else:
            destination = selected
        link(boundary / "alias", destination)
    files = FileHelper(project, allow_symlinks=True)
    retained = root / "retained"
    acquire = FileHelper._deletion_root

    @contextmanager
    def exchange(self):
        with acquire(self) as handle:
            ancestor.rename(retained)
            link(ancestor, outside.parent)
            yield handle

    monkeypatch.setattr(FileHelper, "_deletion_root", exchange)
    files.delete("alias/victim", recursive=kind == "recursive-tree")
    assert not (retained / "project/selected/victim").exists()
    assert (retained / "project/unrelated/victim").exists()
    assert (retained / "project/alias").is_symlink()
    assert (outside / "selected/victim").exists()
    assert (outside / "unrelated/victim").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX retained-root preflight")
def test_delete_classifies_descendants_in_retained_root(root, link, monkeypatch):
    ancestor = root / "ancestor"
    project = ancestor / "project"
    outside = root / "outside/project"
    for boundary in (project, outside):
        (boundary / "tree").mkdir(parents=True)
        (boundary / "tree/a-file").write_text("keep")
    link(project / "tree/z-link", root / "missing")
    (outside / "tree/z-link").write_text("replacement")
    files = FileHelper(project)
    retained = root / "retained"
    acquire = FileHelper._deletion_root

    @contextmanager
    def exchange(self):
        with acquire(self) as handle:
            ancestor.rename(retained)
            link(ancestor, outside.parent)
            yield handle

    monkeypatch.setattr(FileHelper, "_deletion_root", exchange)
    with pytest.raises(SymlinkDeniedError):
        files.delete("tree", recursive=True)
    assert (retained / "project/tree/a-file").read_text() == "keep"
    assert (retained / "project/tree/z-link").is_symlink()
    assert (outside / "tree/z-link").read_text() == "replacement"


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor-relative metadata")
@pytest.mark.parametrize("recursive", [False, True])
def test_delete_metadata_and_links_use_retained_descriptors(root, link, monkeypatch, recursive):
    (root / "selected/tree").mkdir(parents=True)
    (root / "selected/tree/victim").write_text("selected")
    link(root / "alias", "selected")
    files = FileHelper(root, allow_symlinks=True)
    acquire = FileHelper._deletion_root
    stat_entry = os.stat
    readlink = os.readlink
    calls = []

    def relative_stat(path, *args, **kwargs):
        assert isinstance(kwargs.get("dir_fd"), int)
        assert kwargs.get("follow_symlinks") is False
        assert not Path(path).is_absolute()
        calls.append("stat")
        return stat_entry(path, *args, **kwargs)

    def relative_readlink(path, *args, **kwargs):
        assert isinstance(kwargs.get("dir_fd"), int)
        assert not Path(path).is_absolute()
        calls.append("readlink")
        return readlink(path, *args, **kwargs)

    def no_path_metadata(*args, **kwargs):
        pytest.fail("Deletion metadata must not reopen an absolute pathname")

    @contextmanager
    def observe(self):
        with acquire(self) as handle, monkeypatch.context() as scoped:
            scoped.setattr(Path, "lstat", no_path_metadata)
            scoped.setattr(os, "stat", relative_stat)
            scoped.setattr(os, "readlink", relative_readlink)
            yield handle

    monkeypatch.setattr(FileHelper, "_deletion_root", observe)
    files.delete("alias/tree" if recursive else "alias/tree/victim", recursive=recursive)
    assert "stat" in calls and "readlink" in calls
    assert not (root / "selected/tree/victim").exists()
    assert (root / "alias").is_symlink()


@pytest.mark.skipif(os.name == "nt", reason="POSIX retained-root revalidation")
@pytest.mark.parametrize("recursive", [False, True])
def test_delete_revalidates_entries_in_retained_root(root, link, monkeypatch, recursive):
    ancestor = root / "ancestor"
    project = ancestor / "project"
    (project / "selected").mkdir(parents=True)
    (project / "selected/victim").write_text("selected")
    outside = root / "outside/project"
    outside.mkdir(parents=True)
    link(outside / "selected", root / "missing")
    files = FileHelper(project)
    retained = root / "retained"
    plan = FileHelper._deletion_plan
    selected = project / ("selected" if recursive else "selected/victim")
    attempted = False

    def exchange(self, path, **kwargs):
        nonlocal attempted
        result = plan(self, path, **kwargs)
        if path == selected:
            attempted = True
            ancestor.rename(retained)
            link(ancestor, outside.parent)
        return result

    monkeypatch.setattr(FileHelper, "_deletion_plan", exchange)
    files.delete(selected, recursive=recursive)
    assert attempted
    assert not (retained / "project/selected/victim").exists()
    assert (outside / "selected").is_symlink()


@pytest.mark.parametrize(
    ("kind", "error"),
    [
        ("dangling", FileNotFoundError),
        ("cycle", UnsupportedPathError),
        ("excessive", UnsupportedPathError),
        ("non-directory", NotADirectoryError),
        ("escape-and-return", PathEscapeError),
    ],
)
def test_delete_parent_link_targets_preserve_failure_contract(root, link, kind, error):
    (root / "target").mkdir()
    (root / "target/victim").write_text("keep")
    if kind == "dangling":
        target = "missing"
    elif kind == "cycle":
        target = "alias"
    elif kind == "excessive":
        for index in reversed(range(41)):
            link(root / f"chain-{index}", "target" if index == 40 else f"chain-{index + 1}")
        target = "chain-0"
    elif kind == "non-directory":
        (root / "file").write_text("keep")
        target = "file/../target"
    else:
        target = f"../{root.name}/target"
    link(root / "alias", target)
    with pytest.raises(error):
        FileHelper(root, allow_symlinks=True).delete("alias/victim")
    assert (root / "target/victim").read_text() == "keep"
    assert (root / "alias").is_symlink()


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions")
@pytest.mark.parametrize("parent_is_root", [False, True])
@pytest.mark.parametrize("kind", ["file", "empty-directory", "recursive-tree"])
def test_delete_through_write_execute_only_parent(root, parent_is_root, kind):
    if not (sys.platform == "darwin" or getattr(os, "O_SEARCH", 0) or getattr(os, "O_PATH", 0)):
        pytest.skip("Search/path-only directory descriptors are unavailable")
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory read permissions")
    parent = root if parent_is_root else root / "parent"
    parent.mkdir(exist_ok=True)
    control = parent / "control"
    control.write_text("control")
    victim = parent / "victim"
    if kind == "file":
        victim.write_text("selected")
    else:
        victim.mkdir()
        if kind == "recursive-tree":
            (victim / "child").write_text("selected")
    files = FileHelper(root)
    parent.chmod(0o300)
    try:
        control.unlink()
        files.delete(victim, recursive=kind == "recursive-tree")
        assert not victim.exists()
    finally:
        parent.chmod(0o700)


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions")
@pytest.mark.parametrize("mode", [0o400, 0o600, 0o444, 0o644])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_recursive_delete_readable_empty_directory_without_search(root, mode, nested, allow):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory permission checks")
    tree = root / "tree"
    tree.mkdir()
    restricted = tree
    if nested:
        (tree / "a-first").write_text("selected")
        restricted = tree / "z-empty"
        restricted.mkdir()
    restricted.chmod(mode)
    try:
        with FileHelper(root, allow_symlinks=allow) as files:
            files.delete(tree, recursive=True)
        assert not tree.exists()
    finally:
        if restricted.exists():
            restricted.chmod(0o700)


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions")
@pytest.mark.parametrize("mode", [0o400, 0o600])
@pytest.mark.parametrize("allow", [False, True])
def test_recursive_delete_nonempty_directory_without_search_fails_preflight(root, mode, allow):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory permission checks")
    tree = root / "tree"
    restricted = tree / "z-restricted"
    restricted.mkdir(parents=True)
    (tree / "a-first").write_text("keep")
    (restricted / "victim").write_text("keep")
    restricted.chmod(mode)
    try:
        with FileHelper(root, allow_symlinks=allow) as files:
            with pytest.raises(PermissionError):
                files.delete(tree, recursive=True)
        assert (tree / "a-first").read_text() == "keep"
    finally:
        restricted.chmod(0o700)
    assert (restricted / "victim").read_text() == "keep"


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions")
@pytest.mark.parametrize("nonempty", [False, True])
def test_recursive_delete_still_requires_read_permission_for_enumeration(root, nonempty):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory read permissions")
    tree = root / "tree"
    tree.mkdir()
    if nonempty:
        (tree / "victim").write_text("keep")
    tree.chmod(0o300)
    try:
        with FileHelper(root) as files:
            with pytest.raises(PermissionError):
                files.delete(tree, recursive=True)
        if nonempty:
            assert (tree / "victim").read_text() == "keep"
        else:
            assert tree.is_dir()
    finally:
        tree.chmod(0o700)


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions")
def test_delete_still_requires_write_permission_on_parent(root):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory write permissions")
    parent = root / "parent"
    parent.mkdir()
    (parent / "victim").write_text("keep")
    parent.chmod(0o100)
    try:
        with pytest.raises(PermissionError):
            FileHelper(root).delete(parent / "victim")
        assert (parent / "victim").read_text() == "keep"
    finally:
        parent.chmod(0o700)


@pytest.mark.parametrize("allow", [False, True])
def test_delete_rejects_replaced_root_before_validation(root, monkeypatch, allow):
    (root / "victim").write_text("selected")
    files = FileHelper(root, allow_symlinks=allow)
    retained = root.parent / "retained"
    root.rename(retained)
    root.mkdir()
    (root / "victim").write_text("keep")

    def unexpected(*args, **kwargs):
        pytest.fail("A replacement root must be rejected before path validation")

    monkeypatch.setattr(FileHelper, "_path", unexpected)
    with pytest.raises(FileHelperError, match="root changed"):
        files.delete("victim")
    assert (root / "victim").read_text() == "keep"
    assert (retained / "victim").read_text() == "selected"


def test_windows_delete_rejects_replaced_root_during_acquisition_portably(
    root, link, monkeypatch
):
    import specify_cli.file_helper as module

    ancestor = root / "ancestor"
    project = ancestor / "project"
    project.mkdir(parents=True)
    (project / "victim").write_text("selected")
    outside = root / "outside"
    (outside / "project").mkdir(parents=True)
    (outside / "project/victim").write_text("keep")
    retained = root / "retained"
    active = []
    identities = {}
    metadata = {}
    attempted = False

    @contextmanager
    def handle(path, *, directory, pin=True):
        nonlocal attempted
        assert directory
        value = len(identities) + 1
        active.append(path)
        try:
            if pin and path == project:
                # Simulate a replacement just before the root handle is acquired.
                attempted = True
                ancestor.rename(retained)
                link(ancestor, outside)
            metadata[value] = path.stat()
            identities[value] = (1, b"replacement" if attempted else b"original")
            yield value
        finally:
            assert active.pop() == path

    backend = SimpleNamespace(**vars(os))
    backend.name = "nt"
    monkeypatch.setattr(module, "os", backend)
    monkeypatch.setattr(module, "_windows_handle", handle)
    monkeypatch.setattr(
        module, "_windows_file_id",
        lambda value, **kwargs: _WindowsFileIdentity("fileid128", *identities[value]),
    )
    monkeypatch.setattr(module, "_windows_stat", lambda value: metadata[value])
    with FileHelper(project) as files:
        assert not attempted
        with pytest.raises(FileHelperError, match="root changed"):
            files.delete("victim")
        assert active == [project]
    assert attempted
    assert active == []
    assert (outside / "project/victim").read_text() == "keep"
    assert (retained / "project/victim").read_text() == "selected"


@pytest.mark.parametrize("kind", ["file", "directory", "recursive"])
def test_windows_link_resolution_pins_accessed_parents_portably(
    root, link, monkeypatch, kind, windows_delete_model
):
    parent = root / "parent"
    parent.mkdir()
    outside = root.parent / "outside"
    outside.mkdir()
    selected = root / "selected"
    unrelated = root / "unrelated"
    for directory in (selected, unrelated):
        directory.mkdir()
        if kind == "file":
            (directory / "victim").write_text("keep")
        else:
            (directory / "victim").mkdir()
            if kind == "recursive":
                (directory / "victim/child").write_text("keep")
    link(parent / "alias", selected)
    link(outside / "alias", unrelated)
    retained = root / "retained"
    pinned = []
    attempted = False
    blocked = False
    lstat = Path.lstat

    @contextmanager
    def handle(path, *, directory, pin=True, parent=None):
        assert directory
        actual = path if parent is None else windows_delete_model.locations[parent] / path
        if pin:
            pinned.append(actual)
        try:
            with windows_delete_model.opened(path, parent=parent) as value:
                yield value
        finally:
            if pin:
                assert pinned.pop() == actual

    def exchange(path, **kwargs):
        nonlocal attempted, blocked
        if path == parent / "alias" and not attempted:
            attempted = True
            blocked = parent in pinned
            if not blocked:
                parent.rename(retained)
                link(parent, outside)
        return lstat(path, **kwargs)

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", handle)
    monkeypatch.setattr(
        file_helper, "_windows_file_id",
        lambda _, **kwargs: _WindowsFileIdentity("fileid128", 1, b"root"),
    )
    monkeypatch.setattr(file_helper, "_windows_stat", lambda _: root.stat())
    monkeypatch.setattr(Path, "lstat", exchange)
    with FileHelper(root, allow_symlinks=True) as files:
        files.delete("parent/alias/victim", recursive=kind == "recursive")
    assert attempted
    assert (unrelated / "victim").exists()
    assert not (selected / "victim").exists()
    assert blocked
    assert (parent / "alias").is_symlink()
    assert pinned == []


@pytest.mark.skipif(os.name != "nt", reason="Native Windows directory-handle semantics")
def test_native_windows_link_resolution_blocks_accessed_parent_exchange(root, link, monkeypatch):
    parent = root / "parent"
    parent.mkdir()
    selected = root / "selected"
    selected.mkdir()
    (selected / "victim").write_text("selected")
    link(parent / "alias", selected)
    attempted = False
    original_entry = file_helper._windows_entry

    @contextmanager
    def exchange(directory, name, *, deleting=False):
        nonlocal attempted
        with original_entry(directory, name, deleting=deleting) as handle:
            if name == "alias" and not attempted:
                attempted = True
                with pytest.raises(PermissionError):
                    parent.rename(root / "retained")
            yield handle

    monkeypatch.setattr(file_helper, "_windows_entry", exchange)
    with FileHelper(root, allow_symlinks=True) as files:
        files.delete("parent/alias/victim")
    assert attempted
    assert not (selected / "victim").exists()
    parent.rename(root / "retained")


@pytest.mark.parametrize("error_number", [errno.EINVAL, errno.EACCES])
def test_windows_walk_preserves_parent_type_and_access_errors_portably(
    root, monkeypatch, error_number
):
    @contextmanager
    def denied(*args, **kwargs):
        raise OSError(error_number, "directory unavailable")
        yield

    monkeypatch.setattr(file_helper, "_windows_handle", denied)
    expected = NotADirectoryError if error_number == errno.EINVAL else PermissionError
    with file_helper.ExitStack() as resources:
        directories = file_helper._WalkDirectories(
            root, file_helper._WindowsDirectory(root, 123), 0, resources
        )
        with pytest.raises(expected):
            directories.directory(root / "child")


def test_windows_constructor_rejects_replaced_then_restored_root(root, monkeypatch):
    project = root / "project"
    replacement = root / "replacement"
    saved = root / "saved"
    project.mkdir()
    replacement.mkdir()
    (project / "victim").write_text("selected")
    (replacement / "victim").write_text("keep")
    acquired = {}
    active = []

    @contextmanager
    def handle(path, *, directory, pin=True):
        assert path == project and directory and not pin
        project.rename(saved)
        replacement.rename(project)
        acquired[123] = project.stat()
        project.rename(replacement)
        saved.rename(project)
        active.append(123)
        try:
            yield 123
        finally:
            assert active.pop() == 123

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", handle)
    monkeypatch.setattr(
        file_helper, "_windows_file_id",
        lambda _, **kwargs: _WindowsFileIdentity("fileid128", 1, b"replacement"),
    )
    monkeypatch.setattr(file_helper, "_windows_stat", lambda value: acquired[value], raising=False)
    with pytest.raises(FileHelperError, match="root changed"):
        with FileHelper(project):
            pytest.fail("A handle to the replacement root must not be accepted")
    assert active == []
    assert (project / "victim").read_text() == "selected"
    assert (replacement / "victim").read_text() == "keep"


@pytest.mark.parametrize("simulate_missing_winerror", [False, True])
def test_windows_cached_capability_error_has_independent_tracebacks(
    root, monkeypatch, simulate_missing_winerror
):
    native = PermissionError(errno.EACCES, "reference denied", "source", 5, "destination")
    if not hasattr(native, "winerror"):
        native.winerror = 5
    if simulate_missing_winerror:
        original_copy = file_helper.copy

        def copy_without_winerror(error):
            result = original_copy(error)
            result.winerror = None
            return result

        monkeypatch.setattr(file_helper, "copy", copy_without_winerror)

    @contextmanager
    def denied(*args, **kwargs):
        raise native
        yield

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", denied)
    with FileHelper(root) as files:
        errors = []
        for _ in range(3):
            with pytest.raises(PermissionError) as raised:
                files.delete("victim")
            errors.append(raised.value)
            assert files._root_anchor_error is native
            assert native.__traceback__ is None
        assert len({id(error) for error in errors}) == 3
        for error in errors:
            assert error is not native and type(error) is type(native)
            assert (error.errno, error.strerror, error.filename, error.filename2, error.winerror) == (
                native.errno, native.strerror, native.filename, native.filename2, native.winerror,
            )
            assert error.__traceback__ is not None


@pytest.fixture
def windows_victim_read_fd(root, monkeypatch):
    @contextmanager
    def duplicate(handle):
        with (root / "victim").open("rb") as stream:
            yield stream.fileno()

    monkeypatch.setattr(file_helper, "windows_read_fd", duplicate)


def test_windows_read_does_not_require_ancestor_listing_portably(
    root, monkeypatch, windows_victim_read_fd
):
    (root / "victim").write_text("keep")
    active = []

    @contextmanager
    def handle(path, *, directory, pin=True, parent=None, traverse=False):
        if pin and directory and not traverse and path != root:
            raise PermissionError("ancestor listing denied")
        active.append((path, pin))
        try:
            yield 123
        finally:
            assert active.pop() == (path, pin)

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", handle)
    monkeypatch.setattr(
        file_helper, "_windows_file_id",
        lambda _, **kwargs: _WindowsFileIdentity("fileid128", 1, b"root"),
    )
    monkeypatch.setattr(file_helper, "_windows_stat", lambda _: root.stat())
    with FileHelper(root) as files:
        assert files.read_text("victim") == "keep"
        with pytest.raises(PermissionError, match="ancestor listing denied"):
            files.delete("victim")
        assert files.read_text("victim") == "keep"
    assert active == []


@pytest.mark.parametrize("failure", ["open", "identity"])
def test_windows_read_preserves_native_deletion_capability_error(
    root, monkeypatch, failure, windows_victim_read_fd
):
    (root / "victim").write_text("keep")
    active = []

    @contextmanager
    def denied(*args, **kwargs):
        if failure == "open" and not kwargs.get("pin", True):
            raise PermissionError("root reference denied")
        active.append(123)
        try:
            yield 123
        finally:
            active.pop()

    def identity(*args):
        raise PermissionError("root reference denied")

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", denied)
    monkeypatch.setattr(file_helper, "_windows_file_id", identity)
    monkeypatch.setattr(file_helper, "_windows_stat", lambda _: root.stat())
    with FileHelper(root) as files:
        assert active == []
        assert files.read_text("victim") == "keep"
        with pytest.raises(PermissionError, match="root reference denied"):
            files.delete("victim")
    assert not files._root_cleanup.alive


def test_windows_delete_checks_retained_handle_identity_portably(
    root, monkeypatch, windows_victim_read_fd
):
    (root / "victim").write_text("keep")
    active = []
    identities = {}

    @contextmanager
    def handle(path, *, directory, pin=True, parent=None, traverse=False):
        value = len(identities) + 1
        identities[value] = (1, b"replacement" if pin else b"original")
        active.append(value)
        try:
            yield value
        finally:
            assert active.pop() == value

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", handle)
    monkeypatch.setattr(
        file_helper, "_windows_file_id",
        lambda value, **kwargs: _WindowsFileIdentity("fileid128", *identities[value]),
    )
    monkeypatch.setattr(file_helper, "_windows_stat", lambda _: root.stat())
    with FileHelper(root) as files:
        with pytest.raises(FileHelperError, match="root changed"):
            files.delete("victim")
        assert len(active) == 1
        assert files.read_text("victim") == "keep"
    assert active == []


@pytest.mark.parametrize("scenario", ["same", "renamed-reference", "replacement-reused-id"])
@pytest.mark.parametrize("recursive", [False, True])
def test_windows_legacy_root_identity_is_compared_live_with_the_selected_scheme(
    root, monkeypatch, scenario, recursive, windows_delete_model
):
    (root / "tree").mkdir()
    (root / "tree/victim").write_text("keep")
    active = []
    reference = None
    queries = []
    changed = False

    @contextmanager
    def handle(path, *, directory, pin=True, parent=None):
        nonlocal reference
        assert directory
        with windows_delete_model.opened(path, parent=parent) as value:
            active.append(value)
            if not pin:
                reference = value
            try:
                yield value
            finally:
                assert active.pop() == value

    def identity(value, *, kind=None):
        queries.append((value, kind))
        assert kind in (None, "legacy64")
        index = 1
        if changed and scenario != "same":
            index = 2 if value == reference or scenario == "renamed-reference" else 1
        return _WindowsFileIdentity("legacy64", 1, index.to_bytes(8, "little"))

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", handle)
    monkeypatch.setattr(file_helper, "_windows_file_id", identity)
    monkeypatch.setattr(file_helper, "_windows_stat", lambda _: root.stat())
    with FileHelper(root) as files:
        assert files._windows_root_id is not None
        assert files._windows_root_id.kind == "legacy64"
        changed = True
        selected = "tree" if recursive else "tree/victim"
        if scenario == "replacement-reused-id":
            with pytest.raises(FileHelperError, match="root changed"):
                files.delete(selected, recursive=recursive)
            assert (root / "tree/victim").read_text() == "keep"
        else:
            files.delete(selected, recursive=recursive)
            assert not (root / "tree/victim").exists()
        assert active == [reference]
    assert active == []
    assert queries[0] == (reference, None)
    assert len(queries) == 3
    assert queries[-1] == (reference, "legacy64")
    assert all(kind == "legacy64" for _, kind in queries[1:])


@pytest.mark.skipif(os.name != "nt", reason="Native Windows directory ACL semantics")
@pytest.mark.parametrize("consumer", ["helper", "policy", "state"])
def test_windows_readonly_helper_supports_traverse_only_ancestor(root, consumer):
    ancestor = root / "ancestor"
    project = ancestor / "project"
    project.mkdir(parents=True)
    (project / "victim").write_text("keep")
    (project / ".specify").mkdir()
    (project / ".specify/init-options.json").write_text("{}")
    (project / ".specify/integration.json").write_text('{"integration": "claude"}')
    user = subprocess.check_output(["whoami"], text=True).strip()
    subprocess.run(
        ["icacls", str(ancestor), "/deny", f"{user}:(RD)"],
        check=True, capture_output=True, text=True,
    )
    try:
        with FileHelper(project) as files:
            if consumer == "helper":
                assert files.read_text("victim") == "keep"
            elif consumer == "policy":
                from specify_cli._file_policy import read_project_options
                assert read_project_options(project) == {}
            else:
                from specify_cli.integration_state import try_read_integration_json
                state, error = try_read_integration_json(project)
                assert error is None and state is not None and state["integration"] == "claude"
            with pytest.raises(PermissionError):
                files.delete("victim")
            assert files.read_text("victim") == "keep"
    finally:
        subprocess.run(
            ["icacls", str(ancestor), "/remove:d", user],
            check=True, capture_output=True, text=True,
        )


@pytest.mark.parametrize("failure", [False, True])
@pytest.mark.parametrize("recursive", [False, True])
def test_windows_delete_holds_ancestors_until_io_completes_portably(
    root, link, monkeypatch, failure, recursive, windows_delete_model
):
    import specify_cli.file_helper as module

    parent = root / "target/nested"
    parent.mkdir(parents=True)
    (parent / "victim").write_text("selected")
    alias = link(root / "alias", root / "target")
    active = []
    references = []
    events = []

    @contextmanager
    def handle(path, *, directory, pin=True, parent=None):
        assert directory
        actual = path if parent is None else windows_delete_model.locations[parent] / path
        selected_handles = active if pin else references
        selected_handles.append(actual)
        try:
            with windows_delete_model.opened(path, parent=parent) as value:
                yield value
        finally:
            assert selected_handles.pop() == actual

    def assert_anchored(handle):
        assert handle in windows_delete_model.locations
        assert active[0] == Path(root.anchor)
        assert root.resolve() in active
        assert all(not part.is_symlink() for part in active)
        events.append(windows_delete_model.locations[handle])

    def observe_scan(handle):
        assert_anchored(handle)
        return windows_delete_model.names(handle)

    def remove(handle):
        assert_anchored(handle)
        if failure:
            raise PermissionError("removal denied")
        windows_delete_model.remove(handle)

    backend = SimpleNamespace(**vars(os))
    backend.name = "nt"
    monkeypatch.setattr(module, "os", backend)
    monkeypatch.setattr(module, "_windows_handle", handle)
    monkeypatch.setattr(module, "_windows_directory_names", observe_scan)
    monkeypatch.setattr(module, "_windows_delete", remove)
    monkeypatch.setattr(
        module, "_windows_file_id",
        lambda _, **kwargs: _WindowsFileIdentity("fileid128", 1, b"root"),
    )
    monkeypatch.setattr(module, "_windows_stat", lambda _: root.stat())
    files = FileHelper(root, allow_symlinks=True)
    selected = alias / "nested" if recursive else alias / "nested/victim"
    if failure:
        with pytest.raises(PermissionError, match="removal denied"):
            files.delete(selected, recursive=recursive)
        assert (parent / "victim").read_text() == "selected"
    else:
        files.delete(selected, recursive=recursive)
        assert not (parent / "victim").exists()
    assert events
    assert active == []
    assert references == [root.resolve()]
    files.close()
    assert references == []
    assert alias.is_symlink()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor model of native Windows handles")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("recursive", [False, True])
def test_windows_deletion_does_not_reopen_changed_parent_path(
    root, link, monkeypatch, allow, recursive
):
    parent = root / "tree"
    parent.mkdir()
    victim = parent / "victim"
    victim.write_text("selected")
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "victim").write_text("keep")
    retained = root / "retained"
    opened = {}
    changed = False

    @contextmanager
    def handle(path, *, directory, parent=None, **kwargs):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def entry(parent, name, *, deleting=False):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        opened[fd] = (parent, name)
        try:
            yield fd
        finally:
            del opened[fd]
            os.close(fd)

    @contextmanager
    def anchored_root(self):
        with handle(root, directory=True) as fd:
            wrapper = getattr(file_helper, "_WindowsDirectory", None)
            yield root if wrapper is None else wrapper(root, fd)

    def names(fd):
        with os.scandir(fd) as entries:
            return [item.name for item in entries]

    def remove(fd):
        directory, name = opened[fd]
        selected = os.fstat(fd)
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if not os.path.samestat(selected, current):
            raise OSError(errno.ESTALE, "Model cannot remove an object renamed after opening")
        if stat.S_ISDIR(selected.st_mode):
            os.rmdir(name, dir_fd=directory)
        else:
            os.unlink(name, dir_fd=directory)

    original_delete = FileHelper._delete_plan

    def exchange(self, selected, **kwargs):
        nonlocal changed
        if selected.path == victim and not changed:
            changed = True
            parent.rename(retained)
            link(parent, outside)
        return original_delete(self, selected, **kwargs)

    monkeypatch.setattr(file_helper, "_windows_handle", handle)
    monkeypatch.setattr(file_helper, "_windows_entry", entry, raising=False)
    monkeypatch.setattr(file_helper, "_windows_mode", lambda fd: os.fstat(fd).st_mode, raising=False)
    monkeypatch.setattr(file_helper, "_windows_directory_names", names, raising=False)
    monkeypatch.setattr(file_helper, "_windows_delete", remove, raising=False)
    monkeypatch.setattr(FileHelper, "_deletion_root", anchored_root)
    monkeypatch.setattr(FileHelper, "_delete_plan", exchange)
    with FileHelper(root, allow_symlinks=allow) as files:
        try:
            files.delete(parent if recursive else victim, recursive=recursive)
        except OSError:
            assert changed
    assert changed
    assert (outside / "victim").read_text() == "keep"
    assert not (retained / "victim").exists()
    assert opened == {}


@pytest.mark.parametrize("allow", [False, True])
def test_delete_through_trusted_root_alias(root, link, allow):
    alias = link(root.parent / "alias", root)
    (root / "tree/nested").mkdir(parents=True)
    (root / "tree/nested/file").write_text("selected")
    FileHelper(alias, allow_symlinks=allow).delete(alias / "tree", recursive=True)
    assert alias.is_symlink()
    assert root.is_dir()
    assert not (root / "tree").exists()


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
    files = FileHelper(root, allow_symlinks=True)
    opened = []
    real_open = os.open

    def recording_open(path, flags, mode):
        opened.append(Path(path))
        return real_open(path, flags, mode)

    monkeypatch.setattr("specify_cli.file_helper.os.open", recording_open)
    content = b"bad" if operation == "create_bytes" else "bad"
    with pytest.raises(FileExistsError) as error:
        getattr(files, operation)(alias, content)
    files.close()
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


@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("ancestor", ["parent", "parent/nested"])
def test_exclusive_create_rejects_parent_exchange_after_validation(
    root, link, monkeypatch, operation, allow, ancestor
):
    destination = root / "parent/nested/new"
    destination.parent.mkdir(parents=True)
    parent = root / ancestor
    retained = parent.with_name("retained")
    outside = root.parent / "outside"
    outside.mkdir()
    redirected = outside / destination.relative_to(parent)
    redirected.parent.mkdir(parents=True, exist_ok=True)
    files = FileHelper(root, allow_symlinks=allow)
    original_path = FileHelper._path

    def exchange_after_validation(self, path, **kwargs):
        destination = original_path(self, path, **kwargs)
        parent.rename(retained)
        link(parent, outside)
        return destination

    monkeypatch.setattr(FileHelper, "_path", exchange_after_validation)
    content = b"new" if operation == "create_bytes" else "new"
    with pytest.raises(OSError):
        getattr(files, operation)(destination, content)
    assert not redirected.exists()
    assert not (retained / destination.relative_to(parent)).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor-relative creation")
@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("ancestor", ["parent", "parent/nested"])
def test_exclusive_create_uses_open_parent_after_exchange(
    root, link, monkeypatch, operation, allow, ancestor
):
    destination = root / "parent/nested/new"
    destination.parent.mkdir(parents=True)
    parent = root / ancestor
    retained = parent.with_name("retained")
    outside = root.parent / "outside"
    outside.mkdir()
    redirected = outside / destination.relative_to(parent)
    redirected.parent.mkdir(parents=True, exist_ok=True)
    original_open = os.open
    exchanged = False

    def exchange_before_create(path, flags, *args, **kwargs):
        nonlocal exchanged
        if flags & os.O_CREAT:
            parent.rename(retained)
            link(parent, outside)
            exchanged = True
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", exchange_before_create)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {exchange_before_create})
    content = b"new" if operation == "create_bytes" else "new"
    getattr(FileHelper(root, allow_symlinks=allow), operation)(destination, content)
    assert exchanged
    assert not redirected.exists()
    assert (retained / destination.relative_to(parent)).read_bytes() == b"new"


@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("absolute", [False, True])
def test_exclusive_create_preserves_contained_parent_chain(
    root, link, operation, allow, absolute
):
    target = root / "target/nested"
    target.mkdir(parents=True)
    first = link(root / "first", root / "target" if absolute else "target")
    second = link(root / "second", first if absolute else "first")
    path = second / "nested/new"
    files = FileHelper(root, allow_symlinks=allow)
    content = b"\x00\xff" if operation == "create_bytes" else "caf\u00e9\n"
    if allow:
        kwargs = {"encoding": "utf-16"} if operation == "create_text" else {}
        getattr(files, operation)(path, content, **kwargs)
        expected = content if isinstance(content, bytes) else content.encode("utf-16")
        assert (target / "new").read_bytes() == expected
    else:
        with pytest.raises(SymlinkDeniedError):
            getattr(files, operation)(path, content)
        assert not (target / "new").exists()
    assert first.is_symlink() and second.is_symlink()


@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
def test_exclusive_create_accepts_trusted_root_alias(root, link, operation, allow):
    alias = link(root.parent / "root-alias", root)
    ancestor = link(root.parent / "ancestor-alias", root.parent)
    content = b"new" if operation == "create_bytes" else "new"
    for index, supplied in enumerate((alias, ancestor / root.name)):
        files = FileHelper(supplied, allow_symlinks=allow)
        getattr(files, operation)(supplied / f"new-{index}", content)
        assert (root / f"new-{index}").read_bytes() == b"new"
    assert alias.is_symlink() and ancestor.is_symlink()


@pytest.mark.skipif(os.name == "nt", reason="POSIX exclusive no-follow leaf open")
@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "dangling"])
def test_exclusive_create_rejects_leaf_inserted_at_open(
    root, link, monkeypatch, operation, allow, kind
):
    (root / "parent").mkdir()
    outside = root.parent / "outside"
    if kind != "dangling":
        outside.write_bytes(b"keep")
    destination = root / "parent/new"
    real_open = os.open
    attempted = False

    def insert_leaf(path, flags, *args, **kwargs):
        nonlocal attempted
        if flags & os.O_CREAT:
            attempted = True
            if kind == "file":
                destination.write_bytes(b"keep")
            elif kind == "directory":
                destination.mkdir()
            else:
                link(destination, outside)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", insert_leaf)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {insert_leaf})
    content = b"new" if operation == "create_bytes" else "new"
    with pytest.raises(FileExistsError):
        getattr(FileHelper(root, allow_symlinks=allow), operation)(destination, content)
    assert attempted
    if kind == "file":
        assert destination.read_bytes() == b"keep"
    elif kind == "directory":
        assert list(destination.iterdir()) == []
    else:
        assert destination.is_symlink()
    if kind == "dangling":
        assert not outside.exists()
    else:
        assert outside.read_bytes() == b"keep"


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode and umask semantics")
@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
def test_exclusive_create_preserves_mode_and_umask(root, operation, allow):
    previous = os.umask(0o027)
    try:
        content = b"new" if operation == "create_bytes" else "new"
        getattr(FileHelper(root, allow_symlinks=allow), operation)("new", content, mode=0o666)
    finally:
        os.umask(previous)
    assert (root / "new").stat().st_mode & 0o777 == 0o640


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions")
@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("ancestor", [".", "parent", "parent/nested"])
@pytest.mark.parametrize("permissions", [0o300, 0o200])
@pytest.mark.parametrize(
    "search_api",
    [
        "default",
        pytest.param(
            "legacy-macos",
            marks=pytest.mark.skipif(
                sys.platform != "darwin", reason="macOS search-only directory handles"
            ),
        ),
    ],
)
def test_exclusive_create_respects_write_and_search_permissions(
    root, monkeypatch, operation, allow, ancestor, permissions, search_api
):
    if os.geteuid() == 0:
        pytest.skip("Root bypasses directory permission checks")
    if search_api == "legacy-macos":
        monkeypatch.delattr(os, "O_PATH", raising=False)
        monkeypatch.delattr(os, "O_SEARCH", raising=False)
    (root / "parent/nested").mkdir(parents=True)
    files = FileHelper(root, allow_symlinks=allow)
    restricted = root / ancestor
    content = b"new" if operation == "create_bytes" else "new"
    restricted.chmod(permissions)
    try:
        if permissions == 0o300:
            getattr(files, operation)("parent/nested/new", content)
            assert (root / "parent/nested/new").read_bytes() == b"new"
        else:
            with pytest.raises(PermissionError):
                getattr(files, operation)("parent/nested/new", content)
    finally:
        restricted.chmod(0o700)
    if permissions == 0o200:
        assert not (root / "parent/nested/new").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory descriptor traversal")
@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
def test_exclusive_create_bounds_live_parent_descriptors(root, monkeypatch, operation, allow):
    destination = root.joinpath(*("nested" for _ in range(32)), "new")
    destination.parent.mkdir(parents=True)
    files = FileHelper(root, allow_symlinks=allow)
    real_open = os.open
    real_close = os.close
    live = set()
    maximum = 0

    def limited_open(path, flags, *args, **kwargs):
        nonlocal maximum
        if len(live) >= 2:
            raise OSError(errno.EMFILE, "parent descriptor budget exhausted")
        fd = real_open(path, flags, *args, **kwargs)
        if flags & os.O_DIRECTORY:
            live.add(fd)
            maximum = max(maximum, len(live))
        return fd

    def observe_close(fd):
        real_close(fd)
        live.remove(fd)

    monkeypatch.setattr(os, "open", limited_open)
    monkeypatch.setattr(os, "close", observe_close)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {limited_open})
    content = b"new" if operation == "create_bytes" else "new"
    getattr(files, operation)(destination, content)
    assert destination.read_bytes() == b"new"
    assert maximum == 2
    assert live == set()


@pytest.mark.parametrize("encoding", ["ascii", "unknown-encoding"])
def test_exclusive_create_text_encoding_failure_precedes_creation(root, encoding):
    with pytest.raises((UnicodeEncodeError, LookupError)):
        FileHelper(root).create_text("new", "caf\u00e9", encoding=encoding)
    assert not (root / "new").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX capability checks")
@pytest.mark.parametrize("capability", ["O_NOFOLLOW", "O_DIRECTORY", "supports_dir_fd"])
def test_exclusive_create_requires_anchored_io(root, monkeypatch, capability):
    monkeypatch.setattr(os, capability, set() if capability == "supports_dir_fd" else 0)
    with pytest.raises(OSError) as error:
        FileHelper(root).create_bytes("new", b"new")
    assert error.value.errno == errno.ENOTSUP
    assert not (root / "new").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory descriptor lifetimes")
@pytest.mark.parametrize("failure", ["parent", "open", "fdopen", "write", None])
def test_exclusive_create_releases_directory_handles(root, monkeypatch, failure):
    (root / "parent/nested").mkdir(parents=True)
    real_open = os.open
    real_fdopen = os.fdopen
    opened = []

    def observe_open(path, flags, *args, **kwargs):
        if failure == "parent" and path == "nested":
            raise PermissionError("parent denied")
        if failure == "open" and flags & os.O_CREAT:
            raise PermissionError("open denied")
        fd = real_open(path, flags, *args, **kwargs)
        opened.append(fd)
        return fd

    class FailedWriter:
        def __init__(self, fd):
            self.stream = real_fdopen(fd, "wb")

        def __enter__(self):
            return self

        def write(self, content):
            raise OSError("write failed")

        def __exit__(self, *args):
            self.stream.close()

    def observe_fdopen(fd, *args):
        if failure == "fdopen":
            raise OSError("fdopen failed")
        if failure == "write":
            return FailedWriter(fd)
        return real_fdopen(fd, *args)

    monkeypatch.setattr(os, "open", observe_open)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {observe_open})
    monkeypatch.setattr(os, "fdopen", observe_fdopen)
    if failure:
        with pytest.raises(OSError, match=failure):
            FileHelper(root).create_bytes("parent/nested/new", b"new")
    else:
        FileHelper(root).create_bytes("parent/nested/new", b"new")
        assert (root / "parent/nested/new").read_bytes() == b"new"
    assert opened
    for fd in opened:
        with pytest.raises(OSError) as error:
            os.fstat(fd)
        assert error.value.errno == errno.EBADF


@pytest.mark.parametrize("failure", ["parent", "open", None])
def test_exclusive_create_windows_pins_resolved_hierarchy_portably(
    root, link, monkeypatch, failure
):
    (root / "parent/nested").mkdir(parents=True)
    alias = link(root / "alias", root / "parent")
    files = FileHelper(root, allow_symlinks=True)
    pinned = []
    acquired = []
    real_open = os.open
    expected = [root, root / "parent", root / "parent/nested"]

    @contextmanager
    def pin(path, *, directory):
        assert directory
        if failure == "parent" and path == expected[-1]:
            raise PermissionError("parent denied")
        pinned.append(path)
        acquired.append(path)
        try:
            yield 1
        finally:
            assert pinned.pop() == path

    def open_pinned(path, flags, mode):
        assert pinned == expected
        assert path == root / "parent/nested/new"
        assert flags & os.O_CREAT and flags & os.O_EXCL
        if failure == "open":
            raise PermissionError("open denied")
        return real_open(path, flags, mode)

    windows_os = SimpleNamespace(**{**vars(os), "name": "nt", "open": open_pinned})
    monkeypatch.setattr(file_helper, "os", windows_os)
    monkeypatch.setattr(file_helper, "_windows_handle", pin)
    if failure:
        with pytest.raises(PermissionError, match=failure):
            files.create_bytes(alias / "nested/new", b"new")
        assert not (root / "parent/nested/new").exists()
    else:
        files.create_bytes(alias / "nested/new", b"new")
        assert (root / "parent/nested/new").read_bytes() == b"new"
    assert acquired == (expected[:-1] if failure == "parent" else expected)
    assert pinned == []
    assert alias.is_symlink()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows directory handle semantics")
@pytest.mark.parametrize("ancestor", [".", "parent", "parent/nested"])
@pytest.mark.parametrize("operation", ["create_bytes", "create_text"])
@pytest.mark.parametrize("allow", [False, True])
def test_exclusive_create_windows_blocks_parent_exchange(
    root, monkeypatch, ancestor, operation, allow
):
    (root / "parent/nested").mkdir(parents=True)
    parent = root / ancestor
    retained = parent.with_name(parent.name + "-retained")
    real_open = os.open
    attempted = False

    def try_exchange(path, flags, *args, **kwargs):
        nonlocal attempted
        if flags & os.O_CREAT:
            attempted = True
            with pytest.raises(OSError):
                parent.rename(retained)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", try_exchange)
    content = b"new" if operation == "create_bytes" else "new"
    with FileHelper(root, allow_symlinks=allow) as files:
        getattr(files, operation)("parent/nested/new", content)
    assert attempted
    assert (root / "parent/nested/new").read_bytes() == b"new"
    parent.rename(retained)
    assert retained.is_dir()


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
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {fail})
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
    stat_entry = os.stat
    junction_identity = lstat(junction)

    def as_reparse(result):
        return SimpleNamespace(
            st_mode=result.st_mode,
            st_file_attributes=0x400,
            st_reparse_tag=0xA0000003,
        )

    def directory_reparse(path, **kwargs):
        result = lstat(path, **kwargs)
        if path == junction:
            return as_reparse(result)
        return result

    def directory_reparse_stat(path, *args, **kwargs):
        result = stat_entry(path, *args, **kwargs)
        if kwargs.get("dir_fd") is not None and Path(path).name == junction.name:
            return as_reparse(result)
        return result

    monkeypatch.setattr(Path, "lstat", directory_reparse)
    monkeypatch.setattr(os, "stat", directory_reparse_stat)
    if os.name == "nt":
        native_mode = file_helper._windows_mode

        def reparse_mode(handle):
            if os.path.samestat(file_helper._windows_stat(handle), junction_identity):
                raise OSError(errno.ELOOP, "Unsupported Windows reparse point")
            return native_mode(handle)

        monkeypatch.setattr(file_helper, "_windows_mode", reparse_mode)
    files = FileHelper(root, allow_symlinks=allow)
    for operation in (
        lambda: files.read_bytes(junction / "keep"),
        lambda: files.write_bytes(junction / "keep", b"bad"),
        lambda: files.overwrite_text(junction / "keep", "bad"),
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
