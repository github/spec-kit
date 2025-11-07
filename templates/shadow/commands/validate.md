---
description: Validate specification format and quality
---

# Validate Specification

Run specification validation to check format and quality.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/validate-spec{SCRIPT_EXT} <spec-file>
```

## What This Checks

### Structure
- All required sections present
- Proper heading hierarchy
- Consistent formatting

### Content Quality
- Acceptance criteria properly formatted
- Requirements have IDs and descriptions
- Risks include mitigation strategies
- Dependencies are clearly listed

### References
- No broken internal links
- Cross-references are valid
- External links are accessible

### Token Budget
- Specification size is within limits
- Complexity is manageable

## Fix Common Issues

### Missing Sections
Add any missing required sections from template

### Broken References
Update links to valid paths

### Format Issues
Follow markdown best practices

## Re-validate

After fixing issues, run validation again until it passes.
