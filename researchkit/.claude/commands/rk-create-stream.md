# /rk.create-stream - Create Disciplinary Research Stream

You are helping the user create a new research stream - a disciplinary or thematic lens through which to examine their research question.

## Context

Complex research questions often require multiple perspectives. A "research stream" is a focused investigation through a specific disciplinary lens (e.g., psychology, finance, strategy) or thematic lens (e.g., leadership, culture, technology).

Each stream has its own refined question, notes, and concept extraction, but all streams share the same document library and contribute to cross-stream synthesis.

## Your Task

### Step 1: Get Stream Parameters

**Ask the user**:
1. "What discipline or theme should this stream focus on?"
   - Examples: psychology, finance, strategy, culture, leadership, technology
   - Validate it's specific enough (not just "business" or "management")

2. "What's the refined research question for this stream?"
   - Should be a variant of the main question, adapted for this disciplinary lens
   - If user is unsure, help them refine from main question

**Example**:

Main question: "How do organizations balance continuity and adaptation during tech change?"

Psychology stream question: "How do people maintain a sense of belonging when organizational mission shifts due to technology?"

Finance stream question: "How can CFOs account for intangible cultural value during technological transformation?"

Strategy stream question: "How do firms reconfigure resources and capabilities during technological disruption?"

### Step 2: Check if Stream Already Exists

Check if `projects/[project-name]/streams/[stream-slug]/` already exists.

If YES:
- Warn user: "Stream '[stream-name]' already exists. Do you want to:"
  - "1. Use the existing stream"
  - "2. Create a new variant (e.g., 'psychology-2')"
  - "3. Cancel"

If NO: Proceed

### Step 3: Create Stream Directory Structure

Create:
```
projects/[project-name]/streams/[stream-slug]/
├── question.md
├── notes.md
├── concepts.md
└── relevant-docs.md
```

### Step 4: Create question.md

Create: `projects/[project-name]/streams/[stream-slug]/question.md`

**Content**:
```markdown
# Research Stream: [Stream Name]

**Discipline/Theme**: [Discipline]
**Created**: [DATE]
**Status**: Active

---

## Stream-Specific Question

[The refined question for this disciplinary lens]

---

## Relationship to Main Question

**Main research question**: [Copy from questions/02-selected-questions.md]

**How this stream differs**:
- [Explain what makes this stream's question distinctive]
- [What aspect of the main question does this stream address?]
- [What disciplinary concepts/theories does this bring to bear?]

---

## Key Concepts to Explore (Initial)

[Based on the stream's discipline, what concepts are likely relevant?]

**Psychology stream examples**:
- Organizational identity
- Psychological safety
- Meaning-making
- Belonging and inclusion
- Resistance to change

**Finance stream examples**:
- Intangible asset valuation
- Real options theory
- Risk assessment
- Capital allocation
- Financial signaling

**Strategy stream examples**:
- Dynamic capabilities
- Resource reconfiguration
- Competitive positioning
- Strategic renewal
- Business model innovation

[Customize for the user's specific stream]

---

## Success Criteria

This stream will be considered "complete" when:
- [ ] At least 5 foundational sources read and notes captured
- [ ] 3-5 core concepts extracted with definitions
- [ ] At least 2 vivid stories captured
- [ ] Connections to other streams identified
- [ ] Contribution to synthesis documented

---

## Related Research Paths

[Link to relevant research paths from research-paths/paths/]

**Relevant paths for this stream**:
- [[research-path-1]] - [Why relevant]
- [[research-path-2]] - [Why relevant]

---

## Evolution Log

As understanding deepens, this question may evolve. Document changes here:

### [DATE]: [CHANGE_DESCRIPTION]
**From**: [Original question]
**To**: [Revised question]
**Reason**: [What insight prompted this evolution]
```

### Step 5: Create notes.md

Create: `projects/[project-name]/streams/[stream-slug]/notes.md`

