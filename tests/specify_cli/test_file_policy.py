"""Strict project policy and configuration bootstrap contracts."""

import asyncio
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.file_helper import FileHelper


def policy_module():
    from specify_cli import _file_policy

    return _file_policy


@pytest.fixture
def symlinks(tmp_path):
    probe = tmp_path / "probe"
    try:
        probe.symlink_to(tmp_path, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")
    probe.unlink()


@pytest.mark.parametrize("options,allowed", [({}, False), ({"allow_symlinks": False}, False), ({"allow_symlinks": True}, True)])
def test_policy_is_literal_and_fresh(tmp_path, options, allowed):
    policy = policy_module()
    assert policy.project_files(tmp_path).allow_symlinks is False
    policy.save_project_options(tmp_path, options)
    files = policy.project_files(tmp_path)
    assert files.allow_symlinks is allowed
    policy.save_project_options(tmp_path, {"allow_symlinks": not allowed})
    assert policy.project_files(tmp_path).allow_symlinks is not allowed
    assert files.allow_symlinks is allowed


@pytest.mark.parametrize("value", ["true", "false", 0, 1, None, [], {}])
def test_invalid_policy_values(tmp_path, value):
    path = tmp_path / ".specify"
    path.mkdir()
    (path / "init-options.json").write_text(json.dumps({"allow_symlinks": value}))
    with pytest.raises(policy_module().ProjectPolicyError, match="boolean"):
        policy_module().project_files(tmp_path)


@pytest.mark.parametrize("document", [
    "{", "[]", "null", '"text"', "true", "1", "\xff",
    '{"custom": NaN}', '{"custom": Infinity}', '{"custom": -Infinity}',
])
def test_invalid_documents(tmp_path, document):
    path = tmp_path / ".specify"
    path.mkdir()
    (path / "init-options.json").write_bytes(document.encode("latin1"))
    with pytest.raises(policy_module().ProjectPolicyError, match="init-options.json"):
        policy_module().project_files(tmp_path)


@pytest.mark.parametrize("leaf,dangling", [(False, False), (False, True), (True, False), (True, True)])
def test_bootstrap_links_always_denied(tmp_path, symlinks, leaf, dangling):
    policy = policy_module()
    target = tmp_path / "target"
    if leaf:
        (tmp_path / ".specify").mkdir()
        if not dangling:
            target.write_text('{"allow_symlinks": true}')
        (tmp_path / ".specify/init-options.json").symlink_to(target)
    else:
        if not dangling:
            target.mkdir()
            (target / "init-options.json").write_text('{"allow_symlinks": true}')
        (tmp_path / ".specify").symlink_to(target, target_is_directory=True)
    with pytest.raises(policy.ProjectPolicyError, match="symlink"):
        policy.project_files(tmp_path)
    with pytest.raises(policy.ProjectPolicyError, match="symlink"):
        policy.save_project_options(tmp_path, {"allow_symlinks": True})


def test_permission_failure_is_not_missing(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr(FileHelper, "read_text", denied)
    with pytest.raises(policy_module().ProjectPolicyError, match="permission denied"):
        policy_module().project_files(tmp_path)


def test_configuration_directory_is_not_a_document(tmp_path):
    (tmp_path / ".specify/init-options.json").mkdir(parents=True)
    with pytest.raises(policy_module().ProjectPolicyError):
        policy_module().project_files(tmp_path)


def test_policy_root_alias_is_trusted(tmp_path, symlinks):
    root = tmp_path / "project"
    root.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    policy_module().save_project_options(alias, {"allow_symlinks": True})
    assert policy_module().project_files(alias).allow_symlinks is True


def test_project_commands_recheck_edits_and_render_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".specify/init-options.json"
    config.parent.mkdir()
    runner = CliRunner()
    config.write_text('{"allow_symlinks": false}')
    assert runner.invoke(app, ["extension", "list", "--json"]).exit_code == 0
    config.write_text('{"allow_symlinks": "true"}')
    result = runner.invoke(app, ["extension", "list", "--json"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "boolean" in json.loads(result.stderr)["error"]
    config.write_text('{"allow_symlinks": true}')
    assert runner.invoke(app, ["extension", "list", "--json"]).exit_code == 0


@pytest.mark.parametrize("args", [["--help"], ["--version"], ["version", "--json"], ["init", "--help"]])
def test_projectless_commands_ignore_unrelated_invalid_policy(tmp_path, monkeypatch, args):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".specify/init-options.json"
    config.parent.mkdir()
    config.write_text("{")
    result = CliRunner().invoke(app, args)
    assert "init-options.json" not in result.output
    assert result.exit_code == 0


@pytest.mark.parametrize("allowed", [False, True])
def test_init_persists_policy_and_preserves_unrelated_options(tmp_path, monkeypatch, allowed):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".specify/init-options.json"
    config.parent.mkdir()
    config.write_text('{"custom": "retained", "allow_symlinks": true}')
    args = ["init", "--here", "--force", "--non-interactive", "--integration", "generic",
            "--integration-options=--commands-dir .agent/commands", "--ignore-agent-tools"]
    if allowed:
        args.append("--allow-symlinks")
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    options = json.loads(config.read_text())
    assert options["allow_symlinks"] is allowed
    assert options["custom"] == "retained"


@pytest.mark.parametrize("args", [["--allow-symlinks"], ["extension", "list", "--allow-symlinks"], ["workflow", "run", "x", "--allow-symlinks"]])
def test_option_is_init_only(args):
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 2
    assert "No such option" in result.output


def test_init_rejects_policy_before_scaffolding(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".specify/init-options.json"
    config.parent.mkdir()
    config.write_text("{")
    before = set(tmp_path.iterdir())
    result = CliRunner().invoke(app, ["init", "--here", "--force", "--allow-symlinks", "--non-interactive"])
    assert result.exit_code == 1
    assert "init-options.json" in result.output
    assert set(tmp_path.iterdir()) == before


@pytest.mark.parametrize("args", [
    ["extension", "list", "--json"], ["preset", "list", "--json"],
    ["artifact", "list", "--json"], ["artifact", "info", "speckit.plan", "--json"],
    ["integration", "status", "--json"],
    ["workflow", "status", "--json"], ["workflow", "resume", "missing", "--json"],
    ["workflow", "run", "missing", "--json"],
    ["bundle", "list", "--json"], ["bundle", "search", "--offline", "--json"],
    ["bundle", "info", "missing", "--offline", "--json"],
])
def test_policy_failures_use_json_error_surfaces(tmp_path, monkeypatch, args):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify/init-options.json").write_text("{")
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1, result.exception
    assert result.stdout == ""
    assert "init-options.json" in json.loads(result.stderr)["error"]


def test_override_checks_selected_project_only(tmp_path, monkeypatch):
    project = tmp_path / "member"
    project.mkdir()
    policy_module().save_project_options(project, {"allow_symlinks": True})
    policy_module().save_project_options(tmp_path, {})
    (tmp_path / ".specify/init-options.json").write_text("{")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPECIFY_INIT_DIR", "member")
    from specify_cli._project import resolve_specify_project_files

    assert resolve_specify_project_files().root == project.resolve()
    assert resolve_specify_project_files().allow_symlinks is True
    assert CliRunner().invoke(app, ["extension", "list", "--json"]).exit_code == 0
    (project / ".specify/init-options.json").write_text('{"allow_symlinks": null}')
    result = CliRunner().invoke(app, ["extension", "list", "--json"])
    assert result.exit_code == 1
    assert "boolean" in json.loads(result.stderr)["error"]


def test_no_new_ancestor_discovery(tmp_path, monkeypatch):
    policy_module().save_project_options(tmp_path, {"allow_symlinks": True})
    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    result = CliRunner().invoke(app, ["extension", "list", "--json"])
    assert result.exit_code == 1
    assert "Not a Spec Kit project" in json.loads(result.stderr)["error"]


def test_init_explicit_target_ignores_override_and_cwd_policy(tmp_path, monkeypatch):
    policy_module().save_project_options(tmp_path, {})
    (tmp_path / ".specify/init-options.json").write_text("{")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "nonexistent"))
    result = CliRunner().invoke(app, [
        "init", "nested/project", "--allow-symlinks", "--non-interactive",
        "--integration", "generic", "--integration-options=--commands-dir .agent/commands",
        "--ignore-agent-tools",
    ])
    assert result.exit_code == 0, result.output
    assert policy_module().project_files(tmp_path / "nested/project").allow_symlinks is True


def test_direct_workflow_preflights_policy_without_requiring_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workflow = tmp_path / "local.yml"
    workflow.write_text(
        "workflow:\n  id: local\n  name: Local\n  version: 1.0.0\n"
        "steps:\n  - id: done\n    type: shell\n    run: echo done\n"
    )
    policy_module().save_project_options(tmp_path, {})
    (tmp_path / ".specify/init-options.json").write_text("{")
    result = CliRunner().invoke(app, ["workflow", "run", str(workflow), "--json"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "init-options.json" in json.loads(result.stderr)["error"]
    (tmp_path / ".specify/init-options.json").unlink()
    (tmp_path / ".specify").rmdir()
    result = CliRunner().invoke(app, ["workflow", "run", str(workflow), "--json"])
    assert result.exit_code == 0, result.output


def test_configuration_write_preserves_permissions_inode_and_hardlinks(tmp_path):
    policy_module().save_project_options(tmp_path, {"custom": "caf\u00e9"})
    config = tmp_path / ".specify/init-options.json"
    before = config.stat().st_ino
    config.chmod(0o600)
    os.link(config, tmp_path / "hardlink")
    policy_module().save_project_options(tmp_path, {"custom": "retained", "allow_symlinks": True})
    assert config.stat().st_ino == before
    assert json.loads((tmp_path / "hardlink").read_text())["allow_symlinks"] is True
    if os.name != "nt":
        assert config.stat().st_mode & 0o777 == 0o600


def test_write_permission_errors_are_explicit(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr(FileHelper, "overwrite_text", denied)
    with pytest.raises(policy_module().ProjectPolicyError, match="permission denied"):
        policy_module().save_project_options(tmp_path, {"allow_symlinks": False})


@pytest.mark.parametrize("command", [["bundle", "list", "--json"], ["bundle", "init"]])
def test_bundle_resolved_project_does_not_ignore_corrupt_policy(tmp_path, monkeypatch, command):
    policy_module().save_project_options(tmp_path, {})
    (tmp_path / ".specify/init-options.json").write_text("{")
    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    result = CliRunner().invoke(app, command)
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "init-options.json" in result.stderr


def test_integration_updates_preserve_policy(tmp_path):
    from specify_cli.integrations import get_integration
    from specify_cli.integrations._helpers import (
        _update_init_options_for_integration, _clear_init_options_for_integration,
        _refresh_init_options_speckit_version,
    )

    policy_module().save_project_options(tmp_path, {"allow_symlinks": True, "custom": "retained"})
    _update_init_options_for_integration(tmp_path, get_integration("copilot"), script_type="sh")
    _refresh_init_options_speckit_version(tmp_path)
    _clear_init_options_for_integration(tmp_path, "copilot")
    options = policy_module().read_project_options(tmp_path)
    assert options["allow_symlinks"] is True
    assert options["custom"] == "retained"
    assert "ai" not in options


@pytest.mark.parametrize("leaf", [False, True])
def test_init_flag_cannot_authorize_bootstrap_links(tmp_path, monkeypatch, symlinks, leaf):
    monkeypatch.chdir(tmp_path)
    if leaf:
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify/init-options.json").symlink_to(tmp_path / "missing")
    else:
        (tmp_path / ".specify").symlink_to(tmp_path / "missing", target_is_directory=True)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--allow-symlinks", "--non-interactive",
        "--integration", "copilot", "--ignore-agent-tools",
    ])
    assert result.exit_code == 1
    assert "symlink" in result.output
    assert not (tmp_path / ".github").exists()
    assert not (tmp_path / "missing").exists()


def test_new_configuration_respects_umask(tmp_path):
    previous = os.umask(0o077)
    try:
        policy_module().save_project_options(tmp_path, {})
    finally:
        os.umask(previous)
    if os.name != "nt":
        assert (tmp_path / ".specify/init-options.json").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("value", ["false", 1, None])
def test_invalid_write_policy_fails_before_creation(tmp_path, value):
    with pytest.raises(policy_module().ProjectPolicyError, match="boolean"):
        policy_module().save_project_options(tmp_path, {"allow_symlinks": value})
    assert not (tmp_path / ".specify").exists()


@pytest.mark.parametrize("value", [float("nan"), object()])
def test_unserializable_options_fail_before_creation(tmp_path, value):
    with pytest.raises(policy_module().ProjectPolicyError, match="Cannot encode"):
        policy_module().save_project_options(tmp_path, {"custom": value})
    assert not (tmp_path / ".specify").exists()


@pytest.mark.parametrize("args", [["bundle", "search", "--offline"], ["bundle", "info", "nonexistent", "--offline"]])
def test_projectless_catalog_commands_do_not_require_policy(tmp_path, monkeypatch, args):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, args)
    assert "init-options.json" not in result.output
    assert "Not a Spec Kit project" not in result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)


@pytest.mark.parametrize("args", [
    ["bundle", "init"], ["bundle", "install", "missing", "--offline"],
    ["bundle", "list"], ["bundle", "list", "--json"],
    ["bundle", "search", "--offline"], ["bundle", "search", "--offline", "--json"],
    ["bundle", "info", "missing", "--offline"],
    ["bundle", "info", "missing", "--offline", "--json"],
])
@pytest.mark.parametrize("parent_project", [False, True])
@pytest.mark.parametrize("dangling", [False, True])
def test_bundle_forbidden_marker_fails_without_initialization_or_install(
    tmp_path, monkeypatch, symlinks, args, parent_project, dangling,
):
    from unittest.mock import patch

    if parent_project:
        policy_module().save_project_options(tmp_path, {})
    member = tmp_path / "member"
    member.mkdir()
    target = tmp_path / "linked-config"
    if not dangling:
        target.mkdir()
        (target / "init-options.json").write_text('{"allow_symlinks": true}')
    (member / ".specify").symlink_to(target, target_is_directory=True)
    monkeypatch.chdir(member)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    before = set(tmp_path.rglob("*"))
    with (
        patch("specify_cli.bundles.command_init._run_init") as init,
        patch("specify_cli.bundles.command_install._run_init") as install_init,
        patch("specify_cli.bundles.installer.install_bundle") as install,
    ):
        result = CliRunner().invoke(app, args)
    assert result.exit_code == 1, result.output
    assert result.stdout == ""
    if "--json" in args:
        assert "symlink" in json.loads(result.stderr)["error"]
    else:
        assert "symlink" in result.stderr
    assert not init.called and not install_init.called and not install.called
    assert set(tmp_path.rglob("*")) == before


def _configuration_case(root, case):
    marker = root / ".specify"
    marker.mkdir()
    config = marker / "init-options.json"
    if case == "marker-link":
        target = root / "linked-config"
        marker.rename(target)
        (target / "init-options.json").write_text('{"allow_symlinks": true}')
        marker.symlink_to(target, target_is_directory=True)
    elif case in {"leaf-link", "dangling-link"}:
        target = root / "linked-options.json"
        if case == "leaf-link":
            target.write_text('{"allow_symlinks": true}')
        config.symlink_to(target)
    else:
        config.write_text(case)


@pytest.mark.parametrize("case", [
    "{", '{"allow_symlinks": 1}', "[]", "marker-link", "leaf-link", "dangling-link",
])
@pytest.mark.parametrize("explicit", [False, True])
def test_init_lifecycle_policy_precedes_preparation(tmp_path, monkeypatch, symlinks, case, explicit):
    from specify_cli.integrations import _lifecycle, installer

    root = tmp_path / "target" if explicit else tmp_path
    root.mkdir(exist_ok=True)
    _configuration_case(root, case)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "unrelated"))
    handler = Mock()

    def init_handler(project_name=None, here=False, integration=None):
        handler()

    invoke = _lifecycle.external_lifecycle("init")(init_handler)
    with (
        patch.object(installer, "read_records", return_value={}) as records,
        patch.object(installer, "load_installed_integrations") as loader,
        patch.object(installer, "catalog_package") as catalog,
        patch.object(_lifecycle, "_transaction") as transaction,
        pytest.raises(typer.Exit) as failure,
    ):
        invoke(project_name=str(root) if explicit else None, here=not explicit, integration="generic")
    assert failure.value.exit_code == 1
    handler.assert_not_called()
    records.assert_not_called()
    loader.assert_not_called()
    catalog.assert_not_called()
    transaction.assert_not_called()


@pytest.mark.parametrize("options", [None, {}, {"allow_symlinks": False}, {"allow_symlinks": True}])
def test_init_lifecycle_selects_explicit_target(tmp_path, monkeypatch, options):
    from specify_cli.integrations import _lifecycle, installer

    root = tmp_path / "target"
    root.mkdir()
    if options is not None:
        policy_module().save_project_options(root, options)
    _configuration_case(tmp_path, "{")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "unrelated"))
    seen = []

    @_lifecycle.external_lifecycle("init")
    def handler(project_name=None, integration=None):
        seen.append(project_name)

    with (
        patch.object(installer, "read_records", return_value={}) as records,
        patch.object(installer, "load_installed_integrations") as loader,
    ):
        handler(project_name=str(root), integration="generic")
    assert seen == [str(root)]
    assert all(call.args == (root.resolve(),) for call in records.call_args_list)
    assert all(call.args == (root.resolve(),) for call in loader.call_args_list)


