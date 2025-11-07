---
description: Analyze project health, complexity, and metrics
---

# Project Analysis

Analyze project health, code complexity, and quality metrics.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/project-analysis{SCRIPT_EXT}
```

## What This Analyzes

### Code Quality
- Code complexity metrics
- Duplicate code detection
- Code smells
- Technical debt

### Test Coverage
- Unit test coverage
- Integration test coverage
- Untested code paths
- Test quality

### Dependencies
- Outdated dependencies
- Security vulnerabilities
- License compliance
- Dependency graph

### Performance
- Bundle size
- Build time
- Test execution time
- Potential bottlenecks

## Metrics Reported

- Lines of code
- Cyclomatic complexity
- Test coverage percentage
- Dependency count
- Build time
- Technical debt ratio

## Output

Generates:
```
.analysis/code-quality.md
.analysis/test-coverage.md
.analysis/dependencies.md
.analysis/performance.md
```

## Use Cases

### Before Release
Ensure quality standards met

### Regular Reviews
Track quality trends over time

### Refactoring Decisions
Identify areas needing improvement

### Technical Debt
Quantify and prioritize debt

## Best Practices

- Run analysis regularly
- Track metrics over time
- Set quality thresholds
- Address critical issues promptly
- Share results with team

## Actions from Analysis

1. Review flagged issues
2. Prioritize improvements
3. Create refactoring tasks
4. Update dependencies
5. Improve test coverage
