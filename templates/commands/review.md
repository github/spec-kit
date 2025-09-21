---
description: Comprehensive code review using Spec Kit methodology and quality gates.
---

# Code Review - Quality Gates & Standards

**Review Context**: $ARGUMENTS

## Review Process

### 1. Analyze Changed Files

First, identify what needs to be reviewed:

```bash
# Check staged changes
git status
git diff --staged

# If nothing staged, review working directory changes
git diff
git status -s

# For pull request review, check the full diff
git diff main...HEAD
```

**Files to Review**:
- List all modified, added, or deleted files
- Prioritize by potential impact (core logic > configuration > docs)
- Note any files that might need coordinated changes

### 2. Spec Kit Alignment Review

**Constitution Compliance**:
- [ ] **Library-First**: Is feature implemented as reusable library?
- [ ] **CLI Interface**: Does library expose CLI with --help, --version, --format?
- [ ] **Test-First**: Are tests written before implementation (check git history)?
- [ ] **Integration Testing**: Are contract and integration tests present?
- [ ] **Observability**: Is structured logging included?
- [ ] **Simplicity**: No unnecessary abstractions or patterns?

**Specification Alignment**:
- [ ] Implementation matches functional requirements from spec
- [ ] User scenarios from spec are fully addressed
- [ ] No implementation details that should be in plan, not spec
- [ ] Context engineering guidelines followed (patterns, gotchas addressed)

### 3. Technical Quality Review

#### Code Quality
- [ ] **Type Safety**: Type hints on all functions and classes (Python/TypeScript)
- [ ] **Error Handling**: Proper exception handling with meaningful messages
- [ ] **Naming**: Clear, descriptive variable and function names
- [ ] **Documentation**: Functions documented with clear purpose and examples
- [ ] **No Debug Code**: No print statements, console.log, or debug artifacts
- [ ] **Style Consistency**: Follows established codebase patterns

#### Security Review
- [ ] **Input Validation**: All user inputs validated before processing
- [ ] **SQL Injection**: Parameterized queries used, no string concatenation
- [ ] **Authentication**: Proper authentication/authorization checks
- [ ] **Secret Management**: No hardcoded passwords, API keys, or secrets
- [ ] **Data Exposure**: Sensitive data not logged or exposed in errors

#### Performance & Scalability
- [ ] **Efficient Algorithms**: No obvious algorithmic inefficiencies
- [ ] **Database Access**: No N+1 queries or excessive database calls
- [ ] **Resource Management**: Proper cleanup of connections, files, memory
- [ ] **Caching**: Appropriate caching for expensive operations
- [ ] **Async Patterns**: Correct use of async/await where applicable

### 4. Integration & Architecture Review

#### Library Integration
- [ ] **Dependencies**: New dependencies justified and documented
- [ ] **Library Gotchas**: Known gotchas from ai_docs/ addressed
- [ ] **API Contracts**: External API usage follows documented contracts
- [ ] **Error Propagation**: Errors properly caught and transformed
- [ ] **Configuration**: Environment-specific config properly handled

#### Testing Strategy
- [ ] **Test Coverage**: New code has appropriate test coverage
- [ ] **Test Quality**: Tests are focused, fast, and reliable
- [ ] **Integration Tests**: Critical paths have integration test coverage
- [ ] **Contract Tests**: API contracts tested and validated
- [ ] **Edge Cases**: Boundary conditions and error scenarios tested

### 5. Context Engineering Review

Check if implementation follows context engineering principles:

**ULTRATHINK**: Before evaluating patterns, deeply analyze:
- Why were these specific patterns chosen over alternatives?
- What are the long-term implications of pattern choices?
- Are there hidden coupling issues between components?
- How will these patterns affect future feature development?
- What failure modes are introduced by the chosen architecture?

**Pattern Consistency**:
- [ ] Similar features implemented with consistent patterns
- [ ] Established codebase conventions followed
- [ ] Library-specific patterns correctly applied

**Documentation References**:
- [ ] Implementation follows patterns referenced in spec
- [ ] External documentation recommendations implemented
- [ ] Known gotchas and workarounds applied correctly

### 6. Review Report Generation

Create a structured review report:

#### 🟢 Strengths
- List well-implemented aspects
- Note good patterns that should be replicated
- Acknowledge complex problems solved elegantly

#### 🟡 Minor Issues
- Code style inconsistencies
- Missing documentation
- Non-critical performance opportunities
- Suggested improvements

#### 🔴 Major Issues
- Security vulnerabilities
- Performance problems
- Spec/constitution violations
- Breaking changes without proper handling

#### 📋 Action Items
- [ ] **Critical**: [Issue description] - must fix before merge
- [ ] **Important**: [Issue description] - should fix in this PR
- [ ] **Suggestion**: [Issue description] - consider for future improvement

### 7. Specific Language Reviews

#### Python Review Focus
- [ ] **Pydantic v2**: Using ConfigDict, field_validator, model_dump()
- [ ] **Type Hints**: All functions have proper type annotations
- [ ] **Async/Await**: Correct async patterns for I/O operations
- [ ] **Exception Handling**: Specific exception types caught, not bare except
- [ ] **Imports**: Standard library first, third-party, then local imports

#### TypeScript/JavaScript Review Focus
- [ ] **Type Definitions**: Proper interfaces and type definitions
- [ ] **Error Handling**: Proper error boundaries and error propagation
- [ ] **Async Patterns**: Correct Promise handling, no callback hell
- [ ] **Memory Leaks**: Event listeners cleaned up, subscriptions closed
- [ ] **Bundle Impact**: Consider impact on bundle size for frontend code

### 8. Review Completion

#### Before Approval
- [ ] All critical issues addressed
- [ ] Tests pass (run test suite)
- [ ] Linting passes (run project linters)
- [ ] Build succeeds (if applicable)
- [ ] Documentation updated (if needed)

#### After Approval
- Document lessons learned for future reviews
- Update review checklists if new patterns emerge
- Consider if new items should be added to ai_docs/

## Review Report Template

```markdown
# Code Review: [Feature/PR Title]

## Summary
[Brief overview of changes and their purpose]

## Spec Kit Alignment
[Constitutional compliance and specification alignment notes]

## Technical Assessment
### Strengths
- [List positive aspects]

### Issues Found
#### 🔴 Critical (Must Fix)
- [List blocking issues]

#### 🟡 Minor (Should Fix)
- [List improvements]

#### 💡 Suggestions (Consider)
- [List optional enhancements]

## Test Coverage
[Assessment of test quality and coverage]

## Performance Impact
[Any performance considerations]

## Security Review
[Security assessment results]

## Final Recommendation
- [ ] **Approve**: Ready to merge
- [ ] **Approve with Comments**: Minor issues, can merge after addressing
- [ ] **Request Changes**: Major issues must be addressed before merge

## Follow-up Actions
- [Any items for future consideration]
```

Remember: The goal is to maintain code quality while helping the team grow and learn. Be constructive and specific in feedback.