@pytest.mark.parametrize("existing", [False, True])
def test_policy_write_rolls_back_with_init_transaction(tmp_path, existing):
    from specify_cli.integrations import _lifecycle

    root = tmp_path / "target"
    original = {"allow_symlinks": True, "custom": "retained"}
    if existing:
        root.mkdir()
        policy_module().save_project_options(root, original)
    with pytest.raises(RuntimeError, match="downstream init failed"):
        with _lifecycle._transaction(root, "generic", None, {}):
            policy_module().save_project_options(root, {"allow_symlinks": False})
            raise RuntimeError("downstream init failed")
    if existing:
        assert policy_module().read_project_options(root) == original
    else:
        assert not root.exists()


@pytest.mark.parametrize("case", ["marker-link", "leaf-link", "dangling-link"])
def test_configuration_denial_precedes_observer_snapshot(tmp_path, symlinks, case):
    from specify_cli.integrations._file_changes import file_change_observer

    _configuration_case(tmp_path, case)
    observer = Mock()
    token = file_change_observer.set(observer)
    try:
        with pytest.raises(policy_module().ProjectPolicyError, match="symlink"):
            policy_module().save_project_options(tmp_path, {"allow_symlinks": True})
    finally:
        file_change_observer.reset(token)
    observer.assert_not_called()


