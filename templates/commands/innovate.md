---
description: Brainstorm innovative ideas and solutions using parallel subagent discussions.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

This command facilitates creative brainstorming by spawning multiple independent expert perspectives that discuss and debate ideas in parallel. The goal is to generate diverse, innovative solutions by exploring different viewpoints simultaneously.

**Key Features:**

- 🎭 Dynamic multi-role system (2-4 experts based on topic)
- 🌍 Cross-domain inspiration from unrelated fields
- ⚔️ Structured challenge-rebuttal debates
- 👥 User impact analysis from multiple stakeholder perspectives
- 🎚️ Flexible modes: Quick, Standard, or Deep brainstorming

## Execution Flow

### 0. Select Brainstorming Mode

Determine the appropriate mode based on topic complexity and available time:

**Mode Selection Logic:**

1. Analyze user input length and complexity
2. Check for explicit mode request (e.g., "--quick", "--deep")
3. Recommend mode, allow user override

**Available Modes:**

| Mode | Duration | Rounds | Depth | Best For |
|------|----------|--------|-------|----------|
| **Quick** ⚡ | 15-20 min | 2 rounds | Shallow | Rapid ideation, simple topics, time-constrained |
| **Standard** ⚖️ | 30-45 min | 3 rounds | Medium | Most topics, balanced exploration (DEFAULT) |
| **Deep** 🔬 | 60+ min | 4-5 rounds | Deep | Complex topics, critical decisions, high stakes |

**Mode Configurations:**

**Quick Mode** ⚡:

- Round 0: Cross-domain inspiration (optional, can skip)
- Round 1: Initial ideas (3 per agent, brief)
- Round 2: Quick critique + 2 hybrid ideas
- Output: Top 3 recommendations with minimal analysis

**Standard Mode** ⚖️ (Current default):

- Round 0: Cross-domain inspiration
- Round 1: Initial ideas (3-5 per agent)
- Round 2: Challenge-rebuttal + hybrid formation
- Round 3: Full synthesis + user impact matrix
- Output: Comprehensive report

**Deep Mode** 🔬:

- Round 0: Cross-domain inspiration + competitive analysis
- Round 1: Initial ideas (5-7 per agent)
- Round 2: Challenge-rebuttal + hybrid formation
- Round 3: Synthesis + user impact matrix
- Round 4: Risk analysis + failure modes
- Round 5: Implementation roadmap + validation plan
- Output: Executive report with detailed analysis

**Mode Selection Output:**

```markdown
## Brainstorming Session Configuration

**Topic**: [User's topic]
**Selected Mode**: [Quick/Standard/Deep] [emoji]
**Estimated Duration**: [timeframe]
**Rounds**: [number]
**Rationale**: [Why this mode was selected/recommended]

[If not default] User can override by saying "use [mode] mode" or "switch to [mode]"
```

### 1. Initialize Context

Extract the brainstorming topic from user input:

- If `$ARGUMENTS` is empty, ask user: "What topic would you like to brainstorm about?"
- Parse the topic to understand:
  - Problem domain
  - Desired outcome
  - Any constraints or context provided

### 1.5. Cross-Domain Inspiration (Round 0)

Before diving into solutions, activate creative thinking through cross-domain analogies:

1. **Identify 3 unrelated domains** that have solved similar challenges:
   - Use pattern matching: "optimization" → manufacturing, biology, economics
   - Use abstraction: "collaboration" → orchestras, sports teams, ecosystems
   - Use transformation: "security" → castles, immune systems, cryptography

2. **Brief description** (2-3 sentences each):
   - Domain name
   - How they approach similar problems
   - Key insight or pattern

3. **Mandate inspiration**: Each agent must reference at least ONE cross-domain insight in their Round 1 ideas

**Example Output:**

```markdown
## Round 0: Cross-Domain Inspiration

**Topic**: Improve code review process

**Analogous Domains:**

1. **Medical Diagnosis** - Doctors use checklists, peer consultation, and differential diagnosis
   - Key insight: Multiple review passes catch different types of issues

2. **Restaurant Quality Control** - Chefs taste dishes, sous chefs inspect, customers provide feedback
   - Key insight: Different stakeholders have different quality standards

3. **Academic Peer Review** - Anonymous reviewers, revision rounds, editor oversight
   - Key insight: Blind review reduces bias, revision cycles improve quality
```

### 2. Determine Agent Roles (Dynamic Multi-Role System)

