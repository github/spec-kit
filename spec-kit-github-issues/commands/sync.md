---
description: "Sync spec artifacts with updates from the source GitHub Issue"
tools:
  - 'bash/gh'
---

# Sync Spec with GitHub Issue

Keep spec artifacts updated when the source GitHub Issue is modified. Detects changes in title, body, labels, and comments, then updates the spec accordingly.

## User Input

$ARGUMENTS

Optional: Specify feature directory or issue number. If not provided, syncs all linked issues in the project.

Examples:
- `/speckit.github-issues.sync` (sync all linked issues)
- `/speckit.github-issues.sync 001-feature-name` (sync specific feature)
- `/speckit.github-issues.sync #2175` (sync specific issue)

## Prerequisites

1. GitHub CLI (`gh`) must be installed and authenticated
2. Spec must have been previously imported using `/speckit.github-issues.import`
3. Issue link metadata must exist (`.issue-link` file)

## Steps

### 1. Find Linked Issues

Discover all specs that are linked to GitHub Issues.

```bash
# Find all .issue-link files
linked_specs=()
for link_file in .specify/specs/*/.issue-link; do
  if [ -f "$link_file" ]; then
    linked_specs+=("$link_file")
  fi
done

if [ ${#linked_specs[@]} -eq 0 ]; then
  echo "No linked issues found. Use /speckit.github-issues.import first."
  exit 0
fi

echo "Found ${#linked_specs[@]} linked issue(s)"
```

### 2. Parse Arguments

Determine which specs to sync based on user input.

```bash
input="$ARGUMENTS"
specs_to_sync=()

if [ -z "$input" ]; then
  # Sync all linked issues
  specs_to_sync=("${linked_specs[@]}")
elif [[ "$input" =~ ^#([0-9]+)$ ]]; then
  # Sync specific issue number
  issue_num="${BASH_REMATCH[1]}"
  for link_file in "${linked_specs[@]}"; do
    linked_issue=$(grep "^issue_number:" "$link_file" | cut -d' ' -f2)
    if [ "$linked_issue" = "$issue_num" ]; then
      specs_to_sync+=("$link_file")
    fi
  done
else
  # Sync specific feature directory
  feature_dir=".specify/specs/$input"
  link_file="$feature_dir/.issue-link"
  if [ -f "$link_file" ]; then
    specs_to_sync+=("$link_file")
  else
    echo "Error: No linked issue found for feature: $input"
    exit 1
  fi
fi

if [ ${#specs_to_sync[@]} -eq 0 ]; then
  echo "No matching linked issues found."
  exit 0
fi
```

### 3. Check for Updates

For each linked issue, fetch current data and compare with last sync.

```bash
for link_file in "${specs_to_sync[@]}"; do
  feature_dir=$(dirname "$link_file")
  spec_file="$feature_dir/spec.md"
  
  # Read metadata
  repo=$(grep "^repository:" "$link_file" | cut -d' ' -f2)
  issue_number=$(grep "^issue_number:" "$link_file" | cut -d' ' -f2)
  last_synced=$(grep "^last_synced:" "$link_file" | cut -d' ' -f2)
  
  echo ""
  echo "Checking $repo#$issue_number..."
  
  # Fetch current issue data
  issue_data=$(gh issue view "$issue_number" \
    --repo "$repo" \
    --json title,body,labels,comments,updatedAt,state)
  
  if [ $? -ne 0 ]; then
    echo "  ✗ Failed to fetch issue data"
    continue
  fi
  
  # Check if issue was updated since last sync
  updated_at=$(echo "$issue_data" | jq -r '.updatedAt')
  
  if [[ "$updated_at" > "$last_synced" ]] || [ -z "$last_synced" ]; then
    echo "  ✓ Updates detected (last synced: $last_synced, updated: $updated_at)"
    
    # Store for processing
    echo "$feature_dir|$repo|$issue_number|$spec_file" >> /tmp/specs_to_update.txt
  else
    echo "  ✓ No updates since last sync"
  fi
done
```