def test_configuration_observer_surrounds_actual_write(tmp_path):
    from specify_cli.integrations._file_changes import file_change_observer

    original = {"allow_symlinks": True, "custom": "retained"}
    replacement = {"allow_symlinks": False, "custom": "retained"}
    policy_module().save_project_options(tmp_path, original)
    seen = []

    def observe(path, before, removal=False):
        seen.append((path, before, json.loads(path.read_text())))

    token = file_change_observer.set(observe)
    try:
        policy_module().save_project_options(tmp_path, replacement)
    finally:
        file_change_observer.reset(token)
    destination = tmp_path / ".specify/init-options.json"
    assert seen == [(destination, True, original), (destination, False, replacement)]


def test_init_lifecycle_unreadable_policy_precedes_project_work(tmp_path, monkeypatch):
    from specify_cli.integrations import _lifecycle, installer

    policy_module().save_project_options(tmp_path, {})

    def denied(*args, **kwargs):
        raise PermissionError("configuration permission denied")

    monkeypatch.setattr(FileHelper, "read_bytes", denied)
    called = Mock()

    @_lifecycle.external_lifecycle("init")
    def handler(project_name=None, integration=None):
        called()

    with (
        patch.object(installer, "read_records", return_value={}) as records,
        patch.object(installer, "load_installed_integrations") as loader,
        pytest.raises(typer.Exit) as failure,
    ):
        handler(project_name=str(tmp_path), integration="generic")
    assert failure.value.exit_code == 1
    assert "permission denied" in str(failure.value.__cause__)
    records.assert_not_called()
    loader.assert_not_called()
    called.assert_not_called()


