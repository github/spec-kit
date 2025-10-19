# Guard CLI - MVP Scope

## What's Included in MVP

### Core Commands
- `specify guard create` - Create guards with opinionated boilerplate
- `specify guard run` - Execute guard validation
- `specify guard list` - List registered guards
- `specify guard types` - Discover available guard types
- `specify guard create-type` - Create custom guard types

### Guard Types (MVP)
1. **unit-pytest** - Unit testing with pytest (fully implemented)
2. **api** - REST API contract validation (fully implemented)
3. **Custom types architecture** - types/ (official) + types-custom/ (user-defined)

### System Features
- File-based registry (`.specify/guards/list/`, `history/`, `index.json`)
- Execution history tracking with notes for self-healing
- Guard type discovery from both official and custom directories
- Rich CLI output with tables
- Integration with Spec Kit slash commands (`/plan`, `/tasks`, `/implement`)

## What's Excluded from MVP

### Deferred Guard Types
- `database` - Schema/migration validation (add in v0.2.0)
- `lint-ruff` - Code quality checks (add in v0.2.0)
- `docker-playwright` - E2E browser testing (add in v0.2.0)

**Rationale**: Focus on core guard creation/execution. Additional types can be added incrementally as marketplace expands.

### Deferred Features
- `specify guard install` - Install guard types from packages (P4 - extensibility)
- `specify guard validate-type` - Validate guard type structure (P4)
- Format options for `guard list` (--format json/table/ids)
- Filter options for `guard types` (--filter category)
- Task association (`--task` flag for guard run)

## MVP Validation

**Guards for Validation:**
- G001: all-unit-tests (21 tests covering registry, executor, types, utils)
- G002: test-commands (guard CLI command tests)

**Success Criteria:**
- ✅ Guards can be created via `specify guard create`
- ✅ Guards can be executed via `specify guard run` with pass/fail
- ✅ All 21 unit tests pass
- ✅ Custom types can be created and used
- ✅ History tracking works
- ✅ Slash commands have guard integration

## Post-MVP Roadmap

**v0.2.0 - Guard Types Expansion:**
- Add database, lint-ruff, docker-playwright guard types
- Enhanced scaffolders with more templates
- Validator abstractions

**v0.3.0 - Marketplace Features:**
- `specify guard install` for community guard types
- Guard type validation
- Version management

**v0.4.0 - Advanced Features:**
- Guard composition (run multiple guards)
- Parallel guard execution
- Guard result caching
- Performance analytics
