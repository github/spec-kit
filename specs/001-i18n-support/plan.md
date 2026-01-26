# Implementation Plan: Internationalization Support

**Branch**: `001-i18n-support` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-i18n-support/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add comprehensive internationalization (i18n) support to Specify CLI with Chinese (Simplified, zh_CN) as the first additional language. This enables non-English speaking developers to use the entire toolkit in their native language, including CLI messages, templates, documentation, and error handling. The system uses Python's Babel library with gettext standards, environment variable-based language selection (`SPECIFY_LANG`), and graceful fallback to English.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer`, `rich`, `babel` (NEW), `httpx`, `platformdirs`, `readchar`, `truststore`  
**Storage**: File-based translation catalogs (POT/PO/MO files), localized template copies  
**Testing**: pytest with i18n-specific test cases for translation loading, fallback behavior, and template localization  
**Target Platform**: Cross-platform (Linux, macOS, Windows) with UTF-8 terminal support  
**Project Type**: Single CLI application with extensive template system  
**Performance Goals**: <100ms overhead for language initialization, no degradation in CLI response time  
**Constraints**: Must maintain 100% feature parity across all languages, zero regression in English functionality  
**Scale/Scope**: 34 functional requirements, 4 user stories, ~200-300 translatable messages, 10+ template files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Template-First Development

- ✅ **PASS**: Localized templates will maintain same placeholder structure as English templates
- ✅ **PASS**: Template localization process documented and systematic
- ⚠️ **VERIFY IN PHASE 1**: Ensure all agent-specific command templates can be localized

### Principle II: Multi-Agent Compatibility

- ✅ **PASS**: Localization will be applied to all agent command templates (Claude, Cursor, Gemini, etc.)
- ✅ **PASS**: Agent-specific directory structures preserved across languages
- ⚠️ **VERIFY IN PHASE 1**: Test template generation for all supported agents in both English and Chinese

### Principle III: Internationalization & Accessibility (NON-NEGOTIABLE)

- ✅ **PASS**: This feature directly implements the Phase 1 requirements of Constitution Principle III
- ✅ **PASS**: Uses environment variable (`SPECIFY_LANG`) as specified in constitution
- ✅ **PASS**: Translation files stored in `src/specify_cli/i18n/` as mandated
- ✅ **PASS**: Localized templates in `templates/i18n/<lang>/` as mandated
- ✅ **PASS**: Documentation in `docs/i18n/<lang>/` as mandated

### Principle IV: Simplicity & YAGNI

- ✅ **PASS**: Uses industry-standard Babel library, avoiding custom i18n implementation
- ✅ **PASS**: Simple environment variable configuration, no complex setup required
- ✅ **PASS**: Fallback mechanism is straightforward (missing translation → English)

### Principle V: Documentation-First

- ✅ **PASS**: Comprehensive documentation planned for both English and Chinese
- ✅ **PASS**: Translation contribution guide will be created
- ✅ **PASS**: Language selection guide in both languages

### Principle VI: Test Compatibility

- ✅ **PASS**: I18n system does not interfere with test generation workflows
- ✅ **PASS**: Test templates will be localized same as other templates

**Gate Status**: ✅ **PASSED** - All constitutional principles satisfied. Feature fully aligns with project constitution.

## Project Structure

### Documentation (this feature)

```text
specs/001-i18n-support/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command) - N/A for this feature
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/specify_cli/
├── __init__.py          # MODIFY: Add i18n initialization, language detection
├── i18n/                # NEW: Translation infrastructure
│   ├── __init__.py      # NEW: I18n module exports (get_translator, set_language, etc.)
│   ├── core.py          # NEW: Core i18n logic (LocaleContext, language detection, catalog loading)
│   ├── messages.pot     # NEW: Master translation template (English source strings)
│   ├── zh_CN/           # NEW: Chinese translations
│   │   └── LC_MESSAGES/
│   │       ├── messages.po  # NEW: Chinese translation file (human-editable)
│   │       └── messages.mo  # NEW: Compiled Chinese translations (binary)
│   └── en_US/           # NEW: English translations (optional, for consistency)
│       └── LC_MESSAGES/
│           ├── messages.po
│           └── messages.mo
│
templates/
├── i18n/                # NEW: Localized template directory
│   ├── zh_CN/           # NEW: Chinese template versions
│   │   ├── spec-template.md
│   │   ├── plan-template.md
│   │   ├── tasks-template.md
│   │   ├── checklist-template.md
│   │   ├── agent-file-template.md
│   │   └── commands/    # NEW: Chinese command templates
│   │       ├── analyze.md
│   │       ├── checklist.md
│   │       ├── clarify.md
│   │       ├── constitution.md
│   │       ├── implement.md
│   │       ├── plan.md
│   │       ├── specify.md
│   │       ├── tasks.md
│   │       └── taskstoissues.md
│   └── en_US/           # NEW: Explicit English templates (symlinks to root templates)
│
docs/
├── i18n/                # NEW: Localized documentation
│   └── zh_CN/           # NEW: Chinese documentation
│       ├── README.md
│       ├── quickstart.md
│       ├── installation.md
│       ├── local-development.md
│       └── upgrade.md
│
tests/
├── i18n/                # NEW: I18n-specific tests
│   ├── test_core.py     # NEW: Test language detection, catalog loading, fallback
│   ├── test_messages.py # NEW: Test CLI message translation
│   └── test_templates.py # NEW: Test template localization
│
scripts/
├── i18n/                # NEW: I18n tooling scripts
│   ├── extract-messages.sh    # NEW: Extract translatable strings to POT file
│   ├── compile-translations.sh # NEW: Compile PO to MO files
│   └── check-coverage.sh      # NEW: Validate translation completeness
│
.github/
└── workflows/
    └── i18n-check.yml   # NEW: CI workflow to validate translations
```

