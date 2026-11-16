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


_HOOK_BLOCK_HEADER = re.compile(
    r"^\s+\*\*(?:Optional|Automatic)(?: Pre-Hook| Hook)\*\*: \{extension\}$"
)
_FEATURE_DIR_LINE = "SPECKIT_FEATURE_DIR: {FEATURE_DIR}"
# The one hook event that runs before the feature directory exists.
_EMPTY_FEATURE_DIR_NOTE = "`SPECKIT_FEATURE_DIR` resolves to nothing"


@pytest.mark.parametrize("name", HOOK_TEMPLATES)
def test_every_hook_block_carries_the_feature_directory(name: str):
    """A hook block without SPECKIT_FEATURE_DIR leaves its consumer guessing.

    The block is the only surface a hook sees, so the value has to be in it,
    directly under the hook header and inside the same fence.
    """
    lines = (TEMPLATES_DIR / name).read_text(encoding="utf-8").splitlines()
    headers = [i for i, line in enumerate(lines) if _HOOK_BLOCK_HEADER.match(line)]
    # Guard: the before/after sites each render an optional and a mandatory block.
    assert len(headers) >= 4, f"{name}: found only {len(headers)} hook blocks"
    for index in headers:
        following = lines[index + 1].strip() if index + 1 < len(lines) else ""
        assert following == _FEATURE_DIR_LINE, (
            f"{name}: hook block at line {index + 1} does not carry "
            f"{_FEATURE_DIR_LINE!r} as its second line, found {following!r}"
        )


def test_specify_says_the_feature_directory_is_empty_before_it_exists():
    """before_specify runs before the directory exists, so the value is empty.

    The note has to sit in the pre-hook section, ahead of the first hook block,
    or an agent reads it as applying to the post-hook blocks that do carry a
    real path.
    """
    lines = (TEMPLATES_DIR / "specify.md").read_text(encoding="utf-8").splitlines()
    notes = [i for i, line in enumerate(lines) if _EMPTY_FEATURE_DIR_NOTE in line]
    headers = [i for i, line in enumerate(lines) if _HOOK_BLOCK_HEADER.match(line)]
    assert notes, "specify.md does not say SPECKIT_FEATURE_DIR is empty before the folder exists"
    assert notes[0] < headers[0], (
        "specify.md states the empty case after the first hook block, where it "
        "reads as an exception to the blocks that carry a real path"
    )


def test_converge_post_hooks_are_mandatory():
    """after_converge is the only completion signal converge produces.

    Without the mandatory framing the other commands carry, an agent may report
    the handoff and end the command before the hooks run.
    """
    text = (TEMPLATES_DIR / "converge.md").read_text(encoding="utf-8")
    assert "MUST complete this section before reporting converge as finished" in text, (
        "converge.md does not make the after_converge hooks mandatory"
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