**Content**:
```markdown
# Research Notes: [Stream Name]

**Stream Question**: [Copy stream question]

---

## Reading Log

[Track what you've read in this stream]

### [DATE] - [Source Name]
**Source**: [Full citation]
**Location**: [Path to document if applicable]
**Relevance**: [HIGH / MEDIUM / LOW]

#### Key Takeaways
- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

#### Concepts Identified
- [[concept-name-1]] - [Brief description]
- [[concept-name-2]] - [Brief description]

#### Stories/Examples
- [Brief note about any stories to capture with /rk.capture-story]

#### Questions Raised
- [What questions did this reading raise?]
- [What should you explore next?]

#### Connections to Other Streams
- [Any insights relevant to other disciplinary streams?]

---

## Synthesis Notes

[As patterns emerge across multiple readings, capture them here]

### Emerging Theme 1: [Theme Name]

**What**: [What is this theme?]

**Evidence**: [Which sources support this?]
- [Source 1] - [How it supports]
- [Source 2] - [How it supports]

**Contradictions**: [Any sources that contradict or complicate this theme?]

---

## Questions for Further Research

[What do you still need to understand?]

- [ ] [Question 1]
- [ ] [Question 2]
- [ ] [Question 3]

---

## Dead Ends / Unhelpful Paths

[Track what you've explored that didn't pan out - saves time later]

- [Path 1] - [Why it wasn't useful]
- [Path 2] - [Why it wasn't useful]
```

### Step 6: Create concepts.md

Create: `projects/[project-name]/streams/[stream-slug]/concepts.md`

**Content**:
```markdown
# Key Concepts: [Stream Name]

**Stream Question**: [Copy stream question]

---

## Concept Registry

[As you identify important concepts during research, document them here]

### Concept 1: [CONCEPT_NAME]

**Definition**: [Clear, concise definition]

**Foundational Source(s)**:
- [Author (Year)] - [Where this concept was introduced or defined]

**Why It Matters**: [Relevance to research question]

**Related Concepts**:
- [[concept-2]] - [How they relate]
- [[concept-from-other-stream]] - [Cross-stream connection]

**Illustrative Stories**:
- [[story-name]] (Vividness: X/10) - [How this story illustrates the concept]
- [Note if no stories yet captured]

**Contradictions / Complications**:
- [Are there debates about this concept?]
- [Do sources disagree on how to understand it?]

**Practical Application**:
- [How would a practitioner use this concept?]
- [What decisions does this inform?]

---

### Concept 2: [CONCEPT_NAME]

[Same structure as above]

---

## Concept Map

[As concepts accumulate, describe relationships]

**Core concepts** (fundamental to this stream):
- [[concept-1]]
- [[concept-2]]

**Supporting concepts** (important but secondary):
- [[concept-3]]
- [[concept-4]]

**Peripheral concepts** (mentioned but less central):
- [[concept-5]]

**Relationships**:
- [[concept-1]] → [[concept-2]] (Concept 1 enables/causes Concept 2)
- [[concept-2]] ↔ [[concept-3]] (These are in tension)
- [[concept-4]] → [[concept-5]] (Concept 4 is a special case of Concept 5)

---

## Cross-Stream Concept Connections

[Which concepts appear in multiple streams?]

### [CONCEPT_NAME] appears in:
- **This stream ([stream-name])**: [How it's understood here]
- **[[other-stream]]**: [How it's understood there]
- **Synthesis**: [What do we learn from seeing this concept from multiple angles?]

---

## Gaps & Questions

[What concepts are missing? What do you still need to understand?]

- [ ] [Gap 1]
- [ ] [Gap 2]
```

### Step 7: Create relevant-docs.md

Create: `projects/[project-name]/streams/[stream-slug]/relevant-docs.md`

**Content**:
```markdown
# Relevant Documents: [Stream Name]

**Stream Question**: [Copy stream question]

---

## Documents from Research Paths

[Link to documents identified in research paths that are relevant to this stream]

### From [[research-path-1]]

**Foundational**:
- [ ] [Author (Year)] - [Title]
  - Location: `documents/foundational/[filename].pdf`
  - Priority: [HIGH / MEDIUM / LOW]
  - Why relevant to this stream: [Explanation]

**Recent Work**:
- [ ] [Author (Year)] - [Title]
  - Location: `documents/recent-reviews/[filename].pdf`
  - Priority: [HIGH / MEDIUM / LOW]
  - Why relevant: [Explanation]

---

## Stream-Specific Documents

[Documents found specifically for this stream, not listed in research paths]

- [ ] [Author (Year)] - [Title]
  - How found: [Search / Recommendation / Citation chain]
  - Status: [Downloaded / In queue / Unavailable]
  - Why relevant: [Explanation]

---

## Reading Priority

[Suggested reading order for this stream]

### Phase 1: Foundational (Read first)
1. [Document 1] - [Why start here]
2. [Document 2] - [Why second]

### Phase 2: Recent Synthesis (After foundations)
1. [Recent review 1]
2. [Recent review 2]

### Phase 3: Deep Dives (After understanding basics)
1. [Specialized document 1]
2. [Specialized document 2]

---

## Documents Read (Checklist)

- [x] [Document 1] - Read [DATE]
- [ ] [Document 2] - Not yet read
- [ ] [Document 3] - Not yet read
```

