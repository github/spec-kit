# Changelog

All notable changes to the Evaluator Contract extension will be documented in this file.

## [1.0.0] - 2026-09-01

### Added
- Initial release of the Evaluator Contract extension
- JSON Schema for evaluator results (6 outcomes, 14 finding kinds, 5 evidence kinds, 6 uncertainty levels)
- 4 commands: `speckit.evaluator.run`, `.compose`, `.report`, `.route`
- 3 parity scripts: Python, Bash, PowerShell
- 4 lifecycle hooks: `after_specify`, `after_plan`, `after_tasks`, `after_implement`
- Model routing: recommends budget/standard/premium tier per phase
- Composition: strict/majority/optimistic strategies with contradiction detection
- Quick-start demo: `python examples/demo.py`
- Token-economic benchmark suite with Monte Carlo simulation
- 70 tests with 0 regressions against spec-kit test suite