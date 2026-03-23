# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the MiniSpec CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-03-23

### Changed

- **BREAKING: Specs directory moved** - Feature specs now live at top-level `specs/` instead of `.minispec/specs/`
- Updated all command templates, scripts (bash + powershell), and CLI to use new path
- OS-agnostic path matching in upgrade file classifier (Windows compatibility)

### Fixed

- Fixed `.minispec.minispec/` typos in `.claude/commands/` files (pre-existing)
- Enforce tasks file creation in `/minispec.tasks` command

## [0.1.0] - 2025-02-01

### Added

- **MiniSpec workflow** - Pair programming approach to AI-assisted development
- **New commands**: `/minispec.design`, `/minispec.tasks`, `/minispec.next`, `/minispec.walkthrough`, `/minispec.analyze`, `/minispec.status`, `/minispec.checklist`, `/minispec.validate-docs`
- **Interactive design conversations** - AI asks questions, presents trade-offs, engineer decides
- **Configurable chunk sizes** - Small (20-40), Medium (40-80), Large (80-150) lines
- **Living documentation** - Knowledge base with decisions, patterns, and modules
- **CLI rebranded** - `minispec` command with new banner and identity

### Changed

- **Directory structure** - `.specify/` → `.minispec/`
- **Spec files** - `spec.md` → `design.md`, `plan.md` → `tasks.md`
- **Command prefix** - `/speckit.*` → `/minispec.*`
- **Environment variable** - `SPECIFY_FEATURE` → `MINISPEC_FEATURE`

### Removed

- Old SpecKit commands: `/speckit.specify`, `/speckit.plan`, `/speckit.implement`, `/speckit.clarify`

---

## Pre-Fork History (SpecKit)

MiniSpec is forked from [SpecKit](https://github.com/github/spec-kit). For the complete SpecKit changelog, see the [original repository](https://github.com/github/spec-kit/blob/main/CHANGELOG.md).
