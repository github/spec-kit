---
description: Analyze errors with AI-assisted context
---

# Error Analysis

Analyze errors with additional context for debugging.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/error-analysis{SCRIPT_EXT} "<error-message>"
```

Or paste the full error output when prompted.

## What This Provides

- **Root cause analysis** - Likely source of the error
- **Related code** - Files and functions involved
- **Common causes** - Known patterns causing this error
- **Fix suggestions** - Potential solutions
- **Similar issues** - Related problems in codebase

## Example

```bash
{SHADOW_PATH}/scripts/bash/error-analysis{SCRIPT_EXT} "TypeError: Cannot read property 'map' of undefined"
```

## What Gets Analyzed

- Error message and stack trace
- Relevant code context
- Recent changes to affected files
- Dependencies and configurations
- Known issues in project

## Best Practices

- Include full stack trace
- Note when the error started occurring
- Describe what you were trying to do
- Mention any recent changes
- Provide steps to reproduce

## After Analysis

1. Review suggested fixes
2. Understand the root cause
3. Apply the fix
4. Add tests to prevent regression
5. Document if it's a common issue
