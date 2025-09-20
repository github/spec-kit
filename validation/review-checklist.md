# Review Checklists

Comprehensive checklists for different types of reviews in the Spec Kit development process. Use these to ensure consistent, thorough reviews across all work.

## Specification Review Checklist

### Content Quality Review
- [ ] **Business Focus**: No implementation details (no tech stack, APIs, database schemas)
- [ ] **User-Centered**: Written for business stakeholders, not developers
- [ ] **Complete Sections**: All mandatory sections filled out appropriately
- [ ] **Clear Language**: Technical jargon avoided, plain language used
- [ ] **Scope Boundaries**: What's included and excluded is clearly defined

### Requirements Quality Review
- [ ] **No Ambiguity**: Zero [NEEDS CLARIFICATION] markers remain
- [ ] **Testable Requirements**: Each functional requirement can be verified
- [ ] **Measurable Success**: Success criteria are quantifiable
- [ ] **User Scenarios**: Complete user journeys with acceptance criteria
- [ ] **Edge Cases**: Boundary conditions and error scenarios identified

### Context Engineering Review
- [ ] **Context Completeness**: Passes "No Prior Knowledge" test
- [ ] **Documentation References**: All YAML references are accessible and specific
- [ ] **Similar Features**: Existing codebase patterns identified and referenced
- [ ] **External Research**: Best practices and gotchas documented
- [ ] **Implementation Readiness**: Sufficient context for successful implementation

### Constitutional Alignment Review
- [ ] **Library-First Thinking**: Feature conceptualized as reusable component
- [ ] **CLI Interface Consideration**: Command-line interface requirements noted
- [ ] **Test Strategy**: Testing approach aligns with constitutional principles
- [ ] **Simplicity**: No unnecessary complexity or over-engineering
- [ ] **Observability**: Logging and monitoring requirements considered

## Implementation Plan Review Checklist

### Design Completeness Review
- [ ] **Requirement Coverage**: All functional requirements addressed
- [ ] **Technical Context**: Technology stack and dependencies clearly defined
- [ ] **Data Model**: Entities and relationships properly defined
- [ ] **API Contracts**: All user scenarios have corresponding endpoints
- [ ] **Integration Points**: External dependencies identified and documented

### Constitutional Compliance Review
- [ ] **Library Structure**: Feature implemented as standalone library
- [ ] **CLI Interface**: Library exposes command-line interface
- [ ] **Test Strategy**: Contract → Integration → Unit progression planned
- [ ] **Simplicity Check**: No unnecessary abstractions or patterns
- [ ] **Observability Plan**: Structured logging and monitoring included

### Implementation Blueprint Review
- [ ] **Context Integration**: References correct patterns from codebase
- [ ] **Known Gotchas**: Library-specific issues addressed
- [ ] **Validation Gates**: All quality gates defined and achievable
- [ ] **Dependencies**: All external requirements accessible
- [ ] **Performance**: Benchmarks and optimization strategies defined

### Quality Gates Review
- [ ] **Gate Definitions**: Each gate has clear pass/fail criteria
- [ ] **Automation Potential**: Gates can be automated where appropriate
- [ ] **Failure Recovery**: Actions defined for gate failures
- [ ] **Progressive Validation**: Gates build upon each other logically
- [ ] **Team Alignment**: Gates align with team practices and tools

## Code Implementation Review Checklist

### Code Quality Review
- [ ] **Type Safety**: Full type annotations (Python/TypeScript/etc.)
- [ ] **Error Handling**: Comprehensive error handling with meaningful messages
- [ ] **Documentation**: All public interfaces documented with examples
- [ ] **Naming**: Clear, descriptive variable and function names
- [ ] **No Debug Code**: No print statements, console.log, or debug artifacts
- [ ] **Style Consistency**: Follows established project patterns

### Security Review
- [ ] **Input Validation**: All user inputs validated before processing
- [ ] **SQL Injection**: Parameterized queries used, no string concatenation
- [ ] **Authentication**: Proper authentication/authorization checks
- [ ] **Secret Management**: No hardcoded passwords, API keys, or secrets
- [ ] **Data Exposure**: Sensitive data not logged or exposed in errors
- [ ] **HTTPS/TLS**: Secure communication protocols used

### Performance Review
- [ ] **Efficient Algorithms**: No obvious algorithmic inefficiencies
- [ ] **Database Access**: No N+1 queries or excessive database calls
- [ ] **Resource Management**: Proper cleanup of connections, files, memory
- [ ] **Caching**: Appropriate caching for expensive operations
- [ ] **Async Patterns**: Correct use of async/await where applicable
- [ ] **Memory Leaks**: No circular references or unclosed resources

