# Changelog

All notable changes to the Approval Gates extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-05

### Added

- Initial release of Approval Gates extension
- `speckit.approval-gates.status` command to display approval gates configuration
- Support for per-phase approval requirements (specify, plan, tasks, implement, constitution)
- Configurable approval requirements:
  - `enabled` — Toggle approval requirement for a phase
  - `min_approvals` — Minimum number of approvals needed
  - `requires` — List of roles who can approve
  - `description` — Description of what the gate enforces
- `approval-gates-config.template.yml` template for team customization
- Hook integration: After `/speckit.tasks`, optional prompt to check approval gates
- Comprehensive documentation with configuration guide and examples
- Support for optional configuration (teams can use extension without configuring gates)
