#!/usr/bin/env python3
"""
Tests for the template validation module.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, List

from specify_cli.validation import (
    TemplateValidator,
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    validate_template_file,
    validate_templates_directory
)


class TestTemplateValidator:
    """Test cases for TemplateValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TemplateValidator()

    def test_valid_spec_template(self):
        """Test validation of a valid spec template."""
        content = """# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft

## Execution Flow (main)
```
1. Parse user description
2. Extract key concepts
3. Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios
5. Generate Requirements
6. Run Review Checklist
```

## Requirements

### Functional Requirements
- **FR-001**: System MUST [capability]

## Review & Acceptance Checklist

### Content Quality
- [ ] No implementation details
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = self.validator.validate_template(temp_path)
            assert result.is_valid
            assert result.template_type == 'spec'
            assert len(result.issues) == 0
        finally:
            temp_path.unlink()

    def test_missing_required_sections(self):
        """Test detection of missing required sections."""
        content = """# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

## Some Section
Content here but missing required sections.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = self.validator.validate_template(temp_path)
            assert not result.is_valid
            assert result.has_errors
            
            # Check that missing sections are detected
            error_messages = [issue.message for issue in result.issues 
                            if issue.severity == ValidationSeverity.ERROR]
            assert any("Requirements" in msg for msg in error_messages)
            assert any("Execution Flow" in msg for msg in error_messages)
        finally:
            temp_path.unlink()

    def test_invalid_placeholders(self):
        """Test detection of invalid placeholder patterns."""
        content = """# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]

## Requirements
- Invalid placeholder: [invalid-format]
- Another bad one: [123-bad]
- Good one: [NEEDS CLARIFICATION: something]

## Execution Flow
```
Steps here
```

## Review & Acceptance Checklist
- [ ] Something
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = self.validator.validate_template(temp_path)
            # Should have warnings for invalid placeholders but still be structurally valid
            assert result.has_warnings
            
            warning_messages = [issue.message for issue in result.issues 
                              if issue.severity == ValidationSeverity.WARNING]
            assert any("invalid-format" in msg for msg in warning_messages)
            assert any("123-bad" in msg for msg in warning_messages)
            # Should not warn about the valid NEEDS CLARIFICATION
            assert not any("NEEDS CLARIFICATION: something" in msg for msg in warning_messages)
        finally:
            temp_path.unlink()

    def test_command_template_validation(self):
        """Test validation of command templates."""
        valid_command = """---
name: test-command
description: "Test command description"
---

This is a test command template.
"""

        invalid_command = """---
name: test-command
# missing description
---

This command is missing required metadata.
"""

        # Test valid command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(valid_command)
            temp_path = Path(f.name)

        try:
            # Simulate being in commands directory
            commands_dir = temp_path.parent / "commands"
            commands_dir.mkdir(exist_ok=True)
            command_file = commands_dir / "test.md"
            command_file.write_text(valid_command)
            
            result = self.validator.validate_template(command_file)
            assert result.template_type == 'command'
            assert result.is_valid or not result.has_errors  # May have warnings but no errors
        finally:
            if temp_path.exists():
                temp_path.unlink()
            if command_file.exists():
                command_file.unlink()
            if commands_dir.exists():
                commands_dir.rmdir()

        # Test invalid command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(invalid_command)
            temp_path = Path(f.name)

        try:
            commands_dir = temp_path.parent / "commands"
            commands_dir.mkdir(exist_ok=True)
            command_file = commands_dir / "test.md"
            command_file.write_text(invalid_command)
            
            result = self.validator.validate_template(command_file)
            assert result.template_type == 'command'
            assert result.has_errors
            
            error_messages = [issue.message for issue in result.issues 
                            if issue.severity == ValidationSeverity.ERROR]
            assert any("description" in msg for msg in error_messages)
        finally:
            if temp_path.exists():
                temp_path.unlink()
            if command_file.exists():
                command_file.unlink()
            if commands_dir.exists():
                commands_dir.rmdir()

    def test_execution_flow_validation(self):
        """Test validation of execution flow sections."""
        content_without_flow = """# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

## Requirements
- Something

## Review & Acceptance Checklist
- [ ] Something
"""

        content_with_bad_flow = """# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

## Execution Flow
This is not in a code block.

## Requirements
- Something

