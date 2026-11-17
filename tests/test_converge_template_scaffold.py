"""The fork retires converge; fixes flow through test findings and taskscode."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_retired_commands_are_not_delivered():
    for name in ("tasks", "implement", "converge", "checklist"):
        assert not (ROOT / "templates/commands" / (name + ".md")).exists()


def test_fix_loop_has_explicit_ownership():
    text = (ROOT / "templates/commands/test.md").read_text(encoding="utf-8")
    assert "__SPECKIT_COMMAND_TASKSCODE__" in text
    assert "__SPECKIT_COMMAND_IMPCODE__" in text
    assert "Do not modify production source" in text
