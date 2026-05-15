---
description: "Detect Git remote URL for GitHub integration"
---

# Detect Git Remote URL

Detect the Git remote URL for integration with GitHub services (e.g., issue creation).

## Prerequisites

- Check if Git is available by running `git rev-parse --is-inside-work-tree 2>/dev/null`
- If Git is not available, output a warning and return empty:
  ```
  [specify] Warning: Git repository not detected; cannot determine remote URL
  ```

## Execution

Run the following command to get the remote URL:

```bash
git config --get remote.origin.url
```

## Output

Parse the remote URL and determine:

1. **Repository owner**: Extract from the URL (e.g., `github` from `https://github.com/github/spec-kit.git`)
2. **Repository name**: Extract from the URL (e.g., `spec-kit` from `https://github.com/github/spec-kit.git`)
3. **Is GitHub**: Whether the remote points to a GitHub repository

Supported URL formats:
- HTTPS: `https://github.com/<owner>/<repo>.git`
- SSH: `git@github.com:<owner>/<repo>.git`

> [!CAUTION]
> ONLY report a GitHub repository if the remote URL actually points to github.com.
> Do NOT assume the remote is GitHub if the URL format doesn't match.

## Graceful Degradation

If Git is not installed, the directory is not a Git repository, or no remote is configured:
- Return an empty result
- Do NOT error — other workflows should continue without Git remote information
