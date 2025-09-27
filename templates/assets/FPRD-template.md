# FPRD-<ID>: <Feature PRD Title>
**Linked:** PPRD-<ID>, EP-<ID>

## 1. Problem & Outcome
- Problem statement: <1–2 paragraphs>
- Outcome metric(s): <name> — baseline=<x>, target=<y>, measurement window=<w>

## 2. Scope (MoSCoW) & Non-Goals
- Must: <...>
- Should: <...>
- Could: <...>
- Won’t (this cycle): <...>
- Non-Goals: <copy from PPRD and add>

## 3. User Stories (SS-###) & Acceptance Criteria (summary)
- SS-<ID>: <title> — key ACs: <bullets>
- SS-<ID>: ...

## 4. UX Notes
- Primary flow(s), empty/error/loading states, accessibility checks

## 5. Technical Notes
- Data model / schema changes
- API contracts (I/O schemas, versioning)
- Dependencies (services, approvals)
- Performance targets (e.g., p95 latency)

## 6. Tests & Telemetry
- Tests to add: unit / integration / e2e / contract / data-quality
- Telemetry events: <names>, schema (fields, types, required), when emitted
- Dashboard(s): <path or id>, alerts: <thresholds>

## 7. Feature Flags & Rollout
- Flag name: <product.area.flag_name> (default OFF)
- Exposure plan: <phased rollout & success/fail gates>
- Rollback: <how to revert safely>

## 8. Risks & Assumptions
- <enumerate>

## 9. Definition of Ready (DoR) — must be TRUE before starting
- [ ] Outcome metric has baseline & target
- [ ] ACs written for each Story; edge cases captured
- [ ] Telemetry spec & dashboard stub defined
- [ ] Flag strategy & rollback documented
- [ ] Dependencies identified / mocks available

## 10. Definition of Done (DoD)
- [ ] Tests pass; coverage acceptable
- [ ] Telemetry events emit and appear in dashboard
- [ ] Flag default OFF; rollout plan executed or staged
- [ ] Docs & runbooks updated; RTM row marked Done
