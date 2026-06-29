# Changelog

## [0.1.3] - 2026-06-29

### Added

- Added `/speckit.intake.figma2htmlssot` for Figma-derived HTML visual SSOT bundles with component-state, page, asset, viewport, screenshot, and coverage evidence.
- Added HTML SSOT schemas and `validate_html_ssot.py` for bundle artifact, Figma node, component-state, page, asset, viewport, visual-diff, and known-gap readiness checks.
- Added bounded visual inference statuses for irregular Figma and visual-design sources, including `candidate` and `unsupported` claim handling.
- Added readiness blocking for unbounded visual inference and unsupported visual claims.

## [0.1.2] - 2026-06-23

### Changed

- Added release installation and runtime dependency documentation.
- Shortened manifest description and reduced tags for community catalog submission.

## [0.1.1] - 2026-06-23

### Changed

- Added community catalog metadata for category and effect.

## [0.1.0] - 2026-06-23

### Added

- Initial Spec Kit extension manifest.
- Intake commands for visual design, PRD, and test-case sources.
- Intake contracts and evidence packet templates for visual design, PRD, and test-case sources.
- Local readiness validators for PRD, test-case, visual design, and Figma metadata intake artifacts.

### Changed

- Repositioned the extension as the generic `intake` extension with domain commands for visual design, PRD, and test-case sources.
- Expanded the extension goal from Figma-only metadata intake to visual design requirement intake.
- Added support contracts for image, PDF, Markdown, and Figma sources across low, medium, and high-fidelity drafts.
- Added readiness concepts for source integrity, visual requirement traceability, fidelity rules, and delivery parity planning.
- Updated the validator to support generic visual sources while preserving Figma metadata parity validation.
