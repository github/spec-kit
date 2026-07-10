"""Regression tests for SKILL.md frontmatter quoting (#3391).

The skills setup path builds SKILL.md frontmatter by hand with
double-quoted values. A double-quoted YAML scalar cannot carry a raw
newline (the parser folds it to a space) or a control character (the
reader rejects the document), so descriptions taken from template
frontmatter must be escaped by the YAML emitter.
"""

from pathlib import Path

import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations.base import yaml_quote
from specify_cli.integrations.manifest import IntegrationManifest

MULTILINE = "first line\nsecond line\n"
CONTROL = "ding\aling"

HOSTILE_TEMPLATE = """---
description: |
  first line
  second line
---

Body of the command.
"""

CONTROL_TEMPLATE = """---
description: "ding\\aling"
---

Body of the command.
"""


def _parse_frontmatter(skill_file: Path) -> dict:
    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    return yaml.safe_load(content.split("---", 2)[1])


def _fake_templates(tmp_path: Path, body: str) -> Path:
    templates = tmp_path / "templates"
    templates.mkdir(exist_ok=True)
    (templates / "plan.md").write_text(body, encoding="utf-8")
    return templates


class TestYamlQuote:
    def test_simple_value_keeps_plain_double_quoted_form(self):
        assert yaml_quote("speckit-plan") == '"speckit-plan"'
        assert yaml_quote('say "hi"') == '"say \\"hi\\""'
        assert yaml_quote("back\\slash") == '"back\\\\slash"'

    def test_multiline_value_round_trips(self):
        quoted = yaml_quote(MULTILINE)
        assert "\n" not in quoted
        assert yaml.safe_load(quoted) == MULTILINE

    def test_control_character_round_trips(self):
        quoted = yaml_quote(CONTROL)
        assert "\a" not in quoted
        assert yaml.safe_load(quoted) == CONTROL


class TestSkillFrontmatterQuoting:
    def _generate(self, tmp_path, monkeypatch, template: str) -> Path:
        integration = get_integration("agy")
        monkeypatch.setattr(
            integration,
            "shared_commands_dir",
            lambda: _fake_templates(tmp_path, template),
        )
        manifest = IntegrationManifest("agy", tmp_path)
        created = integration.setup(tmp_path, manifest)
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) == 1
        return skill_files[0]

    def test_multiline_description_survives(self, tmp_path, monkeypatch):
        skill_file = self._generate(tmp_path, monkeypatch, HOSTILE_TEMPLATE)
        fm = _parse_frontmatter(skill_file)
        assert fm["description"] == MULTILINE

    def test_control_character_description_parses(self, tmp_path, monkeypatch):
        skill_file = self._generate(tmp_path, monkeypatch, CONTROL_TEMPLATE)
        fm = _parse_frontmatter(skill_file)
        assert fm["description"] == CONTROL


class TestHermesSkillFrontmatterQuoting:
    def test_multiline_description_survives(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir(exist_ok=True)
        monkeypatch.setattr(Path, "home", lambda: home)

        integration = get_integration("hermes")
        monkeypatch.setattr(
            integration,
            "shared_commands_dir",
            lambda: _fake_templates(tmp_path, HOSTILE_TEMPLATE),
        )
        manifest = IntegrationManifest("hermes", tmp_path)
        created = integration.setup(tmp_path, manifest)
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) == 1

        fm = _parse_frontmatter(skill_files[0])
        assert fm["description"] == MULTILINE
