# Tasks: Python Library with Universal LLM Support

**Branch**: `001-python-litellm-library` | **Date**: 2025-12-19
**Input**: Design documents from `/specs/001-python-litellm-library/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/api.md (complete)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Python package structure

- [x] T001 Create src/speckit/ package directory structure per plan.md
- [x] T002 Create pyproject.toml with dependencies (litellm, pydantic, instructor, typer, rich, jinja2, pyyaml)
- [x] T003 [P] Create tests/ directory structure (unit/, integration/, contract/)
- [x] T004 [P] Create tests/conftest.py with shared fixtures
- [x] T005 [P] Configure ruff for linting and formatting in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Implement enums (Priority, TaskStatus, PhaseType, FeatureStatus) in src/speckit/schemas.py
- [x] T007 [P] Implement config models (LLMConfig, StorageConfig, SpecKitConfig) in src/speckit/config.py
- [x] T008 [P] Create abstract storage interface in src/speckit/storage/base.py
- [x] T009 Create Jinja2 prompt templates directory at src/speckit/templates/
- [x] T010 [P] Create constitution.jinja2 template in src/speckit/templates/
- [x] T011 [P] Create specification.jinja2 template in src/speckit/templates/
- [x] T012 [P] Create clarify.jinja2 template in src/speckit/templates/
- [x] T013 [P] Create plan.jinja2 template in src/speckit/templates/
- [x] T014 [P] Create tasks.jinja2 template in src/speckit/templates/
- [x] T015 [P] Create analyze.jinja2 template in src/speckit/templates/

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 2 - Universal LLM Provider Support (Priority: P1)

**Goal**: Enable any LLM provider via LiteLLM with automatic fallback

**Independent Test**: `provider.complete("Hello")` works with any configured provider

**Why First**: US1 and US3 depend on the LLM provider being available

### Implementation for User Story 2

- [x] T016 [US2] Create LLMResponse dataclass in src/speckit/llm.py
- [x] T017 [US2] Implement LiteLLMProvider class with __init__() in src/speckit/llm.py
- [x] T018 [US2] Implement complete() method with retry logic in src/speckit/llm.py
- [x] T019 [US2] Implement complete_async() method in src/speckit/llm.py
- [x] T020 [US2] Implement stream() iterator method in src/speckit/llm.py
- [x] T021 [US2] Implement stream_async() async iterator in src/speckit/llm.py
- [x] T022 [US2] Implement fallback model chain logic in src/speckit/llm.py
- [x] T023 [US2] Implement list_models() static method in src/speckit/llm.py
- [x] T024 [P] [US2] Create unit tests in tests/unit/test_llm.py
- [x] T025 [P] [US2] Create contract tests for provider interface in tests/contract/test_llm_providers.py

**Checkpoint**: LLM provider works with OpenAI, Anthropic, Ollama, and others via LiteLLM

---

## Phase 4: User Story 6 - Structured Data Outputs (Priority: P2)

**Goal**: All workflow artifacts as validated Pydantic models with serialization

**Independent Test**: `spec.to_markdown()` produces valid markdown, `Specification.model_validate_json(json_str)` round-trips

**Why Here**: Schema models are needed by US1 and US3 implementations

### Implementation for User Story 6

- [x] T026 [P] [US6] Implement Constitution model with to_markdown() in src/speckit/schemas.py
- [x] T027 [P] [US6] Implement UserStory model with to_markdown() in src/speckit/schemas.py
- [x] T028 [P] [US6] Implement FunctionalRequirement model in src/speckit/schemas.py
- [x] T029 [P] [US6] Implement Entity model in src/speckit/schemas.py
- [x] T030 [US6] Implement Specification model with to_markdown() in src/speckit/schemas.py (depends on T027-T029)
- [x] T031 [P] [US6] Implement TechStack model in src/speckit/schemas.py
- [x] T032 [P] [US6] Implement ArchitectureComponent model in src/speckit/schemas.py
- [x] T033 [US6] Implement TechnicalPlan model with to_markdown() in src/speckit/schemas.py (depends on T031-T032)
- [x] T034 [P] [US6] Implement Task model in src/speckit/schemas.py
- [x] T035 [US6] Implement TaskBreakdown model with helper methods in src/speckit/schemas.py (depends on T034)
- [x] T036 [P] [US6] Implement ClarificationQuestion model in src/speckit/schemas.py
- [x] T037 [P] [US6] Implement AnalysisReport model in src/speckit/schemas.py
- [x] T038 [US6] Implement complete_structured() using Instructor in src/speckit/llm.py
- [x] T039 [US6] Implement complete_structured_async() in src/speckit/llm.py
- [ ] T040 [P] [US6] Create unit tests for schemas in tests/unit/test_schemas.py

**Checkpoint**: All Pydantic models validate and serialize to JSON/Markdown

---

## Phase 5: User Story 8 - File-Based Artifact Storage (Priority: P3)

**Goal**: Markdown file storage with versioning and backups

**Independent Test**: `storage.save_specification(spec, "001-feature")` creates readable markdown file

**Why Here**: Storage is needed before implementing the SpecKit orchestrator

### Implementation for User Story 8

- [x] T041 [US8] Implement FileStorage class in src/speckit/storage/file_storage.py
- [x] T042 [US8] Implement save_specification() method in src/speckit/storage/file_storage.py
- [x] T043 [US8] Implement load_specification() method in src/speckit/storage/file_storage.py
- [x] T044 [US8] Implement save_plan() and load_plan() methods in src/speckit/storage/file_storage.py
- [x] T045 [US8] Implement save_tasks() and load_tasks() methods in src/speckit/storage/file_storage.py
- [x] T046 [US8] Implement save_constitution() and load_constitution() methods in src/speckit/storage/file_storage.py
- [x] T047 [US8] Implement list_features() method in src/speckit/storage/file_storage.py
- [x] T048 [US8] Implement backup creation on overwrite in src/speckit/storage/file_storage.py
- [x] T049 [US8] Export FileStorage in src/speckit/storage/__init__.py
- [x] T050 [P] [US8] Create unit tests in tests/unit/test_storage.py

**Checkpoint**: Artifacts persist as readable Markdown files in specs/{feature_id}/

---

## Phase 6: User Story 7 - Configuration Management (Priority: P3)

**Goal**: Hierarchical configuration via env vars, YAML files, and code

**Independent Test**: Environment variables override config file values

**Why Here**: Configuration loading completes the infrastructure for SpecKit class

### Implementation for User Story 7

- [x] T051 [US7] Implement SpecKitConfig.from_project() factory in src/speckit/config.py
- [x] T052 [US7] Implement YAML config file loading from .speckit/config.yaml in src/speckit/config.py
- [x] T053 [US7] Implement environment variable precedence logic in src/speckit/config.py
- [x] T054 [US7] Implement config.save() method for persisting configuration in src/speckit/config.py
- [ ] T055 [P] [US7] Create unit tests in tests/unit/test_config.py

**Checkpoint**: Configuration works with env vars, YAML, and programmatic overrides

---

## Phase 7: User Story 1 - Library Installation and Basic Usage (Priority: P1)

**Goal**: Import `from speckit import SpecKit` and call workflow methods

**Independent Test**: `kit = SpecKit("./project"); spec = kit.specify("feature")` works

### Implementation for User Story 1

- [x] T056 [US1] Create SpecKit orchestrator class skeleton in src/speckit/speckit.py
- [x] T057 [US1] Implement SpecKit.__init__() with config loading in src/speckit/speckit.py
- [x] T058 [US1] Wire up LiteLLMProvider in SpecKit class in src/speckit/speckit.py
- [x] T059 [US1] Wire up FileStorage in SpecKit class in src/speckit/speckit.py
- [x] T060 [US1] Export SpecKit and key classes in src/speckit/__init__.py
- [x] T061 [P] [US1] Create basic_usage.py example in examples/
- [ ] T062 [P] [US1] Create integration test in tests/integration/test_workflow.py

**Checkpoint**: Library is pip-installable and basic import/usage works

---

## Phase 8: User Story 3 - Complete Specification Workflow (Priority: P1)

**Goal**: Execute full spec-driven workflow programmatically

**Independent Test**: Full workflow from specify() through tasks() produces valid artifacts

### Core Module Implementation

- [x] T063 [P] [US3] Implement ConstitutionManager in src/speckit/core/constitution.py
- [x] T064 [P] [US3] Implement SpecificationBuilder in src/speckit/core/specification.py
- [x] T065 [P] [US3] Implement ClarificationEngine in src/speckit/core/clarifier.py
- [x] T066 [P] [US3] Implement TechnicalPlanner in src/speckit/core/planner.py
- [x] T067 [P] [US3] Implement TaskGenerator in src/speckit/core/tasker.py
- [x] T068 [P] [US3] Implement ImplementationTracker in src/speckit/core/implementer.py
- [x] T069 [P] [US3] Implement ConsistencyAnalyzer in src/speckit/core/analyzer.py
- [x] T070 [US3] Create core/__init__.py with exports in src/speckit/core/

### SpecKit Method Wiring

- [x] T071 [US3] Implement SpecKit.constitution() method in src/speckit/speckit.py
- [x] T072 [US3] Implement SpecKit.specify() method in src/speckit/speckit.py
- [x] T073 [US3] Implement SpecKit.clarify() method in src/speckit/speckit.py
- [x] T074 [US3] Implement SpecKit.apply_clarification() method in src/speckit/speckit.py
- [x] T075 [US3] Implement SpecKit.plan() method in src/speckit/speckit.py
- [x] T076 [US3] Implement SpecKit.tasks() method in src/speckit/speckit.py
- [x] T077 [US3] Implement SpecKit.analyze() method in src/speckit/speckit.py

### Async Variants

- [x] T078 [P] [US3] Implement specify_async() in src/speckit/speckit.py
- [x] T079 [P] [US3] Implement plan_async() in src/speckit/speckit.py
- [x] T080 [P] [US3] Implement tasks_async() in src/speckit/speckit.py
- [ ] T081 [P] [US3] Create complete_workflow.py example in examples/

**Checkpoint**: Full workflow executes: constitution → specify → clarify → plan → tasks → analyze

---

## Phase 9: User Story 4 - Command-Line Interface (Priority: P2)

**Goal**: CLI exposes all library functions with human-readable and JSON output

**Independent Test**: `speckit specify "feature" --feature-id 001-test` produces spec.md

### Implementation for User Story 4

- [x] T082 [US4] Create Typer app skeleton in src/speckit/cli.py
- [x] T083 [US4] Implement `speckit init` command in src/speckit/cli.py
- [x] T084 [US4] Implement `speckit constitution` command in src/speckit/cli.py
- [x] T085 [US4] Implement `speckit specify` command in src/speckit/cli.py
- [x] T086 [US4] Implement `speckit clarify` command in src/speckit/cli.py
- [x] T087 [US4] Implement `speckit plan` command in src/speckit/cli.py
- [x] T088 [US4] Implement `speckit tasks` command in src/speckit/cli.py
- [x] T089 [US4] Implement `speckit analyze` command in src/speckit/cli.py
- [x] T090 [US4] Implement `speckit config` subcommands (get/set/show) in src/speckit/cli.py
- [x] T091 [US4] Add Rich progress indicators for LLM operations in src/speckit/cli.py
- [x] T092 [US4] Add --format flag (rich/json/quiet) output modes in src/speckit/cli.py
- [x] T093 [US4] Add entry point in pyproject.toml [project.scripts]
- [ ] T094 [P] [US4] Create CLI integration tests in tests/integration/test_cli.py

**Checkpoint**: All workflow phases accessible via command line

---

## Phase 10: User Story 5 - MCP Server Integration (Priority: P2)

**Goal**: Expose spec-kit tools to AI assistants via MCP protocol

**Independent Test**: Claude Desktop can invoke speckit_specify tool

### Implementation for User Story 5

- [x] T095 [US5] Create MCP server skeleton in src/speckit/mcp/server.py
- [x] T096 [US5] Implement speckit_specify tool in src/speckit/mcp/server.py
- [x] T097 [US5] Implement speckit_clarify tool in src/speckit/mcp/server.py
- [x] T098 [US5] Implement speckit_plan tool in src/speckit/mcp/server.py
- [x] T099 [US5] Implement speckit_tasks tool in src/speckit/mcp/server.py
- [x] T100 [US5] Implement speckit_analyze tool in src/speckit/mcp/server.py
- [x] T101 [US5] Implement speckit_list_features tool in src/speckit/mcp/server.py
- [x] T102 [US5] Implement speckit_get_artifact tool in src/speckit/mcp/server.py
- [x] T103 [US5] Create __main__.py for `python -m speckit.mcp` in src/speckit/mcp/
- [x] T104 [US5] Export server in src/speckit/mcp/__init__.py
- [x] T105 [US5] Add [mcp] optional dependency in pyproject.toml
- [ ] T106 [US5] Implement `speckit mcp serve` CLI command in src/speckit/cli.py

**Checkpoint**: MCP server exposes all spec-kit operations to AI assistants

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Error Handling

- [x] T107 Create exception hierarchy in src/speckit/exceptions.py
- [x] T108 Add SpecKitError, ConfigurationError, LLMError classes
- [x] T109 Add LLMRateLimitError, LLMTimeoutError with retry_after
- [x] T110 Add ValidationError, StorageError, WorkflowError classes
- [ ] T111 Integrate exception handling across all modules

### Examples & Documentation

- [ ] T112 [P] Create multi_provider.py example in examples/
- [ ] T113 [P] Create custom_templates.py example in examples/
- [ ] T114 [P] Create automation_pipeline.py example in examples/
- [ ] T115 Run quickstart.md validation with real API calls

### Final Testing

- [ ] T116 Verify all unit tests pass with `pytest tests/unit/`
- [ ] T117 Run integration tests with `pytest tests/integration/`
- [ ] T118 Run contract tests with real providers (requires API keys)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **US2 (Phase 3)**: Depends on Foundational - LLM provider is core dependency
- **US6 (Phase 4)**: Depends on Foundational - Pydantic models extend base enums
- **US8 (Phase 5)**: Depends on US6 - Storage needs schema models
- **US7 (Phase 6)**: Can run parallel with US8 after Foundational
- **US1 (Phase 7)**: Depends on US2, US6, US7, US8 - Orchestrator integrates all
- **US3 (Phase 8)**: Depends on US1 - Workflow methods need orchestrator
- **US4 (Phase 9)**: Depends on US1 - CLI wraps library
- **US5 (Phase 10)**: Depends on US1 - MCP wraps library
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies Summary

```
Foundational → US2 (LLM) → US1 (Library) → US3 (Workflow) → US4 (CLI)
                    ↓                                        ↘
              US6 (Schemas) → US8 (Storage) ─────────────────→ US5 (MCP)
                    ↓
              US7 (Config)
