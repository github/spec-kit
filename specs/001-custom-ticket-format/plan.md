# Implementation Plan: Custom Linear Ticket Format Configuration

**Branch**: `001-custom-ticket-format` | **Date**: 2025-11-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-custom-ticket-format/spec.md`

**Note**: This feature enables the Auror workflow integration (Principle VII) by making Linear ticket formats configurable for different teams.

## Summary

Enable teams to configure their Linear ticket ID prefix (e.g., AFR, ASR, PROJ) during `specify init`, replacing the hardcoded AUROR default. This configuration will drive branch naming (`PREFIX-NUMBER-description`), spec directory naming, and commit message conventions. The implementation requires updates to the Python CLI (`specify init`), bash scripts (`create-new-feature.sh`, `common.sh`), and documentation (README, constitution template) while maintaining backward compatibility with existing `001-feature-name` format.

**Technical Approach**: Configuration-driven workflow modification using JSON config file (`.specify/config.json`) with fallback logic for legacy projects. Dual regex patterns in bash scripts support both old (`001-`) and new (`AFR-1234-`) formats. Python CLI prompts for prefix with alphabetic-only validation.

## Technical Context

**Language/Version**:
- Python 3.11+ (CLI - `src/specify_cli/__init__.py`)
- Bash 4.0+ (workflow scripts - `.specify/scripts/bash/*.sh`)

**Primary Dependencies**:
- Python: `typer` (CLI framework), `rich` (UI), `platformdirs`, `httpx`
- Bash: `jq` (JSON parsing - optional with fallback), standard GNU utilities

**Storage**:
- File-based configuration: `.specify/config.json` (JSON format)
- No database required

**Testing**:
- Manual testing of CLI interactions (Python)
- Bash script testing with sample repos (old and new formats)
- Integration tests for mixed-format repositories

**Target Platform**:
- Cross-platform: macOS, Linux, Windows (via WSL or native PowerShell future support)
- Primary focus: POSIX-compliant bash environments

**Project Type**:
- CLI tool enhancement + workflow script modification
- Single codebase with Python CLI and bash automation scripts

**Performance Goals**:
- CLI prompt response: <500ms
- Config file read/parse: <50ms
- Branch creation: <2s (including git operations)
- No performance regression for legacy format

**Constraints**:
- Backward compatibility: Must support existing `001-feature-name` projects
- No breaking changes: Legacy projects without config must continue working
- Validation: Reject invalid prefixes (numbers, special chars, hyphens)
- Cross-platform: Regex patterns must work in bash and PowerShell (future)

**Scale/Scope**:
- 5 files to modify (3 scripts, 1 CLI, 1 config template)
- 2 documentation files to update
- ~300-400 lines of code changes total
- Support unlimited team prefixes (AFR, ASR, PROJ, etc.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This section validates adherence to the Auror Spec-Kit Constitution (`.specify/memory/constitution.md`). Review each principle and document any violations with explicit justification.

### Principle I: Structured Workflow Automation
- [x] Feature follows Specify → Plan → Tasks → Implement progression
- [x] Each phase has clear completion criteria
- [x] Artifacts from prior phases inform current phase

**Violations**: None - Following standard workflow

### Principle II: Template-Driven Generation
- [x] All artifacts use templates from `.specify/templates/`
- [x] No ad-hoc documentation structures introduced

**Violations**: None - Using existing spec, plan, and tasks templates

### Principle III: User Story Independence
- [x] Feature spec decomposes into independently testable user stories (P1, P2, P3...)
- [x] Each story delivers standalone value
- [x] Tasks will be organized by user story

**Violations**: None - Spec has 5 user stories with clear priorities:
- P1: Configure format during init (foundational)
- P2: Create branches with custom format (core functionality)
- P2: Create spec directories with custom format (core functionality)
- P3: Commit message guidance (documentation)
- P3: Multi-team documentation (adoption support)

### Principle IV: Specification Quality Gates
- [x] Spec has ≤3 [NEEDS CLARIFICATION] markers (has 0)
- [x] All functional requirements are testable and unambiguous
- [x] Success criteria are measurable and technology-agnostic
- [x] No implementation details in spec.md

**Violations**: None - Spec passed validation checklist with all items marked complete

### Principle V: Constitution Compliance Verification
- [x] This Constitution Check section is present and complete

**Violations**: None

### Principle VI: Technology-Agnostic Requirements
- [x] Spec.md contains no technology/framework references
- [x] Technical decisions documented in research.md and plan.md only

**Violations**: None - Spec focuses on user needs and outcomes, technical details are in this plan

### Principle VII: Auror Workflow Integration
- [x] Branch follows Linear ticket format: 001-custom-ticket-format (numeric prefix as interim format)
- [x] Commits will follow: `001 description` format
- [~] Generated code aligns with Auror patterns (N/A - no code generation, modifying existing scripts)
- [~] Testing approach uses Auror standards (Manual testing + integration tests, not xUnit-based)

**Violations**:
1. **Branch format deviation**: Using numeric `001-` prefix instead of `F-XXXXX-` Linear format
   - **Justification**: This feature *implements* the Linear format capability. Bootstrapping issue - can't use Linear format until feature is complete.
   - **Mitigation**: Once feature is merged, future branches will use proper Linear format (e.g., `AFR-1234-description`)

2. **Testing approach**: Manual + integration tests instead of xUnit/AutoFixture
   - **Justification**: This is bash/Python CLI code, not C# .NET. Auror's testing standards (xUnit, AutoFixture, FluentAssertions) are .NET-specific and don't apply to Python/Bash.
   - **Mitigation**: Will follow Python testing best practices (pytest if tests requested) and bash integration testing patterns

### Principle VIII: Versioned Governance
- [x] N/A for feature implementation (applies to constitution amendments only)

**Complexity Justification**: See violations documented above - both are justified by project context.

## Project Structure

### Documentation (this feature)

```text
specs/001-custom-ticket-format/
├── spec.md                  # Feature specification (/speckit.specify output)
├── plan.md                  # This file (/speckit.plan output)
├── research.md              # Phase 0: Technical research and decisions
├── data-model.md            # Phase 1: Configuration schema and validation
├── quickstart.md            # Phase 1: Developer quick reference
├── affected-files.md        # Analysis: All files requiring changes
├── checklists/
│   └── requirements.md      # Spec quality validation (completed)
└── contracts/
    └── config-schema.json   # JSON schema for .specify/config.json
```

### Source Code (repository root)

```text
spec-kit/
├── src/specify_cli/
│   └── __init__.py          # Python CLI - ADD Linear format prompt (lines 1010+)
│
├── .specify/
│   ├── config.json          # NEW: Project configuration (created by init)
│   ├── scripts/bash/
│   │   ├── create-new-feature.sh   # MODIFY: Read config, support custom formats
│   │   ├── common.sh               # MODIFY: Update regex patterns for dual format
│   │   └── setup-plan.sh           # NO CHANGE: Inherits from common.sh
│   └── templates/
│       └── constitution-template.md # MODIFY: Document Linear format conventions
│
├── README.md                # MODIFY: Add multi-team examples
│
└── specs/                   # Feature specs (existing structure)
    └── 001-custom-ticket-format/   # This feature
```

**Structure Decision**: Single-project CLI tool with Python CLI frontend and bash script automation backend. No separate frontend/backend split. Configuration is file-based JSON, no database.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Branch format `001-` instead of `F-XXXXX-` | Bootstrapping issue: implementing the feature that enables Linear format | Cannot use Linear format until the feature that enables it is complete. Using placeholder numeric format is necessary for initial implementation. |
| Manual/integration testing instead of xUnit | Python/Bash codebase, not .NET | Auror's xUnit/AutoFixture standards are .NET-specific. Python has pytest, bash has shell integration tests. Following language-appropriate patterns. |

## Phase 0: Research & Technical Decisions

**Status**: Complete (see [research.md](./research.md))

**Key Decisions**:
1. **Configuration Storage**: `.specify/config.json` at project root
2. **JSON Parsing in Bash**: Use `jq` with fallback to grep/sed for portability
3. **Validation Strategy**: Client-side validation in Python CLI before saving
4. **Regex Pattern**: Dual support `^([A-Z]+-[0-9]+|[0-9]{3})-` for old/new formats
5. **Parameter Naming**: `--linear-ticket AFR-1234` for explicit ticket specification

## Phase 1: Design & Contracts

**Status**: Complete (see [data-model.md](./data-model.md) and [contracts/](./contracts/))

**Artifacts**:
- **Configuration Schema**: `.specify/config.json` structure with validation rules
- **Validation Contract**: Alphabetic-only prefix, no special chars
- **Backward Compatibility**: Legacy format detection and handling
- **Error Messages**: User-friendly validation and format guidance

## Implementation Phases

### Phase 1: Configuration Infrastructure (P1)

**Goal**: Enable configuration during `specify init` and persist to config file

**Files Changed**:
- `src/specify_cli/__init__.py` (lines 1010-1050): Add prompt after script type selection

**Tasks**:
1. Add Linear format prompt after script type selection
2. Implement alphabetic-only validation with re-prompt
3. Save configuration to `.specify/config.json`
4. Add confirmation message showing configured format
5. Handle non-interactive mode (default to AUROR)

**Testing**:
- New project with default (press Enter) → AUROR
- New project with custom (AFR) → AFR saved to config
- Invalid input (AFR-123) → error + re-prompt
- Non-interactive mode → defaults to AUROR

---

### Phase 2: Core Script Updates (P2)

**Goal**: Update bash scripts to read config and support custom formats

**Files Changed**:
- `.specify/scripts/bash/common.sh` (lines 40, 75, 94): Update regex patterns
- `.specify/scripts/bash/create-new-feature.sh` (lines 131-135, 183-214): Read config, generate custom format

**Tasks**:
1. Add config reading utility to common.sh
2. Update get_current_branch() regex: `^([A-Z]+-[0-9]+|[0-9]{3})-`
3. Update check_feature_branch() validation and error messages
4. Update find_feature_dir_by_prefix() prefix extraction
5. Modify create-new-feature.sh to read config for prefix
6. Add --linear-ticket parameter support
7. Update branch name generation logic
8. Update check_existing_branches() for dual format

**Testing**:
- Legacy project (no config) → uses 001- format
- New project with AFR config → creates AFR-001- branches
- Mixed repo with 001- and AFR-1234- → both work
- --linear-ticket AFR-1234 → creates AFR-1234-description

---

### Phase 3: Documentation Updates (P3)

**Goal**: Document custom format feature for users

**Files Changed**:
- `README.md`: Add configuration section
- `.specify/templates/constitution-template.md`: Add Linear format conventions

**Tasks**:
1. Add "Linear Ticket Configuration" section to README
2. Provide examples from AFR, ASR, AUROR teams
3. Document branch naming: `PREFIX-NUMBER-description`
4. Document commit format: `PREFIX-NUMBER Description`
5. Update constitution template with naming conventions
6. Add troubleshooting section for format issues

**Testing**:
- README includes 3+ team examples
- Constitution template has Linear format section
- Examples are clear and copy-pasteable

---

### Phase 4: Integration & Validation (P4)

**Goal**: Verify end-to-end workflows and backward compatibility

**Tasks**:
1. Test new project creation with custom format
2. Test legacy project compatibility (no config)
3. Test mixed repository scenarios
4. Verify config persistence across sessions
5. Test all edge cases from spec
6. Manual CLI interaction testing
7. Cross-check affected-files.md for completeness

**Acceptance**:
- All 6 testing scenarios from spec pass
- All 7 success criteria met
- Backward compatibility confirmed
- No regressions in existing workflows

## Integration Points

### Python CLI → Config File
- **Flow**: User input → Validation → JSON serialization → File write
- **Location**: `src/specify_cli/__init__.py` lines 1040-1050
- **Contract**: See [contracts/config-schema.json](./contracts/config-schema.json)

### Bash Scripts → Config File
- **Flow**: Script execution → Config read → Prefix extraction → Branch naming
- **Location**: `.specify/scripts/bash/common.sh` config_reader function
- **Fallback**: If no config, default to legacy `001-` format

### Branch Creation → Git Operations
- **Flow**: Config-driven prefix → Branch name generation → Git checkout -b
- **Location**: `.specify/scripts/bash/create-new-feature.sh` lines 213-238
- **Backward Compatibility**: Dual regex support in all git branch operations

## Risk Assessment

### High Risk
1. **Regex pattern changes in common.sh**: Used by multiple scripts, incorrect pattern breaks all features
   - **Mitigation**: Comprehensive testing with old/new formats, gradual rollout

2. **Backward compatibility**: Breaking existing workflows causes user disruption
   - **Mitigation**: Fallback logic, extensive legacy format testing

### Medium Risk
1. **Config file corruption**: Malformed JSON breaks workflow
   - **Mitigation**: Validation before write, graceful degradation to defaults

2. **Cross-platform compatibility**: Bash patterns may differ on macOS/Linux
   - **Mitigation**: Use POSIX-compliant regex, test on multiple platforms

### Low Risk
1. **CLI prompt UX**: Users unclear on what to enter
   - **Mitigation**: Clear examples in prompt, validation with helpful errors

2. **Documentation clarity**: Teams don't understand how to use feature
   - **Mitigation**: Multiple examples, clear step-by-step instructions

## Success Metrics

From spec.md Success Criteria (all must pass):

1. **SC-001**: Teams configure format in <1 minute → Verify with user testing
2. **SC-002**: 100% format consistency → Automated testing of branch/spec creation
3. **SC-003**: Config persists across sessions → Integration test with multiple runs
4. **SC-004**: 100% invalid input rejection → Validation test suite
5. **SC-005**: Documentation has 3+ team examples → Manual verification
6. **SC-006**: Zero breaking changes for legacy → Legacy project test suite
7. **SC-007**: Clear error messages → User testing + error message review

## Rollout Plan

### Stage 1: Internal Testing
- Deploy to spec-kit development environment
- Test with AFR, ASR, AUROR prefixes
- Verify backward compatibility with existing specs

### Stage 2: Team Pilot
- Roll out to Auror Facial Recognition team (AFR prefix)
- Collect feedback on CLI prompts and error messages
- Validate documentation clarity

### Stage 3: General Availability
- Merge to main branch
- Update README with announcement
- Create migration guide for existing projects

## Open Questions

None - All technical decisions resolved in research phase.

## Next Steps

1. Generate `research.md` with detailed technical decisions
2. Generate `data-model.md` with configuration schema
3. Generate `contracts/config-schema.json` with JSON schema
4. Generate `quickstart.md` for developer reference
5. Run `/speckit.tasks` to create actionable task list
6. Execute implementation via `/speckit.implement`

---

**Plan Complete** | Ready for `/speckit.tasks` phase
