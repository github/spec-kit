# Add notice that git extension will no longer be enabled by default at 1.0.0

> **Source**: [#2165](https://github.com/github/spec-kit/issues/2165) — imported on 2026-04-12

## Overview

Add a deprecation notice during `specify init` to inform users that the git extension, currently auto-enabled by default, will require explicit opt-in starting with v1.0.0. This ensures users are aware of the upcoming behavioral change well in advance.

## Problem Statement

The `git` extension is currently bundled and enabled by default during `specify init`. Starting with v1.0.0, it will still be bundled but no longer enabled by default — users will need to explicitly opt in. Without advance notice, users may be surprised by this change when upgrading to v1.0.0.

## Requirements

### Functional Requirements

- FR-1: During `specify init`, display a warning notice when the git extension is auto-enabled
- FR-2: The notice must clearly state the timeline (v1.0.0) for the change
- FR-3: The notice must explain how to opt in after the change (`specify init --extension git` or `specify extension add git`)
- FR-4: The notice must be non-blocking (warning styling, does not halt initialization)

### Non-Functional Requirements

- NFR-1: Notice should use yellow/warning styling consistent with existing CLI warning patterns
- NFR-2: Notice should be concise and actionable

## User Scenarios

### Scenario 1: User runs specify init and sees deprecation notice

**Given** a user is initializing a new project with `specify init`
**When** the git extension is auto-enabled as part of the default behavior
**Then** a warning notice is displayed informing them that the git extension will require explicit opt-in starting with v1.0.0

### Scenario 2: User understands how to opt in after v1.0.0

**Given** a user sees the deprecation notice during `specify init`
**When** they read the notice
**Then** they understand they can use `specify init --extension git` or `specify extension add git` to enable the git extension after v1.0.0

## Acceptance Criteria

- [ ] AC-1: `specify init` shows a notice when the git extension is auto-enabled
- [ ] AC-2: Notice is visible but non-blocking (yellow/warning styling)
- [ ] AC-3: Message clearly states the timeline (v1.0.0) and how to opt in

## Out of Scope

- Changes to the git extension itself or its functionality
- Changes to the bundled status of the git extension (it remains bundled/shipped with spec-kit)
- Actually removing the default-enabled behavior (that happens at v1.0.0, not now)
