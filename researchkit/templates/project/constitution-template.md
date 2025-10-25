# Research Constitution

**Version**: [VERSION]
**Ratified**: [RATIFICATION_DATE]
**Last Amended**: [LAST_AMENDED_DATE]

---

## Preamble

This constitution establishes the immutable methodological principles governing all research conducted under this framework. These principles ensure rigor, multi-perspective analysis, and the production of actionable insights.

All research activities, document analysis, framework extraction, and writing MUST conform to these principles. Violations are subject to validation review.

---

## Article I: [PRINCIPLE_1_NAME]

**Description**: [PRINCIPLE_1_DESCRIPTION]

### Requirements
- [REQUIREMENT_1]
- [REQUIREMENT_2]
- [REQUIREMENT_3]

### Rationale
[PRINCIPLE_1_RATIONALE]

### Enforcement
[HOW_THIS_IS_ENFORCED]

---

## Article II: [PRINCIPLE_2_NAME]

**Description**: [PRINCIPLE_2_DESCRIPTION]

### Requirements
- [REQUIREMENT_1]
- [REQUIREMENT_2]
- [REQUIREMENT_3]

### Rationale
[PRINCIPLE_2_RATIONALE]

### Enforcement
[HOW_THIS_IS_ENFORCED]

---

## Article III: [PRINCIPLE_3_NAME]

**Description**: [PRINCIPLE_3_DESCRIPTION]

### Requirements
- [REQUIREMENT_1]
- [REQUIREMENT_2]
- [REQUIREMENT_3]

### Rationale
[PRINCIPLE_3_RATIONALE]

### Enforcement
[HOW_THIS_IS_ENFORCED]

---

## Article IV: [PRINCIPLE_4_NAME]

**Description**: [PRINCIPLE_4_DESCRIPTION]

### Requirements
- [REQUIREMENT_1]
- [REQUIREMENT_2]
- [REQUIREMENT_3]

### Rationale
[PRINCIPLE_4_RATIONALE]

### Enforcement
[HOW_THIS_IS_ENFORCED]

---

## Article V: [PRINCIPLE_5_NAME]

**Description**: [PRINCIPLE_5_DESCRIPTION]

### Requirements
- [REQUIREMENT_1]
- [REQUIREMENT_2]
- [REQUIREMENT_3]

### Rationale
[PRINCIPLE_5_RATIONALE]

### Enforcement
[HOW_THIS_IS_ENFORCED]

---

## Article VI: [PRINCIPLE_6_NAME]

**Description**: [PRINCIPLE_6_DESCRIPTION]

### Requirements
- [REQUIREMENT_1]
- [REQUIREMENT_2]
- [REQUIREMENT_3]

### Rationale
[PRINCIPLE_6_RATIONALE]

### Enforcement
[HOW_THIS_IS_ENFORCED]

---

## Amendment Process

**Semantic Versioning**: This constitution follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Backward-incompatible changes to core principles (removal or fundamental redefinition of articles)
- **MINOR**: New articles added or material expansion of existing principles
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

**Amendment Procedure**:
1. Proposed amendment must be documented with rationale
2. Impact assessment on existing research streams and artifacts
3. Version increment following semantic rules
4. Update of `Last Amended` date
5. Propagation of changes to all active research projects

**Immutability**: Articles marked as `[NON-NEGOTIABLE]` cannot be removed, only refined or clarified.

---

## Governance

**Authority**: This constitution is the highest authority in research methodology decisions. All conflicts between convenience and constitutional principles MUST be resolved in favor of the constitution.

**Enforcement**: The `/rk.validate` command checks all research artifacts against constitutional requirements and flags violations.

**Review Cadence**: Constitution should be reviewed at project milestones:
- After question refinement
- After completing first research stream
- Before synthesis phase
- After completing writing

---

## Example Principles (Sample - Replace with Your Own)

### Example Article I: Multi-Perspective Analysis

**Description**: All research must examine topics through multiple disciplinary and theoretical lenses.

**Requirements**:
- At least THREE different perspectives (e.g., cultural, structural, technological)
- Explicit identification of disciplinary lens for each research stream
- Documentation of how perspectives complement or contradict each other

**Rationale**: Complex topics cannot be understood through a single lens. Multi-perspective analysis reveals nuances and contradictions that single-perspective work misses.

**Enforcement**: The `/rk.create-stream` command requires explicit disciplinary lens declaration. The `/rk.validate` command checks for minimum three perspectives.

### Example Article II: Evidence-Based Reasoning

**Description**: All claims must be supported by traceable evidence from primary or authoritative sources.

**Requirements**:
- Every framework concept must cite foundational sources
- Every story/anecdote must include source document and location
- Distinguish between primary research, reviews, and commentary
- No unsourced assertions in synthesis or writing

**Rationale**: Intellectual rigor requires clear provenance. Unsourced claims undermine credibility and prevent verification.

**Enforcement**: Story templates require source fields. Framework templates require citation. `/rk.validate` checks for citation completeness.

### Example Article III: Contradiction Awareness

**Description**: Research must actively seek and document contradictions rather than prematurely resolving complexity.

**Requirements**:
- Create `synthesis/contradictions.md` documenting tensions in literature
- When sources disagree, both positions must be represented
- Resist urge to force consensus where none exists
- Document boundary conditions where frameworks apply/don't apply

**Rationale**: Premature synthesis loses valuable nuance. Contradictions often reveal the most important insights about a topic.

**Enforcement**: `/rk.cross-stream` command generates contradiction report. `/rk.validate` checks for contradiction documentation in synthesis phase.

### Example Article IV: Framework Extraction

**Description**: Research must produce clear, actionable frameworks suitable for practitioner application.

**Requirements**:
- Frameworks must include decision criteria (when to use, when not to use)
- Frameworks must be documented with illustrative examples
- Frameworks must specify context boundaries
- Abstract concepts must be paired with concrete applications

**Rationale**: Research that doesn't produce actionable insights has limited value for practitioners.

**Enforcement**: Framework template includes required sections. `/rk.validate` checks framework completeness.

### Example Article V: Practitioner Readiness

**Description**: All outputs must be accessible to non-academic audiences and grounded in real-world constraints.

**Requirements**:
- Avoid unnecessary jargon; define technical terms when used
- Include concrete examples and case studies
- Address practical constraints (time, resources, organizational politics)
- Test frameworks against real organizational contexts

**Rationale**: Research for consulting/practitioner work must bridge academic rigor and practical application.

**Enforcement**: Writing templates include readability checklist. `/rk.validate` can flag jargon density.

### Example Article VI: Narrative Evidence Discipline

**Description**: Research must distinguish between abstract concepts and vivid narrative evidence, systematically collecting both.

**Requirements**:
- For each significant concept, identify at least ONE vivid story
- Rate story vividness (specific people, moments, quotes, sensory detail)
- Tag stories with emotional tone and use cases
- Track story provenance (source document, page number)
- Writing must pair abstract frameworks with concrete narratives

**Rationale**: Abstract ideas become memorable and actionable when paired with character-driven stories.

**Enforcement**: `/rk.capture-story` command enforces story template. `/rk.write` command suggests stories for concepts. `/rk.validate` checks story-concept pairing.

---

*Replace the example articles above with principles specific to your research methodology and domain.*
