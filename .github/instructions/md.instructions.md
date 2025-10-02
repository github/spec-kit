---
applyTo: '**/*.md'
description: Markdown style guidelines for consistency across documentation.
---

# Markdown Style Guidelines

This document defines the markdown style guidelines for all markdown files in this repository. These rules follow common markdown linter best practices and ensure consistency across documentation.

## Headings

- Use ATX-style headings (`#`) instead of Setext-style (underlines)
- Include a space after the hash marks: `# Heading` not `#Heading`
- Use only one top-level heading (`#`) per document
- Do not skip heading levels (e.g., don't go from `#` to `###`)
- Surround headings with blank lines (one before, one after, excluding the first heading in the document unless preceded by frontmatter)
- Do not use trailing punctuation in headings (no periods, colons, etc.)
- Use sentence case for headings unless referring to proper nouns or code identifiers

**Good:**

```markdown
# Main heading

## Subsection

### Details
```

**Bad:**

```markdown
#No space after hash
### Skipped level 2
## Heading with period.
```

## Lists

- Use consistent list markers throughout the document (`-` for unordered, `1.` for ordered)
- Do not add blank lines between list items (unless item contains multiple paragraphs)
- Indent nested lists by 2 spaces for unordered, 3 spaces for ordered
- Use `1.` for all ordered list items (auto-numbering) or number them sequentially
- Surround lists with blank lines (one before, one after)
- Use `-` for unordered lists (not `*` or `+`)

**Good:**

```markdown
Here is a list:

- First item
- Second item
- Third item

Another list:

1. First step
1. Second step
1. Third step
```

**Bad:**

```markdown
No blank line before list:
- Item one

- Blank lines between items
- Not needed

* Wrong marker
+ Mixed markers
```

## Code Blocks

- Always use fenced code blocks (triple backticks) with language identifiers
- Always include a blank line before and after code blocks
- Specify the language for syntax highlighting (`bash`, `python`, `markdown`, `json`, etc.)
- Use `plaintext` or `text` if no specific language applies
- Indent code blocks at the same level as surrounding content

**Good:**

```markdown
Here is an example:

\`\`\`bash
echo "Hello, world!"
\`\`\`

The command prints a message.
```

**Bad:**

```markdown
No language identifier:
\`\`\`
code here
\`\`\`
No blank lines before/after code blocks.
```

## Links

- Use reference-style links for repeated URLs
- Use relative paths for internal links (relative to the current file)
- Always provide link text in square brackets: `[text](url)`
- Do not use bare URLs (wrap them: `<https://example.com>`)
- For internal repository links, use relative paths starting with `./` or `../`
- Use `.md` extension for links to markdown files

**Good:**

```markdown
See the [installation guide](../docs/installation.md) for details.

Check out [GitHub][gh] and [GitLab][gl] for hosting.

[gh]: https://github.com
[gl]: https://gitlab.com
```

**Bad:**

```markdown
Absolute path: [guide](/docs/installation.md)
Missing extension: [guide](../docs/installation)
Bare URL: Visit https://example.com
```

## Tables

- Use tables when content follows a consistent structure (instead of lists)
- Align columns using hyphens for readability
- Include header row separator with at least 3 hyphens per column
- Surround tables with blank lines (one before, one after)
- Use pipes (`|`) to separate columns
- Align content within columns for readability (optional but recommended)

**Good:**

```markdown
Here is a comparison:

| Feature | Supported | Notes |
|---------|-----------|-------|
| Feature A | Yes | Fully supported |
| Feature B | No | Planned for v2 |
| Feature C | Partial | Beta feature |

The table shows current status.
```

**Bad:**

```markdown
Using list when table is better:
- Feature A: Yes - Fully supported
- Feature B: No - Planned for v2
- Feature C: Partial - Beta feature
```

## Emphasis

- Use `*` or `_` for emphasis (italic), `**` or `__` for strong emphasis (bold)
- Be consistent within a document (prefer `*` and `**`)
- Do not use emphasis for headings
- Use backticks for code/technical terms, not emphasis

**Good:**

```markdown
This is *emphasized* text.
This is **strong** text.
Use the `--verbose` flag for details.
```

**Bad:**

```markdown
This is _emphasized_ text with **strong** mixed styles.
Use the *--verbose* flag (should be backticks).
```

## Line Length

- Wrap prose at 80-120 characters per line
- Do not wrap code blocks, tables, or URLs
- Break after sentences or at natural phrase boundaries
- Empty lines do not count toward line length

## Whitespace

- Use a single blank line to separate blocks of content
- Do not use multiple consecutive blank lines
- End files with a single newline character
- Do not use trailing whitespace at the end of lines
- Use spaces (not tabs) for indentation

## Other Rules

### Horizontal Rules

- Use three hyphens (`---`) for horizontal rules
- Surround horizontal rules with blank lines

**Good:**

```markdown
Section one content.

---

Section two content.
```

### Blockquotes

- Use `>` for blockquotes with a space after
- Surround blockquotes with blank lines
- Use multiple `>` for nested quotes

**Good:**

```markdown
As the docs state:

> This is an important note.
> It spans multiple lines.

Back to regular text.
```

### Images

- Use alt text for all images: `![alt text](path/to/image.png)`
- Use relative paths for repository images
- Prefer reference-style for repeated images

**Good:**

```markdown
![Architecture diagram](../media/architecture.png)

See the [logo][logo-img] above.

[logo-img]: ./images/logo.png
```

### HTML

- Avoid HTML in markdown when possible
- Use HTML only for features not supported by markdown
- Close all HTML tags properly

### File Names

- Use lowercase for markdown file names
- Use hyphens (`-`) not underscores (`_`) to separate words
- Use `.md` extension (not `.markdown`)

**Examples:**

- `installation-guide.md` ✅
- `Installation_Guide.markdown` ❌

## Linting

To validate markdown files against these guidelines, use a markdown linter such as:

- [markdownlint](https://github.com/DavidAnson/markdownlint)
- [remark-lint](https://github.com/remarkjs/remark-lint)
- [superlinter](https://github.com/super-linter/super-linter)

Configure the linter to enforce these rules in your CI/CD pipeline.
