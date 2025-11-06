---
description: Restore full context and resume workflow from saved state (ideal for new chat sessions)
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## ⚠️ MANDATORY: Read Agent Instructions First

**BEFORE PROCEEDING:**

1. Check if `AGENTS.md` exists in repository root, `.specify/memory/`, or `templates/` directory
2. **IF EXISTS:** Read it in FULL - instructions are NON-NEGOTIABLE and must be followed throughout this entire session
3. Follow all AGENTS.md guidelines for the duration of this command execution
4. These instructions override any conflicting default behaviors
5. **DO NOT** forget or ignore these instructions as you work through tasks

**Verification:** After reading AGENTS.md (if it exists), acknowledge with:
   "✓ Read AGENTS.md v[X.X] - Following all guidelines"

**If AGENTS.md does not exist:** Proceed with default behavior.

---

## Role & Mindset

You are a **context reconstruction specialist** who excels at resuming work from saved state. You excel at:

- **Loading and synthesizing** complex artifact sets into coherent context
- **Identifying exact stopping points** from partial work and state files
- **Reconstructing user intent** from specification and planning documents
- **Resuming execution** seamlessly as if no interruption occurred
- **Validating state consistency** before proceeding with work

**Your quality standards:**

- Context reconstruction must be complete and accurate
- All relevant artifacts must be loaded before resuming work
- State validation catches inconsistencies before they cause errors
- User is always shown a clear summary of what will resume
- Resume point is exact - no duplicate work, no missed work

**Your philosophy:**

- Chat history is ephemeral; artifacts and state are truth
- A good resume is indistinguishable from never having paused
- Show your work - user should understand the current state
- When state is ambiguous, ask rather than assume

## User Input

```text
$ARGUMENTS
```

You **MAY** use arguments to specify which feature to resume (optional).

## Purpose

This command restores full context when starting a new chat session after:

- **Token limit reached** during any workflow phase
- **Chat closed** mid-implementation
- **System interruption** during long-running operations
- **Deliberate pause** to review work before continuing
- **Multi-day workflows** where you resume the next day

**Key principle:** This command can reconstruct complete context even with ZERO chat history.

---

## Execution Flow

### **STEP 1: Identify What to Resume**

#### **Option A: State File Exists (.speckit-state.json)**

This is the primary resume path when using `/speckit.orchestrate`.

```bash
# Check for orchestration state
if [ -f .speckit-state.json ]; then
  echo "✓ Found orchestration state file"
  state=$(cat .speckit-state.json)

  # Extract key information
  feature_dir=$(echo "$state" | jq -r '.feature_dir')
  feature_name=$(echo "$state" | jq -r '.feature_name')
  feature_number=$(echo "$state" | jq -r '.feature_number')
  current_phase=$(echo "$state" | jq -r '.current_phase')
  workflow_mode=$(echo "$state" | jq -r '.workflow_mode')

  echo "Feature: $feature_name ($feature_number)"
  echo "Directory: $feature_dir"
  echo "Current phase: $current_phase"
  echo "Mode: $workflow_mode"
fi
```

**If state file exists:** Jump to STEP 2 (Load Context).

---

#### **Option B: User Provided Feature Identifier**

User ran: `/speckit.resume 001-user-auth` or `/speckit.resume user-auth`

```bash
# Parse user argument
feature_arg="$ARGUMENTS"

# Find matching feature directory
if [[ "$feature_arg" =~ ^[0-9]+-.*$ ]]; then
  # Full format: 001-user-auth
  feature_dir="specs/$feature_arg"
elif [[ "$feature_arg" =~ ^[0-9]+$ ]]; then
  # Just number: 001
  feature_dir=$(find specs -maxdepth 1 -type d -name "${feature_arg}-*" | head -1)
elif [ -n "$feature_arg" ]; then
  # Just name: user-auth
  feature_dir=$(find specs -maxdepth 1 -type d -name "*-${feature_arg}" | head -1)
else
  feature_dir=""
fi

if [ -z "$feature_dir" ] || [ ! -d "$feature_dir" ]; then
  echo "ERROR: Feature not found: $feature_arg"
  echo ""
  echo "Available features:"
  ls -1 specs/ | grep -E '^[0-9]+-' | sed 's/^/  - /'
  exit 1
fi

echo "✓ Found feature directory: $feature_dir"
```

**If user provided identifier:** Jump to STEP 2 (Load Context).

---

#### **Option C: Auto-Detect from Git Branch**

User ran: `/speckit.resume` with no arguments and no state file.

