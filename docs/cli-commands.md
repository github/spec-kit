# CLI Commands

The `specify` command-line interface (CLI) is a tool for initializing and managing `spec-kit` projects.

## `specify init`

Initializes a new `spec-kit` project.

### Usage

```bash
specify init [PROJECT_NAME] [OPTIONS]
```

### Arguments

-   `PROJECT_NAME`: The name of the new project directory. If not provided, you must use the `--here` flag.

### Options

-   `--ai [claude|gemini|copilot]`: The AI assistant to use.
-   `--ignore-agent-tools`: Skip checks for AI agent tools.
-   `--no-git`: Skip git repository initialization.
-   `--here`: Initialize the project in the current directory.

## `specify update`

Updates an existing `spec-kit` project with the latest templates.

### Usage

```bash
specify update [OPTIONS]
```

### Options

-   `--force`: Force the update without confirmation.

## `specify check`

Checks that all required tools for `spec-kit` are installed.

### Usage

```bash
specify check
```
