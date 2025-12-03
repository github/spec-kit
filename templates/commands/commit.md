---
description: Generate and execute standardized git commits following Conventional Commits format with agent signature.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Configuration

The following configuration can be modified to customize commit behavior:

### Commit Types

Allowed commit types (modify this list to add/remove types):

| Type | Description | Emoji | Use When |
|------|-------------|-------|----------|
| feat | New feature | ✨ | Adding new functionality |
| fix | Bug fix | 🐛 | Fixing a bug |
| docs | Documentation | 📝 | Documentation only changes |
| style | Code style | 💄 | Formatting, no code change |
| refactor | Refactoring | ♻️ | Code change without feature/fix |
| test | Tests | ✅ | Adding or updating tests |
| chore | Chores | 🔧 | Build process, dependencies |
| perf | Performance | ⚡ | Performance improvements |
| ci | CI/CD | 👷 | CI configuration changes |
| build | Build | 📦 | Build system changes |

### Message Format

- **subject_max_length**: 72
- **body_max_line_length**: 100
- **require_scope**: false
- **require_body**: false
- **use_emoji**: false

### Confirmation Mode

- **default_mode**: auto
  - `auto`: Confirm for complex changes (5+ files), skip for simple changes
  - `confirm`: Always wait for confirmation
  - `skip`: Never wait for confirmation

### Language

- **default**: en
  - `en`: English commit messages
  - `zh`: Chinese commit messages

### Sensitive File Patterns

Files matching these patterns will trigger a warning:

```text
.env
.env.*
*.key
*.pem
*.p12
*secret*
*credential*
*password*
*token*
serviceAccountKey.json
id_rsa
id_dsa
```

---

## Outline

### Step 1: Parse Command Arguments

Parse `$ARGUMENTS` to extract options:

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--type` | `-t` | string | Commit type (feat, fix, docs, etc.) |
| `--scope` | `-s` | string | Commit scope (e.g., auth, api) |
| `--message` | `-m` | string | Custom commit description |
| `--confirm` | - | flag | Force confirmation mode |
| `--no-confirm` | - | flag | Skip confirmation |
| `--dry-run` | - | flag | Preview only, don't commit |
| `--amend` | - | flag | Amend the last commit |

Any remaining text after options is treated as the commit description.

**Examples**:
- `/commit` - Auto-analyze and commit
- `/commit --type feat` - Commit as feature
- `/commit --type fix --scope auth` - Fix in auth scope
- `/commit --dry-run` - Preview without committing
- `/commit Add user login feature` - Use text as description

### Step 2: Check Git Status

1. **Verify Git repository**:
   ```bash
   git rev-parse --git-dir 2>/dev/null
   ```
   If this fails, display error: "❌ **Error**: Not a git repository. Please run this command from within a git repository."

2. **Check for changes**:
   ```bash
   git status --porcelain
   ```

3. **Handle different states**:
   - If no changes (empty output): Display "❌ **No changes to commit**. Stage changes with `git add` first or make some modifications."
   - If only untracked files: Ask if user wants to include them
   - If staged changes exist: Proceed with staged changes only
   - If unstaged changes exist: Stage all changes with `git add -A`

4. **Check for special Git states**:
   ```bash
   git status
   ```
   - If in rebase/merge state: Display warning and suggest resolving first

### Step 3: Detect Sensitive Files

1. **Get list of files to be committed**:
   ```bash
   git diff --cached --name-only
   ```

2. **Check each file against sensitive patterns** defined in Configuration section

3. **If sensitive files detected**:
   ```markdown
   ## ⚠️ Warning: Sensitive Files Detected

   The following files match sensitive patterns:
   - `.env.local` (matches: `.env.*`)
   - `secrets/api.key` (matches: `*.key`)

   These files may contain secrets or credentials. Do you want to proceed?
   ```

   Wait for user confirmation before proceeding. If user declines, display "提交已取消" and stop.

### Step 4: Analyze Changes

1. **Get detailed diff**:
   ```bash
   git diff --cached --stat
   git diff --cached
   ```

2. **Identify change characteristics**:
   - File types modified (source code, tests, docs, config)
   - Nature of changes (additions, modifications, deletions)
   - Affected directories/modules

3. **Auto-infer commit type** (if not specified via `--type`):

   | Change Pattern | Inferred Type |
   |---------------|---------------|
   | New files in `test/` or `*.test.*`, `*.spec.*` | test |
   | Changes only in `docs/` or `*.md` files | docs |
   | Only `package.json`, `pom.xml`, `build.gradle`, etc. | chore |
   | Changes in `.github/workflows/`, `.gitlab-ci.yml` | ci |
   | New source files in `src/` | feat |
   | Modified files with "fix", "bug", "error" in diff | fix |
   | Code changes without new features | refactor |
   | Default | feat |

4. **Auto-infer scope** (if not specified via `--scope`):
   - Extract common parent directory of changed files
   - Use module name if changes are in a single module

### Step 5: Generate Commit Message

Based on the Configuration section settings:

1. **Build subject line**:
   ```
   <type>[(<scope>)]: <description>
   ```

   - If `use_emoji` is true, prepend emoji: `✨ feat(auth): Add login`
   - Ensure subject length ≤ `subject_max_length` (72 chars)
   - Do not end with period
   - Use imperative mood (Add, Fix, Update, not Added, Fixed, Updated)

2. **Build body** (for complex changes):
   - Summarize what changed and why
   - Use bullet points for multiple changes
   - Wrap lines at `body_max_line_length` (100 chars)

3. **Add footer with agent signature**:
   ```
   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

