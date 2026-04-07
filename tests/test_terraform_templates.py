"""
Unit tests for Terraform template files.

Tests cover:
- All expected template files exist under templates/iac/terraform/
- Command files have valid YAML frontmatter with required fields
- Command files contain expected $ARGUMENTS placeholder
- Frontmatter description fields are non-empty
- Frontmatter argument-hint fields are present
- coding-style-template.md contains expected Terraform placeholders
- terraform_engineer.md agent persona has correct frontmatter
"""

import re
from pathlib import Path

import pytest


# Locate the templates/iac/terraform directory relative to this test file.
REPO_ROOT = Path(__file__).parent.parent
TERRAFORM_TEMPLATES_DIR = REPO_ROOT / "templates" / "iac" / "terraform"


def _read(path: Path) -> str:
    """Read a file and return its text content."""
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(content: str) -> dict:
    """
    Extract key-value pairs from a simple YAML frontmatter block (between --- markers).
    Returns a dict of top-level scalar string fields only (no nested parsing).
    """
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value:
                result[key] = value
    return result


class TestTerraformTemplateDirectoryStructure:
    """Verify expected directories and files exist."""

    def test_terraform_template_root_exists(self):
        """templates/iac/terraform/ directory must exist."""
        assert TERRAFORM_TEMPLATES_DIR.is_dir(), (
            f"Expected directory not found: {TERRAFORM_TEMPLATES_DIR}"
        )

    def test_commands_directory_exists(self):
        """templates/iac/terraform/commands/ must exist."""
        assert (TERRAFORM_TEMPLATES_DIR / "commands").is_dir()

    def test_assets_directory_exists(self):
        """templates/iac/terraform/assets/ must exist."""
        assert (TERRAFORM_TEMPLATES_DIR / "assets").is_dir()

    def test_agent_personas_directory_exists(self):
        """templates/iac/terraform/agent_personas/ must exist."""
        assert (TERRAFORM_TEMPLATES_DIR / "agent_personas").is_dir()


class TestTerraformCommandFilesExist:
    """Verify all four required IaC-native command template files are present."""

    @pytest.mark.parametrize(
        "filename",
        [
            "create_terraform_code.md",
            "update_terraform_code.md",
            "plan.md",
            "review.md",
        ],
    )
    def test_command_file_exists(self, filename):
        """Each expected command template file must exist."""
        path = TERRAFORM_TEMPLATES_DIR / "commands" / filename
        assert path.is_file(), f"Missing command template: {path}"

    @pytest.mark.parametrize(
        "filename",
        [
            "create_terraform_code.md",
            "update_terraform_code.md",
            "plan.md",
            "review.md",
        ],
    )
    def test_command_file_non_empty(self, filename):
        """Each command template file must contain content."""
        path = TERRAFORM_TEMPLATES_DIR / "commands" / filename
        content = _read(path)
        assert len(content.strip()) > 0, f"Command template is empty: {filename}"


class TestTerraformCommandFileFrontmatter:
    """Verify YAML frontmatter in command files is valid and complete."""

    @pytest.mark.parametrize(
        "filename",
        [
            "create_terraform_code.md",
            "update_terraform_code.md",
            "plan.md",
            "review.md",
        ],
    )
    def test_frontmatter_present(self, filename):
        """Command file must start with a YAML frontmatter block."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "commands" / filename)
        assert content.startswith("---"), (
            f"{filename} must start with YAML frontmatter (---)"
        )

    @pytest.mark.parametrize(
        "filename",
        [
            "create_terraform_code.md",
            "update_terraform_code.md",
            "plan.md",
            "review.md",
        ],
    )
    def test_frontmatter_has_description(self, filename):
        """Frontmatter must contain a non-empty description field."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "commands" / filename)
        fm = _parse_frontmatter(content)
        assert "description" in fm, f"{filename} frontmatter missing 'description'"
        assert len(fm["description"]) > 0, f"{filename} has empty description"

    @pytest.mark.parametrize(
        "filename",
        [
            "create_terraform_code.md",
            "update_terraform_code.md",
            "plan.md",
            "review.md",
        ],
    )
    def test_frontmatter_has_argument_hint(self, filename):
        """Frontmatter must contain an argument-hint field."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "commands" / filename)
        assert "argument-hint:" in content, (
            f"{filename} frontmatter missing 'argument-hint'"
        )

    @pytest.mark.parametrize(
        "filename",
        [
            "create_terraform_code.md",
            "update_terraform_code.md",
            "plan.md",
            "review.md",
        ],
    )
    def test_command_body_contains_arguments_placeholder(self, filename):
        """Command file body must contain the $ARGUMENTS placeholder."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "commands" / filename)
        assert "$ARGUMENTS" in content, f"{filename} missing $ARGUMENTS placeholder"


