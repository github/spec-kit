# Changelog

All notable changes to the Guided SDD Pipeline workflow will be documented in this file.

## [1.0.0] - 2026-07-08

### Added
- Initial release of the Guided SDD Pipeline workflow
- Support for optional constitution phase (`with_constitution`)
- Support for optional checklist phase (`with_checklist`)  
- Support for clarify gate with approval/rejection options (`skip_clarify`)
- Single pre-implement analyze pass (cross-artifact consistency check)
- Post-implement convergence loop via `speckit.converge` (up to 3 cycles)
- Integration-agnostic design supporting Claude, Copilot, Gemini, OpenCode
- Full workflow state persistence for resumable runs
- Comprehensive documentation and usage examples