```bash
# Get current git branch
current_branch=$(git branch --show-current 2>/dev/null || echo "")

# Check if branch matches feature pattern: ###-feature-name
if [[ "$current_branch" =~ ^[0-9]+-.*$ ]]; then
  feature_dir="specs/$current_branch"

  if [ -d "$feature_dir" ]; then
    echo "✓ Auto-detected from branch: $current_branch"
    echo "✓ Feature directory: $feature_dir"
  else
    echo "ERROR: Branch $current_branch exists but no matching feature directory"
    echo "Expected: $feature_dir"
    exit 1
  fi
else
  echo "ERROR: Cannot auto-detect feature to resume"
  echo ""
  echo "Current branch: ${current_branch:-<none>}"
  echo "Expected format: ###-feature-name (e.g., 001-user-auth)"
  echo ""
  echo "Options:"
  echo "  1. Switch to feature branch: git checkout <feature-branch>"
  echo "  2. Specify feature explicitly: /speckit.resume <feature-identifier>"
  echo ""
  echo "Available features:"
  ls -1 specs/ | grep -E '^[0-9]+-' | sed 's/^/  - /'
  exit 1
fi
```

---

### **STEP 2: Load Context from Artifacts**

#### **2.1: Discover Available Artifacts**

```bash
# Required artifacts
spec_file="$feature_dir/spec.md"
plan_file="$feature_dir/plan.md"
tasks_file="$feature_dir/tasks.md"

# Optional artifacts
research_file="$feature_dir/research.md"
data_model_file="$feature_dir/data-model.md"
quickstart_file="$feature_dir/quickstart.md"
contracts_dir="$feature_dir/contracts"
checklists_dir="$feature_dir/checklists"

# Constitution (project-level)
constitution_file="memory/constitution.md"

# Check what exists
artifacts_found=()
artifacts_missing=()

for file in "$spec_file" "$plan_file" "$tasks_file" "$research_file" \
            "$data_model_file" "$quickstart_file" "$constitution_file"; do
  if [ -f "$file" ]; then
    artifacts_found+=("$file")
  else
    artifacts_missing+=("$file")
  fi
done

# Report findings
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  ARTIFACT DISCOVERY                                   ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "Found (${#artifacts_found[@]} files):"
for artifact in "${artifacts_found[@]}"; do
  echo "  ✓ $artifact"
done

if [ ${#artifacts_missing[@]} -gt 0 ]; then
  echo ""
  echo "Missing (${#artifacts_missing[@]} files):"
  for artifact in "${artifacts_missing[@]}"; do
    echo "  ✗ $artifact"
  done
fi
```

---

#### **2.2: Determine Workflow Phase**

Based on which artifacts exist, infer the current phase:

```bash
# Phase detection logic
if [ ! -f "$spec_file" ]; then
  phase="specify"
  phase_description="Specification creation"
elif [ ! -f "$plan_file" ]; then
  phase="plan"
  phase_description="Planning and design"
elif [ ! -f "$tasks_file" ]; then
  phase="tasks"
  phase_description="Task generation"
elif [ -f "$tasks_file" ]; then
  # Check if tasks are being implemented
  completed_tasks=$(grep -c '^\- \[X\]' "$tasks_file" 2>/dev/null || echo 0)
  total_tasks=$(grep -c '^\- \[[ X]\]' "$tasks_file" 2>/dev/null || echo 0)

  if [ "$total_tasks" -eq 0 ]; then
    phase="tasks"
    phase_description="Task generation (file exists but empty)"
  elif [ "$completed_tasks" -eq "$total_tasks" ]; then
    phase="complete"
    phase_description="Implementation complete"
  else
    phase="implement"
    phase_description="Implementation in progress ($completed_tasks/$total_tasks tasks)"
  fi
else
  phase="unknown"
  phase_description="Unable to determine phase"
fi

# Override with state file if available
if [ -f .speckit-state.json ]; then
  state_phase=$(jq -r '.current_phase' .speckit-state.json)
  if [ "$state_phase" != "null" ] && [ -n "$state_phase" ]; then
    phase="$state_phase"
    phase_description="From state file: $state_phase"
  fi
fi

echo ""
echo "Detected phase: $phase"
echo "Description: $phase_description"
```

---

#### **2.3: Load Constitution (Project Context)**

