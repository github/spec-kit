---
description: "Define and use a custom TOML command with {{args}} and !{...}"
---

Objective: Practice defining reusable commands that safely accept arguments.

Setup (conceptual)
- Imagine a TOML at `.qwen/commands/search.toml`:

```toml
description = "Search project for a pattern and summarize findings"

prompt = """
Please summarize the findings for the pattern `{{args}}`.

Search Results:
!{grep -R --line-number --no-color {{args}} .}
"""
```

Steps
1. In interactive session, run: `/search Qwen Code`
2. Try quoted args: `/search "def main\("`

Acceptance
- Model returns a short summary and relevant matches.
- No shell injection occurs (arguments are shell-escaped by the CLI).



