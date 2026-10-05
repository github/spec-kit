"""Machine-readable adapter for the existing ``specify init`` execution path."""

from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, NoReturn

import typer
from typer.core import TyperCommand
from typer.exceptions import TyperException

from ._agent_config import (
    AGENT_CONFIG,
    DEFAULT_INIT_INTEGRATION,
    DEFAULT_INIT_INTEGRATION_ENV_VAR,
    SCRIPT_TYPE_CHOICES,
)
from ._console import console, err_console
from ._utils import check_tool


@dataclass
class InitJsonFailure(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class InitJsonCommand(TyperCommand):
    """Keep JSON-mode parser failures machine-readable."""

    def make_context(self, info_name, args, parent=None, **extra):
        end_of_options = args.index("--") if "--" in args else len(args)
        json_output = "--json" in args[:end_of_options]
        try:
            return super().make_context(info_name, args, parent=parent, **extra)
        except TyperException as exc:
            if json_output:
                _emit_failure(
                    InitJsonFailure(
                        "invalid_arguments",
                        _single_line(exc),
                    )
                )
            raise


def _single_line(value: object, *, limit: int = 500) -> str:
    text = " ".join(str(value).split())
    return (text or value.__class__.__name__)[:limit]


def _emit(value: dict[str, Any], *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    binary_stream = getattr(stream, "buffer", None)
    if binary_stream is None:
        stream.write(payload.decode("utf-8"))
        stream.flush()
        return
    binary_stream.write(payload)
    binary_stream.flush()


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


def _extension_url(value: str) -> bool:
    from urllib.parse import urlparse

    try:
        return urlparse(value).scheme in {"http", "https"}
    except ValueError:
        return False


def _preflight(
    *,
    project_name: str | None,
    script_type: str | None,
    ignore_agent_tools: bool,
    here: bool,
    force: bool,
    integration_key: str | None,
    integration_options: str | None,
    extensions: list[str] | None,
    trust_extension_urls: bool,
) -> dict[str, Any]:
    from ._download_security import is_https_or_localhost_http
    from .command_init import (
        _InitIntegrationOptionsError,
        _validate_init_integration_options,
    )
    from .integrations import get_integration
    from .integrations._commands import _parse_integration_options

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

    project_path = Path.cwd() if here else Path(project_name or "").resolve()
    existed_before = project_path.exists()
    if existed_before:
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
    unsupported_urls = [
        extension
        for extension in requested_extensions
        if _extension_url(extension)
        and not is_https_or_localhost_http(extension)
    ]
    if unsupported_urls:
        raise InitJsonFailure(
            "invalid_extension_url",
            "Extension URLs must use HTTPS; HTTP is allowed only for localhost.",
            {"extensions": unsupported_urls},
        )
    untrusted_urls = [
        extension
        for extension in requested_extensions
        if _extension_url(extension) and not trust_extension_urls
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

    warnings: list[dict[str, Any]] = []
    integration_defaulted = not integration_key
    if integration_key:
        selected_integration = integration_key
    else:
        override = (os.environ.get(DEFAULT_INIT_INTEGRATION_ENV_VAR) or "").strip()
        if override and override not in AGENT_CONFIG:
            warnings.append(
                {
                    "code": "invalid_default_integration",
                    "message": (
                        "The configured default integration was not recognized; "
                        "the built-in default was used."
                    ),
                    "details": {
                        "environment_variable": DEFAULT_INIT_INTEGRATION_ENV_VAR,
                        "value": override,
                        "default": DEFAULT_INIT_INTEGRATION,
                    },
                }
            )
            selected_integration = DEFAULT_INIT_INTEGRATION
        else:
            selected_integration = override or DEFAULT_INIT_INTEGRATION

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
    if selected_integration == "generic" and not integration_options:
        raise InitJsonFailure(
            "invalid_integration_options",
            "The generic integration requires --commands-dir.",
            {"integration": "generic"},
        )

    try:
        parsed_options = (
            _parse_integration_options(integration, integration_options)
            if integration_options
            else {}
        )
        integration.is_skills_mode(
            parsed_options or None,
            project_root=project_path,
        )
        _validate_init_integration_options(
            project_path,
            integration,
            parsed_options or None,
            integration_options,
        )
    except _InitIntegrationOptionsError as exc:
        raise InitJsonFailure(
            "invalid_integration_options",
            exc.message,
            {
                "integration": selected_integration,
                **exc.details,
            },
        ) from exc
    except (ValueError, typer.Exit) as exc:
        raise InitJsonFailure(
            "invalid_integration_options",
            "Integration options are invalid.",
            {
                "integration": selected_integration,
                "reason": _single_line(exc),
            },
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

    script_defaulted = not script_type
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

    return {
        "project_path": project_path,
        "integration_defaulted": integration_defaulted,
        "script_defaulted": script_defaulted,
        "warnings": warnings,
    }


def run_init_json(
    *,
    execute: Callable[[], dict[str, Any]],
    project_name: str | None,
    script_type: str | None,
    ignore_agent_tools: bool,
    here: bool,
    force: bool,
    integration: str | None,
    integration_options: str | None,
    extensions: list[str] | None,
    trust_extension_urls: bool,
) -> None:
    """Invoke the regular initializer and replace only its output rendering."""
    from .command_init import (
        _InitRollbackError,
        _InitTargetClaimError,
        _init_failure_context,
        _init_json_mode,
        _init_rollback_context,
    )

    result: dict[str, Any] | None = None
    failure: InitJsonFailure | None = None
    context: dict[str, Any] | None = None
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    failure_token = _init_failure_context.set(None)
    rollback_token = _init_rollback_context.set(None)
    json_mode_token = _init_json_mode.set(True)
    try:
        with (
            redirect_stdout(stdout_capture),
            redirect_stderr(stderr_capture),
            console.capture(),
            err_console.capture(),
        ):
            context = _preflight(
                project_name=project_name,
                script_type=script_type,
                ignore_agent_tools=ignore_agent_tools,
                here=here,
                force=force,
                integration_key=integration,
                integration_options=integration_options,
                extensions=extensions,
                trust_extension_urls=trust_extension_urls,
            )
            result = execute()
    except InitJsonFailure as exc:
        failure = exc
    except (typer.Exit, SystemExit) as exc:
        internal_failure = _init_failure_context.get()
        rollback = _init_rollback_context.get()
        project_path = context["project_path"] if context else None
        if isinstance(internal_failure, _InitTargetClaimError):
            failure = InitJsonFailure(
                internal_failure.code,
                internal_failure.message,
                internal_failure.details,
            )
        elif isinstance(internal_failure, _InitRollbackError):
            failure = InitJsonFailure(
                "rollback_failed",
                "Initialization failed and the newly created target could not be removed.",
                {
                    "path": str(project_path),
                    "original_error": {
                        "code": "initialization_failed",
                        "message": "Project initialization failed.",
                        "details": {},
                    },
                    "cleanup_error": internal_failure.details,
                },
            )
        elif internal_failure is not None and not isinstance(
            internal_failure,
            (OSError, ValueError),
        ):
            failure = InitJsonFailure(
                "internal_error",
                "Project initialization failed because of an unexpected internal error.",
                {"exception_type": internal_failure.__class__.__name__},
            )
        else:
            details: dict[str, Any] = {}
            if rollback is not None and rollback.get("status") == "completed":
                details["rollback"] = rollback
            failure = InitJsonFailure(
                "initialization_failed",
                "Project initialization failed.",
                details,
            )
        exit_code = (
            exc.exit_code
            if isinstance(exc, typer.Exit)
            else exc.code
            if isinstance(exc.code, int)
            else 1
        )
        if exit_code == 0:
            failure = InitJsonFailure(
                "initialization_failed",
                "Project initialization did not complete.",
            )
    except Exception as exc:  # noqa: BLE001 - sanitize the JSON boundary
        failure = InitJsonFailure(
            "internal_error",
            "Project initialization failed because of an unexpected internal error.",
            {"exception_type": exc.__class__.__name__},
        )
    finally:
        _init_failure_context.reset(failure_token)
        _init_rollback_context.reset(rollback_token)
        _init_json_mode.reset(json_mode_token)

    if failure is not None:
        _emit_failure(failure)
    if result is None or context is None:
        _emit_failure(
            InitJsonFailure(
                "internal_error",
                "Project initialization did not produce a result.",
            )
        )

    result["integration"]["defaulted"] = context["integration_defaulted"]
    result["script"]["defaulted"] = context["script_defaulted"]
    result["warnings"] = [*context["warnings"], *result["warnings"]]
    _emit(result)