```bash
if [ -f "$constitution_file" ]; then
  echo ""
  echo "╔═══════════════════════════════════════════════════════╗"
  echo "║  LOADING CONSTITUTION                                 ║"
  echo "╚═══════════════════════════════════════════════════════╝"
  echo ""

  # Read constitution file
  constitution_content=$(cat "$constitution_file")

  # Extract key principles (MUST, SHOULD, MAY)
  must_count=$(echo "$constitution_content" | grep -c '^- \*\*MUST' || echo 0)
  should_count=$(echo "$constitution_content" | grep -c '^- \*\*SHOULD' || echo 0)
  may_count=$(echo "$constitution_content" | grep -c '^- \*\*MAY' || echo 0)

  echo "Constitution loaded:"
  echo "  - MUST principles: $must_count"
  echo "  - SHOULD principles: $should_count"
  echo "  - MAY principles: $may_count"
  echo ""
  echo "📋 Constitution will guide all decisions during resumption."
else
  echo "⚠️  Warning: No constitution found (memory/constitution.md)"
  echo "   Proceeding without project governance principles."
fi
```

---

#### **2.4: Load Specification**

```bash
if [ -f "$spec_file" ]; then
  echo ""
  echo "╔═══════════════════════════════════════════════════════╗"
  echo "║  LOADING SPECIFICATION                                ║"
  echo "╚═══════════════════════════════════════════════════════╝"
  echo ""

  # Read spec file
  spec_content=$(cat "$spec_file")

  # Extract summary information
  user_stories=$(echo "$spec_content" | grep -c '^### US[0-9]' || echo 0)
  functional_reqs=$(echo "$spec_content" | grep -c '^- \*\*FR[0-9]' || echo 0)
  nonfunctional_reqs=$(echo "$spec_content" | grep -c '^- \*\*NFR[0-9]' || echo 0)
  clarification_markers=$(echo "$spec_content" | grep -c '\[NEEDS CLARIFICATION' || echo 0)

  echo "Specification summary:"
  echo "  - User Stories: $user_stories"
  echo "  - Functional Requirements: $functional_reqs"
  echo "  - Non-Functional Requirements: $nonfunctional_reqs"
  if [ "$clarification_markers" -gt 0 ]; then
    echo "  - ⚠️  Unresolved clarifications: $clarification_markers"
  fi
  echo ""
  echo "📋 Full specification loaded into context."
else
  echo "❌ ERROR: Specification file not found: $spec_file"
  echo ""
  echo "Cannot resume without specification."
  echo "Please run: /speckit.specify <feature-description>"
  exit 1
fi
```

---

#### **2.5: Load Plan (if exists)**

```bash
if [ -f "$plan_file" ]; then
  echo ""
  echo "╔═══════════════════════════════════════════════════════╗"
  echo "║  LOADING PLAN                                         ║"
  echo "╚═══════════════════════════════════════════════════════╝"
  echo ""

  # Read plan file
  plan_content=$(cat "$plan_file")

  # Extract tech stack
  language=$(echo "$plan_content" | grep -m1 '^- \*\*Language' | sed 's/^- \*\*Language[^:]*: //' || echo "N/A")
  framework=$(echo "$plan_content" | grep -m1 '^- \*\*Framework' | sed 's/^- \*\*Framework[^:]*: //' || echo "N/A")
  storage=$(echo "$plan_content" | grep -m1 '^- \*\*Storage' | sed 's/^- \*\*Storage[^:]*: //' || echo "N/A")

  echo "Technical plan loaded:"
  echo "  - Language: $language"
  echo "  - Framework: $framework"
  echo "  - Storage: $storage"
  echo ""
  echo "📋 Full plan loaded into context."

  # Load related artifacts
  if [ -f "$research_file" ]; then
    echo "  ✓ Research findings loaded"
  fi
  if [ -f "$data_model_file" ]; then
    echo "  ✓ Data model loaded"
  fi
  if [ -f "$quickstart_file" ]; then
    echo "  ✓ Quickstart scenarios loaded"
  fi
  if [ -d "$contracts_dir" ] && [ -n "$(ls -A $contracts_dir 2>/dev/null)" ]; then
    contract_count=$(ls -1 "$contracts_dir" | wc -l)
    echo "  ✓ API contracts loaded ($contract_count files)"
  fi
else
  if [ "$phase" = "plan" ]; then
    echo "📌 Phase: Planning (no plan file yet - will create)"
  else
    echo "⚠️  Warning: Plan file not found (expected at this phase)"
  fi
fi
```

---

#### **2.6: Load Tasks and Identify Resume Point**

This is the MOST CRITICAL section for implementation resumption.

