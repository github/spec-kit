---
description: Display current token usage estimation and budget recommendations for the session
scripts:
  sh: scripts/bash/token-budget.sh --json
  ps: scripts/powershell/token-budget.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Provide real-time visibility into estimated token consumption during the current session. Help users make informed decisions about when to use token optimization strategies like `/speckit.prune`, incremental analysis, or summary modes.

## Operating Constraints

- **Read-only**: Does not modify any files
- **Estimation-based**: Token counts are approximations based on file sizes and heuristics
- **Session-aware**: Tracks cumulative usage in current conversation
- **Actionable**: Provides specific recommendations based on usage patterns

## Execution Steps

### 1. Run Token Budget Script

Execute `{SCRIPT}` from repo root and parse JSON output:

```bash
# Example: scripts/bash/token-budget.sh --json
```

Expected JSON structure:
```json
{
  "session_tokens": 45000,
  "total_budget": 200000,
  "remaining_tokens": 155000,
  "usage_percentage": 22.5,
  "breakdown": {
    "conversation": 34000,
    "specs": {
      "001-feature-a": 8500,
      "002-feature-b": 2500
    },
    "constitution": 2100,
    "plans": 5400,
    "code_context": 12000
  },
  "recommendations": [
    "You have sufficient budget for planning and implementation",
    "Consider using /speckit.prune if session exceeds 80K tokens"
  ],
  "status": "healthy"
}
```

### 2. Display Token Budget Status

Present the information in a clear, formatted output:

```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~45K tokens used
Remaining: ~155K tokens (77% available)

Breakdown:
  Conversation: 34.0K
  Specifications: 11.0K
    • 001-feature-a: 8.5K
    • 002-feature-b: 2.5K
  Constitution: 2.1K
  Plans: 5.4K
  Code context: 12.0K

Status: ✓ Healthy
```

### 3. Provide Context-Aware Recommendations

Based on token usage percentage, provide actionable advice:

**< 40% usage (0-80K tokens)**:
```
💡 Recommendations:
  • You have plenty of budget remaining
  • Safe to proceed with planning and implementation
  • No optimization needed at this stage
```

**40-60% usage (80K-120K tokens)**:
```
💡 Recommendations:
  • Moderate token usage detected
  • Consider these optimizations for long tasks:
    - Use quick-ref.md instead of full ai-doc.md (saves ~2K per feature)
    - Use /speckit.analyze --summary for quick checks (90% faster)
  • Continue monitoring usage
```

**60-80% usage (120K-160K tokens)**:
```
⚠️  Recommendations:
  • High token usage - optimization recommended
  • Before long operations:
    - Run /speckit.prune to compress session (saves 40-60K tokens)
    - Use /speckit.analyze --incremental (70-90% faster)
    - Load only essential specs/docs
  • Budget may be tight for implementation
```

**> 80% usage (160K+ tokens)**:
```
🚨 Recommendations:
  • Critical: Token budget nearly exhausted
  • IMMEDIATE ACTIONS:
    - Run /speckit.prune NOW to free up space
    - Use summary modes for all analysis
    - Consider starting fresh session for implementation
  • Estimated remaining capacity: 1-2 major operations
```

### 4. Show Optimization Opportunities

If applicable, list specific optimization commands:

```
🔧 Optimization Options:
  /speckit.prune              - Compress session (save ~40-50K tokens)
  /speckit.analyze --summary  - Quick analysis (90% faster)
  /speckit.analyze --incremental - Smart analysis (70% faster)

  Load quick refs:
    cat specs/001-feature/quick-ref.md (200 tokens vs 2.4K)
```

### 5. Track Historical Patterns (Optional Enhancement)

If the script provides historical data:

```
📊 Session History:
  Previous operations:
    • /speckit.specify: ~8K tokens
    • /speckit.plan: ~12K tokens
    • /speckit.tasks: ~6K tokens

  Estimated for next operations:
    • /speckit.implement: ~60-80K tokens
    • /speckit.analyze: ~15-25K tokens (full) or ~2K (incremental)
```

## Token Estimation Heuristics

The budget script uses these estimation methods:

### File-Based Estimation
```
Tokens ≈ (Characters / 4) × 1.2

Adjustments:
  - Markdown files: ×1.1 (formatting overhead)
  - Code files: ×1.0 (actual content)
  - JSON files: ×0.9 (structured, compressed)
  - Binary files: Excluded
```

