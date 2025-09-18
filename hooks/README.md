# Specify Hooks

This directory contains Git-style hook script samples that customize the `/specify` command workflow. All hooks are optional and follow Git's naming conventions for familiar, intuitive usage.

## Hook Activation

Hooks are provided as `.sample` files and must be activated by removing the `.sample` extension:

**Unix/Linux/macOS:**
```bash
# Activate bash hook (example: prepare-feature-num)
cp .specify/hooks/prepare-feature-num.sample .specify/hooks/prepare-feature-num
chmod +x .specify/hooks/prepare-feature-num
```

**Windows PowerShell:**
```powershell
# Activate PowerShell hook
Copy-Item .specify/hooks/prepare-feature-num.ps1.sample .specify/hooks/prepare-feature-num.ps1
```

**Cross-platform support:** The system automatically detects and uses the appropriate hook format (`.ps1` for Windows, executable scripts for Unix).

## Available Hooks (Git-Style Naming)

### `pre-specify` - Pre-processing Hook
- **When**: Before the entire specify workflow begins
- **Purpose**: Validation, setup, or preprocessing tasks
- **Arguments**: `$1` = feature description
- **Exit codes**: Non-zero exit codes show warnings but don't stop execution

**Example uses:**
- Validate feature description format and length
- Check prerequisites or dependencies
- Set up external resources or authenticate

### `prepare-feature-num` - Feature Number Preparation Hook
- **When**: Before auto-incrementing feature number (similar to Git's `prepare-commit-msg`)
- **Purpose**: Provide custom feature numbering from external sources
- **Arguments**: `$1` = feature description
- **Output**: Integer feature number (stdout)
- **Fallback**: If hook fails or outputs nothing, auto-increment is used

**Example uses:**
- Fetch feature number from external spec server
- Create GitHub issue and use issue number
- Implement custom numbering schemes

### `post-checkout` - Post-Checkout Hook
- **When**: After branch creation and checkout (matches Git's `post-checkout`)
- **Purpose**: Setup tasks after branch creation but before spec writing
- **Arguments**: `$1` = feature description
- **Environment**: `BRANCH_NAME`, `SPEC_FILE`, `FEATURE_NUM` are available
- **Exit codes**: Non-zero exit codes show warnings but don't stop execution

**Example uses:**
- Initialize additional project files
- Set up branch-specific configurations
- Create directory structures
- Send branch creation notifications

### `post-specify` - Post-Specification Hook
- **When**: After spec file is completely written (true post-specify)
- **Purpose**: Final integration tasks and notifications
- **Arguments**: `$1` = feature description
- **Environment**: `BRANCH_NAME`, `SPEC_FILE`, `FEATURE_NUM` are available
- **Exit codes**: Non-zero exit codes show warnings but don't stop execution

**Example uses:**
- Create GitHub issues linking to completed specs
- Send completion notifications
- Trigger CI/CD pipelines for spec review
- Update external tracking systems

## Hook Examples

### Custom Feature Numbering from Server

**Bash version:**
```bash
#!/bin/bash
# .specify/hooks/prepare-feature-num
FEATURE_DESC="$1"
FEATURE_NUMBER=$(curl -s "$SPEC_SERVER/api/next-number")
echo "$FEATURE_NUMBER"
```

**PowerShell version:**
```powershell
#!/usr/bin/env pwsh
# .specify/hooks/prepare-feature-num.ps1
param([string]$FeatureDescription)
$featureNumber = Invoke-RestMethod -Uri "$env:SPEC_SERVER/api/next-number"
Write-Output $featureNumber
```

### GitHub Issue for Feature Number

**Bash version:**
```bash
#!/bin/bash
# .specify/hooks/prepare-feature-num
FEATURE_DESC="$1"
ISSUE_URL=$(gh issue create --title "Spec: $FEATURE_DESC" --body "Specification development")
ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -o '[0-9]*$')
echo "$ISSUE_NUMBER"
```

**PowerShell version:**
```powershell
#!/usr/bin/env pwsh
# .specify/hooks/prepare-feature-num.ps1
param([string]$FeatureDescription)
$issueUrl = gh issue create --title "Spec: $FeatureDescription" --body "Specification development"
$issueNumber = [regex]::Match($issueUrl, '\d+$').Value
Write-Output $issueNumber
```

### Post-Checkout Setup

**Bash version:**
```bash
#!/bin/bash
# .specify/hooks/post-checkout
FEATURE_DESC="$1"
# Create additional project directories
mkdir -p "docs/$BRANCH_NAME"
# Set up branch-specific configuration
echo "Branch $BRANCH_NAME created for: $FEATURE_DESC" > "docs/$BRANCH_NAME/info.txt"
```

### Post-Specification Notification

**Bash version:**
```bash
#!/bin/bash
# .specify/hooks/post-specify
FEATURE_DESC="$1"
# Create completion issue
gh issue create --title "Spec Complete: $FEATURE_DESC" --body "Specification ready for review: $SPEC_FILE"
# Send notification
echo "Specification $FEATURE_NUM completed: $SPEC_FILE" | mail -s "Spec Ready" team@company.com
```

## Technical Notes

### Platform-Specific Behavior
- **Unix/Linux/macOS**: Hooks must be executable (`chmod +x`). System looks for exact hook name.
- **Windows**: PowerShell hooks use `.ps1` extension. No execute permission needed.
- **Cross-platform**: System automatically detects and uses appropriate hook format.

### Hook Execution
- Hooks are called with the feature description as the first argument
- The `feature-num` hook should output only the number to stdout
- The `post-specify` hook has access to environment variables set by the create script
- Failed hooks generate warnings but don't stop the specification process
- Non-existent or non-executable hook files are safely ignored

### Available Hook Formats
- `hook-name` - Bash/shell script (Unix/Linux/macOS)
- `hook-name.ps1` - PowerShell script (Windows/cross-platform)

### Hook Execution Order
1. `pre-specify` - Workflow validation and setup
2. `prepare-feature-num` - Custom feature numbering (optional)
3. **Script execution** - Branch/directory creation
4. `post-checkout` - Post-branch setup tasks
5. **Spec writing** - Template processing and content generation
6. `post-specify` - Completion notifications and final tasks

## Customization

**To activate and customize hooks:**

1. **Copy the sample**: Remove `.sample` from the appropriate hook file
2. **Make executable** (Unix only): `chmod +x .specify/hooks/hook-name`
3. **Edit the hook**: Customize the logic for your needs
4. **Test**: Run the hook manually with test data

**Example activation:**
```bash
# Unix/Linux/macOS - Activate prepare-feature-num hook
cp .specify/hooks/prepare-feature-num.sample .specify/hooks/prepare-feature-num
chmod +x .specify/hooks/prepare-feature-num

# Windows PowerShell - Activate prepare-feature-num hook
Copy-Item .specify/hooks/prepare-feature-num.ps1.sample .specify/hooks/prepare-feature-num.ps1
```

The Git-style naming provides familiar patterns for developers already using Git hooks, making the system more intuitive and easier to understand.