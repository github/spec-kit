# Tasks: Internationalization Support for Specify CLI

**Input**: Design documents from `/specs/001-i18n-support/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: This feature does NOT explicitly request tests in the specification. Test tasks are included for core i18n functionality to ensure quality, but are optional and can be removed if TDD is not desired.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `templates/`, `docs/` at repository root
- Paths shown below follow single project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic i18n infrastructure

- [x] T001 Add babel dependency to pyproject.toml (version >=2.12.0,<3.0.0)
- [x] T002 Create babel.cfg configuration file in repository root for message extraction
- [x] T003 Create src/specify_cli/i18n/ directory structure
- [x] T004 Create templates/i18n/ directory structure  
- [x] T005 Create docs/i18n/ directory structure
- [x] T006 Create tests/i18n/ directory for i18n-specific tests
- [x] T007 Create scripts/i18n/ directory for i18n tooling scripts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core i18n infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Core I18n Module

- [x] T008 [P] Create src/specify_cli/i18n/**init**.py with module exports (get_translator, setup_i18n)
- [x] T009 [P] Implement core i18n logic in src/specify_cli/i18n/core.py (LocaleContext, language detection, catalog loading)
- [x] T010 Define SUPPORTED_LANGUAGES constant in src/specify_cli/i18n/core.py with en_US and zh_CN metadata
- [x] T011 Implement get_active_locale() function in src/specify_cli/i18n/core.py to read SPECIFY_LANG environment variable
- [x] T012 Implement setup_i18n() function in src/specify_cli/i18n/core.py to initialize translation with fallback chain
- [x] T013 Implement get_template_path() function in src/specify_cli/i18n/core.py for localized template selection

### Translation Infrastructure Setup

- [x] T014 Create src/specify_cli/i18n/en_US/LC_MESSAGES/ directory for English catalog
- [x] T015 Create src/specify_cli/i18n/zh_CN/LC_MESSAGES/ directory for Chinese catalog
- [x] T016 Create scripts/i18n/extract-messages.sh script to extract translatable strings using pybabel
- [x] T017 Create scripts/i18n/compile-translations.sh script to compile PO to MO files using pybabel
- [x] T018 Create scripts/i18n/check-coverage.sh script to validate translation completeness using msgfmt

### Core Tests (Optional)

- [x] T019 [P] Create tests/i18n/test_core.py with tests for language detection and catalog loading
- [x] T020 [P] Create tests/i18n/test_messages.py with tests for CLI message translation
- [x] T021 [P] Create tests/i18n/test_templates.py with tests for template localization

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Chinese Developer Uses CLI in Native Language (Priority: P1) 🎯 MVP

**Goal**: Enable Chinese-speaking developers to use Specify CLI with all output, messages, and help text displayed in Chinese via SPECIFY_LANG=zh_CN environment variable.

**Independent Test**: Set `SPECIFY_LANG=zh_CN` and run `specify --help`, `specify init`, `specify check`. All output should be in Chinese. Falls back to English gracefully if translations missing.

### CLI Integration

- [x] T022 [US1] Modify src/specify_cli/**init**.py to import and initialize i18n module at startup
- [x] T023 [US1] Update src/specify_cli/**init**.py to call setup_i18n() before any CLI operations
- [x] T024 [US1] Wrap all user-facing strings in **init**.py with _() function for translation (sample strings wrapped)

### Message Extraction and Catalog Creation

- [ ] T025 [US1] Run scripts/i18n/extract-messages.sh to generate src/specify_cli/i18n/messages.pot from source code
- [ ] T026 [US1] Initialize Chinese catalog using pybabel init: src/specify_cli/i18n/zh_CN/LC_MESSAGES/specify.po
- [ ] T027 [US1] Initialize English catalog using pybabel init: src/specify_cli/i18n/en_US/LC_MESSAGES/specify.po

### Chinese Translation - Core CLI Messages

- [ ] T028 [US1] Translate help command messages in specify.po (--help output, command descriptions)
- [ ] T029 [US1] Translate init command messages in specify.po (initialization messages, prompts, confirmations)
- [ ] T030 [US1] Translate check command messages in specify.po (tool check results, status messages)
- [ ] T031 [US1] Translate version command messages in specify.po (version information display)
- [ ] T032 [US1] Translate banner and general UI messages in specify.po (ASCII banner, taglines, progress indicators)

### Compilation and Testing

- [ ] T033 [US1] Run scripts/i18n/compile-translations.sh to generate MO files from PO files
- [ ] T034 [US1] Test CLI with SPECIFY_LANG=zh_CN: verify specify --help displays Chinese
- [ ] T035 [US1] Test CLI with SPECIFY_LANG=zh_CN: verify specify init myproject displays Chinese
- [ ] T036 [US1] Test CLI with SPECIFY_LANG=zh_CN: verify specify check displays Chinese
- [ ] T037 [US1] Test CLI with SPECIFY_LANG unset: verify default English messages
- [ ] T038 [US1] Test CLI with SPECIFY_LANG=invalid: verify fallback to English with warning

**Checkpoint**: At this point, User Story 1 should be fully functional - Chinese developers can use CLI commands in Chinese

---

## Phase 4: User Story 2 - Chinese Developer Reads Localized Templates (Priority: P2)

**Goal**: Provide specification templates, plan templates, task templates, and command templates with Chinese comments and instructions when SPECIFY_LANG=zh_CN is set.

**Independent Test**: Run `specify init myproject --ai claude` with `SPECIFY_LANG=zh_CN`, then inspect generated templates. All instructional comments and section descriptions should be in Chinese, placeholders preserved exactly.

### Template Localization Infrastructure

- [x] T039 [US2] Create templates/i18n/zh_CN/ base directory
- [x] T040 [US2] Create templates/i18n/zh_CN/commands/ directory for command templates
- [x] T041 [US2] Update specify init command in src/specify_cli/**init**.py to use get_template_path() for template selection (via apply_localized_templates)

### Core Template Translation (Chinese)

- [x] T042 [P] [US2] Translate templates/spec-template.md to templates/i18n/zh_CN/spec-template.md (preserve [PLACEHOLDERS])
- [x] T043 [P] [US2] Translate templates/plan-template.md to templates/i18n/zh_CN/plan-template.md (preserve [PLACEHOLDERS])
- [x] T044 [P] [US2] Translate templates/tasks-template.md to templates/i18n/zh_CN/tasks-template.md (preserve [PLACEHOLDERS])
- [x] T045 [P] [US2] Translate templates/checklist-template.md to templates/i18n/zh_CN/checklist-template.md (preserve [PLACEHOLDERS])
- [x] T046 [P] [US2] Translate templates/agent-file-template.md to templates/i18n/zh_CN/agent-file-template.md (preserve [PLACEHOLDERS])

### Command Template Translation (Chinese)

- [x] T047 [P] [US2] Translate templates/commands/specify.md to templates/i18n/zh_CN/commands/specify.md
- [x] T048 [P] [US2] Translate templates/commands/plan.md to templates/i18n/zh_CN/commands/plan.md
- [x] T049 [P] [US2] Translate templates/commands/tasks.md to templates/i18n/zh_CN/commands/tasks.md
- [x] T050 [P] [US2] Translate templates/commands/implement.md to templates/i18n/zh_CN/commands/implement.md
- [x] T051 [P] [US2] Translate templates/commands/clarify.md to templates/i18n/zh_CN/commands/clarify.md
- [x] T052 [P] [US2] Translate templates/commands/analyze.md to templates/i18n/zh_CN/commands/analyze.md
- [x] T053 [P] [US2] Translate templates/commands/checklist.md to templates/i18n/zh_CN/commands/checklist.md
- [x] T054 [P] [US2] Translate templates/commands/constitution.md to templates/i18n/zh_CN/commands/constitution.md
- [x] T055 [P] [US2] Translate templates/commands/taskstoissues.md to templates/i18n/zh_CN/commands/taskstoissues.md

### Template Validation and Testing

- [ ] T056 [US2] Create validation script to verify placeholders match between English and Chinese templates
- [ ] T057 [US2] Test template generation with SPECIFY_LANG=zh_CN: verify Chinese spec-template.md is used
- [ ] T058 [US2] Test template generation with SPECIFY_LANG=zh_CN: verify Chinese plan-template.md is used
- [ ] T059 [US2] Test template generation with SPECIFY_LANG=zh_CN: verify Chinese command templates are used
- [ ] T060 [US2] Test template generation with SPECIFY_LANG unset: verify English templates are used (fallback)

**Checkpoint**: At this point, User Story 2 should be fully functional - Chinese developers receive localized templates when initializing projects

---

## Phase 5: User Story 3 - Chinese Developer Receives Localized Error Messages (Priority: P3)

**Goal**: Provide clear, actionable error messages in Chinese when errors occur during CLI operations (missing tools, invalid arguments, network failures, etc.).

**Independent Test**: Trigger various error conditions with `SPECIFY_LANG=zh_CN` set. All error messages, warnings, and troubleshooting hints should be in Chinese.

### Error Message Translation

- [ ] T061 [US3] Translate usage error messages in specify.po (missing arguments, invalid syntax)
- [ ] T062 [US3] Translate validation error messages in specify.po (invalid agent selection, invalid script type)
- [ ] T063 [US3] Translate tool missing error messages in specify.po (git not found, CLI tools not found)
- [ ] T064 [US3] Translate network error messages in specify.po (download failures, timeout errors, rate limit errors)
- [ ] T065 [US3] Translate file system error messages in specify.po (directory conflicts, permission errors)
- [ ] T066 [US3] Translate git operation error messages in specify.po (init failures, branch conflicts)

### Warning and Diagnostic Messages

- [ ] T067 [US3] Translate warning messages in specify.po (non-empty directory, git not available)
- [ ] T068 [US3] Translate diagnostic messages in specify.po (debug output, environment info)
- [ ] T069 [US3] Translate security notices in specify.po (agent folder security warning)
- [ ] T070 [US3] Add terminal encoding detection and warning in src/specify_cli/i18n/core.py

### Error Testing

- [ ] T071 [US3] Test error: Run specify init without arguments with SPECIFY_LANG=zh_CN, verify Chinese error
- [ ] T072 [US3] Test error: Run specify init --ai invalidagent with SPECIFY_LANG=zh_CN, verify Chinese error
- [ ] T073 [US3] Test error: Trigger network timeout with SPECIFY_LANG=zh_CN, verify Chinese error
- [ ] T074 [US3] Test warning: Initialize in non-empty directory with SPECIFY_LANG=zh_CN, verify Chinese warning
- [ ] T075 [US3] Test fallback: Verify stack traces and technical details remain in English

**Checkpoint**: At this point, User Story 3 should be fully functional - Chinese developers receive localized error messages

---

## Phase 6: User Story 4 - Multilingual Team Collaboration (Priority: P4)

**Goal**: Validate that team members can use different languages simultaneously without conflicts. Each sees CLI output in their language, but generated specs and code are identical.

**Independent Test**: Two developers (one with SPECIFY_LANG=zh_CN, another with unset or en_US) work on same project. Each sees output in their language, but file contents are identical.

### Multilingual Validation

- [ ] T076 [US4] Document language-neutral specification content guidelines in docs/i18n/zh_CN/
- [ ] T077 [US4] Test scenario: Developer A (zh_CN) initializes project, Developer B (en_US) runs commands
- [ ] T078 [US4] Test scenario: Verify specify check output differs by language but underlying checks are identical
- [ ] T079 [US4] Test scenario: Verify generated spec files have same structure regardless of language
- [ ] T080 [US4] Test scenario: Verify templates can be regenerated in different language without affecting content

### Cross-Language Documentation

- [ ] T081 [US4] Add multilingual team workflow section to docs/i18n/zh_CN/README.md
- [ ] T082 [US4] Document template regeneration process for language switching
- [ ] T083 [US4] Add FAQ for common multilingual team scenarios

**Checkpoint**: All user stories should now be independently functional - multilingual teams validated

---

## Phase 7: Documentation Localization

**Purpose**: Translate core documentation files to Chinese for complete user experience

### Chinese Documentation Translation

- [ ] T084 [P] Translate README.md to docs/i18n/zh_CN/README.md (full translation with examples)
- [ ] T085 [P] Translate docs/quickstart.md to docs/i18n/zh_CN/quickstart.md
- [ ] T086 [P] Translate docs/installation.md to docs/i18n/zh_CN/installation.md
- [ ] T087 [P] Translate docs/local-development.md to docs/i18n/zh_CN/local-development.md
- [ ] T088 [P] Translate docs/upgrade.md to docs/i18n/zh_CN/upgrade.md

### Documentation Updates

- [x] T089 Add language selection section to English README.md explaining SPECIFY_LANG (--lang option documented)
- [ ] T090 Add links to Chinese documentation in English README.md
- [ ] T091 Update CONTRIBUTING.md with translation contribution guidelines
- [ ] T092 Create docs/i18n/TRANSLATORS_GUIDE.md with technical terminology standards

---

## Phase 8: CI/CD and Quality Assurance

**Purpose**: Automated validation and quality checks for translations

### CI/CD Integration

- [ ] T093 Create .github/workflows/i18n-check.yml workflow for translation validation
- [ ] T094 Add translation completeness check to CI pipeline (fail if <100% for Chinese)
- [ ] T095 Add template placeholder validation to CI pipeline (verify Chinese templates match English)
- [ ] T096 Add MO file compilation check to CI pipeline (ensure PO files compile without errors)

### Translation Coverage and Quality

- [ ] T097 Run scripts/i18n/check-coverage.sh to verify 100% translation coverage for Chinese
- [ ] T098 Create translation coverage report generator script
- [ ] T099 Document translation quality review process in CONTRIBUTING.md
- [ ] T100 Add pre-commit hook suggestion for running pybabel compile before commits

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final quality checks

### Performance and Optimization

- [ ] T101 Profile i18n initialization overhead (target <100ms)
- [ ] T102 Add performance test to verify no degradation in CLI response time
- [ ] T103 Document performance characteristics in quickstart.md

### Edge Case Handling

- [ ] T104 Add handling for incomplete translations (graceful fallback with optional warning)
- [ ] T105 Add terminal encoding detection for Windows (warn if UTF-8 not supported)
- [ ] T106 Add support for locale variants detection (zh_CN vs zh_TW)
- [ ] T107 Document edge case handling in docs/i18n/zh_CN/README.md

### Final Documentation and Cleanup

- [ ] T108 Update CHANGELOG.md with i18n feature addition
- [ ] T109 Update pyproject.toml version number (minor version bump)
- [ ] T110 Run final translation completeness check for all languages
- [ ] T111 Create user-facing release notes for i18n feature
- [ ] T112 Add i18n troubleshooting section to docs/i18n/zh_CN/README.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Documentation (Phase 7)**: Can proceed in parallel with User Stories 3-4
- **CI/CD (Phase 8)**: Depends on User Stories 1-3 being complete
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: MVP - Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories  
- **User Story 4 (P4)**: Should start after User Stories 1-3 complete (validation story)

### Within Each User Story

- Message extraction before translation (T025 before T028-T032 in US1)
- Translation before compilation (T028-T032 before T033 in US1)
- Template creation before testing (T042-T055 before T057-T060 in US2)
- Core implementation before edge cases (US1-3 before US4)

### Parallel Opportunities

- **Setup tasks (T001-T007)**: All can run in parallel (creating directories)
- **Foundational core module (T008-T009)**: Can run in parallel (different files)
- **Foundational tests (T019-T021)**: Can run in parallel (different files)
- **Template translations (T042-T055)**: All can run in parallel (different files)
- **Documentation translations (T084-T088)**: All can run in parallel (different files)
- **Once Foundational phase completes**: User Stories 1, 2, 3 can all start in parallel by different team members

---

## Parallel Example: User Story 2 (Template Translation)

```bash
# Launch all template translations together (after T039-T041 complete):
Task T042: Translate spec-template.md to Chinese
Task T043: Translate plan-template.md to Chinese
Task T044: Translate tasks-template.md to Chinese
Task T045: Translate checklist-template.md to Chinese
Task T046: Translate agent-file-template.md to Chinese