Instead of fixed 2-agent system, dynamically configure 2-4 expert roles based on the topic:

1. **Load role configuration** from `.specify/memory/agent-roles.yaml`

2. **Match topic to category** using keyword detection:
   - Extract keywords from user input
   - Find best matching category from config
   - If no strong match, use default roles (Optimizer + Innovator)

3. **Select optimal roles** (2-4 roles):
   - If category found: use its predefined roles
   - Limit to 4 roles maximum to avoid discussion fragmentation
   - Minimum 2 roles for diverse perspectives

4. **Role assignment output**:

   ```markdown
   ## Assigned Expert Roles
   
   Based on topic analysis, the following experts will participate:
   
   **Role 1: [Name]**
   - Focus: [key areas]
   - Approach: [methodology]
   - Key Questions: [questions they ask]
   
   **Role 2: [Name]**
   - Focus: [key areas]
   - Approach: [methodology]
   - Key Questions: [questions they ask]
   
   [... additional roles if 3-4 selected]
   ```

**Examples:**

- Topic: "Improve our authentication system"
  - Matched category: `authentication`
  - Roles: Security Expert, UX Designer, Compliance Officer

- Topic: "Optimize database query performance"
  - Matched category: `performance`
  - Roles: Performance Engineer, Cost Analyst, Infrastructure Architect

- Topic: "Design a new reporting dashboard"
  - Matched category: `feature_design`
  - Roles: Product Manager, Developer, End User Advocate

- Topic: "How to make better coffee" (no tech match)
  - Matched category: `default`
  - Roles: The Optimizer, The Innovator

### 3. Parallel Discussion Rounds

Execute 3 rounds of parallel thinking, where ALL assigned agents respond simultaneously:

#### Round 1: Initial Ideas Generation (5 minutes thinking time per agent)

- **Each agent's task**: From their unique perspective, propose 3-5 ideas
- **Mandate**: Must reference at least ONE cross-domain insight from Round 0
- **Format**: Structured with reasoning, pros/cons, and feasibility assessment

**Output Format for Round 1:**

```markdown
## Round 1: Initial Ideas

### [Role 1 Name]'s Perspective

**Inspired by**: [Which cross-domain insight influenced this thinking]

1. [Idea 1 title]
   - Why: [reasoning]
   - Pros: [benefits]
   - Cons: [limitations]
   - Feasibility: [Low/Medium/High]

2. [Idea 2 title]
   ...

### [Role 2 Name]'s Perspective

**Inspired by**: [Which cross-domain insight influenced this thinking]

1. [Idea 1 title]
   - Why: [reasoning]
   - Pros: [benefits]
   - Cons: [limitations]
   - Feasibility: [Low/Medium/High]

[... additional roles if 3-4 assigned]
```

#### Round 2: Challenge-Rebuttal & Cross-Pollination

This round introduces structured debate to stress-test ideas:

**Phase 2A: Constructive Challenges (Each agent challenges another)**

- Each agent selects ONE idea from a different agent to challenge
- Challenge must be specific and constructive (not just "I disagree")
- Focus on hidden assumptions, edge cases, or overlooked constraints

**Phase 2B: Rebuttals & Improvements**

- Original proposer responds to challenge
- Options: Refute, Acknowledge & Improve, or Pivot to new approach
- Both parties collaborate to strengthen the idea

**Phase 2C: Hybrid Formation**

- Agents identify synergies between their ideas
- Propose 2-3 hybrid approaches combining best elements
- Cross-pollinate: practical + innovative elements

**Output Format for Round 2:**

```markdown
## Round 2: Challenge-Rebuttal & Cross-Pollination

### Phase A: Constructive Challenges

**[Role 1] challenges [Role 2]'s Idea [X]:**
- **Challenge**: [Specific concern or overlooked issue]
- **Why this matters**: [Impact if not addressed]

**[Role 2] challenges [Role 3]'s Idea [Y]:**
- **Challenge**: [Specific concern]
- **Why this matters**: [Impact]

[Continue pattern for all roles - each challenges exactly one other role]

### Phase B: Rebuttals & Improvements

**[Role 2] responds to challenge on Idea [X]:**
- **Response**: [Refutation or acknowledgment]
- **Improvement**: [How the idea evolves to address the challenge]
- **New version**: [Updated idea if significantly changed]

[Continue for all challenged ideas]

### Phase C: Hybrid Ideas

**Hybrid 1: [Descriptive Name]**
- **Combines**: [Role X's Idea A] + [Role Y's Idea B]
- **Synthesis**: [How they complement each other]
- **Unique value**: [What's gained by combining]

**Hybrid 2: [Descriptive Name]**
- **Combines**: [Ideas and roles]
- **Synthesis**: [Integration approach]
- **Unique value**: [Combined benefits]

[2-3 hybrid ideas total]
```

