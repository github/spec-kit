#!/usr/bin/env python3
"""
Template validation module for Specify CLI.

This module provides functionality to validate templates for:
- Structure and format compliance
- Required sections and placeholders
- Content consistency
- Command template metadata
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a template."""
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    section: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of template validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    template_type: str
    file_path: Path

    @property
    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)


class TemplateValidator:
    """Main template validation class."""

    # Pattern definitions for different placeholder types
    PLACEHOLDER_PATTERNS = {
        'feature_name': r'\[FEATURE\s*NAME?\]',
        'feature_branch': r'\[###-[^]]+\]',
        'date': r'\[DATE\]',
        'project_name': r'\[PROJECT\s*NAME?\]',
        'version': r'\[VERSION\]',
        'args': r'\[ARGS\]',
        'needs_clarification': r'\[NEEDS\s+CLARIFICATION:.*?\]',
        'generic_placeholder': r'\[[A-Z_][A-Z0-9_\s]*\]',
    }

    # Required sections for different template types
    REQUIRED_SECTIONS = {
        'spec': [
            'Feature Specification',
            'Execution Flow',
            'Requirements',
            'Review & Acceptance Checklist',
        ],
        'plan': [
            'Implementation Plan',
            'Execution Flow',
            'Technical Context',
            'Constitution Check',
            'Progress Tracking',
        ],
        'tasks': [
            'Tasks',
            'Execution Flow',
            'Format',
            'Phase 3.1: Setup',
            'Phase 3.2: Tests First',
        ],
        'command': [
            'Front matter (YAML)',
        ],
        'agent': [
            'Development Guidelines',
            'Active Technologies',
            'Project Structure',
        ],
    }

    def __init__(self):
        """Initialize the validator."""
        self.current_file: Optional[Path] = None
        self.current_content: Optional[str] = None
        self.current_lines: Optional[List[str]] = None

    def validate_template(self, template_path: Path) -> ValidationResult:
        """
        Validate a single template file.
        
        Args:
            template_path: Path to the template file
            
        Returns:
            ValidationResult with issues found
        """
        self.current_file = template_path
        
        if not template_path.exists():
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Template file not found: {template_path}"
                )],
                template_type="unknown",
                file_path=template_path
            )

        try:
            self.current_content = template_path.read_text(encoding='utf-8')
            self.current_lines = self.current_content.splitlines()
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Failed to read template file: {e}"
                )],
                template_type="unknown",
                file_path=template_path
            )

        # Determine template type
        template_type = self._determine_template_type(template_path)
        
        # Run validation checks
        issues = []
        issues.extend(self._validate_basic_structure())
        issues.extend(self._validate_required_sections(template_type))
        issues.extend(self._validate_placeholders())
        issues.extend(self._validate_command_metadata(template_type))
        issues.extend(self._validate_execution_flow())
        
        # Filter and sort issues
        issues = self._filter_and_sort_issues(issues)
        
        return ValidationResult(
            is_valid=not any(issue.severity == ValidationSeverity.ERROR for issue in issues),
            issues=issues,
            template_type=template_type,
            file_path=template_path
        )

    def validate_template_directory(self, templates_dir: Path) -> Dict[str, ValidationResult]:
        """
        Validate all templates in a directory.
        
        Args:
            templates_dir: Path to templates directory
            
        Returns:
            Dictionary mapping template names to validation results
        """
        results = {}
        
        if not templates_dir.exists():
            return results

        # Find all template files
        template_files = []
        template_files.extend(templates_dir.glob("*.md"))
        template_files.extend(templates_dir.glob("commands/*.md"))
        
        for template_file in template_files:
            relative_path = template_file.relative_to(templates_dir)
            results[str(relative_path)] = self.validate_template(template_file)
            
        return results

    def _determine_template_type(self, template_path: Path) -> str:
        """Determine the type of template based on filename and content."""
        filename = template_path.name.lower()
        
        if 'spec' in filename:
            return 'spec'
        elif 'plan' in filename:
            return 'plan'
        elif 'tasks' in filename:
            return 'tasks'
        elif template_path.parent.name == 'commands':
            return 'command'
        elif 'agent' in filename or 'claude' in filename or 'gemini' in filename:
            return 'agent'
        else:
            # Try to determine from content
            if self.current_content:
                content_lower = self.current_content.lower()
                if 'feature specification' in content_lower:
                    return 'spec'
                elif 'implementation plan' in content_lower:
                    return 'plan'
                elif 'tasks:' in content_lower and 'phase 3' in content_lower:
                    return 'tasks'
                elif content_lower.startswith('---\nname:'):
                    return 'command'
                    
        return 'unknown'

    def _validate_basic_structure(self) -> List[ValidationIssue]:
        """Validate basic template structure."""
        issues = []
        
        if not self.current_content.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template file is empty"
            ))
            return issues
            
        # Check for basic markdown structure
        if not re.search(r'^#\s+', self.current_content, re.MULTILINE):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="No main heading found (should start with # )"
            ))
            
        return issues

    def _validate_required_sections(self, template_type: str) -> List[ValidationIssue]:
        """Validate that required sections are present."""
        issues = []
        
        if template_type not in self.REQUIRED_SECTIONS:
            return issues
            
        required_sections = self.REQUIRED_SECTIONS[template_type]
        content_lower = self.current_content.lower()
        
        for section in required_sections:
            if section == 'Front matter (YAML)':
                # Special check for YAML front matter
                if not self.current_content.startswith('---\n'):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="Command template must start with YAML front matter (---)",
                        suggestion="Add YAML front matter with name and description fields"
                    ))
            else:
                # Check for section heading
                section_pattern = re.escape(section.lower())
                if not re.search(rf'^#+\s*{section_pattern}', content_lower, re.MULTILINE):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Required section missing: {section}",
                        suggestion=f"Add section heading: ## {section}"
                    ))
                    
        return issues

    def _validate_placeholders(self) -> List[ValidationIssue]:
        """Validate placeholder patterns."""
        issues = []
        
        # Find all placeholders in the content
        placeholder_pattern = r'\[([^\]]+)\]'
        placeholders = re.findall(placeholder_pattern, self.current_content)
        
        for i, line in enumerate(self.current_lines, 1):
            line_placeholders = re.findall(placeholder_pattern, line)
            
            for placeholder in line_placeholders:
                full_placeholder = f'[{placeholder}]'
                
                # Check if it's a valid placeholder pattern
                is_valid = False
                for pattern_name, pattern in self.PLACEHOLDER_PATTERNS.items():
                    if re.match(pattern, full_placeholder):
                        is_valid = True
                        break
                
                if not is_valid:
                    # Check for common mistakes
                    if placeholder.isupper() and '_' in placeholder:
                        # Looks like a valid placeholder format
                        is_valid = True
                    elif 'NEEDS CLARIFICATION' in placeholder.upper():
                        # Special case for clarification markers
                        is_valid = True
                    else:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Unrecognized placeholder pattern: {full_placeholder}",
                            line_number=i,
                            suggestion="Ensure placeholder follows expected format like [FEATURE NAME] or [DATE]"
                        ))
                        
        return issues

    def _validate_command_metadata(self, template_type: str) -> List[ValidationIssue]:
        """Validate command template metadata."""
        issues = []
        
        if template_type != 'command':
            return issues
            
        if not self.current_content.startswith('---\n'):
            return issues  # Already caught in required sections
            
        # Extract YAML front matter
        try:
            yaml_end = self.current_content.find('\n---\n', 4)
            if yaml_end == -1:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="YAML front matter not properly closed (missing closing ---)"
                ))
                return issues
                
            yaml_content = self.current_content[4:yaml_end]
            metadata = yaml.safe_load(yaml_content)
            
            if not isinstance(metadata, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="YAML front matter must be a dictionary"
                ))
                return issues
                
            # Check required fields
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in metadata:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Required field missing in YAML front matter: {field}"
                    ))
                elif not isinstance(metadata[field], str) or not metadata[field].strip():
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Field '{field}' must be a non-empty string"
                    ))
                    
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Invalid YAML front matter: {e}"
            ))
            
        return issues

    def _validate_execution_flow(self) -> List[ValidationIssue]:
        """Validate execution flow sections."""
        issues = []
        
        # Look for execution flow sections
        execution_flow_pattern = r'##\s*Execution\s+Flow'
        matches = list(re.finditer(execution_flow_pattern, self.current_content, re.IGNORECASE))
        
        if not matches:
            # Execution flow is required for most templates
            if self._determine_template_type(self.current_file) in ['spec', 'plan', 'tasks']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Execution Flow section not found",
                    suggestion="Add ## Execution Flow section with step-by-step process"
                ))
        else:
            # Validate execution flow content
            for match in matches:
                section_start = match.end()
                
                # Find next section or end of document
                next_section = re.search(r'\n##\s+', self.current_content[section_start:])
                if next_section:
                    section_end = section_start + next_section.start()
                else:
                    section_end = len(self.current_content)
                    
                flow_content = self.current_content[section_start:section_end]
                
                # Check for code block with steps
                if '```' not in flow_content:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="Execution Flow should contain a code block with numbered steps",
                        suggestion="Add ``` code block with step-by-step process"
                    ))
                    
        return issues

    def _filter_and_sort_issues(self, issues: List[ValidationIssue]) -> List[ValidationIssue]:
        """Filter and sort validation issues by severity and line number."""
        # Sort by severity (errors first), then by line number
        severity_order = {
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.INFO: 2
        }
        
        return sorted(issues, key=lambda issue: (
            severity_order[issue.severity],
            issue.line_number or 0
        ))


def validate_template_file(template_path: Union[str, Path]) -> ValidationResult:
    """
    Convenience function to validate a single template file.
    
    Args:
        template_path: Path to template file
        
    Returns:
        ValidationResult
    """
    validator = TemplateValidator()
    return validator.validate_template(Path(template_path))


def validate_templates_directory(templates_dir: Union[str, Path]) -> Dict[str, ValidationResult]:
    """
    Convenience function to validate all templates in a directory.
    
    Args:
        templates_dir: Path to templates directory
        
    Returns:
        Dictionary mapping template names to validation results
    """
    validator = TemplateValidator()
    return validator.validate_template_directory(Path(templates_dir))
