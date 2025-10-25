#!/bin/bash
# new-project.sh - Create a new ResearchKit project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCHKIT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if project name provided
if [ -z "$1" ]; then
    echo "Usage: $0 <project-name>"
    echo ""
    echo "Example: $0 organizational-ai-transformation"
    echo "         $0 'corporate culture change'"
    exit 1
fi

PROJECT_NAME="$1"

# Convert to kebab-case (lowercase, spaces to hyphens)
PROJECT_SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')

# Check if projects directory exists
if [ ! -d "projects" ]; then
    echo "❌ Error: projects/ directory not found."
    echo "Run ./researchkit/scripts/init-researchkit.sh first"
    exit 1
fi

# Find next project number
NEXT_NUM=1
if [ -d "projects" ]; then
    LAST_NUM=$(ls -d projects/[0-9]* 2>/dev/null | sed 's/projects\///' | sed 's/-.*//' | sort -n | tail -1)
    if [ ! -z "$LAST_NUM" ]; then
        NEXT_NUM=$((LAST_NUM + 1))
    fi
fi

# Format project number with leading zeros (e.g., 001)
PROJECT_NUM=$(printf "%03d" $NEXT_NUM)

# Full project directory name
PROJECT_DIR="projects/${PROJECT_NUM}-${PROJECT_SLUG}"

echo "🔬 Creating new ResearchKit project..."
echo ""
echo "Project: $PROJECT_NAME"
echo "Location: $PROJECT_DIR"
echo ""

# Check if already exists
if [ -d "$PROJECT_DIR" ]; then
    echo "❌ Error: Project directory already exists: $PROJECT_DIR"
    exit 1
fi

# Create directory structure
echo "📁 Creating directory structure..."

mkdir -p "$PROJECT_DIR"/{questions,research-paths/paths,documents/{foundational,recent-reviews,supplementary},stories/{meta,by-concept},streams,synthesis,writing/drafts}

# Create .gitkeep files for empty directories
touch "$PROJECT_DIR"/documents/foundational/.gitkeep
touch "$PROJECT_DIR"/documents/recent-reviews/.gitkeep
touch "$PROJECT_DIR"/documents/supplementary/.gitkeep
touch "$PROJECT_DIR"/stories/meta/.gitkeep
touch "$PROJECT_DIR"/stories/by-concept/.gitkeep
touch "$PROJECT_DIR"/streams/.gitkeep
touch "$PROJECT_DIR"/writing/drafts/.gitkeep

# Create initial story index
echo "📚 Creating story index..."
cat > "$PROJECT_DIR"/stories/index.md <<EOF
# Story Library Index

**Project**: $PROJECT_NAME
**Created**: $(date +%Y-%m-%d)

---

## By Vividness Rating

### Highly Vivid (8-10) - Lead story candidates
[Stories will appear here as you capture them]

### Moderately Vivid (5-7) - Supporting examples
[Stories will appear here as you capture them]

### Lower Vividness (1-4) - Background/reference
[Stories will appear here as you capture them]

---

## By Concept/Framework

[Concepts will appear here as you extract them]

---

## By Emotional Tone

### Tragic/Cautionary
[Stories will appear here]

### Hopeful/Transformative
[Stories will appear here]

### Ironic/Surprising
[Stories will appear here]

### Inspiring/Aspirational
[Stories will appear here]

---

## Quick Stats

- **Total stories**: 0
- **High vividness (8+)**: 0
- **By stream**: [Will be populated as streams are created]

---

## Usage

Capture new stories with: \`/rk.capture-story\`

Find stories with: \`/rk.find-stories --concept [concept-name]\`
EOF

# Create download queue
echo "📥 Creating download queue..."
cat > "$PROJECT_DIR"/documents/download-queue.md <<EOF
# Document Download Queue

**Project**: $PROJECT_NAME

---

## Documents Needing Manual Download

[Items will appear here when /rk.collect-documents finds paywalled sources]

Format:
- [ ] **Author (Year)** - "Title"
  - Source: [Journal/Publisher]
  - Reason: [Behind paywall / Library access needed / etc.]
  - Priority: [High / Medium / Low]
  - Save to: [foundational / recent-reviews / supplementary]

---

## Downloaded Documents

[Move items here once downloaded]

- [x] **Example (2024)** - "Example Title"
  - Saved to: documents/foundational/example-2024.pdf

---

## Unable to Obtain

[Items that cannot be accessed]

- [ ] **Example (2020)** - "Example Title"
  - Reason: [Not available / Too expensive / etc.]
  - Alternative: [Summary or related work]
EOF

# Create README for the project
echo "📝 Creating project README..."
cat > "$PROJECT_DIR"/README.md <<EOF
# Research Project: $PROJECT_NAME

**Project ID**: ${PROJECT_NUM}
**Created**: $(date +%Y-%m-%d)
**Status**: Setup

---

## Project Structure

\`\`\`
${PROJECT_NUM}-${PROJECT_SLUG}/
├── constitution.md          # Research principles (run /rk.constitution)
├── questions/               # Question development
├── research-paths/          # Research traditions and disciplines
├── documents/               # Collected sources (PDFs, papers)
├── stories/                 # Story library
├── streams/                 # Multi-disciplinary research streams
├── synthesis/               # Cross-stream integration
└── writing/                 # Drafts and outlines
\`\`\`

---

## Getting Started

1. **Define research principles**: \`/rk.constitution\`
2. **Articulate your question**: \`/rk.question\`
3. **Identify research paths**: \`/rk.identify-paths\`
4. **Begin research**: \`/rk.create-stream\` then \`/rk.research\`

---

## Current Status

- [ ] Constitution created
- [ ] Research question defined
- [ ] Research paths identified
- [ ] Documents collected
- [ ] Research streams active
- [ ] Frameworks extracted
- [ ] Writing begun

---

## Notes

[Add project-specific notes here]
EOF

echo ""
echo "✅ Project created: $PROJECT_DIR"
echo ""
echo "Next steps:"
echo "  1. Define research principles: /rk.constitution"
echo "  2. Define your research question: /rk.question"
echo ""
echo "Project structure:"
echo "  $PROJECT_DIR/"
echo "  ├── constitution.md       (Create with /rk.constitution)"
echo "  ├── questions/            (Populated by /rk.question)"
echo "  ├── research-paths/       (Populated by /rk.identify-paths)"
echo "  ├── documents/            (PDFs and sources)"
echo "  ├── stories/              (Story library)"
echo "  ├── streams/              (Research by discipline)"
echo "  ├── synthesis/            (Frameworks and integration)"
echo "  └── writing/              (Drafts)"
echo ""
