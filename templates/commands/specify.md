---
name: specify
description: "Start a new feature by creating a specification and feature branch. This is the first step in the Spec-Driven Development lifecycle."
---

# Available Commands

The following commands are available in the orchestration library:

- **Initialize**
- **Logs**
- **Overview**
- **Start**
- **Status**
- **Stop**

# Command Structure

Each command follows a specific structure to ensure consistency and clarity. The general format is as follows:

```
command [options] [arguments]
```

# Commands Specification

## Initialize

Start a new feature by creating a specification and feature branch.

Given the feature description provided as an argument, do this:

1. Run the script `scripts/create-new-feature.sh --json "{ARGS}"` from the repo root and parse its JSON output for `BRANCH_NAME` and `SPEC_FILE`. All file paths must be absolute.
2. Load `templates/spec-template.md` to understand required sections.
3. Write the specification to `SPEC_FILE` using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
4. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing.

## Logs

Use this command to view the logs of the orchestration process. The logs provide insights into the execution and any issues encountered.

```
logs [options]
```

## Overview

This command provides a summary of the current state of the orchestration library, including active features and their statuses.

```
overview [options]
```

## Start

Initiate the execution of the specified feature. This command triggers the orchestration process.

```
start [feature_name] [options]
```

## Status

Check the current status of the specified feature. This command returns information about the execution state.

```
status [feature_name] [options]
```

## Stop

Terminate the execution of the specified feature. This command halts the orchestration process.

```
stop [feature_name] [options]
```

# Conclusion

This document outlines the commands available in the orchestration library, providing a clear structure for initiating and managing features. Follow the specified commands to ensure a smooth workflow in the Spec-Driven Development lifecycle.