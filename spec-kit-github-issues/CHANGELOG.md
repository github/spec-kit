# Changelog

All notable changes to the GitHub Issues Integration extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-12

### Added

- Initial release of GitHub Issues Integration extension
- `/speckit.github-issues.import` command to import GitHub Issues and generate spec.md
- `/speckit.github-issues.sync` command to sync spec artifacts with issue updates
- `/speckit.github-issues.link` command to add bidirectional traceability
- Configuration file support for customizing behavior
- Automatic parsing of issue sections (problem, solution, alternatives)
- Comment preservation in spec Discussion Notes
- Label integration as spec tags
- Issue state tracking (open/closed)
- Metadata file (`.issue-link`) for tracking linked issues
- Comprehensive documentation and examples

### Features

- Import issues from any GitHub repository
- Support for both `owner/repo#123` and `#123` formats
- Automatic detection of current repository
- Bidirectional linking between specs and issues
- Sync detection based on issue update timestamps
- Batch sync for all linked issues
- Selective sync for specific features or issues
- User confirmation before applying updates
- Graceful error handling and permission checks

[1.0.0]: https://github.com/Fatima367/spec-kit-github-issues/releases/tag/v1.0.0
