"""Tests for the /delta command and the Vision & Direction section.

The delta command itself is markdown executed by an LLM; these tests cover the
*scaffolding* contracts that the rest of the system relies on:

- delta is a recognized core command (registered alongside specify/plan/tasks).
- The delta template file ships under templates/commands/ and respects its
  read-mostly contract (single canonical write target).
- The constitution template carries the Vision & Direction section with the
  subsections the /constitution command is instructed to populate.
- The plan template carries a Vision Alignment Check gate that references the
  Vision section.
"""

from pathlib import Path

from specify_cli import SKILL_DESCRIPTIONS
from specify_cli.extensions import _FALLBACK_CORE_COMMAND_NAMES
from specify_cli.integrations.claude import ARGUMENT_HINTS

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "templates"


class TestDeltaCommandRegistration:
    """The /delta command must be wired into every place core commands are listed."""

    def test_delta_in_skill_descriptions(self):
        assert "delta" in SKILL_DESCRIPTIONS
        # Description should mention the two things /delta uniquely promises:
        # Vision and a recommendation/next-feature direction.
        desc = SKILL_DESCRIPTIONS["delta"].lower()
        assert "vision" in desc
        assert "next" in desc or "recommend" in desc

    def test_delta_in_core_command_fallback(self):
        """Extensions must not be allowed to shadow /delta."""
        assert "delta" in _FALLBACK_CORE_COMMAND_NAMES

    def test_delta_has_claude_argument_hint(self):
        assert "delta" in ARGUMENT_HINTS
        assert ARGUMENT_HINTS["delta"].strip() != ""

    def test_delta_template_file_exists(self):
        assert (TEMPLATES / "commands" / "delta.md").is_file()


class TestDeltaTemplateContract:
    """Read-only audit of templates/commands/delta.md's behavior contract."""

    def setup_method(self):
        self.content = (TEMPLATES / "commands" / "delta.md").read_text()

    def test_writes_to_canonical_memory_path(self):
        # The report has exactly one canonical write location.
        assert ".specify/memory/delta.md" in self.content

    def test_does_not_create_spec_directories(self):
        # /delta is a recommender, not a creator. It must explicitly disclaim
        # spec/branch creation so future edits don't drift into that territory.
        lowered = self.content.lower()
        assert "do not create spec" in lowered or "do **not** create spec" in lowered

    def test_has_frontmatter_and_handoff_to_specify(self):
        # YAML frontmatter present.
        assert self.content.startswith("---")
        # Recommends the natural next command.
        assert "speckit.specify" in self.content

    def test_references_constitution_and_specs(self):
        # Both inputs must be named in the instructions.
        assert ".specify/memory/constitution.md" in self.content
        assert "specs/" in self.content


class TestConstitutionVisionSection:
    """The constitution template must expose the Vision & Direction structure."""

    def setup_method(self):
        self.content = (TEMPLATES / "constitution-template.md").read_text()

    def test_vision_section_present(self):
        assert "## Vision & Direction" in self.content

    def test_vision_above_core_principles(self):
        vision_idx = self.content.index("## Vision & Direction")
        principles_idx = self.content.index("## Core Principles")
        assert vision_idx < principles_idx, (
            "Vision & Direction must precede Core Principles so it reads as the "
            "fixed objective above the principles that govern HOW."
        )

    def test_required_subsections_present(self):
        for heading in (
            "### North Star",
            "### Target Users & Value",
            "### Long-Term Objectives",
            "### Non-Goals",
        ):
            assert heading in self.content, f"missing subsection: {heading}"


class TestPlanTemplateVisionGate:
    """The plan template must gate on Vision alignment, not just Constitution."""

    def setup_method(self):
        self.content = (TEMPLATES / "plan-template.md").read_text()

    def test_vision_alignment_gate_present(self):
        assert "## Vision Alignment Check" in self.content

    def test_vision_gate_after_constitution_gate(self):
        # Order matters: Constitution Check stays first (existing contract),
        # Vision Alignment Check is the new sibling gate that follows it.
        const_idx = self.content.index("## Constitution Check")
        vision_idx = self.content.index("## Vision Alignment Check")
        assert const_idx < vision_idx

    def test_vision_gate_references_delta_and_constitution_commands(self):
        # Failure path should route the user to /delta or /constitution.
        assert "__SPECKIT_COMMAND_DELTA__" in self.content
        assert "__SPECKIT_COMMAND_CONSTITUTION__" in self.content