@pytest.mark.parametrize("alias", [False, True])
def test_init_transaction_retains_requested_spelling_and_initial_state(tmp_path, monkeypatch, symlinks, alias):
    from specify_cli.integrations import _lifecycle, installer

    parent = tmp_path / "parent"
    parent.mkdir()
    requested_parent = tmp_path / "alias" if alias else parent
    if alias:
        requested_parent.symlink_to(parent, target_is_directory=True)
    requested = requested_parent / "new"
    prepared = []
    original_prepare = policy_module().prepare_init_root

    def prepare(target):
        prepared.append(target)
        return original_prepare(target)

    monkeypatch.setattr(policy_module(), "prepare_init_root", prepare)
    monkeypatch.setattr(installer, "read_records", lambda root: {"generic": {}})
    monkeypatch.setattr(installer, "load_installed_integrations", lambda root: None)

    @_lifecycle.external_lifecycle("init")
    def handler(project_name=None, integration=None):
        assert _lifecycle.initial_directory_state(Path(project_name).absolute()) == (False, [])
        policy_module().save_project_options(Path(project_name).resolve(), {"allow_symlinks": True})
        raise RuntimeError("downstream init failed")

    with pytest.raises(typer.Exit) as failure:
        handler(project_name=str(requested), integration="generic")
    assert failure.value.exit_code == 1
    assert prepared == [requested]
    assert not requested.exists()