```

### Parallel Opportunities

- **Phase 1**: T003, T004, T005 can run in parallel
- **Phase 2**: T006, T007, T008 can run in parallel; T010-T015 can run in parallel
- **Phase 3**: T024, T025 tests can run in parallel
- **Phase 4**: T026-T029, T031-T032, T034, T036, T037 models can run in parallel
- **Phase 8**: T063-T069 core modules can ALL run in parallel (different files)
- **Phase 8**: T078-T081 async variants can run in parallel

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US2 - LLM Provider
4. Complete Phase 4: US6 - Schemas (minimal for MVP)
5. Complete Phase 5: US8 - Storage (minimal for MVP)
6. Complete Phase 6: US7 - Config (minimal for MVP)
7. Complete Phase 7: US1 - Library API
8. Complete Phase 8: US3 - Workflow
9. **STOP and VALIDATE**: Full workflow works programmatically
10. Deploy library to PyPI as 0.1.0

### Incremental Delivery

1. MVP (US1+US2+US3) → Library works, 0.1.0 release
2. Add US4 (CLI) → Command-line access, 0.2.0 release
3. Add US5 (MCP) → AI assistant integration, 0.3.0 release
4. Polish all → Production ready, 1.0.0 release

---

## Task Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| 1 Setup | - | 5 | 3 |
| 2 Foundational | - | 10 | 9 |
| 3 | US2 | 10 | 2 |
| 4 | US6 | 15 | 10 |
| 5 | US8 | 10 | 1 |
| 6 | US7 | 5 | 1 |
| 7 | US1 | 7 | 2 |
| 8 | US3 | 19 | 12 |
| 9 | US4 | 13 | 1 |
| 10 | US5 | 12 | 0 |
| 11 Polish | - | 12 | 3 |
| **Total** | | **118** | **44** |

---

## Notes

- [P] tasks = different files, no dependencies within that phase
- Tests are included where specified in the spec (unit, integration, contract)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All core/ modules can be implemented in parallel by different developers
