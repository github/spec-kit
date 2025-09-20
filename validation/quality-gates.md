# Quality Gates

Quality gates are checkpoints that ensure work meets Spec Kit standards before proceeding to the next phase. Each gate has specific criteria that must be met for validation to pass.

## Specification Phase Gates

### Context Completeness Gate

**Purpose**: Ensure specification has sufficient context for successful implementation

**Validation Criteria**:
- [ ] **Documentation References**: All YAML references are accessible and specific
- [ ] **Similar Features**: At least 2-3 existing codebase patterns identified
- [ ] **External Research**: Minimum 1-2 authoritative sources documented
- [ ] **Library Gotchas**: Relevant gotchas from ai_docs/ documented
- [ ] **No Prior Knowledge Test**: Someone unfamiliar with codebase could implement successfully

**Failure Actions**:
- Conduct additional research to fill gaps
- Update ai_docs/ with missing gotchas or patterns
- Add more specific documentation references
- Clarify ambiguous or incomplete sections

### Requirements Clarity Gate

**Purpose**: Ensure all requirements are testable and unambiguous

**Validation Criteria**:
- [ ] **No Clarification Markers**: Zero [NEEDS CLARIFICATION] markers remain
- [ ] **Testable Requirements**: Every functional requirement can be tested
- [ ] **User Scenarios Complete**: All user journeys have acceptance criteria
- [ ] **Scope Boundaries**: Clear definition of what's included/excluded
- [ ] **Business Focus**: No implementation details in specification

**Failure Actions**:
- Research unclear requirements using external sources
- Clarify user scenarios with stakeholders
- Break down complex requirements into testable components
- Remove or relocate implementation details

## Planning Phase Gates

### Design Validation Gate

**Purpose**: Ensure technical design aligns with requirements and architectural principles

**Validation Criteria**:
- [ ] **Requirement Mapping**: All functional requirements addressed in design
- [ ] **Data Model Alignment**: Entities match requirement specifications
- [ ] **API Contract Coverage**: All user scenarios have corresponding endpoints
- [ ] **Integration Points**: External dependencies identified and documented
- [ ] **Error Handling Strategy**: Comprehensive error scenario coverage

**Failure Actions**:
- Revise design to cover missing requirements
- Add missing API contracts or data models
- Document additional integration points
- Define error handling approaches

### Constitutional Compliance Gate

**Purpose**: Verify design adheres to Spec Kit constitutional principles

**Validation Criteria**:
- [ ] **Library-First**: Feature implemented as reusable library
- [ ] **CLI Interface**: Library exposes command-line interface
- [ ] **Test Strategy**: Contract → Integration → Unit test progression planned
- [ ] **Simplicity**: No unnecessary abstractions or over-engineering
- [ ] **Observability**: Structured logging and monitoring planned

**Failure Actions**:
- Refactor design to follow library-first principle
- Add CLI interface design to library
- Restructure test strategy to follow constitutional order
- Simplify over-engineered components
- Add observability requirements

### Implementation Readiness Gate

**Purpose**: Confirm all prerequisites are met for implementation to begin

**Validation Criteria**:
- [ ] **Dependencies Available**: All external services and libraries accessible
- [ ] **Environment Setup**: Development environment documented and tested
- [ ] **Test Infrastructure**: Testing framework and test data prepared
- [ ] **Performance Benchmarks**: Success criteria and measurement approach defined
- [ ] **Integration Documentation**: All external system interfaces documented

**Failure Actions**:
- Set up missing development environment components
- Document or fix dependency accessibility issues
- Prepare test infrastructure and test data
- Define performance measurement approach
- Document external integration requirements

## Implementation Phase Gates

### Code Quality Gate

**Purpose**: Ensure implementation meets technical quality standards

**Validation Criteria**:
- [ ] **Type Safety**: Full type annotations (where applicable)
- [ ] **Error Handling**: Comprehensive error handling with meaningful messages
- [ ] **Documentation**: All public interfaces documented
- [ ] **No Debug Code**: No print statements, console.log, or debug artifacts
- [ ] **Style Consistency**: Code follows established project patterns
- [ ] **Security**: Input validation and secure coding practices applied

