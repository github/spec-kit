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
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot start or end with whitespace")

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
                mock_console.print.assert_any_call("[red]Error:[/red] Spec directory must be relative to project root, not an absolute path")

    def test_absolute_path_spec_dir_windows(self):
        """Test that absolute Windows paths raise SystemExit."""
        import platform
        import pytest
        # On Unix systems, Windows paths are not detected as absolute by os.path
        # This test is only meaningful on Windows systems
        if platform.system() != 'Windows':
            pytest.skip("Windows absolute path detection only works on Windows")

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
                mock_console.print.assert_any_call("[red]Error:[/red] Spec directory must be relative to project root, not an absolute path")

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
        """Test that invalid characters raise SystemExit with user-friendly error messages."""
        # Test regular invalid characters
        invalid_chars_and_examples = [
            ('<', 'specs<test>', 'less-than (<)'),
            ('>', 'specs>test<', 'greater-than (>)'),
            (':', 'specs:test', 'colon (:)'),
            ('"', '"specs"', 'double quote (")'),
            ('|', 'specs|test', 'pipe (|)'),
            ('?', 'specs?test', 'question mark (?)'),
            ('*', 'specs*test', 'asterisk (*)')
        ]

        for char, example, expected_description in invalid_chars_and_examples:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(example)
                assert exc_info.value.code == 1

                # Check that the error message mentions invalid characters with specific description
                all_calls = [call[0][0] for call in mock_console.print.call_args_list]
                error_message = next((msg for msg in all_calls if "invalid characters" in msg.lower()), None)
                assert error_message is not None, f"No error message with 'invalid characters' found in calls: {all_calls}"
                assert expected_description in error_message, f"Expected '{expected_description}' in error message: {error_message}"

                # Check for helpful tip (printed as separate call)
                tip_message = next((msg for msg in all_calls if "These characters are not allowed in directory names" in msg), None)
                assert tip_message is not None, f"Missing helpful tip in calls: {all_calls}"

        # Test control characters separately (they're caught by a different validation)
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir('specs\0test')
            assert exc_info.value.code == 1

            all_calls = [call[0][0] for call in mock_console.print.call_args_list]
            error_message = next((msg for msg in all_calls if "invalid control character" in msg), None)
            assert error_message is not None, f"No 'invalid control character' error message found: {all_calls}"
            assert "position 5" in error_message, f"Missing position information in control character error: {error_message}"

            tip_message = next((msg for msg in all_calls if "Control characters cannot be used" in msg), None)
            assert tip_message is not None, f"Missing control character tip: {all_calls}"

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
        """Test that too long path raises SystemExit with user-friendly error message."""
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

            # Check for specific error message and helpful tip
            all_calls = [call[0][0] for call in mock_console.print.call_args_list]
            error_message = next((msg for msg in all_calls if "too long" in msg.lower()), None)
            assert error_message is not None, f"No 'too long' error message found in calls: {all_calls}"
            assert f"{len(long_path)} characters, max 255" in error_message, f"Missing character count in error message: {error_message}"

            # Check for helpful tip (printed as separate call)
            tip_message = next((msg for msg in all_calls if "Consider using a shorter directory name" in msg), None)
            assert tip_message is not None, f"Missing helpful tip in calls: {all_calls}"

    def test_non_alphanumeric_start_spec_dir(self):
        """Test that non-alphanumeric start raises SystemExit with user-friendly error messages."""
        invalid_starts = [
            ("-specs", "cannot start with '-' - it must start with a letter or number"),
            ("_specs", "cannot start with '_' - it must start with a letter or number"),
            (".specs", "cannot start with '.' - it must start with a letter or number"),
            ("/specs", "must be relative to project root, not an absolute path"),  # Leading slash (caught as absolute path)
        ]

        for path, expected_message_fragment in invalid_starts:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1

                # Check for specific error message content
                all_calls = [call[0][0] for call in mock_console.print.call_args_list]
                error_message = next((msg for msg in all_calls if expected_message_fragment in msg), None)
                assert error_message is not None, f"Expected message fragment '{expected_message_fragment}' not found in calls: {all_calls}"

                # For specific character errors, check for helpful tip (printed as separate call)
                if path[0] in '-_.':
                    tip_message = next((msg for msg in all_calls if "Start directory names with a letter" in msg), None)
                    assert tip_message is not None, f"Missing helpful tip for {path}: {all_calls}"

        # Test backslash separately (behavior differs by platform)
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir("\\specs")
            assert exc_info.value.code == 1
            # On Unix, backslash is treated as invalid starting character
            # On Windows, it would be treated as an absolute path
            import platform
            if platform.system() == 'Windows':
                mock_console.print.assert_any_call("[red]Error:[/red] Spec directory must be relative to project root, not an absolute path")
            else:
                mock_console.print.assert_any_call("[red]Error:[/red] Spec directory must start with an alphanumeric character (found: '\\')")
        
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

    def test_comprehensive_unicode_scenarios(self):
        """Test comprehensive unicode scenarios including edge cases."""
        # Various unicode scripts that should work
        unicode_dirs = [
            "spécs-documentation",  # Latin with accent
            "仕様書",  # Japanese "specifications"
            "문서",    # Korean "documents"
            "文档",    # Chinese "documents"
            "документы",  # Cyrillic "documents"
            "مستندات",   # Arabic "documents"
            "dokümanlar",  # Turkish with accent
            "αδιαβαστικά",  # Greek
        ]

        for unicode_dir in unicode_dirs:
            # Only test if the first character is alphanumeric
            if unicode_dir[0].isalnum():
                result = validate_spec_dir(unicode_dir)
                assert result == unicode_dir, f"Unicode dir '{unicode_dir}' should pass validation"

    def test_long_path_scenarios(self):
        """Test very long path handling and edge cases."""
        # Test exactly at the boundary (255 characters)
        long_boundary = "a" * 255
        result = validate_spec_dir(long_boundary)
        assert result == long_boundary

        # Test over the boundary (256 characters) - should fail
        over_boundary_path = "a" * 256
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir(over_boundary_path)
            assert exc_info.value.code == 1
            mock_console.print.assert_any_call(f"[red]Error:[/red] Spec directory path is too long ({len(over_boundary_path)} characters, max 255)")

        # Test reasonable long paths that should work
        reasonable_long = "specification-documents-very-long-name-but-still-under-limit"
        result = validate_spec_dir(reasonable_long)
        assert result == reasonable_long

    def test_edge_case_unicode_combinations(self):
        """Test edge case combinations of unicode and special characters."""
        # Unicode with dashes and underscores
        unicode_mixed = "spécs-docs_123"
        result = validate_spec_dir(unicode_mixed)
        assert result == unicode_mixed

        # Multiple unicode characters
        unicode_multi = "α-β-γ-specs"
        result = validate_spec_dir(unicode_multi)
        assert result == unicode_multi

        # Unicode at start with alphanumeric property
        unicode_start_alnum = "1-specs-测试"
        result = validate_spec_dir(unicode_start_alnum)
        assert result == unicode_start_alnum

    def test_reserved_names_spec_dir(self):
        """Test that reserved names raise SystemExit with user-friendly error message."""
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]

        for reserved_name in reserved_names:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(reserved_name)
                assert exc_info.value.code == 1

                # Check for specific error message and helpful tip
                all_calls = [call[0][0] for call in mock_console.print.call_args_list]
                error_message = next((msg for msg in all_calls if "reserved system name" in msg), None)
                assert error_message is not None, f"No 'reserved system name' error message found for {reserved_name}: {all_calls}"
                assert f"'{reserved_name}' is a reserved system name" in error_message, f"Missing reserved name in error message: {error_message}"

                tip_message = next((msg for msg in all_calls if "Windows reserves these names" in msg), None)
                assert tip_message is not None, f"Missing Windows tip for reserved name {reserved_name}: {all_calls}"