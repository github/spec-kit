# Fork engineering verification

Date: 2026-11-17. Development version: `2.0.0.dev0`.

The eleven-command implementation, durable coding progress, integration migration,
bundled workflow, optional hooks and package contents are implemented. The workflow
runner now requires a current completion receipt and matching output hashes before
advancing a bundled command. The zero-exit blocked-response regression failed before
the fix and passes after it.

## Evidence

- All eleven installed skill procedures were exercised on Tiny Notes, including
  actual local deployment, bug repair and redeployment. Its final suite passed 22
  tests. See the [end-to-end audit](02-end-to-end-audit.md) for command boundaries.
- Final focused workflow verification: 72 passed, including 17 completion-receipt
  cases, 24 bundled orchestration cases and 31 helper/progress cases. The helper
  suite exercised Windows PowerShell 5.1 and Git Bash.
- Broad Windows run: 15,064 passed, 1,379 skipped and 66 failed. The failures exposed
  37 missed migration expectations or catalog metadata inconsistencies, which were
  corrected. The affected-area rerun then passed 2,444 tests with 33 platform skips
  and no failures. It covered catalog/update delivery, integration lifecycle,
  installed adapters, presets, bundle validation, artifact APIs and template rendering.
- Of the remaining 29 broad-run failures, 28 reproduced on an unchanged `main`
  checkout: 21 shell-based community-download cases, five cases needing Windows
  symlink privileges and two workflow composition cases. The remaining file-handle
  failure passed in isolation; running that whole unchanged test module reproduced
  a related nondeterministic extra-handle assertion. The fork module rerun likewise
  reported one extra-handle assertion, 201 passes and seven skips. These are retained
  as upstream/host limitations, not presented as passing tests.
- Ruff and changed-guide Markdown lint passed. The existing changelog and extension
  README example retain unrelated historical Markdown lint findings. Diff whitespace
  checks passed.
- The wheel built successfully. An isolated installation initialized exactly eleven
  Codex skills, all six new page templates and the current Python helpers. The built
  package contains the completion verifier and matching bundled manifest versions.

The broad run used the checkout's `.venv/Scripts/python.exe -m pytest tests -q -n 8`
with `-k 'not symlink and not shared_template_refresh_preflights_before_writing and
not shared_infra_install_buckets_unsafe_destinations_and_continues'`. Those exclusions
avoid tests already known to need unavailable Windows symlink privileges; five tests
with other names still exposed that same restriction. Full Linux/macOS validation
was intentionally omitted at the user's request.

Local detailed logs are retained under `.venv/final-*.log`. The unchanged baseline
comparison used the original Git HEAD's source and tests from `.venv/final-baseline`.

## Remaining external verification

The local Codex CLI authenticates but cannot start its execution tools:
`registered Core launch requires an installed app`. The installed desktop CLI
reproduced the same failure. No sandbox or approval settings were weakened.
Consequently, unattended execution of the entire bundled workflow remains unverified
on this host. Direct skill execution, deterministic helper behavior, runner failure
handling and package installation were verified separately. Completion receipts do
not prove semantic correctness or enforce an operating-system sandbox.

This is an engineering branch and development build, not a published production
release. Full Linux/macOS testing and a production deployment are outside this pass.