### Constitutional Compliance Review
- [ ] **Library-First**: Feature implemented as reusable library
- [ ] **CLI Interface**: Library exposes CLI with --help, --version, --format
- [ ] **Test-First Evidence**: Git history shows tests before implementation
- [ ] **Integration Testing**: Contract and integration tests present
- [ ] **Structured Logging**: Proper logging with structured format
- [ ] **Simplicity**: No unnecessary abstractions or over-engineering

### Testing Review
- [ ] **Contract Tests**: API contracts tested and passing
- [ ] **Integration Tests**: End-to-end user scenarios tested
- [ ] **Unit Tests**: Core business logic thoroughly tested
- [ ] **Edge Cases**: Boundary conditions and error scenarios covered
- [ ] **Test Quality**: Tests are focused, fast, and reliable
- [ ] **Coverage**: Adequate test coverage for all new code

## Pull Request Review Checklist

### Change Analysis
- [ ] **Scope Appropriateness**: Changes match PR description and intent
- [ ] **Single Responsibility**: PR addresses one logical change
- [ ] **File Organization**: Related changes grouped appropriately
- [ ] **Breaking Changes**: Breaking changes properly documented
- [ ] **Migration Plan**: Data migration or upgrade path provided if needed

### Git History Review
- [ ] **Commit Messages**: Follow conventional commit format
- [ ] **Logical Commits**: Each commit represents logical unit of work
- [ ] **Test-First Evidence**: Tests committed before implementation
- [ ] **Clean History**: No merge commits, fixup commits, or debug commits
- [ ] **Constitutional Compliance**: Commits show library-first development

### Integration Review
- [ ] **Dependency Management**: New dependencies justified and documented
- [ ] **Configuration**: Environment-specific config properly handled
- [ ] **Database Changes**: Schema changes properly versioned and migrated
- [ ] **API Changes**: Backward compatibility maintained or properly versioned
- [ ] **Documentation Updates**: README, API docs, and specs updated

### Deployment Readiness
- [ ] **Build Success**: All builds pass in CI/CD pipeline
- [ ] **Test Passage**: All automated tests pass
- [ ] **Lint Clean**: Code passes all linting and formatting checks
- [ ] **Security Scan**: No new security vulnerabilities introduced
- [ ] **Performance**: No performance regressions detected

## Architecture Review Checklist

### Design Principles Review
- [ ] **Single Responsibility**: Each component has one clear purpose
- [ ] **Open/Closed**: Open for extension, closed for modification
- [ ] **Dependency Inversion**: Depend on abstractions, not concretions
- [ ] **Interface Segregation**: Clients don't depend on unused interfaces
- [ ] **DRY Compliance**: No code duplication without justification

### Spec Kit Architectural Review
- [ ] **Library-First**: All features implemented as libraries
- [ ] **CLI Interfaces**: Every library exposes CLI functionality
- [ ] **Test Structure**: Contract → Integration → Unit test organization
- [ ] **Observability**: Comprehensive logging and monitoring
- [ ] **Simplicity**: Minimal viable architecture without over-engineering

### Scalability Review
- [ ] **Performance**: System meets defined performance benchmarks
- [ ] **Capacity**: Can handle expected load and growth
- [ ] **Reliability**: Proper error handling and graceful degradation
- [ ] **Maintainability**: Code is readable, testable, and modifiable
- [ ] **Monitoring**: Adequate observability for operational needs

### Integration Review
- [ ] **External Dependencies**: All integrations documented and tested
- [ ] **Data Flow**: Information flows logically through system
- [ ] **Error Propagation**: Errors handled appropriately at each layer
- [ ] **Configuration Management**: Environment-specific settings isolated
- [ ] **Security Boundaries**: Proper isolation and access controls

## Review Process Guidelines

### Before Starting Review
1. **Understand Context**: Read related specifications and plans
2. **Check Prerequisites**: Ensure all quality gates have been run
3. **Set Expectations**: Allocate appropriate time for thorough review
4. **Prepare Environment**: Have access to all necessary tools and documentation

### During Review
1. **Use Checklists**: Work through relevant checklists systematically
2. **Take Notes**: Document findings and questions as you review
3. **Test Locally**: Run code locally if possible to verify functionality
4. **Think Like User**: Consider user experience and edge cases

### After Review
1. **Provide Clear Feedback**: Use specific examples and suggestions
2. **Categorize Issues**: Mark issues as critical, important, or suggestions
3. **Offer Solutions**: Suggest specific improvements where possible
4. **Update Checklists**: Add items discovered during review for future use

Remember: Reviews are opportunities for learning and improvement, not just quality gates. Focus on helping the team grow while maintaining high standards.