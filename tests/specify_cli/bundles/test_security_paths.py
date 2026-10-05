"""Security tests: path-traversal / symlink confinement (Constitution Principle V).

These assert the bundler refuses to read or write outside an allowed root, so a
malicious manifest or artifact path cannot escape the project/bundle directory.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundles.yamlio import ensure_within, is_safe_relpath


def test_ensure_within_allows_child(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    child = root / "sub" / "file.txt"
    assert ensure_within(root, child) == child.resolve()


def test_ensure_within_rejects_parent_traversal(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    escape = root / ".." / "secret.txt"
    with pytest.raises(BundlerError, match="escapes"):
        ensure_within(root, escape)


def test_ensure_within_rejects_absolute_outside(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    with pytest.raises(BundlerError):
        ensure_within(root, Path("/etc/passwd"))


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_ensure_within_rejects_symlink_escape(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "link.txt"
    link.symlink_to(outside)
    with pytest.raises(BundlerError, match="escapes"):
        ensure_within(root, link)


@pytest.mark.parametrize("rel,safe", [
    ("a/b.txt", True),
    ("./a.txt", True),
    ("../escape", False),
    ("a/../../escape", False),
    ("/abs", False),
    ("C:/abs", False),
    ("C:\\abs", False),
    ("\\\\server\\share", False),
    ("", False),
])
def test_is_safe_relpath(rel, safe):
    assert is_safe_relpath(rel) is safe


def test_build_skips_symlinks(tmp_path: Path):
    """Packager must not follow symlinks out of the bundle dir."""
    import yaml

    from specify_cli.bundles.packager import build_bundle
    from tests.specify_cli.bundles.helpers import valid_manifest_dict

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (bundle / "README.md").write_text("# Demo", encoding="utf-8")

    if os.name != "nt":
        secret = tmp_path / "secret.txt"
        secret.write_text("top secret", encoding="utf-8")
        (bundle / "leak.txt").symlink_to(secret)

    result = build_bundle(bundle, output_dir=tmp_path / "out")
    import zipfile

    with zipfile.ZipFile(result.artifact_path) as archive:
        names = archive.namelist()
    assert "leak.txt" not in names
    assert "bundle.yml" in names


def test_load_records_refuses_symlinked_specify_escape(tmp_path: Path):
    # Reading bundle-records.json must honour the same confinement as writes:
    # a symlinked .specify pointing outside project_root is refused.
    from specify_cli.bundles.records import load_records

    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bundle-records.json").write_text(
        '{"schema_version": "1.0", "bundles": []}', encoding="utf-8"
    )
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    with pytest.raises(BundlerError, match="escapes the allowed root"):
        load_records(project)


def test_active_integration_refuses_symlinked_specify_escape(tmp_path: Path):
    # Reading the integration marker must not follow a .specify symlink that
    # resolves outside project_root; an escape is treated as "not determinable".
    from specify_cli.bundles.project import active_integration

    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "integration.json").write_text(
        '{"integration": "leaked"}', encoding="utf-8"
    )
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    assert active_integration(project) is None


def _write_marker(tmp_path: Path, payload: str) -> Path:
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    (project / ".specify" / "integration.json").write_text(
        payload, encoding="utf-8"
    )
    return project


def test_active_integration_reads_default_integration(tmp_path: Path):
    """A marker carrying only ``default_integration`` must resolve.

    ``write_integration_json`` writes both ``integration`` and
    ``default_integration``, so a marker produced by the current CLI already
    resolved through the alias. This covers the authoritative field on its own —
    hand-edited, or written by anything that follows the shape of the canonical
    reader (``integration_state`` line 199:
    ``state.get("default_integration") or state.get("integration")``).
    """
    from specify_cli.bundles.project import active_integration

    project = _write_marker(tmp_path, '{"default_integration": "copilot"}')
    assert active_integration(project) == "copilot"


def test_active_integration_prefers_default_over_legacy_alias(tmp_path: Path):
    """When both are present the authoritative field wins, matching
    ``integration_state``'s own ordering."""
    from specify_cli.bundles.project import active_integration

    project = _write_marker(
        tmp_path, '{"integration": "stale", "default_integration": "copilot"}'
    )
    assert active_integration(project) == "copilot"


def test_active_integration_still_reads_legacy_alias(tmp_path: Path):
    """Projects initialised by older versions carry only ``integration``."""
    from specify_cli.bundles.project import active_integration

    project = _write_marker(tmp_path, '{"integration": "copilot"}')
    assert active_integration(project) == "copilot"


@pytest.mark.parametrize(
    "recorded,expected",
    [
        ("copilot", "copilot"),
        ("  copilot  ", "copilot"),  # padded: previously returned verbatim
        ("   ", None),  # whitespace-only: previously truthy
        ("\t\n", None),
        ("", None),
        (None, None),
        (5, None),
    ],
    ids=["plain", "padded", "spaces", "tabs", "empty", "null", "non_string"],
)
def test_active_integration_matches_the_canonical_key_reader(
    tmp_path: Path, recorded, expected
):
    """`active_integration` must normalize the way the canonical reader does.

    That reader runs every value through `clean_integration_key`, while this
    one only checked `isinstance(value, str) and value`. A whitespace-only key
    is truthy, so it was returned as a real integration *and* suppressed the
    "not determinable" fallback; a padded key was returned verbatim and
    matches no registered integration.
    """
    from specify_cli.bundles.project import active_integration

    project = _write_marker(tmp_path, json.dumps({"default_integration": recorded}))
    assert active_integration(project) == expected


