"""Unit tests for shared path normalization helpers."""

from tests._path_utils import normalize_path_text


def test_normalize_path_text_preserves_unc_prefix():
    value = r"\\server\share\\folder"
    assert normalize_path_text(value) == "//server/share/folder"


def test_normalize_path_text_collapses_overprefixed_unc_leading_slashes():
    value = r"\\\\server\share\\folder"
    assert normalize_path_text(value) == "//server/share/folder"


def test_normalize_path_text_collapses_redundant_non_unc_slashes():
    value = "foo///bar//baz"
    assert normalize_path_text(value) == "foo/bar/baz"


def test_normalize_path_text_collapses_redundant_posix_leading_slashes():
    value = "///usr//local///bin"
    assert normalize_path_text(value) == "/usr/local/bin"
