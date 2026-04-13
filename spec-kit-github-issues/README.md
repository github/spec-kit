# GitHub Issues Integration Extension

A Spec Kit extension that generates spec artifacts from GitHub Issues, eliminating duplicate work between issue tracking and Specification-Driven Development (SDD).

## Problem

Developers already document requirements in GitHub Issues (user stories, acceptance criteria, labels, discussions) but then rewrite everything from scratch in `spec.md` when starting Specification-Driven Development. This creates:

- **Duplicate work** - Writing the same information twice
- **Context loss** - Losing valuable discussion and rationale from issues
- **Sync drift** - Issues and specs diverge over time
- **Manual overhead** - Copying and reformatting content manually

## Solution

This extension provides three commands that bridge GitHub Issues and Spec Kit:

1. **`/speckit.github-issues.import`** - Import a GitHub Issue and generate structured `spec.md`
2. **`/speckit.github-issues.sync`** - Keep specs updated when source issues change
3. **`/speckit.github-issues.link`** - Add bidirectional traceability between specs and issues

## Features

- ✅ **Import GitHub Issues** - Convert issues to structured spec.md files
- ✅ **Structured parsing** - Extract problem statements, solutions, acceptance criteria
- ✅ **Include discussions** - Preserve valuable comments and context
- ✅ **Bidirectional links** - Maintain traceability between issues and specs
- ✅ **Automatic sync** - Keep specs updated when issues change
- ✅ **Label integration** - Import issue labels as spec tags
- ✅ **Status tracking** - Monitor issue state (open/closed)

## Installation

### Prerequisites

- Spec Kit installed (`specify` CLI)
- GitHub CLI (`gh`) installed and authenticated
- Git repository initialized

### Install Extension

```bash
# From your spec-kit project directory
specify extension add github-issues --from https://github.com/Fatima367/spec-kit-github-issues/archive/refs/tags/v1.0.0.zip
```

### Verify Installation

```bash
specify extension list
```

You should see:

```
✓ GitHub Issues Integration (v1.0.0)
   Generate spec artifacts from GitHub Issues
   Commands: 3 | Status: Enabled
```

### Authenticate with GitHub

```bash
gh auth login
```

## Usage

### 1. Import a GitHub Issue

Convert a GitHub Issue into a structured spec.md file:

```bash
# In your AI agent (e.g., Claude Code)
/speckit.github-issues.import github/spec-kit#2175

# Or if you're in the same repository
/speckit.github-issues.import #2175
```

**What it does:**
- Fetches issue title, body, labels, and comments
- Parses structured sections (problem, solution, alternatives)
- Generates `spec.md` with requirements and acceptance criteria
- Creates `.issue-link` metadata for tracking
- Preserves discussion context from comments

**Output:**
```
✓ Spec generated at: specs/001-generate-spec-artifacts/spec.md
✓ Linked to issue: https://github.com/github/spec-kit/issues/2175

Next steps:
  1. Review and refine the generated spec
  2. Run /speckit.clarify to fill in any gaps
  3. Run /speckit.plan to create implementation plan
  4. Use /speckit.github-issues.sync to keep spec updated
```

### 2. Link Existing Spec to Issue

Add bidirectional traceability between an existing spec and a GitHub Issue:

```bash
/speckit.github-issues.link github/spec-kit#2175
```

**What it does:**
- Adds issue reference to spec frontmatter
- Creates `.issue-link` metadata file
- Posts a comment on the GitHub Issue linking back to the spec
- Establishes bidirectional traceability

**Output:**
```
✓ Added issue link to spec
✓ Created link metadata
✓ Added traceability comment to issue

Bidirectional traceability established:
  ✓ Spec references issue
  ✓ Issue references spec (via comment)
```

### 3. Sync Spec with Issue Updates

Keep your spec synchronized with changes to the source GitHub Issue:

```bash
# Sync all linked issues
/speckit.github-issues.sync

# Sync specific feature
/speckit.github-issues.sync 001-feature-name

# Sync specific issue
/speckit.github-issues.sync #2175
```

**What it does:**
- Detects changes in linked issues (title, body, labels, comments)
- Shows what will be updated
- Prompts for confirmation
- Updates spec with latest issue data
- Appends new comments to Discussion Notes
- Updates metadata timestamps

