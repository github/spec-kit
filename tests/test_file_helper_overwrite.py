"""Handle-based non-atomic text overwrite behavior."""

import csv
import errno
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli import _file_handles, file_helper
from specify_cli.file_helper import FileHelper, UnsupportedPathError


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("existing", [False, True])
def test_parent_swap_after_validation_does_not_redirect_overwrite(
    tmp_path, monkeypatch, allow, existing
):
    root = tmp_path / "project"
    parent = root / "parent"
    parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    if existing:
        (parent / "file").write_text("inside")
        (outside / "file").write_text("outside")
    try:
        probe = root / "probe"
        probe.symlink_to(outside, target_is_directory=True)
        probe.unlink()
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    original = FileHelper._path
    swapped = False

    def swap(self, path, **kwargs):
        nonlocal swapped
        destination = original(self, path, **kwargs)
        if not swapped:
            swapped = True
            parent.rename(root / "original")
            parent.symlink_to(outside, target_is_directory=True)
        return destination

    monkeypatch.setattr(FileHelper, "_path", swap)
    with pytest.raises(OSError):
        FileHelper(root, allow_symlinks=allow).overwrite_text("parent/file", "new")
    assert swapped
    if existing:
        assert (outside / "file").read_text() == "outside"
        assert (root / "original/file").read_text() == "inside"
    else:
        assert not (outside / "file").exists()
        assert not (root / "original/file").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor-relative open required")
@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory"])
def test_leaf_replacement_at_open_is_checked_before_truncation(tmp_path, monkeypatch, kind):
    root = tmp_path / "project"
    root.mkdir()
    leaf = root / "file"
    leaf.write_text("original")
    outside = tmp_path / "outside"
    outside.write_text("outside")
    original = os.open
    reader = None

    def swap(path, flags, *args, **kwargs):
        nonlocal reader
        if Path(path).name == "file":
            leaf.rename(root / "original")
            if kind == "symlink":
                leaf.symlink_to(outside)
            elif kind == "fifo":
                os.mkfifo(leaf)
                reader = original(leaf, os.O_RDWR | os.O_NONBLOCK)
            else:
                leaf.mkdir()
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap)
    try:
        with pytest.raises((OSError, UnsupportedPathError)):
            FileHelper(root).overwrite_text("file", "new")
        if reader is not None:
            with pytest.raises(BlockingIOError):
                os.read(reader, 100)
    finally:
        if reader is not None:
            os.close(reader)
    assert outside.read_text() == "outside"
    assert (root / "original").read_text() == "original"


