"""CLI adapter for ``specify self check``."""

from __future__ import annotations

from . import self_app


@self_app.command("check")
def self_check() -> None:
    """Check whether a newer specify-cli release is available. Read-only.

    This command only checks for updates; it does not modify your installation.
    Use `specify self upgrade` to actually perform the upgrade once you've seen
    the result here, or `specify self upgrade --dry-run` to preview the
    installer command without running it.
    """
    from .._version import (
        _MANUAL_TAG_PLACEHOLDER,
        _fetch_latest_release_tag,
        _get_installed_version,
        _is_newer,
        _manual_source_spec,
        _manual_tag_or_placeholder,
        _normalize_tag,
        console,
    )

    installed = _get_installed_version()
    tag, failure_reason = _fetch_latest_release_tag()

    if tag is None:
        assert failure_reason is not None
        console.print(f"Installed: {installed}")
        console.print(f"[yellow]Could not check latest release:[/yellow] {failure_reason}")
        return

    manual_tag = _manual_tag_or_placeholder(tag)
    latest_display = manual_tag or _MANUAL_TAG_PLACEHOLDER

    if manual_tag is None:
        if installed == "unknown":
            console.print("Current version could not be determined.")
            console.print(f"Latest release: {latest_display}")
        else:
            console.print(f"Installed: {installed}")
            console.print(f"Latest release: {latest_display}")
        console.print("[yellow]Could not validate latest release tag from GitHub.[/yellow]")
        console.print("\nManual fallback:")
        console.print(
            f"  uv tool install specify-cli --force --from {_manual_source_spec(manual_tag)}"
        )
        console.print(f"  pipx install --force {_manual_source_spec(manual_tag)}")
        return

    if installed == "unknown":
        console.print("Current version could not be determined.")
        console.print(f"Latest release: {latest_display}")
        console.print("\nManual fallback:")
        console.print(
            f"  uv tool install specify-cli --force --from {_manual_source_spec(manual_tag)}"
        )
        console.print(f"  pipx install --force {_manual_source_spec(manual_tag)}")
        console.print("\nIf this install can still be detected:")
        console.print("  specify self upgrade")
        return

    latest_normalized = _normalize_tag(manual_tag)
    if _is_newer(latest_normalized, installed):
        console.print(f"[green]Update available:[/green] {installed} → {latest_display}")
        console.print("\nTo upgrade:")
        console.print("  specify self upgrade")
        console.print("\nManual fallback:")
        console.print(
            f"  uv tool install specify-cli --force --from {_manual_source_spec(manual_tag)}"
        )
        console.print(f"  pipx install --force {_manual_source_spec(manual_tag)}")
        return

    console.print(f"[green]Up to date:[/green] {installed}")
