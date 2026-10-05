"""Private machine-readable execution path for ``specify init --json``."""

from __future__ import annotations

import io
import json
import os
import shlex
import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

import typer
from rich.console import Console
from typer.core import TyperCommand

try:
    from typer._click.exceptions import UsageError as _UsageError
except ModuleNotFoundError as error:
    if error.name != "typer._click":
        raise
    from click import UsageError as _UsageError

from ._agent_config import (
    AGENT_CONFIG,
    DEFAULT_INIT_INTEGRATION,
    DEFAULT_INIT_INTEGRATION_ENV_VAR,
    SCRIPT_TYPE_CHOICES,
)
from ._assets import (
    _locate_bundled_preset,
    _locate_bundled_workflow,
    _locate_core_pack,
    _repo_root,
    get_speckit_version,
)
from ._console import StepTracker, console, err_console
from ._utils import check_tool


@dataclass
class InitJsonFailure(Exception):
    """A stable command-specific failure for ``specify init --json``."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class InitJsonCommand(TyperCommand):
    """Keep JSON-mode parse failures on the init error contract."""

    def make_context(self, info_name, args, parent=None, **extra):
        json_output = "--json" in args
        try:
            return super().make_context(info_name, args, parent=parent, **extra)
        except _UsageError as error:
            if json_output:
                _emit_failure(
                    InitJsonFailure(
                        "invalid_arguments",
                        _single_line(error),
                    )
                )
            raise


@dataclass
class _InitPlan:
    project_name: str
    project_path: Path
    operation: str
    target_owned: bool
    here: bool
    force: bool
    integration: Any
    integration_defaulted: bool
    integration_options: dict[str, Any]
    raw_integration_options: str | None
    script_type: str
    script_defaulted: bool
    ignore_agent_tools: bool
    preset: str | None
    extensions: list[str]
    warnings: list[dict[str, Any]]


def _warning(
    code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details or {}}


def _single_line(value: object, *, limit: int = 500) -> str:
    text = " ".join(str(value).split())
    return (text or value.__class__.__name__)[:limit]


def _emit(value: dict[str, Any], *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    stream.write(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def _emit_failure(failure: InitJsonFailure) -> NoReturn:
    _emit(
        {
            "error": {
                "code": failure.code,
                "message": failure.message,
                "details": failure.details,
            }
        },
        error=True,
    )
    raise typer.Exit(1)


def _invalid_integration_options(message: str, **details: Any) -> InitJsonFailure:
    return InitJsonFailure(
        "invalid_integration_options",
        message,
        details,
    )


def _parse_integration_options(
    integration: Any, raw_options: str | None
) -> dict[str, Any]:
    if not raw_options:
        parsed: dict[str, Any] = {}
    else:
        try:
            tokens = shlex.split(raw_options)
        except ValueError as exc:
            raise _invalid_integration_options(
                "Could not parse integration options.",
                reason=_single_line(exc),
            ) from exc

        declared_options = list(integration.options())
        declared = {opt.name.lstrip("-"): opt for opt in declared_options}
        allowed = sorted(opt.name for opt in declared_options)
        parsed = {}
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if not token.startswith("-"):
                raise _invalid_integration_options(
                    "Unexpected integration option value.",
                    value=token,
                    allowed=allowed,
                )
            name = token.lstrip("-")
            value: str | None = None
            if "=" in name:
                name, value = name.split("=", 1)
            option = declared.get(name)
            if option is None:
                raise _invalid_integration_options(
                    "Unknown integration option.",
                    option=token,
                    allowed=allowed,
                )
            key = name.replace("-", "_")
            if option.is_flag:
                if value is not None:
                    raise _invalid_integration_options(
                        "Integration flag does not accept a value.",
                        option=option.name,
                    )
                parsed[key] = True
                i += 1
            elif value is not None:
                parsed[key] = value
                i += 1
            elif i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                parsed[key] = tokens[i + 1]
                i += 2
            else:
                raise _invalid_integration_options(
                    "Integration option requires a value.",
                    option=option.name,
                )

    missing = []
    for option in integration.options():
        if not option.required:
            continue
        key = option.name.lstrip("-").replace("-", "_")
        value = parsed.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(option.name)
    if missing:
        raise _invalid_integration_options(
            "Required integration options were not supplied.",
            missing=missing,
        )

    return parsed


def _validate_integration_mode_options(
    integration: Any,
    parsed_options: dict[str, Any],
    *,
    integration_key: str,
    project_root: Path,
) -> None:
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    try:
        with (
            console.capture() as console_capture,
            err_console.capture() as err_console_capture,
            redirect_stdout(stdout_capture),
            redirect_stderr(stderr_capture),
        ):
            integration.is_skills_mode(
                parsed_options or None,
                project_root=project_root,
            )
    except (ValueError, typer.Exit) as exc:
        captured = (
            stdout_capture.getvalue()
            + console_capture.get()
            + stderr_capture.getvalue()
            + err_console_capture.get()
        )
        raise _invalid_integration_options(
            "Integration options are invalid.",
            integration=integration_key,
            reason=_single_line(captured or exc),
        ) from exc


def _resolve_default_integration(
    warnings: list[dict[str, Any]],
) -> str:
    override = (os.environ.get(DEFAULT_INIT_INTEGRATION_ENV_VAR) or "").strip()
    if not override:
        return DEFAULT_INIT_INTEGRATION
    if override in AGENT_CONFIG:
        return override
    warnings.append(
        _warning(
            "invalid_default_integration",
            "The configured default integration was not recognized; the built-in default was used.",
            {
                "environment_variable": DEFAULT_INIT_INTEGRATION_ENV_VAR,
                "value": override,
                "default": DEFAULT_INIT_INTEGRATION,
            },
        )
    )
    return DEFAULT_INIT_INTEGRATION


def _build_plan(
    *,
    project_name: str | None,
    script_type: str | None,
    ignore_agent_tools: bool,
    here: bool,
    force: bool,
    preset: str | None,
    integration_key: str | None,
    integration_options: str | None,
    extensions: list[str] | None,
    trust_extension_urls: bool,
) -> _InitPlan:
    from .integrations import get_integration

    warnings: list[dict[str, Any]] = []

    if project_name == ".":
        here = True
        project_name = None
    if here and project_name:
        raise InitJsonFailure(
            "conflicting_target_options",
            "Cannot specify both a project name and --here.",
            {"project_name": project_name},
        )
    if not here and not project_name:
        raise InitJsonFailure(
            "target_required",
            "Specify a project name, use '.', or pass --here.",
        )

    if here:
        project_path = Path.cwd().resolve()
        resolved_name = project_path.name
        dir_existed_before = True
    else:
        assert project_name is not None
        project_path = Path(project_name).resolve()
        resolved_name = project_path.name
        dir_existed_before = project_path.exists()

    already_initialized = (project_path / ".specify").is_dir()
    operation = (
        "reinitialized"
        if already_initialized
        else "merged"
        if dir_existed_before
        else "created"
    )

    if dir_existed_before:
        if not project_path.is_dir():
            raise InitJsonFailure(
                "target_not_directory",
                "The target exists but is not a directory.",
                {"path": str(project_path)},
            )
        try:
            existing_items = list(project_path.iterdir())
        except OSError as exc:
            raise InitJsonFailure(
                "target_unavailable",
                "The target directory could not be inspected.",
                {"path": str(project_path), "reason": _single_line(exc)},
            ) from exc
        if not force:
            if here and existing_items:
                raise InitJsonFailure(
                    "target_not_empty",
                    "The current directory is not empty; pass --force to merge into it.",
                    {"path": str(project_path), "item_count": len(existing_items)},
                )
            if not here:
                raise InitJsonFailure(
                    "target_exists",
                    "The target directory already exists; pass --force to merge into it.",
                    {"path": str(project_path), "item_count": len(existing_items)},
                )

    requested_extensions = list(extensions or [])
    untrusted_urls = [
        spec
        for spec in requested_extensions
        if _extension_spec_is_url(spec) and not trust_extension_urls
    ]
    if untrusted_urls:
        raise InitJsonFailure(
            "extension_url_trust_required",
            "External extension URLs require explicit trust before initialization.",
            {
                "extensions": untrusted_urls,
                "required_flag": "--trust-extension-urls",
            },
        )

    integration_defaulted = integration_key is None
    selected_integration = integration_key or _resolve_default_integration(warnings)
    integration = get_integration(selected_integration)
    if integration is None or selected_integration not in AGENT_CONFIG:
        raise InitJsonFailure(
            "invalid_integration",
            "The requested integration is not registered.",
            {
                "integration": selected_integration,
                "available": sorted(AGENT_CONFIG),
            },
        )

    parsed_options = _parse_integration_options(integration, integration_options)
    _validate_integration_mode_options(
        integration,
        parsed_options,
        integration_key=selected_integration,
        project_root=project_path,
    )
    if selected_integration == "generic":
        try:
            integration._resolve_commands_destination(
                project_path,
                parsed_options,
                {"raw_options": integration_options},
            )
        except ValueError as exc:
            raise _invalid_integration_options(
                "Integration options are invalid.",
                integration=selected_integration,
                reason=_single_line(exc),
            ) from exc

    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG[selected_integration]
        if agent_config.get("requires_cli") and not check_tool(selected_integration):
            raise InitJsonFailure(
                "missing_agent_tool",
                "The selected integration requires an agent tool that was not found.",
                {
                    "integration": selected_integration,
                    "install_url": agent_config.get("install_url"),
                    "override_flag": "--ignore-agent-tools",
                },
            )

    script_defaulted = script_type is None
    selected_script = script_type or ("ps" if os.name == "nt" else "sh")
    if selected_script not in SCRIPT_TYPE_CHOICES:
        raise InitJsonFailure(
            "invalid_script_type",
            "The requested script type is not supported.",
            {
                "script_type": selected_script,
                "available": sorted(SCRIPT_TYPE_CHOICES),
            },
        )

    return _InitPlan(
        project_name=resolved_name,
        project_path=project_path,
        operation=operation,
        target_owned=False,
        here=here,
        force=force,
        integration=integration,
        integration_defaulted=integration_defaulted,
        integration_options=parsed_options,
        raw_integration_options=integration_options,
        script_type=selected_script,
        script_defaulted=script_defaulted,
        ignore_agent_tools=ignore_agent_tools,
        preset=preset,
        extensions=requested_extensions,
        warnings=warnings,
    )


def _claim_new_target(plan: _InitPlan) -> None:
    if plan.operation != "created":
        return
    try:
        plan.project_path.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        if plan.project_path.is_dir():
            raise InitJsonFailure(
                "target_exists",
                "The target directory already exists; pass --force to merge into it.",
                {
                    "path": str(plan.project_path),
                    "concurrent_creation": True,
                },
            ) from exc
        raise InitJsonFailure(
            "target_not_directory",
            "The target exists but is not a directory.",
            {
                "path": str(plan.project_path),
                "concurrent_creation": True,
            },
        ) from exc
    except OSError as exc:
        raise InitJsonFailure(
            "target_unavailable",
            "The target directory could not be created.",
            {"path": str(plan.project_path), "reason": _single_line(exc)},
        ) from exc
    plan.target_owned = True


def _extension_spec_is_url(value: str) -> bool:
    from urllib.parse import urlparse

    try:
        return urlparse(value).scheme in {"http", "https"}
    except ValueError:
        return False


def _record_suppressed_output(
    warnings: list[dict[str, Any]],
    *,
    stdout: str,
    stderr: str,
) -> None:
    if stdout.strip():
        warnings.append(
            _warning(
                "suppressed_stdout",
                "Initialization produced human-readable output that was suppressed in JSON mode.",
                {"output": _single_line(stdout, limit=1000)},
            )
        )
    if stderr.strip():
        warnings.append(
            _warning(
                "suppressed_stderr",
                "Initialization produced diagnostic output that was suppressed in JSON mode.",
                {"output": _single_line(stderr, limit=1000)},
            )
        )


def _re_register_existing_artifacts(
    plan: _InitPlan,
    warnings: list[dict[str, Any]],
) -> None:
    if not plan.force:
        return
    try:
        from .extensions import ExtensionManager

        ExtensionManager(plan.project_path).register_enabled_extensions_for_agent(
            plan.integration.key,
            force=True,
        )
    except Exception as exc:  # noqa: BLE001 - re-registration is best-effort
        warnings.append(
            _warning(
                "extension_reregistration_failed",
                "The integration was updated, but installed extension artifacts could not be re-registered.",
                {
                    "integration": plan.integration.key,
                    "reason": _single_line(exc),
                },
            )
        )
    try:
        from .presets import PresetManager

        PresetManager(plan.project_path).register_enabled_presets_for_agent(
            plan.integration.key
        )
    except Exception as exc:  # noqa: BLE001 - re-registration is best-effort
        warnings.append(
            _warning(
                "preset_reregistration_failed",
                "The integration was updated, but installed preset artifacts could not be re-registered.",
                {
                    "integration": plan.integration.key,
                    "reason": _single_line(exc),
                },
            )
        )


def _install_shared_infrastructure(
    plan: _InitPlan,
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    from .integration_runtime import (
        invoke_prefix_for_integration,
    )
    from .shared_infra import install_shared_infra

    captured = io.StringIO()
    recording_console = Console(
        file=captured,
        force_terminal=False,
        color_system=None,
        width=240,
        highlight=False,
    )
    try:
        install_shared_infra(
            plan.project_path,
            plan.script_type,
            version=get_speckit_version(),
            core_pack=_locate_core_pack(),
            repo_root=_repo_root(),
            console=recording_console,
            force=plan.force,
            invoke_separator=plan.integration.effective_invoke_separator(
                plan.integration_options or None,
                project_root=plan.project_path,
            ),
            invoke_prefix=invoke_prefix_for_integration(
                plan.integration,
                plan.integration.key,
                plan.integration_options or None,
                plan.project_path,
            ),
        )
    except (OSError, ValueError) as exc:
        raise InitJsonFailure(
            "initialization_failed",
            "Failed to install shared infrastructure.",
            {
                "component": "shared_infrastructure",
                "reason": _single_line(exc),
            },
        ) from exc

    notice = _single_line(captured.getvalue(), limit=2000)
    if captured.getvalue().strip():
        warnings.append(
            _warning(
                "shared_infrastructure_notice",
                "Some shared infrastructure paths were preserved or skipped.",
                {"notice": notice},
            )
        )
    return {"status": "installed", "script_type": plan.script_type}


def _install_bundled_workflow(
    project_path: Path,
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        bundled_workflow = _locate_bundled_workflow("speckit")
        if bundled_workflow is None:
            outcome = {
                "id": "speckit",
                "status": "skipped",
                "reason": "bundled_workflow_not_found",
            }
            warnings.append(
                _warning(
                    "bundled_workflow_not_found",
                    "The bundled speckit workflow was not available.",
                    {"workflow": "speckit"},
                )
            )
            return outcome

        from .workflows.catalog import WorkflowRegistry
        from .workflows.engine import WorkflowDefinition

        registry = WorkflowRegistry(project_path)
        if registry.is_installed("speckit"):
            return {"id": "speckit", "status": "already_installed"}

        destination = project_path / ".specify" / "workflows" / "speckit"
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            bundled_workflow / "workflow.yml",
            destination / "workflow.yml",
        )
        definition = WorkflowDefinition.from_yaml(destination / "workflow.yml")
        registry.add(
            "speckit",
            {
                "name": definition.name,
                "version": definition.version,
                "description": definition.description,
                "source": "bundled",
            },
        )
        return {
            "id": "speckit",
            "status": "installed",
            "version": definition.version,
        }
    except Exception as exc:  # noqa: BLE001 - optional workflow failures continue
        warnings.append(
            _warning(
                "workflow_install_failed",
                "The project was initialized without the optional bundled workflow.",
                {"workflow": "speckit", "reason": _single_line(exc)},
            )
        )
        return {
            "id": "speckit",
            "status": "failed",
            "reason": _single_line(exc),
        }


def _install_optional_preset(
    project_path: Path,
    preset: str | None,
    warnings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if preset is None:
        return None

    try:
        from .presets import PresetCatalog, PresetManager

        manager = PresetManager(project_path)
        version = get_speckit_version()
        local_path = Path(preset).resolve()
        if local_path.is_dir() and (local_path / "preset.yml").exists():
            manifest = manager.install_from_directory(local_path, version)
            return {
                "requested": preset,
                "id": manifest.id,
                "status": "installed",
                "source": "local",
            }

        bundled_path = _locate_bundled_preset(preset)
        if bundled_path is not None:
            manifest = manager.install_from_directory(bundled_path, version)
            return {
                "requested": preset,
                "id": manifest.id,
                "status": "installed",
                "source": "bundled",
            }

        catalog = PresetCatalog(project_path)
        info = catalog.get_pack_info(preset)
        if not info:
            warnings.append(
                _warning(
                    "preset_not_found",
                    "The requested optional preset was not found and was skipped.",
                    {"preset": preset},
                )
            )
            return {
                "requested": preset,
                "status": "skipped",
                "reason": "not_found",
            }
        if info.get("bundled") and not info.get("download_url"):
            warnings.append(
                _warning(
                    "bundled_preset_not_found",
                    "The requested bundled preset was missing from the installed package.",
                    {"preset": preset},
                )
            )
            return {
                "requested": preset,
                "status": "failed",
                "reason": "bundled_preset_not_found",
            }

        zip_path: Path | None = None
        try:
            zip_path = catalog.download_pack(preset)
            manifest = manager.install_from_zip(
                zip_path,
                version,
                catalog_name=info.get("_catalog_name"),
            )
            return {
                "requested": preset,
                "id": manifest.id,
                "status": "installed",
                "source": "catalog",
            }
        finally:
            if zip_path is not None:
                try:
                    zip_path.unlink(missing_ok=True)
                except OSError as exc:
                    warnings.append(
                        _warning(
                            "preset_download_cleanup_failed",
                            "The preset was processed, but its temporary download could not be removed.",
                            {"preset": preset, "reason": _single_line(exc)},
                        )
                    )
    except Exception as exc:  # noqa: BLE001 - optional preset failures continue
        warnings.append(
            _warning(
                "preset_install_failed",
                "The project was initialized without the optional preset.",
                {"preset": preset, "reason": _single_line(exc)},
            )
        )
        return {
            "requested": preset,
            "status": "failed",
            "reason": _single_line(exc),
        }


def _install_requested_extensions(
    project_path: Path,
    extensions: list[str],
    warnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not extensions:
        return []

    from .command_init import _install_extension_during_init

    outcomes: list[dict[str, Any]] = []
    installed_any = False
    version = get_speckit_version()
    for extension in extensions:
        try:
            message = _install_extension_during_init(
                project_path,
                extension,
                version,
            )
            status = "already_installed" if message == "already installed" else "installed"
            outcomes.append(
                {
                    "requested": extension,
                    "status": status,
                    "message": message,
                }
            )
            installed_any = True
        except Exception as exc:  # noqa: BLE001 - optional extension failures continue
            reason = _single_line(exc)
            warnings.append(
                _warning(
                    "extension_install_failed",
                    "The project was initialized without a requested optional extension.",
                    {"extension": extension, "reason": reason},
                )
            )
            outcomes.append(
                {
                    "requested": extension,
                    "status": "failed",
                    "reason": reason,
                }
            )

    if installed_any:
        try:
            from .events import EventRefreshError, refresh_integration_events

            refresh_integration_events(project_path)
        except EventRefreshError as exc:
            warnings.append(
                _warning(
                    "extension_event_refresh_failed",
                    "Extensions were installed, but one or more integration event configurations could not be refreshed.",
                    {
                        "failures": [
                            {"integration": key, "reason": detail}
                            for key, detail in exc.failures
                        ]
                    },
                )
            )
    return outcomes


def _initialize_constitution(
    project_path: Path,
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    destination = project_path / ".specify" / "memory" / "constitution.md"
    if destination.exists():
        return {"status": "preserved", "path": str(destination)}
    try:
        from .presets import _materialize_constitution_template

        materialization = _materialize_constitution_template(
            project_path,
            destination,
        )
        if materialization is None:
            warnings.append(
                _warning(
                    "constitution_template_not_found",
                    "The constitution could not be initialized because no template was available.",
                    {"path": str(destination)},
                )
            )
            return {
                "status": "failed",
                "path": str(destination),
                "reason": "template_not_found",
            }
        return {
            "status": "created",
            "path": str(destination),
            "source": materialization,
        }
    except Exception as exc:  # noqa: BLE001 - constitution failure is non-fatal
        warnings.append(
            _warning(
                "constitution_initialization_failed",
                "The project was initialized, but its constitution could not be created.",
                {"path": str(destination), "reason": _single_line(exc)},
            )
        )
        return {
            "status": "failed",
            "path": str(destination),
            "reason": _single_line(exc),
        }


def _ensure_script_permissions(
    project_path: Path,
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    from . import ensure_executable_scripts

    tracker = StepTracker("init-json")
    ensure_executable_scripts(project_path, tracker=tracker)
    step = next((item for item in tracker.steps if item["key"] == "chmod"), None)
    if step is None:
        return {"status": "not_applicable"}
    if step["status"] == "error":
        warnings.append(
            _warning(
                "script_permission_update_failed",
                "Some executable script permissions could not be updated.",
                {"detail": step["detail"]},
            )
        )
        return {"status": "partial", "detail": step["detail"]}
    return {"status": "completed", "detail": step["detail"]}


def _next_steps(plan: _InitPlan) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    if not plan.here:
        steps.append(
            {
                "action": "change_directory",
                "path": str(plan.project_path),
            }
        )
    steps.extend(
        [
            {
                "action": "start_agent",
                "integration": plan.integration.key,
                "working_directory": str(plan.project_path),
            },
            {
                "action": "run_spec_kit",
                "commands": [
                    "constitution",
                    "specify",
                    "plan",
                    "tasks",
                    "implement",
                    "converge",
                ],
                "working_directory": str(plan.project_path),
            },
        ]
    )
    return steps


def _initialize_project(plan: _InitPlan) -> dict[str, Any]:
    from . import save_init_options
    from .events import resolve_events
    from .integration_runtime import with_integration_setting
    from .integration_state import write_integration_json
    from .integrations.manifest import IntegrationManifest

    warnings = list(plan.warnings)
    parsed_options = plan.integration_options or None
    try:
        manifest = IntegrationManifest(
            plan.integration.key,
            plan.project_path,
            version=get_speckit_version(),
        )
        events = resolve_events(
            plan.integration.key,
            plan.integration.config,
            plan.project_path,
            parsed_options,
        )
        plan.integration.setup(
            plan.project_path,
            manifest,
            parsed_options=parsed_options,
            script_type=plan.script_type,
            raw_options=plan.raw_integration_options,
            events=events,
        )
        manifest.save()
    except (OSError, ValueError) as exc:
        raise InitJsonFailure(
            "initialization_failed",
            "Failed to install the selected integration.",
            {
                "component": "integration",
                "integration": plan.integration.key,
                "reason": _single_line(exc),
            },
        ) from exc

    try:
        init_options: dict[str, Any] = {
            "ai": plan.integration.key,
            "integration": plan.integration.key,
            "here": plan.here,
            "script": plan.script_type,
            "feature_numbering": "sequential",
            "speckit_version": get_speckit_version(),
        }
        if plan.integration.is_skills_mode(
            parsed_options,
            project_root=plan.project_path,
        ):
            init_options["ai_skills"] = True
        save_init_options(plan.project_path, init_options)
    except (OSError, ValueError) as exc:
        raise InitJsonFailure(
            "initialization_failed",
            "Failed to save initialization state.",
            {
                "component": "init_options",
                "reason": _single_line(exc),
            },
        ) from exc

    try:
        _re_register_existing_artifacts(plan, warnings)

        settings = with_integration_setting(
            {},
            plan.integration.key,
            plan.integration,
            script_type=plan.script_type,
            raw_options=plan.raw_integration_options,
            parsed_options=parsed_options,
            project_root=plan.project_path,
        )
        write_integration_json(
            plan.project_path,
            version=get_speckit_version(),
            integration_key=plan.integration.key,
            installed_integrations=[plan.integration.key],
            settings=settings,
        )

        shared_infrastructure = _install_shared_infrastructure(plan, warnings)
    except (OSError, ValueError) as exc:
        raise InitJsonFailure(
            "initialization_failed",
            "Failed to configure project infrastructure.",
            {
                "component": "project_infrastructure",
                "reason": _single_line(exc),
            },
        ) from exc
    workflow = _install_bundled_workflow(plan.project_path, warnings)

    permissions = _ensure_script_permissions(plan.project_path, warnings)
    preset = _install_optional_preset(plan.project_path, plan.preset, warnings)
    extensions = _install_requested_extensions(
        plan.project_path,
        plan.extensions,
        warnings,
    )
    constitution = _initialize_constitution(plan.project_path, warnings)

    return {
        "project": {
            "name": plan.project_name,
            "path": str(plan.project_path),
            "operation": plan.operation,
        },
        "integration": {
            "key": plan.integration.key,
            "defaulted": plan.integration_defaulted,
            "status": "installed",
        },
        "script": {
            "type": plan.script_type,
            "defaulted": plan.script_defaulted,
        },
        "components": {
            "shared_infrastructure": shared_infrastructure,
            "workflow": workflow,
            "constitution": constitution,
            "script_permissions": permissions,
            "preset": preset,
            "extensions": extensions,
        },
        "warnings": warnings,
        "next_steps": _next_steps(plan),
    }


def _as_failure(exc: BaseException) -> InitJsonFailure:
    if isinstance(exc, InitJsonFailure):
        return exc
    if isinstance(exc, (OSError, ValueError, typer.Exit, SystemExit)):
        return InitJsonFailure(
            "initialization_failed",
            "Project initialization failed.",
            {"reason": _single_line(exc)},
        )
    return InitJsonFailure(
        "internal_error",
        "Project initialization failed because of an unexpected internal error.",
        {"exception_type": exc.__class__.__name__},
    )


def _rollback_new_target(
    plan: _InitPlan,
    failure: InitJsonFailure,
) -> InitJsonFailure:
    if not plan.target_owned or not plan.project_path.exists():
        return failure
    try:
        shutil.rmtree(plan.project_path)
    except OSError as cleanup_error:
        return InitJsonFailure(
            "rollback_failed",
            "Initialization failed and the newly created target could not be removed.",
            {
                "path": str(plan.project_path),
                "original_error": {
                    "code": failure.code,
                    "message": failure.message,
                    "details": failure.details,
                },
                "cleanup_error": {
                    "exception_type": cleanup_error.__class__.__name__,
                    "reason": _single_line(cleanup_error),
                },
            },
        )
    failure.details = {
        **failure.details,
        "rollback": {
            "status": "completed",
            "path": str(plan.project_path),
        },
    }
    return failure


def run_init_json(
    *,
    project_name: str | None,
    script_type: str | None,
    ignore_agent_tools: bool,
    here: bool,
    force: bool,
    preset: str | None,
    integration: str | None,
    integration_options: str | None,
    extensions: list[str] | None,
    trust_extension_urls: bool,
) -> None:
    """Execute ``specify init --json`` and emit exactly one JSON object."""
    try:
        plan = _build_plan(
            project_name=project_name,
            script_type=script_type,
            ignore_agent_tools=ignore_agent_tools,
            here=here,
            force=force,
            preset=preset,
            integration_key=integration,
            integration_options=integration_options,
            extensions=extensions,
            trust_extension_urls=trust_extension_urls,
        )
        _claim_new_target(plan)
    except Exception as exc:  # noqa: BLE001 - JSON boundary sanitizes all failures
        _emit_failure(_as_failure(exc))

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    try:
        with (
            console.capture() as console_capture,
            err_console.capture() as err_console_capture,
            redirect_stdout(stdout_capture),
            redirect_stderr(stderr_capture),
        ):
            result = _initialize_project(plan)
        _record_suppressed_output(
            result["warnings"],
            stdout=stdout_capture.getvalue() + console_capture.get(),
            stderr=stderr_capture.getvalue() + err_console_capture.get(),
        )
    except Exception as exc:  # noqa: BLE001 - JSON boundary sanitizes all failures
        _emit_failure(_rollback_new_target(plan, _as_failure(exc)))

    _emit(result)
