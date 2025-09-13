# Quickstart: AI Model Switching and Task Tracking

**Feature**: 001-ai-model-switching
**Version**: 1.0.0
**Audience**: Developers using spec-kit CLI

## Getting Started

### Prerequisites
- Spec-kit CLI installed and working
- Existing project OR ability to create new project
- Terminal with minimum 100x24 character display

### 5-Minute Demo

#### 1. Check Current Setup
```bash
# Verify you have a spec-kit project
specify detect-project

# Expected output:
# ✓ Valid Spec-Kit Project
# Current AI Model: gemini
# Project Version: 2.0.1
```

#### 2. List Available Models
```bash
# See what AI models are available
specify list-models

# Expected output:
# MODEL    PROVIDER    STATUS     COMPATIBLE
# gemini   google      active     ✓
# claude   anthropic   available  ✓
# gpt4     openai      available  ⚠️
```

#### 3. Switch AI Models
```bash
# Switch from current model to Claude
specify switch-model claude

# You'll see a progress dialog:
# ⠋ Switching to Claude...
#   ✓ Creating backup
#   ✓ Validating compatibility
#   ⠋ Migrating configurations
#   □ Updating project files
```

#### 4. Enable Task Tracking UI
```bash
# Turn on the task tracking sidebar
specify track-tasks enable

# Now run any spec-kit command to see the sidebar
specify plan my-new-feature
```

**Expected Result**: You should see a split-screen interface with your main command output on the left and a task tracking sidebar on the right showing real-time progress.

### Common Workflows

#### Scenario A: Developer Wants to Try Different AI Model
```bash
# Current situation: Using Gemini, want to try Claude
specify list-models                    # See available options
specify switch-model claude --dry-run  # Preview changes
specify switch-model claude            # Actually switch

# Test the new model
specify /specify my-test-feature

# If not satisfied, switch back
specify switch-model gemini
```

#### Scenario B: Setting Up Task Tracking for Team
```bash
# Enable task tracking for better visibility
specify track-tasks enable --sidebar

# Run a complex command to see tracking in action
specify /plan complex-feature "Add user authentication system"

# Tasks will appear in real-time:
# ✓ [001] Parse feature description
# ⏳[002] Research authentication patterns
# □ [003] Generate data models
# □ [004] Create API contracts
```

#### Scenario C: Recovering from Issues
```bash
# If something goes wrong during model switch
specify detect-project --repair

# If project gets corrupted
specify reset-project --backup --keep-specs

# Check what backups are available
ls -la .specify/backups/
```

## Feature Validation Tests

### Test 1: Model Switching Works Without Data Loss
```bash
# Setup: Start with Gemini model
echo "Testing model switching..."

# Create some specifications
specify /specify test-feature "Simple test feature"
specify /plan test-feature
ls specs/  # Note the files created

# Switch to Claude
specify switch-model claude

# Verify specifications are preserved
ls specs/  # Should show same files
specify detect-project  # Should show claude as current model

# Verify we can continue working
specify /plan another-test-feature "Another test"
```
**Expected**: All existing specs preserved, new model active, can create new specs.

### Test 2: Automatic Project Detection
```bash
# Setup: Navigate to project directory
cd /path/to/existing/project

# Test detection without explicit init
specify list-models  # Should work without requiring init
specify detect-project  # Should show project details

# Test in non-project directory
cd /tmp
specify detect-project  # Should indicate no project found
```
**Expected**: Commands work in project directories, fail gracefully elsewhere.

### Test 3: Task Tracking UI
```bash
# Enable task tracking
specify track-tasks enable

# Run command that generates multiple tasks
specify /plan complex-feature "Multi-step feature with database, API, and UI"

# Verify UI shows:
# - Total task count
# - Completed tasks (green checkmarks)
# - Failed tasks (red X marks)
# - Current task progress
# - Real-time updates
```
**Expected**: Sidebar appears, updates in real-time, shows accurate status.

### Test 4: Error Recovery
```bash
# Simulate corruption
echo "invalid json" > .specify/config/ai-model.json

# Verify graceful error handling
specify detect-project  # Should detect and offer repair

# Test backup restoration
specify switch-model claude  # Should fail safely
ls .specify/backups/  # Should show available backups

# Test repair
specify detect-project --repair  # Should fix the corruption
```
**Expected**: Errors handled gracefully, backup/restore works, auto-repair available.

## Performance Benchmarks

### Response Time Tests
Run these commands and verify they complete within expected times:

```bash
# Model switching should complete in < 30 seconds
time specify switch-model claude
# Expected: real time < 30s

# Project detection should be instant
time specify detect-project
# Expected: real time < 1s

# Task UI updates should be real-time
# (Visual test: watch sidebar during long operations)
```

### Resource Usage Tests
```bash
# Monitor resource usage during operation
top -p $(pgrep -f "specify") &
specify /plan large-feature "Complex feature with many components"
# Expected: CPU < 5%, Memory < 100MB
```

## Troubleshooting

### Common Issues

**Issue**: "Terminal too small for task tracking UI"
```bash
# Solution: Increase terminal size or disable sidebar
specify track-tasks disable
# Or resize terminal to at least 100x24
```

**Issue**: "Model switching failed - backup not created"
```bash
# Solution: Check permissions and disk space
ls -la .specify/
df -h .
# Fix permissions if needed:
chmod -R u+w .specify/
```

**Issue**: "Project detection fails in valid project"
```bash
# Solution: Check for corruption and repair
specify detect-project --validate
specify detect-project --repair
```

**Issue**: "Task tracking shows outdated information"
```bash
# Solution: Clear task cache and restart
specify track-tasks clear
specify track-tasks disable
specify track-tasks enable
```

### Getting Help

```bash
# Command-specific help
specify switch-model --help
specify detect-project --help
specify track-tasks --help

# Version and debug info
specify --version
specify --verbose detect-project

# Check logs
cat .specify/logs/latest.log
```

---

**Quickstart Status**: ✅ Complete - Ready for user testing