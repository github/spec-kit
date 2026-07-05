# Changelog

All notable changes to the Pipeline extension are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); this project adheres to Semantic Versioning.

## [1.0.0] - 2026-07-05

### Added

- Initial release.
- `speckit.pipeline.run` — chains `specify → clarify → plan → tasks → analyze → implement`
  into one guided invocation with a single interactive clarify gate and an
  analyze → fix → re-analyze loop (≤3 cycles) before implement.
- `speckit.pipeline.preview` — dry-run printer for the resolved phase plan.
- `--skip` / `--add` flags with a deterministic phase resolver (`scripts/resolve_phases.py`),
  strict validation, and dedicated exit codes (10–14).
- Insertable phases: `constitution` (before specify), `checklist` (after tasks).
- `--yes` unattended mode: answers the clarify gate in-place, halting before `plan`
  on a question too consequential to answer without a human.
- Bash + PowerShell wrappers over the Python resolver.
- Stdlib `unittest` suite covering default order, permutation invariance, and every exit code.
