# /rk.constitution - Create or Update Research Constitution

You are helping the user create or update their research constitution - the immutable methodological principles that govern all research work.

## Context

The user is working with ResearchKit, a systematic framework for conducting rigorous research and extracting actionable frameworks. The constitution is the foundation of all work - it defines the methodological principles, quality standards, and enforcement mechanisms.

## Your Task

### If NO constitution exists yet (first time):

1. **Understand the user's research approach**:
   - Ask about their typical research methodology
   - What disciplines do they work across?
   - What's their target audience (academics, practitioners, executives)?
   - What quality standards matter most to them?
   - What methodological pitfalls do they want to avoid?

2. **Propose 4-6 core principles** based on their responses:
   - Each principle should be a "Article" (Article I, Article II, etc.)
   - Each should have: Description, Requirements (bullet points), Rationale, Enforcement
   - Consider principles like:
     - Multi-perspective analysis (examining topics through multiple lenses)
     - Evidence-based reasoning (clear source citations)
     - Contradiction awareness (documenting tensions, not hiding them)
     - Framework extraction (producing actionable insights)
     - Practitioner readiness (accessible to non-experts)
     - Narrative evidence discipline (pairing concepts with stories)

3. **Review the template** at `researchkit/templates/project/constitution-template.md` for structure

4. **Create the constitution** at `projects/[current-project]/constitution.md`:
   - Use semantic versioning: Start with 1.0.0
   - Set ratification date to today
   - Fill in all placeholder sections
   - Make principles specific to the user's work style

### If a constitution already EXISTS:

1. **Read the existing constitution** at `projects/[current-project]/constitution.md`

2. **Ask what needs updating**:
   - Adding a new principle? (MINOR version bump)
   - Clarifying existing wording? (PATCH version bump)
   - Removing or fundamentally changing a principle? (MAJOR version bump)

3. **Make the requested changes**:
   - Update version number following semantic versioning rules
   - Update "Last Amended" date
   - Document the change rationale

4. **Impact assessment**:
   - Note which existing research artifacts might be affected
   - Suggest running `/rk.validate` to check consistency

## Constitution Principles Guidelines

Good constitutional principles are:
- **Specific**: Not vague platitudes, but concrete requirements
- **Enforceable**: Include clear "how this is enforced" section
- **Valuable**: Address real methodological challenges
- **Measurable**: Can be validated via `/rk.validate` command

Avoid:
- Generic advice that applies to all research
- Principles that are impossible to check
- Overly restrictive rules that will be constantly violated

## Example Principles to Consider

Adapt these to the user's specific needs:

**Article I: Multi-Perspective Analysis**
- Require at least 3 different disciplinary lenses
- Document how perspectives complement or contradict
- Create separate research streams for different disciplines

**Article II: Evidence-Based Reasoning**
- Every claim must cite sources
- Distinguish primary vs. secondary sources
- Track document provenance

**Article III: Contradiction Awareness**
- Document contradictions in synthesis/contradictions.md
- Don't force consensus where none exists
- Represent multiple viewpoints when sources disagree

**Article IV: Framework Extraction**
- Frameworks must include decision criteria
- Must specify when framework applies/doesn't apply
- Must pair abstract concepts with concrete examples

**Article V: Practitioner Readiness**
- Avoid unnecessary jargon
- Include real-world constraints
- Test against actual organizational contexts

**Article VI: Narrative Evidence Discipline**
- For each concept, capture at least one vivid story
- Rate story vividness (1-10)
- Tag stories by emotional tone and use case
- Track story provenance

## File Management

- Constitution location: `projects/[project-name]/constitution.md`
- Use the template from: `researchkit/templates/project/constitution-template.md`
- Ensure proper versioning and dates

## After Creating/Updating Constitution

Suggest next steps:
- If first time: "Now run `/rk.question` to define your research question"
- If updating: "Run `/rk.validate` to check existing work against updated principles"

## Important

- The constitution should reflect the USER's methodology, not a generic template
- Ask questions to understand their specific needs
- Make it practical and enforceable
- Keep it concise - 4-6 core principles is usually enough