# Launch all command template translations together:
Task T047: Translate specify.md command
Task T048: Translate plan.md command
Task T049: Translate tasks.md command
Task T050: Translate implement.md command
Task T051: Translate clarify.md command
Task T052: Translate analyze.md command
Task T053: Translate checklist.md command
Task T054: Translate constitution.md command
Task T055: Translate taskstoissues.md command
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T021) - CRITICAL
3. Complete Phase 3: User Story 1 (T022-T038)
4. **STOP and VALIDATE**: Test User Story 1 independently with Chinese CLI
5. Deploy/demo if ready - Chinese developers can now use basic CLI commands

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - CLI in Chinese!)
3. Add User Story 2 → Test independently → Deploy/Demo (Templates in Chinese!)
4. Add User Story 3 → Test independently → Deploy/Demo (Errors in Chinese!)
5. Add User Story 4 → Test independently → Deploy/Demo (Team collaboration validated!)
6. Add Documentation → Deploy/Demo (Full Chinese docs!)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T021)
2. Once Foundational is done:
   - Developer A: User Story 1 (CLI messages) - T022-T038
   - Developer B: User Story 2 (Templates) - T039-T060
   - Developer C: User Story 3 (Errors) - T061-T075
3. Stories complete and integrate independently
4. Team reconvenes for User Story 4 validation
5. Final polish and documentation in parallel

