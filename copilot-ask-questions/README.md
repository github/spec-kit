# Copilot askQuestions Clarify Preset

A [Spec Kit](https://github.com/github/spec-kit) preset that enhances the `/speckit.clarify` command to use the `vscode/askQuestions` tool for batched interactive questioning, reducing API request costs in GitHub Copilot.

## Problem

When using `/speckit.clarify` with GitHub Copilot in VS Code, each question-answer cycle consumes multiple API requests.

See [github/spec-kit#1657](https://github.com/github/spec-kit/issues/1657) for the original issue report.

## Solution

This preset overrides the clarify command's questioning loop to:

- **When `vscode/askQuestions` is available**: Present **all** queued questions (up to 5) in a **single batched call**, with full option lists and recommendations for each question. This minimizes round-trips and API request consumption.
- **When `vscode/askQuestions` is not available**: Fall back to the standard sequential one-question-at-a-time flow, preserving full compatibility with non-Copilot agents.

All other behavior (ambiguity scanning, spec integration, validation, reporting) remains identical to the core clarify command.

## Installation

### From a release URL

```bash
# FIXME ?
specify preset add --from https://github.com/github/spec-kit/releases/.../copilot-ask-questions.zip
```

### From local directory (development)

```bash
specify preset add --dev ./copilot-ask-questions
```

## Usage

After installation, use `/speckit.clarify` as usual. The preset override is applied automatically.

If you're using GitHub Copilot in VS Code, questions will be presented via the interactive `askQuestions` UI. Otherwise, behavior is unchanged.

## Removal

```bash
specify preset remove copilot-ask-questions
```

## Requirements

- Spec Kit >= 0.1.0

## Credits

- Original issue: [github/spec-kit#1657](https://github.com/github/spec-kit/issues/1657) by [@Son-Dam](https://github.com/Son-Dam)
- Interactive questioning approach: [@stenyin](https://github.com/stenyin) ([comment](https://github.com/github/spec-kit/issues/1657#issuecomment-3976746134))
- Batched questioning refinement and PR: [@fdcastel](https://github.com/fdcastel) ([PR #1962](https://github.com/github/spec-kit/pull/1962))

## License

MIT