### Step 8: Link to Research Paths

Read: `projects/[project-name]/research-paths/paths/*.md`

Identify which research paths are relevant to this stream and:
- Update `relevant-docs.md` with documents from those paths
- List paths in `question.md` under "Related Research Paths"

### Step 9: Update Story Index

Update: `projects/[project-name]/stories/index.md`

Add stream to stats:
```markdown
## Quick Stats
- Total stories: [X]
- High vividness (8+): [X]
- By stream:
  - [existing-stream]: [X] stories
  - [new-stream]: 0 stories  ← ADD THIS
```

### Step 10: Update Project README

Update: `projects/[project-name]/README.md`

Add to status section:
```markdown
## Active Research Streams

- [[streams/[stream-slug]]] - [Stream Name] ([Discipline])
  - Question: [One-line question]
  - Status: [Just started / Active / Near complete]
  - Documents read: [X] of [Y]
  - Stories captured: [X]
  - Concepts extracted: [X]
```

### Step 11: Suggest Next Steps

Tell user:
```
✅ Research stream created: [Stream Name]

Stream directory: streams/[stream-slug]/
- question.md      - Stream-specific research question
- notes.md         - Reading notes and synthesis
- concepts.md      - Concept extraction
- relevant-docs.md - Document tracking

Next steps:
1. Review relevant documents: streams/[stream-slug]/relevant-docs.md
2. Start reading and taking notes: /rk.research --stream [stream-slug]
3. Capture stories as you find them: /rk.capture-story
4. Extract concepts: Update streams/[stream-slug]/concepts.md

Suggested reading priority listed in relevant-docs.md
```

## Guidelines for Stream Creation

### Good Streams Are:
- **Focused**: Clear disciplinary or thematic lens
- **Distinctive**: Asks a different question than other streams
- **Bounded**: Scope is manageable (not "all of psychology")
- **Relevant**: Clearly contributes to answering main question
- **Complementary**: Adds perspective not covered by other streams

### Stream Naming:
- Use discipline name if disciplinary (psychology, finance, strategy)
- Use theme name if thematic (leadership, culture, technology)
- Keep lowercase, hyphenated (psychology-stream → psychology)
- Be specific (not "business" but "strategic-management")

### Number of Streams:
- **Minimum**: 2 (need multiple perspectives per constitution)
- **Optimal**: 3-5 (enough diversity, not overwhelming)
- **Maximum**: 7 (beyond this, synthesis becomes very hard)

### For Different Research Styles:
- **Deep single-discipline**: May only need 1-2 streams
- **Multi-disciplinary synthesis**: 3-5 streams
- **Comprehensive literature review**: 5-7 streams

### Stream Questions:
- Must be specific to the disciplinary lens
- Should be answerable within that discipline
- Can use discipline-specific terminology
- Should still connect to main question

## Constitutional Validation

Check constitution for:
- **Article I (Multi-Perspective)**: Creating streams enforces this
- Ensure at least 3 streams total (or document why fewer)
- Each stream should represent distinct perspective

## Important Notes

**On stream evolution**:
- Stream questions may evolve as understanding deepens
- Document evolution in question.md evolution log
- Evolving questions is normal and good

**On cross-stream work**:
- Concepts that appear in multiple streams are especially important
- Note cross-stream connections in concepts.md
- Save full synthesis for /rk.cross-stream command later

**On documents**:
- Streams share the same document library (documents/)
- relevant-docs.md just tracks which docs are relevant to THIS stream
- Same document may be relevant to multiple streams

## File Locations

- Stream directory: `projects/[project-name]/streams/[stream-slug]/`
- Question file: `streams/[stream-slug]/question.md`
- Notes file: `streams/[stream-slug]/notes.md`
- Concepts file: `streams/[stream-slug]/concepts.md`
- Relevant docs: `streams/[stream-slug]/relevant-docs.md`
