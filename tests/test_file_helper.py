"""Operation-level evidence for the scoped FileHelper foundation."""

from dataclasses import FrozenInstanceError
from contextlib import contextmanager
import errno
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from types import SimpleNamespace

import pytest

from specify_cli import file_helper
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


@pytest.mark.skipif(os.name == "nt", reason="POSIX shared directory traversal")
@pytest.mark.parametrize("operation", ["read_bytes", "create_bytes", "overwrite_text"])
def test_posix_operations_share_parent_walk_and_preserve_leaf_flags(root, monkeypatch, operation):
    parent = root / "parent/nested"
    parent.mkdir(parents=True)
    selected = parent / "file"
    if operation != "create_bytes":
        selected.write_bytes(b"inside")
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
    files = FileHelper(root)
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
    assert FileHelper(root, allow_symlinks=allow).read_bytes(selected) == b"inside"
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
    monkeypatch.setattr(file_helper, "os", windows_os)
    monkeypatch.setattr(file_helper, "_windows_handle", pin)
    monkeypatch.setattr(file_helper, "windows_read_fd", duplicate, raising=False)
    files = FileHelper(root)
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

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(
        name="nt", open=os.open, O_RDONLY=os.O_RDONLY,
        O_BINARY=getattr(os, "O_BINARY", 0), close=os.close,
        fstat=os.fstat, fdopen=os.fdopen,
    ))
    monkeypatch.setattr(file_helper, "_windows_handle", pin)
    monkeypatch.setattr(file_helper, "windows_read_fd", duplicate, raising=False)
    assert FileHelper(root, allow_symlinks=allow).read_bytes(selected) == b"inside"
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
    original_open = os.open

    def recording_open(path, flags, *args, **kwargs):
        if str(path) == {"parent": "directory", "leaf": "file"}.get(failure):
            raise PermissionError("injected open failure")
        fd = original_open(path, flags, *args, **kwargs)
        opened.append(fd)
        return fd

    def fail(*args, **kwargs):
        raise OSError("injected read failure")

    class FailedRead:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        read = fail

    with monkeypatch.context() as patch:
        patch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {recording_open})
        patch.setattr(os, "open", recording_open)
        if failure in ("fstat", "fdopen"):
            patch.setattr(os, failure, fail)
        elif failure == "read":
            patch.setattr(os, "fdopen", lambda *args, **kwargs: FailedRead())
        with pytest.raises(OSError, match="injected"):
            FileHelper(root).read_bytes(selected)
    assert opened
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
    def denied(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(FileHelper, "_overwrite_descriptor", denied)
    with pytest.raises(PermissionError, match="denied"):
        FileHelper(root, allow_symlinks=allow).overwrite_text("new", "text")
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
    getattr(FileHelper(root, allow_symlinks=allow), operation)("parent/nested/new", content)
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
