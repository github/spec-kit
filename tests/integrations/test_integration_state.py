"""Tests for integration state normalization helpers."""

import json

import pytest

from specify_cli.file_helper import SymlinkDeniedError
from specify_cli.integration_state import (
    INTEGRATION_JSON,
    default_integration_key,
    integration_setting,
    normalize_integration_state,
    try_read_integration_json,
    try_read_integration_json_with_raw,
    write_integration_json,
)
from specify_cli.integrations._file_changes import file_change_observer


def test_normalize_integration_state_strips_default_key_without_duplicates():
    state = normalize_integration_state(
        {
            "default_integration": " claude ",
            "integration": " claude ",
            "installed_integrations": ["claude"],
        }
    )

    assert state["integration"] == "claude"
    assert state["default_integration"] == "claude"
    assert state["installed_integrations"] == ["claude"]


def test_normalize_integration_state_strips_legacy_key_fallback():
    state = normalize_integration_state(
        {
            "integration": " codex ",
            "installed_integrations": [],
        }
    )

    assert state["integration"] == "codex"
    assert state["default_integration"] == "codex"
    assert state["installed_integrations"] == ["codex"]


def test_normalize_integration_state_preserves_newer_schema():
    state = normalize_integration_state(
        {
            "integration_state_schema": 99,
            "integration": "claude",
            "installed_integrations": ["claude"],
            "future_field": {"keep": True},
        }
    )

    assert state["integration_state_schema"] == 99
    assert state["future_field"] == {"keep": True}


def test_default_integration_key_strips_raw_state_values():
    assert default_integration_key({"default_integration": " claude "}) == "claude"
    assert default_integration_key({"integration": " codex "}) == "codex"


def test_integration_settings_strip_invoke_separator():
    setting = integration_setting(
        {
            "integration_settings": {
                "claude": {
                    "invoke_separator": " - ",
                }
            }
        },
        "claude",
    )

    assert setting["invoke_separator"] == "-"


def test_write_integration_json_strips_integration_key(tmp_path):
    write_integration_json(
        tmp_path,
        version="1.2.3",
        integration_key=" claude ",
        installed_integrations=["claude"],
    )

    state = json.loads((tmp_path / INTEGRATION_JSON).read_text(encoding="utf-8"))
    assert state["integration"] == "claude"
    assert state["default_integration"] == "claude"
    assert state["installed_integrations"] == ["claude"]


@pytest.fixture(params=[
    "external-file",
    "dangling-file",
    "contained-file",
    "cyclic-file",
    "external-directory",
    "dangling-directory",
    "contained-directory",
])
def linked_integration_state(tmp_path, request):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "integration.json").write_text('{"integration": "claude"}\n', encoding="utf-8")
    contained = project / "state"
    contained.mkdir()
    (contained / "integration.json").write_text('{"integration": "claude"}\n', encoding="utf-8")
    kind = request.param
    if kind.endswith("directory"):
        target = {
            "external-directory": outside,
            "dangling-directory": outside / "missing",
            "contained-directory": contained,
        }[kind]
        link = project / ".specify"
    else:
        (project / ".specify").mkdir()
        link = project / INTEGRATION_JSON
        target = {
            "external-file": outside / "integration.json",
            "dangling-file": outside / "missing.json",
            "contained-file": contained / "integration.json",
            "cyclic-file": link,
        }[kind]
    try:
        link.symlink_to(target, target_is_directory=kind.endswith("directory"))
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    return project, link, target, outside, contained


@pytest.mark.parametrize("reader", [try_read_integration_json, try_read_integration_json_with_raw])
def test_read_integration_json_rejects_symlinks(linked_integration_state, reader):
    project, link, _, _, _ = linked_integration_state

    *states, error = reader(project)

    assert all(state is None for state in states)
    assert error is not None
    assert error.kind == "os"
    assert "symlink" in error.detail.lower()
    assert "Replace linked entries" in error.detail
    assert "allow_symlinks does not apply to integration state" in error.detail
    assert "explicitly allow symlinks" not in error.detail
    assert link.is_symlink()


def test_write_integration_json_rejects_symlinks_before_observer(linked_integration_state):
    project, link, _, outside, contained = linked_integration_state
    original_target = link.readlink()
    original = (outside / "integration.json").read_bytes()
    contained_original = (contained / "integration.json").read_bytes()
    changes = []
    token = file_change_observer.set(lambda *args: changes.append(args))
    try:
        with pytest.raises(SymlinkDeniedError, match="symlink") as exc_info:
            write_integration_json(project, version="1.2.3", integration_key="codex")
    finally:
        file_change_observer.reset(token)

    assert changes == []
    assert "Replace linked entries" in str(exc_info.value)
    assert "allow_symlinks does not apply to integration state" in str(exc_info.value)
    assert "explicitly allow symlinks" not in str(exc_info.value)
    assert link.is_symlink()
    assert link.readlink() == original_target
    assert (outside / "integration.json").read_bytes() == original
    assert (contained / "integration.json").read_bytes() == contained_original
    assert not (outside / "missing.json").exists()
    assert not (outside / "missing").exists()


def test_write_integration_json_preserves_observer_and_regular_file(tmp_path):
    destination = tmp_path / INTEGRATION_JSON
    destination.parent.mkdir()
    destination.write_text('{"integration": "claude"}\n', encoding="utf-8")
    original = destination.read_bytes()
    changes = []
    token = file_change_observer.set(
        lambda path, before, removal: changes.append((path, before, removal, path.read_bytes()))
    )
    try:
        write_integration_json(tmp_path, version="1.2.3", integration_key="codex")
    finally:
        file_change_observer.reset(token)

    assert changes == [
        (destination, True, False, original),
        (destination, False, False, destination.read_bytes()),
    ]
    state, raw, error = try_read_integration_json_with_raw(tmp_path)
    assert error is None
    assert state == raw
    assert state["integration"] == "codex"


@pytest.mark.parametrize("reader", [try_read_integration_json, try_read_integration_json_with_raw])
def test_read_integration_json_missing_is_not_an_error(tmp_path, reader):
    assert all(value is None for value in reader(tmp_path))


def test_integration_state_accepts_trusted_root_alias(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(project, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    write_integration_json(alias, version="1.2.3", integration_key="claude")
    state, error = try_read_integration_json(alias)

    assert error is None
    assert state["integration"] == "claude"
    assert (project / INTEGRATION_JSON).is_file()


def test_with_integration_setting_recomputes_separator_from_retained_options():
    """Updating only script_type must not drop an options-dependent separator.

    Copilot resolves the command-ref separator to '.' when '--commands' is
    stored and '-' by default. A second call that changes only script_type
    (parsed_options=None, raw_options=None) retains the stored parsed_options,
    so invoke_separator must stay '.', not be recomputed from the None argument.
    """
    from specify_cli.integrations import get_integration
    from specify_cli.integration_runtime import with_integration_setting

    copilot = get_integration("copilot")

    settings = with_integration_setting(
        {}, "copilot", copilot, parsed_options={"commands": True}
    )
    assert settings["copilot"]["invoke_separator"] == "."

    settings2 = with_integration_setting(
        {"integration_settings": settings}, "copilot", copilot, script_type="ps"
    )
    # parsed_options are retained (only script_type changed) ...
    assert settings2["copilot"]["parsed_options"] == {"commands": True}
    assert settings2["copilot"]["script"] == "ps"
    # ... so the separator must reflect them, not the (None) argument.
    assert settings2["copilot"]["invoke_separator"] == "."
