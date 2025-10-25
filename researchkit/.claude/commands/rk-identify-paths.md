# /rk.identify-paths - Identify Research Paths and Traditions

You are helping the user identify relevant research paths, traditions, and theoretical frameworks for their research question.

## Context

The user has defined and refined their research question. Now they need to identify which research traditions, disciplines, and theoretical frameworks are relevant to answering it.

A "research path" is a coherent body of scholarship - a research tradition, theoretical framework, or disciplinary approach that addresses aspects of the question.

## Your Task

### Step 1: Read the Research Question

Load: `projects/[project-name]/questions/02-selected-questions.md`

Understand:
- What question(s) have been selected?
- What disciplines were mentioned as relevant?
- What's the practical context and audience?

### Step 2: Identify Potential Research Paths

Based on the question, propose 5-8 research paths that could provide valuable perspectives.

**For each path, suggest**:
- **Path name** (e.g., "Organizational Ambidexterity," "Culture Change Theory")
- **Core focus** (what this tradition studies)
- **Key disciplines** (psychology, sociology, strategy, economics, etc.)
- **Relevance to question** (why this path matters)
- **Practical value** (how actionable insights are likely to be)
- **Foundation strength** (is there established foundational work + recent reviews?)

**Example paths for "How do organizations balance continuity and adaptation during tech change?"**:

1. **Organizational Ambidexterity**
   - Focus: Balancing exploration vs exploitation
   - Disciplines: Organizational theory, strategic management
   - Relevance: HIGH - directly addresses continuity/adaptation tension
   - Practical value: HIGH - established frameworks for practitioners
   - Foundation: Strong (O'Reilly & Tushman 1996, recent reviews available)

2. **Corporate Culture & Identity Studies**
   - Focus: How organizational identity shapes adaptation
   - Disciplines: Organizational psychology, sociology
   - Relevance: HIGH - explains resistance to change
   - Practical value: MEDIUM - concepts need translation for practitioners
   - Foundation: Strong (Schein 1985, Albert & Whetten 1985)

3. **Strategic Transformation Literature**
   - Focus: How firms reconfigure during disruption
   - Disciplines: Strategy, business history
   - Relevance: HIGH - case studies of transformation
   - Practical value: VERY HIGH - practitioner-focused field
   - Foundation: Moderate (scattered across cases, some frameworks)

4. **Innovation Diffusion Theory**
   - Focus: How new technologies spread in organizations
   - Disciplines: Innovation studies, sociology
   - Relevance: MEDIUM - too broad, not specific to identity/culture
   - Practical value: MEDIUM - general principles
   - Foundation: Strong (Rogers 1962, extensive follow-up)

5. **Change Management Theory**
   - Focus: Process models for organizational change
   - Disciplines: Management, organizational development
   - Relevance: MEDIUM-HIGH - process focus, less on culture/identity
   - Practical value: HIGH - very practitioner-oriented
   - Foundation: Moderate (Kotter, others - more practitioner than academic)

### Step 3: Present Paths for Selection

Present paths in a clear format showing:
- Path name
- One-sentence description
- Relevance rating (VERY HIGH / HIGH / MEDIUM / LOW)
- Practical value rating (VERY HIGH / HIGH / MEDIUM / LOW)
- Foundation strength (Strong / Moderate / Weak)
- Expected insights (what this path would contribute)

**Format as an interactive selection** (like Spec Kit's specify command):
```markdown
Select research paths to explore (recommended: 3-5 paths):

[ ] Organizational Ambidexterity
    Focus: Balancing exploration vs exploitation
    Relevance: HIGH | Practical Value: HIGH | Foundation: Strong
    Expected insights: Frameworks for managing dual structures

[✓] Corporate Culture & Identity
    Focus: How organizational identity shapes adaptation
    Relevance: HIGH | Practical Value: MEDIUM | Foundation: Strong
    Expected insights: Why culture resists change, identity rigidity

[ ] Strategic Transformation
    Focus: How firms reconfigure during disruption
    Relevance: HIGH | Practical Value: VERY HIGH | Foundation: Moderate
    Expected insights: Transformation patterns, success factors
```

Ask: "Which research paths would you like to explore? Select 3-5 that seem most promising."

### Step 4: For Each Selected Path, Generate Research Path File

Using template at `researchkit/templates/project/research-path-template.md`, create:

`projects/[project-name]/research-paths/paths/[path-slug].md`

**You'll need to populate**:

#### A. Path Description
- What is this research tradition?
- Core focus and key debates
- Relationship to research question

#### B. Foundational Texts (3-5 seminal works)

**Use your knowledge to suggest** foundational texts. For example:

For "Organizational Ambidexterity":
1. **March, J.G. (1991)** - "Exploration and Exploitation in Organizational Learning"
   - Core contribution: Introduced explore/exploit tension
   - Why foundational: Defined the central paradox
   - Citation count: ~30,000+

2. **O'Reilly, C.A. & Tushman, M.L. (1996)** - "Ambidextrous Organizations"
   - Core contribution: How to manage dual structures
   - Why foundational: First framework for organizational ambidexterity
   - Citation count: ~10,000+

**Important**: Mark these as "AI-suggested - verify availability" since you don't know if user has access.

#### C. Recent Literature Reviews (1-3 from last 3-5 years)

Suggest recent reviews based on your knowledge. For example:

For "Organizational Ambidexterity":
1. **Birkinshaw, J., et al. (2023)** - "Ambidexterity: A systematic review"
   - Scope: Reviews 200+ papers, 1990-2022
   - Key synthesis: Four types of ambidexterity (structural, contextual, temporal, leadership)
   - Identified gaps: Limited work on digital transformation contexts
   - Relevance: VERY HIGH

**Important**: Mark as "AI-suggested - verify this review exists and is accessible"

#### D. High-Impact Recent Work

Based on your knowledge of the field, suggest 2-4 highly-cited recent papers (post-2010).

#### E. Emerging Concepts (Post-2020)

Suggest emerging concepts you're aware of. For example:
- "Digital ambidexterity" - applying classic framework to AI/digital contexts
- "Temporal ambidexterity" - switching vs simultaneous approaches
- "Ambidextrous leadership" - individual vs structural solutions

#### F. Practical Relevance Assessment

For the user's stated audience (from question file), assess:
- **High practical value**: Which concepts/frameworks are directly actionable?
- **Medium practical value**: What needs translation?
- **Low practical value**: What's academic-only (debates without practical import)?

Example:
```markdown
### High Practical Value ✓
- Ambidextrous structures (separate vs integrated teams)
- Leadership behaviors for ambidexterity
- Metrics for balancing exploration/exploitation

### Low Practical Value (Academic interest only)
- Measurement debates (how to operationalize ambidexterity)
- Boundary condition arguments (when framework applies)
```

### Step 5: Create Research Path Selection File

Create: `projects/[project-name]/research-paths/selection.md`

Document:
- Which paths were selected (and why)
- Which paths were considered but rejected (and why)
- How paths relate to each other (complementary? contradictory?)
- Recommended reading order or priority

### Step 6: Generate Initial Document Collection List

Create: `projects/[project-name]/documents/download-queue.md`

For each selected research path, list:
- Foundational texts to collect
- Recent reviews to collect
- Priority level (HIGH / MEDIUM / LOW)
- Where to save (foundational / recent-reviews / supplementary)

Format:
```markdown
## Documents Needing Collection

### HIGH Priority - Foundational Texts

- [ ] **March, J.G. (1991)** - "Exploration and Exploitation in Organizational Learning"
  - Source: Organization Science
  - Save to: documents/foundational/march-1991-exploration-exploitation.pdf
  - Note: Seminal work - essential reading

- [ ] **O'Reilly & Tushman (1996)** - "Ambidextrous Organizations"
  - Source: California Management Review
  - Save to: documents/foundational/oreilly-tushman-1996-ambidextrous.pdf
  - Note: Foundational framework

### HIGH Priority - Recent Reviews

- [ ] **Birkinshaw et al. (2023)** - "Ambidexterity: A systematic review"
  - Source: [Journal name if known]
  - Save to: documents/recent-reviews/birkinshaw-2023-review.pdf
  - Note: Comprehensive synthesis, most recent review
```

### Step 7: Update Project README

Update `projects/[project-name]/README.md` to check off:
```markdown
- [x] Constitution created
- [x] Research question defined
- [x] Research paths identified  ← NEW
- [ ] Documents collected
```

### Step 8: Suggest Next Steps

Tell user:
```
✅ Research paths identified: [X] paths selected

Next steps:
1. Review the research path files in research-paths/paths/
2. Check the download queue: documents/download-queue.md
3. Collect documents (manually download PDFs from your library/sources)
4. Once you have some documents, run /rk.create-stream [discipline-name] to start research
```

## Guidelines for Path Identification

### Good Research Paths Are:
- **Coherent**: A recognizable tradition with foundational works
- **Relevant**: Addresses some aspect of the research question
- **Rich**: Has both foundations and recent developments
- **Accessible**: User can find the key texts (not too obscure)
- **Valuable**: Will contribute actionable insights

### Avoid:
- Paths too narrow (single paper, not a tradition)
- Paths too broad (e.g., "psychology" - need specific sub-field)
- Purely methodological paths (unless methodology IS the question)
- Paths without recent activity (dormant fields)

### For Multi-Disciplinary Questions:
- Ensure paths span different disciplines
- Note where paths complement vs contradict each other
- Suggest reading order (foundations first, then specialized)

### For Practitioner-Focused Research:
- Weight practical value heavily
- Include at least one practitioner-oriented path (HBR, strategy consulting)
- Flag academic debates that don't matter to practitioners

## Handling User Constraints

If user says:
- "I only have access to open sources" → Prioritize open-access journals, working papers
- "I need Fortune 500 relevant only" → Filter ruthlessly for practitioner value
- "I'm short on time" → Suggest 3 paths max, focus on recent reviews
- "I need academic rigor" → Include foundational theoretical work, not just practitioner literature

## Important Notes

**On suggesting sources**:
- You're suggesting based on your training knowledge
- Mark everything as "AI-suggested - verify availability"
- User will need to confirm these sources exist and are accessible
- Provide enough detail (author, year, title) for user to search

**On practical relevance**:
- Always assess for user's stated audience
- Don't assume all academic work is irrelevant or all practitioner work is shallow
- The best insights often combine academic rigor with practical application

**On research path selection**:
- 3-5 paths is usually optimal (not too narrow, not overwhelming)
- Encourage diversity of perspectives
- Warn if all paths are from same discipline

## File Locations

- Research paths: `projects/[project-name]/research-paths/paths/[path-slug].md`
- Selection file: `projects/[project-name]/research-paths/selection.md`
- Download queue: `projects/[project-name]/documents/download-queue.md`
- Template: `researchkit/templates/project/research-path-template.md`
