# Changelog

All notable changes to Spec-Kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Template Validation System**: Comprehensive validation for all template types
  - New `specify validate` command to check template structure and format
  - Validation for required sections, placeholder patterns, and content consistency
  - Support for command template YAML front matter validation
  - Execution flow format checking (proper code blocks with steps)
  - Detailed error reporting with suggestions for fixes
  - Options to control warning display and error exit behavior
  - Support for validating individual files or entire directories

### Changed
- Updated README.md with template validation documentation and examples
- Enhanced CONTRIBUTING.md with template development guidelines
- Added PyYAML dependency for YAML front matter parsing

### Development
- Added comprehensive test suite for validation functionality
- Created validation module with extensible architecture for future enhancements
- Implemented rich CLI output with colored severity indicators and suggestions

## [0.0.2] - Previous Release

### Added
- Initial release of Specify CLI
- Project initialization with AI assistant selection
- Template downloading and extraction
- Basic project setup functionality

### Features
- Support for Claude Code, GitHub Copilot, and Gemini CLI
- Interactive AI assistant selection
- Git repository initialization
- Template-based project structure creation