#### Round 3: Synthesis & Recommendation

- **All agents collaborate**: Rank top 3-5 combined/hybrid ideas
- **Multi-criteria evaluation**: Each agent scores from their perspective
- **User impact analysis**: Evaluate from multiple stakeholder viewpoints
- **Consensus building**: Identify which ideas have broad support vs. niche appeal

**Output Format for Round 3:**

```markdown
## Round 3: Synthesis

### Multi-Agent Evaluation Matrix

| Idea | [Role 1] Score | [Role 2] Score | [Role 3] Score | Consensus |
|------|---------------|---------------|---------------|-----------|
| Hybrid Idea 1 | 8/10 | 9/10 | 7/10 | Strong ⭐⭐⭐ |
| Original Idea from Role 2 | 9/10 | 6/10 | 8/10 | Moderate ⭐⭐ |
| Hybrid Idea 2 | 7/10 | 8/10 | 9/10 | Strong ⭐⭐⭐ |

**Scoring criteria per role:**
- [Role 1]: [Their specific evaluation criteria]
- [Role 2]: [Their specific evaluation criteria]  
- [Role 3]: [Their specific evaluation criteria]

### Top 3 Consensus Recommendations

#### Recommendation 1: [Idea Name] ⭐⭐⭐

- **What it is**: [Clear description]
- **Why it's strong**: [Multi-perspective strengths]
- **Implementation complexity**: [Low/Medium/High]
- **Time to value**: [Timeframe estimate]
- **Innovation score**: [1-10]
- **Key risks**: [What could go wrong]

#### Recommendation 2: [Idea Name] ⭐⭐⭐

[Same structure]

#### Recommendation 3: [Idea Name] ⭐⭐

[Same structure]

### User Impact Matrix

Evaluate the top 3 consensus ideas from different stakeholder perspectives:

| Solution | Novice Users 👶 | Power Users 💪 | Administrators 👨‍💼 | Overall Sentiment |
|----------|----------------|----------------|---------------------|-------------------|
| Idea 1   | 😊 [reason]    | 😐 [reason]    | 😊 [reason]         | Positive          |
| Idea 2   | 😐 [reason]    | 😊 [reason]    | 😊 [reason]         | Very Positive     |
| Idea 3   | 😊 [reason]    | 😊 [reason]    | 😐 [reason]         | Positive          |

**Legend**: 😊 Positive | 😐 Neutral/Mixed | 😟 Negative concern

**Key Insights:**
- Which user group benefits most from each solution?
- Are there any "lose-lose" scenarios where multiple groups suffer?
- Can we adjust any solution to improve stakeholder alignment?
```

### 4. Convergence & Final Output

After 3 rounds, synthesize findings into a unified brainstorm report:

```markdown
## Brainstorming Report: [Topic]

**Date**: [YYYY-MM-DD]
**Duration**: 3 rounds of parallel discussion

### Top Recommended Ideas (Consensus)

#### Idea 1: [Best Combined Approach]

- **Description**: [Clear explanation]
- **Practical Strengths**: [From Optimizer]
- **Innovation Strengths**: [From Innovator]
- **Implementation Path**: [High-level steps]
- **Unique Value**: [Differentiation]
- **Risk Assessment**: [Key considerations]

#### Idea 2: [Second Best Approach]

[Same structure as above]

#### Idea 3: [Third Best Approach]

[Same structure as above]

### Alternative Approaches Worth Exploring

- [Other notable ideas from discussion]

### Key Insights & Patterns

- [Common themes across both perspectives]
- [Surprising synergies discovered]
- [Assumptions challenged successfully]

### Next Steps

1. [Immediate action items]
2. [Further research needed]
3. [Prototype/validation suggestions]
```

### 5. Save Output & Session Management

**Session Persistence:**

All brainstorming sessions are automatically saved with incremental checkpoints for resumability.

**Directory Structure:**