@pytest.mark.skipif(os.name == "nt", reason="POSIX FIFO open semantics required")
@pytest.mark.parametrize("allow", [False, True])
def test_fifo_without_reader_at_leaf_open_does_not_block(tmp_path, allow):
    result = subprocess.run(
        [
            sys.executable, "-c",
            """
import errno
import os
import stat
import sys
from pathlib import Path
from specify_cli.file_helper import FileHelper

root = Path(sys.argv[1])
leaf = root / "file"
leaf.write_text("original")
files = FileHelper(root, allow_symlinks=sys.argv[2] == "True")
original = os.open
swapped = False

def swap(path, flags, *args, **kwargs):
    global swapped
    if Path(path).name == "file":
        leaf.rename(root / "original")
        os.mkfifo(leaf)
        swapped = True
    return original(path, flags, *args, **kwargs)

os.open = swap
try:
    files.overwrite_text("file", "new")
except OSError as exc:
    assert exc.errno == errno.ENXIO, repr(exc)
else:
    raise AssertionError("Overwrite accepted a FIFO without a reader")
assert swapped
assert stat.S_ISFIFO(leaf.lstat().st_mode)
assert (root / "original").read_text() == "original"
""",
            str(tmp_path), str(allow),
        ],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("encoding", ["utf-8", "utf-16", "cp1252"])
def test_overwrite_matches_native_text_and_preserves_hardlinks(tmp_path, allow, encoding):
    root = tmp_path / "project"
    root.mkdir()
    reference = root / "reference"
    content = "caf\u00e9\nsecond\r\n"
    reference.write_text(content, encoding=encoding)
    files = FileHelper(root, allow_symlinks=allow)
    files.overwrite_text("file", "a longer old value")
    path = root / "file"
    alias = root / "hardlink"
    os.link(path, alias)
    before = path.stat()
    files.overwrite_text("file", content, encoding=encoding)
    assert path.read_bytes() == reference.read_bytes() == alias.read_bytes()
    assert path.stat().st_ino == alias.stat().st_ino == before.st_ino
    assert path.stat().st_mode == before.st_mode == reference.stat().st_mode
    files.overwrite_text("file", "")
    assert path.read_bytes() == alias.read_bytes() == b""


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions required")
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("restricted", ["root", "parent"])
@pytest.mark.parametrize(
    "legacy_macos",
    [False, pytest.param(True, marks=pytest.mark.skipif(sys.platform != "darwin", reason="Darwin flags"))],
)
def test_searchable_unreadable_directory_retains_native_overwrite_behavior(
    tmp_path, monkeypatch, existing, allow, restricted, legacy_macos
):
    if legacy_macos:
        monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{
            key: value for key, value in vars(os).items() if key not in ("O_SEARCH", "O_PATH", "O_EXEC")
        }))
    root = tmp_path / "project"
    parent = root / "parent"
    parent.mkdir(parents=True)
    native = parent / "native"
    leaf = parent / "file"
    if existing:
        native.write_text("longer old content")
        leaf.write_text("longer old content")
    directory = root if restricted == "root" else parent
    directory.chmod(0o300)
    try:
        try:
            os.listdir(directory)
        except PermissionError:
            pass
        else:
            pytest.skip("This process can read directories without read permission")
        native.write_text("new\n")
        FileHelper(root, allow_symlinks=allow).overwrite_text("parent/file", "new\n")
        assert leaf.read_bytes() == native.read_bytes()
        assert leaf.stat().st_mode == native.stat().st_mode
    finally:
        directory.chmod(0o700)


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory permissions required")
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_unsearchable_parent_still_rejects_overwrite(tmp_path, existing, allow):
    parent = tmp_path / "parent"
    parent.mkdir()
    leaf = parent / "file"
    native = parent / "native"
    if existing:
        leaf.write_text("old")
        native.write_text("old")
    parent.chmod(0o600)
    try:
        try:
            native.write_text("new")
        except PermissionError:
            pass
        else:
            pytest.skip("This process can traverse directories without search permission")
        with pytest.raises(PermissionError):
            FileHelper(tmp_path, allow_symlinks=allow).overwrite_text("parent/file", "new")
    finally:
        parent.chmod(0o700)
    if existing:
        assert leaf.read_text() == "old"
    else:
        assert not leaf.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows CRT mask semantics required")
