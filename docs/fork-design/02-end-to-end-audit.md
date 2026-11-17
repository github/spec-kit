# Tiny Notes end-to-end workflow audit

Date: 2026-11-17. All eleven installed skill procedures were exercised on a real local
sample, including application deployment, test execution, defect repair, redeployment
and cleanup. The final sample suite passed 22 tests; 55 focused toolkit tests passed.
No out-of-scope sample file-content changes were found across the 17 recorded stages.

## Execution method and limitation

The sample lives beside this checkout at `../spec-kit-sample-notes`. It was initialized
with this fork's CLI, the Codex integration and PowerShell scripts. It has no Git hooks,
optional presets or external services. The primary agent applied the installed
`.agents/skills/speckit-*/SKILL.md` procedures sequentially, rather than generating
prebuilt fixture artifacts or mocking command execution.

An initial independent `codex exec` probe used Codex CLI 0.161.0 and authenticated
successfully, but both shell and Node execution failed with
`registered Core launch requires an installed app`. Constitution made no file changes.
The CLI nevertheless returned exit code 0 with a blocked final response. **This was
not a successful command execution.** The automated CLI/bundled-engine path therefore
remains unverified on this host. No sandbox or approval restriction was weakened to
get around that failure; the remaining work used this session's existing tools.

A subsequent probe used the installed desktop application's own CLI executable
with the same workspace sandbox and reproduced that shell-launch failure. The fork
now rejects a zero-exit command without an invocation-specific completion receipt
and matching artifact hashes. The original false-success reproduction failed before
the fix; all 17 completion-verification tests pass after it. This prevents silent
advancement on the observed response, but does not repair the external launcher.

The sample operator selected the product details and clarification answers. The audit
does not attribute those choices to human answers or claim an interactive clarification
UI was tested. It verifies the skill procedures and actual effects of this run, not
that every future model or extension will obey the same boundaries.

## Sample and observations

Tiny Notes provides a local HTTP JSON interface to create, list and delete persistent
plain-text notes. The design uses one component, one logical asset, Python standard
libraries and SQLite. There is no browser UI or cloud infrastructure. The sample's
architecture and environment documents cite the primary sources used for technology,
OS compatibility and resource recommendations.

Before and after each stage, the observer recorded SHA-256 hashes of all sample files.
Subprocess arguments, stdout, stderr and exit codes were recorded separately from the
sample. Source edits were inspected against the task inventory. The observer's logs
and summaries are not artifacts written by the command under review.

| Command | Observed writes | Observed execution / responsibility result |
|---|---|---|
| constitution | constitution.md only | Resolved template and established governance; no product code |
| specify | spec.md, requirements checklist, feature pointer | Defined product scope; no stack or runtime operations |
| clarify | spec.md and two checklist markers | Resolved ordering and whitespace; preserved checklist text |
| architecture | architecture.md only | Selected component, libraries and interfaces; no OS/resources |
| environment | environment.md only | Recommended OS, resources and logical placement; no target inspection or installation |
| plan | plan.md only | Specified schema, API/errors and module design; no test plan or code |
| taskscode | tasks-code.md and helper-managed progress | Three coding tasks; independent modules then integration; no testing/deployment tasks |
| analyze | analysis.md only | Input hashes, feature pointer and progress unchanged; no automatic fixes |
| impcode | Three task-listed source files and progress | No application, build, lint or test execution; legal component/asset/task headers |
| deployment | deploy/ and deployment.md | Observed host/runtime, staged immutable files, started hidden local service and checked accessibility |
| test | tests/, bugs.md and test-report.md | Real unit/integration/end-to-end requests; production source and progress unchanged |

The test stages also changed disposable runtime data through the authorized local API.
They did not edit deployment configuration, staged code or service records. This is
explicitly distinguished from deployment work in the revised command contract.

The initial three coding tasks reached CODE_COMPLETE before any application execution
or tests. T001 was reopened through a fresh helper process while in progress; its
attempt count stayed at 1 and its partial source was preserved. Task T004 later repaired
the shared HTTP file without resetting T001–T003 or adding a testing completion gate.

## Defects and repairs

### Sample BUG-001: deeply nested JSON

A validly framed 2201-byte nested JSON body triggered an uncaught RecursionError and
closed the connection. The expected outcome was a clear HTTP 400 response without
data mutation. The failure reproduced in two runs. Test recorded the bug; taskscode
added T004; impcode expanded the parser error boundary. The same reproduction then
passed against both isolated source and the updated deployed release.

### Sample BUG-002: early wrong-content-type rejection

The first run observed Windows connection error 10053 instead of HTTP 415. A repeat
did not reproduce it, so the record identifies it as intermittent. The handler rejected
before consuming a correctly framed bounded request body. T004 moved content-type
rejection after the bounded body read. The final run passed 25 repeated requests on
an isolated server and 25 against the deployed service. No stronger reliability claim
is inferred from those repetitions.

### Workflow repair: stale deployed revision

After the code repair, the local tests passed but the deployed-source digest check
failed: the running service still contained the first release. The audit correctly
refused to credit that deployment to the repaired source. Deployment stopped the
verified old PID, retained its record/release/data, staged the new revision and started
it. The subsequent complete suite passed.

The reusable test command and report template now explicitly compare intended and
observed deployed identities. Local retests can proceed after coding; target-dependent
retests require deployment to refresh changed artifacts. Tests cannot silently redeploy
or apply successful old-release results to new code. The guide also clarifies that
authorized disposable test data may change through the product interface.

### Workflow repair: legacy task-path hint

Clarify's installed paths-only helper returned the legacy `TASKS=tasks.md` field.
Its prompt still suggested retaining that field for later chained work. The prompt
now consumes only its own feature/spec fields and directs later commands to their
own context resolution, preventing confusion with `tasks-code.md`. The legacy helper
output remains available to existing optional consumers.

## Results and evidence

| Run | Scope | Result |
|---|---|---|
| 01 | Initial sample suite | 18 passed, 2 errors |
| 02 | HTTP reproductions | 8 passed, 1 error; deep JSON reproduced |
| 03 | Repaired source with old deployment | 20 passed, 1 revision mismatch; deployed verification blocked |
| 04 | Repaired and redeployed sample | 22 passed, no failures or skips |
| Toolkit regression | Helper behavior and bundled workflow | 55 passed |

The machine-readable [boundary evidence](evidence/tiny-notes-run.json) records created,
modified and deleted paths, subprocess invocations and results for all 17 stages.
Raw observer logs and before/after hashes are retained locally under
`.venv/e2e-audit/`. The sample retains `tests/evidence/run-*.log`, its test report,
bug history, task/progress records and both deployed release manifests.

Final release: `378bcb5920b851a7062ce501f31b0335ca7895561b9b837784edc53dbbca9137`.
Windows PowerShell 5.1.26100.9818 executed the helpers and deployment inspection/cleanup.
The actual service ran at `127.0.0.1:8765`. Cleanup verified its executable and release
identity, stopped PID 4388 and observed no remaining listener for that process.
No background service, global package change or cloud resource remains.

To inspect or rerun the preserved sample, see its `specs/001-tiny-notes/deployment.md`
for the recorded runtime, restart and rollback commands. From the sample root, with
the deployment running, execute:

```powershell
python -B -m unittest discover -s tests -v
```

The source/release identity case intentionally fails if a deployment is stale or absent.
The audit is a local demonstration, not production hardening, performance certification
or proof of an automatically enforced agent sandbox.
