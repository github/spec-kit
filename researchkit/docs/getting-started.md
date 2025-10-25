# Getting Started with ResearchKit

Welcome to ResearchKit! This guide will walk you through setting up your first research project.

---

## What is ResearchKit?

ResearchKit is a systematic framework for conducting rigorous, multi-disciplinary research and extracting actionable frameworks. It helps you:

- **Refine vague questions** into precise, answerable research questions
- **Organize research** across multiple disciplines and perspectives
- **Capture vivid stories** alongside abstract concepts
- **Extract frameworks** that combine rigor with practitioner value
- **Write compellingly** by integrating evidence and narrative

---

## Installation & Setup

### Step 1: Initialize ResearchKit

From your workspace directory:

```bash
./researchkit/scripts/init-researchkit.sh
```

This creates:
- `projects/` directory for your research projects
- `.researchkit` configuration file
- `.gitignore` for document management

### Step 2: Create Your First Project

```bash
./researchkit/scripts/new-project.sh "your-research-topic"
```

Example:
```bash
./researchkit/scripts/new-project.sh "organizational AI transformation"
```

This creates a numbered project directory (e.g., `projects/001-organizational-ai-transformation/`) with the complete structure:

```
001-organizational-ai-transformation/
├── constitution.md          # Your research principles
├── questions/               # Question development
├── research-paths/          # Research traditions
├── documents/               # Collected sources
├── stories/                 # Story library
├── streams/                 # Disciplinary research
├── synthesis/               # Frameworks
└── writing/                 # Drafts
```

---

## The Research Workflow

ResearchKit guides you through a structured workflow:

### 1. Define Research Principles (Constitution)

```bash
/rk.constitution
```

**What it does**: Creates your research methodology "constitution" - the immutable principles governing all your work.