```
.specify/brainstorms/
├── sessions/
│   ├── [session-id]/
│   │   ├── metadata.json
│   │   ├── round-0-inspiration.md
│   │   ├── round-1-ideas.md
│   │   ├── round-2-debate.md
│   │   ├── round-3-synthesis.md
│   │   └── final-report.md
│   └── ...
└── reports/
    ├── YYYY-MM-DD-[topic-slug].md (symbolic link to final report)
    └── ...
```

**Session Metadata (metadata.json):**

```json
{
  "session_id": "20251104-103042-innovate-optimization",
  "topic": "Optimize innovate command workflow",
  "mode": "standard",
  "status": "completed",
  "started_at": "2025-11-04T10:30:42Z",
  "completed_at": "2025-11-04T11:15:20Z",
  "rounds_completed": 3,
  "roles": ["The Optimizer", "The Innovator"],
  "can_resume": false
}
```

**Save Process:**

1. **Generate session ID**: `YYYYMMDD-HHMMSS-[topic-slug]`
2. **Create session directory**: `.specify/brainstorms/sessions/[session-id]/`
3. **Save incrementally after each round**:
   - Round 0 → `round-0-inspiration.md`
   - Round 1 → `round-1-ideas.md`
   - Round 2 → `round-2-debate.md`
   - Round 3 → `round-3-synthesis.md`
   - Final report → `final-report.md`
4. **Update metadata.json** after each round:
   - `rounds_completed`: increment
   - `status`: "in_progress" → "completed"
   - `can_resume`: true if interrupted, false if completed
5. **Create quick-access link**:
   - Symlink in `reports/`: `YYYY-MM-DD-[topic-slug].md` → `sessions/[session-id]/final-report.md`

**Resume Capability:**

Users can resume interrupted sessions:

```bash
/specify.innovate --resume [session-id]
```

**Resume Logic:**

1. Load `metadata.json` to check status
2. If `status == "in_progress"`:
   - Load completed rounds from session directory
   - Display summary: "Resuming from Round [N+1]"
   - Continue execution
3. If `status == "completed"`:
   - Ask: "Session already complete. View report or start new iteration?"
   - Options: View, Iterate (adds rounds 4-5), New session

**Output to User:**

```markdown
## Session Saved ✅

**Session ID**: [session-id]
**Location**: `.specify/brainstorms/sessions/[session-id]/`
**Quick access**: `.specify/brainstorms/reports/YYYY-MM-DD-[topic-slug].md`

**Files created:**
- ✅ Round 0: Cross-domain inspiration
- ✅ Round 1: Initial ideas
- ✅ Round 2: Challenge-rebuttal
- ✅ Round 3: Synthesis
- ✅ Final report

**To resume later**: `/specify.innovate --resume [session-id]`
**To view report**: Check the quick-access link above
```

**If not in a feature context:**

- Only display the report in conversation
- Ask user: "Would you like to save this session? If yes, I'll create the directory structure."
- If user confirms, create `.specify/brainstorms/` in current directory

## Operating Principles

### Parallel Thinking Rules

1. **True Independence**: All agents must develop their ideas independently in Round 1
2. **No Premature Convergence**: Encourage divergent thinking before synthesizing
3. **Constructive Critique**: When challenging ideas, focus on improvement not destruction
4. **Evidence-Based**: Support claims with reasoning, examples, or analogies
5. **Time-Boxed**: Each round should produce focused output, not exhaustive analysis
6. **Cross-Domain Inspiration**: Each agent must reference at least one insight from Round 0
7. **Mandatory Challenges**: In Round 2, each agent must challenge at least one other agent's idea

### Quality Standards

- **Clarity**: Each idea must be understandable to a non-expert
- **Actionability**: Include enough detail to evaluate feasibility
- **Originality**: Challenge conventional approaches
- **Balance**: Maintain tension between practical and innovative
- **Testability**: Ideas should be specific enough to prototype or validate
- **Diversity**: Avoid groupthink - actively seek contrarian perspectives

### User Interaction

- **After Mode Selection**: Confirm mode or allow user to override
- **After Round 0**: Ask if user wants to add custom analogies
- **After Round 1**: Ask user if they want to focus on specific ideas (optional filter)
- **After Round 2**: Ask if any direction should be explored deeper
- **After Round 3**: Ask if synthesis captures their needs or needs iteration
- **Allow interruption**: User can interrupt at any point with new constraints or directions
- **Support mode switching**: User can say "switch to deep mode" mid-session

### Session Management

- **Auto-save**: Save after each round automatically
- **Resumable**: All sessions can be resumed after interruption
- **Versioned**: Keep all intermediate rounds for traceability
- **Quick access**: Provide simple paths to final reports
- **Metadata tracking**: Record decisions, roles, and timing for future reference