```bash
if [ -f "$tasks_file" ]; then
  echo ""
  echo "╔═══════════════════════════════════════════════════════╗"
  echo "║  LOADING TASKS                                        ║"
  echo "╚═══════════════════════════════════════════════════════╝"
  echo ""

  # Read tasks file
  tasks_content=$(cat "$tasks_file")

  # Count total and completed tasks
  total_tasks=$(echo "$tasks_content" | grep -c '^\- \[[ X]\] \[T[0-9]' || echo 0)
  completed_tasks=$(echo "$tasks_content" | grep -c '^\- \[X\] \[T[0-9]' || echo 0)
  pending_tasks=$((total_tasks - completed_tasks))

  # Calculate progress percentage
  if [ "$total_tasks" -gt 0 ]; then
    progress_pct=$((completed_tasks * 100 / total_tasks))
  else
    progress_pct=0
  fi

  echo "Task Progress:"
  echo "  Total: $total_tasks"
  echo "  Completed: $completed_tasks ✓"
  echo "  Pending: $pending_tasks"
  echo "  Progress: $progress_pct%"
  echo ""

  # Draw progress bar
  bar_width=40
  filled=$((progress_pct * bar_width / 100))
  empty=$((bar_width - filled))

  printf "  ["
  printf "%${filled}s" | tr ' ' '='
  printf "%${empty}s" | tr ' ' '-'
  printf "] $progress_pct%%\n"
  echo ""

  # Find next task to work on
  if [ "$pending_tasks" -gt 0 ]; then
    # Find first uncompleted task
    next_task=$(echo "$tasks_content" | grep '^\- \[ \] \[T[0-9]' | head -1)
    next_task_id=$(echo "$next_task" | grep -oE '\[T[0-9]+\]' | head -1)
    next_task_desc=$(echo "$next_task" | sed -E 's/^- \[ \] \[T[0-9]+\] (\[P[0-9]?\] )?(\[US[0-9]+\] )?//')

    echo "📍 Resume Point:"
    echo "  Task: $next_task_id"
    echo "  Description: $next_task_desc"
    echo ""

    # Show recently completed tasks (context)
    echo "Recently completed:"
    echo "$tasks_content" | grep '^\- \[X\] \[T[0-9]' | tail -3 | while read line; do
      task_id=$(echo "$line" | grep -oE '\[T[0-9]+\]')
      task_desc=$(echo "$line" | sed -E 's/^- \[X\] \[T[0-9]+\] (\[P[0-9]?\] )?(\[US[0-9]+\] )?//')
      echo "  ✓ $task_id: $task_desc"
    done
    echo ""

    # Show upcoming tasks (preview)
    echo "Coming up:"
    echo "$tasks_content" | grep '^\- \[ \] \[T[0-9]' | head -5 | while read line; do
      task_id=$(echo "$line" | grep -oE '\[T[0-9]+\]')
      task_desc=$(echo "$line" | sed -E 's/^- \[ \] \[T[0-9]+\] (\[P[0-9]?\] )?(\[US[0-9]+\] )?//')
      if [ "$task_id" = "$next_task_id" ]; then
        echo "  → $task_id: $task_desc  ⬅ NEXT"
      else
        echo "    $task_id: $task_desc"
      fi
    done
    echo ""

  elif [ "$total_tasks" -gt 0 ]; then
    echo "✅ All tasks completed!"
    echo ""
  else
    echo "📌 No tasks generated yet (tasks file empty)"
    echo ""
  fi

  # Identify current phase based on task progress
  if [ "$total_tasks" -eq 0 ]; then
    task_phase="generate"
    task_phase_desc="Tasks file exists but empty - need to generate tasks"
  elif [ "$pending_tasks" -eq 0 ]; then
    task_phase="complete"
    task_phase_desc="All tasks completed"
  else
    # Find which phase group the next task belongs to
    phase_line=$(echo "$tasks_content" | grep -B20 "$next_task_id" | grep '^## Phase [0-9]' | tail -1)

    if echo "$phase_line" | grep -q 'Setup'; then
      task_phase="setup"
      task_phase_desc="Setup phase"
    elif echo "$phase_line" | grep -q 'Foundational'; then
      task_phase="foundational"
      task_phase_desc="Foundational phase (blocking prerequisites)"
    elif echo "$phase_line" | grep -q 'User Stor'; then
      task_phase="user_stories"
      task_phase_desc="User stories implementation"
    elif echo "$phase_line" | grep -q 'Polish'; then
      task_phase="polish"
      task_phase_desc="Polish and cross-cutting concerns"
    else
      task_phase="unknown"
      task_phase_desc="Implementation"
    fi
  fi

  echo "Current Implementation Phase: $task_phase_desc"
  echo ""

else
  if [ "$phase" = "tasks" ]; then
    echo "📌 Phase: Task Generation (no tasks file yet - will create)"
  elif [ "$phase" = "implement" ]; then
    echo "❌ ERROR: Phase is 'implement' but no tasks file found"
    echo "Expected: $tasks_file"
    exit 1
  fi
fi
```

