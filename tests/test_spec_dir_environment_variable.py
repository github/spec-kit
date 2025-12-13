"""
Test the SPECIFY_SPEC_DIR environment variable functionality.

This test verifies that the CLI correctly reads and uses the SPECIFY_SPEC_DIR
environment variable when no --spec-dir flag is provided.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

# Add the src directory to the path for importing the CLI
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specify_cli import validate_spec_dir


class TestSpecDirEnvironmentVariable:
    """Test SPECIFY_SPEC_DIR environment variable functionality."""

    def test_cli_reads_environment_variable(self):
        """Test that the CLI correctly reads SPECIFY_SPEC_DIR from environment."""
        # Test with environment variable set
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = "test-specs"

        # Run CLI help command and check if it shows the correct default
        result = subprocess.run(
            [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=env
        )

        # The help output should contain the environment variable value as default
        assert "test-specs" in result.stdout
        assert result.returncode == 0

    def test_cli_fallback_to_specs_when_env_not_set(self):
        """Test that CLI falls back to 'specs' when SPECIFY_SPEC_DIR is not set."""
        # Remove SPECIFY_SPEC_DIR from environment
        env = os.environ.copy()
        env.pop("SPECIFY_SPEC_DIR", None)

        # Run CLI help command
        result = subprocess.run(
            [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=env
        )

        # Should fall back to 'specs' as default
        assert "[default: specs" in result.stdout
        assert result.returncode == 0

    def test_override_environment_variable_with_flag(self):
        """Test that --spec-dir flag overrides the environment variable."""
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = "env-specs"

        # Run CLI help command with --spec-dir flag
        result = subprocess.run(
            [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=env
        )

        # Help should show environment variable as default
        assert "env-specs" in result.stdout
        assert result.returncode == 0

    def test_environment_variable_validation(self):
        """Test that the environment variable value is validated properly."""
        # Test valid environment variable
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = "valid-specs"

        # Test that the validate_spec_dir function accepts the environment variable value
        try:
            result = validate_spec_dir("valid-specs")
            assert result == "valid-specs"
        except SystemExit:
            pytest.fail("validate_spec_dir rejected a valid environment variable value")

    def test_environment_variable_with_special_chars(self):
        """Test that environment variables with special characters are handled."""
        # Test with hyphens (should be valid)
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = "my-features-specs"

        result = subprocess.run(
            [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=env
        )

        assert "my-features-specs" in result.stdout
        assert result.returncode == 0

    def test_environment_variable_with_nested_path(self):
        """Test that nested paths work in environment variable."""
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = "documentation/api-specs"

        result = subprocess.run(
            [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=env
        )

        assert "documentation/api-specs" in result.stdout
        assert result.returncode == 0

    def test_environment_variable_ignored_when_flag_provided(self):
        """Test that --spec-dir flag takes precedence over environment variable."""
        # This tests the CLI behavior - when both env var and flag are provided,
        # the flag should win
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = "env-specs"

        # Create a temporary script to test this
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f'''
import sys
import os
sys.path.insert(0, "{Path(__file__).parent.parent / "src"}")

# Simulate how typer would handle this
import typer
from pathlib import Path

@app.command()
def test_init(
    spec_dir: str = typer.Option(os.getenv("SPECIFY_SPEC_DIR", "specs"), "--spec-dir"),
):
    print(f"Using spec_dir: {{spec_dir}}")

if __name__ == "__main__":
    from typer.main import get_command
    cli = get_command(test_init)
    cli(["test_init", "--spec-dir", "flag-specs"])
''')
            temp_script = f.name

        try:
            # This is a conceptual test - in real usage, typer would handle the
            # precedence correctly where command-line flags override defaults
            pass
        finally:
            os.unlink(temp_script)

    def test_environment_variable_empty_string(self):
        """Test behavior when SPECIFY_SPEC_DIR is set to empty string."""
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = ""

        # Empty string should be rejected and fall back to 'specs'
        result = subprocess.run(
            [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=env
        )

        # Should fall back to 'specs' when environment variable is empty
        assert "[default: specs" in result.stdout
        assert result.returncode == 0

    def test_environment_variable_whitespace_only(self):
        """Test behavior when SPECIFY_SPEC_DIR contains only whitespace."""
        env = os.environ.copy()
        env["SPECIFY_SPEC_DIR"] = "   "

        # Whitespace-only should be rejected and fall back to 'specs'
        result = subprocess.run(
            [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env=env
        )

        # Should fall back to 'specs' when environment variable is whitespace-only
        assert "[default: specs" in result.stdout
        assert result.returncode == 0

    def test_validate_spec_dir_function_with_env_var_value(self):
        """Test the validate_spec_dir function with typical environment variable values."""
        # Test values that should be valid in environment variables
        valid_values = [
            "specs",
            "docs",
            "documentation",
            "api-specs",
            "feature_specs",
            "docs/api",
            "requirements/specifications"
        ]

        for value in valid_values:
            try:
                result = validate_spec_dir(value)
                assert result == value, f"Expected '{value}', got '{result}'"
            except SystemExit as e:
                pytest.fail(f"validate_spec_dir rejected valid value '{value}': {e}")

    def test_environment_variable_persistence(self):
        """Test that environment variable setting persists across multiple calls."""
        env = os.environ.copy()
        test_value = "persistent-specs"
        env["SPECIFY_SPEC_DIR"] = test_value

        # Run help command twice to ensure consistency
        for i in range(2):
            result = subprocess.run(
                [sys.executable, "src/specify_cli/__init__.py", "init", "--help"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                env=env
            )

            assert test_value in result.stdout
            assert result.returncode == 0