"""Unit tests for the adg CLI bridge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli import adg_bridge


def test_find_adg_uses_path(monkeypatch):
    monkeypatch.setattr(adg_bridge.shutil, "which", lambda _: "/usr/bin/adg")
    assert adg_bridge.find_adg() == "/usr/bin/adg"


def test_find_adg_missing_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(adg_bridge.shutil, "which", lambda _: None)
    # Point HOME at an empty dir so the nvm/homebrew fallbacks miss too.
    monkeypatch.setattr(adg_bridge.Path, "home", staticmethod(lambda: tmp_path))
    # Mock Path.is_file to simulate candidates missing as well.
    monkeypatch.setattr(adg_bridge.Path, "is_file", lambda self: False)
    assert adg_bridge.find_adg() is None


def test_require_adg_raises_when_missing(monkeypatch):
    monkeypatch.setattr(adg_bridge, "find_adg", lambda: None)
    with pytest.raises(adg_bridge.AdgNotFoundError) as exc:
        adg_bridge.require_adg()
    assert adg_bridge.ADG_INSTALL_HINT in str(exc.value)


def _fake_run(captured, output=""):
    def _run(adg, args):
        captured.append([adg, *args])
        return _run.output
    _run.output = output
    return _run


def test_has_global_plugin_uses_json(monkeypatch):
    captured: list[list[str]] = []
    runner = _fake_run(captured)
    runner.output = json.dumps(
        {"plugins": [{"name": "apple-skills"}, {"name": "speckit"}]}
    )
    monkeypatch.setattr(adg_bridge, "_run", runner)
    assert adg_bridge.has_global_plugin("speckit", adg="/x/adg") is True
    assert adg_bridge.has_global_plugin("nope", adg="/x/adg") is False
    # Prefers the stable --json contract.
    assert captured[0] == ["/x/adg", "plugins", "list", "--global", "--json"]


def test_has_global_plugin_text_fallback(monkeypatch):
    # Older adg: --json call fails; must fall back to text parsing.
    calls: list[list[str]] = []

    def _run(adg, args):
        calls.append([adg, *args])
        if "--json" in args:
            raise adg_bridge.AdgCommandError([adg, *args], 1, "Unknown option '--json'")
        return "design@1.2.0   …\nspeckit@0.11.4   …\n"

    monkeypatch.setattr(adg_bridge, "_run", _run)
    assert adg_bridge.has_global_plugin("speckit", adg="/x/adg") is True
    assert calls[0][-1] == "--json"  # tried json first
    assert calls[1] == ["/x/adg", "plugins", "list", "--global"]  # then text


def test_has_global_plugin_false_when_absent(monkeypatch):
    runner = _fake_run([])
    runner.output = json.dumps({"plugins": [{"name": "design"}]})
    monkeypatch.setattr(adg_bridge, "_run", runner)
    assert adg_bridge.has_global_plugin("speckit", adg="/x/adg") is False


def test_add_plugin_builds_global_args(monkeypatch, tmp_path):
    captured: list[list[str]] = []
    monkeypatch.setattr(adg_bridge, "_run", _fake_run(captured))
    adg_bridge.add_plugin(tmp_path, as_global=True, adg="/x/adg")
    assert captured[0] == [
        "/x/adg", "plugins", "add", str(tmp_path), "--all", "--target", "all", "--global",
    ]


def test_add_plugin_without_global(monkeypatch, tmp_path):
    captured: list[list[str]] = []
    monkeypatch.setattr(adg_bridge, "_run", _fake_run(captured))
    adg_bridge.add_plugin(tmp_path, as_global=False, adg="/x/adg")
    assert "--global" not in captured[0]


def test_link_builds_global_args(monkeypatch):
    captured: list[list[str]] = []
    monkeypatch.setattr(adg_bridge, "_run", _fake_run(captured))
    adg_bridge.link(["speckit"], target="all", as_global=True, adg="/x/adg")
    assert captured[0] == [
        "/x/adg", "plugins", "link", "--target", "all", "--global", "speckit",
    ]


def test_link_all_when_no_names(monkeypatch):
    captured: list[list[str]] = []
    monkeypatch.setattr(adg_bridge, "_run", _fake_run(captured))
    adg_bridge.link(target="claude", as_global=False, adg="/x/adg")
    assert captured[0] == ["/x/adg", "plugins", "link", "--target", "claude"]


def test_run_raises_on_nonzero(monkeypatch):
    class _Proc:
        returncode = 3
        stdout = "boom"
        stderr = "bad"

    monkeypatch.setattr(adg_bridge.subprocess, "run", lambda *a, **k: _Proc())
    with pytest.raises(adg_bridge.AdgCommandError):
        adg_bridge._run("/x/adg", ["plugins", "list"])
