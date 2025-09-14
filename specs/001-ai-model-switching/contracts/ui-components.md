# UI Components Contract

**Feature**: AI Model Switching and Task Tracking UI
**Version**: 1.0.0
**Created**: 2025-09-13

## Terminal UI Component Specifications

### TaskTrackingSidebar
**Purpose**: Real-time task status display in CLI sidebar

**Dimensions**:
- Width: 30% of terminal width (minimum 40 columns)
- Height: Full terminal height
- Position: Right side of terminal

**Layout**:
```
┌─ Task Progress ────────────────┐
│ Session: plan (14/16 tasks)    │
│                                │
│ ✓ [001] Initialize project     │
│ ✓ [002] Load configuration     │
│ ⚠ [003] Validate dependencies  │
│ ✗ [004] Setup database         │
│ ⏳[005] Generate contracts     │
│ □ [006] Create tests           │
│                                │
│ Failed Tasks (1):              │
│ • Setup database               │
│   Error: Connection timeout    │
│                                │
│ Active: Generating contracts   │
│ Progress: ████████░░ 80%       │
└────────────────────────────────┘
```

**Status Icons**:
- ✓ Completed (green)
- ✗ Failed (red)
- ⚠ Warning (yellow)
- ⏳ Running (blue)
- □ Pending (gray)

**Update Frequency**: Real-time (immediate on status change)

**Data Binding**:
- Source: TaskState entity from task-state.json
- Updates: Event-driven from task status changes
- Refresh: Every 100ms for active tasks

### ModelSwitchDialog
**Purpose**: Interactive AI model selection and migration UI

**Dimensions**:
- Width: 60 columns
- Height: 20 rows
- Position: Centered in terminal

**Layout**:
```
┌─ Switch AI Model ──────────────────────────────────────┐
│                                                        │
│ Current Model: Claude 3.5 Sonnet                      │
│                                                        │
│ Available Models:                                      │
│ ○ Claude 3.5 Sonnet (current)                        │
│ ● Gemini Pro                                          │
│ ○ GPT-4 Turbo                                         │
│                                                        │
│ Migration Options:                                     │
│ ☑ Create backup before switching                      │
│ ☑ Validate compatibility                              │
│ ☐ Keep existing configurations                        │
│                                                        │
│ Estimated time: 30 seconds                            │
│                                                        │
│            [Switch] [Cancel]                           │
└────────────────────────────────────────────────────────┘
```

**Controls**:
- Arrow keys: Navigate model selection
- Space: Toggle options
- Enter: Confirm switch
- Escape: Cancel dialog
- Tab: Navigate between sections

### ProgressIndicator
**Purpose**: Show progress for long-running operations

**Types**:

**1. Linear Progress Bar**:
```
Switching AI Model...
████████████████████████████████░░░░░░░░ 80% (24s remaining)
Step 3/4: Migrating configuration files...
```

**2. Spinner with Steps**:
```
⠋ Switching AI Model...
  ✓ Creating backup
  ✓ Validating compatibility
  ⠋ Migrating configurations
  □ Updating project files
```

**3. Task List Progress**:
```
Migration Progress:
├─ ✓ Backup original config (2s)
├─ ✓ Validate model compatibility (1s)
├─ ⠋ Convert configuration format (15s)
└─ □ Update project metadata
```

### ProjectDetectionPanel
**Purpose**: Show project detection and validation results

**Layout**:
```
┌─ Project Detection ────────────────────────────────────┐
│                                                        │
│ Status: ✓ Valid Spec-Kit Project                      │
│                                                        │
│ Project Details:                                       │
│ • Name: My Awesome Project                            │
│ • Version: 2.1.0                                      │
│ • AI Model: Claude 3.5 Sonnet                        │
│ • Features: 12 specifications                         │
│ • Created: 2025-09-01                                 │
│                                                        │
│ Health Check:                                          │
│ ✓ Configuration files present                         │
│ ✓ Project structure valid                             │
│ ⚠ 2 deprecated settings found                         │
│                                                        │
│                    [Repair] [Continue]                 │
└────────────────────────────────────────────────────────┘
```

### ErrorDisplayPanel
**Purpose**: User-friendly error presentation with recovery options

**Layout**:
```
┌─ Error ────────────────────────────────────────────────┐
│                                                        │
│ ✗ Migration Failed                                     │
│                                                        │
│ Error: Configuration file corrupted                    │
│                                                        │
│ Details:                                               │
│ • File: .specify/config/ai-model.json                │
│ • Issue: Invalid JSON syntax at line 15              │
│ • Backup: Available (.specify/backups/2025-09-13/)   │
│                                                        │
│ Recovery Options:                                      │
│ 1. Restore from backup                                │
│ 2. Reset configuration                                │
│ 3. Manual repair                                      │
│                                                        │
│         [Restore] [Reset] [Cancel]                     │
└────────────────────────────────────────────────────────┘
```

## Component Interactions

### Event Flow
```
User Command → CLI Parser → UI Component → Data Update → UI Refresh
```

### State Management
- Components read from JSON state files
- Updates trigger component re-renders
- Debounced updates for high-frequency changes
- Error boundaries prevent UI crashes

### Layout Responsiveness

**Terminal Size Handling**:
- Minimum width: 100 columns
- Minimum height: 24 rows
- Graceful degradation for smaller terminals
- Responsive sidebar width (20%-40% of terminal)

**Small Terminal Fallback**:
```
Terminal too small for sidebar UI.
Falling back to text-only mode.

Tasks: 14/16 completed, 1 failed, 1 active
Active: Generating contracts (80% complete)
Failed: Setup database (Connection timeout)
```

## Accessibility

### Keyboard Navigation
- Tab/Shift+Tab: Navigate between elements
- Arrow keys: Navigate lists and menus
- Enter: Confirm actions
- Escape: Cancel/go back
- Space: Toggle checkboxes/radio buttons

### Visual Accessibility
- High contrast colors for readability
- Support for terminal color limitations
- Alternative text representations for icons
- Clear visual hierarchy

### Screen Reader Support
- Structured content for screen readers
- Descriptive labels for all interactive elements
- Status announcements for dynamic updates

## Performance Requirements

### Update Frequency
- Task status: Real-time (< 100ms delay)
- Progress indicators: 10 updates per second maximum
- Terminal resize: Immediate layout adjustment
- File system changes: < 500ms detection

### Memory Usage
- Maximum 10MB for UI components
- Efficient terminal buffer management
- Cleanup of inactive components
- Garbage collection of old state

### CPU Usage
- < 1% CPU during idle display
- < 5% CPU during active updates
- Efficient redraw algorithms
- Batch updates for multiple changes

---

**UI Contract Status**: ✅ Complete - All components and interactions specified