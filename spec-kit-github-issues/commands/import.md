---
description: "Import a GitHub Issue and generate spec.md with structured requirements"
tools:
  - 'bash/gh'
---

# Import GitHub Issue to Spec

Import a GitHub Issue (title, body, labels, comments) and generate a structured `spec.md` file with requirements, scenarios, and acceptance criteria.

## User Input

$ARGUMENTS

Expected format: `<owner>/<repo>#<issue_number>` or just `#<issue_number>` (uses current repo)

Examples:
- `github/spec-kit#2175`
- `#2175` (if in a GitHub repository)

## Prerequisites

1. GitHub CLI (`gh`) must be installed and authenticated
2. You must have read access to the specified repository
3. Run `gh auth login` if not already authenticated

## Steps

### 1. Parse Arguments

Extract the repository owner, name, and issue number from the user input.

```bash
# Parse input format
input="$ARGUMENTS"

if [[ "$input" =~ ^#([0-9]+)$ ]]; then
  # Format: #123 (use current repo)
  issue_number="${BASH_REMATCH[1]}"
  repo_info=$(gh repo view --json nameWithOwner -q .nameWithOwner)
  repo_owner=$(echo "$repo_info" | cut -d'/' -f1)
  repo_name=$(echo "$repo_info" | cut -d'/' -f2)
elif [[ "$input" =~ ^([^/]+)/([^#]+)#([0-9]+)$ ]]; then
  # Format: owner/repo#123
  repo_owner="${BASH_REMATCH[1]}"
  repo_name="${BASH_REMATCH[2]}"
  issue_number="${BASH_REMATCH[3]}"
else
  echo "Error: Invalid format. Use 'owner/repo#123' or '#123'"
  exit 1
fi

echo "Importing issue #$issue_number from $repo_owner/$repo_name"
```

### 2. Fetch Issue Data

Retrieve the issue details using GitHub CLI.

```bash
# Fetch issue data
issue_data=$(gh issue view "$issue_number" \
  --repo "$repo_owner/$repo_name" \
  --json title,body,labels,comments,author,createdAt,updatedAt,url,state)

if [ $? -ne 0 ]; then
  echo "Error: Failed to fetch issue. Check repository access and issue number."
  exit 1
fi

# Extract fields
title=$(echo "$issue_data" | jq -r '.title')
body=$(echo "$issue_data" | jq -r '.body // ""')
url=$(echo "$issue_data" | jq -r '.url')
author=$(echo "$issue_data" | jq -r '.author.login')
created_at=$(echo "$issue_data" | jq -r '.createdAt')
state=$(echo "$issue_data" | jq -r '.state')
labels=$(echo "$issue_data" | jq -r '.labels[].name' | paste -sd ',' -)
```

### 3. Parse Issue Body

Extract structured information from the issue body:
- Problem statement
- Proposed solution
- Acceptance criteria
- Alternative approaches

```bash
# Parse sections from issue body
problem=$(echo "$body" | sed -n '/^[#*]*\s*Problem/,/^[#*]*\s*[A-Z]/p' | sed '$d' | sed '1d')
solution=$(echo "$body" | sed -n '/^[#*]*\s*[Pp]roposed [Ss]olution/,/^[#*]*\s*[A-Z]/p' | sed '$d' | sed '1d')
alternatives=$(echo "$body" | sed -n '/^[#*]*\s*[Aa]lternative/,/^[#*]*\s*[A-Z]/p' | sed '$d' | sed '1d')
```

### 4. Process Comments

Extract relevant information from issue comments.

```bash
# Get comments
comments=$(echo "$issue_data" | jq -r '.comments[] | "**\(.author.login)** (\(.createdAt)):\n\(.body)\n"')
```

### 5. Generate Spec File

Create a structured `spec.md` file following the spec-kit template format.

```bash
# Determine feature directory
feature_dir=$(ls -d .specify/specs/*/ 2>/dev/null | tail -1)
if [ -z "$feature_dir" ]; then
  # Create new feature
  feature_num="001"
  feature_name=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')
  feature_dir=".specify/specs/${feature_num}-${feature_name}"
  mkdir -p "$feature_dir"
else
  # Use existing feature directory
  feature_dir="${feature_dir%/}"
fi

spec_file="$feature_dir/spec.md"
```

### 6. Write Spec Content

Generate the spec.md file with structured content from the issue.

```markdown
# Feature Specification: $title

**Source Issue:** [$repo_owner/$repo_name#$issue_number]($url)
**Issue Author:** @$author
**Issue Status:** $state
**Labels:** $labels
**Last Updated:** $(date -u +"%Y-%m-%d")

## Overview

$body

## Problem Statement

$problem

## Proposed Solution

$solution

## User Stories

<!-- Extract or generate user stories from the issue description -->

### User Story 1: [Title]

**As a** [user type]
**I want** [goal]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

## Functional Requirements

<!-- Extract requirements from the issue -->

### Requirement 1: [Title]

**Description:** [Detailed description]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

## Alternative Approaches Considered

$alternatives

## Discussion Notes

<!-- Include relevant comments from the issue -->

$comments

## Review & Acceptance Checklist

- [ ] All user stories are clearly defined
- [ ] Acceptance criteria are testable
- [ ] Edge cases are documented
- [ ] Dependencies are identified
- [ ] Success metrics are defined
```

### 7. Link Issue to Spec

Add metadata linking the spec back to the source issue.

```bash
# Create metadata file
metadata_file="$feature_dir/.issue-link"
cat > "$metadata_file" <<EOF
repository: $repo_owner/$repo_name
issue_number: $issue_number
issue_url: $url
imported_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
last_synced: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo "✓ Spec generated at: $spec_file"
echo "✓ Linked to issue: $url"
```

### 8. Summary

Provide a summary of the import operation.

```bash
echo ""
echo "Import Summary:"
echo "  Issue: $repo_owner/$repo_name#$issue_number"
echo "  Title: $title"
echo "  Spec: $spec_file"
echo ""
echo "Next steps:"
echo "  1. Review and refine the generated spec"
echo "  2. Run /speckit.clarify to fill in any gaps"
echo "  3. Run /speckit.plan to create implementation plan"
echo "  4. Use /speckit.github-issues.sync to keep spec updated with issue changes"
```

## Configuration

Load configuration from `.specify/extensions/github-issues/github-issues-config.yml` if it exists.

## Error Handling

- Verify `gh` CLI is installed and authenticated
- Check repository access permissions
- Validate issue number exists
- Handle missing or malformed issue data gracefully