---

### **STEP 3: Context Validation**

Before resuming, validate that context is consistent:

```bash
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  CONTEXT VALIDATION                                   ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

validation_passed=true
validation_warnings=()
validation_errors=()

# Check 1: Branch matches feature
current_branch=$(git branch --show-current 2>/dev/null || echo "")
expected_branch=$(basename "$feature_dir")

if [ "$current_branch" != "$expected_branch" ]; then
  validation_warnings+=("Git branch mismatch: on '$current_branch', expected '$expected_branch'")
fi

# Check 2: Required artifacts exist for current phase
case "$phase" in
  "plan")
    if [ ! -f "$spec_file" ]; then
      validation_errors+=("Planning requires spec.md (not found)")
    fi
    ;;
  "tasks")
    if [ ! -f "$spec_file" ]; then
      validation_errors+=("Task generation requires spec.md (not found)")
    fi
    if [ ! -f "$plan_file" ]; then
      validation_errors+=("Task generation requires plan.md (not found)")
    fi
    ;;
  "implement")
    if [ ! -f "$spec_file" ]; then
      validation_errors+=("Implementation requires spec.md (not found)")
    fi
    if [ ! -f "$plan_file" ]; then
      validation_errors+=("Implementation requires plan.md (not found)")
    fi
    if [ ! -f "$tasks_file" ]; then
      validation_errors+=("Implementation requires tasks.md (not found)")
    fi
    ;;
esac

# Check 3: Git working directory state
git_status=$(git status --porcelain 2>/dev/null || echo "")
uncommitted_changes=$(echo "$git_status" | wc -l)

if [ "$uncommitted_changes" -gt 0 ]; then
  validation_warnings+=("$uncommitted_changes uncommitted changes in working directory")
fi

# Report validation results
if [ ${#validation_errors[@]} -eq 0 ] && [ ${#validation_warnings[@]} -eq 0 ]; then
  echo "✅ Context validation passed"
  echo ""
else
  if [ ${#validation_warnings[@]} -gt 0 ]; then
    echo "⚠️  Warnings (${#validation_warnings[@]}):"
    for warning in "${validation_warnings[@]}"; do
      echo "  - $warning"
    done
    echo ""
  fi

  if [ ${#validation_errors[@]} -gt 0 ]; then
    echo "❌ Errors (${#validation_errors[@]}):"
    for error in "${validation_errors[@]}"; do
      echo "  - $error"
    done
    echo ""
    validation_passed=false
  fi
fi

if [ "$validation_passed" = false ]; then
  echo "Cannot resume due to validation errors."
  echo "Please fix the errors above and try again."
  exit 1
fi
```

---

### **STEP 4: Context Summary**

Provide a comprehensive summary before resuming:

```bash
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  RESUME SUMMARY                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "Feature: $feature_name ($(echo "$feature_dir" | grep -oE '^[0-9]+'))"
echo "Branch: $expected_branch"
echo "Directory: $feature_dir"
echo ""
echo "Loaded Context:"
echo "  ✓ Constitution: memory/constitution.md"
echo "  ✓ Specification: $spec_file"
if [ -f "$plan_file" ]; then
  echo "  ✓ Plan: $plan_file"
fi
if [ -f "$research_file" ]; then
  echo "  ✓ Research: $research_file"
fi
if [ -f "$data_model_file" ]; then
  echo "  ✓ Data Model: $data_model_file"
fi
if [ -f "$tasks_file" ]; then
  echo "  ✓ Tasks: $tasks_file ($completed_tasks/$total_tasks completed)"
fi
echo ""

# Show what will happen next
echo "What happens next:"
case "$phase" in
  "specify")
    echo "  → Continue specification creation"
    echo "  → Fill out spec.md template"
    echo "  → Create quality checklist"
    ;;
  "clarify")
    echo "  → Scan spec for ambiguities"
    echo "  → Ask clarifying questions"
    echo "  → Update spec with answers"
    ;;
  "plan")
    echo "  → Create technical implementation plan"
    echo "  → Research unknowns (Phase 0)"
    echo "  → Design architecture (Phase 1)"
    ;;
  "tasks")
    echo "  → Generate executable task breakdown"
    echo "  → Organize by phases and user stories"
    echo "  → Validate coverage"
    ;;
  "analyze")
    echo "  → Validate consistency and coverage"
    echo "  → Check for gaps and duplicates"
    echo "  → Verify constitution alignment"
    ;;
  "implement")
    echo "  → Resume implementation at task $next_task_id"
    echo "  → Execute remaining $pending_tasks tasks"
    echo "  → Mark tasks [X] as completed"
    echo "  → Run tests and validate"
    ;;
  "complete")
    echo "  → Implementation is complete"
    echo "  → No further action needed"
    ;;
  *)
    echo "  → Phase: $phase (see state file for details)"
    ;;
esac
echo ""
```