### Context Estimation
```
Conversation history: Sum of all previous messages
Specifications: File size × weight
  - spec.md: ×1.0 (full weight)
  - plan.md: ×0.9 (often referenced partially)
  - tasks.md: ×0.8 (scanned, not read fully)
  - ai-doc.md: ×1.0 (full when loaded)
  - quick-ref.md: ×1.0 (lightweight but fully loaded)
Constitution: File size × 1.0 (always fully loaded)
```

### Session Budget
```
Default budget: 200,000 tokens (Claude Sonnet)
Safe operating range: 0-160K tokens (80%)
Warning threshold: 160K+ tokens
Critical threshold: 180K+ tokens
```

## Command Variations

### Basic Usage
```bash
/speckit.budget
```
Shows current token usage and recommendations.

### With Historical Comparison (Future)
```bash
/speckit.budget --history
```
Shows usage trends across multiple sessions.

### Export Budget Report (Future)
```bash
/speckit.budget --export
```
Saves budget report to `.speckit/budget-report.txt`.

## Integration with Other Commands

### Before Planning
```bash
# Check budget before creating plan
/speckit.budget
# If budget is healthy, proceed
/speckit.plan
```

### Before Implementation
```bash
# Check if enough budget for implementation
/speckit.budget
# If usage > 60%, prune first
/speckit.prune
/speckit.implement
```

### During Long Sessions
```bash
# Periodic budget checks
/speckit.budget
# ... work on features ...
/speckit.budget  # Check again
```

## Output Format Examples

### Healthy Session
```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~32K tokens used
Remaining: ~168K tokens (84% available)

Breakdown:
  Conversation: 24.0K
  Specifications: 6.0K
  Constitution: 2.0K

Status: ✓ Healthy

💡 Tip: You have plenty of budget for planning and implementation
```

### Moderate Usage
```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~95K tokens used
Remaining: ~105K tokens (52% available)

Breakdown:
  Conversation: 58.0K
  Specifications: 24.0K
  Code context: 13.0K

Status: ⚠️  Moderate

💡 Recommendations:
  • Consider /speckit.prune before long operations
  • Use quick-ref.md for feature lookups
  • Budget should support 1-2 more features
```

### Critical Usage
```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~178K tokens used
Remaining: ~22K tokens (11% available)

Breakdown:
  Conversation: 102.0K
  Specifications: 45.0K
  Code context: 31.0K

Status: 🚨 CRITICAL

⚠️  IMMEDIATE ACTIONS REQUIRED:
  1. Run /speckit.prune to free up ~40-50K tokens
  2. Use summary modes for analysis
  3. Consider starting fresh session for implementation

Estimated capacity: Only 1 small operation remaining
```

## Best Practices

### Proactive Monitoring
- Check budget before major operations (plan, implement, analyze)
- Run `/speckit.budget` every 50-60K tokens during long sessions
- Set up periodic reminders for budget checks

### Optimization Strategy
1. **0-80K tokens**: Normal operation
2. **80K-120K tokens**: Start using quick refs and incremental modes
3. **120K-160K tokens**: Prune session, use summary modes
4. **160K+ tokens**: Critical - prune immediately or start new session

### Prevention
- Use quick-ref.md by default for feature lookups
- Enable incremental analysis after first full analysis
- Prune proactively at 100K tokens, don't wait for critical state
- Close exploration threads that are no longer relevant

## Limitations

### Current Limitations
1. **Estimation accuracy**: ±15-20% variance from actual token usage
2. **No real-time tracking**: Estimates based on files, not actual LLM context
3. **Conversation overhead**: Cannot precisely track conversation compression
4. **No historical persistence**: Budget resets each session

### Future Enhancements
- Integration with LLM token counters for precise tracking
- Historical trend analysis across sessions
- Automatic pruning triggers at thresholds
- Budget alerts during commands (e.g., "Planning will use ~12K tokens, proceed?")

## Error Handling

### No Specs Found
```
Token Budget Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ~15K tokens used (conversation only)
Remaining: ~185K tokens

⚠️  Note: No specifications found in project
Run /speckit.specify to create your first feature
```

### Script Error
```
⚠️  Unable to calculate precise token budget
   Using simplified estimation based on conversation length

Estimated usage: ~50K tokens
Remaining: ~150K tokens

Recommendation: Budget tracking unavailable, proceed with caution
```

## Context

{ARGS}