**Failure Actions**:
- Add missing type annotations
- Implement proper error handling
- Document public interfaces
- Remove debug code and artifacts
- Align code style with project conventions
- Add security validations

### Test Coverage Gate

**Purpose**: Ensure comprehensive testing coverage for all implemented functionality

**Validation Criteria**:
- [ ] **Contract Tests**: API contracts tested and passing
- [ ] **Integration Tests**: End-to-end user scenarios tested
- [ ] **Unit Tests**: Core business logic thoroughly tested
- [ ] **Edge Cases**: Boundary conditions and error scenarios covered
- [ ] **Test Quality**: Tests are focused, fast, and reliable
- [ ] **Red-Green-Refactor**: Evidence of test-first development in git history

**Failure Actions**:
- Add missing contract tests for API endpoints
- Implement integration tests for user scenarios
- Write unit tests for core business logic
- Add tests for edge cases and error scenarios
- Refactor tests for clarity and reliability
- Reorganize development approach to follow test-first

### Performance Gate

**Purpose**: Verify performance meets defined benchmarks and expectations

**Validation Criteria**:
- [ ] **Response Time**: API endpoints meet latency requirements
- [ ] **Throughput**: System handles expected load volume
- [ ] **Resource Usage**: Memory and CPU usage within acceptable limits
- [ ] **Database Performance**: No N+1 queries or inefficient database access
- [ ] **Scalability**: Performance degrades gracefully under load

**Failure Actions**:
- Optimize slow API endpoints
- Implement caching for expensive operations
- Fix database query inefficiencies
- Reduce resource usage through code optimization
- Add performance monitoring and alerting

## Quality Gate Automation

### Pre-commit Hooks

```bash
#!/bin/bash
# Quality gate enforcement in pre-commit hook

echo "Running Spec Kit quality gates..."

# Code quality checks
echo "- Code quality gate..."
ruff check . || mypy . || eslint . || exit 1

# Test coverage gate
echo "- Test coverage gate..."
coverage run -m pytest && coverage report --fail-under=80 || exit 1

# Security gate
echo "- Security gate..."
safety check || npm audit --audit-level moderate || exit 1

# Constitutional compliance
echo "- Constitutional compliance gate..."
find src/ -name "cli.py" -o -name "cli.js" | grep -q . || {
    echo "Error: No CLI interfaces found (violates library-first principle)"
    exit 1
}

echo "All quality gates passed ✅"
```

### CI/CD Integration

```yaml
# GitHub Actions workflow example
name: Quality Gates
on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Context Completeness Gate
        run: |
          # Check for NEEDS CLARIFICATION markers
          if grep -r "NEEDS CLARIFICATION" specs/; then
            echo "❌ Context Completeness Gate FAILED"
            exit 1
          fi
          echo "✅ Context Completeness Gate PASSED"

      - name: Constitutional Compliance Gate
        run: |
          # Check for CLI interfaces
          if ! find src/ -name "*cli*" | grep -q .; then
            echo "❌ Constitutional Compliance Gate FAILED"
            exit 1
          fi
          echo "✅ Constitutional Compliance Gate PASSED"

      - name: Test Coverage Gate
        run: |
          coverage run -m pytest
          coverage report --fail-under=80
          echo "✅ Test Coverage Gate PASSED"
```

## Gate Customization

### Project-Specific Gates

Projects can add custom quality gates by:

```yaml
# .spec-kit/quality-gates.yaml
custom_gates:
  - name: "API Documentation Gate"
    description: "Ensure all API endpoints are documented"
    validation:
      - "All endpoints have OpenAPI documentation"
      - "All request/response schemas defined"
      - "All error responses documented"

  - name: "Performance Benchmark Gate"
    description: "Meet project-specific performance targets"
    validation:
      - "API responses under 200ms p95"
      - "Database queries under 100ms p95"
      - "Memory usage under 512MB per process"
```

### Gate Weights and Scoring

```yaml
# Configure gate importance and scoring
gate_weights:
  context_completeness: 25
  constitutional_compliance: 30
  code_quality: 20
  test_coverage: 15
  performance: 10

pass_threshold: 80  # Minimum score to pass
```

Remember: Quality gates should enable quality, not slow down development. Adjust gates based on project needs and team maturity.