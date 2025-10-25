# ResearchKit

A systematic framework for conducting rigorous, multi-disciplinary research and extracting actionable frameworks from complex topic areas.

## What is ResearchKit?

ResearchKit is a research workflow tool inspired by Spec-Driven Development principles. It provides a structured, constitutional approach to:

- **Refining research questions** from broad topics to precise, answerable questions
- **Identifying research paths** across multiple disciplines and traditions
- **Collecting and organizing** foundational texts and recent literature
- **Capturing vivid stories and anecdotes** alongside abstract concepts
- **Conducting multi-stream research** across different disciplinary perspectives
- **Extracting frameworks** that are both rigorous and practitioner-ready
- **Writing** that combines conceptual clarity with narrative power

## Core Philosophy

ResearchKit operates on the principle of **constitutional research**: a set of immutable methodological principles (your research constitution) governs all research activities, ensuring:

- **Multi-perspective analysis** across disciplines
- **Evidence-based reasoning** with clear provenance
- **Contradiction awareness** rather than premature synthesis
- **Framework extraction** that produces actionable insights
- **Practitioner readiness** for real-world application
- **Narrative evidence** alongside conceptual frameworks

## How It Works

ResearchKit uses a **layered workflow**:

```
Constitution (Research principles)
    ↓
Question Refinement (Broad → Precise)
    ↓
Research Path Identification (Disciplines, traditions, frameworks)
    ↓
Document Collection (Foundations + Recent work + Emerging concepts)
    ↓
Multi-Stream Research (Different disciplinary lenses)
    ├─→ Story Capture (Vivid, character-driven examples)
    └─→ Concept Extraction (Frameworks, models, insights)
    ↓
Synthesis (Cross-stream integration, frameworks)
    ↓
Writing (Evidence + Narrative)
```

Each layer builds on the previous one, with your constitution ensuring quality and consistency throughout.

## Quick Start

1. **Initialize ResearchKit** in your workspace:
   ```bash
   ./researchkit/scripts/init-researchkit.sh
   ```

2. **Create your first research project**:
   ```bash
   ./researchkit/scripts/new-project.sh "organizational-ai-transformation"
   ```

3. **Start your research workflow**:
   ```bash
   /rk.constitution    # Define your research principles
   /rk.question        # State your broad research question
   /rk.refine-question # Interactively refine to precise questions
   /rk.identify-paths  # Select research traditions and disciplines
   /rk.research        # Begin systematic research
   ```

See [Getting Started Guide](docs/getting-started.md) for detailed instructions.

## Directory Structure

### Tool Structure (ResearchKit itself)
```
researchkit/
├── templates/              # All template files
│   ├── commands/           # Command workflow templates
│   └── project/            # Document templates for projects
├── scripts/                # Helper scripts
├── .claude/commands/       # Claude Code command integration
├── docs/                   # Documentation
└── README.md               # This file
```

### Project Structure (Your research projects)
```
projects/001-your-research-topic/
├── constitution.md         # Research principles for this project
├── questions/              # Question evolution
│   ├── 00-original.md
│   ├── 01-refinement-options.md
│   └── 02-selected-questions.md
├── research-paths/         # Research traditions and approaches
│   ├── selection.md
│   └── paths/
│       ├── foundational-texts.md
│       └── recent-work.md
├── documents/              # Collected sources
│   ├── foundational/
│   ├── recent-reviews/
│   ├── supplementary/
│   └── download-queue.md
├── stories/                # Story library
│   ├── index.md
│   ├── meta/               # Individual story files
│   └── by-concept/         # Stories organized by concept
├── streams/                # Multi-disciplinary research
│   ├── [discipline-name]/
│   │   ├── question.md
│   │   ├── notes.md
│   │   └── concepts.md
├── synthesis/              # Cross-stream integration
│   ├── frameworks.md
│   ├── integration-map.md
│   └── contradictions.md
└── writing/                # Drafts and outlines
    ├── topics.md
    └── drafts/
```

## Available Commands

### Setup & Constitution
- `/rk.constitution` - Create or update research constitution
- `/rk.validate` - Validate research against constitutional principles

### Question Development
- `/rk.question` - Define initial broad research question
- `/rk.refine-question` - Generate refined question options (interactive)
- `/rk.evolve-question` - Create discipline-specific question variants

### Research Planning
- `/rk.identify-paths` - Identify research traditions and disciplines (interactive)
- `/rk.filter-relevance` - Apply practical relevance filters
- `/rk.collect-documents` - Find and organize source documents

### Active Research
- `/rk.create-stream` - Start new disciplinary research stream
- `/rk.research` - Conduct research in a stream
- `/rk.capture-story` - Capture vivid story/anecdote
- `/rk.find-stories` - Query story library

### Synthesis & Writing
- `/rk.frameworks` - Extract frameworks from research
- `/rk.cross-stream` - Find connections across research streams
- `/rk.write` - Generate writing with integrated stories and frameworks

See [Command Reference](docs/command-reference.md) for detailed usage.

## Key Features

### 1. Constitutional Research
Your research constitution defines immutable principles that govern all work. Like Spec Kit's constitutional approach to development, ResearchKit ensures methodological rigor through explicit, enforced principles.

### 2. Interactive Question Refinement
ResearchKit helps you move from vague, broad questions to precise, answerable ones through an interactive refinement process that highlights subtle differences between options.

### 3. Foundation-First Approach
For every research path, ResearchKit enforces identification of:
- Foundational/seminal texts
- Recent literature reviews
- Most-cited recent work
- Emerging concepts and frameworks

### 4. Story Library System
Capture vivid, character-driven stories during research with rich metadata:
- Vividness ratings (1-10)
- Emotional tone tagging
- Concept/framework linkage
- Source provenance
- Quick retrieval for writing

### 5. Multi-Stream Research
Conduct parallel research across different disciplines while maintaining:
- Stream-specific refined questions
- Shared document libraries
- Cross-stream concept mapping
- Contradiction tracking

### 6. Integrated Writing Support
When writing, ResearchKit automatically:
- Identifies relevant frameworks
- Suggests high-vividness stories
- Proposes narrative structures
- Maintains source citations

## Use Cases

ResearchKit is designed for:

- **Consultants** researching complex topics for client engagements
- **Writers** combining rigorous research with narrative storytelling
- **Academics** managing multi-disciplinary literature reviews
- **Strategists** extracting frameworks from diverse sources
- **Journalists** conducting deep investigative research
- **Thought leaders** synthesizing insights across domains

## Philosophy: Research as Software Development

ResearchKit applies software engineering principles to research:

- **Version control** for evolving questions and understanding
- **Modular architecture** through research streams
- **Quality gates** via constitutional validation
- **Documentation-first** with explicit artifact creation
- **Refactoring** of concepts and frameworks
- **Testing** ideas against multiple perspectives

## Documentation

- [Getting Started Guide](docs/getting-started.md) - Step-by-step setup and first project
- [Workflow Guide](docs/workflow-guide.md) - Detailed workflow explanations
- [Command Reference](docs/command-reference.md) - Complete command documentation
- [Examples](docs/examples.md) - Sample projects and use cases

## License

[Specify your license here]

## Contributing

ResearchKit is designed to be extensible. Contributions welcome for:
- New command templates
- Additional document templates
- Helper scripts and utilities
- Documentation improvements

---

**Built with principles inspired by [Spec Kit](https://github.com/githubresearch/spec-kit) - constitutional software development.**