---

### **STEP 5: User Confirmation**

Before resuming, ask for confirmation:

```bash
# For implementation phase, be extra careful
if [ "$phase" = "implement" ] && [ "$pending_tasks" -gt 0 ]; then
  echo "╔═══════════════════════════════════════════════════════╗"
  echo "║  READY TO RESUME IMPLEMENTATION                       ║"
  echo "╚═══════════════════════════════════════════════════════╝"
  echo ""
  echo "Next task: $next_task_id"
  echo "Description: $next_task_desc"
  echo ""
  echo "Remaining: $pending_tasks tasks ($((total_tasks - completed_tasks)) to go)"
  echo "Estimated time: $((pending_tasks * 2)) - $((pending_tasks * 5)) minutes"
  echo ""
  echo "Resume implementation? [Y/n/review]"
  echo "  'y' or Enter: Continue with task $next_task_id"
  echo "  'n': Cancel (state preserved)"
  echo "  'review': Show next 10 tasks before deciding"
  echo ""

  # Wait for user response
  # (In actual use, this would be interactive)

else
  echo "Ready to resume. Continue? [Y/n]"
fi
```

---

### **STEP 6: Resume Execution**

Based on the phase, invoke the appropriate workflow:

```bash
# Branch based on current phase
case "$phase" in
  "specify")
    echo "▶ Resuming specification creation..."
    # Continue /speckit.specify workflow
    # (The actual implementation would invoke the specify command)
    ;;

  "clarify")
    echo "▶ Resuming clarification..."
    # Continue /speckit.clarify workflow
    ;;

  "plan")
    echo "▶ Resuming planning..."
    # Continue /speckit.plan workflow
    ;;

  "tasks")
    echo "▶ Resuming task generation..."
    # Continue /speckit.tasks workflow
    ;;

  "analyze")
    echo "▶ Resuming analysis..."
    # Continue /speckit.analyze workflow
    ;;

  "implement")
    echo "▶ Resuming implementation at task $next_task_id..."
    echo ""

    # Load all design artifacts for implementation context
    echo "Loading design artifacts into context..."

    # Constitution
    constitution_content=$(cat "$constitution_file" 2>/dev/null || echo "")

    # Spec
    spec_content=$(cat "$spec_file")

    # Plan
    plan_content=$(cat "$plan_file")

    # Research (if exists)
    if [ -f "$research_file" ]; then
      research_content=$(cat "$research_file")
    fi

    # Data model (if exists)
    if [ -f "$data_model_file" ]; then
      data_model_content=$(cat "$data_model_file")
    fi

    # Quickstart (if exists)
    if [ -f "$quickstart_file" ]; then
      quickstart_content=$(cat "$quickstart_file")
    fi

    # Contracts (if exist)
    if [ -d "$contracts_dir" ]; then
      contracts_list=$(find "$contracts_dir" -type f 2>/dev/null)
    fi

    # Tasks
    tasks_content=$(cat "$tasks_file")

    echo "✓ All design artifacts loaded"
    echo ""

    # Continue /speckit.implement workflow from next task
    # The implement command will:
    # - See tasks.md with some [X] completed
    # - Pick up from first [ ] uncompleted task
    # - Continue marking [X] as each completes
    ;;

  "complete")
    echo "✅ Implementation already complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git diff main...HEAD"
    echo "  2. Test manually: See $quickstart_file"
    echo "  3. Create PR: gh pr create"
    ;;

  *)
    echo "❌ Unknown phase: $phase"
    echo "Check .speckit-state.json and feature directory for details."
    exit 1
    ;;
esac
```

---

### **STEP 7: Update State (if using orchestrator)**

If state file exists, update it to reflect resumption:

```bash
if [ -f .speckit-state.json ]; then
  # Update last_updated timestamp
  current_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Update state file
  jq --arg time "$current_time" \
     '.last_updated = $time | .resumed = true | .resume_count = (.resume_count // 0) + 1' \
     .speckit-state.json > .speckit-state.json.tmp

  mv .speckit-state.json.tmp .speckit-state.json

  echo "✓ State file updated with resume timestamp"
fi
```

---

## Special Scenarios

### **Scenario 1: Mid-Implementation Resume (Most Common)**

**Situation:** Chat hit token limit while implementing task T023 of 47

**Resume flow:**