---

## Notes

- **[P] tasks**: Different files, no dependencies - run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **Each user story**: Independently completable and testable
- **Tests included**: Core i18n tests are included for quality but are optional
- **Translation work**: Tasks T028-T032, T042-T055, T061-T069, T084-T088 require native Chinese speaker or translator
- **Commit strategy**: Commit after each logical group (e.g., after T033 compile, after T060 template validation)
- **Stop at any checkpoint**: Validate story independently before moving to next priority
- **Avoid**: Cross-story dependencies, vague tasks, conflicting file edits

## Total Task Count Summary

- **Phase 1 (Setup)**: 7 tasks
- **Phase 2 (Foundational)**: 14 tasks (11 core + 3 tests)
- **Phase 3 (US1 - CLI Messages)**: 17 tasks
- **Phase 4 (US2 - Templates)**: 22 tasks
- **Phase 5 (US3 - Errors)**: 15 tasks
- **Phase 6 (US4 - Collaboration)**: 8 tasks
- **Phase 7 (Documentation)**: 9 tasks
- **Phase 8 (CI/CD)**: 8 tasks
- **Phase 9 (Polish)**: 12 tasks

**Total**: 112 tasks

**Parallel opportunities identified**: 45+ tasks can run in parallel across different phases

**MVP scope** (Minimum Viable Product): Phases 1-3 (Tasks T001-T038) = 38 tasks