def test_init_transaction_does_not_resolve_away_dangling_parent(tmp_path, monkeypatch, symlinks):
    from specify_cli.integrations import _lifecycle, installer

    missing = tmp_path / "missing-parent"
    alias = tmp_path / "alias"
    alias.symlink_to(missing, target_is_directory=True)
    monkeypatch.setattr(installer, "read_records", lambda root: {"generic": {}})
    monkeypatch.setattr(installer, "load_installed_integrations", lambda root: None)
    called = []

    @_lifecycle.external_lifecycle("init")
    def handler(project_name=None, integration=None):
        called.append(project_name)
        raise RuntimeError("must not invoke handler")

    with pytest.raises(typer.Exit):
        handler(project_name=str(alias / "new"), integration="generic")
    assert called == []
    assert not missing.exists()


@pytest.mark.parametrize("case", ["dangling-parent", "missing-parent-traversal"])
def test_new_init_target_preserves_evidence_before_project_reads(tmp_path, symlinks, case):
    from specify_cli.integrations import _lifecycle, installer

    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    policy_module().save_project_options(unrelated, {"allow_symlinks": True})
    if case == "dangling-parent":
        alias = tmp_path / "alias"
        alias.symlink_to(tmp_path / "missing", target_is_directory=True)
        requested = alias / "new"
    else:
        requested = tmp_path / "missing" / ".." / "unrelated"
    called = Mock()

    @_lifecycle.external_lifecycle("init")
    def handler(project_name=None, integration=None):
        called()

    with (
        patch.object(installer, "read_records", return_value={}) as records,
        patch.object(installer, "load_installed_integrations") as loader,
        patch.object(installer, "catalog_package") as catalog,
        pytest.raises(typer.Exit),
    ):
        handler(project_name=str(requested), integration="generic")
    records.assert_not_called()
    loader.assert_not_called()
    catalog.assert_not_called()
    called.assert_not_called()
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("override", [False, True])
@pytest.mark.parametrize("document", [None, "{}", '{"allow_symlinks": true}', '{"allow_symlinks": false}'])
def test_check_policy_optional_project_and_override(tmp_path, monkeypatch, override, document):
    root = tmp_path / "selected" if override else tmp_path
    root.mkdir(exist_ok=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    if override:
        _configuration_case(tmp_path, "{")
        monkeypatch.setenv("SPECIFY_INIT_DIR", "selected")
        (root / ".specify").mkdir()
    if document is not None:
        (root / ".specify").mkdir(exist_ok=True)
        (root / ".specify/init-options.json").write_text(document)
    with (
        patch("specify_cli.integrations.installer.load_installed_integrations") as loader,
        patch("specify_cli.integrations.installer.read_records", return_value={}) as records,
        patch("specify_cli.check_tool", return_value=True) as tools,
    ):
        result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 0, result.output
    loader.assert_called_once_with(root)
    records.assert_called_once_with(root)
    assert tools.called


@pytest.mark.parametrize("override", [False, True])
@pytest.mark.parametrize("case", ["{", '{"allow_symlinks": null}', "marker-link", "leaf-link", "dangling-link"])
def test_check_policy_failure_precedes_adapters_and_tools(tmp_path, monkeypatch, symlinks, override, case):
    root = tmp_path / "selected" if override else tmp_path
    root.mkdir(exist_ok=True)
    _configuration_case(root, case)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    if override:
        monkeypatch.setenv("SPECIFY_INIT_DIR", "selected")
    with (
        patch("specify_cli.integrations.installer.load_installed_integrations") as loader,
        patch("specify_cli.integrations.installer.read_records") as records,
        patch("specify_cli.check_tool") as tools,
    ):
        result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 1, result.output
    assert "init-options.json" in result.output
    loader.assert_not_called()
    records.assert_not_called()
    tools.assert_not_called()


@pytest.mark.parametrize("operation", ["list", "info"])
@pytest.mark.parametrize("case", ["{", '{"allow_symlinks": "true"}', "marker-link", "leaf-link", "dangling-link"])
def test_artifact_operation_policy_failure_precedes_catalog(tmp_path, monkeypatch, symlinks, operation, case):
    from specify_cli.artifacts import _operation_info, _operation_list

    _configuration_case(tmp_path, case)
    catalog = Mock()
    module = _operation_list if operation == "list" else _operation_info
    monkeypatch.setattr(module, "ArtifactCatalog", catalog)
    if operation == "list":
        request = module.ArtifactListRequest(tmp_path)
        call = module.list_artifacts
        expected = module.ArtifactListResolutionError
    else:
        request = module.ArtifactInfoRequest(tmp_path, "speckit.plan")
        call = module.get_artifact_info
        expected = module.ArtifactInfoResolutionError
    with pytest.raises(expected, match="init-options.json") as failure:
        call(request)
    assert failure.value.code == "artifact_resolution_failed"
    catalog.assert_not_called()


@pytest.mark.parametrize("operation", ["list", "info"])
@pytest.mark.parametrize("options", [None, {}, {"allow_symlinks": False}, {"allow_symlinks": True}])
def test_artifact_operations_reload_valid_policy(tmp_path, operation, options):
    from specify_cli.artifacts import _operation_info, _operation_list

    for folder in ["templates", "presets", "extensions"]:
        (tmp_path / ".specify" / folder).mkdir(parents=True, exist_ok=True)
    config = tmp_path / ".specify/init-options.json"
    if options is None:
        config.unlink(missing_ok=True)
    else:
        policy_module().save_project_options(tmp_path, options)
    if operation == "list":
        request = _operation_list.ArtifactListRequest(tmp_path)
        call = _operation_list.list_artifacts
        expected = _operation_list.ArtifactListResolutionError
    else:
        request = _operation_info.ArtifactInfoRequest(tmp_path, "speckit.plan")
        call = _operation_info.get_artifact_info
        expected = _operation_info.ArtifactInfoResolutionError
    assert call(request) is not None
    config.write_text("{")
    with pytest.raises(expected, match="init-options.json"):
        call(request)


@pytest.mark.parametrize("operation", ["list", "info"])
@pytest.mark.parametrize("case", ["{", '{"allow_symlinks": 0}', "marker-link", "leaf-link", "dangling-link"])
def test_artifact_mcp_policy_errors_keep_transport_contract(tmp_path, symlinks, operation, case):
    from specify_cli.mcp_server.server import create_server

    _configuration_case(tmp_path, case)
    arguments = {"identifier": "speckit.plan"} if operation == "info" else {}
    result = asyncio.run(create_server(launch_directory=tmp_path).call_tool(
        f"specify_artifact_{operation}", arguments,
    ))
    assert result.is_error is True
    error = result.structured_content["error"]
    assert error["code"] == "artifact_resolution_failed"
    assert error["retryable"] is False
    assert error["details"]["project_directory"] == str(tmp_path)
    assert "init-options.json" in error["message"]
    assert "Traceback" not in str(result)
