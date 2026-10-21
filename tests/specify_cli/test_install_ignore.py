"""Contract tests for shared installation filtering in specify_cli._install_ignore."""

import re
import shutil
from pathlib import Path

import pathspec
import pytest

from specify_cli._install_ignore import load_install_ignore
from specify_cli.extensions import ValidationError
from specify_cli.presets import PresetValidationError


@pytest.fixture(params=[
    pytest.param((".extensionignore", ValidationError), id="extension"),
    pytest.param((".presetignore", PresetValidationError), id="preset"),
])
def ignore_contract(request):
    return request.param


@pytest.mark.parametrize(
    ("patterns", "excluded", "included"),
    [
        (".git/\n.idea/\ntests/\n", [".git/config", ".idea/x", "tests/a.py"], ["README.md"]),
        ("*.pyc\n", ["cache.pyc", "nested/cache.pyc"], ["nested/code.py"]),
        ("# comment\n\n  notes.txt  \n\n", ["notes.txt"], ["README.md"]),
        ("docs/internal/draft.md\n", ["docs/internal/draft.md"], ["docs/guide.md"]),
        ("docs\\internal\\draft.md\n", ["docs/internal/draft.md"], ["docs/guide.md"]),
        ("ドキュメント/\ncafé/\n", ["ドキュメント/private.md", "café/résumé.txt"], ["docs/guide.md"]),
        ("docs/*.draft.md\n", ["docs/api.draft.md"], ["docs/sub/api.draft.md"]),
        ("docs/**/*.draft.md\n", ["docs/api.draft.md", "docs/sub/api.draft.md"], ["docs/guide.md"]),
        ("docs/*.md\n!docs/api.md\n", ["docs/guide.md"], ["docs/api.md"]),
        ("/notes.txt\n", ["notes.txt"], ["nested/notes.txt"]),
        ("docs/draft.md\n", ["docs/draft.md"], ["nested/docs/draft.md"]),
        ("cache/\n", ["cache/data", "nested/cache/data"], ["other/cache"]),
        ("file?.txt\n", ["file1.txt"], ["file12.txt"]),
        ("../sibling/\n/etc/passwd\n", [], ["sibling/data", "passwd"]),
        # copytree never visits an excluded parent; child negation cannot restore it.
        ("docs/\n!docs/api.md\n", ["docs/api.md"], ["README.md"]),
        ("docs/\n!docs/\n", [], ["docs/api.md"]),
    ],
)
def test_pattern_semantics(tmp_path, ignore_contract, patterns, excluded, included):
    """Both callers use the same pattern contract with copytree traversal."""
    ignore_filename, validation_error = ignore_contract
    source = tmp_path / "source"
    source.mkdir()
    for relative in [*excluded, *included, "keep.txt"]:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"contents of {relative}\n", encoding="utf-8")
    (source / ignore_filename).write_text(patterns, encoding="utf-8")

    dest = tmp_path / "installed"
    shutil.copytree(source, dest, ignore=load_install_ignore(source, ignore_filename, validation_error))

    for relative in excluded:
        assert not (dest / relative).exists()
    for relative in [*included, "keep.txt"]:
        assert (dest / relative).read_bytes() == (source / relative).read_bytes()
    assert not (dest / ignore_filename).exists()


def test_absent_ignore_returns_no_filter(tmp_path, ignore_contract):
    ignore_filename, validation_error = ignore_contract
    (tmp_path / ".gitignore").write_text("*\n", encoding="utf-8")

    assert load_install_ignore(tmp_path, ignore_filename, validation_error) is None


@pytest.mark.parametrize("directory", ["tests", "café"])
def test_utf8_bom_first_pattern(tmp_path, ignore_contract, directory):
    """Accept the UTF-8 BOM and CRLF bytes emitted by Windows PowerShell 5.1."""
    ignore_filename, validation_error = ignore_contract
    source = tmp_path / "source"
    (source / directory).mkdir(parents=True)
    (source / directory / "private.txt").write_text("development only", encoding="utf-8")
    (source / "keep.txt").write_text("shipped", encoding="utf-8")
    (source / ignore_filename).write_bytes(b"\xef\xbb\xbf" + f"{directory}/\r\n".encode("utf-8"))

    dest = tmp_path / "installed"
    shutil.copytree(source, dest, ignore=load_install_ignore(source, ignore_filename, validation_error))

    assert not (dest / directory).exists()
    assert (dest / "keep.txt").read_text(encoding="utf-8") == "shipped"
    assert not (dest / ignore_filename).exists()


