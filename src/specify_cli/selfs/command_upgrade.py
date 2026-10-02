"""CLI adapter for ``specify self upgrade``."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from . import self_app


@self_app.command("upgrade")
def self_upgrade(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the preview (method, current, target, installer argv) and "
        "exit 0 without launching the installer subprocess.",
    ),
    tag: str | None = typer.Option(
        None,
        "--tag",
        help="Pin the target version (vX.Y.Z\\[suffix]). Without --tag, the "
        "latest stable release is resolved via GitHub Releases.",
    ),
) -> None:
    """Upgrade specify-cli to the latest release (or a pinned --tag).

    Bare invocation executes immediately with no confirmation prompt, matching
    pip install -U / uv tool upgrade / npm update conventions. Use --dry-run
    to preview without mutating anything. See `specify self check` for the
    non-destructive read-only counterpart.

    Detection classifies the runtime into uv-tool / pipx / uvx (ephemeral) /
    source-checkout / unsupported. Only uv-tool and pipx are upgraded
    automatically; the other three paths print path-specific guidance and
    exit 0.

    Exit codes:
      0      success or no-op-success (already on latest, --dry-run, or
             non-upgradable path with guidance shown)
      1      target-tag resolution failure or --tag regex validation failure
      2      verification mismatch when the installer exited 0 but
             `specify --version` does not resolve to the target tag; if the
             installer itself exits 2, that installer failure code is
             propagated verbatim
      3      installer binary not found on PATH, or resolved installer path is
             missing / non-executable
      124    internal installer timeout when SPECIFY_UPGRADE_TIMEOUT_SECS is set,
             or a real installer exit code 124 propagated verbatim; scripts
             should treat 124 as ambiguous and inspect the failure message
      other  installer exit code propagated verbatim

    Environment variables:
      SPECIFY_UPGRADE_TIMEOUT_SECS  Optional integer/float seconds. Caps how
        long the installer subprocess may run. Unset (default) means no
        timeout — interrupt with Ctrl+C if the installer hangs.
    """
    from .._version import (
        _FAILURE_INSTALLER_FAILED,
        _FAILURE_INSTALLER_INVALID,
        _FAILURE_INSTALLER_MISSING,
        _FAILURE_INSTALLER_TIMEOUT,
        _FAILURE_TARGET_TAG_UNPARSEABLE,
        _FAILURE_VERIFICATION_MISMATCH,
        _InstallMethod,
        _InstallerResultKind,
        _build_upgrade_plan,
        _canonicalize_version_text,
        _emit_failure,
        _emit_guidance,
        _installer_binary_name,
        _method_label,
        _parse_version_text,
        _render_argv,
        _run_installer,
        _validate_tag,
        _verify_upgrade,
        console,
    )

    if tag is not None:
        try:
            tag = _validate_tag(tag)
        except typer.BadParameter as exc:
            console.print(_escape_markup(str(exc)), soft_wrap=True)
            raise typer.Exit(1) from exc

    plan, failure_reason = _build_upgrade_plan(target_tag_override=tag)

    if plan is None:
        if failure_reason is None:
            raise RuntimeError(
                "internal contract violation: _build_upgrade_plan returned (None, None)"
            )
        _emit_failure(failure_reason)
        raise typer.Exit(1)

    if failure_reason is not None:
        _emit_failure(failure_reason, plan=plan)
        raise typer.Exit(1)

    if dry_run:
        if plan.method in (
            _InstallMethod.UVX_EPHEMERAL,
            _InstallMethod.SOURCE_CHECKOUT,
            _InstallMethod.UNSUPPORTED,
        ):
            _emit_guidance(plan.method, plan.target_tag)
            raise typer.Exit(0)
        console.print("Dry run — no changes will be made.")
        for line in plan.preview_summary.splitlines():
            console.print(line)
        raise typer.Exit(0)

    if plan.method in (
        _InstallMethod.UVX_EPHEMERAL,
        _InstallMethod.SOURCE_CHECKOUT,
        _InstallMethod.UNSUPPORTED,
    ):
        _emit_guidance(plan.method, plan.target_tag)
        raise typer.Exit(0)

    if plan.installer_argv is None:
        _emit_failure(
            _FAILURE_INSTALLER_MISSING,
            plan=plan,
            installer_name=_installer_binary_name(plan.method),
        )
        raise typer.Exit(3)

    if plan.target_tag is None:
        raise RuntimeError("Upgrade target tag is required for upgradable install methods")
    target_tag = plan.target_tag
    target_version = _parse_version_text(target_tag)
    if target_version is None:
        _emit_failure(_FAILURE_TARGET_TAG_UNPARSEABLE, plan=plan)
        raise typer.Exit(1)
    if plan.current_version != "unknown":
        current_version = _parse_version_text(plan.current_version)
        if tag is None and current_version is not None and not (
            target_version > current_version
        ):
            if target_version == current_version:
                console.print(f"Already on latest release: {target_tag}")
            else:
                console.print(f"Already on latest release or newer: {plan.current_version}")
            raise typer.Exit(0)
        if (
            tag is not None
            and current_version is not None
            and target_version == current_version
        ):
            console.print(f"Already on requested release: {target_tag}")
            raise typer.Exit(0)

    installed_version = _parse_version_text(plan.current_version)
    verb = (
        "Downgrading"
        if tag is not None
        and installed_version is not None
        and target_version < installed_version
        else "Upgrading"
    )
    argv_str = _render_argv(plan.installer_argv) if plan.installer_argv else ""
    console.print(
        f"{verb} specify-cli {plan.current_version} → {plan.target_tag} "
        f"via {_method_label(plan.method)}: {argv_str}",
        soft_wrap=True,
    )

    installer_result = _run_installer(plan)
    installer_name = plan.installer_argv[0] if plan.installer_argv else None

    if installer_result.kind == _InstallerResultKind.MISSING:
        _emit_failure(_FAILURE_INSTALLER_MISSING, plan=plan, installer_name=installer_name)
        raise typer.Exit(3)

    if installer_result.kind == _InstallerResultKind.INVALID:
        _emit_failure(_FAILURE_INSTALLER_INVALID, plan=plan, installer_name=installer_name)
        raise typer.Exit(3)

    if installer_result.kind == _InstallerResultKind.TIMEOUT:
        _emit_failure(_FAILURE_INSTALLER_TIMEOUT, plan=plan)
        raise typer.Exit(124)

    if (
        installer_result.kind != _InstallerResultKind.EXITED
        or installer_result.returncode is None
    ):
        raise RuntimeError(f"Unknown installer result: {installer_result!r}")

    if installer_result.returncode != 0:
        _emit_failure(
            _FAILURE_INSTALLER_FAILED,
            plan=plan,
            installer_exit=installer_result.returncode,
        )
        raise typer.Exit(installer_result.returncode)

    verified = _verify_upgrade(plan)
    verified_version = _parse_version_text(verified) if verified is not None else None
    if verified_version is None or verified_version != target_version:
        _emit_failure(
            _FAILURE_VERIFICATION_MISMATCH,
            plan=plan,
            verified_version=verified,
        )
        raise typer.Exit(2)

    pre_upgrade_display = _canonicalize_version_text(plan.pre_upgrade_snapshot)
    verified_display = _canonicalize_version_text(verified)
    console.print(
        f"Upgraded specify-cli: {pre_upgrade_display} → {verified_display}",
        soft_wrap=True,
    )
