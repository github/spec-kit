"""Test spec directory validation functionality."""

import pytest
from unittest.mock import patch
from typer.testing import CliRunner
import typer

# Import the module directly to avoid dependency issues
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specify_cli import validate_spec_dir


class TestValidateSpecDir:
    """Test the validate_spec_dir function."""

    def test_valid_spec_directories(self):
        """Test that valid spec directory names pass validation."""
        valid_dirs = [
            "specs",
            "docs", 
            "requirements",
            "feature-specs",
            "documentation",
            "specifications",
            "s",
            "spec_docs",
            "my-specs-123",
            "123specs",  # Numeric start is valid
            "a",
            "spec_dir_with_underscores",
            "spec-dir-with-dashes",
            "CamelCaseSpecs"
        ]
        
        for spec_dir in valid_dirs:
            result = validate_spec_dir(spec_dir)
            assert result == spec_dir, f"Valid spec_dir '{spec_dir}' should pass validation"

    def test_empty_spec_dir(self):
        """Test that empty spec directory raises typer.Exit."""
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir("")
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot be empty")

    def test_whitespace_only_spec_dir(self):
        """Test that whitespace-only spec directory raises typer.Exit."""
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir("   ")
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot be empty")

    def test_absolute_path_spec_dir_unix(self):
        """Test that absolute Unix paths raise SystemExit."""
        absolute_paths = [
            "/etc/specs",
            "/home/user/specs",
            "/usr/local/specs",
            "/tmp/specs"
        ]
        
        for path in absolute_paths:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory must be relative to project root, not an absolute path")

    def test_absolute_path_spec_dir_windows(self):
        """Test that absolute Windows paths raise SystemExit."""
        absolute_paths = [
            "C:\\specs",
            "C:/Users/user/specs",
            "D:\\Projects\\specs",
            "E:/specs"
        ]
        
        for path in absolute_paths:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory must be relative to project root, not an absolute path")

    def test_parent_traversal_spec_dir(self):
        """Test that parent directory traversal raises SystemExit."""
        traversal_paths = [
            "../specs",
            "specs/../..",
            "../../specs",
            "docs/../../specs",
            "specs/../other",
            "../specs/../docs",
            "specs/../../../etc"
        ]
        
        for path in traversal_paths:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot contain parent directory traversal (..)")

    def test_invalid_characters_spec_dir(self):
        """Test that invalid characters raise SystemExit."""
        invalid_chars_and_examples = [
            ('<', 'specs<test>'),
            ('>', 'specs>test<'),
            (':', 'specs:test'),
            ('"', '"specs"'),
            ('|', 'specs|test'),
            ('?', 'specs?test'),
            ('*', 'specs*test'),
            ('\0', 'specs\0test')
        ]
        
        for char, example in invalid_chars_and_examples:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(example)
                assert exc_info.value.code == 1
                # Check that the error message mentions invalid characters
                mock_console.print.assert_called()
                call_args = mock_console.print.call_args[0][0]
                assert "invalid characters" in call_args.lower()

    def test_trailing_slash_spec_dir(self):
        """Test that trailing slash raises SystemExit."""
        trailing_slash_paths = [
            "specs/",
            "docs\\",
            "requirements/",
            "feature\\",
            "documentation/",
            "specifications\\"
        ]
        
        for path in trailing_slash_paths:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot end with a slash or backslash")

    def test_too_long_spec_dir(self):
        """Test that too long path raises SystemExit."""
        # Test exactly at limit (should pass)
        valid_long_path = "a" * 255
        result = validate_spec_dir(valid_long_path)
        assert result == valid_long_path
        
        # Test over limit (should fail)
        long_path = "a" * 256
        
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir(long_path)
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory path is too long (max 255 characters)")

    def test_non_alphanumeric_start_spec_dir(self):
        """Test that non-alphanumeric start raises SystemExit."""
        invalid_starts = [
            "-specs",
            "_specs",
            ".specs",
            "/specs",  # Leading slash (caught as absolute path)
            "\\specs",  # Leading backslash
        ]
        
        for path in invalid_starts:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                if path.startswith(('/', '\\')):
                    mock_console.print.assert_called_with("[red]Error:[/red] Spec directory must be relative to project root, not an absolute path")
                else:
                    mock_console.print.assert_called_with("[red]Error:[/red] Spec directory must start with an alphanumeric character")
        
        # Test leading space separately
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir(" specs")
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot start or end with whitespace")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Single character (valid)
        result = validate_spec_dir("s")
        assert result == "s"
        
        # Single numeric (valid)
        result = validate_spec_dir("1")
        assert result == "1"
        
        # Mixed alphanumeric (valid)
        result = validate_spec_dir("specs123")
        assert result == "specs123"
        
        # With numbers and letters (valid)
        result = validate_spec_dir("123specs456")
        assert result == "123specs456"

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        # Valid unicode characters should pass
        unicode_valid = "spécs"  # Contains accented character
        result = validate_spec_dir(unicode_valid)
        assert result == unicode_valid
        
        # Unicode that starts with alphanumeric should pass
        unicode_valid_start = "αspecs"  # Greek alpha
        result = validate_spec_dir(unicode_valid_start)
        assert result == unicode_valid_start