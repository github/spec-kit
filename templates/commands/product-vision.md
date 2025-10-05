---
description: Create or update product-level strategic vision (PRD) with market research, personas, and success metrics.
scripts:
  sh: scripts/bash/setup-product-vision.sh --json
  ps: scripts/powershell/setup-product-vision.ps1 -Json
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

## Purpose

Generate product-level strategic vision (Tier 1) that provides context for all feature specifications. This is **optional** but recommended for:
- Complex products or platforms
- 0-to-1 (greenfield) development
- Multi-feature systems
- Products requiring strategic alignment

**Skip this for**:
- Single features or simple tools
- Brownfield feature additions to existing products
- Quick prototypes

## Execution Flow

1. **Run Setup Script**

   Run `{SCRIPT}` from repo root and parse JSON output for PRODUCT_VISION_FILE (absolute path).

2. **Load Template**

   Load `templates/product-vision-template.md` to understand required sections and execution flow.

3. **CRITICAL VALIDATION**

   This is STRATEGIC ONLY. Any technical architecture, API design, or implementation details are ERRORS and must not appear in the output.

   **Forbidden content**:
   - System architecture diagrams
   - API endpoint design
   - Database schema
   - Technology stack choices
   - Component diagrams
   - Technical sequence diagrams
   - Implementation strategies

   **If you find yourself wanting to include any of the above: STOP. That content belongs in /plan, not here.**

4. **Phase 1: Strategic Research**

   Conduct parallel research using Task tool if needed:

   **Market Research**:
   - Identify competitors and alternative solutions
   - Estimate total addressable market (TAM)
   - Analyze market trends relevant to this product
   - Research competitive differentiation opportunities

   **User Research**:
   - Identify target user segments
   - Research common pain points in this domain
   - Understand current user workflows
   - Find opportunities for value creation

   **Business Research**:
   - Research common pricing models in this space
   - Understand go-to-market strategies
   - Identify business risks (market, competitive, adoption)

5. **ULTRATHINK: Deep Strategic Analysis**

   Before creating the vision document, deeply analyze:
   - What business assumptions could invalidate this product?
   - What user behaviors are we assuming that might not be true?
   - What market dynamics could change in 6-12 months?
   - What competitive responses should we anticipate?
   - What edge cases or exceptional scenarios could derail adoption?
   - How does this product align with long-term business strategy?

6. **Phase 2: Vision Generation**

   Using the template structure, generate:

   **Problem Statement**:
   - Clear articulation of user pain
   - Why this problem is worth solving
   - Business opportunity size

   **Target Users & Personas** (3-5 detailed personas):
   - Role and context
   - Goals and motivations
   - Pain points and frustrations
   - Success criteria

   **Product-Wide User Stories**:
   - High-level, strategic user stories
   - Not feature-specific (those come in /specify)
   - Capture core value proposition

   **User Journey Maps**:
   - Create Mermaid flow diagrams showing USER actions and decisions
   - **NOT system diagrams** - focus on user perspective
   - Discovery → Onboarding → Usage → Success

   **Success Metrics & KPIs**:
   - North Star metric
   - Acquisition, engagement, retention metrics
   - Business metrics (revenue, CAC, LTV)
   - Timeline: 3-month, 6-month, 12-month targets

   **Product-Wide Non-Functional Requirements**:
   - Performance: Response times, throughput
   - Security: Auth, encryption, compliance
   - Scalability: User capacity, data scale
   - Availability: Uptime SLAs, disaster recovery
   - These apply to ALL features

7. **Phase 3: Risk Analysis**

   **Business Risks**:
   - Market risks (competition, adoption, timing)
   - Business model risks (pricing, go-to-market)
   - User behavior risks (assumptions about usage)
   - Each risk with: Impact, Likelihood, Mitigation

   **Edge Cases (Business Perspective)**:
   - User without internet?
   - Organization blocks external services?
   - Competitor makes product free?
   - Regulatory changes?
   - Viral growth exceeds capacity?

