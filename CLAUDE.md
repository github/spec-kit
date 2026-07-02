# spec-kit Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-07-02

## Active Technologies
- Bash (POSIX-compatible), PowerShell (5.1+/7+) + git (for branch operations) (002-allow-existing-branch)
- Python 3.11+ (matching existing spec-kit requirements) + No new dependencies. Uses existing Python stdlib (re module for template processing). The capability processor is purpose-built, not based on Jinja2. (003-extension-capability-system)
- N/A (file-based, processes command templates at install time) (003-extension-capability-system)

- Bash (POSIX-compatible), PowerShell (5.1+/7+) + git (optional, for branch scanning), jq (optional, for JSON output) (001-dry-run-flag)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for Bash (POSIX-compatible), PowerShell (5.1+/7+)

## Code Style

Bash (POSIX-compatible), PowerShell (5.1+/7+): Follow standard conventions

## Recent Changes
- 003-extension-capability-system: Added Python 3.11+ (matching existing spec-kit requirements) + No new dependencies. Uses existing Python stdlib (re module for template processing). The capability processor is purpose-built, not based on Jinja2.
- 002-allow-existing-branch: Added Bash (POSIX-compatible), PowerShell (5.1+/7+) + git (for branch operations)

- 001-dry-run-flag: Added Bash (POSIX-compatible), PowerShell (5.1+/7+) + git (optional, for branch scanning), jq (optional, for JSON output)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
