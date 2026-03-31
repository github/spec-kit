"""
Tests for the /speckit.fix feature (templates/commands/fix.md and templates/fix-template.md).

Invariants verified
───────────────────
  fix.md — command template
  • Valid YAML frontmatter (parseable by yaml.safe_load)
  • Has non-empty 'description' field
  • Has 'scripts.sh' referencing check-prerequisites.sh
  • Has 'scripts.ps' referencing check-prerequisites.ps1
  • Contains the $ARGUMENTS placeholder
  • Body references all 9 Spec Kit workflow commands
  • Contains the mandatory 4-point diagnosis block (ROOT CAUSE, SPEC IMPACT,
    NEW FEATURE, SCOPE)
  • Contains the escalation guard ("NEW FEATURE = YES")
  • Contains all 5 execution phases
  • References fix.md as the output log file
  • No stray double-brace placeholders leaked from TOML format

  fix-template.md — log scaffold
  • File exists in templates/
  • Contains the FIX-NNN · date · title header pattern
  • Contains all 4 metadata table rows (Error type, Detected in, Root cause,
    Spec impact)
  • Contains the Decisions, Files modified, Invariants established, and
    Edge cases not covered sections
  • Uses the INVARIANT: and EDGE CASE: prefixes
  • Contains the Spec Kit follow-up commands checklist
  • References all four follow-up commands (/speckit.clarify, /speckit.plan,
    /speckit.analyze, /speckit.taskstoissues)
  • Newest-first ordering comment is present

  bundle inclusion
  • 'fix' stem is returned by _get_source_template_stems()
  • pyproject.toml declares fix-template.md in the data-files section
"""

import re
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIX_CMD = _REPO_ROOT / "templates" / "commands" / "fix.md"
_FIX_TMPL = _REPO_ROOT / "templates" / "fix-template.md"
_PYPROJECT = _REPO_ROOT / "pyproject.toml"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) for a Markdown file with YAML frontmatter.

    Returns ({}, text) if no frontmatter delimiters are found.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm_text = text[3:end].strip()
    body = text[end + 3:].strip()
    parsed = yaml.safe_load(fm_text) or {}
    return parsed, body


# ---------------------------------------------------------------------------
# 1. fix.md — YAML frontmatter
# ---------------------------------------------------------------------------

class TestFixCommandFrontmatter:
    """Validate the YAML frontmatter block in templates/commands/fix.md."""

    @pytest.fixture(scope="class")
    def content(self) -> str:
        return _FIX_CMD.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def frontmatter(self, content) -> dict:
        fm, _ = _parse_frontmatter(content)
        return fm

    def test_file_exists(self):
        assert _FIX_CMD.is_file(), "templates/commands/fix.md is missing"

    def test_frontmatter_is_parseable(self, content):
        """File must open with --- and contain valid YAML."""
        assert content.startswith("---"), "fix.md must start with a YAML frontmatter block (---)"
        fm, _ = _parse_frontmatter(content)
        assert isinstance(fm, dict), "Frontmatter could not be parsed as a YAML mapping"

    def test_has_nonempty_description(self, frontmatter):
        assert "description" in frontmatter, "Frontmatter missing 'description' key"
        assert frontmatter["description"], "'description' must not be empty"

    def test_has_scripts_sh(self, frontmatter):
        scripts = frontmatter.get("scripts", {}) or {}
        assert "sh" in scripts, "Frontmatter missing 'scripts.sh'"
        assert "check-prerequisites.sh" in scripts["sh"], (
            "'scripts.sh' must reference check-prerequisites.sh"
        )

    def test_has_scripts_ps(self, frontmatter):
        scripts = frontmatter.get("scripts", {}) or {}
        assert "ps" in scripts, "Frontmatter missing 'scripts.ps'"
        assert "check-prerequisites.ps1" in scripts["ps"], (
            "'scripts.ps' must reference check-prerequisites.ps1"
        )

    def test_scripts_sh_includes_json_flag(self, frontmatter):
        """check-prerequisites must be invoked with --json so output is machine-readable."""
        sh_cmd = (frontmatter.get("scripts") or {}).get("sh", "")
        assert "--json" in sh_cmd, "'scripts.sh' must include --json flag"

    def test_scripts_ps_includes_json_flag(self, frontmatter):
        ps_cmd = (frontmatter.get("scripts") or {}).get("ps", "")
        assert "-Json" in ps_cmd, "'scripts.ps' must include -Json flag"


# ---------------------------------------------------------------------------
# 2. fix.md — body content
# ---------------------------------------------------------------------------

