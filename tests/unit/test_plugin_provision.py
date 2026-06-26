"""Unit tests for init.py plugin-mode provisioning (author/consume + link)."""
from __future__ import annotations

from pathlib import Path

import specify_cli.adg_bridge as adg_bridge
import specify_cli.commands.init as init_mod
import specify_cli.plugin_export as plugin_export
from specify_cli.commands.init import _maybe_install_adg, _provision_plugin_skills


class _Tracker:
    def __init__(self):
        self.completed = []

    def complete(self, name, msg):
        self.completed.append((name, msg))


def _stub_common(monkeypatch, calls):
    monkeypatch.setattr(adg_bridge, "require_adg", lambda: "/x/adg")
    monkeypatch.setattr(
        adg_bridge, "add_plugin",
        lambda *a, **k: calls.append("add") or "",
    )
    monkeypatch.setattr(
        adg_bridge, "link",
        lambda *a, **k: calls.append("link") or "",
    )
    monkeypatch.setattr(plugin_export, "build_plugin", lambda *a, **k: calls.append("build"))


def test_author_branch_adds_then_links(monkeypatch):
    calls: list[str] = []
    _stub_common(monkeypatch, calls)
    monkeypatch.setattr(adg_bridge, "has_global_plugin", lambda **k: False)
    tracker = _Tracker()

    _provision_plugin_skills("sh", tracker)

    # Author must build, add, THEN link (link after add is the P0 fix).
    assert calls == ["build", "add", "link"]
    assert "authored" in tracker.completed[-1][1]


def test_consume_branch_still_links(monkeypatch):
    calls: list[str] = []
    _stub_common(monkeypatch, calls)
    monkeypatch.setattr(adg_bridge, "has_global_plugin", lambda **k: True)
    tracker = _Tracker()

    _provision_plugin_skills("sh", tracker)

    # Consume must NOT re-author, but must still link (self-heal).
    assert calls == ["link"]
    assert "consumed" in tracker.completed[-1][1]


def test_degrade_path_writes_out_dir_no_adg(monkeypatch, tmp_path):
    calls: list[str] = []
    # adg functions must NOT be called in degrade mode; build must.
    monkeypatch.setattr(
        adg_bridge, "add_plugin", lambda *a, **k: calls.append("add"))
    monkeypatch.setattr(adg_bridge, "link", lambda *a, **k: calls.append("link"))
    monkeypatch.setattr(
        plugin_export, "build_plugin", lambda *a, **k: calls.append("build"))
    tracker = _Tracker()

    out = tmp_path / "speckit-plugin"
    degraded = _provision_plugin_skills(
        "sh", tracker, out_dir=out, adg_available=False
    )

    assert degraded is True
    assert calls == ["build"]  # no add/link without adg
    assert "adg plugins add" in tracker.completed[-1][1]


def test_author_to_out_dir_persists(monkeypatch, tmp_path):
    calls: list[str] = []
    monkeypatch.setattr(adg_bridge, "require_adg", lambda: "/x/adg")
    monkeypatch.setattr(adg_bridge, "has_global_plugin", lambda **k: False)
    monkeypatch.setattr(
        adg_bridge, "add_plugin",
        lambda d, **k: calls.append(("add", Path(d))) or "")
    monkeypatch.setattr(adg_bridge, "link", lambda *a, **k: calls.append("link") or "")
    monkeypatch.setattr(plugin_export, "build_plugin", lambda d, *a, **k: calls.append(("build", Path(d))))
    tracker = _Tracker()

    out = tmp_path / "speckit-plugin"
    degraded = _provision_plugin_skills(
        "sh", tracker, out_dir=out, adg_available=True
    )

    assert degraded is False
    # built and added at the persistent out_dir (not a temp dir)
    assert ("build", out.resolve()) in calls
    assert ("add", out.resolve()) in calls
    assert "authored" in tracker.completed[-1][1]


def test_maybe_install_adg_noninteractive_declines(monkeypatch):
    # Non-interactive without --yes must decline early (no install attempt).
    monkeypatch.setattr(init_mod, "_stdin_is_interactive", lambda: False)
    assert _maybe_install_adg(yes=False) is False


def test_link_failure_is_non_fatal(monkeypatch):
    calls: list[str] = []
    _stub_common(monkeypatch, calls)
    monkeypatch.setattr(adg_bridge, "has_global_plugin", lambda **k: True)

    def _boom(*a, **k):
        raise adg_bridge.AdgCommandError(["adg", "plugins", "link"], 1, "nope")

    monkeypatch.setattr(adg_bridge, "link", _boom)
    tracker = _Tracker()

    _provision_plugin_skills("sh", tracker)  # must not raise

    assert "link failed" in tracker.completed[-1][1]