@pytest.mark.parametrize("mask", [0, 0o200])
@pytest.mark.parametrize("allow", [False, True])
def test_native_windows_overwrite_creation_matches_masked_native_creation(tmp_path, mask, allow):
    native = tmp_path / "native"
    leaf = tmp_path / "file"
    existing = tmp_path / "existing"
    existing.write_text("longer old content")
    before = existing.stat()
    previous_mask = os.umask(mask)
    try:
        native.write_text("caf\u00e9\n", encoding="utf-8")
        files = FileHelper(tmp_path, allow_symlinks=allow)
        files.overwrite_text("file", "caf\u00e9\n")
        files.overwrite_text("existing", "new")
        assert leaf.read_bytes() == native.read_bytes()
        assert leaf.stat().st_mode == native.stat().st_mode
        assert existing.stat().st_mode == before.st_mode
        assert existing.stat().st_ino == before.st_ino
        assert existing.read_text() == "new"
        assert os.umask(mask) == mask
        for path in (native, leaf):
            if mask & 0o200:
                with pytest.raises(PermissionError):
                    path.write_text("again")
            else:
                path.write_text("again")
        assert {path.name for path in tmp_path.iterdir()} == {"native", "file", "existing"}
    finally:
        os.umask(previous_mask)
        for path in (native, leaf):
            if path.exists():
                path.chmod(0o600)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows directory ACL semantics required")
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_native_windows_overwrite_does_not_require_project_delete_rights(
    tmp_path, existing, allow
):
    root = tmp_path / "project"
    parent = root / "parent"
    parent.mkdir(parents=True)
    leaf = parent / "file"
    if existing:
        leaf.write_text("longer old content")
    identity = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        capture_output=True, text=True, check=True,
    )
    rows = [row for row in csv.reader(identity.stdout.splitlines()) if row]
    sid = rows[0][1].strip()
    assert sid.startswith("S-")

    def icacls(*args):
        result = subprocess.run(
            ["icacls", str(parent), *args], capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    try:
        icacls("/deny", f"*{sid}:(OI)(CI)(DE,DC)")
        native = parent / "native"
        native.write_text("native")
        assert native.read_text() == "native"
        with pytest.raises(PermissionError):
            native.unlink()
        FileHelper(root, allow_symlinks=allow).overwrite_text("parent/file", "new")
        assert leaf.read_text() == "new"
        with pytest.raises(PermissionError):
            leaf.unlink()
        assert {path.name for path in parent.iterdir()} == {"native", "file"}
    finally:
        icacls("/remove:d", f"*{sid}", "/T", "/C")


@pytest.mark.parametrize("allow", [False, True])
def test_overwrite_trusted_root_alias_and_contained_link_chains(tmp_path, allow):
    root = tmp_path / "project"
    directory = root / "directory"
    directory.mkdir(parents=True)
    trusted = tmp_path / "trusted"
    try:
        trusted.symlink_to(root, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    files = FileHelper(trusted, allow_symlinks=allow)
    files.overwrite_text(trusted / "directory/file", "old")
    if allow:
        (root / "parent").symlink_to("directory", target_is_directory=True)
        (root / "parent-chain").symlink_to("parent", target_is_directory=True)
        (directory / "alias").symlink_to("file")
        (directory / "chain").symlink_to("alias")
        files.overwrite_text(trusted / "parent-chain/chain", "new")
        assert (directory / "file").read_text() == "new"
        assert all(
            path.is_symlink()
            for path in (root / "parent", root / "parent-chain", directory / "alias", directory / "chain")
        )
    else:
        assert (directory / "file").read_text() == "old"
    assert trusted.is_symlink()


@pytest.mark.parametrize("allow", [False, True])
def test_missing_parent_and_invalid_codec_do_not_create_or_truncate(tmp_path, allow):
    files = FileHelper(tmp_path, allow_symlinks=allow)
    with pytest.raises(FileNotFoundError):
        files.overwrite_text("missing/file", "new")
    assert not (tmp_path / "missing").exists()
    path = tmp_path / "file"
    path.write_text("old")
    with pytest.raises(LookupError):
        files.overwrite_text("file", "new", encoding="not-a-codec")
    assert path.read_text() == "old"


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor capability required")
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize(
    ("capability", "value"),
    [
        ("dir_fd", False),
        ("O_NOFOLLOW", 0), ("O_NOFOLLOW", None),
        ("O_DIRECTORY", 0), ("O_DIRECTORY", None),
        ("O_NONBLOCK", 0), ("O_NONBLOCK", None),
    ],
)
def test_unsupported_descriptor_backend_fails_without_path_fallback(
    tmp_path, monkeypatch, existing, capability, value
):
    path = tmp_path / "file"
    if existing:
        path.write_text("old")

    def unexpected_open(*args, **kwargs):
        raise AssertionError("An unsupported backend must not open a destination")

    attributes = {**vars(os), "open": unexpected_open}
    if capability == "dir_fd":
        attributes["supports_dir_fd"] = set()
    elif value is None:
        attributes.pop(capability, None)
    else:
        attributes[capability] = value
    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**attributes))
    with pytest.raises(OSError, match="unsupported") as caught:
        FileHelper(tmp_path).overwrite_text("file", "new")
    assert caught.value.errno == errno.ENOTSUP
    if existing:
        assert path.read_text() == "old"
    else:
        assert not path.exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX upsert open semantics required")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("writable", [False, True])