class TestFixCommandBody:
    """Validate the substantive content in the body of fix.md."""

    @pytest.fixture(scope="class")
    def body(self) -> str:
        content = _FIX_CMD.read_text(encoding="utf-8")
        _, b = _parse_frontmatter(content)
        return b

    def test_contains_arguments_placeholder(self, body):
        assert "$ARGUMENTS" in body, "fix.md must contain $ARGUMENTS placeholder"

    def test_references_all_workflow_commands(self, body):
        """The command map must list every Spec Kit command."""
        expected_commands = [
            "speckit.constitution",
            "speckit.specify",
            "speckit.clarify",
            "speckit.plan",
            "speckit.analyze",
            "speckit.tasks",
            "speckit.implement",
            "speckit.taskstoissues",
            "speckit.fix",
        ]
        for cmd in expected_commands:
            assert cmd in body, f"fix.md must reference /{cmd} in the command map"

    def test_contains_four_point_diagnosis(self, body):
        """Phase 2 must instruct the agent to produce the 4-point diagnosis."""
        required_labels = ["ROOT CAUSE", "SPEC IMPACT", "NEW FEATURE", "SCOPE"]
        for label in required_labels:
            assert label in body, f"fix.md diagnosis block must contain '{label}'"

    def test_contains_escalation_guard(self, body):
        """If NEW FEATURE = YES the agent must stop and escalate."""
        assert "NEW FEATURE = YES" in body, (
            "fix.md must contain escalation guard 'NEW FEATURE = YES'"
        )

    def test_five_phases_present(self, body):
        """fix.md must describe all 5 execution phases."""
        for phase_num in range(1, 6):
            assert f"Phase {phase_num}" in body, (
                f"fix.md is missing 'Phase {phase_num}'"
            )

    def test_references_fix_log_file(self, body):
        """The command must direct output to the fix.md log file."""
        assert "fix.md" in body, "fix.md command body must reference the fix.md log file"

    def test_script_placeholder_present(self, body):
        """{SCRIPT} placeholder must appear so scaffold rewrites it to the real path."""
        assert "{SCRIPT}" in body, "fix.md must contain the {SCRIPT} placeholder"

    def test_no_toml_double_brace_leak(self, body):
        """Markdown files must not contain TOML-style {{args}} placeholders."""
        assert "{{args}}" not in body, (
            "fix.md must not contain TOML-style {{args}} — use $ARGUMENTS instead"
        )

    def test_constitution_is_read_only(self, body):
        """The constitution.md must be declared read-only (agents must not modify it)."""
        assert "read-only" in body.lower(), (
            "fix.md must mark constitution.md as read-only"
        )


# ---------------------------------------------------------------------------
# 2b. fix.md — triage and layered diagnosis (smart error localization)
# ---------------------------------------------------------------------------

class TestFixCommandTriage:
    """Validate the triage step and layered diagnosis added for token-efficient diagnosis."""

    @pytest.fixture(scope="class")
    def body(self) -> str:
        content = _FIX_CMD.read_text(encoding="utf-8")
        _, b = _parse_frontmatter(content)
        return b

    def test_triage_block_present(self, body):
        """Phase 1.2 must instruct the agent to produce a TRIAGE block before opening files."""
        assert "TRIAGE" in body, (
            "fix.md must contain a TRIAGE block in Phase 1.2 for zero-file-I/O error classification"
        )

    def test_triage_has_layer_field(self, body):
        """TRIAGE block must include a Role field to identify the functional layer."""
        assert "Role" in body, (
            "fix.md TRIAGE block must include a 'Role' field (functional role in the project chain)"
        )

    def test_triage_has_read_set_field(self, body):
        """TRIAGE block must include a Read set field listing the minimal files to open."""
        assert "Read set" in body, (
            "fix.md TRIAGE block must include a 'Read set' field (minimal files to open)"
        )

    def test_data_path_chain_present(self, body):
        """Functional role names covering all major project types must be documented."""
        for role in ("data-access", "business-logic", "entry-point", "guard", "routing", "validation"):
            assert role in body, (
                f"fix.md must document functional role '{role}' in the Data Path Quick Reference"
            )

    def test_architecture_pattern_detection(self, body):
        """The command must instruct the agent to infer the project's own chain before mapping errors."""
        # At least 3 distinct architecture patterns must be documented
        patterns = ["Django", "Express", "GraphQL", "CLI", "Serverless", "Event-driven",
                    "Clean Architecture", "NestJS", "Laravel", "React", "Vue"]
        found = [p for p in patterns if p in body]
        assert len(found) >= 3, (
            f"fix.md must document at least 3 architecture patterns for chain inference — found: {found}"
        )

    def test_constitution_never_read_proactively(self, body):
        """constitution.md must be documented as never read proactively."""
        assert "never" in body.lower() and "proactively" in body.lower(), (
            "fix.md must state that constitution.md is never read proactively"
        )

    def test_chain_impact_field_in_diagnosis(self, body):
        """The layered diagnosis must include a CHAIN IMPACT field."""
        assert "CHAIN IMPACT" in body, (
            "fix.md diagnosis block must contain 'CHAIN IMPACT' to flag error propagation"
        )

    def test_layer_field_in_diagnosis(self, body):
        """The layered diagnosis must include a LAYER field."""
        assert "LAYER" in body, (
            "fix.md diagnosis block must contain 'LAYER' to identify the data-path layer"
        )

    def test_third_party_guard_present(self, body):
        """Phase 1.2 must instruct the agent to skip third-party frames in the stack trace."""
        for dep_dir in ("node_modules", "site-packages", "vendor"):
            assert dep_dir in body, (
                f"fix.md must contain a third-party stack trace guard for '{dep_dir}' in Phase 1.2"
            )

    def test_scope_creep_guard_present(self, body):
        """Phase 2 must stop execution when SCOPE exceeds 5 files (refactoring, not a fix)."""
        assert "5 files" in body, (
            "fix.md must contain a scope creep guard that stops at > 5 files in Phase 2"
        )

    def test_validation_test_in_phase_4(self, body):
        """Phase 4 must require the agent to write a concrete VALIDATION block."""
        assert "VALIDATION" in body, (
            "fix.md Phase 4 must contain a mandatory 'VALIDATION' block before Phase 5"
        )

    def test_coverage_gap_flag_present(self, body):
        """When no automated test covers the scenario the agent must flag COVERAGE GAP."""
        assert "COVERAGE GAP" in body, (
            "fix.md must contain a 'COVERAGE GAP' flag for fixes without automated tests"
        )