class TestCreateTerraformCodeCommand:
    """Detailed tests for create_terraform_code.md content."""

    @pytest.fixture
    def content(self):
        return _read(TERRAFORM_TEMPLATES_DIR / "commands" / "create_terraform_code.md")

    def test_description_references_terraform(self, content):
        """Description should reference Terraform."""
        assert "terraform" in content.lower() or "hcl" in content.lower()

    def test_references_setup_command_on_missing_files(self, content):
        """Must direct users to setup when required files are missing."""
        assert "infrakit:setup" in content

    def test_references_spec_md_output(self, content):
        """Must mention generating spec.md."""
        assert "spec.md" in content

    def test_references_tracks_md(self, content):
        """Must reference the track registry."""
        assert "tracks.md" in content

    def test_references_architect_review_phase(self, content):
        """Must include architect review phase."""
        assert "architect" in content.lower() or "cloud architect" in content.lower()

    def test_references_security_review_phase(self, content):
        """Must include security review phase."""
        assert "security" in content.lower()

    def test_references_update_command_for_existing_dirs(self, content):
        """Must suggest update_terraform_code for non-empty directories."""
        assert "update_terraform_code" in content

    def test_references_infrakit_plan_next_step(self, content):
        """Must point to infrakit:plan as the next step."""
        assert "infrakit:plan" in content

    def test_has_error_handling_section(self, content):
        """Must have an Error Handling section."""
        assert "Error Handling" in content or "error handling" in content.lower()


class TestUpdateTerraformCodeCommand:
    """Detailed tests for update_terraform_code.md content."""

    @pytest.fixture
    def content(self):
        return _read(TERRAFORM_TEMPLATES_DIR / "commands" / "update_terraform_code.md")

    def test_references_main_tf(self, content):
        """Must check for main.tf as the primary Terraform file."""
        assert "main.tf" in content

    def test_references_variables_tf(self, content):
        """Must reference variables.tf for context reconstruction."""
        assert "variables.tf" in content

    def test_references_outputs_tf(self, content):
        """Must reference outputs.tf for context reconstruction."""
        assert "outputs.tf" in content

    def test_references_change_classification(self, content):
        """Must classify changes as Additive, Behavioral, or Breaking."""
        assert "Additive" in content
        assert "Breaking" in content

    def test_references_migration_md_for_breaking_changes(self, content):
        """Must generate migration.md for breaking changes."""
        assert "migration.md" in content

    def test_references_create_command_for_new_dirs(self, content):
        """Must suggest create_terraform_code for non-existent directories."""
        assert "create_terraform_code" in content

    def test_references_state_impact(self, content):
        """Must address Terraform state impact for breaking changes."""
        assert "state" in content.lower()


class TestTerraformPlanCommand:
    """Detailed tests for plan.md content."""

    @pytest.fixture
    def content(self):
        return _read(TERRAFORM_TEMPLATES_DIR / "commands" / "plan.md")

    def test_references_terraform_registry(self, content):
        """Must look up resources on registry.terraform.io."""
        assert "registry.terraform.io" in content

    def test_references_variables_design(self, content):
        """Must include variable mapping section."""
        assert "variable" in content.lower() or "Variable" in content

    def test_references_outputs_design(self, content):
        """Must include output mapping section."""
        assert "output" in content.lower() or "Output" in content

    def test_references_create_command_for_missing_spec(self, content):
        """Must direct to create_terraform_code when spec.md is missing."""
        assert "create_terraform_code" in content

    def test_references_plan_md_output_file(self, content):
        """Must produce plan.md."""
        assert "plan.md" in content

    def test_references_tagging_strategy(self, content):
        """Must address tagging strategy for AWS/Azure/GCP."""
        assert "tag" in content.lower() or "label" in content.lower()


