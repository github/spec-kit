---
description: Analyze changes and create intelligent git commits following Spec Kit principles and conventional commit standards.
---

# Smart Git Commit

**Additional Instructions and Jira issue key (project-123)**: $ARGUMENTS

## Smart Commit Process

### 1. Analyze Current State

First, let's understand what changes need to be committed:

```bash
# Check current git status
git status

# Look at staged changes
git diff --staged

# If nothing staged, examine working directory changes
git diff
git status -s
```

**Analysis Questions**:
- What files have been modified?
- Are there new files that should be included?
- Do the changes represent a logical unit of work?
- Are there changes that should be in separate commits?

### 2. Spec Kit Change Classification

**Classify changes according to Spec Kit methodology**:

#### Specification Changes (`spec:`)
- Updates to feature specifications
- Changes to functional requirements
- User story modifications
- Acceptance criteria updates

#### Planning Changes (`plan:`)
- Implementation plan updates
- Technical decision documentation
- Architecture modifications
- Research findings

#### Library Implementation (`feat:` or `fix:`)
- New library functionality
- Library interface changes
- Core business logic implementation
- Bug fixes in libraries

#### CLI Interface (`feat:` or `fix:`)
- Command-line interface additions
- CLI argument handling changes
- Output format modifications
- Help text updates

#### Testing (`test:`)
- New test cases (contract, integration, unit)
- Test framework changes
- Test data updates
- Testing infrastructure

#### Constitutional (`refactor:` or `chore:`)
- Architectural realignments
- Code organization improvements
- Dependency management
- Build system changes

### 3. Conventional Commit Format

**Standard Format**:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Spec Kit Types**:
- `feat`: New feature or enhancement (user-visible)
- `fix`: Bug fix (user-visible)
- `spec`: Specification changes
- `plan`: Implementation plan changes
- `test`: Adding or modifying tests
- `docs`: Documentation updates
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring without behavior change
- `perf`: Performance improvements
- `chore`: Maintenance tasks, dependencies, build changes

