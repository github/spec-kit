# Test Case Intake Contract

Required test-case intake artifacts and readiness gates. Runtime agents or external intake tools extract existing behavioral evidence before downstream SDD workflows project scenarios, assertions, fixtures, and coverage gaps into specifications.

Intake does not generate requirements. It preserves all reachable test sources, stable source refs, checksums or retrieval metadata, and schema-required behavioral evidence that SDD `specify` can consume accurately.

The machine-readable structures in this contract are enforced by JSON Schemas under `templates/schemas/` before readiness-specific validation runs. Field lists in this document are semantic summaries; the JSON Schemas are canonical for required fields, types, and enums.

Tests are evidence, not the only source of truth. This contract preserves what existing tests prove while keeping inferred product intent explicit.

## Supported Sources

`source-manifest.yaml` must identify the original test source and preserve source integrity.

Required source fields:

- source_type: code|gherkin|spreadsheet|test_management|issue|mixed
- source_files:
  - path:
  - mime_type:
  - byte_size:
  - sha256:
  - role: original|export|attachment|snapshot
- source_integrity_complete:
- captured_at:
- capture_method:
- framework_or_format:
- execution_scope:

Source-specific requirements:

- Automated test files must record framework, file paths, test names, skipped markers, fixtures, mocks, and execution status; unavailable values must be represented by explicit fixture, assertion, or coverage gaps.
- Gherkin sources must record feature, background, scenario, examples, tags, and step coverage.
- Spreadsheets or test management exports must record sheet or suite names, row IDs, case IDs, priorities, statuses, and imported range coverage.
- Issue or bug repro sources must record stable URLs, repro steps, expected and actual behavior, environment, and linked artifacts.
- Remote source refs may use a stable URL as `source_files[].path`; when no local snapshot exists, record retrieval metadata and mark unavailable checksum fields as explicit gaps instead of pretending integrity is complete.
- Mixed source packets must preserve source precedence and record duplicate or conflicting scenarios.

## Vertical Scenario Coverage

- Unit or component tests: capture subject under test, setup, inputs, assertions, mocks, and boundary cases.
- Integration or API tests: capture endpoints, contracts, fixtures, state transitions, permissions, and external dependencies.
- End-to-end tests: capture user journey, actor, preconditions, actions, expected outcomes, screenshots or traces, and environment assumptions.
- Manual QA cases: capture case IDs, steps, expected results, priority, test data, platform matrix, and pass or fail history.
- Regression or bug repros: capture trigger, affected version, expected behavior, actual behavior, assertion gap, and linked fix context.

## Test Case Intake Facts

`test-case-intake.yaml` must normalize existing behavioral evidence into engineering input.

Required top-level fields:

- test_case_intake_complete:
- source_refs_complete:
- scenario_count:
- assertions_complete:
- fixture_evidence_complete:
- coverage_gaps_recorded:
- assertion_gaps:
- fixture_or_test_data_gaps:
- coverage_gaps:
- flaky_or_skipped_cases:
- blocker_lint_errors:
- scenarios:

Each scenario must include:

- id:
- category: unit|component|integration|api|e2e|manual|regression|bug_repro|performance|accessibility|security
- scenario:
- source_refs:
- evidence_type: observed|inferred|missing|out_of_scope
- confidence: low|medium|high
- confidence_rationale:
- actors:
- preconditions:
- actions:
- expected_outcomes:
- assertions:
- fixtures_or_test_data:
- coverage_signal:

When evidenced by the source, include provider-neutral optional fields:

- tags:
- priority:
- risk:
- status:
- skipped_or_flaky_reason:
- related_requirement_refs:
- blockers:

## Readiness Gate

Test-case intake is ready only when:

- source_integrity_complete: true
- test_case_intake_complete: true
- source_refs_complete: true
- scenario_count greater than 0 and equal to the number of records in `scenarios`
- when `assertions_complete: true`, scenario assertions are recorded; when false, `assertion_gaps` records the reason and source refs
- fixtures, mocks, or test data assumptions are recorded when relevant
- coverage gaps and flaky or skipped cases are explicit
- no blocker lint errors exist

## Blocker Lint Errors

- TEST_SOURCE_MANIFEST_MISSING
- TEST_SOURCE_TYPE_UNSUPPORTED
- TEST_SOURCE_FILE_MISSING
- TEST_SOURCE_HASH_MISMATCH
- TEST_SOURCE_INTEGRITY_INCOMPLETE
- TEST_CASE_INTAKE_MISSING
- TEST_SCENARIOS_UNTRACEABLE
- TEST_ASSERTIONS_MISSING
- TEST_FIXTURE_EVIDENCE_MISSING
- TEST_COVERAGE_GAPS_MISSING
- TEST_READY_WITHOUT_EVIDENCE
- TEST_EVIDENCE_PACKET_MISSING
- TEST_BLOCKER_LINT_ERRORS
- TEST_SCHEMA_INVALID

## Gap Rules

Record a gap instead of passing silently when test evidence is missing, untraceable, skipped, flaky, obsolete, duplicated, contradictory, or too implementation-specific to support product behavior. Inferred product intent must remain marked `evidence_type: inferred` or `[NEEDS CLARIFICATION]`.

## Evidence Packet Metadata

`evidence-packet.md` must start with YAML front matter:

- ready_gate: `PASS|BLOCKED`
- blockers:
- source_ref_count:
- extracted_item_count:
- generated_at:

Human-readable sections may summarize the same records, but readiness metadata is validated from the front matter when present.
