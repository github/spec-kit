# Development Workflow

**Generic specification-driven development workflow**

---

## Overview

This workflow uses specifications as the primary source of truth, with code as the implementation. By writing detailed specifications before coding, we reduce ambiguity, improve planning, and deliver higher quality software.

---

## Workflow Phases

### Phase 1: Specification

**Goal:** Define what needs to be built

**Process:**
1. Understand the requirement
2. Create detailed specification
3. Validate specification quality
4. Get stakeholder approval

**Commands:**
- `/specify` - Create new specification
- `/validate` - Validate specification
- `/clarify` - Ask clarifying questions

**Output:**
- `.specs/<feature-name>.md`

**Best Practices:**
- Be specific and detailed
- Include acceptance criteria
- Identify dependencies and risks
- Define success metrics

---

### Phase 2: Planning

**Goal:** Break down how to build it

**Process:**
1. Review approved specification
2. Design technical approach
3. Break into phases
4. Estimate effort and timeline

**Commands:**
- `/plan` - Generate implementation plan
- `/analyze` - Check spec-plan alignment

**Output:**
- `.plans/<feature-name>-plan.md`

**Best Practices:**
- Organize into logical phases
- Identify dependencies
- Include testing and documentation
- Account for risks

---

### Phase 3: Task Breakdown

**Goal:** Create actionable tasks

**Process:**
1. Review implementation plan
2. Break phases into tasks
3. Set priorities
4. Map dependencies

**Commands:**
- `/tasks` - Generate task breakdown
- `/checklist` - Create quality checklist

**Output:**
- `.tasks/<feature-name>-tasks.md`
- `.checklists/<feature-name>-checklist.md`

**Best Practices:**
- Tasks should be 1-2 days max
- Include acceptance criteria
- Add testing tasks
- Document integration points

---

### Phase 4: Implementation

**Goal:** Build the feature

**Process:**
1. Review spec, plan, and tasks
2. Write tests first (TDD)
3. Implement incrementally
4. Run tests continuously
5. Update documentation

**Commands:**
- `/implement` - Get implementation guidance
- `/budget` - Check token usage
- `/find` - Search codebase
- `/error-context` - Analyze errors

**Best Practices:**
- Follow coding standards
- Commit frequently
- Keep changes focused
- Request early code reviews

---

### Phase 5: Validation

**Goal:** Ensure quality

**Process:**
1. Run all tests
2. Check code quality
3. Review against acceptance criteria
4. Get code review approval

**Commands:**
- `/validate` - Validate changes
- `/analyze` - Check consistency

**Quality Checks:**
- All tests passing
- Code coverage maintained
- No linting errors
- Documentation updated
- Acceptance criteria met

---

## Supporting Activities

### Token Management

**Commands:**
- `/budget` - Check current token usage
- `/prune` - Compress session context

**When to Use:**
- Regularly during long sessions
- Before starting major work
- When approaching limits

### Code Discovery

**Commands:**
- `/find "<query>"` - Semantic search
- `/discover` - Project structure
- `/project-catalog` - Component catalog

**When to Use:**
- Understanding unfamiliar code
- Finding similar patterns
- Locating integration points

### Error Handling

**Commands:**
- `/error-context` - Analyze errors
- `/clarify-history` - Review decisions

**When to Use:**
- Debugging issues
- Understanding failures
- Learning from mistakes

### Documentation

**Commands:**
- `/document` - Generate docs
- `/onboard` - Create onboarding
- `/constitution` - Project principles

**When to Use:**
- After major features
- When onboarding new members
- Establishing team norms

---

## Best Practices

### Specification Quality

✅ **Do:**
- Write clear, unambiguous requirements
- Include concrete acceptance criteria
- Identify all dependencies
- Define success metrics
- Consider edge cases

❌ **Don't:**
- Leave requirements vague
- Skip risk identification
- Ignore non-functional requirements
- Forget about error handling

### Planning Quality

✅ **Do:**
- Break work into phases
- Map dependencies clearly
- Estimate realistically
- Include testing and docs
- Plan for rollback

❌ **Don't:**
- Create monolithic plans
- Ignore technical debt
- Skip testing tasks
- Underestimate complexity

### Implementation Quality

✅ **Do:**
- Write tests first
- Follow project standards
- Commit frequently
- Document as you go
- Request reviews early

❌ **Don't:**
- Skip tests
- Take shortcuts
- Batch commits
- Leave code undocumented
- Wait to request review

---

## Common Patterns

### New Feature

```
1. /specify          # Create specification
2. /validate         # Validate spec
3. /plan             # Create plan
4. /tasks            # Break into tasks
5. /checklist        # Quality checklist
6. /implement        # Build feature
7. /validate         # Final validation
```

### Bug Fix

```
1. Reproduce issue
2. Write failing test
3. /error-context    # Analyze error
4. Fix bug
5. Verify test passes
6. Add regression test
```

### Refactoring

```
1. Document motivation
2. Ensure tests pass
3. /analyze          # Impact analysis
4. Make incremental changes
5. Run tests after each
6. Update documentation
```

---

## Workflow Tips

### Session Management

- Use `/resume` to start sessions
- Check `/budget` periodically
- Use `/prune` before major work
- Save context before breaks

### Quality Assurance

- Validate specifications early
- Run `/analyze` before implementing
- Use `/checklist` for reviews
- Keep artifacts synchronized

### Team Collaboration

- Share specifications for alignment
- Review plans together
- Discuss task priorities
- Communicate blockers early

---

## Tool Integration

### Version Control

```bash
# After specification
git add .specs/<feature>.md
git commit -m "Add specification for <feature>"

# After implementation
git add .
git commit -m "Implement <feature>"
```

### CI/CD Integration

```bash
# Validate specs in CI
./validate-all-specs.sh

# Run tests
npm test

# Check coverage
npm run coverage
```

### IDE Integration

- Use workspace settings for consistency
- Configure linting and formatting
- Set up test runners
- Enable auto-formatting

---

## Continuous Improvement

### Regular Reviews

- Review workflow quarterly
- Gather team feedback
- Update processes
- Share learnings

### Metrics

Track:
- Time from spec to deploy
- Defect rates
- Code review cycles
- Test coverage

### Learning

- Document lessons learned
- Share best practices
- Mentor new members
- Iterate on process

---

**Remember:** This workflow is a guideline, not a rulebook. Adapt it to your team's needs and context.
