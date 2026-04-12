---
description: "Add bidirectional traceability between spec artifacts and source issue"
tools:
  - 'bash/gh'
---

# Link Spec to GitHub Issue

Add bidirectional traceability between spec artifacts and their source GitHub Issue. Creates links in both the spec file and the GitHub Issue.

## User Input

$ARGUMENTS

Expected format: `<owner>/<repo>#<issue_number>` or just `#<issue_number>` (uses current repo)

Examples:
- `github/spec-kit#2175`
- `#2175` (if in a GitHub repository)

## Prerequisites

1. GitHub CLI (`gh`) must be installed and authenticated
2. You must have write access to the repository to add comments
3. A spec file must exist in the current feature directory

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

repo="$repo_owner/$repo_name"
echo "Linking to issue #$issue_number from $repo"
```

### 2. Verify Issue Exists

Check that the issue exists and is accessible.

```bash
# Fetch issue data
issue_data=$(gh issue view "$issue_number" \
  --repo "$repo" \
  --json title,url,state)

if [ $? -ne 0 ]; then
  echo "Error: Failed to fetch issue. Check repository access and issue number."
  exit 1
fi

title=$(echo "$issue_data" | jq -r '.title')
url=$(echo "$issue_data" | jq -r '.url')
state=$(echo "$issue_data" | jq -r '.state')

echo "Found issue: $title"
```

### 3. Find Current Feature Spec

Locate the spec file in the current feature directory.

```bash
# Determine current feature directory
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

if [[ "$current_branch" =~ ^[0-9]+-(.+)$ ]]; then
  # Extract feature name from branch
  feature_pattern="${current_branch}"
  feature_dir=$(find .specify/specs -maxdepth 1 -type d -name "$feature_pattern" | head -1)
else
  # Use most recent feature directory
  feature_dir=$(ls -td .specify/specs/*/ 2>/dev/null | head -1)
fi

if [ -z "$feature_dir" ]; then
  echo "Error: No feature directory found. Create a spec first."
  exit 1
fi

feature_dir="${feature_dir%/}"
spec_file="$feature_dir/spec.md"

if [ ! -f "$spec_file" ]; then
  echo "Error: Spec file not found at $spec_file"
  exit 1
fi

echo "Found spec: $spec_file"
```

### 4. Add Link to Spec

Update the spec file to include a reference to the source issue.

```bash
# Check if link already exists
if grep -q "Source Issue.*$repo#$issue_number" "$spec_file"; then
  echo "✓ Spec already linked to this issue"
else
  # Add source issue link to spec frontmatter
  # Find the first heading and insert before it
  temp_file=$(mktemp)
  
  # Read spec and add link after title
  awk -v repo="$repo" -v num="$issue_number" -v url="$url" -v state="$state" '
    /^# Feature Specification:/ {
      print $0
      print ""
      print "**Source Issue:** [" repo "#" num "](" url ")"
      print "**Issue Status:** " state
      print "**Last Updated:** " strftime("%Y-%m-%d")
      next
    }
    { print }
  ' "$spec_file" > "$temp_file"
  
  mv "$temp_file" "$spec_file"
  echo "✓ Added issue link to spec"
fi
```

### 5. Create Metadata File

Create or update the `.issue-link` metadata file.

```bash
# Create metadata file
metadata_file="$feature_dir/.issue-link"

cat > "$metadata_file" <<EOF
repository: $repo
issue_number: $issue_number
issue_url: $url
linked_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
last_synced: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo "✓ Created link metadata"
```

### 6. Add Comment to GitHub Issue

Add a comment to the GitHub Issue linking back to the spec.

```bash
# Get current git branch and commit
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
current_commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Get repository URL
repo_url=$(git config --get remote.origin.url 2>/dev/null | sed 's/\.git$//')
if [[ "$repo_url" =~ ^git@ ]]; then
  repo_url=$(echo "$repo_url" | sed 's|^git@github.com:|https://github.com/|')
fi

# Construct spec URL (if on GitHub)
if [[ "$repo_url" =~ github.com ]]; then
  spec_url="$repo_url/blob/$current_branch/$spec_file"
else
  spec_url="$spec_file"
fi

# Create comment body
comment_body="## 📋 Spec-Driven Development

This issue has been imported into a specification document for structured development.

**Spec Location:** \`$spec_file\`
**Branch:** \`$current_branch\`
**Spec URL:** $spec_url

The spec will be kept in sync with this issue using the \`/speckit.github-issues.sync\` command.

---
*Generated by [Spec Kit GitHub Issues Extension](https://github.com/github/spec-kit)*"

# Post comment to issue
gh issue comment "$issue_number" \
  --repo "$repo" \
  --body "$comment_body"

if [ $? -eq 0 ]; then
  echo "✓ Added traceability comment to issue"
else
  echo "⚠ Warning: Could not add comment to issue (may lack permissions)"
fi
```

### 7. Summary

Provide a summary of the linking operation.

```bash
echo ""
echo "Link Summary:"
echo "  Issue: $repo#$issue_number"
echo "  Title: $title"
echo "  Spec: $spec_file"
echo "  Metadata: $metadata_file"
echo ""
echo "Bidirectional traceability established:"
echo "  ✓ Spec references issue"
echo "  ✓ Issue references spec (via comment)"
echo ""
echo "Next steps:"
echo "  • Use /speckit.github-issues.sync to keep spec updated with issue changes"
echo "  • Continue with /speckit.plan to create implementation plan"
```

## Configuration

Load configuration from `.specify/extensions/github-issues/github-issues-config.yml`:
- `link.add_to_frontmatter`: Add issue link to spec frontmatter
- `link.add_to_body`: Add issue reference to spec body
- `link.link_format`: Format for the link in spec body

## Error Handling

- Verify `gh` CLI is installed and authenticated
- Check repository write permissions for commenting
- Handle cases where spec already has a link
- Gracefully handle network errors
- Warn if comment cannot be added but continue with local linking
