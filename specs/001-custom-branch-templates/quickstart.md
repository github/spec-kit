# Quickstart: Customizable Branch Naming Templates

**Feature**: 001-custom-branch-templates

## Key Validation Scenarios

### Scenario 1: Team Setup (US1 - P1)

**Goal**: Configure branch templates for a team repository

```bash
# 1. Initialize settings file
specify init --settings

# 2. Edit .specify/settings.toml
# Change template to include username:
#   template = "{username}/{number}-{short_name}"

# 3. Developer "Jane Smith" creates a feature
git config user.name "Jane Smith"
/speckit.specify Add user authentication

# Expected result:
# Branch created: jane-smith/001-add-user-authentication
# Spec file: specs/jane-smith/001-add-user-authentication/spec.md
```

**Validation**:
- [ ] Branch name follows pattern `{username}/{number}-{short_name}`
- [ ] Username is normalized (lowercase, hyphens)
- [ ] Number is 001 (first feature for this user)

---

### Scenario 2: Backward Compatibility (US2 - P2)

**Goal**: Verify existing behavior when no settings file exists

```bash
# Ensure no settings file
rm -f .specify/settings.toml

# Create a feature
/speckit.specify Build dashboard

# Expected result:
# Branch created: 001-build-dashboard (default pattern)
```

**Validation**:
- [ ] Branch follows original `{number}-{short_name}` pattern
- [ ] No errors about missing settings file
- [ ] Existing workflows continue unchanged

---

### Scenario 3: Username Fallback (US3 - P3)

**Goal**: Verify username resolution falls back to OS username

```bash
# Clear Git username
git config --unset user.name

# Set template with username
echo '[branch]
template = "{username}/{number}-{short_name}"' > .specify/settings.toml

# Create a feature
/speckit.specify Test fallback

# Expected result:
# Branch created: $USER/001-test-fallback
# (where $USER is the OS username)
```

**Validation**:
- [ ] OS username (`$USER` / `$env:USERNAME`) is used when Git user.name is unset
- [ ] No prompts or errors
- [ ] Username is normalized (lowercase, hyphens)

---

### Scenario 4: Per-User Number Scoping

**Goal**: Verify independent number sequences per user prefix

```bash
# Setup: Two branches exist
# - johndoe/001-feature-a
# - janedoe/001-feature-b
# - janedoe/002-feature-c

git config user.name "John Doe"

# Create new feature
/speckit.specify Add new feature

# Expected result:
# Branch created: johndoe/002-add-new-feature
# (002 because johndoe's highest is 001)
```

**Validation**:
- [ ] Number scoped to `johndoe/` prefix only
- [ ] Jane's branches don't affect John's sequence
- [ ] Global sequence not used when prefix exists

---

### Scenario 5: Settings File Generation (US4 - P4)

**Goal**: Generate settings file with examples

```bash
# Generate settings
specify init --settings

# Verify file created
cat .specify/settings.toml
```

**Expected Output**:
```toml
# Spec Kit Settings
# Documentation: https://github.github.io/spec-kit/

[branch]
# Template for generating feature branch names.
# ... (documented examples)
template = "{number}-{short_name}"
```

**Validation**:
- [ ] File created at `.specify/settings.toml`
- [ ] Contains documented examples as comments
- [ ] Default template is `{number}-{short_name}`

---

### Scenario 6: Overwrite Protection

**Goal**: Prevent accidental settings file overwrite

```bash
# Settings file already exists
specify init --settings

# Expected: Prompt or error
# "Settings file already exists. Use --force to overwrite."

# Force overwrite
specify init --settings --force

# Expected: File overwritten
```

**Validation**:
- [ ] Without `--force`: prompts or exits with message
- [ ] With `--force`: overwrites without prompt

---

## Edge Case Validations

### Invalid Template

```bash
echo '[branch]
template = "no-number-here"' > .specify/settings.toml

/speckit.specify Test invalid

# Expected: Error message
# "Error: Template must contain {number} placeholder"
```

### Invalid Branch Name Characters

```bash
echo '[branch]
template = "feature..test/{number}-{short_name}"' > .specify/settings.toml

/speckit.specify Test invalid chars

# Expected: Error message
# "Error: Template contains invalid Git branch characters: .."
```

### Username with Special Characters

```bash
git config user.name "José O'Brien-Smith"

# Expected normalized: jose-obrien-smith
```

---

## Quick Reference

| Template | Example Output | Use Case |
|----------|---------------|----------|
| `{number}-{short_name}` | `001-add-login` | Solo developer (default) |
| `{username}/{number}-{short_name}` | `johndoe/001-add-login` | Team |
| `feature/{username}/{number}-{short_name}` | `feature/johndoe/001-add-login` | Team with prefix |
| `users/{email_prefix}/{number}-{short_name}` | `users/jsmith/001-add-login` | Enterprise (email-based) |