**Example principles**:
- Multi-Perspective Analysis (examine through 3+ lenses)
- Evidence-Based Reasoning (all claims cited)
- Contradiction Awareness (document tensions, don't hide them)
- Framework Extraction (produce actionable insights)
- Practitioner Readiness (accessible to non-experts)
- Narrative Evidence (pair concepts with vivid stories)

**Output**: `projects/[your-project]/constitution.md`

**Why it matters**: The constitution ensures methodological rigor throughout your research. Every subsequent step can be validated against these principles.

---

### 2. Define Your Research Question

```bash
/rk.question
```

**What it does**: Helps you move from a broad, vague question to precise, answerable questions.

**Process**:
1. State your broad question (e.g., "What do we know about organizational change?")
2. ResearchKit generates 3-5 refined variants with different:
   - Focus (identity vs. strategy vs. culture)
   - Assumptions (what each takes for granted)
   - Disciplines (psychology vs. economics vs. sociology)
   - Scope (broad vs. narrow)
3. You select the most promising question(s)

**Output**:
- `questions/00-original.md` - Your initial broad question
- `questions/01-refinement-options.md` - Generated variants
- `questions/02-selected-questions.md` - Your selection

**Why it matters**: A well-refined question shapes everything that follows - what research paths to explore, what sources to read, what frameworks to extract.

---

### 3. Identify Research Paths

```bash
/rk.identify-paths
```

**What it does**: Identifies relevant research traditions, disciplines, and theoretical frameworks for your question.

**For each research path**:
- **Foundational texts** (seminal works)
- **Recent literature reviews** (synthesis of field)
- **High-impact recent work** (most-cited papers from reviews)
- **Emerging concepts** (new frameworks post-2020)
- **Practical relevance assessment** (for your target audience)

**Output**: `research-paths/paths/[path-name].md` for each tradition

**Example paths** for "organizational change during tech disruption":
- Organizational ambidexterity
- Corporate culture & identity
- Strategic transformation
- Change management theory

**Why it matters**: This prevents missing important perspectives and ensures you're building on established foundations.

---

### 4. Collect Documents

```bash
/rk.collect-documents
```

**What it does**: Generates list of documents to collect based on identified research paths.

**Process**:
1. Attempts to find and download available PDFs
2. Flags paywalled or restricted sources
3. Creates download queue for manual retrieval

**Output**:
- `documents/foundational/` - Seminal texts
- `documents/recent-reviews/` - Literature reviews
- `documents/supplementary/` - Additional sources
- `documents/download-queue.md` - Items needing manual download

**Why it matters**: Systematic document collection ensures you're not missing key sources.

---

### 5. Create Research Streams

```bash
/rk.create-stream [discipline-name] "[refined question]"
```

**What it does**: Creates a disciplinary "stream" - a lens through which to examine your question.

**Example**:
```bash
/rk.create-stream psychology "How do people maintain belonging when company mission shifts?"
/rk.create-stream finance "How can CFOs account for intangible value from new tech?"
/rk.create-stream strategy "How do firms reconfigure resources during disruption?"
```

**Output**: `streams/[discipline-name]/` with:
- `question.md` - Discipline-specific question variant
- `notes.md` - Research notes
- `concepts.md` - Extracted concepts and frameworks

**Why it matters**: Complex topics require multiple disciplinary perspectives. Streams keep each perspective organized while enabling cross-stream synthesis.

---

### 6. Conduct Research

```bash
/rk.research --stream [stream-name]
```

**What it does**: Guides systematic research within a stream, with prompts for:
- Reading and note-taking
- Concept extraction
- Story capture (see next section)
- Source tracking

**Why it matters**: Structured research prevents aimless reading and ensures you extract insights systematically.

---

### 7. Capture Stories (During Research)

```bash
/rk.capture-story
```

**What it does**: Captures vivid, character-driven stories that illustrate abstract concepts.

**Guided prompts**:
- One-sentence summary
- Full narrative with vivid detail (names, dates, quotes, sensory details)
- Key characters
- Emotional tone
- What concepts this illustrates
- Source citation
- Vividness rating (1-10)

**Output**:
- `stories/meta/[story-name].md` - Full story with metadata
- Updated `stories/index.md` - Searchable index

**Example story elements**:
- **Specific person**: "Steve Sasson, age 24"
- **Specific moment**: "In 1975, when he showed executives..."
- **Direct quote**: "That's cute—but don't tell anyone about it"
- **Irony/surprise**: Invented digital camera, told not to pursue it
- **Consequence**: Kodak missed the digital revolution

**Why it matters**: Stories make abstract frameworks memorable and emotionally engaging. Capturing them during research (with full detail) is far easier than reconstructing them later when writing.

---

### 8. Extract Frameworks

```bash
/rk.frameworks
```

**What it does**: Synthesizes research into actionable frameworks.

**Framework components**:
- Core insight (what's the "aha"?)
- Problem it addresses
- Framework components and their interactions
- When to use / not use (boundary conditions)
- Application process (how to use it)
- Illustrative stories (from story library)
- Evidence base (foundational + recent sources)
- Practical applications (for different audiences)

**Output**: `synthesis/frameworks.md`

**Why it matters**: Frameworks are the actionable output of research - the mental models practitioners can actually use.

---

### 9. Write

```bash
/rk.write "[topic]"
```

**What it does**: Generates writing that integrates:
- Frameworks (rigorous concepts)
- Stories (vivid examples)
- Evidence (proper citations)
- Practitioner focus (actionable insights)

**Process**:
1. Identifies relevant frameworks
2. Queries story library for high-vividness stories
3. Proposes narrative structure (e.g., "Lead with Kodak story, explain identity rigidity framework, contrast with Microsoft transformation")
4. Generates outline
5. Produces draft

**Output**: `writing/drafts/[topic].md`

**Why it matters**: Writing is where rigorous research becomes compelling communication.

---

## Example Workflow: Full Project

Let's walk through a complete example project.

### Scenario
You're consulting with Fortune 500 companies on AI adoption and want to understand organizational culture change during technological transformation.

### Step-by-Step

#### 1. Initialize and Create Project
```bash
./researchkit/scripts/init-researchkit.sh
./researchkit/scripts/new-project.sh "AI culture transformation"
```

#### 2. Define Research Principles
```bash
/rk.constitution
```

Creates constitution with principles like:
- Multi-Perspective Analysis (culture + strategy + finance)
- Evidence-Based Reasoning (cite all claims)
- Practitioner Readiness (Fortune 500 context)
- Narrative Evidence (capture vivid examples)

#### 3. Refine Question
```bash
/rk.question
```

**Broad question**: "How do companies adapt culture during AI transformation?"

**Refined options generated**:
1. "How can employees maintain identity when AI changes their role?"
2. "What cultural factors predict successful AI adoption?"
3. "How do leaders balance AI efficiency with human meaning?"

**Selected**: Option 3 (leadership focus, practitioner-relevant)

#### 4. Identify Research Paths
```bash
/rk.identify-paths
```

**Paths selected**:
- Organizational ambidexterity (balancing old + new)
- Culture change literature
- Leadership during transformation
- AI adoption studies

For each path, identifies:
- Foundational: O'Reilly & Tushman (1996), Schein (1985)
- Recent reviews: Birkinshaw et al. (2023)
- Emerging: "Digital ambidexterity" concepts

#### 5. Create Multi-Disciplinary Streams
```bash
/rk.create-stream psychology "How do people maintain meaning when AI changes work?"
/rk.create-stream strategy "How do leaders balance AI efficiency and human purpose?"
/rk.create-stream finance "How do CFOs value cultural capital during AI transformation?"
```

#### 6. Research and Capture Stories
```bash
/rk.research --stream psychology
```

While reading case studies, captures stories:

**Story 1**: Microsoft's transformation under Satya Nadella
- Vivid details: First all-hands, "read" vs "know-it-all" culture shift
- Emotional tone: Hopeful transformation
- Illustrates: Leadership-driven culture change
- Vividness: 8/10

**Story 2**: Kodak's digital camera suppression
- Vivid details: Steve Sasson, 1975, "don't tell anyone"
- Emotional tone: Tragic irony
- Illustrates: Culture resistance to change
- Vividness: 9/10

Captured via `/rk.capture-story` for each

#### 7. Extract Frameworks
```bash
/rk.frameworks
```

**Framework extracted**: "Culture-AI Balance Model"
- Components: (1) Identity preservation (2) Capability evolution (3) Meaning-making
- When to use: AI adoption in established companies
- Application: CFOs assess all three dimensions before rollout
- Stories: Microsoft (success), Kodak (failure)

#### 8. Write
```bash
/rk.write "The Culture-AI Paradox: Why Technical Success Isn't Enough"
```

**Generated structure**:
1. Hook: Kodak story (grab attention with irony)
2. Framework: Culture-AI Balance Model
3. Contrast: Microsoft transformation (shows alternative)
4. Application: How CFOs can use this framework
5. Conclusion: Culture eats strategy for breakfast, even with AI

**Output**: Polished draft integrating rigorous framework with emotionally resonant narrative.

---

## Key Principles

### 1. Constitution Governs Everything
Your research principles (constitution) are the foundation. Every command can validate against it with `/rk.validate`.

### 2. Questions Evolve
Initial questions are rarely final. Use `/rk.evolve-question` to create disciplinary variants as understanding deepens.

### 3. Multiple Perspectives Required
Complex topics need multiple disciplinary lenses. Create research streams for each perspective.

### 4. Capture Stories During Research
Don't wait until writing to look for examples. Capture vivid stories immediately with full detail.

### 5. Frameworks Before Writing
Extract frameworks during synthesis phase, not while drafting. This separates rigorous thinking from narrative craft.

### 6. Practical Relevance Filter
For consulting/practitioner work, explicitly assess practical value of every concept. Academic disputes without real-world implications are noted but deprioritized.

---

## Tips for Success

### For Question Refinement
- Start broad, refine iteratively
- Don't lock in too quickly - explore variants
- Consider who the audience is (academics vs practitioners)
- Test question against "so what?" criterion

### For Story Capture
- Names, dates, and quotes make stories vivid
- Capture during research, not during writing
- Rate vividness honestly (8+ are lead story candidates)
- Tag liberally - concepts can be added later

### For Multi-Stream Research
- Each stream should have a distinct question variant
- Document contradictions between streams
- Look for common concepts across streams
- Synthesis happens AFTER streams are developed

### For Framework Extraction
- Every framework needs boundary conditions (when NOT to use)
- Pair every abstract concept with concrete example
- Include diagnostic questions for practitioners
- Test against "can someone actually use this?" standard

### For Writing
- Query story library first (find 8+ vividness stories)
- Lead with narrative when possible
- Explain frameworks before applying them
- End with actionable insights

---

## Available Commands Quick Reference

**Setup**
- `/rk.constitution` - Create/update research principles
- `/rk.validate` - Validate work against constitution

**Question Development**
- `/rk.question` - Define and refine research question
- `/rk.evolve-question` - Create discipline-specific variants

**Research Planning**
- `/rk.identify-paths` - Find research traditions
- `/rk.filter-relevance` - Apply practical value filter
- `/rk.collect-documents` - Gather sources

**Active Research**
- `/rk.create-stream` - Start disciplinary stream
- `/rk.research` - Conduct systematic research
- `/rk.capture-story` - Capture vivid story
- `/rk.find-stories` - Query story library

**Synthesis & Writing**
- `/rk.frameworks` - Extract frameworks
- `/rk.cross-stream` - Find connections across streams
- `/rk.write` - Generate writing with stories + frameworks

---

## Next Steps

1. **Initialize ResearchKit**: Run `./researchkit/scripts/init-researchkit.sh`
2. **Create your first project**: Run `./researchkit/scripts/new-project.sh "your-topic"`
3. **Define your principles**: Run `/rk.constitution`
4. **Start researching**: Run `/rk.question`

For more details:
- [Command Reference](command-reference.md) - Detailed command documentation
- [Workflow Guide](workflow-guide.md) - Deep dive into each workflow stage
- [Examples](examples.md) - Sample projects and use cases

---

**Happy researching!** 🔬