**Output:**
```
Found 1 linked issue(s)
Checking github/spec-kit#2175...
  ✓ Updates detected (last synced: 2026-04-10, updated: 2026-04-12)

The following specs have updates available:
  • github/spec-kit#2175 → .specify/specs/001-generate-spec-artifacts/spec.md

Apply updates? (y/n): y

Updating .specify/specs/001-generate-spec-artifacts/spec.md...
  ✓ Updated title
  ✓ Added new comments
  ✓ Sync complete
```

## Configuration

Create `.specify/extensions/github-issues/github-issues-config.yml` to customize behavior:

```yaml
# GitHub repository settings
repository:
  owner: "github"
  name: "spec-kit"

# Import settings
import:
  include_comments: true
  max_comments: 0  # 0 = unlimited
  include_labels: true

# Sync settings
sync:
  auto_detect: true
  prompt_before_sync: true

# Link settings
link:
  add_to_frontmatter: true
  add_to_body: true
  link_format: "**Source Issue:** [{repo}#{number}]({url})"

# Authentication
auth:
  use_gh_cli: true
```

## Workflow Example

Here's a complete workflow using this extension:

```bash
# 1. Initialize spec-kit project
specify init my-project --ai claude

# 2. Install GitHub Issues extension
specify extension add github-issues

# 3. Import an issue
/speckit.github-issues.import github/spec-kit#2175

# 4. Review and refine the generated spec
/speckit.clarify

# 5. Create implementation plan
/speckit.plan

# 6. Generate tasks
/speckit.tasks

# 7. Implement
/speckit.implement

# 8. Later, sync with issue updates
/speckit.github-issues.sync
```

## Commands Reference

### `/speckit.github-issues.import`

**Syntax:** `/speckit.github-issues.import <owner>/<repo>#<number>` or `/speckit.github-issues.import #<number>`

**Description:** Import a GitHub Issue and generate structured spec.md

**Examples:**
```bash
/speckit.github-issues.import github/spec-kit#2175
/speckit.github-issues.import #2175
```

### `/speckit.github-issues.sync`

**Syntax:** `/speckit.github-issues.sync [feature-dir|#number]`

**Description:** Sync spec artifacts with updates from source issues

**Examples:**
```bash
/speckit.github-issues.sync                    # Sync all linked issues
/speckit.github-issues.sync 001-feature-name   # Sync specific feature
/speckit.github-issues.sync #2175              # Sync specific issue
```

### `/speckit.github-issues.link`

**Syntax:** `/speckit.github-issues.link <owner>/<repo>#<number>` or `/speckit.github-issues.link #<number>`

**Description:** Add bidirectional traceability between spec and issue

**Examples:**
```bash
/speckit.github-issues.link github/spec-kit#2175
/speckit.github-issues.link #2175
```

## Troubleshooting

### GitHub CLI not authenticated

**Error:** `Failed to fetch issue. Check repository access and issue number.`

**Solution:**
```bash
gh auth login
```

### No linked issues found

**Error:** `No linked issues found. Use /speckit.github-issues.import first.`

**Solution:** Import an issue first using `/speckit.github-issues.import #<number>`

### Permission denied when commenting

**Warning:** `Could not add comment to issue (may lack permissions)`

**Solution:** Ensure you have write access to the repository. The extension will still create local links.

### Issue not found

**Error:** `Invalid format. Use 'owner/repo#123' or '#123'`

**Solution:** Check the issue number and format. Use full format `owner/repo#123` for external repos.

## Benefits

- **Save time** - No more rewriting issue content into specs
- **Preserve context** - Keep valuable discussions and rationale
- **Stay synchronized** - Specs automatically update with issue changes
- **Maintain traceability** - Bidirectional links between issues and specs
- **Reduce errors** - Automated parsing reduces manual transcription mistakes
- **Better collaboration** - Team discussions in issues flow into specs

## Limitations

- Requires GitHub CLI (`gh`) installed and authenticated
- Only works with GitHub Issues (not other issue trackers)
- Requires write access to add comments to issues
- Sync is manual (not automatic on issue updates)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

**Fatima367**
- GitHub: [@Fatima367](https://github.com/Fatima367)
- Repository: [spec-kit-github-issues](https://github.com/Fatima367/spec-kit-github-issues)

## Acknowledgements

- Built for [Spec Kit](https://github.com/github/spec-kit)
- Inspired by issue [#2175](https://github.com/github/spec-kit/issues/2175)
- Thanks to the Spec Kit community

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## Support

- **Issues:** [GitHub Issues](https://github.com/Fatima367/spec-kit-github-issues/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Fatima367/spec-kit-github-issues/discussions)
- **Spec Kit:** [Main Repository](https://github.com/github/spec-kit)