## Edge Cases

- **Vague Topic**: Ask 2-3 clarifying questions before starting rounds
- **Technical Topic**: Agents should understand domain context; briefly research if needed
- **Early Termination**: User says "stop" → save current progress, provide summary so far
- **Iteration Request**: User says "iterate on idea X" → run focused micro-session on that idea
- **No Clear Winner**: Present all top ideas as equally valid options with tradeoffs
- **Mode Switch Mid-Session**: User requests deeper analysis → switch to Deep mode, add rounds 4-5
- **Session Resumption**: Load interrupted session → verify context, continue from last checkpoint
- **Role Mismatch**: If no roles match topic → gracefully fall back to default (Optimizer + Innovator)
- **Too Many Roles**: If config returns >4 roles → pick top 4 by relevance
- **Custom Roles**: User specifies "--roles 'Security, UX, Performance'" → use custom roles instead of auto-detection
- **Save Failure**: If directory creation fails → display report only, warn about missing persistence
- **Cross-Domain Shortage**: Can't find 3 good analogies → use 1-2 strong ones rather than weak matches

## Example Usage

### Example 1: Standard Mode (Default)

```
User: /specify.innovate How can we improve our code review process?
```

Expected flow:

1. **Mode Selection**: Analyzes topic, recommends Standard mode (30-45 min, 3 rounds)
2. **Role Assignment**: Detects "code review" + "improve" → assigns Developer, Product Manager, End User Advocate
3. **Round 0**: Generates cross-domain analogies (Medical peer review, Restaurant quality control, Academic publishing)
4. **Round 1**: Each of 3 agents proposes 3-5 ideas inspired by analogies
5. **Round 2**: 
   - Phase A: Each agent challenges another's idea
   - Phase B: Rebuttals and improvements
   - Phase C: Generate 2-3 hybrid ideas
6. **Round 3**: 
   - Multi-agent evaluation matrix (all agents score top ideas)
   - User impact analysis (novice, power users, admins)
   - Top 3 consensus recommendations
7. **Save**: Auto-save to `.specify/brainstorms/sessions/[id]/`, create quick-access link
8. **Output**: Comprehensive report with actionable recommendations

### Example 2: Quick Mode for Simple Topics

```
User: /specify.innovate --quick What's a catchy name for our new feature?
```

Expected flow:

1. **Mode Selection**: User specified Quick mode (15-20 min, 2 rounds)
2. **Role Assignment**: Creative task → uses default (Optimizer + Innovator)
3. **Round 0**: Skipped (optional in Quick mode)
4. **Round 1**: Each agent proposes 3 name ideas
5. **Round 2**: Quick critique + 2 hybrid suggestions
6. **Output**: Top 3 name recommendations with brief rationale

### Example 3: Deep Mode for Critical Decisions

```
User: /specify.innovate --deep Should we migrate to microservices or stay monolithic?
```

Expected flow:

1. **Mode Selection**: Deep mode (60+ min, 5 rounds)
2. **Role Assignment**: Architecture topic → Solution Architect, DevOps Engineer, Cost Analyst, Performance Engineer
3. **Round 0**: Cross-domain + competitive analysis (Netflix, Uber, Shopify case studies)
4. **Round 1**: Each of 4 agents proposes 5-7 ideas
5. **Round 2**: Challenge-rebuttal + hybrid formation
6. **Round 3**: Full synthesis + user impact
7. **Round 4**: Risk analysis + failure modes for top 3
8. **Round 5**: Implementation roadmap + validation plan
9. **Output**: Executive-level report with detailed analysis, risks, and migration plan

### Example 4: Resume Interrupted Session

```
User: /specify.innovate --resume 20251104-103042-code-review-improvement
```

Expected flow:

1. Load metadata.json from session
2. Verify status = "in_progress", rounds_completed = 2
3. Display: "Resuming from Round 3 - Synthesis & Recommendation"
4. Load Round 1 and Round 2 results from saved files
5. Continue with Round 3
6. Update session status to "completed"

### Example 5: Custom Roles

```
User: /specify.innovate --roles "Security Expert, Privacy Officer, Compliance" Design a new user authentication system
```

Expected flow:

1. Override auto-detection, use custom roles specified
2. Proceed with 3 specified expert roles
3. Standard 3-round flow with custom perspectives

## Context

$ARGUMENTS

