# Blueprint: URL Shortener Service

**Short Name**: `url-shortener`
**Date**: 2026-05-06
**Status**: Draft
**Source Idea**: > "I want a small URL shortening service. Users paste a long URL, get back a short code, and visiting the short code redirects them. Track click counts so I can see which links are popular. Personal project, single Linux server, won't get more than a few thousand links."

---

## 1. Constitutional Gates

- [ ] **Library-First**: URL-shortening logic and click-tracking each live as standalone libraries.
- [ ] **CLI Interface**: A `urlshort` CLI exposes shorten, lookup, and stats commands with JSON output.
- [ ] **Test-First (NON-NEGOTIABLE)**: Tests written and failing before any implementation.
- [ ] **Simplicity**: ≤3 projects (single project here: `src/` + `tests/`).
- [ ] **Anti-Abstraction**: Use SQLite directly via the standard driver; no ORM.
- [ ] **Integration-First Testing**: Integration tests use a real SQLite file; contract tests for HTTP endpoints precede implementation.

---

## 2. User Scenarios

### User Story 1 — Shorten a URL and visit it (Priority: P1) — MVP

A user pastes a long URL into a form, receives a short code, and visiting the short code redirects them to the original URL.

**Why this priority**: Without this, the service has no reason to exist. This is the entire core loop.

**Independent Test**: From a clean install, submit `https://example.com/very/long/path` to the shorten endpoint, receive a code, request `/<code>`, and verify a 302 redirect to the original URL.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** a user submits a valid URL to the shorten endpoint, **Then** the response includes a unique short code of 6-8 characters.
2. **Given** a previously shortened code, **When** a user visits `/<code>`, **Then** they receive a 302 redirect to the original URL.
3. **Given** an invalid URL (e.g., not http/https), **When** a user submits it, **Then** the response is a 400 with a clear error message.

---

### User Story 2 — See click counts per short code (Priority: P2)

A user looks up the click count for any short code they created.

**Why this priority**: Popularity tracking is the user's stated goal but is not on the critical redirect path; ship redirects first.

**Independent Test**: Create a short code, visit it 5 times, query the stats endpoint for that code, verify the count is 5.

**Acceptance Scenarios**:

1. **Given** a short code has been visited N times, **When** the user requests its stats, **Then** the response shows `clicks: N`.
2. **Given** an unknown short code, **When** the user requests its stats, **Then** the response is a 404.

---

### User Story 3 — List all shortened URLs (Priority: P3)

A user can list every short code they've created with original URL and click count.

**Why this priority**: Convenience for a personal-use tool; not required for either core loop or stats lookup.

**Independent Test**: Create three codes, list them, verify all three appear with correct original URLs and counts.

**Acceptance Scenarios**:

1. **Given** at least one code exists, **When** the user requests the list endpoint, **Then** the response is a JSON array of `{code, original_url, clicks, created_at}` objects ordered newest-first.

---

## 3. Edge Cases

- What happens when the same long URL is submitted twice? (Return existing code or generate new one — see FR-005.)
- What happens on a short-code collision when generating? (Retry with a new code; cap retries at 5 then 500.)
- What happens when a redirect target becomes invalid (DNS fails)? (Out of scope — service still issues the redirect; the browser handles failure.)
- What happens at scale beyond stated assumptions? (Out of scope; stated cap is "few thousand links".)

---

## 4. Functional Requirements

- **FR-001**: System MUST accept a URL via an HTTP POST endpoint and return a unique short code.
- **FR-002**: System MUST validate that submitted URLs use the `http` or `https` scheme; reject all others with 400.
- **FR-003**: System MUST redirect requests for `/<code>` to the original URL with HTTP 302 when the code exists.
- **FR-004**: System MUST return HTTP 404 for unknown short codes.
- **FR-005**: System MUST return the existing short code when a previously submitted URL is submitted again (no duplicate codes for the same URL).
- **FR-006**: System MUST increment a click counter every time a short code is resolved successfully.
- **FR-007**: System MUST expose a stats endpoint returning `{code, original_url, clicks, created_at}` for a given code.
- **FR-008**: System MUST expose a list endpoint returning all codes ordered by `created_at` descending.
- **FR-009**: System MUST persist data across restarts.