def test_regular_file_created_at_leaf_open_retains_native_upsert_behavior(
    tmp_path, monkeypatch, allow, writable
):
    if not writable and os.geteuid() == 0:
        pytest.skip("Root bypasses file write permissions")
    leaf = tmp_path / "file"
    alias = tmp_path / "hardlink"
    original = os.open
    created = []
    mode = 0o600 if writable else 0o400

    def create_before_open(path, flags, *args, **kwargs):
        if Path(path).name == "file":
            assert not leaf.exists()
            assert flags & os.O_CREAT and not flags & os.O_TRUNC
            leaf.write_text("created immediately before open")
            leaf.chmod(mode)
            os.link(leaf, alias)
            created.append(leaf.stat().st_ino)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(
        file_helper, "os", SimpleNamespace(**{**vars(os), "open": create_before_open})
    )
    files = FileHelper(tmp_path, allow_symlinks=allow)
    if writable:
        files.overwrite_text("file", "new")
    else:
        with pytest.raises(PermissionError):
            files.overwrite_text("file", "new")
    assert len(created) == 1
    assert leaf.stat().st_ino == alias.stat().st_ino == created[0]
    assert leaf.stat().st_mode & 0o777 == mode
    expected = "new" if writable else "created immediately before open"
    assert leaf.read_text() == alias.read_text() == expected


@pytest.mark.skipif(os.name != "nt", reason="Native Windows overwrite backend required")
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_native_windows_creation_probe_is_only_required_for_missing_leaf(
    tmp_path, monkeypatch, existing, allow
):
    leaf = tmp_path / "file"
    if existing:
        leaf.write_text("longer old content")
        before = leaf.stat()
    probes = []

    def unavailable_probe():
        probes.append(True)
        raise PermissionError("Runtime permissions probe unavailable")

    monkeypatch.setattr(_file_handles, "_windows_creation_attributes", unavailable_probe)
    files = FileHelper(tmp_path, allow_symlinks=allow)
    if existing:
        files.overwrite_text("file", "new")
        assert leaf.read_text() == "new"
        assert leaf.stat().st_ino == before.st_ino
        assert leaf.stat().st_mode == before.st_mode
        assert probes == []
    else:
        with pytest.raises(PermissionError, match="Runtime permissions probe unavailable"):
            files.overwrite_text("file", "new")
        assert not leaf.exists()
        assert probes == [True]
    assert {path.name for path in tmp_path.iterdir()} == ({"file"} if existing else set())


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor cleanup required")
@pytest.mark.parametrize("failure", ["open", "fstat", "ftruncate", "fdopen", "write"])
def test_overwrite_closes_descriptors_on_failure(tmp_path, monkeypatch, failure):
    parent = tmp_path / "parent"
    parent.mkdir()
    (parent / "file").write_text("old")
    opened = []
    original = os.open
    fstat = os.fstat

    def observe(path, flags, *args, **kwargs):
        if failure == "open" and Path(path).name == "file":
            raise PermissionError("test failure")
        fd = original(path, flags, *args, **kwargs)
        opened.append(fd)
        return fd

    def fail(*args, **kwargs):
        raise OSError("test failure")

    class FailedStream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        write = fail

    replacements = {"open": observe}
    if failure == "write":
        replacements["fdopen"] = lambda *args, **kwargs: FailedStream()
    elif failure != "open":
        replacements[failure] = fail
    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), **replacements}))
    with pytest.raises(OSError, match="test failure"):
        FileHelper(tmp_path).overwrite_text("parent/file", "new")
    assert opened
    for fd in opened:
        with pytest.raises(OSError):
            fstat(fd)