class TestTerraformReviewCommand:
    """Detailed tests for review.md content."""

    @pytest.fixture
    def content(self):
        return _read(TERRAFORM_TEMPLATES_DIR / "commands" / "review.md")

    def test_references_main_tf(self, content):
        """Must check main.tf."""
        assert "main.tf" in content

    def test_references_versions_tf(self, content):
        """Must check versions.tf for provider pinning."""
        assert "versions.tf" in content

    def test_references_no_hardcoded_secrets(self, content):
        """Must check for hardcoded secrets."""
        assert "secret" in content.lower() or "hardcode" in content.lower()

    def test_references_tagging_check(self, content):
        """Must verify required tags."""
        assert "tag" in content.lower() or "label" in content.lower()

    def test_references_encryption(self, content):
        """Must check encryption at rest."""
        assert "encrypt" in content.lower()

    def test_references_version_constraints(self, content):
        """Must check for required_version or version constraint."""
        assert "required_version" in content or "version" in content.lower()

    def test_verdict_options_present(self, content):
        """Must include APPROVED / NEEDS FIXES verdict options."""
        assert "APPROVED" in content
        assert "NEEDS FIXES" in content

    def test_references_severity_levels(self, content):
        """Must define severity levels for findings."""
        assert "CRITICAL" in content
        assert "HIGH" in content


class TestTerraformAssets:
    """Tests for templates/iac/terraform/assets/ files."""

    def test_coding_style_template_exists(self):
        """coding-style-template.md must exist."""
        path = TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md"
        assert path.is_file(), f"Missing: {path}"

    def test_coding_style_template_non_empty(self):
        """coding-style-template.md must contain content."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md")
        assert len(content.strip()) > 0

    def test_coding_style_references_terraform_version(self):
        """coding-style-template.md must include Terraform version section."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md")
        assert "TERRAFORM_VERSION" in content or "required_version" in content

    def test_coding_style_references_provider_pinning(self):
        """coding-style-template.md must document provider version constraints."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md")
        assert "required_providers" in content or "~>" in content

    def test_coding_style_references_tagging(self):
        """coding-style-template.md must include tagging section."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md")
        assert "tag" in content.lower() or "label" in content.lower()

    def test_coding_style_references_security_standards(self):
        """coding-style-template.md must include security standards section."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md")
        assert "security" in content.lower() or "Security" in content

    def test_coding_style_references_managed_by_tag(self):
        """coding-style-template.md must include managed-by = terraform tag."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md")
        assert "managed-by" in content

    def test_coding_style_references_file_structure(self):
        """coding-style-template.md must describe the module file structure."""
        content = _read(TERRAFORM_TEMPLATES_DIR / "assets" / "coding-style-template.md")
        assert "main.tf" in content
        assert "variables.tf" in content
        assert "outputs.tf" in content


class TestTerraformAgentPersona:
    """Tests for templates/iac/terraform/agent_personas/terraform_engineer.md."""

    @pytest.fixture
    def content(self):
        path = TERRAFORM_TEMPLATES_DIR / "agent_personas" / "terraform_engineer.md"
        return _read(path)

    def test_terraform_engineer_persona_exists(self):
        """terraform_engineer.md must exist."""
        path = TERRAFORM_TEMPLATES_DIR / "agent_personas" / "terraform_engineer.md"
        assert path.is_file(), f"Missing: {path}"

    def test_persona_has_frontmatter(self, content):
        """terraform_engineer.md must have a YAML frontmatter block."""
        assert content.startswith("---")

    def test_persona_frontmatter_has_name(self, content):
        """Frontmatter must declare name: terraform-engineer."""
        assert "name: terraform-engineer" in content

    def test_persona_references_registry_terraform_io(self, content):
        """Persona must reference registry.terraform.io for schema lookups."""
        assert "registry.terraform.io" in content

    def test_persona_references_never_guess(self, content):
        """Persona must instruct agent to never guess argument names."""
        assert "NEVER" in content
        assert "guess" in content.lower() or "GUESS" in content

    def test_persona_references_compliance_check(self, content):
        """Persona must include a compliance/checklist section."""
        assert "compliance" in content.lower() or "Compliance" in content

    def test_persona_references_hcl_files(self, content):
        """Persona must reference Terraform HCL output files."""
        assert "main.tf" in content
        assert "variables.tf" in content
        assert "outputs.tf" in content
        assert "versions.tf" in content

    def test_persona_references_tagging(self, content):
        """Persona must mandate tagging."""
        assert "tag" in content.lower() or "label" in content.lower()

    def test_persona_references_sensitive_variables(self, content):
        """Persona must address sensitive variable handling."""
        assert "sensitive" in content.lower()

    def test_persona_references_spec_as_immutable_contract(self, content):
        """Persona must treat spec.md as the immutable contract."""
        assert "spec.md" in content
        assert "immutable" in content.lower() or "contract" in content.lower()

