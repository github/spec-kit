---
description: Run validation gates to ensure quality and readiness at any stage of development.
---

# Validate - Quality Gates Enforcement

**Validation Target**: $ARGUMENTS

## Available Validation Gates

### 1. Specification Validation
**Ultrathink** Validates that a feature specification is complete and ready for planning.

```bash
# Run validation on current feature spec
/validate spec [spec-file-path]
```

**Validation Criteria**:
- [ ] **Context Completeness**: All required context items documented
- [ ] **Requirements Clarity**: No [NEEDS CLARIFICATION] markers remain
- [ ] **User Scenarios**: Complete user stories with acceptance criteria
- [ ] **Functional Requirements**: All requirements testable and unambiguous
- [ ] **Business Focus**: No implementation details in spec
- [ ] **Research Quality**: External research findings documented
- [ ] **Similar Features**: Codebase patterns identified and referenced

### 2. Plan Validation
**Ultrathink** Validates that an implementation plan meets all quality gates.

```bash
# Run validation on current implementation plan
/validate plan [plan-file-path]
```

**Validation Criteria**:
- [ ] **Context Integration**: Implementation blueprint references correct patterns
- [ ] **Constitution Compliance**: All constitutional requirements met
- [ ] **Design Completeness**: Data models, contracts, and tests defined
- [ ] **Dependency Verification**: All external dependencies accessible
- [ ] **Test Strategy**: Complete testing approach documented
- [ ] **Performance Benchmarks**: Performance expectations defined (if applicable)
- [ ] **Integration Points**: All system integration points identified

### 3. Implementation Validation
**Ultrathink** Validates that code implementation meets Spec Kit standards.

```bash
# Run validation on current implementation
/validate implementation [target-directory]
```

**Validation Criteria**:
- [ ] **Constitutional Alignment**: Library-first, CLI interface, test-first
- [ ] **Code Quality**: Type safety, error handling, documentation
- [ ] **Security Standards**: Input validation, no hardcoded secrets
- [ ] **Performance Considerations**: No obvious bottlenecks or inefficiencies
- [ ] **Test Coverage**: Comprehensive test suite covering all scenarios
- [ ] **Integration Tests**: Contract and integration tests present and passing

### 4. Repository Validation
**Ultrathink** Validates overall repository health and compliance.

```bash
# Run validation on entire repository
/validate repository
```

**Validation Criteria**:
- [ ] **Project Structure**: Follows Spec Kit directory conventions
- [ ] **Documentation**: README, constitution, and specs up to date
- [ ] **Git Health**: Clean history, proper branching, no secrets in history
- [ ] **Dependencies**: All dependencies documented and up to date
- [ ] **CI/CD**: Automated testing and validation in place
- [ ] **Security**: No exposed secrets, proper access controls

## Detailed Validation Processes

### Context Engineering Validation

**Check Documentation References**:
```bash
# Verify all referenced URLs are accessible
# Check that file references exist and contain expected patterns
# Validate ai_docs/ files are current and accurate
```

**Validation Steps**:
1. Parse YAML documentation references from spec
2. Verify URL accessibility (200 status codes)
3. Check file existence and read permissions
4. Validate patterns mentioned actually exist in referenced files
5. Confirm ai_docs/ references are current and complete

### Constitutional Validation

**Library-First Principle**:
- [ ] Feature implemented as standalone library
- [ ] Library has clear, documented purpose
- [ ] No direct application code in core logic

**CLI Interface Principle**:
- [ ] Library exposes CLI commands
- [ ] Commands support --help, --version, --format flags
- [ ] Text-based input/output protocol followed

**Test-First Principle** (NON-NEGOTIABLE):
- [ ] Git history shows tests committed before implementation
- [ ] RED-GREEN-Refactor cycle evidence in commits
- [ ] Contract tests written first, then integration, then unit tests
- [ ] No implementation commits without corresponding test commits