## Review & Acceptance Checklist
- [ ] Something
"""

        # Test missing execution flow
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content_without_flow)
            temp_path = Path(f.name)

        try:
            result = self.validator.validate_template(temp_path)
            assert result.has_warnings
            warning_messages = [issue.message for issue in result.issues 
                              if issue.severity == ValidationSeverity.WARNING]
            assert any("Execution Flow" in msg for msg in warning_messages)
        finally:
            temp_path.unlink()

        # Test execution flow without code block
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content_with_bad_flow)
            temp_path = Path(f.name)

        try:
            result = self.validator.validate_template(temp_path)
            assert result.has_warnings
            warning_messages = [issue.message for issue in result.issues 
                              if issue.severity == ValidationSeverity.WARNING]
            assert any("code block" in msg for msg in warning_messages)
        finally:
            temp_path.unlink()

    def test_empty_template(self):
        """Test validation of empty template."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            result = self.validator.validate_template(temp_path)
            assert not result.is_valid
            assert result.has_errors
            
            error_messages = [issue.message for issue in result.issues 
                            if issue.severity == ValidationSeverity.ERROR]
            assert any("empty" in msg.lower() for msg in error_messages)
        finally:
            temp_path.unlink()

    def test_nonexistent_file(self):
        """Test validation of nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.md")
        result = self.validator.validate_template(nonexistent_path)
        
        assert not result.is_valid
        assert result.has_errors
        assert result.template_type == "unknown"
        
        error_messages = [issue.message for issue in result.issues 
                        if issue.severity == ValidationSeverity.ERROR]
        assert any("not found" in msg for msg in error_messages)

    def test_template_type_detection(self):
        """Test template type detection logic."""
        test_cases = [
            ("spec-template.md", "# Feature Specification", "spec"),
            ("plan-template.md", "# Implementation Plan", "plan"),
            ("tasks-template.md", "# Tasks:", "tasks"),
            ("agent-template.md", "# Development Guidelines", "agent"),
        ]

        for filename, content, expected_type in test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(content)
                temp_path = Path(f.name)
                # Rename to expected filename
                new_path = temp_path.parent / filename
                temp_path.rename(new_path)

            try:
                result = self.validator.validate_template(new_path)
                assert result.template_type == expected_type
            finally:
                new_path.unlink()

    def test_directory_validation(self):
        """Test validation of entire template directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create valid template
            valid_template = temp_path / "valid.md"
            valid_template.write_text("""# Feature Specification: [FEATURE NAME]

## Execution Flow
```
1. Steps
```

## Requirements
- Something

## Review & Acceptance Checklist
- [ ] Something
""")

            # Create invalid template
            invalid_template = temp_path / "invalid.md"
            invalid_template.write_text("""# Incomplete Template

Missing required sections.
""")

            # Create commands subdirectory with command template
            commands_dir = temp_path / "commands"
            commands_dir.mkdir()
            command_template = commands_dir / "test.md"
            command_template.write_text("""---
name: test
description: "Test command"
---

Command content.
""")

            results = self.validator.validate_template_directory(temp_path)
            
            assert len(results) == 3
            assert "valid.md" in results
            assert "invalid.md" in results
            assert "commands/test.md" in results
            
            # Check results
            assert results["valid.md"].is_valid
            assert not results["invalid.md"].is_valid
            assert results["commands/test.md"].template_type == "command"


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_validate_template_file(self):
        """Test validate_template_file convenience function."""
        content = """# Feature Specification: [FEATURE NAME]

## Execution Flow
```
1. Steps
```

## Requirements
- Something

## Review & Acceptance Checklist
- [ ] Something
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = validate_template_file(temp_path)
            assert isinstance(result, ValidationResult)
            assert result.is_valid
        finally:
            temp_path.unlink()

    def test_validate_templates_directory(self):
        """Test validate_templates_directory convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            template = temp_path / "test.md"
            template.write_text("""# Feature Specification: [FEATURE NAME]

## Execution Flow
```
1. Steps
```

## Requirements
- Something

## Review & Acceptance Checklist
- [ ] Something
""")

            results = validate_templates_directory(temp_path)
            assert isinstance(results, dict)
            assert "test.md" in results
            assert isinstance(results["test.md"], ValidationResult)


class TestValidationResult:
    """Test ValidationResult class methods."""

    def test_has_errors_property(self):
        """Test has_errors property."""
        # Result with errors
        result_with_errors = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(ValidationSeverity.ERROR, "Error message"),
                ValidationIssue(ValidationSeverity.WARNING, "Warning message")
            ],
            template_type="spec",
            file_path=Path("test.md")
        )
        assert result_with_errors.has_errors

        # Result without errors
        result_without_errors = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue(ValidationSeverity.WARNING, "Warning message")
            ],
            template_type="spec",
            file_path=Path("test.md")
        )
        assert not result_without_errors.has_errors

    def test_has_warnings_property(self):
        """Test has_warnings property."""
        # Result with warnings
        result_with_warnings = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue(ValidationSeverity.WARNING, "Warning message"),
                ValidationIssue(ValidationSeverity.INFO, "Info message")
            ],
            template_type="spec",
            file_path=Path("test.md")
        )
        assert result_with_warnings.has_warnings

        # Result without warnings
        result_without_warnings = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue(ValidationSeverity.INFO, "Info message")
            ],
            template_type="spec",
            file_path=Path("test.md")
        )
        assert not result_without_warnings.has_warnings


if __name__ == "__main__":
    pytest.main([__file__])
