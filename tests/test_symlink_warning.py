"""Encounter warnings must not change existing symlink handling."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
from types import SimpleNamespace
import warnings
import zipfile

import pytest
from typer.testing import CliRunner

from specify_cli import _file_handles, app
from specify_cli._download_security import safe_extract_tar, safe_extract_zip
from specify_cli.file_helper import FileHelper, SymlinkDeniedError
from specify_cli.integrations import opencode
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.symlink_warning import (
    SymlinkDeprecationWarning,
    mode_is_symlink,
    path_is_symlink,
)


def _link(path, target):
    try:
        path.symlink_to(target, target_is_directory=target.is_dir())
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")
    return path


@pytest.mark.parametrize("allow", [False, True])
def test_file_helper_warns_without_changing_read_policy(tmp_path, allow):
    target = tmp_path / "target"
    target.write_text("unchanged", encoding="utf-8")
    link = _link(tmp_path / "link", target)

    with FileHelper(tmp_path, allow_symlinks=allow) as files:
        with pytest.warns(FutureWarning, match="Symlinks are not specifically supported"):
            if allow:
                assert files.read_text(link) == "unchanged"
            else:
                with pytest.raises(SymlinkDeniedError):
                    files.read_text(link)
    assert link.is_symlink()
    assert target.read_text(encoding="utf-8") == "unchanged"


def test_non_file_helper_encounter_warns_without_changing_rejection(tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    _link(root / "linked", target)

    with pytest.warns(FutureWarning, match="Symlinks are not specifically supported"):
        with pytest.raises(ValueError):
            IntegrationManifest("copilot", root).record_file("linked/file", "content")


@pytest.mark.parametrize("symlink", [False, True])
@pytest.mark.parametrize("location", [".rgignore", ".specify", ".specify/.ignore"])
def test_opencode_ignore_layers_warn_without_changing_skip_policy(tmp_path, symlink, location):
    root = tmp_path / "project"
    root.mkdir()
    path = root / location
    path.parent.mkdir(parents=True, exist_ok=True)
    target = tmp_path / "target"
    content = b"*.tmp\n"
    if location == ".specify":
        target.mkdir()
        (target / ".ignore").write_bytes(content)
    else:
        target.write_bytes(content)
    if symlink:
        _link(path, target)
    elif location == ".specify":
        path.mkdir()
        (path / ".ignore").write_bytes(content)
    else:
        path.write_bytes(content)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        layers = opencode._ignore_layers(root, b"")
    extra = ".specify/.ignore" if location == ".specify" else location
    assert [layer[2] for layer in layers] == [root / ".ignore"] + (
        [] if symlink else [root / extra]
    )
    assert bool(caught) is symlink
    assert all(item.category is SymlinkDeprecationWarning for item in caught)
    preserved = target / ".ignore" if location == ".specify" else target
    assert preserved.read_bytes() == content


def test_file_helper_does_not_scan_unrelated_symlinks(tmp_path):
    target = tmp_path / "target"
    target.write_text("ordinary", encoding="utf-8")
    _link(tmp_path / "unrelated", target)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with FileHelper(tmp_path) as files:
            assert files.read_text("target") == "ordinary"
    assert not caught


@pytest.mark.parametrize("kind", ["dangling", "external", "cyclic"])
def test_link_encounters_do_not_resolve_targets(tmp_path, monkeypatch, kind):
    root = tmp_path / "project"
    root.mkdir()
    link = root / "link"
    target = tmp_path / "target"
    if kind == "external":
        target.write_text("outside", encoding="utf-8")
    elif kind == "cyclic":
        target = link
    _link(link, target)

    def forbidden(*args, **kwargs):
        pytest.fail("A warning must not resolve or read a link target")

    monkeypatch.setattr(Path, "resolve", forbidden)
    monkeypatch.setattr(Path, "readlink", forbidden)
    with pytest.warns(SymlinkDeprecationWarning):
        assert path_is_symlink(link)


def test_path_probe_preserves_errors(tmp_path, monkeypatch):
    def denied(self):
        raise PermissionError("cannot inspect path")

    monkeypatch.setattr(Path, "is_symlink", denied)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(PermissionError, match="cannot inspect path"):
            path_is_symlink(tmp_path)
    assert not caught


@pytest.mark.parametrize("kind", ["file", "directory", "missing"])
def test_ordinary_paths_do_not_warn(tmp_path, kind):
    path = tmp_path / kind
    if kind == "file":
        path.write_text("ordinary", encoding="utf-8")
    elif kind == "directory":
        path.mkdir()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert not path_is_symlink(path)
    assert not caught


@pytest.mark.parametrize("allow", [False, True])
def test_recursive_delete_warns_without_changing_policy(tmp_path, allow):
    root = tmp_path / "project"
    tree = root / "tree"
    tree.mkdir(parents=True)
    target = tmp_path / "outside"
    target.write_text("preserved", encoding="utf-8")
    _link(tree / "link", target)
    with FileHelper(root, allow_symlinks=allow) as files:
        with pytest.warns(SymlinkDeprecationWarning):
            if allow:
                files.delete("tree", recursive=True)
            else:
                with pytest.raises(SymlinkDeniedError):
                    files.delete("tree", recursive=True)
    assert tree.exists() is not allow
    assert target.read_text(encoding="utf-8") == "preserved"


@pytest.mark.parametrize("format", ["zip", "tar"])
@pytest.mark.parametrize("symlink", [False, True])
def test_archive_warning_retains_rejection_and_extraction(tmp_path, format, symlink):
    archive = tmp_path / f"package.{format}"
    if format == "zip":
        member = zipfile.ZipInfo("entry")
        member.create_system = 3
        member.external_attr = (stat.S_IFLNK if symlink else stat.S_IFREG) << 16
        with zipfile.ZipFile(archive, "w") as stream:
            stream.writestr(member, b"target")
        extract = safe_extract_zip
    else:
        member = tarfile.TarInfo("entry")
        if symlink:
            member.type = tarfile.SYMTYPE
            member.linkname = "target"
        else:
            member.size = 6
        with tarfile.open(archive, "w:gz") as stream:
            stream.addfile(member, None if symlink else io.BytesIO(b"target"))
        extract = safe_extract_tar
    destination = tmp_path / "extracted"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if symlink:
            with pytest.raises(ValueError, match="Unsafe symlink"):
                extract(archive, destination)
        else:
            extract(archive, destination)
    assert bool(caught) is symlink
    assert all(item.category is SymlinkDeprecationWarning for item in caught)
    if not symlink:
        assert (destination / "entry").read_bytes() == b"target"


@pytest.mark.parametrize("tag", [0xA000000C, 0xA0000003])
def test_native_windows_classification_warns_only_for_symlinks(monkeypatch, tag):
    def attributes(handle, info_class, buffer, size):
        buffer._obj.attributes = 0x400
        buffer._obj.tag = tag
        return True

    monkeypatch.setattr(
        _file_handles, "_windows_api",
        lambda: SimpleNamespace(GetFileInformationByHandleEx=attributes),
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if tag == 0xA000000C:
            assert _file_handles._windows_mode(1) == stat.S_IFLNK
        else:
            with pytest.raises(OSError, match="Unsupported Windows reparse point"):
                _file_handles._windows_mode(1)
    assert bool(caught) is (tag == 0xA000000C)


def test_warning_is_visible_once_on_stderr_with_default_filters(tmp_path):
    target = tmp_path / "target"
    target.write_text("content", encoding="utf-8")
    link = _link(tmp_path / "link", target)
    program = """