### Quality Gate Automation

**Automated Checks**:
```bash
# Run linting and type checking
ruff check . || mypy . || eslint . || tsc --noEmit

# Run test suite
pytest || npm test || go test ./... || cargo test

# Check for secrets
git-secrets --scan || truffleHog .

# Dependency vulnerability scan
safety check || npm audit || go mod download

# Performance regression check
hyperfine './benchmark.sh' --warmup 3 --min-runs 10
```

### Integration Validation

**External Dependencies**:
- [ ] All APIs accessible and responding correctly
- [ ] Database connections established and tested
- [ ] Required services running and healthy
- [ ] Authentication credentials valid

**Internal Integration**:
- [ ] Module interfaces compatible
- [ ] Shared schemas validated
- [ ] Event contracts honored
- [ ] Data flow integrity maintained

## Validation Reporting

### Validation Report Format

```markdown
# Validation Report: [Target] - [Timestamp]

## Overall Status: [PASS/FAIL/WARNING]

### Gate Results
| Gate | Status | Score | Critical Issues |
|------|--------|-------|----------------|
| Context Engineering | ✅ PASS | 95% | 0 |
| Constitution Compliance | ❌ FAIL | 60% | 2 |
| Code Quality | ⚠️  WARNING | 85% | 0 |
| Security | ✅ PASS | 100% | 0 |

### Critical Issues (Must Fix)
1. **[Issue Category]**: [Specific problem description]
   - **Impact**: [Why this blocks progress]
   - **Resolution**: [What needs to be done]

### Warnings (Should Fix)
1. **[Issue Category]**: [Specific problem description]
   - **Impact**: [Potential future problems]
   - **Suggestion**: [Recommended action]

### Quality Metrics
- **Test Coverage**: 85%
- **Documentation Coverage**: 90%
- **Constitutional Compliance**: 75%
- **Performance Score**: 92%

### Next Steps
- [ ] Address critical issues before proceeding
- [ ] Consider warnings for next iteration
- [ ] Update documentation based on findings

## Recommendation
**[PROCEED/BLOCK/CONDITIONAL]**: [Explanation of recommendation]
```

### Continuous Validation

**Pre-commit Hooks**:
```bash
#!/bin/bash
# Add to .git/hooks/pre-commit
/validate implementation --critical-only
if [ $? -ne 0 ]; then
    echo "Critical validation failures detected. Commit blocked."
    exit 1
fi
```

**CI/CD Integration**:
```yaml
# Add to CI pipeline
- name: Spec Kit Validation
  run: |
    /validate repository
    /validate implementation
    /validate plan --if-exists
```

## Validation Configuration

### Custom Validation Rules
Create `.spec-kit/validation.yaml` for project-specific rules:

```yaml
validation:
  gates:
    specification:
      required_sections: ['Context Engineering', 'User Scenarios', 'Requirements']
      max_clarifications: 0
    implementation:
      min_test_coverage: 80
      required_linters: ['ruff', 'mypy']
    constitution:
      enforce_test_first: true
      require_cli_interface: true
```

### Gate Weights
Configure how different validation aspects are weighted:

```yaml
weights:
  constitution_compliance: 40
  code_quality: 30
  test_coverage: 20
  documentation: 10
```

## Troubleshooting Validation Failures

### Common Issues
1. **"Context references not found"**: Update ai_docs/ or fix file paths
2. **"Constitutional violation: No CLI interface"**: Add command-line interface to library
3. **"Test-first violation detected"**: Reorganize git history or add missing tests
4. **"Performance regression detected"**: Profile and optimize slow operations

### Recovery Strategies
- Use `/debug` command for systematic troubleshooting
- Reference ai_docs/library_gotchas.md for known issues
- Check similar features for successful patterns
- Run partial validation to isolate specific problems

Remember: Validation gates exist to prevent problems, not create barriers. Use them as quality improvement tools.