@pytest.mark.parametrize(
    "recorded,expected",
    [
        ({"default_integration": "   ", "integration": "copilot"}, "copilot"),
        ({"default_integration": "\t\n", "integration": "  copilot  "}, "copilot"),
        ({"default_integration": 5, "integration": "copilot"}, "copilot"),
        ({"integration": "   ", "id": "claude"}, "claude"),
        ({"default_integration": "   ", "integration": "   "}, None),
        ({"default_integration": "cursor", "integration": "copilot"}, "cursor"),
    ],
    ids=[
        "blank_default",
        "blank_default_padded_legacy",
        "non_string_default",
        "blank_legacy_falls_to_id",
        "all_blank",
        "precedence_kept",
    ],
)
def test_active_integration_cleans_each_candidate_before_selecting(
    tmp_path: Path, recorded, expected
):
    """Each candidate must be cleaned before selection, not just the winner.

    A raw `or` chain selects a whitespace-only `default_integration` (truthy)
    and then normalizes it to None, losing the valid legacy key behind it --
    while `normalize_integration_state` does
    `clean_integration_key(default) or legacy_key` and falls through.
    """
    from specify_cli.bundles.project import active_integration

    project = _write_marker(tmp_path, json.dumps(recorded))
    assert active_integration(project) == expected


@pytest.mark.parametrize(
    "recorded,expected",
    [
        ({"installed_integrations": ["claude", "copilot"]}, "claude"),
        ({"installed_integrations": ["   ", "  claude  "]}, "claude"),
        ({"installed_integrations": []}, None),
        ({"installed_integrations": "claude"}, None),
    ],
    ids=["installed_only", "blank_first_entry", "empty_list", "non_list"],
)
def test_active_integration_resolves_installed_only_state(
    tmp_path: Path, recorded, expected
):
    """Installed-only state resolves exactly as the canonical reader does.

    With ``installed_integrations`` populated but no default recorded,
    ``normalize_integration_state`` promotes the first installed key to the
    default. ``active_integration`` returned None instead -- "cannot be
    determined" -- which lets an explicit ``--integration`` bypass the FR-019
    integration-clash guard in ``bundle install`` / ``bundle update``.
    """
    from specify_cli.bundles.project import active_integration
    from specify_cli.integration_state import (
        default_integration_key,
        normalize_integration_state,
    )

    project = _write_marker(tmp_path, json.dumps(recorded))
    assert active_integration(project) == expected
    assert expected == default_integration_key(normalize_integration_state(recorded))


@pytest.mark.parametrize(
    "recorded,expected",
    [
        ({"integration": "copilot", "installed_integrations": ["claude"]}, "copilot"),
        ({"id": "cursor", "installed_integrations": ["claude"]}, "cursor"),
    ],
    ids=["recorded_default_wins", "legacy_id_still_wins"],
)
def test_active_integration_installed_fallback_is_checked_last(
    tmp_path: Path, recorded, expected
):
    """The installed-only fallback must not change any marker that already
    resolved: it is consulted only after every recorded field, so it can turn
    a None into a key but never replace a key this function already returned.
    """
    from specify_cli.bundles.project import active_integration

    project = _write_marker(tmp_path, json.dumps(recorded))
    assert active_integration(project) == expected


def test_read_catalog_config_refuses_symlinked_specify_escape(tmp_path: Path):
    from specify_cli.bundles import catalog_config as cc

    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bundle-catalogs.yml").write_text(
        "schema_version: '1.0'\ncatalogs: []\n", encoding="utf-8"
    )
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    with pytest.raises(BundlerError, match="escapes the allowed root"):
        cc._read(project)


def test_load_source_stack_refuses_symlinked_specify_dir(tmp_path: Path):
    from specify_cli.bundles.catalogs import load_source_stack

    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bundle-catalogs.yml").write_text("catalogs: []\n", encoding="utf-8")
    try:
        (project / ".specify").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    with pytest.raises(BundlerError, match="escapes the allowed root"):
        load_source_stack(project)


def test_find_project_root_ignores_symlinked_specify(tmp_path: Path):
    from specify_cli.bundles.project import find_project_root

    real = tmp_path / "real-specify"
    real.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    # A symlinked .specify must not be accepted as a project root.
    assert find_project_root(project) is None


def test_find_project_root_override_errors_on_symlinked_specify(tmp_path: Path, monkeypatch):
    """The SPECIFY_INIT_DIR override path refuses a symlinked .specify too,
    matching the cwd loop path (regression: the override returned early and
    skipped the symlink guard)."""
    from specify_cli.bundles.project import find_project_root

    real = tmp_path / "real-specify"
    real.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(project))
    with pytest.raises(BundlerError, match="symlinked \\.specify"):
        find_project_root(None)
