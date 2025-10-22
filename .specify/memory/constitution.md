<!--
Sync Impact Report:
- Version change: [new constitution] → 1.0.0
- Added sections: All core principles and governance structure established
- Modified principles: None (initial creation)
- Templates requiring updates: ✅ All templates reviewed and compatible
- Follow-up TODOs: None - all placeholders filled
-->

# Spec Kit 4ApplEns Constitution

## Core Principles

### I. Code Simplicity and Clarity (NON-NEGOTIABLE)

Prioritize code that is simple, easy-to-understand, debuggable, and readable above all other considerations. Complex solutions MUST be justified against simpler alternatives. Every line of code should be immediately comprehensible to team members with basic domain knowledge.

**Rationale**: Simple code reduces maintenance burden, enables faster debugging, facilitates knowledge transfer, and minimizes the likelihood of bugs. Complex code creates technical debt and reduces team velocity over time.

### II. Root Cause Solutions

Fix the root cause rather than applying band-aid solutions. When issues arise, teams MUST investigate the underlying cause and address it directly rather than implementing workarounds or patches.

**Rationale**: Band-aid solutions accumulate technical debt, often create new problems, and prevent genuine resolution of systemic issues. Root cause fixes eliminate entire classes of problems rather than treating symptoms.

### III. Explicit Failure Over Silent Defaults

Avoid fallbacks and defaults - prefer explicit failures when input assumptions are not met. Systems MUST fail fast and clearly when provided with invalid or unexpected inputs rather than attempting to continue with assumed values.

**Rationale**: Silent failures and hidden defaults make debugging extremely difficult and can lead to data corruption or incorrect system behavior. Explicit failures provide immediate feedback and force proper error handling.

### IV. Early and Fatal Error Handling

Raise errors early, clearly, and fatally when assumptions are violated. Prefer NOT to wrap operations in try/except blocks so that tracebacks remain obvious and complete for debugging purposes.

**Rationale**: Early error detection prevents cascading failures and makes debugging significantly easier. Complete tracebacks provide essential context for identifying and fixing issues.

### V. Iterative Development Approach

Do not attempt to write a complete, final version immediately. Get a simple version working end-to-end first, then gradually layer in complexity through iterative stages. Each iteration MUST be a working, deployable version.

**Rationale**: End-to-end working systems provide immediate value and feedback. Iterative approaches reduce risk, enable early user feedback, and prevent over-engineering based on assumptions.

### VI. Minimal and Focused Changes

Keep changes minimal and tightly focused on the specific task at hand. Avoid scope creep, unnecessary refactoring, or "while we're here" modifications that are not directly related to the current objective.

**Rationale**: Focused changes are easier to review, test, and debug. They reduce the risk of introducing unrelated bugs and make it easier to identify the source of any issues that arise.

### VII. Engineering Excellence Through Simplicity

Follow software engineering best practices while maintaining simplicity. Reuse code where it makes sense, extract core functionality into utility functions, break down complex functions, write testable code preferring functional style, and avoid object-oriented patterns unless they provide clear benefits.

**Rationale**: Good engineering practices improve code quality and maintainability, but they must not become ends in themselves. The goal is always to create simple, working solutions that solve real problems.

## Development Standards

### Code Organization

- Extract reusable functionality into well-named utility functions
- Break down long or complex functions into smaller, single-purpose functions
- Organize code in a logical directory structure that reflects the application architecture
- Keep related functionality grouped together while maintaining clear separation of concerns

### Testing Philosophy

- Write code that is inherently easy to test through good design
- Prefer functional programming approaches that enable straightforward unit testing
- Focus testing efforts on critical business logic and integration points
- Avoid testing implementation details; test behavior and outcomes

### Documentation Requirements

- Keep documentation up-to-date as development progresses, not as an afterthought
- Document the "why" behind decisions, not just the "what" or "how"
- Maintain README files that enable new team members to understand and contribute quickly
- Document any deviations from these principles with clear justification

## Technology Constraints

### Object-Oriented Usage

Object-oriented programming patterns should be avoided unless they provide a clear, demonstrable benefit for the specific use case. Default to functional approaches and simple data structures.

### Conciseness Over Cleverness

Prioritize concise, straightforward solutions over clever or sophisticated implementations. If a solution requires extensive explanation, consider whether a simpler approach would be more appropriate.

### Over-Engineering Prevention

Actively resist the urge to over-engineer solutions. Implement what is needed for the current requirements, not what might be needed in the future. Follow YAGNI (You Aren't Gonna Need It) principles consistently.

## Governance

### Constitutional Authority

This constitution supersedes all other development practices and guidelines. When conflicts arise between this constitution and other standards, these principles take precedence.

### Amendment Process

- Constitutional amendments require documentation of the proposed change and its rationale
- Amendments must be approved by project maintainers
- All amendments must include a migration plan for existing code if applicable
- Version numbers must follow semantic versioning: MAJOR.MINOR.PATCH format

### Compliance and Review

- All code reviews MUST verify compliance with these constitutional principles
- Any complexity or deviation from these principles MUST be explicitly justified in code comments or commit messages
- Teams should regularly review existing code against these principles during refactoring efforts

### Version Control

- Use feature branches for all changes
- Commit messages should reference relevant constitutional principles when applicable
- Pull requests must demonstrate adherence to constitutional principles

**Version**: 1.0.0 | **Ratified**: 2025-10-21 | **Last Amended**: 2025-10-21
