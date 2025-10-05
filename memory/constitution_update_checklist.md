# Constitution Update Checklist

When amending the constitution (`/memory/constitution.md`), ensure all dependent documents are updated to maintain consistency.

## Templates to Update

### When adding/modifying ANY article:
- [ ] `/templates/plan-template.md` - Update Constitution Check section
- [ ] `/templates/spec-template.md` - Update if requirements/scope affected
- [ ] `/templates/tasks-template.md` - Update if new task types needed
- [ ] `/.claude/commands/plan.md` - Update if planning process changes
- [ ] `/.claude/commands/tasks.md` - Update if task generation affected
- [ ] `/CLAUDE.md` - Update runtime development guidelines

### Article-specific updates:

#### Article I (Library-First):
- [ ] Ensure templates emphasize library creation
- [ ] Update CLI command examples
- [ ] Add llms.txt documentation requirements

#### Article II (CLI Interface):
- [ ] Update CLI flag requirements in templates
- [ ] Add text I/O protocol reminders

#### Article III (Test-First):
- [ ] Update test order in all templates
- [ ] Emphasize TDD requirements
- [ ] Add test approval gates

#### Article IV (Integration Testing):
- [ ] List integration test triggers
- [ ] Update test type priorities
- [ ] Add real dependency requirements

#### Article V (Observability):
- [ ] Add logging requirements to templates
- [ ] Include multi-tier log streaming
- [ ] Update performance monitoring sections

#### Article VI (Versioning):
- [ ] Add version increment reminders
- [ ] Include breaking change procedures
- [ ] Update migration requirements

#### Article VII (Simplicity):
- [ ] Update project count limits
- [ ] Add pattern prohibition examples
- [ ] Include YAGNI reminders

#### Article VIII (Atomic Development & Scope Management):
- [ ] Add LOC budget tracking to plan-template.md (200-500 LOC targets)
- [ ] Include /decompose workflow references in templates
- [ ] Add justification requirements for >500 LOC
- [ ] Update tasks-template.md with budget validation gates
- [ ] Add decomposition benefits (faster reviews, parallel work, manageable TDD)
- [ ] Document capability sizing guidelines (200-400 ideal, 400-500 acceptable, >500 exceptional)

## Validation Steps

1. **Before committing constitution changes:**
   - [ ] All templates reference new requirements
   - [ ] Examples updated to match new rules
   - [ ] No contradictions between documents

2. **After updating templates:**
   - [ ] Run through a sample implementation plan
   - [ ] Verify all constitution requirements addressed
   - [ ] Check that templates are self-contained (readable without constitution)

3. **Version tracking:**
   - [ ] Update constitution version number
   - [ ] Note version in template footers
   - [ ] Add amendment to constitution history

## Common Misses

Watch for these often-forgotten updates:
- Command documentation (`/commands/*.md`)
- Checklist items in templates
- Example code/commands
- Domain-specific variations (web vs mobile vs CLI)
- Cross-references between documents

## Template Sync Status

Last sync check: 2025-10-05
- Constitution template version: Updated with Article VIII placeholder
- Templates aligned: ✅ (decompose, plan, tasks include LOC budgeting and atomic development workflow)
- Recent updates:
  - 2025-10-05: Added Article VIII (Atomic Development) to constitution template and checklist
  - 2025-10-05: LOC budget tracking added to plan-template.md and tasks-template.md
  - 2025-10-05: Decomposition workflow (/decompose) integrated into spec-kit methodology

---

*This checklist ensures the constitution's principles are consistently applied across all project documentation.*