# /rk.capture-story - Capture Vivid Story or Anecdote

You are helping the user capture a vivid, character-driven story that illustrates research concepts.

## Context

During research, the user encounters compelling stories, anecdotes, or examples that bring abstract concepts to life. These stories are essential for writing that combines rigorous frameworks with emotional engagement and memorability.

Your job is to help capture these stories with rich detail and proper metadata for easy retrieval when writing.

## Your Task

### Step 1: Quick Capture (Guided Interview)

Guide the user through capturing the story by asking:

1. **"What's a one-sentence summary of this story?"**
   - Get the punchy essence

2. **"Tell me the full story with as much vivid detail as you can remember:"**
   - Specific people (names, ages, roles)
   - Specific moments (dates, times, places)
   - Direct quotes if available
   - Sensory details (what did it look/sound/feel like?)
   - Emotional context (how did people feel?)
   - What happened (concrete consequences)

3. **"Who are the key characters?"**
   - Main people/organizations involved
   - Their roles, motivations, characteristics

4. **"What's the emotional tone?"**
   - Tragic? Hopeful? Ironic? Inspiring? Cautionary? Surprising?
   - What should the reader feel?

5. **"What concept or framework does this illustrate?"**
   - What abstract idea does this story make concrete?
   - Can suggest concepts based on the story

6. **"Where did you find this story?"**
   - Full source citation
   - Document location (path to PDF/file)
   - Page number or timestamp
   - How was it accessed?

### Step 2: Rate Vividness

Score the story on vividness (1-10) using these criteria (1 point each):
- [ ] Specific person with name/role/age
- [ ] Specific date/time/location
- [ ] Direct quotes from participants
- [ ] Sensory details (visual, auditory, tactile)
- [ ] Emotional context (how people felt)
- [ ] Concrete consequences (what happened next)
- [ ] Surprising or counterintuitive element
- [ ] Character motivations clear
- [ ] Memorable image or moment
- [ ] Stakes are clear (what was at risk)

Total score = vividness rating

### Step 3: Identify Use Cases

Ask: "How might you use this story in writing?"

Suggest options:
- Opening/hook (grab attention immediately)
- Illustrating abstract concept (make theory concrete)
- Providing contrast (counterexample or alternative path)
- Building emotional connection (make reader care)
- Memorable conclusion (leave lasting impression)
- Case study (deep dive into application)

### Step 4: Create Story File

Using template at `researchkit/templates/project/story-template.md`, create:

`projects/[project-name]/stories/meta/[story-slug].md`

Where `[story-slug]` is a kebab-case version of the story name (e.g., `kodak-identity-crisis.md`)

Fill in all template sections:
- Story summary
- Full narrative
- Key characters
- Emotional tone
- What this illustrates (with [[concept]] links)
- Vividness rating (with checklist)
- Use cases
- Source (full citation)
- Collection metadata
- Tags

### Step 5: Update Story Index

Update `projects/[project-name]/stories/index.md`:

Add entry under:
- **By Vividness Rating** (in the appropriate tier: 8-10 / 5-7 / 1-4)
- **By Concept/Framework** (under relevant concept categories)
- **By Emotional Tone** (under relevant tone categories)

Update statistics:
- Total stories count
- High vividness count
- By stream count

### Step 6: Link to Concepts

If concept files exist (e.g., `streams/[stream-name]/concepts.md`), add reference:

Under the relevant concept section, add:
```markdown
### Illustrative Stories
- [[stories/meta/story-name]] (Vividness: X/10) - [One-line description]
  - Best for: [Use case]
```

### Step 7: Confirm and Suggest

Tell the user:
- "Story captured: `[story-name]`"
- "Vividness rating: X/10"
- "Tagged to concepts: [list]"
- "Stored in: `stories/meta/[story-slug].md`"

Suggest:
- "You can find this story later with `/rk.find-stories --concept [concept-name]`"
- "Continue research with `/rk.research --stream [stream-name]`"

## Guidelines for Story Capture

### What Makes a Story "Vivid" (High Ratings)

**Look for**:
- Specific people with names (not "an executive" but "Steve Sasson, age 24")
- Specific moments ("in 1975" not "a while ago")
- Direct quotes ("don't tell anyone about it" vs. paraphrased)
- Sensory details (toaster-sized, cassette tape, room went quiet)
- Irony or surprise (inventing your own obsolescence)
- Clear stakes (what was at risk)

**Avoid**:
- Generic summaries without detail
- Vague timelines
- Unnamed characters
- Abstract descriptions
- Stories without emotional weight

### Capturing from Different Sources

**From academic papers**:
- Often have case study boxes or examples
- May lack narrative detail - note what's missing
- Extract what's there, mark gaps for follow-up

**From books/articles**:
- Rich narrative detail usually available
- Note page numbers precisely
- Capture quotes exactly

**From interviews/conversations**:
- Get permission to use if not public
- Note who, when, where
- Capture exact words when possible

**From case studies**:
- Often detailed but may be anonymized
- Note which details are real vs. disguised
- Still capture vividly

## Story Library Architecture

Stories are stored with bidirectional linking:

```
Concept ←→ Story

When writing about a concept,
can query: "Show me stories tagged to this concept"

When you have a great story,
can tag: "This illustrates these concepts"
```

## File Locations

- Story files: `projects/[project-name]/stories/meta/[story-slug].md`
- Story index: `projects/[project-name]/stories/index.md`
- Story by concept: `projects/[project-name]/stories/by-concept/[concept-name].md`
- Template: `researchkit/templates/project/story-template.md`

## Important

- Stories are as important as concepts - they're how abstract ideas become memorable
- Capture stories DURING research, not when trying to write (you'll forget details)
- High-vividness stories (8-10) are candidates for lead stories
- Multiple stories for the same concept give writing flexibility
- Track source meticulously - journalistic integrity matters
- Tag liberally - easier to filter later than to remember connections

## Tips for the User

Remind the user:
- "The more vivid detail now, the easier writing later"
- "Direct quotes make stories memorable"
- "Names and dates add credibility"
- "The best stories often have irony or surprise"
- "Capture emotional tone explicitly - it guides writing later"