### 4. Smart Commit Generation
- NEVER include "meta" information about spec-kit in commit messages (e.g.,  "LOC: 380 (within 500 budget)"                                            │ │
  or "Part of parent feature: specs/wtmt-1027.contextual-embeddings-replace"
- Based on the change analysis, I'll suggest appropriate commits:

**For Test-First Development** (following Spec Kit constitution):
```bash
# Example sequence for new feature
git add tests/contract/user_auth_test.py
git commit -m "test(auth): add user authentication contract tests

Contract tests for user registration, login, and session management
following specification requirements from spec.md section 3.2.

Tests currently fail as expected (RED phase)."

git add tests/integration/auth_flow_test.py
git commit -m "test(auth): add integration tests for auth flow

End-to-end tests covering complete user authentication journey
from registration through logout, including error scenarios."

git add src/auth/user_service.py src/auth/auth_api.py
git commit -m "feat(auth): implement user authentication service

- User registration with email validation
- Login with JWT token generation
- Session management and logout
- Input validation and error handling

Implements requirements FR-001 through FR-005 from specification.
Makes contract and integration tests pass (GREEN phase)."
```

**For Bug Fixes**:
```bash
# Example bug fix commit
git add tests/unit/password_validation_test.py
git commit -m "test(auth): add test for password validation bug

Reproduces issue where passwords with special characters
are incorrectly rejected. Test fails as expected."

git add src/auth/password_validator.py
git commit -m "fix(auth): handle special characters in password validation

- Update regex pattern to allow all valid special characters
- Add proper escaping for regex metacharacters
- Fix edge case with Unicode characters

Fixes issue reported in #123. Makes validation test pass."
```

### 5. Change Staging Strategy

**Intelligent Staging**:
- If no files are staged, I'll analyze what should be included
- Group related changes into logical commits
- Suggest splitting if changes are too diverse
- Identify files that should always be committed together

**Staging Recommendations**:
```bash
# Stage related files together
git add src/models/user.py src/models/session.py  # Related models
git add tests/unit/user_test.py tests/unit/session_test.py  # Corresponding tests

# Stage documentation with implementation
git add src/auth/ docs/api/authentication.md  # Code + docs

# Stage configuration with implementation
git add src/config/ deploy/config/  # Implementation + deployment config
```

### 6. Commit Quality Checks

**Pre-commit Validation**:
- [ ] Changes align with Spec Kit constitution
- [ ] Test-first principle followed (tests before implementation)
- [ ] Commit message follows conventional commit format
- [ ] Related files committed together
- [ ] No secrets or sensitive data included
- [ ] Code passes linting and type checking

**Constitutional Compliance Check**:
```bash
# Verify test-first principle
git log --oneline -5 | grep -E "(test|spec).*feat|fix.*test"

# Check for proper library structure
ls src/*/cli/ | wc -l  # Should have CLI interfaces

# Validate no direct app code (library-first principle)
find src/ -name "main.py" -o -name "app.py" | wc -l  # Should be minimal
```

### 7. Interactive Commit Process

**Decision Points**:
1. **Review suggested commit message**:
   - Does it accurately describe the changes?
   - Is the type classification correct?
   - Should the scope be more specific?

2. **Consider commit body**:
   - Do complex changes need explanation?
   - Should implementation decisions be documented?
   - Are there breaking changes that need callouts?

3. **Multiple commits**:
   - Should changes be split into smaller logical commits?
   - Are there preparatory changes that should be separate?
   - Should refactoring be committed before new features?

### 8. Post-Commit Actions

**After Creating Commits**:
```bash
# Show the created commit for review
git log --oneline -1
git show --stat

# Check if any files were missed
git status

# Verify commit message format
git log --pretty=format:"%h %s" -1 | grep -E "^[0-9a-f]{7} (feat|fix|docs|style|refactor|perf|test|chore|spec|plan)(\(.+\))?: .+"
```

**Next Steps Options**:
- **Continue working**: Stay on current branch for more changes
- **Push changes**: `git push origin [branch-name]`
- **Create pull request**: `git push -u origin [branch-name]` then open PR
- **Switch context**: Move to different feature or task

### 9. Branch and PR Strategy

**Branch Naming** (following Spec Kit conventions):
```bash
# Feature branches
git checkout -b "username/proj-123.user-authentication"  # Matches JIRA and spec
git checkout -b "username/PROJ-456.user-dashboard"       # JIRA integration

# Bug fix branches
git checkout -b "fix/password-validation-issue"
git checkout -b "bugfix/session-timeout-error"

# Specification branches
git checkout -b "spec/002-payment-system"
```

**Pull Request Preparation**:
- Ensure all commits follow conventional format
- Run full validation suite: `/validate implementation`
- Update documentation if needed
- Prepare PR description referencing specification

### 10. Commit Message Templates

**Feature Implementation**:
```
feat(scope): brief description of user-visible change

Detailed explanation of what was implemented and why.
Reference to specification sections if applicable.

- List key functionality added
- Note any API changes or new interfaces
- Mention testing approach used

Implements: [spec reference]
Closes: #[issue number]
```

**Bug Fix**:
```
fix(scope): brief description of what was fixed

Explanation of the bug and how it was resolved.

- Root cause analysis summary
- Solution approach taken
- Testing added to prevent regression

Fixes: #[issue number]
```

**Testing**:
```
test(scope): brief description of tests added

Explanation of what testing coverage was added and why.

- Test scenarios covered
- Testing methodology used
- Integration with existing test suite

Part of: [feature/fix reference]
```

## Example Interactive Session

```bash
$ /smart-commit "implement user authentication"

🔍 Analyzing changes...

📁 Files changed:
  M  src/auth/user_service.py
  M  src/auth/auth_api.py
  A  tests/contract/user_auth_test.py
  A  tests/integration/auth_flow_test.py
  M  docs/api/authentication.md

⚖️  Constitutional check: ✅ PASS
  - Test files committed first ✅
  - Library structure maintained ✅
  - CLI interface present ✅

💡 Suggested commits:

1️⃣  feat(auth): implement user authentication service
   Type: feat | Scope: auth
   Files: src/auth/*, tests/*, docs/api/authentication.md

   Message preview:
   feat(auth): implement user authentication service

   - User registration with email validation
   - JWT token-based session management
   - Password hashing with bcrypt
   - Rate limiting for login attempts

   Implements FR-001 to FR-005 from specification.
   All contract and integration tests pass.

✅ Accept this commit message? [Y/n/e/s]
   (Y=yes, n=no, e=edit, s=split into multiple commits)

> Y

📝 Creating commit...
[username/proj-123.user-auth abc1234] feat(auth): implement user authentication service
- where proj-123 is a Jira issue key. If not provided as ARGUMENTS to this command, prompt the user. Do not proceed without one.
🚀 Next actions:
  1. Push to remote: git push -u origin username/proj-123.user-auth
  2. Create pull request
  3. Continue development
  4. Run validation: /validate implementation

What would you like to do next?
```

Remember: The goal is to create meaningful, traceable commits that tell the story of your development process while adhering to Spec Kit principles.