@pytest.mark.parametrize("failed_parent", [None, "parent"])
def test_windows_overwrite_pins_resolved_hierarchy_until_stream_closes(
    tmp_path, monkeypatch, failed_parent
):
    parent = tmp_path / "parent"
    parent.mkdir()
    leaf = parent / "file"
    leaf.write_text("old")
    events = []
    active = []

    @contextmanager
    def pin(path, *, directory):
        assert directory
        events.append(("pin", path))
        if path.name == failed_parent:
            raise PermissionError("pin failed")
        active.append(path)
        try:
            yield 1
        finally:
            assert active.pop() == path
            events.append(("unpin", path))

    @contextmanager
    def open_leaf(path):
        assert active == [tmp_path, parent]
        assert leaf.read_text() == "old"
        fd = os.open(path, os.O_WRONLY)
        try:
            yield fd
            assert leaf.read_text() == "new"
            assert active == [tmp_path, parent]
        finally:
            os.close(fd)
            events.append(("close", path))

    monkeypatch.setattr(file_helper, "os", SimpleNamespace(**{**vars(os), "name": "nt"}))
    monkeypatch.setattr(file_helper, "_windows_handle", pin)
    monkeypatch.setattr(file_helper, "_windows_overwrite_fd", open_leaf)
    if failed_parent:
        with pytest.raises(PermissionError, match="pin failed"):
            FileHelper(tmp_path).overwrite_text("parent/file", "new")
        assert leaf.read_text() == "old"
    else:
        FileHelper(tmp_path).overwrite_text("parent/file", "new")
        assert events[-3:] == [("close", leaf), ("unpin", parent), ("unpin", tmp_path)]
    assert not active


@pytest.mark.skipif(os.name != "nt", reason="Native Windows sharing semantics required")
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_native_windows_overwrite_holds_every_parent_and_leaf(tmp_path, monkeypatch, existing, allow):
    root = tmp_path / "project"
    parent = root / "parent"
    parent.mkdir(parents=True)
    leaf = parent / "file"
    if existing:
        leaf.write_text("old")
    original = os.ftruncate
    open_leaf = file_helper._windows_overwrite_fd
    attempted = []
    parents_checked = []

    @contextmanager
    def open_while_pinned(path):
        for directory in (root, parent):
            with pytest.raises(PermissionError):
                directory.rename(directory.with_name(directory.name + "-moved"))
            parents_checked.append(directory)
        with open_leaf(path) as fd:
            yield fd

    def truncate(fd, length):
        for path in (root, parent, leaf):
            with pytest.raises(PermissionError):
                path.rename(path.with_name(path.name + "-moved"))
            attempted.append(path)
        return original(fd, length)

    monkeypatch.setattr(os, "ftruncate", truncate)
    monkeypatch.setattr(file_helper, "_windows_overwrite_fd", open_while_pinned)
    FileHelper(root, allow_symlinks=allow).overwrite_text("parent/file", "new")
    assert parents_checked == [root, parent]
    assert attempted == [root, parent, leaf]
    assert leaf.read_text() == "new"
    leaf.rename(parent / "finished")
    parent.rename(root / "finished")
    root.rename(tmp_path / "finished")


@pytest.mark.skipif(os.name != "nt", reason="Native Windows reparse semantics required")
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_native_windows_leaf_swap_at_open_never_follows_new_link(
    tmp_path, monkeypatch, existing, allow
):
    root = tmp_path / "project"
    root.mkdir()
    leaf = root / "file"
    outside = tmp_path / "outside"
    outside.write_text("outside")
    try:
        probe = root / "probe"
        probe.symlink_to(outside)
        probe.unlink()
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    if existing:
        leaf.write_text("old")
    original = file_helper._windows_overwrite_fd

    @contextmanager
    def swap(path):
        if existing:
            leaf.rename(root / "original")
        leaf.symlink_to(outside)
        with original(path) as fd:
            yield fd

    monkeypatch.setattr(file_helper, "_windows_overwrite_fd", swap)
    with pytest.raises(OSError):
        FileHelper(root, allow_symlinks=allow).overwrite_text("file", "new")
    assert leaf.is_symlink()
    assert outside.read_text() == "outside"
    if existing:
        assert (root / "original").read_text() == "old"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows CRT exclusive-create semantics required")
