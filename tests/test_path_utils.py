"""Unit tests for shared path normalization helpers."""

import os
from pathlib import Path

import pytest

from tests._path_utils import (
    assert_normalized_path_equal,
    bash_path_from_host,
    normalize_path_text,
    path_from_bash_output,
)


def test_normalize_path_text_preserves_unc_prefix():
    value = r"\\server\share\\folder"
    assert normalize_path_text(value) == "//server/share/folder"


def test_normalize_path_text_preserves_slash_normalized_unc_prefix():
    value = "//server/share//folder"
    assert normalize_path_text(value) == "//server/share/folder"


def test_normalize_path_text_collapses_overprefixed_unc_leading_slashes():
    value = r"\\\\server\share\\folder"
    assert normalize_path_text(value) == "//server/share/folder"


def test_normalize_path_text_preserves_overprefixed_slash_unc_like_path():
    value = "////server//share///folder"
    assert normalize_path_text(value) == "//server/share/folder"


def test_normalize_path_text_collapses_redundant_non_unc_slashes():
    value = "foo///bar//baz"
    assert normalize_path_text(value) == "foo/bar/baz"


def test_normalize_path_text_collapses_redundant_posix_leading_slashes():
    value = "///usr//local///bin"
    assert normalize_path_text(value) == "/usr/local/bin"


def test_path_from_bash_output_trims_quotes_whitespace_and_crlf():
    raw = "  '/tmp/my-feature/path'\r\n"
    parsed = path_from_bash_output(raw)
    expected_suffix = os.path.join("my-feature", "path")
    assert str(parsed).endswith(expected_suffix)


def test_path_from_bash_output_tmp_mapping_ignores_existence(monkeypatch):
    monkeypatch.setenv("SPECKIT_BASH_TMPDIR", "/virtual-tmp")
    parsed = path_from_bash_output("/tmp/a/b")
    assert str(parsed).endswith(os.path.join("virtual-tmp", "a", "b"))


def test_bash_path_from_host_converts_windows_drive_paths():
    converted = bash_path_from_host(Path("C:/tmp/spec-kit"))
    if os.name == "nt":
        assert converted == "/c/tmp/spec-kit"
    else:
        assert converted == "C:/tmp/spec-kit"


def test_assert_normalized_path_equal_rejects_mismatched_drives():
    with pytest.raises(AssertionError):
        assert_normalized_path_equal("C:/tmp/spec-kit", "D:/tmp/spec-kit")


def test_assert_normalized_path_equal_rejects_unc_vs_non_unc_equivalence():
    if os.name == "nt":
        with pytest.raises(AssertionError):
            assert_normalized_path_equal("//server/share/path", "/server/share/path")
    else:
        assert_normalized_path_equal("//server/share/path", "/server/share/path")