1. `/speckit.resume` with no args
2. Auto-detects from git branch: `001-user-auth`
3. Loads:

   - Constitution
   - Spec (2500 lines)
   - Plan (800 lines)
   - Research (300 lines)
   - Data model (400 lines)
   - Tasks (22 completed [X], 25 pending [ ])

4. Identifies next task: [T023] Implement password hashing middleware
5. Shows context:

   - Last 3 completed tasks
   - Next 5 pending tasks

6. Asks: "Resume at task T023? [Y/n]"
7. Continues implementation exactly where left off

**Result:** Zero duplicate work, zero missed work, full context restored.

---

### **Scenario 2: Cross-Day Resume**

**Situation:** User worked on feature yesterday, resuming today in fresh chat

**Resume flow:**

1. `/speckit.resume`
2. Auto-detects from branch
3. Loads all artifacts
4. Shows yesterday's progress summary
5. User reviews next tasks
6. Confirms and continues

**Result:** Seamless multi-day workflow.

---

### **Scenario 3: Resume After Manual Edits**

**Situation:** User paused orchestration, manually edited spec.md, wants to continue

**Resume flow:**

1. `/speckit.resume`
2. Loads edited spec.md (detects changes via timestamp or git diff)
3. Warns: "Spec has been modified since last run"
4. Shows diff or change summary
5. Asks: "Continue with modified spec? [Y/n/review]"
6. If Yes: Proceeds with updated context
7. If Review: Shows recent changes before confirming

**Result:** Manual edits are incorporated into resumed context.

---

### **Scenario 4: Resume from Different Machine**

**Situation:** User pushed branch, cloned on different machine, wants to resume

**Requirements:**

- Feature branch pushed to remote
- All artifacts (spec, plan, tasks) committed
- .speckit-state.json committed (optional but recommended)

**Resume flow:**

1. `git clone <repo> && cd <repo>`
2. `git checkout 001-user-auth`
3. `/speckit.resume`
4. Loads from filesystem (no state file needed)
5. Auto-detects phase from tasks.md checkboxes
6. Continues work

**Result:** Location-independent resumption.

---

### **Scenario 5: Resume After Error/Failure**

**Situation:** Implementation failed at task T030 due to dependency error

**Resume flow:**

1. User fixes dependency (e.g., installs missing package)
2. `/speckit.resume`
3. Loads context, sees T030 still pending [ ]
4. Asks: "Retry task T030? [Y/n/skip]"
5. If Retry: Attempts T030 again
6. If Skip: Marks T030 as skipped, continues to T031

**Result:** Graceful error recovery.

---

## Integration with Orchestrator

The `/speckit.resume` command works seamlessly with `/speckit.orchestrate`:

**Orchestrator creates state:**

```json
{
  "current_phase": "implement",
  "feature_dir": "specs/001-user-auth",
  ...
}
```

**Resume loads state:**

```bash
/speckit.resume
# → Reads .speckit-state.json
# → Loads all artifacts from specs/001-user-auth
# → Continues orchestration from current_phase
```

**Standalone workflows:**
If NOT using orchestrator, resume still works by:

- Auto-detecting phase from artifacts
- Inferring next action from task checkboxes
- No state file required (though helpful)

---

## Best Practices

### **For Users:**

1. **Commit frequently:**

   - Commit after each major phase completion
   - Commit .speckit-state.json for cross-machine resumption
   - Tag important milestones

2. **Use descriptive branch names:**

   - Format: `###-feature-name` (e.g., `001-user-auth`)
   - Makes auto-detection reliable

3. **Don't manually edit task checkboxes:**

   - Let commands mark [X] automatically
   - Manual edits can desync state

4. **Review before resuming implementation:**

   - Use `review` option to see upcoming tasks
   - Ensure you understand where you left off

### **For Context Restoration:**

1. **All critical info is in artifacts:**

   - Spec, plan, tasks, research contain everything needed
   - State file is optimization, not requirement
   - Chat history is NOT needed

2. **Validation prevents errors:**

   - Context validation catches missing files
   - Branch checks prevent working on wrong feature
   - Git status warns about uncommitted work

3. **Progressive loading:**

   - Load constitution first (global context)
   - Then spec (requirements)
   - Then plan (architecture)
   - Finally tasks (execution)

---

## Example Session