---

## 5. Key Entities

- **Link**: A single shortened URL. Holds the short code, the original URL, the creation timestamp, and the click count.

---

## 6. Success Criteria

- **SC-001**: A user can shorten a URL and see the redirect work in under 5 seconds end-to-end on a fresh install.
- **SC-002**: The redirect path returns within 100ms at the 95th percentile under a load of 100 requests/second.
- **SC-003**: Click counts are accurate to within 1% under concurrent load (100 simultaneous redirects of the same code).
- **SC-004**: The service survives restart without losing any links or click counts.

---

## 7. Assumptions

- Single-user (or trusted multi-user) personal service; no authentication required.
- Single Linux server; no horizontal scaling.
- Total link count stays under 10,000 (well below the SQLite practical ceiling).
- Short codes are case-sensitive base62 strings, 6-8 characters.
- Default retention is indefinite; no expiry mechanism in this slice.

---

## 8. Technical Context

| Field                   | Value                                  |
|-------------------------|----------------------------------------|
| Language / Version      | Python 3.12                            |
| Primary Dependencies    | FastAPI, uvicorn, sqlite3 (stdlib)     |
| Storage                 | SQLite, single file `data/links.db`    |
| Testing Framework       | pytest, httpx (test client)            |
| Target Platform         | Linux server (any distro with Python)  |
| Project Type            | Single project (web service + CLI)     |
| Performance Goals       | 100 req/s sustained on the redirect path |
| Constraints             | <100ms p95 redirect; single binary deploy preferred |
| Scale / Scope           | <10,000 total links, <1M total clicks  |

---

## 9. Project Structure

### Documentation (this feature)

```text
specs/001-url-shortener/
└── BLUEPRINT.md
```

### Source Code (repository root)

```text
src/
├── models/
│   └── link.py
├── services/
│   ├── shortener.py
│   └── stats.py
├── cli/
│   └── urlshort.py
└── api/
    └── routes.py

tests/
├── contract/
│   ├── test_shorten_endpoint.py
│   ├── test_redirect_endpoint.py
│   ├── test_stats_endpoint.py
│   └── test_list_endpoint.py
├── integration/
│   ├── test_shorten_and_redirect.py
│   ├── test_click_counting.py
│   └── test_list_links.py
└── unit/
    └── test_code_generation.py
```

**Structure Decision**: Single-project layout. Service is small enough that splitting backend/CLI into separate projects would violate the Simplicity gate.

---

## 10. Tasks

### Phase 1 — Setup

- [ ] T001 Create project structure per §9 (src/, tests/, data/)
- [ ] T002 Initialize Python 3.12 project with pyproject.toml; add FastAPI, uvicorn, pytest, httpx
- [ ] T003 [P] Configure ruff (lint) and black (format)
- [ ] T004 [P] Add Makefile with `test`, `lint`, `run` targets

### Phase 2 — Foundational

- [ ] T005 Create SQLite schema migration in src/db/schema.sql (links table: code TEXT PRIMARY KEY, original_url TEXT, clicks INTEGER, created_at TEXT)
- [ ] T006 [P] Implement DB connection helper in src/db/connection.py
- [ ] T007 [P] Implement structured logging in src/logging_config.py
- [ ] T008 Wire FastAPI app skeleton in src/api/app.py with health endpoint

**Checkpoint**: Foundation ready — user-story phases can begin.

### Phase 3 — User Story 1: Shorten and visit (P1) 🎯 MVP

**Goal**: Submit a URL, receive a short code, visit the code, get redirected.
**Independent Test**: See §2 US1.

#### Tests for User Story 1

- [ ] T009 [P] [US1] Contract test for POST /shorten (valid URL → 200 + code) in tests/contract/test_shorten_endpoint.py
- [ ] T010 [P] [US1] Contract test for POST /shorten (invalid URL → 400) in tests/contract/test_shorten_endpoint.py
- [ ] T011 [P] [US1] Contract test for GET /<code> (known → 302) in tests/contract/test_redirect_endpoint.py
- [ ] T012 [P] [US1] Contract test for GET /<code> (unknown → 404) in tests/contract/test_redirect_endpoint.py
- [ ] T013 [P] [US1] Integration test for shorten-then-redirect happy path in tests/integration/test_shorten_and_redirect.py