# ---------------------------------------------------------------------------
# 2c. fix.md — Phase 0 pre-flight checks
# ---------------------------------------------------------------------------

class TestFixCommandPhaseZero:
    """Validate the Phase 0 pre-flight checks for token-efficient short-circuit workflows."""

    @pytest.fixture(scope="class")
    def body(self) -> str:
        content = _FIX_CMD.read_text(encoding="utf-8")
        _, b = _parse_frontmatter(content)
        return b

    def test_phase_zero_present(self, body):
        assert "Phase 0" in body, "fix.md must contain a 'Phase 0' pre-flight section"

    def test_confidence_threshold_present(self, body):
        """0.1 — ambiguous input must trigger exactly one targeted question, not a guess."""
        assert "Confidence threshold" in body or "0.1" in body, (
            "fix.md Phase 0 must contain a confidence threshold check (0.1)"
        )

    def test_multi_error_handling_present(self, body):
        """0.2 — multiple errors in one input must be ranked and fixed in priority order."""
        assert "Multi-error" in body or "0.2" in body, (
            "fix.md Phase 0 must contain multi-error input handling (0.2)"
        )

    def test_recurrent_error_check_present(self, body):
        """0.3 — existing fix.md must be scanned for previous entries before diagnosing."""
        assert "Recurrent error" in body or "0.3" in body, (
            "fix.md Phase 0 must contain a recurrent error check (0.3)"
        )

    def test_trivial_fast_path_present(self, body):
        """0.4 — trivially diagnosable errors must bypass Phases 1–2 entirely."""
        assert "fast path" in body.lower() or "0.4" in body, (
            "fix.md Phase 0 must contain a trivial fast path (0.4)"
        )

    def test_trivial_fast_path_covers_syntax_error(self, body):
        assert "SyntaxError" in body, (
            "fix.md trivial fast path must enumerate SyntaxError as a direct-fix case"
        )

    def test_trivial_fast_path_covers_module_not_found(self, body):
        assert "ModuleNotFoundError" in body, (
            "fix.md trivial fast path must enumerate ModuleNotFoundError as a direct-fix case"
        )

    def test_recurrent_flag_in_diagnosis(self, body):
        """The RECURRENT flag must be documented for agents to use in Phase 2."""
        assert "RECURRENT" in body, (
            "fix.md must document a RECURRENT flag for errors that recur after a previous fix"
        )


# ---------------------------------------------------------------------------
# 3. fix-template.md — log scaffold
# ---------------------------------------------------------------------------

