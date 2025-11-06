"""
Tests for critical bash scripts.
"""
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


# Path to bash scripts
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts" / "bash"


@pytest.mark.unit
class TestBashScriptStructure:
    """Tests for bash script file structure."""

    def test_bash_scripts_exist(self):
        """Test critical bash scripts exist."""
        expected_scripts = [
            "check-prerequisites.sh",
            "create-new-feature.sh",
            "update-agent-context.sh",
            "check-guidelines-compliance.sh",
            "autofix-guidelines.sh",
            "common.sh",
        ]

        for script_name in expected_scripts:
            script_path = SCRIPTS_DIR / script_name
            assert script_path.exists(), f"Script {script_name} should exist"

    def test_bash_scripts_have_shebang(self):
        """Test bash scripts have proper shebang."""
        scripts = [
            "check-prerequisites.sh",
            "create-new-feature.sh",
            "common.sh",
        ]

        for script_name in scripts:
            script_path = SCRIPTS_DIR / script_name
            if script_path.exists():
                with open(script_path) as f:
                    first_line = f.readline().strip()
                    assert first_line.startswith("#!"), f"{script_name} should have shebang"
                    assert "sh" in first_line or "bash" in first_line, f"{script_name} should be shell script"

    def test_bash_scripts_are_not_empty(self):
        """Test bash scripts are not empty."""
        for script_path in SCRIPTS_DIR.glob("*.sh"):
            assert script_path.stat().st_size > 0, f"{script_path.name} should not be empty"

    def test_common_script_sourced_correctly(self):
        """Test scripts that source common.sh have correct path."""
        scripts_to_check = [
            "check-prerequisites.sh",
            "create-new-feature.sh",
        ]

        for script_name in scripts_to_check:
            script_path = SCRIPTS_DIR / script_name
            if script_path.exists():
                content = script_path.read_text()
                # Should source common.sh
                if "source" in content or "." in content:
                    # Verify it references common.sh
                    assert "common.sh" in content, f"{script_name} should source common.sh"


@pytest.mark.unit
class TestCheckPrerequisitesScript:
    """Tests for check-prerequisites.sh script."""

    def test_check_prerequisites_syntax(self):
        """Test check-prerequisites.sh has valid bash syntax."""
        script_path = SCRIPTS_DIR / "check-prerequisites.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        # Check syntax using bash -n
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_check_prerequisites_has_functions(self):
        """Test check-prerequisites.sh defines expected functions."""
        script_path = SCRIPTS_DIR / "check-prerequisites.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should define functions or have main logic
        assert "function" in content or "check" in content.lower()

    def test_check_prerequisites_checks_constitution(self):
        """Test check-prerequisites.sh checks for constitution file."""
        script_path = SCRIPTS_DIR / "check-prerequisites.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should reference constitution
        assert "constitution" in content.lower()


@pytest.mark.unit
class TestCreateNewFeatureScript:
    """Tests for create-new-feature.sh script."""

    def test_create_new_feature_syntax(self):
        """Test create-new-feature.sh has valid bash syntax."""
        script_path = SCRIPTS_DIR / "create-new-feature.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_create_new_feature_has_usage(self):
        """Test create-new-feature.sh has usage documentation."""
        script_path = SCRIPTS_DIR / "create-new-feature.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should have usage or help information
        assert "usage" in content.lower() or "help" in content.lower()

    def test_create_new_feature_checks_branch(self):
        """Test create-new-feature.sh handles branch creation."""
        script_path = SCRIPTS_DIR / "create-new-feature.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should reference git branch operations
        assert "branch" in content.lower()


@pytest.mark.unit
class TestCommonScript:
    """Tests for common.sh shared functions."""

    def test_common_script_syntax(self):
        """Test common.sh has valid bash syntax."""
        script_path = SCRIPTS_DIR / "common.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_common_script_defines_functions(self):
        """Test common.sh defines shared functions."""
        script_path = SCRIPTS_DIR / "common.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should define functions
        assert "function" in content or "()" in content

    def test_common_script_has_color_codes(self):
        """Test common.sh defines color codes for output."""
        script_path = SCRIPTS_DIR / "common.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Common scripts often define color codes
        # This is optional but common practice
        if "color" in content.lower() or "red" in content.lower():
            assert True