4. **Language handling**:
   - If `language.default` is `zh`: Generate description in Chinese
   - If `language.default` is `en`: Generate description in English

### Step 6: Validate Message

1. **Check subject length**:
   - If > 72 characters: Truncate or warn user

2. **Check type validity**:
   - If type not in allowed list: Show error with available types

3. **Check required fields**:
   - If `require_scope` is true and no scope: Prompt for scope
   - If `require_body` is true and no body: Generate body

### Step 7: Display Preview

Show the commit preview:

```markdown
## Commit Preview

**Type**: feat
**Scope**: auth
**Subject**: Add user login functionality

### Files to be Committed (3)
- `src/auth/login.ts` (added)
- `src/auth/token.ts` (added)
- `src/routes/auth.ts` (modified)

### Commit Message
```
feat(auth): Add user login functionality

Implement JWT-based user authentication:
- Add login endpoint
- Add token validation middleware
- Add refresh token support

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```
```

### Step 8: Handle Confirmation

Based on `confirmation.default_mode` and command arguments:

| Config Mode | `--confirm` | `--no-confirm` | Behavior |
|-------------|-------------|----------------|----------|
| auto | - | - | Confirm if 5+ files, else skip |
| auto | yes | - | Wait for confirmation |
| auto | - | yes | Skip confirmation |
| confirm | - | - | Wait for confirmation |
| confirm | - | yes | Skip confirmation |
| skip | - | - | Skip confirmation |
| skip | yes | - | Wait for confirmation |

If `--dry-run` is specified: Display preview and stop without committing.

If user cancels confirmation: Display "提交已取消" and stop.

### Step 9: Execute Commit

1. **Stage changes** (if not already staged):
   ```bash
   git add -A
   ```

2. **Create commit**:
   ```bash
   git commit -m "<message>"
   ```

   Use HEREDOC for multi-line messages:
   ```bash
   git commit -m "$(cat <<'EOF'
   feat(auth): Add user login functionality

   Implement JWT-based authentication

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

3. **Handle --amend**:
   - If `--amend` specified:
     - Check if last commit is pushed: `git status` shows "Your branch is ahead"
     - If pushed to remote: Display warning about force push requirement
     - Execute: `git commit --amend -m "<message>"`

### Step 10: Display Result

On success:
```markdown
## ✅ Commit Successful

**Commit**: `a1b2c3d`
**Type**: feat
**Scope**: auth
**Subject**: Add user login functionality

### Summary
- 3 files changed
- 150 insertions(+)
- 12 deletions(-)
```

On failure:
```markdown
## ❌ Commit Failed

**Error**: <git error message>

### Troubleshooting
- Check `git status` for conflicts
- Ensure you have write permissions
- Try running `git add` manually
```

---

## Error Handling

| Error | Message | Suggestion |
|-------|---------|------------|
| Not a git repo | Not a git repository | Run from within a git repository |
| No changes | No changes to commit | Stage changes with `git add` first |
| Invalid type | Unknown commit type: {type} | Use one of: feat, fix, docs, style, refactor, test, chore |
| Message too long | Subject exceeds 72 characters | Use a shorter description |
| Git command failed | Git error: {message} | Check git status and resolve issues |
| Amend pushed commit | Last commit already pushed | Use `git push --force` after amend (caution!) |

---

## Examples

### Basic Usage
```
/commit
```
Auto-analyzes changes, infers type, generates message, and commits.

### Specify Type
```
/commit --type feat
```
Commits as a new feature.

### Specify Type and Scope
```
/commit --type fix --scope auth
```
Commits as a bug fix in the auth module.

### With Description
```
/commit --type feat Add user login functionality
```
Uses the provided description.

### Preview Mode
```
/commit --dry-run
```
Shows what would be committed without actually committing.

### Skip Confirmation
```
/commit --no-confirm
```
Commits immediately without waiting for confirmation.

### Amend Last Commit
```
/commit --amend
```
Modifies the previous commit with current changes.