**Structure Decision**: Single project structure with dedicated i18n subdirectories for translations, templates, and documentation. This approach keeps all language-specific content organized and easily discoverable while maintaining the existing project structure.

## Complexity Tracking

No constitutional violations. All complexity is justified and necessary for the feature requirements.

---

## Phase 0: Research - ✅ COMPLETE

Research completed on Python i18n best practices. Key findings:

- **Library choice**: Babel + Python gettext provides best cross-platform support
- **Workflow**: Standard PO/MO file workflow with `pybabel` tooling
- **Performance**: <10ms catalog load, <1μs message lookup - no overhead concerns
- **Chinese pluralization**: Simplified (nplurals=1), use consistent ngettext() pattern
- **Template strategy**: Separate localized template files, preserve placeholders exactly
- **Fallback**: Built-in gettext fallback chain handles missing translations gracefully

See [research.md](./research.md) for complete findings and implementation recommendations.

---

## Phase 1: Design & Contracts - ✅ COMPLETE

### Data Model

Defined 5 core entities for i18n system:

1. **Language**: Metadata for supported languages (code, display name, catalog paths)
2. **TranslationCatalog**: Collection of translated messages (PO/MO files)
3. **TemplateSet**: Localized template files maintaining structure
4. **LocaleContext**: Runtime translation context (active locale, translator functions)
5. **TranslationKey**: Unique identifiers for translatable messages

See [data-model.md](./data-model.md) for complete entity definitions, relationships, and validation rules.

### Contracts

No API contracts needed - this is CLI-only functionality with file-based translations.

### Agent Context

✅ Updated Cursor agent context file with:

- Python 3.11+ as language
- Babel added to framework dependencies
- File-based translation catalogs as storage
- Single CLI application project type

### Quickstart Guide

Created comprehensive quickstart documentation covering:

- **Users**: Setting `SPECIFY_LANG`, using CLI in Chinese, troubleshooting
- **Developers**: Marking translatable strings, extraction workflow, testing
- **Translators**: Editing PO files, translation guidelines, technical terms
- **Template Translators**: Localizing templates, preserving placeholders
- **Maintainers**: Adding new languages, updating translations, CI/CD

See [quickstart.md](./quickstart.md) for complete guide.

---

## Phase 2: Planning Summary - ✅ COMPLETE

### Implementation Ready

All planning artifacts complete and validated against constitution:

- ✅ **Research**: Technology decisions documented with rationale
- ✅ **Data Model**: 5 entities defined with relationships and validation
- ✅ **Quickstart**: Comprehensive usage and workflow documentation
- ✅ **Constitutional Compliance**: All 6 principles validated and passed
- ✅ **Agent Context**: Updated with i18n technology stack

### Next Steps

Ready for `/speckit.tasks` to generate implementation task breakdown.

The planning phase has established:

1. **Clear architecture**: Babel for tooling, gettext for runtime, separate localized templates
2. **File organization**: Standard PO/MO structure in `src/specify_cli/i18n/`, templates in `templates/i18n/`
3. **Workflow processes**: Extraction → Translation → Compilation pipeline documented
4. **Quality gates**: Translation coverage checks, placeholder validation, CI/CD integration
5. **Extensibility path**: Adding new languages follows documented pattern

### Key Technical Decisions

- **Babel >=2.12.0** for extraction/compilation (cross-platform)
- **Environment variable** `SPECIFY_LANG` for language selection
- **Named arguments** (`.format()`) for all variable interpolation
- **Separate template files** per language, preserving `[PLACEHOLDERS]`
- **Fallback chain**: `zh_CN` → `en_US` → original string

### Estimated Scope

- **~200-300 translatable messages** in CLI code
- **10+ template files** to localize
- **5 core documentation files** to translate
- **34 functional requirements** to implement
- **4 user stories** (P1-P4) to deliver independently