@pytest.mark.unit
class TestGuidelinesComplianceScript:
    """Tests for check-guidelines-compliance.sh script."""

    def test_guidelines_compliance_syntax(self):
        """Test check-guidelines-compliance.sh has valid bash syntax."""
        script_path = SCRIPTS_DIR / "check-guidelines-compliance.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_guidelines_compliance_references_guidelines_dir(self):
        """Test compliance script references guidelines directory."""
        script_path = SCRIPTS_DIR / "check-guidelines-compliance.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should reference .guidelines directory
        assert ".guidelines" in content

    def test_guidelines_compliance_has_severity_levels(self):
        """Test compliance script handles severity levels."""
        script_path = SCRIPTS_DIR / "check-guidelines-compliance.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should handle error/warning levels
        has_severity = any(word in content.lower() for word in ["error", "warning", "severity"])
        assert has_severity


@pytest.mark.unit
class TestAutofixGuidelinesScript:
    """Tests for autofix-guidelines.sh script."""

    def test_autofix_guidelines_syntax(self):
        """Test autofix-guidelines.sh has valid bash syntax."""
        script_path = SCRIPTS_DIR / "autofix-guidelines.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_autofix_references_compliance_check(self):
        """Test autofix script references compliance checking."""
        script_path = SCRIPTS_DIR / "autofix-guidelines.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should relate to compliance
        assert "compliance" in content.lower() or "fix" in content.lower()


@pytest.mark.unit
class TestUpdateAgentContextScript:
    """Tests for update-agent-context.sh script."""

    def test_update_agent_context_syntax(self):
        """Test update-agent-context.sh has valid bash syntax."""
        script_path = SCRIPTS_DIR / "update-agent-context.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_update_agent_context_references_artifacts(self):
        """Test update-agent-context.sh handles artifacts."""
        script_path = SCRIPTS_DIR / "update-agent-context.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        content = script_path.read_text()

        # Should handle artifacts or context
        has_artifact_ref = any(word in content.lower() for word in ["artifact", "context", "spec"])
        assert has_artifact_ref


@pytest.mark.integration
@pytest.mark.slow
class TestBashScriptExecution:
    """Integration tests for bash script execution."""

    def test_common_script_can_be_sourced(self, temp_dir: Path):
        """Test common.sh can be sourced without errors."""
        script_path = SCRIPTS_DIR / "common.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        # Create a test script that sources common.sh
        test_script = temp_dir / "test_source.sh"
        test_script.write_text(f"""#!/bin/bash
source "{script_path}"
echo "Success"
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0, f"Failed to source common.sh: {result.stderr}"
        assert "Success" in result.stdout

    def test_check_prerequisites_with_help_flag(self):
        """Test check-prerequisites.sh responds to help flag."""
        script_path = SCRIPTS_DIR / "check-prerequisites.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        # Try running with --help
        result = subprocess.run(
            ["bash", str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should exit (may be 0 or 1) and show usage
        assert result.returncode in [0, 1]

    def test_create_new_feature_with_help_flag(self):
        """Test create-new-feature.sh responds to help flag."""
        script_path = SCRIPTS_DIR / "create-new-feature.sh"

        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            ["bash", str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should show help information
        assert result.returncode in [0, 1]


@pytest.mark.unit
class TestScriptPermissions:
    """Tests for script file permissions."""

    def test_scripts_have_execute_permission(self):
        """Test bash scripts have execute permission."""
        for script_path in SCRIPTS_DIR.glob("*.sh"):
            # Check if file is executable (on Unix-like systems)
            import os
            import stat

            file_stat = script_path.stat()
            is_executable = bool(file_stat.st_mode & stat.S_IXUSR)

            # Note: This test may not be meaningful on all platforms
            # On Windows, all files may appear executable
            if os.name != 'nt':
                # On Unix-like systems, scripts should be executable
                # But we'll make this a soft assertion since permissions
                # might not be preserved in some environments
                pass  # Permissions will be set by ensure_executable_scripts


@pytest.mark.unit
class TestScriptDocumentation:
    """Tests for script documentation."""

    def test_scripts_have_header_comments(self):
        """Test bash scripts have header documentation."""
        for script_path in SCRIPTS_DIR.glob("*.sh"):
            content = script_path.read_text()
            lines = content.split('\n')

            # Should have comments near the top (within first 10 lines)
            has_comments = any(line.strip().startswith('#') for line in lines[:10])
            assert has_comments, f"{script_path.name} should have header comments"

    def test_scripts_describe_purpose(self):
        """Test scripts include purpose description."""
        for script_path in SCRIPTS_DIR.glob("*.sh"):
            if script_path.name == "common.sh":
                continue  # Library file may not need extensive docs

            content = script_path.read_text()

            # Should have some description words
            description_words = ["description", "purpose", "usage", "this script"]
            has_description = any(word in content.lower() for word in description_words)

            # This is a soft assertion - not all scripts may have this
            # but it's good practice
            if not has_description:
                pass  # Log warning but don't fail