#### Implementation for User Story 1

- [ ] T014 [P] [US1] Create Link model in src/models/link.py
- [ ] T015 [US1] Implement code generation (base62, 6-8 chars, collision retry) in src/services/shortener.py (depends on T014)
- [ ] T016 [US1] Implement POST /shorten route in src/api/routes.py (depends on T015)
- [ ] T017 [US1] Implement GET /<code> redirect route in src/api/routes.py (depends on T015)
- [ ] T018 [US1] Add URL scheme validation and 400 handling

**Checkpoint**: US1 fully functional — service can shorten and redirect.

### Phase 4 — User Story 2: Click counts (P2)

**Goal**: Read click counts per short code.
**Independent Test**: See §2 US2.

#### Tests for User Story 2

- [ ] T019 [P] [US2] Contract test for GET /stats/<code> in tests/contract/test_stats_endpoint.py
- [ ] T020 [P] [US2] Integration test for click counter under concurrent load in tests/integration/test_click_counting.py

#### Implementation for User Story 2

- [ ] T021 [US2] Add atomic click-count increment to GET /<code> handler in src/api/routes.py (modifies T017's handler)
- [ ] T022 [US2] Implement stats lookup in src/services/stats.py
- [ ] T023 [US2] Implement GET /stats/<code> route in src/api/routes.py

**Checkpoint**: US2 functional — stats reflect real visit counts.

### Phase 5 — User Story 3: List all (P3)

**Goal**: List every link.
**Independent Test**: See §2 US3.

#### Tests for User Story 3

- [ ] T024 [P] [US3] Contract test for GET /links in tests/contract/test_list_endpoint.py
- [ ] T025 [P] [US3] Integration test for list ordering in tests/integration/test_list_links.py

#### Implementation for User Story 3

- [ ] T026 [US3] Implement list query in src/services/stats.py
- [ ] T027 [US3] Implement GET /links route in src/api/routes.py

**Checkpoint**: All three stories independently functional.

### Phase 6 — Polish & Cross-Cutting

- [ ] T028 [P] Implement urlshort CLI wrapping shorten/stats/list in src/cli/urlshort.py
- [ ] T029 [P] Write README.md with quickstart matching §6 SC-001
- [ ] T030 Run load test to verify SC-002 (100 req/s, <100ms p95)
- [ ] T031 Add structured access logging on the redirect path

---

## 11. Dependencies & Execution Order

### Phase Dependencies

- Setup (1) → Foundational (2) → US1 / US2 / US3 (3-5) → Polish (6).
- US2 modifies a file owned by US1 (routes.py); US1 must complete first or US2 must merge into US1's handler carefully.

### User Story Dependencies

- US1: independent.
- US2: shares routes.py with US1; sequence US1 → US2.
- US3: shares routes.py with US1 and US2; sequence after US2.

### Parallel Opportunities

- All `[P]` tests within a story can run concurrently.
- T014 and T015 cannot — T015 imports the Link model.
- Polish tasks T028 and T029 can run in parallel.

---

## 12. Implementation Strategy

### MVP First

1. Phases 1-3.
2. Validate US1 against acceptance scenarios.
3. Ship.

### Incremental Delivery

1. Foundation + US1 → working shortener.
2. + US2 → analytics.
3. + US3 → admin convenience.
4. + Polish → CLI and ops readiness.

### Parallel Team Strategy

Single-developer project; sequential execution is fine.

---

## 13. Complexity Tracking

> No gate violations. Section intentionally empty.

---

## 14. Open Questions

> No unresolved clarifications. Section intentionally empty.

---

## 15. Change Log

| Date       | Author | Change                                  |
|------------|--------|-----------------------------------------|
| 2026-05-06 | skill  | Initial blueprint generated by skill.   |
