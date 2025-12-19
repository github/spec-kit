# Changelog

All notable changes to the SpecLite CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.3] - 2025-12-19

### Changed

- Added support for multiple AI agents in a project:
  - `speclite init --ai` accepts comma-separated agents and install templates for each selection.
  - The interactive UI supports multi-select for AI agents (defaults to none).

## [0.0.2] - 2025-12-19

### Changed

- Split template packaging into a core archive plus agent-specific archives, and install both during init.

## [0.0.1] - 2025-12-17

### Changed

- Started SpecLite as a fork of GitHub Spec Kit, taking the latest code as of https://github.com/github/spec-kit/commit/9111699cd27879e3e6301651a03e502ecb6dd65d (Spec Kit version 0.0.22 in `CHANGELOG.md`, released in https://github.com/github/spec-kit/releases/tag/v0.0.90). Will add new updates from Spec Kit from time to time.