@pytest.mark.parametrize("negate_self", [False, True])
def test_ignore_file_is_always_excluded(tmp_path, ignore_contract, negate_self):
    ignore_filename, validation_error = ignore_contract
    source = tmp_path / "source"
    source.mkdir()
    (source / ignore_filename).write_text(
        f"!{ignore_filename}\n" if negate_self else "", encoding="utf-8"
    )
    (source / "keep.txt").write_text("keep\n", encoding="utf-8")

    dest = tmp_path / "installed"
    shutil.copytree(source, dest, ignore=load_install_ignore(source, ignore_filename, validation_error))

    assert sorted(path.name for path in dest.iterdir()) == ["keep.txt"]


@pytest.mark.parametrize(
    ("content", "offset"),
    [
        pytest.param(b"caf\xe9/\n", 3, id="without-bom"),
        pytest.param(b"\xef\xbb\xbfcaf\xe9/\n", 6, id="with-bom"),
    ],
)
def test_invalid_utf8_uses_callers_validation_error(tmp_path, ignore_contract, content, offset):
    ignore_filename, validation_error = ignore_contract
    ignore_file = tmp_path / ignore_filename
    ignore_file.write_bytes(content)

    with pytest.raises(validation_error) as caught:
        load_install_ignore(tmp_path, ignore_filename, validation_error)

    assert f"{ignore_filename} is not valid UTF-8: {ignore_file}" in str(caught.value)
    assert f"at byte {offset})" in str(caught.value)


@pytest.mark.parametrize(
    ("patterns", "line_number", "normalized_pattern"),
    [
        ("!\n", 1, "!"),
        ("# comment\n\ntests/\n  !  \n", 4, "!"),
        ("[z-a].txt\n", 1, "[z-a].txt"),
        ("# comment\n\ntests/\n  docs\\[z-a].txt  \n!\n", 4, "docs/[z-a].txt"),
    ],
)
def test_malformed_pattern_uses_callers_validation_error(
    tmp_path, ignore_contract, patterns, line_number, normalized_pattern, monkeypatch
):
    ignore_filename, validation_error = ignore_contract
    ignore_file = tmp_path / ignore_filename
    ignore_file.write_text(patterns, encoding="utf-8")
    original_from_lines = pathspec.GitIgnoreSpec.from_lines
    failures = []

    def record_failures(lines):
        try:
            return original_from_lines(lines)
        except (ValueError, re.error) as error:
            failures.append(error)
            raise

    monkeypatch.setattr(pathspec.GitIgnoreSpec, "from_lines", record_failures)

    with pytest.raises(validation_error) as caught:
        load_install_ignore(tmp_path, ignore_filename, validation_error)

    assert f"Invalid patterns in {ignore_filename}: {ignore_file}" in str(caught.value)
    assert f"at line {line_number}: {normalized_pattern!r}" in str(caught.value)
    assert caught.value.__cause__ is failures[0]
    assert isinstance(caught.value.__cause__, (ValueError, re.error))
    assert str(caught.value.__cause__) in str(caught.value)


def test_valid_patterns_compile_once(tmp_path, ignore_contract, monkeypatch):
    ignore_filename, validation_error = ignore_contract
    (tmp_path / ignore_filename).write_text("# comment\n\ndocs/*\n!docs/api.md\n", encoding="utf-8")
    original_from_lines = pathspec.GitIgnoreSpec.from_lines
    calls = []

    def record_compilation(lines):
        calls.append(list(lines))
        return original_from_lines(calls[-1])

    monkeypatch.setattr(pathspec.GitIgnoreSpec, "from_lines", record_compilation)

    ignore = load_install_ignore(tmp_path, ignore_filename, validation_error)

    assert len(calls) == 1
    assert ignore(str(tmp_path / "docs"), ["api.md", "draft.md"]) == {"draft.md"}


def test_read_failure_is_propagated(tmp_path, ignore_contract, monkeypatch):
    ignore_filename, validation_error = ignore_contract
    ignore_file = tmp_path / ignore_filename
    ignore_file.write_text("tests/\n", encoding="utf-8")
    original_read = Path.read_text

    def fail_read(path, *args, **kwargs):
        if path == ignore_file:
            raise PermissionError("ignore file is unreadable")
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_read)
    with pytest.raises(PermissionError, match="ignore file is unreadable"):
        load_install_ignore(tmp_path, ignore_filename, validation_error)