### 4. Review Changes

Show what will be updated and prompt for confirmation.

```bash
if [ ! -f /tmp/specs_to_update.txt ]; then
  echo ""
  echo "All specs are up to date!"
  exit 0
fi

echo ""
echo "The following specs have updates available:"
echo ""

while IFS='|' read -r feature_dir repo issue_number spec_file; do
  echo "  • $repo#$issue_number → $spec_file"
done < /tmp/specs_to_update.txt

echo ""
read -p "Apply updates? (y/n): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Sync cancelled."
  rm /tmp/specs_to_update.txt
  exit 0
fi
```

### 5. Apply Updates

Update each spec with the latest issue data.

```bash
while IFS='|' read -r feature_dir repo issue_number spec_file; do
  echo ""
  echo "Updating $spec_file..."
  
  # Fetch fresh issue data
  issue_data=$(gh issue view "$issue_number" \
    --repo "$repo" \
    --json title,body,labels,comments,updatedAt,state,url)
  
  title=$(echo "$issue_data" | jq -r '.title')
  body=$(echo "$issue_data" | jq -r '.body // ""')
  state=$(echo "$issue_data" | jq -r '.state')
  labels=$(echo "$issue_data" | jq -r '.labels[].name' | paste -sd ',' -)
  url=$(echo "$issue_data" | jq -r '.url')
  updated_at=$(echo "$issue_data" | jq -r '.updatedAt')
  
  # Update spec frontmatter
  sed -i "s|^**Issue Status:**.*|**Issue Status:** $state|" "$spec_file"
  sed -i "s|^**Labels:**.*|**Labels:** $labels|" "$spec_file"
  sed -i "s|^**Last Updated:**.*|**Last Updated:** $(date -u +"%Y-%m-%d")|" "$spec_file"
  
  # Update title if changed
  current_title=$(grep "^# Feature Specification:" "$spec_file" | sed 's/^# Feature Specification: //')
  if [ "$current_title" != "$title" ]; then
    sed -i "s|^# Feature Specification:.*|# Feature Specification: $title|" "$spec_file"
    echo "  ✓ Updated title"
  fi
  
  # Append new comments to Discussion Notes section
  new_comments=$(echo "$issue_data" | jq -r --arg last_synced "$last_synced" \
    '.comments[] | select(.createdAt > $last_synced) | "**\(.author.login)** (\(.createdAt)):\n\(.body)\n"')
  
  if [ -n "$new_comments" ]; then
    # Find Discussion Notes section and append
    echo "" >> "$spec_file"
    echo "### New Comments (synced $(date -u +"%Y-%m-%d"))" >> "$spec_file"
    echo "" >> "$spec_file"
    echo "$new_comments" >> "$spec_file"
    echo "  ✓ Added new comments"
  fi
  
  # Update metadata
  link_file="$feature_dir/.issue-link"
  sed -i "s|^last_synced:.*|last_synced: $(date -u +"%Y-%m-%dT%H:%M:%SZ")|" "$link_file"
  
  echo "  ✓ Sync complete"
  
done < /tmp/specs_to_update.txt

rm /tmp/specs_to_update.txt
```

### 6. Summary

Provide a summary of the sync operation.

```bash
echo ""
echo "Sync Summary:"
echo "  ✓ All linked issues synced successfully"
echo ""
echo "Next steps:"
echo "  1. Review the updated specs"
echo "  2. Update plan.md if requirements changed significantly"
echo "  3. Update tasks.md if needed"
```

## Configuration

Load configuration from `.specify/extensions/github-issues/github-issues-config.yml`:
- `sync.auto_detect`: Automatically detect changes
- `sync.prompt_before_sync`: Prompt before applying changes

## Error Handling

- Verify `gh` CLI is installed and authenticated
- Check that `.issue-link` metadata exists
- Handle network errors gracefully
- Skip specs that fail to update and continue with others
- Preserve original spec content if update fails