import json
import stat
import sys
from pathlib import Path
from specify_cli.symlink_warning import mode_is_symlink, path_is_symlink
for _ in range(3):
    assert path_is_symlink(Path(sys.argv[1]))
    assert mode_is_symlink(stat.S_IFLNK)
print(json.dumps({"ok": True}))
"""
    env = os.environ.copy()
    env.pop("PYTHONWARNINGS", None)
    result = subprocess.run(
        [sys.executable, "-c", program, str(link)],
        capture_output=True, text=True, env=env, check=True,
    )
    assert json.loads(result.stdout) == {"ok": True}
    assert result.stderr.count("SymlinkDeprecationWarning:") == 1
    assert "not specifically supported" in result.stderr
    assert "responsible for the outcome" in result.stderr


def test_mode_encounter_reuses_metadata_without_path_probes(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Mode-based recognition must not probe the filesystem")

    monkeypatch.setattr(Path, "is_symlink", forbidden)
    monkeypatch.setattr(Path, "lstat", forbidden)
    with pytest.warns(SymlinkDeprecationWarning):
        assert mode_is_symlink(stat.S_IFLNK)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert not mode_is_symlink(stat.S_IFREG)
    assert not caught


@pytest.mark.parametrize("symlink", [False, True])
def test_real_cli_status_keeps_json_and_symlink_handling(tmp_path, symlink):
    env = os.environ.copy()
    for key in ("SPECIFY_INIT_DIR", "PYTHONWARNINGS"):
        env.pop(key, None)
    command = [sys.executable, "-c", "from specify_cli import main; main()"]
    initialized = subprocess.run(
        [
            *command, "init", "--here", "--integration", "copilot",
            "--integration-options=--skills", "--script", "sh", "--ignore-agent-tools",
        ],
        cwd=tmp_path, env=env, capture_output=True, text=True, check=True,
    )
    assert "SymlinkDeprecationWarning" not in initialized.stderr
    managed = tmp_path / ".specify" / "templates" / "spec-template.md"
    original = managed.read_bytes()
    if symlink:
        target = tmp_path / "template-target.md"
        target.write_bytes(original)
        managed.unlink()
        _link(managed, target)

    result = subprocess.run(
        [*command, "integration", "status", "--json"],
        cwd=tmp_path, env=env, capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert report["status"] == ("warning" if symlink else "ok")
    assert report["modified_managed_files"] == (1 if symlink else 0)
    assert ("SymlinkDeprecationWarning:" in result.stderr) is symlink
    assert managed.is_symlink() is symlink
    assert managed.read_bytes() == original


@pytest.mark.parametrize(
    "arguments",
    [
        ["artifact", "list", "--json"],
        ["extension", "list", "--json"],
        ["bundle", "list", "--json"],
        ["integration", "status", "--json"],
        ["workflow", "run", "missing.yml", "--json"],
    ],
)
def test_real_cli_symlink_error_stays_one_json_document(tmp_path, arguments):
    project = tmp_path / "project"
    project.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    _link(project / ".specify", target)
    env = os.environ.copy()
    for key in ("SPECIFY_INIT_DIR", "PYTHONWARNINGS"):
        env.pop(key, None)

    result = subprocess.run(
        [sys.executable, "-c", "from specify_cli import main; main()", *arguments],
        cwd=project, env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    error = json.loads(result.stderr)
    assert list(error) == ["error"]
    assert "symlink" in error["error"].lower()
    assert "not specifically supported" in error["error"]
    assert "responsible for the outcome" in error["error"]


def test_json_warning_state_does_not_leak_between_invocations(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    marker = _link(root / ".specify", target)
    runner = CliRunner()
    with monkeypatch.context() as scoped:
        scoped.chdir(root)
        scoped.delenv("SPECIFY_INIT_DIR", raising=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            first = runner.invoke(app, ["artifact", "list", "--json"])
        assert not caught
        assert "responsible for the outcome" in json.loads(first.stderr)["error"]
        marker.unlink()
        marker.mkdir()
        (marker / "init-options.json").write_text("{", encoding="utf-8")
        second = runner.invoke(app, ["artifact", "list", "--json"])
    assert first.exit_code == second.exit_code == 1
    assert "SymlinkDeprecationWarning" not in second.stderr
    assert "init-options.json" in json.loads(second.stderr)["error"]
    with pytest.warns(SymlinkDeprecationWarning):
        assert mode_is_symlink(stat.S_IFLNK)
