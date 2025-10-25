# /rk.question - Define Research Question

You are helping the user define their research question - the foundation of their research project.

## Context

The user is starting a new research project or refining an existing question. The research question guides all subsequent work: what research paths to explore, what documents to collect, what frameworks to extract.

## Your Task

### Step 1: Capture the Initial Question

Ask the user:
- "What's the broad topic or question you want to research?"
- "Why does this matter? What decision or understanding does this inform?"
- "Who's the primary audience for these insights?"
- "What's the practical context? What real-world problem does this address?"

### Step 2: Create the Question File

Using the template at `researchkit/templates/project/question-template.md`, create:

`projects/[project-name]/questions/00-original.md`

Include:
- The original broad question (exactly as user stated it)
- Why this matters
- Intended audience
- Practical context

### Step 3: Propose Refinement Options (3-5 variants)

Generate 3-5 refined question variants that:
- Have different **focus** (what each emphasizes)
- Make different **assumptions** (what each takes for granted)
- Engage different **disciplines** (what fields each would draw from)
- Have different **scope** (broad/medium/narrow)
- Have different **practical value** (how actionable insights would be)

**Important**: Highlight the **subtle but meaningful differences** between options.

For example, if the broad question is:
"How do organizations change during technological disruption?"

Refined options might be:
1. "How do organizations **maintain identity** during tech disruption?"
   - Focus: Identity preservation
   - Assumes: Identity is primary concern
   - Disciplines: Org psychology, culture studies

2. "How do organizations **balance continuity and adaptation**?"
   - Focus: Paradox management
   - Assumes: Both continuity AND change are needed
   - Disciplines: Org theory, strategic management

3. "What **patterns predict successful** tech transformation?"
   - Focus: Success factors
   - Assumes: Success can be pattern-matched
   - Disciplines: Strategy, business history

### Step 4: Present Options to User

Present the refined options clearly, showing:
- The question variant
- What it focuses on
- Key assumptions
- Disciplines engaged
- Scope
- Expected practical value

Format as a table or structured list for easy comparison.

**Ask the user**: "Which refined question(s) resonate most? You can select 1-2 to pursue."

### Step 5: Document Selection

Once user selects:

Create: `projects/[project-name]/questions/01-refinement-options.md`
- Include all options you generated
- Show the comparison

Create: `projects/[project-name]/questions/02-selected-questions.md`
- Document which question(s) selected
- Why they chose this formulation
- Expected insights
- Research paths this implies

### Step 6: Suggest Next Steps

After question is defined, suggest:
- "Run `/rk.identify-paths` to explore research traditions relevant to this question"
- If constitution doesn't exist: "Consider running `/rk.constitution` first to establish your research principles"

## Guidelines for Good Refinement

**Effective refined questions are**:
- **Precise**: Clear about what's being asked
- **Answerable**: Not so broad that they can't be addressed
- **Distinctive**: Each variant offers a meaningfully different angle
- **Practical**: Connected to real decisions or understanding

**Avoid**:
- Questions that are too similar to each other
- Questions so narrow they're trivial
- Questions so broad they're unanswerable
- Purely academic questions with no practical value (unless that's what user wants)

## Question Evolution

Note to user: "Your research question may evolve as you learn more. That's normal and good. You can:
- Run `/rk.question` again to refine further
- Run `/rk.evolve-question --stream [name]` to create discipline-specific variants
- Document evolution in the question file's evolution log"

## File Locations

- Original question: `projects/[project-name]/questions/00-original.md`
- Refinement options: `projects/[project-name]/questions/01-refinement-options.md`
- Selected questions: `projects/[project-name]/questions/02-selected-questions.md`
- Template: `researchkit/templates/project/question-template.md`

## Important

- Take time to understand what the user REALLY cares about
- The refined options should meaningfully differ, not just use different words
- Highlight the **trade-offs** between options (what you gain/lose with each)
- Connect questions to practical outcomes when possible
- Remember: A good question shapes everything that follows