@pytest.mark.parametrize("kind", ["file", "existing-target-link", "missing-target-link"])
@pytest.mark.parametrize("allow", [False, True])
def test_native_windows_leaf_introduced_during_mode_probe_is_not_followed(
    tmp_path, monkeypatch, kind, allow
):
    root = tmp_path / "project"
    root.mkdir()
    leaf = root / "file"
    outside = tmp_path / "outside"
    if kind != "missing-target-link":
        outside.write_text("outside")
    if kind != "file":
        try:
            probe = root / "probe"
            probe.symlink_to(outside)
            probe.unlink()
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"Symlink creation unavailable: {exc}")
    original = os.open
    attempted = []

    def insert(path, flags, mode):
        assert flags & os.O_EXCL and not flags & os.O_TRUNC
        fd = original(path, flags, mode)
        attempted.append(leaf)
        if kind == "file":
            leaf.write_text("introduced")
        else:
            leaf.symlink_to(outside)
        return fd

    monkeypatch.setattr(_file_handles, "os", SimpleNamespace(**{**vars(os), "open": insert}))
    with pytest.raises(OSError):
        FileHelper(root, allow_symlinks=allow).overwrite_text("file", "new")
    assert attempted == [leaf]
    if kind == "missing-target-link":
        assert not outside.exists()
    else:
        assert outside.read_text() == "outside"
    if kind == "file":
        assert leaf.read_text() == "introduced"
    else:
        assert leaf.is_symlink()


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor-relative open required")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("existing", [False, True])
def test_parent_swap_at_leaf_open_uses_anchored_directory(
    tmp_path, monkeypatch, allow, existing
):
    root = tmp_path / "project"
    parent = root / "parent"
    parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    if existing:
        (parent / "file").write_text("inside")
        (outside / "file").write_text("outside")
    original = os.open
    swapped = False

    def swap(path, flags, *args, **kwargs):
        nonlocal swapped
        if Path(path).name == "file":
            swapped = True
            parent.rename(root / "original")
            parent.symlink_to(outside, target_is_directory=True)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap)
    FileHelper(root, allow_symlinks=allow).overwrite_text("parent/file", "new")
    assert swapped
    assert (root / "original/file").read_text() == "new"
    if existing:
        assert (outside / "file").read_text() == "outside"
    else:
        assert not (outside / "file").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX opened-file rename semantics required")
@pytest.mark.parametrize("allow", [False, True])
def test_leaf_swap_after_open_keeps_truncation_and_write_on_opened_file(
    tmp_path, monkeypatch, allow
):
    root = tmp_path / "project"
    root.mkdir()
    leaf = root / "file"
    leaf.write_text("a longer old value")
    inode = leaf.stat().st_ino
    outside = tmp_path / "outside"
    outside.write_text("outside")
    original = os.ftruncate
    swapped = False

    def swap(fd, length):
        nonlocal swapped
        swapped = True
        leaf.rename(root / "original")
        leaf.symlink_to(outside)
        return original(fd, length)

    monkeypatch.setattr(os, "ftruncate", swap)
    FileHelper(root, allow_symlinks=allow).overwrite_text("file", "new")
    assert swapped
    assert outside.read_text() == "outside"
    assert leaf.is_symlink()
    assert (root / "original").read_text() == "new"
    assert (root / "original").stat().st_ino == inode


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor limits required")
@pytest.mark.parametrize("depth", [1, 80])
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_overwrite_descriptor_usage_is_independent_of_path_depth(tmp_path, depth, existing, allow):
    parent = tmp_path
    for _ in range(depth):
        parent = parent / "d"
        parent.mkdir()
    if existing:
        (parent / "file").write_text("longer old content")
    result = subprocess.run(
        [
            sys.executable, "-c",
            """
import resource
import sys
from pathlib import Path
from specify_cli.file_helper import FileHelper

root = Path(sys.argv[1])
parent = root.joinpath(*(["d"] * int(sys.argv[2])))
files = FileHelper(root, allow_symlinks=sys.argv[3] == "True")
_, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (64, hard))
(parent / "native").write_text("native")
files.overwrite_text(parent / "file", "new")
assert (parent / "file").read_text() == "new"
""",
            str(tmp_path), str(depth), str(allow),
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
