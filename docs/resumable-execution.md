# Resumable MVP-to-Full Execution Guide

## Overview

The enhanced `mvp-to-full` prompt now supports **resumable execution** to handle token limit interruptions gracefully. This prevents the need to start from scratch when LLM context windows are exhausted.

## Key Features

### 🔍 **State Detection**
- Analyzes each spec folder for artifact completeness
- Detects which specs are incomplete, partially complete, or ready for implementation
- Tracks task progress within each spec's `tasks.md`

### 🚀 **Smart Resumption**
- Never creates duplicate numbered spec folders
- Continues from exact interruption point
- Completes missing artifacts before starting new specs
- Prioritizes incomplete work over new feature creation

### 📋 **Automated Instructions**
- Generates precise resumption commands for new chat windows
- Includes current state analysis and priority actions
- Provides clear context for seamless continuation

## Usage

### When Execution is Interrupted

1. **Generate Resumption Instructions:**
   ```bash
   ./.specify/scripts/bash/generate-resumption-instructions.sh --reason=token_limit
   ```

2. **Copy the Generated Command:**
   The script outputs an exact `/mvp-to-full` command to use in a new chat window.

3. **Start New Chat and Paste:**
   Use the generated command exactly as provided.

### Example Output

```
=== RESUMPTION INSTRUCTIONS ===
Generated: 2025-09-20T19:51:13-03:00
Reason: token_limit

🚀 TO RESUME IN NEW CHAT WINDOW:

1. Copy this EXACT command and paste in new chat:

   /mvp-to-full Resume interrupted execution from 2025-09-20T19:51:13-03:00. Continue implementing tasks in spec: 001-mcp-server-infrastructure.

2. Include this state context:

   Current incomplete specs: 003-server-detection-capabilities 004-server-detection-and 
   Specs in progress: 001-mcp-server-infrastructure 
   Ready for implementation: 002-authentication-system-implement 

3. Priority Action: continue_implementation
   Focus Spec: 001-mcp-server-infrastructure

4. The system will automatically:
   - Detect existing spec folders and their completion status
   - Continue from the exact interruption point
   - Avoid creating duplicate numbered specs
   - Complete missing artifacts before starting new specs
```

## Spec Completion States

The system recognizes these completion states:

- **`fully_complete`**: All artifacts present, all tasks completed
- **`implementation_in_progress`**: All artifacts present, some tasks completed
- **`ready_for_implementation`**: All artifacts present, no tasks started
- **`partially_complete`**: Some artifacts missing, 50%+ complete
- **`incomplete`**: Most artifacts missing, <50% complete

## Required Artifacts

Each spec is considered complete when it has:
- `spec.md` - Feature specification
- `plan.md` - Implementation plan
- `tasks.md` - Task breakdown
- `data-model.md` - Data structures
- `research.md` - Research notes
- `quickstart.md` - Quick start guide
- `contracts/` - API contracts (optional)

## Manual State Analysis

You can manually check spec completion status:

```bash
# Analyze all specs
./.specify/scripts/bash/analyze-spec-completion.sh

# Analyze specific spec
./.specify/scripts/bash/analyze-spec-completion.sh 002-authentication-system-implement

# Get JSON output
./.specify/scripts/bash/analyze-spec-completion.sh --json
```

## Best Practices

### For LLM Assistants
1. **Monitor Token Usage**: When approaching token limits, run the resumption script
2. **Follow Resumption Instructions**: Use the exact command provided
3. **Check State First**: Always run state analysis when resuming
4. **Complete Before Creating**: Finish incomplete specs before starting new ones

### For Users
1. **Save Resumption Commands**: Copy the generated instructions before token exhaustion
2. **New Chat Window**: Start fresh chat session for resumption
3. **Include Context**: Paste the full resumption command with state context
4. **Validate Continuation**: Ensure the assistant detects existing work correctly

## Troubleshooting

### Common Issues

**"Cannot find spec-kit scripts"**
- Ensure scripts are copied to `.specify/scripts/` directory
- Check file permissions (`chmod +x` on script files)

**"Duplicate spec folders created"**
- Assistant didn't detect resumption context
- Ensure you used the exact resumption command generated
- Include full state context in new chat

**"Missing artifacts not detected"**
- Check script output for any error messages
- Verify spec folder structure matches expected format
- Ensure `tasks.md` follows proper checkbox format (`- [ ]` and `- [x]`)

### Debug Commands

```bash
# Check if scripts exist
ls -la .specify/scripts/bash/

# Test state analysis
./.specify/scripts/bash/analyze-spec-completion.sh --json | jq .

# Verify project state
./.specify/scripts/bash/analyze-project-state.sh --json | jq .
```

## Integration with MVP-to-Full

The enhanced `mvp-to-full` prompt automatically:

1. **Detects Resumption**: Checks if arguments contain "Resume interrupted execution"
2. **Analyzes Current State**: Runs spec completion analysis
3. **Prioritizes Work**: Focuses on incomplete specs before creating new ones
4. **Avoids Duplicates**: Never creates numbered folders for existing features
5. **Generates Instructions**: Outputs resumption commands when interrupted

This ensures seamless continuation of multi-spec development workflows regardless of token limit constraints.