"""Static content tests for the Smart Constitution Bootstrap changes.

Verifies that `templates/commands/constitution.md` and
`presets/lean/commands/speckit.constitution.md` contain the correct
new vs existing solution detection logic, bootstrap questions, and
safety rails introduced by the Smart Constitution Bootstrap feature.

These are pure static-analysis tests — they read the markdown files and
assert key strings are present, following the pattern established in
`test_cursor_frontmatter.py`.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MAIN_TEMPLATE = REPO_ROOT / "templates" / "commands" / "constitution.md"
LEAN_PRESET_COMMAND = REPO_ROOT / "presets" / "lean" / "commands" / "speckit.constitution.md"


class TestMainConstitutionCommandStructure:
    """Verify the main constitution command template has the bootstrap detection flow."""

    def _content(self) -> str:
        return MAIN_TEMPLATE.read_text(encoding="utf-8")

    def test_step_0_detection_section_exists(self):
        """Step 0 must exist to trigger solution-state detection before any constitution work."""
        assert "## Step 0" in self._content()

    def test_detection_rule_checks_constitution_file(self):
        """Detection rule must check whether the constitution file exists with filled content."""
        content = self._content()
        assert "Detection rule" in content
        assert ".specify/memory/constitution.md" in content
        assert "unfilled" in content or "[PROJECT_NAME]" in content

    def test_detection_distinguishes_initialized_repo_from_truly_new(self):
        """Missing working copies in initialized repos must route to Path A, not Path B."""
        content = self._content()
        assert ".specify/templates/constitution-template.md" in content
        assert "initialized existing repo with a missing working copy" in content
        assert "copy the template to `.specify/memory/constitution.md`, then proceed to **Path A**" in content

    def test_detection_is_automatic_no_user_prompt(self):
        """Detection must be fully automatic — the command must not ask the user."""
        content = self._content()
        # Explicit instruction not to ask the user
        assert "do not ask the user" in content.lower()
        # The old interactive prompt reply syntax must not appear
        assert "`new`, `existing`" not in content

    def test_path_a_existing_solution_section_exists(self):
        """Path A (existing solution) section must be present."""
        assert "Path A" in self._content()

    def test_path_b_new_solution_section_exists(self):
        """Path B (new solution bootstrap) section must be present."""
        assert "Path B" in self._content()

    def test_path_a_preserves_existing_update_flow(self):
        """Path A must still contain the full existing-solution constitution update logic."""
        content = self._content()
        # Core steps from the original existing-solution flow
        assert "CONSTITUTION_VERSION" in content
        assert "RATIFICATION_DATE" in content
        assert "LAST_AMENDED_DATE" in content
        assert "Sync Impact Report" in content
        assert "semantic versioning" in content

    def test_path_b_collects_ten_bootstrap_questions(self):
        """Path B must ask all 10 required minimum-durable-input questions."""
        content = self._content()
        questions = [
            "solution_name",
            "solution_purpose",
            "solution_type",
            "primary_stack",
            "core_dependencies",
            "security_constraints",
            "data_rules",
            "quality_rules",
            "boundary_rules",
            "out_of_scope",
        ]
        for q in questions:
            assert q in content, f"Bootstrap question '{q}' missing from Path B"

    def test_path_b_questions_include_options_or_examples(self):
        """Bootstrap questions must include options or examples to reduce ambiguity."""
        content = self._content()
        # solution_type must offer structured options
        assert "Windows desktop app" in content
        assert "Web app" in content
        assert "REST API" in content
        assert "CLI tool" in content
        # primary_stack must offer technology options
        assert "C# / .NET" in content
        assert "Python" in content
        assert "TypeScript / Node.js" in content
        # security_constraints must offer auth options
        assert "OAuth 2.0" in content
        assert "RBAC" in content
        # data_rules must offer storage options
        assert "SQL Server only" in content
        assert "parameterized queries" in content
        # quality_rules must offer quality options
        assert "Unit tests" in content
        assert "Structured logging" in content
        # out_of_scope must offer exclusion options
        assert "Feature-specific requirements" in content
        assert "standard exclusions" in content

    def test_path_b_questions_show_concrete_examples(self):
        """Bootstrap questions must show concrete examples where applicable."""
        content = self._content()
        # solution_name should have name examples
        assert "InventoryTracker" in content or "PayrollEngine" in content
        # core_dependencies should have service examples
        assert "Active Directory" in content
        # boundary_rules should have boundary examples
        assert "shared" in content.lower() or "public API" in content

    def test_path_b_normalizes_answers_into_categories(self):
        """Path B must normalize answers into constitution-friendly categories."""
        content = self._content()
        assert "Scope" in content
        assert "Technical context" in content
        assert "Security and data handling" in content
        assert "Quality and engineering standards" in content
        assert "Exclusions" in content

    def test_path_b_generates_ten_constitution_sections(self):
        """Path B must produce a constitution with all required sections."""
        content = self._content()
        required_sections = [
            "Scope",
            "Purpose",
            "Solution Boundary",
            "Architecture",
            "Security",
            "Data Access",
            "Error Handling",
            "Quality",
            "Change Governance",
            "Explicit Exclusions",
        ]
        for section in required_sections:
            assert section in content, f"Required constitution section '{section}' missing from Path B"

    def test_path_b_includes_documentation_boundaries_rule(self):
        """Path B constitution must include the Documentation Boundaries rule."""
        content = self._content()
        assert "Documentation Boundaries" in content
        assert "constitution" in content.lower()
        assert "Specifications" in content
        assert "Implementation plans" in content or "Implementation plan" in content
        assert "Tasks" in content

    def test_path_b_outputs_version_1_0_0_for_new_solutions(self):
        """New solutions must start at version 1.0.0."""
        assert "1.0.0" in self._content()

    def test_path_b_requires_concrete_iso_dates_in_footer(self):
        """Path B must require concrete ISO dates instead of leaving placeholders in the footer."""
        content = self._content()
        assert "current date in ISO format `YYYY-MM-DD`" in content
        assert "Do **not** leave literal placeholders such as `<TODAY>`" in content
        assert "**Ratified**: YYYY-MM-DD | **Last Amended**: YYYY-MM-DD" in content

    def test_path_b_safety_rails_forbid_functional_requirements(self):
        """Safety rails must explicitly forbid functional requirements in the constitution."""
        content = self._content()
        assert "Safety rails" in content or "safety rails" in content
        # Key prohibitions
        assert "functional requirement" in content.lower() or "raw functional requirements" in content.lower()
        assert "feature-specific" in content.lower()
        assert "pseudo-code" in content.lower() or "pseudocode" in content.lower()

    def test_path_b_handles_unknown_answers_gracefully(self):
        """Path B must document behavior when user answers 'unknown'."""
        content = self._content()
        assert "`unknown`" in content
        # Must not invent specifics
        assert "safe, minimal defaults" in content or "generic and durable" in content

    def test_no_ambiguous_answer_handling(self):
        """Detection is automatic — there is no ambiguous-answer follow-up prompt."""
        content = self._content().lower()
        assert "if the answer is ambiguous" not in content
        assert "ask a single follow-up" not in content

    def test_path_b_writes_to_memory_constitution(self):
        """Path B must write the generated constitution to the correct path."""
        content = self._content()
        assert ".specify/memory/constitution.md" in content

    def test_description_frontmatter_reflects_bootstrap_behavior(self):
        """The frontmatter description must mention new vs existing detection."""
        content = self._content()
        # The description should be in the first few lines
        lines = content.split("\n")
        frontmatter_block = "\n".join(lines[:10])
        assert "new" in frontmatter_block.lower() and "existing" in frontmatter_block.lower()

    def test_extension_hooks_are_preserved(self):
        """Pre/post extension hook checks must still be present (regression guard)."""
        content = self._content()
        assert "before_constitution" in content
        assert "after_constitution" in content

    def test_no_standalone_prompt_file(self):
        """The standalone bootstrap prompt file must be removed — logic now lives in the command."""
        standalone_lowercase = REPO_ROOT / ".github" / "prompts" / "smart-constitution-bootstrap-prompt.md"
        standalone_uppercase = REPO_ROOT / ".github" / "Prompts" / "smart-constitution-bootstrap-prompt.md"
        assert not standalone_lowercase.exists() and not standalone_uppercase.exists(), (
            "Standalone smart-constitution-bootstrap-prompt.md should be deleted from "
            ".github/prompts/ or .github/Prompts/; the logic now lives in "
            "templates/commands/constitution.md"
        )


class TestLeanPresetConstitutionCommand:
    """Verify the lean preset command has the same detection structure."""

    def _content(self) -> str:
        return LEAN_PRESET_COMMAND.read_text(encoding="utf-8")

    def test_lean_preset_command_exists(self):
        """The lean preset constitution command file must exist."""
        assert LEAN_PRESET_COMMAND.exists()

    def test_step_0_detection_exists_in_lean(self):
        """Lean preset must also have Step 0 detection logic."""
        assert "Step 0" in self._content()

    def test_lean_detection_is_automatic_no_user_prompt(self):
        """Lean preset detection must be fully automatic — no user prompt."""
        content = self._content()
        assert "do not ask the user" in content.lower()
        assert "`new`, `existing`" not in content

    def test_lean_detection_rule_checks_constitution_file(self):
        """Lean preset detection must check constitution file existence and whether content is still placeholders."""
        content = self._content()
        assert ".specify/memory/constitution.md" in content
        assert "unfilled" in content or "[PROJECT_NAME]" in content

    def test_lean_detection_distinguishes_initialized_repo_from_truly_new(self):
        """Lean preset must route initialized repos with a missing working copy to Path A."""
        content = self._content()
        assert ".specify/templates/constitution-template.md" in content
        assert "initialized existing repo with a missing working copy" in content
        assert "copy the template to `.specify/memory/constitution.md`, then follow Path A below" in content

    def test_path_a_exists_in_lean(self):
        """Lean preset must have a Path A for existing solutions."""
        assert "Path A" in self._content()

    def test_path_b_exists_in_lean(self):
        """Lean preset must have a Path B for new solutions."""
        assert "Path B" in self._content()

    def test_lean_bootstrap_questions_present(self):
        """Lean preset Path B must include the core bootstrap questions."""
        content = self._content()
        for question_key in [
            "solution_name",
            "solution_purpose",
            "primary_stack",
            "security_constraints",
            "data_rules",
        ]:
            assert question_key in content, f"Bootstrap question '{question_key}' missing from lean preset"

    def test_lean_bootstrap_questions_include_options(self):
        """Lean preset bootstrap questions must include options to reduce ambiguity."""
        content = self._content()
        # solution_type must offer options
        assert "Windows desktop app" in content
        assert "REST API" in content
        # primary_stack must offer technology options
        assert "C# / .NET" in content
        assert "Python" in content
        # security_constraints must offer auth options
        assert "OAuth 2.0" in content
        # data_rules must offer storage options
        assert "SQL Server" in content
        # quality_rules must offer quality options
        assert "Unit tests" in content

    def test_lean_path_b_constitution_sections(self):
        """Lean preset Path B must list the required constitution sections."""
        content = self._content()
        for section in ["Scope", "Purpose", "Security", "Quality"]:
            assert section in content, f"Section '{section}' missing from lean preset Path B"

    def test_lean_path_b_no_feature_specs(self):
        """Lean preset must state that the constitution must not contain feature specs."""
        content = self._content()
        assert "feature spec" in content.lower() or "feature-specific" in content.lower()

    def test_lean_description_updated(self):
        """Lean preset description must reflect the new detection behavior."""
        content = self._content()
        lines = content.split("\n")
        frontmatter_block = "\n".join(lines[:10])
        assert "new" in frontmatter_block.lower() and "existing" in frontmatter_block.lower()

    def test_lean_writes_to_memory_constitution(self):
        """Lean preset Path B must write to `.specify/memory/constitution.md`."""
        assert ".specify/memory/constitution.md" in self._content()
