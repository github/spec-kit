# Technical Debt Patterns

## Design Debt Patterns

### 1. God Object / God Class
**Symptoms:**
- Class with 500+ lines
- Too many responsibilities
- Everyone depends on it
- Frequent merge conflicts

**Impact:** High - blocks parallel development, testing nightmare

**Remediation:**
1. Identify distinct responsibilities
2. Extract classes for each responsibility
3. Use composition over inheritance
4. Apply Single Responsibility Principle

### 2. Spaghetti Architecture
**Symptoms:**
- Unclear module boundaries
- Circular dependencies
- Everything imports everything
- No clear data flow

**Impact:** High - changes cascade unpredictably

**Remediation:**
1. Map current dependencies
2. Define clear layers/boundaries
3. Introduce interfaces at boundaries
4. Refactor one module at a time

### 3. Anemic Domain Model
**Symptoms:**
- Models are just data containers
- All logic in services/controllers
- Domain objects have no behavior
- Procedural code masquerading as OOP

**Impact:** Medium - violates encapsulation, scattered logic

**Remediation:**
1. Identify behaviors that belong to entities
2. Move logic into domain objects
3. Use domain events for cross-cutting concerns

### 4. Big Ball of Mud
**Symptoms:**
- No discernible architecture
- Haphazard structure
- Changes require system-wide understanding
- No one wants to touch it

**Impact:** Critical - extreme maintenance cost

**Remediation:**
1. Document current state (as-is)
2. Define target architecture
3. Establish boundaries with Strangler Fig pattern
4. Migrate piece by piece

## Code Debt Patterns

### 5. Copy-Paste Programming
**Symptoms:**
- Similar code blocks across files
- Bug fixes needed in multiple places
- Slight variations of same logic
- Inconsistent implementations

**Impact:** High - bugs multiply, inconsistent behavior

**Remediation:**
1. Identify duplicated patterns
2. Extract to shared utilities/services
3. Parameterize differences
4. Use generics/templates where appropriate

### 6. Primitive Obsession
**Symptoms:**
- Using strings for everything (IDs, enums, etc.)
- Multiple primitives passed together
- Validation scattered everywhere
- Meaningful concepts hidden

**Impact:** Medium - type errors, validation bugs

**Remediation:**
1. Create value objects for concepts
2. Encapsulate validation in constructors
3. Use type aliases at minimum
4. Replace with enums where appropriate

### 7. Feature Envy
**Symptoms:**
- Methods using other objects' data extensively
- Logic that belongs elsewhere
- Breaking encapsulation frequently
- Getters for everything

**Impact:** Medium - poor cohesion, fragile code

**Remediation:**
1. Move logic to the data owner
2. Pass only what's needed
3. Consider Tell, Don't Ask principle

### 8. Long Parameter Lists
**Symptoms:**
- Functions with 5+ parameters
- Boolean flags changing behavior
- Hard to remember parameter order
- Frequent null parameters

**Impact:** Low-Medium - hard to use, error-prone

**Remediation:**
1. Introduce Parameter Object
2. Use Builder pattern for construction
3. Split function by responsibility
4. Use named parameters/options objects

## Test Debt Patterns

### 9. Missing Tests
**Symptoms:**
- Low code coverage (< 60%)
- Critical paths untested
- Fear of refactoring
- "Works on my machine"

**Impact:** High - risk, slow development

**Remediation:**
1. Prioritize critical path tests
2. Add tests before any changes
3. Use coverage as a guide, not a goal
4. Focus on behavior, not implementation

### 10. Flaky Tests
**Symptoms:**
- Tests pass/fail randomly
- CI requires multiple runs
- "Just run it again"
- Time-dependent tests

**Impact:** Medium - eroded trust in tests

**Remediation:**
1. Identify flaky tests
2. Fix or quarantine immediately
3. Remove time dependencies
4. Use deterministic test data

### 11. Slow Tests
**Symptoms:**
- Full suite takes 30+ minutes
- Developers skip tests
- CI is a bottleneck
- Tests hit real services

**Impact:** Medium - slow feedback loop

**Remediation:**
1. Profile test suite
2. Mock external dependencies
3. Parallelize test execution
4. Split into fast/slow suites

## Infrastructure Debt Patterns

### 12. Manual Deployments
**Symptoms:**
- Deployment runbooks in wiki
- "Only John knows how to deploy"
- Different steps for each environment
- Frequent deployment failures

**Impact:** High - slow releases, human error

**Remediation:**
1. Document current process
2. Automate one step at a time
3. Use infrastructure as code
4. Implement CI/CD pipeline

### 13. Environment Drift
**Symptoms:**
- "Works in dev, fails in prod"
- Manual configuration changes
- Undocumented differences
- Debugging environment issues

**Impact:** Medium-High - unpredictable behavior

**Remediation:**
1. Document all environments
2. Use containers for consistency
3. Automate environment provisioning
4. Version control all configuration

### 14. Dependency Hell
**Symptoms:**
- Conflicting version requirements
- Outdated security patches
- "Don't update, it will break"
- Multiple versions of same library

**Impact:** High - security risk, upgrade pain

**Remediation:**
1. Audit all dependencies
2. Update incrementally
3. Use lock files
4. Automate vulnerability scanning
