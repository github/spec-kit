# Tasks: Company Standards & AGENTS.md

**Feature**: `001-company-standards`
**Status**: Ready for Implementation

## Phase 1: Setup

- [x] T001 Create directory structure `templates/company-standards/code-style`

## Phase 2: Foundational (Agent Context Standardization)

**Goal**: Standardize on `AGENTS.md` as the single source of truth for all AI agents.
**Test Criteria**: `specify init` creates `AGENTS.md` and appropriate pointer files; legacy files are not created.

- [x] T002 [US0] Update `src/specify_cli/__init__.py` to generate `AGENTS.md` by default using `templates/agent-file-template.md`
- [x] T003 [US0] Update `src/specify_cli/__init__.py` to create pointer files for Cursor (`.cursor/rules/specify-rules.mdc`) and Windsurf (`.windsurf/rules/specify-rules.md`)
- [x] T004 [US0] Update `src/specify_cli/__init__.py` to remove generation of legacy files (`CLAUDE.md`, `GEMINI.md`, etc.)
- [x] T005 [US0] Update `scripts/bash/update-agent-context.sh` to detect and update `AGENTS.md` primarily
- [x] T006 [US0] Update `scripts/powershell/update-agent-context.ps1` to detect and update `AGENTS.md` primarily
- [x] T007 [US0] Manual Verify: Run `specify init` in a fresh directory and confirm `AGENTS.md` creation

## Phase 3: User Story 1 (Code Standards)

**Goal**: Provide standard code style templates for core languages.
**Test Criteria**: Files exist and contain required sections (Naming, Formatting, Best Practices).

- [x] T008 [P] [US1] Create JavaScript/TypeScript style guide in `templates/company-standards/code-style/javascript.md`
- [x] T009 [P] [US1] Create Python style guide in `templates/company-standards/code-style/python.md`
- [x] T010 [P] [US1] Create Java style guide in `templates/company-standards/code-style/java.md`
- [x] T011 [P] [US1] Create Go style guide in `templates/company-standards/code-style/go.md`

## Phase 4: User Story 2 (Constitution)

**Goal**: Provide a template for architectural principles.
**Test Criteria**: Template contains Core Principles, Tech Stack, and Governance sections.

- [x] T012 [US2] Create constitution template in `templates/company-standards/constitution-template.md`

## Phase 5: User Story 3 (Security Checklist)

**Goal**: Provide a standardized security review checklist.
**Test Criteria**: Checklist covers OWASP Top 10 categories.

- [x] T013 [US3] Create security checklist in `templates/company-standards/security-checklist.md`

## Phase 6: User Story 4 (Review Guidelines)

**Goal**: Standardize code review process.
**Test Criteria**: Guidelines include severity levels and feedback templates.

- [x] T014 [US4] Create review guidelines in `templates/company-standards/review-guidelines.md`

## Phase 7: User Story 5 (Incident Response)

**Goal**: Standardize incident handling.
**Test Criteria**: Template includes Triage, Response, and Post-Mortem sections.

- [x] T015 [US5] Create incident response template in `templates/company-standards/incident-response.md`

## Phase 8: Polish & Verification

- [x] T016 Verify all new Markdown templates render correctly (no broken syntax)
- [x] T017 Check `create-release-packages.sh` to ensure `templates/company-standards` is included in the zip

## Dependencies

1. **US0 (Agent Context)** must be done first as it affects project structure.
2. **US1-US5** are independent content tasks and can be done in parallel.

## Implementation Strategy

1. **Start with US0**: This involves Python and Shell script changes, which are the most complex parts.
2. **Parallelize Content**: Once US0 is stable, the Markdown templates (US1-US5) can be created rapidly.