8. **VALIDATION GATE: Technical Content Check**

   **Critical check before writing file**:
   - Scan entire generated content
   - If system architecture diagrams found: ERROR "Remove system architecture - belongs in /plan"
   - If API design or endpoints found: ERROR "Remove API design - belongs in /plan"
   - If technology choices found: ERROR "Remove tech stack decisions - belong in /plan"
   - If database design found: ERROR "Remove database schema - belongs in /plan"
   - If implementation strategy found: ERROR "Remove implementation details - belong in /plan"

   **Only pass gate if**: Document contains ONLY strategic, business, and user-focused content.

9. **Write Product Vision File**

   Write the completed product-vision.md to PRODUCT_VISION_FILE (absolute path from script output).

   Ensure:
   - All template sections filled appropriately
   - Markdown formatting correct
   - Mermaid diagrams valid syntax
   - No [NEEDS CLARIFICATION] for strategic decisions (unless truly uncertain)

10. **Report Completion**

    Report to user:
    - File path: PRODUCT_VISION_FILE
    - Summary: Problem statement in 1-2 sentences
    - Key personas: List 2-3 primary personas
    - North Star metric: What success looks like
    - Next step: "Use `/specify` to create first feature (MVP)"

## Research Integration Guidelines

### Strategic Research (DO THIS)
- Market analysis and competitive landscape
- User persona development
- Business model research
- Success metric benchmarks
- Regulatory/compliance research if applicable

### Technical Research (DON'T DO THIS - belongs in /plan)
- ❌ Architecture pattern research
- ❌ Technology stack evaluation
- ❌ Library/framework comparisons
- ❌ Infrastructure research
- ❌ API design patterns

### Quality Gates

**Must have**:
- [ ] At least 2-3 detailed personas
- [ ] Clear problem statement tied to business value
- [ ] Measurable success metrics with targets
- [ ] Product-wide NFRs that features will inherit
- [ ] Business risk analysis with mitigations
- [ ] User flow diagrams (user perspective, not system)

**Must NOT have**:
- [ ] Zero system architecture content
- [ ] Zero API design content
- [ ] Zero technology decisions
- [ ] Zero implementation strategies
- [ ] All diagrams are user-focused, not system-focused

## User Experience Flow

When user runs `/product-vision Build a team collaboration platform`:

1. **Research Phase** (may take 2-3 minutes with parallel agents):
   - "Researching collaboration platform market..."
   - "Analyzing competitor offerings..."
   - "Identifying user personas in distributed teams..."

2. **Generation Phase**:
   - "Creating product vision..."
   - "Defining success metrics..."
   - "Analyzing business risks..."

3. **Validation Phase**:
   - "Validating no technical content leaked..."
   - "Ensuring all strategic sections complete..."

4. **Completion**:
   ```
   Created product vision at: docs/product-vision.md

   Problem: Distributed teams struggle with async communication across timezones

   Key Personas:
   - Remote Developer: Needs async collaboration without blocking teammates
   - Product Manager: Needs visibility into team activity
   - Team Lead: Needs to organize conversations by project

   North Star Metric: 70% daily active users with <2hr response times

   Next: Use /specify to create your first feature (MVP)
   ```

## Template Constraints

The product-vision-template.md enforces these constraints through its structure:

1. **No Technical Sections**: Template has no section for architecture or technical design
2. **User-Focused Diagrams**: Mermaid examples show user journeys, not system architecture
3. **Strategic NFRs Only**: NFRs are stated as requirements (what), not solutions (how)
4. **Validation Checklist**: Template includes explicit check for technical content

## Integration with Other Commands

### /specify reads product-vision.md
- Inherits personas for feature user stories
- Inherits product-wide NFRs
- Uses success metrics to prioritize features
- Aligns feature with strategic vision

### /plan does NOT read product-vision.md directly
- Reads /specify output which contains product context
- Makes technical decisions to satisfy requirements
- Product vision influences through feature specs, not directly

## Common Mistakes to Avoid

1. **Including "Technology Stack" section** - belongs in /plan
2. **Drawing system architecture diagrams** - only user journey diagrams allowed
3. **Specifying API endpoints or data models** - belongs in /plan
4. **Choosing databases or cloud providers** - belongs in /plan
5. **Implementation phases or technical milestones** - belongs in /plan

**Remember**: If it's about HOW to build, it doesn't belong here. Only WHAT to build and WHY.

Use absolute paths with the repository root for all file operations to avoid path issues.
