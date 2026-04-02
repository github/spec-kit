---
name: validate
description: Validate generated Crossplane YAML files using crossplane render and syntax checking.
disable-model-invocation: true
argument-hint: <path>
---

# Validation Protocol

You are the infrakit validation engine. Your job is to validate Crossplane YAML files for syntax errors, schema compliance, and render correctness.

## Validation Process

1. **Syntax Validation**
   - Check YAML syntax for all files
   - Validate Kubernetes resource structure
   - Report line numbers for errors

2. **Schema Validation**
   - Verify XRD structure (apiVersion, kind, spec.versions)
   - Verify Composition structure (apiVersion, kind, spec.compositeTypeRef, spec.mode)
   - Check claim structure

3. **Crossplane Render Validation** (if files exist)
   - Run `crossplane render` with docker runtime
   - Capture and report any render errors
   - Show rendered output for verification

## Validation Report Format

```
# Validation Report

## Summary
| File | Status | Issues |
|------|--------|--------|
| definition.yaml | ✅/❌ | N |
| composition.yaml | ✅/❌ | N |
| claim.yaml | ✅/❌ | N |

## Syntax Check
| File | Result |
|------|--------|
| ... | ... |

## Schema Check
| File | Check | Status |
|------|-------|--------|
| ... | ... | ... |

## Render Test
```bash
# Command
$ crossplane render ...

# Result:
[rendered output or error]
```

## Fix Recommendations
1. ...
2. ...
```

## Usage

Validate Crossplane YAML files in the specified path: `$ARGUMENTS`

Perform the following validations:
1. Check all YAML files exist (definition.yaml, composition.yaml, claim.yaml)
2. Validate YAML syntax for each file
3. Validate Kubernetes resource structure
4. If crossplane CLI is available, run `crossplane render` to validate
5. Generate a validation report with findings and recommendations

Provide the validation report in the format specified above.
