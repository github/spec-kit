"""Command templates must not tell the agent to skip hook checking silently.

Every core command template reads ``.specify/extensions.yml`` before and after
its main work, looking for ``hooks.before_*`` / ``hooks.after_*`` entries.  A
manifest that could not be parsed used to be treated exactly like a manifest
with no hooks: the agent was told to "skip hook checking silently and continue
normally".  A mandatory hook (``optional: false``, the kind the bundled ``git``
extension registers) could therefore be disabled by a single malformed line,
and nothing would say so.

These tests pin the replacement wording: an unreadable manifest is reported to
the user (the parser error, and the fact that no hooks were checked) before
the command continues.  They read the templates as text on purpose: the
behaviour lives in the prompt, so the prompt is what must be checked.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates" / "commands"

_HOOK_KEY = re.compile(r"`hooks\.(before|after)_[a-z_]+`")
_PARSE_FAILURE_LINE = re.compile(
    r"^.*If the YAML cannot be parsed or is invalid.*$", re.MULTILINE
)
_SILENT = "skip hook checking silently"
# Every clause of the replacement instruction, so that dropping any one of
# them from the templates fails the test: the manifest could not be read, the
# parser error is shown, no hooks were checked, mandatory hooks are named, and
# the command still continues afterwards.
_REPORTED = (
    "could not be read",
    "include the parser error",
    "no hooks were checked",
    "including any mandatory (`optional: false`) hooks",
    "then continue",
)

HOOK_TEMPLATES = sorted(
    p.name
    for p in TEMPLATES_DIR.glob("*.md")
    if _HOOK_KEY.search(p.read_text(encoding="utf-8"))
)


def test_hook_templates_discovered():
    # Guard: the glob must find the templates that read extensions.yml,
    # otherwise the parametrized tests below would pass by vacuity.
    assert {"specify.md", "plan.md", "tasks.md", "implement.md"} <= set(
        HOOK_TEMPLATES
    )


@pytest.mark.parametrize("name", HOOK_TEMPLATES)
def test_unreadable_manifest_is_never_skipped_silently(name: str):
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    assert _SILENT not in text, (
        f"{name}: an unreadable .specify/extensions.yml may still be skipped "
        "silently, which disables mandatory hooks without saying so"
    )


@pytest.mark.parametrize("name", HOOK_TEMPLATES)
def test_every_parse_failure_line_reports_before_continuing(name: str):
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    lines = _PARSE_FAILURE_LINE.findall(text)
    # One line for the before-hook check, one for the after-hook check.
    assert len(lines) >= 2, (
        f"{name}: expected a parse-failure instruction at both hook sites, "
        f"found {len(lines)}"
    )
    for line in lines:
        for phrase in _REPORTED:
            assert phrase in line, (
                f"{name}: parse-failure instruction does not tell the user "
                f"{phrase!r}: {line.strip()}"
            )