class TestFixTemplate:
    """Validate the structure and required sections of templates/fix-template.md."""

    @pytest.fixture(scope="class")
    def content(self) -> str:
        return _FIX_TMPL.read_text(encoding="utf-8")

    def test_file_exists(self):
        assert _FIX_TMPL.is_file(), "templates/fix-template.md is missing"

    def test_fix_entry_header_pattern(self, content):
        """Must contain at least one FIX-NNN header with date and title."""
        assert re.search(r"##\s+FIX-\d{3}\s*·", content), (
            "fix-template.md must contain a FIX-NNN · date · title header"
        )

    def test_metadata_table_has_error_type(self, content):
        assert "Error type" in content, "fix-template.md metadata table must have 'Error type' row"

    def test_metadata_table_has_detected_in(self, content):
        assert "Detected in" in content, "fix-template.md must have 'Detected in' row"

    def test_metadata_table_has_root_cause(self, content):
        assert "Root cause" in content, "fix-template.md must have 'Root cause' row"

    def test_metadata_table_has_spec_impact(self, content):
        assert "Spec impact" in content, "fix-template.md must have 'Spec impact' row"

    def test_decisions_section_present(self, content):
        assert "### Decisions" in content, "fix-template.md must contain '### Decisions' section"

    def test_files_modified_section_present(self, content):
        assert "### Files modified" in content, (
            "fix-template.md must contain '### Files modified' section"
        )

    def test_invariants_section_present(self, content):
        assert "### Invariants established" in content, (
            "fix-template.md must contain '### Invariants established' section"
        )

    def test_invariant_prefix_present(self, content):
        assert "INVARIANT:" in content, (
            "fix-template.md must use 'INVARIANT:' prefix for invariants"
        )

    def test_edge_cases_section_present(self, content):
        assert "### Edge cases not covered" in content, (
            "fix-template.md must contain '### Edge cases not covered' section"
        )

    def test_edge_case_prefix_present(self, content):
        assert "EDGE CASE:" in content, (
            "fix-template.md must use 'EDGE CASE:' prefix"
        )

    def test_followup_commands_section_present(self, content):
        assert "### Spec Kit follow-up commands" in content, (
            "fix-template.md must contain '### Spec Kit follow-up commands' section"
        )

    def test_followup_references_clarify(self, content):
        assert "/speckit.clarify" in content, (
            "fix-template.md must reference /speckit.clarify in follow-up"
        )

    def test_followup_references_plan(self, content):
        assert "/speckit.plan" in content, (
            "fix-template.md must reference /speckit.plan in follow-up"
        )

    def test_followup_references_analyze(self, content):
        assert "/speckit.analyze" in content, (
            "fix-template.md must reference /speckit.analyze in follow-up"
        )

    def test_followup_references_taskstoissues(self, content):
        assert "/speckit.taskstoissues" in content, (
            "fix-template.md must reference /speckit.taskstoissues in follow-up"
        )

    def test_newest_first_comment_present(self, content):
        """Template must remind agents to prepend newest entries."""
        assert "newest first" in content.lower(), (
            "fix-template.md must document the newest-first ordering convention"
        )

    def test_error_origin_block_present(self, content):
        """Each entry must have a verbatim error capture block."""
        assert "Error origin" in content, (
            "fix-template.md must contain an 'Error origin' block for verbatim error capture"
        )

    def test_location_comment_present(self, content):
        """Template must document where the file lives (specs/<feature>/fix.md)."""
        assert "fix.md" in content and "specs/" in content, (
            "fix-template.md must document its target location (specs/<feature>/fix.md)"
        )


# ---------------------------------------------------------------------------
# 4. Bundle inclusion
# ---------------------------------------------------------------------------

class TestFixCommandBundleInclusion:
    """Verify fix.md is wired into packaging and scaffold discovery."""

    def test_fix_stem_in_source_template_stems(self):
        """_get_source_template_stems() must include 'fix' so scaffold copies it."""
        from specify_cli import _locate_core_pack

        core = _locate_core_pack()
        if core and (core / "commands").is_dir():
            commands_dir = core / "commands"
        else:
            commands_dir = _REPO_ROOT / "templates" / "commands"

        stems = sorted(p.stem for p in commands_dir.glob("*.md"))
        assert "fix" in stems, (
            f"'fix' not found in command template stems: {stems}"
        )

    def test_fix_template_in_pyproject_data_files(self):
        """pyproject.toml must declare fix-template.md as a data file for wheel packaging."""
        pyproject_text = _PYPROJECT.read_text(encoding="utf-8")
        assert "fix-template.md" in pyproject_text, (
            "pyproject.toml must include fix-template.md in data-files so it is bundled in the wheel"
        )

    def test_fix_command_in_commands_directory(self):
        """templates/commands/ must contain fix.md so the scaffold loop picks it up."""
        commands_dir = _REPO_ROOT / "templates" / "commands"
        fix_cmd = commands_dir / "fix.md"
        assert fix_cmd.is_file(), (
            "templates/commands/fix.md must exist for scaffold loop inclusion"
        )
