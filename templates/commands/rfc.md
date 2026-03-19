---
description: Create a technical RFC (Request for Comments) from an existing feature spec, proposing HOW to build it.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec and RFC. I am building with...
    send: true
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
scripts:
  sh: scripts/bash/setup-rfc.sh --json
  ps: scripts/powershell/setup-rfc.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/speckit.rfc` in the triggering message provides additional context or constraints for the RFC (e.g., preferred technology, architectural direction). Use it to guide decisions but derive the RFC content from the spec.

Given the feature spec, do this:

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, RFC_FILE, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC. If spec.md does not exist, ERROR: "No spec found. Run /speckit.specify first."

3. **Load RFC template**: Read `templates/rfc-template.md` to understand required sections.

4. **Extract from spec**:
   - Functional requirements (FR-xxx) — these define WHAT the system must do
   - Success criteria (SC-xxx) — these become business metrics
   - User scenarios — these inform rollout and architecture decisions
   - Edge cases — these inform known limitations and trade-offs
   - Key entities — these inform data/architecture design

5. **Generate RFC content** following the execution flow:

   1. Parse user input for technology preferences or constraints
      If user specified tech stack or direction: use as primary constraint
      If empty: infer from project context (existing code, dependencies)
   2. Write Decision Summary (2-3 sentences: problem, chosen approach, key trade-off)
   3. Write Background (technical landscape, current system state — NOT business context)
   4. Write Problem (why current system can't meet spec requirements — NOT the business need)
   5. Write Proposal with Architecture diagram
   6. Write Alternatives Considered (MANDATORY — minimum 2 alternatives with verdicts)
   7. Write Rollout Strategy (ONLY if change affects production systems)
   8. Write Metrics — split into Business (from spec SC-xxx) and Technical
   9. Write Known Limitations (bullet list)
   10. Write Dependencies (ONLY if cross-team or external)
   11. Write Security & Compliance (ONLY if auth, PII, external APIs, or trust boundary changes)
   12. Write Outstanding Questions (MAX 5, each must be BLOCKING, tagged with owner)

6. **Write the RFC** to RFC_FILE using the template structure.

7. **RFC Quality Validation**: After writing, validate against the discipline guidelines:

   a. **Run validation check** against each rule:

      | Rule | Check |
      |------|-------|
      | Decision document | Does every section help a reviewer make or validate a decision? |
      | No business rehash | Does Background/Problem avoid restating what's in the spec? |
      | No teaching | Does it avoid explaining standard concepts the audience already knows? |
      | Alternatives have verdicts | Does every alternative state why it was chosen or rejected? |
      | Diagrams over prose | Are component interactions shown as diagrams, not paragraphs? |
      | Blocking questions only | Are all Outstanding Questions genuinely blocking? |
      | Single decision scope | Does the RFC cover ONE architectural decision (or tightly coupled set)? |
      | Length discipline | Background 1-2 paragraphs, Problem 1-3 paragraphs, Questions max 5? |

   b. **Handle validation results**:
      - If all pass: proceed to step 8
      - If any fail: fix the RFC content and re-validate (max 2 iterations)
      - After 2 iterations: document remaining issues and warn user

8. **Report completion** with branch name, RFC file path, spec reference, and readiness for `/speckit.plan`.

## RFC Writing Guidelines

These rules are NON-NEGOTIABLE. Apply them during generation, not just validation.

1. **RFCs are DECISION documents, not design documents.**
   The plan handles implementation detail. The RFC captures WHAT technical
   approach was chosen, WHY it was chosen over alternatives, and WHAT the
   trade-offs are. If a section doesn't help a reviewer make or validate
   a decision, cut it.

2. **Don't re-explain the business problem.**
   The spec already covers WHAT and WHY. The RFC's Problem section explains
   why the CURRENT SYSTEM can't meet that need — not why the business needs
   the feature.

3. **Don't teach your reviewers.**
   Assume technical competence. Don't define industry terms, explain standard
   patterns, or cite Wikipedia. Link to references if context is truly needed.

4. **Every alternative must have a verdict.**
   "Alternatives Considered" is not a literature review. Each option needs:
   what it is, why it could work, why it was rejected (or chosen).
   If you can't articulate why an alternative was rejected, you haven't
   made a decision yet.

5. **Diagrams over paragraphs.**
   A system diagram replaces 500 words of prose. If you're describing
   data flow or component interaction in sentences, draw it instead.

6. **Outstanding Questions must be blocking.**
   If a question doesn't block the decision or implementation, it doesn't
   belong here. Nice-to-know questions go in discussion threads, not the RFC.

7. **Scope the RFC to ONE decision.**
   If your RFC covers multiple independent architectural decisions,
   split it into separate RFCs. Exception: tightly coupled decisions
   that can't be evaluated independently.

8. **Length discipline.**
   - Decision Summary: 2-3 sentences
   - Background: 1-2 paragraphs (link to prior work, don't summarize it)
   - Problem: 1-3 paragraphs
   - Proposal: as long as needed, but prefer diagrams + bullets over prose
   - Alternatives: table format preferred
   - Known Limitations: bullet list
   - Outstanding Questions: max 5 (if more, the RFC isn't ready)

### Section Requirements

- **Mandatory sections**: Decision Summary, Background, Problem, Proposal (with Architecture), Alternatives Considered, Metrics & Definition of Success, Known Limitations
- **Optional sections**: Rollout Strategy, Dependencies, Security & Compliance, Outstanding Questions
- When an optional section doesn't apply, remove it entirely (don't leave as "N/A")

### How Sections Connect to the Spec

| RFC Section | Draws From Spec | Purpose |
|-------------|-----------------|---------|
| Background | Context + current system state | Technical landscape |
| Problem | Requirements (FR-xxx) | Why current system fails |
| Proposal | Success criteria + requirements | Technical approach |
| Alternatives | -- (new in RFC) | Decision justification |
| Metrics (Business) | Success criteria (SC-xxx) | How RFC achieves spec goals |
| Metrics (Technical) | -- (new in RFC) | Implementation-specific measures |
| Known Limitations | Edge cases | Deliberate scope boundaries |

### What Feeds Into the Plan

The `/speckit.plan` command consumes both the spec AND the RFC:
- Spec provides: requirements, success criteria, user scenarios
- RFC provides: architecture, technology choices, trade-offs, constraints
- Plan produces: phased implementation steps, research tasks, data model, contracts