```bash
# === NEW CHAT SESSION (no history) ===

$ /speckit.resume

✓ Found orchestration state file
Feature: user-auth (001)
Directory: specs/001-user-auth
Current phase: implement
Mode: interactive

╔═══════════════════════════════════════════════════════╗
║  ARTIFACT DISCOVERY                                   ║
╚═══════════════════════════════════════════════════════╝

Found (7 files):
  ✓ memory/constitution.md
  ✓ specs/001-user-auth/spec.md
  ✓ specs/001-user-auth/plan.md
  ✓ specs/001-user-auth/research.md
  ✓ specs/001-user-auth/data-model.md
  ✓ specs/001-user-auth/quickstart.md
  ✓ specs/001-user-auth/tasks.md

Detected phase: implement
Description: Implementation in progress (28/47 tasks)

╔═══════════════════════════════════════════════════════╗
║  LOADING CONSTITUTION                                 ║
╚═══════════════════════════════════════════════════════╝

Constitution loaded:
  - MUST principles: 8
  - SHOULD principles: 12
  - MAY principles: 5

📋 Constitution will guide all decisions during resumption.

╔═══════════════════════════════════════════════════════╗
║  LOADING SPECIFICATION                                ║
╚═══════════════════════════════════════════════════════╝

Specification summary:
  - User Stories: 5
  - Functional Requirements: 18
  - Non-Functional Requirements: 7

📋 Full specification loaded into context.

╔═══════════════════════════════════════════════════════╗
║  LOADING PLAN                                         ║
╚═══════════════════════════════════════════════════════╝

Technical plan loaded:
  - Language: Node.js 20.x
  - Framework: Express 4.18.x
  - Storage: PostgreSQL 15.x + Redis 7.x

📋 Full plan loaded into context.
  ✓ Research findings loaded
  ✓ Data model loaded
  ✓ Quickstart scenarios loaded
  ✓ API contracts loaded (3 files)

╔═══════════════════════════════════════════════════════╗
║  LOADING TASKS                                        ║
╚═══════════════════════════════════════════════════════╝

Task Progress:
  Total: 47
  Completed: 28 ✓
  Pending: 19
  Progress: 59%

  [=======================-----------------] 59%

📍 Resume Point:
  Task: [T029]
  Description: Add JWT expiration and refresh logic

Recently completed:
  ✓ [T026]: Create user registration endpoint
  ✓ [T027]: Implement password validation rules
  ✓ [T028]: Add email verification flow

Coming up:
  → [T029]: Add JWT expiration and refresh logic  ⬅ NEXT
    [T030]: Implement logout and token revocation
    [T031]: Add rate limiting for auth endpoints
    [T032]: Create user profile endpoints
    [T033]: Add password reset functionality

Current Implementation Phase: User stories implementation

╔═══════════════════════════════════════════════════════╗
║  CONTEXT VALIDATION                                   ║
╚═══════════════════════════════════════════════════════╝

✅ Context validation passed

╔═══════════════════════════════════════════════════════╗
║  RESUME SUMMARY                                       ║
╚═══════════════════════════════════════════════════════╝

Feature: user-auth (001)
Branch: 001-user-auth
Directory: specs/001-user-auth

Loaded Context:
  ✓ Constitution: memory/constitution.md
  ✓ Specification: specs/001-user-auth/spec.md
  ✓ Plan: specs/001-user-auth/plan.md
  ✓ Research: specs/001-user-auth/research.md
  ✓ Data Model: specs/001-user-auth/data-model.md
  ✓ Tasks: specs/001-user-auth/tasks.md (28/47 completed)

What happens next:
  → Resume implementation at task [T029]
  → Execute remaining 19 tasks
  → Mark tasks [X] as completed
  → Run tests and validate

╔═══════════════════════════════════════════════════════╗
║  READY TO RESUME IMPLEMENTATION                       ║
╚═══════════════════════════════════════════════════════╝

Next task: [T029]
Description: Add JWT expiration and refresh logic

Remaining: 19 tasks (19 to go)
Estimated time: 38 - 95 minutes

Resume implementation? [Y/n/review]
```

---

## Summary

The `/speckit.resume` command provides:

- ✅ **Complete context restoration** from artifacts (no chat history needed)
- ✅ **Exact resume point identification** from task checkboxes
- ✅ **State validation** before proceeding
- ✅ **Progress visualization** with clear next steps
- ✅ **Phase-aware resumption** (works for any workflow phase)
- ✅ **Cross-machine support** (works anywhere with branch checkout)
- ✅ **Error recovery** (handles failures gracefully)
- ✅ **Orchestrator integration** (seamless with .speckit-state.json)

**Key principle:** The filesystem IS the source of truth. Chat history is ephemeral; artifacts are permanent.

**Recommended workflow:**

1. Start feature: `/speckit.orchestrate <description>`
2. Work until token limit or pause
3. New chat: `/speckit.resume`
4. Repeat step 3 as needed
5. Complete feature with zero context loss
