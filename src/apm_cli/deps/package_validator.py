"""APM package structure validation."""

from pathlib import Path
from typing import List, Optional
import os

from ..models.apm_package import (
    ValidationResult,
    APMPackage,
    validate_apm_package as base_validate_apm_package
)


class PackageValidator:
    """Validates APM package structure and content."""
    
    def __init__(self):
        """Initialize the package validator."""
        pass
    
    def validate_package(self, package_path: Path) -> ValidationResult:
        """Validate that a directory contains a valid APM package.
        
        Args:
            package_path: Path to the directory to validate
            
        Returns:
            ValidationResult: Validation results with any errors/warnings
        """
        return base_validate_apm_package(package_path)
    
    def validate_package_structure(self, package_path: Path) -> ValidationResult:
        """Validate APM package directory structure.
        
        Checks for required files and directories:
        - apm.yml at root
        - .apm/ directory with primitives
        
        Args:
            package_path: Path to the package directory
            
        Returns:
            ValidationResult: Detailed validation results
        """
        result = ValidationResult()
        
        if not package_path.exists():
            result.add_error(f"Package directory does not exist: {package_path}")
            return result
        
        if not package_path.is_dir():
            result.add_error(f"Package path is not a directory: {package_path}")
            return result
        
        # Check for apm.yml
        apm_yml = package_path / "apm.yml"
        if not apm_yml.exists():
            result.add_error("Missing required file: apm.yml")
            return result
        
        # Try to parse apm.yml
        try:
            package = APMPackage.from_apm_yml(apm_yml)
            result.package = package
        except (ValueError, FileNotFoundError) as e:
            result.add_error(f"Invalid apm.yml: {e}")
            return result
        
        # Check for .apm directory
        apm_dir = package_path / ".apm"
        if not apm_dir.exists():
            result.add_error("Missing required directory: .apm/")
            return result
        
        if not apm_dir.is_dir():
            result.add_error(".apm must be a directory")
            return result
        
        # Check for primitive content
        primitive_types = ['instructions', 'chatmodes', 'contexts', 'prompts']
        has_primitives = False
        
        for primitive_type in primitive_types:
            primitive_dir = apm_dir / primitive_type
            if primitive_dir.exists() and primitive_dir.is_dir():
                md_files = list(primitive_dir.glob("*.md"))
                if md_files:
                    has_primitives = True
                    # Validate each primitive file
                    for md_file in md_files:
                        self._validate_primitive_file(md_file, result)
        
        if not has_primitives:
            result.add_warning("No primitive files found in .apm/ directory")
        
        return result
    
    def _validate_primitive_file(self, file_path: Path, result: ValidationResult) -> None:
        """Validate a single primitive file.
        
        Args:
            file_path: Path to the primitive markdown file
            result: ValidationResult to add warnings/errors to
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            if not content.strip():
                result.add_warning(f"Empty primitive file: {file_path.name}")
        except Exception as e:
            result.add_warning(f"Could not read primitive file {file_path.name}: {e}")
    
    def validate_primitive_structure(self, apm_dir: Path) -> List[str]:
        """Validate the structure of primitives in .apm directory.
        
        Args:
            apm_dir: Path to the .apm directory
            
        Returns:
            List[str]: List of validation warnings/issues found
        """
        issues = []
        
        if not apm_dir.exists():
            issues.append("Missing .apm directory")
            return issues
        
        primitive_types = ['instructions', 'chatmodes', 'contexts', 'prompts']
        found_primitives = False
        
        for primitive_type in primitive_types:
            primitive_dir = apm_dir / primitive_type
            if primitive_dir.exists():
                if not primitive_dir.is_dir():
                    issues.append(f"{primitive_type} should be a directory")
                    continue
                
                # Check for markdown files
                md_files = list(primitive_dir.glob("*.md"))
                if md_files:
                    found_primitives = True
                    
                    # Validate naming convention
                    for md_file in md_files:
                        if not self._is_valid_primitive_name(md_file.name, primitive_type):
                            issues.append(f"Invalid primitive file name: {md_file.name}")
                
        if not found_primitives:
            issues.append("No primitive files found in .apm directory")
            
        return issues
    
    def _is_valid_primitive_name(self, filename: str, primitive_type: str) -> bool:
        """Check if a primitive filename follows naming conventions.
        
        Args:
            filename: The filename to validate
            primitive_type: Type of primitive (instructions, chatmodes, etc.)
            
        Returns:
            bool: True if filename is valid
        """
        # Basic validation - should end with .md
        if not filename.endswith('.md'):
            return False
        
        # Should not contain spaces (prefer hyphens or underscores)
        if ' ' in filename:
            return False
        
        # For specific types, check expected suffixes using a mapping
        name_without_ext = filename[:-3]  # Remove .md
        suffix_map = {
            'instructions': '.instructions',
            'chatmodes': '.chatmode',
            'contexts': '.context',
            'prompts': '.prompt',
        }
        expected_suffix = suffix_map.get(primitive_type)
        if expected_suffix and not name_without_ext.endswith(expected_suffix):
            return False
        
        return True
    
    def get_package_info_summary(self, package_path: Path) -> Optional[str]:
        """Get a summary of package information for display.
        
        Args:
            package_path: Path to the package directory
            
        Returns:
            Optional[str]: Summary string or None if package is invalid
        """
        validation_result = self.validate_package(package_path)
        
        if not validation_result.is_valid or not validation_result.package:
            return None
        
        package = validation_result.package
        summary = f"{package.name} v{package.version}"
        
        if package.description:
            summary += f" - {package.description}"
        
        # Count primitives
        apm_dir = package_path / ".apm"
        if apm_dir.exists():
            primitive_count = 0
            for primitive_type in ['instructions', 'chatmodes', 'contexts', 'prompts']:
                primitive_dir = apm_dir / primitive_type
                if primitive_dir.exists():
                    primitive_count += len(list(primitive_dir.glob("*.md")))
            
            if primitive_count > 0:
                summary += f" ({primitive_count} primitives)"
        
        return summary