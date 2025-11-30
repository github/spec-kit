# Security Policy

## Reporting Security Issues

If you believe you have found a security vulnerability in Spectrena, please report it through coordinated disclosure.

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

Instead, please use GitHub's private vulnerability reporting feature:
1. Go to the [Security tab](https://github.com/rghsoftware/spectrena/security) of the repository
2. Click "Report a vulnerability"
3. Fill out the form with details

Alternatively, you can email: security@rghsoftware.com

## What to Include

Please include as much of the following information as possible:

- The type of issue (e.g., command injection, path traversal, information disclosure)
- Full paths of source file(s) related to the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Scope

Security issues in the following areas are in scope:

- **CLI commands** (`spectrena`, `sw`)
- **MCP server** (`spectrena-mcp`)
- **Lineage database** handling
- **File operations** (spec creation, template handling)
- **Git operations** (worktree management, branch creation)
- **Configuration parsing** (YAML, Mermaid)

## Out of Scope

- Issues in dependencies (report to the upstream project)
- Issues requiring physical access to the machine
- Social engineering attacks
- Denial of service attacks

## Response Timeline

We aim to:
- Acknowledge receipt within 48 hours
- Provide an initial assessment within 7 days
- Release a fix within 30 days for critical issues

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (unless they prefer to remain anonymous).
