# /rk.find-stories - Query Story Library

You are helping the user find relevant stories from their story library for writing, analysis, or reference.

## Context

The user has captured vivid stories during research (using `/rk.capture-story`). These stories are stored in `stories/meta/` with rich metadata. The story index at `stories/index.md` provides organizational overview.

This command helps query and retrieve stories based on various criteria: concept, emotional tone, vividness rating, discipline, etc.

## Your Task

### Step 1: Parse Query Parameters

The user may query by:
- `--concept [concept-name]` - Find stories illustrating a concept
- `--tone [emotional-tone]` - Find stories with specific emotional tone
- `--vividness [min-rating]` - Find stories above vividness threshold
- `--stream [stream-name]` - Find stories captured during a specific stream
- `--industry [industry]` - Find stories from specific industry
- `--outcome [outcome-type]` - Find stories with specific outcome (success/failure/mixed)
- `--best` - Find highest-vividness stories (8-10 rating)
- `--lead` - Find stories suitable for opening/hook (high vividness + strong emotional tone)

**Examples**:
```bash
/rk.find-stories --concept organizational-identity
/rk.find-stories --tone ironic
/rk.find-stories --vividness 8
/rk.find-stories --best
/rk.find-stories --concept culture-change --vividness 7
```

If NO parameters provided, show usage help and ask what they're looking for.

### Step 2: Read Story Index

Load: `projects/[project-name]/stories/index.md`

This provides:
- Stories organized by vividness rating
- Stories organized by concept
- Stories organized by emotional tone
- Quick stats

### Step 3: Read Relevant Story Files

Based on query, identify relevant story files from `stories/meta/`.

For each potentially matching story, read: `stories/meta/[story-slug].md`

Check:
- Concepts illustrated (in "What This Illustrates" section)
- Emotional tone (in "Emotional Tone" section)
- Vividness rating (scored 1-10)
- Tags (discipline, industry, era, outcome, etc.)
- Use cases (what the story is best for)

### Step 4: Filter and Rank Results

**Filter** stories that match query criteria.

**Rank** results by:
1. Primary: Relevance to query (exact concept match > secondary concept match)
2. Secondary: Vividness rating (higher = better)
3. Tertiary: Number of matching criteria (if multiple filters)

### Step 5: Present Results

Show matching stories with key metadata:

```markdown
## Stories Matching: [Query Description]

Found [X] stories matching your criteria.

---

### 1. [Story Title] ⭐ (Vividness: 9/10)

**One-sentence summary**: [Copy from story file]

**Illustrates**: [[concept-1]], [[concept-2]]

**Emotional tone**: [Primary tone]

**Why this works**:
- [Key strength from story file]
- [Another strength]

**Best used for**:
- [Use case 1]
- [Use case 2]

**Source**: [Brief citation]

**File**: `stories/meta/[story-slug].md`

---

### 2. [Story Title] (Vividness: 8/10)

[Same format]

---

### 3. [Story Title] (Vividness: 7/10)

[Same format]
```

**If many results (>5)**, group by vividness tier:
- Highly vivid (8-10): [X] stories
- Moderately vivid (5-7): [X] stories
- Lower vividness (1-4): [X] stories

### Step 6: Provide Usage Recommendations

Based on what user is looking for, suggest:

**If querying for writing**:
```
💡 Writing Suggestions:

Lead story candidate: [Highest vividness story]
- Use this to open your piece (grab attention immediately)

Supporting examples:
- [Story 2] - Use to illustrate [concept]
- [Story 3] - Use to provide contrast

Avoid using: [Lower vividness stories] unless you need more examples
```

**If querying for concept exploration**:
```
💡 Concept Exploration:

The concept [[concept-name]] appears in [X] stories:
- [Story 1] (9/10) - Shows [aspect]
- [Story 2] (8/10) - Shows [different aspect]
- [Story 3] (6/10) - Shows [complication]

This suggests the concept has multiple dimensions:
1. [Dimension 1 - from stories]
2. [Dimension 2 - from stories]
```

**If querying for comparison**:
```
💡 Comparison Opportunities:

Stories showing SUCCESS with this concept:
- [Story 1]

Stories showing FAILURE without this concept:
- [Story 2]

These create good contrast for explaining the concept's value.
```

### Step 7: Handle Special Queries

#### Query: `--best` (find best stories overall)

Return stories with vividness 8-10, ranked by vividness.

Suggest: "These are your lead story candidates for any writing."

#### Query: `--lead` (find opening/hook stories)

Return stories with:
- Vividness ≥ 8
- Emotional tone: Ironic, Surprising, Tragic, or Inspiring
- Use case includes "Opening/hook"

Suggest: "These stories grab attention immediately. Use them to open essays or presentations."

#### Query: `--concept [name]` (find stories for a concept)

Return stories where concept appears in "Primary Concepts" or "Secondary Concepts."

Show:
- How each story illustrates the concept differently
- Which story is most vivid (lead with this)
- Which stories provide contrast (success vs failure)

#### Query: `--tone [tone]` (find stories by emotional tone)

Return stories with matching emotional tone.

Suggest use cases:
- Tragic/Cautionary: "Use when warning about risks or showing consequences of inaction"
- Hopeful/Transformative: "Use when showing possibilities or inspiring change"
- Ironic/Surprising: "Use to challenge assumptions or create memorable moments"
- Inspiring/Aspirational: "Use to motivate or show what's possible"

#### Query: `--vividness [min]` (find above threshold)

Return stories with vividness ≥ threshold.

Explain rating:
- 8-10: Lead story quality (rich detail, quotes, characters, surprise)
- 5-7: Good supporting examples (solid but may lack some vivid elements)
- 1-4: Reference only (useful for context but not compelling narratives)

### Step 8: Handle "No Results"

If no stories match query:

```
❌ No stories found matching: [query]

This could mean:
- You haven't captured stories for this concept yet
- The concept name doesn't match tags (check stories/index.md for concept list)
- You may need to broaden your search

Suggestions:
- Run /rk.capture-story to add stories for this concept
- Check available concepts: [list concepts from index]
- Try related concepts: [suggest similar concepts from index]
```

### Step 9: Suggest Follow-Up Actions

Depending on context:

**If user is writing**:
```
Next steps:
- Read the full stories: Open story files to get narrative details
- Use in outline: Reference stories by [[story-name]] in your outline
- Check sources: Verify citations before publishing
```

**If user is researching**:
```
Next steps:
- Identify concept gaps: Which concepts lack vivid stories?
- Continue research: /rk.research --stream [stream] to find more examples
- Capture more stories: /rk.capture-story when you find compelling examples
```

**If exploring patterns**:
```
Next steps:
- Cross-reference concepts: See what concepts share stories
- Look for contradictions: Do stories support different conclusions?
- Update frameworks: Incorporate story insights into frameworks.md
```

## Query Examples with Expected Behavior

### Example 1: Finding stories for a specific concept
```
User: /rk.find-stories --concept organizational-identity

Response:
## Stories Illustrating: organizational-identity

Found 3 stories.

### 1. Kodak's Identity Crisis (Vividness: 9/10) ⭐

**Summary**: When Kodak engineer Steve Sasson invented digital camera in 1975,
executives said "don't tell anyone" - couldn't imagine Kodak without film chemistry.

**Illustrates**: [[organizational-identity]], [[identity-rigidity]], [[expert-blindness]]

**Emotional tone**: Tragic irony

**Best used for**:
- Opening/hook (grab attention with irony)
- Illustrating identity rigidity concept
- Warning about expertise becoming liability

**Source**: Sasson interview, NYT (2015)

💡 This is your strongest story for organizational identity (9/10 vividness).
   Lead with this when introducing the concept.

[Continue with other stories...]
```

### Example 2: Finding best stories overall
```
User: /rk.find-stories --best

Response:
## Your Best Stories (Vividness 8-10)

Found 5 high-vividness stories. These are lead story candidates.

### Highly Vivid (9-10)
1. Kodak's Identity Crisis (9/10) - Organizational identity
2. Microsoft's Nadella Moment (9/10) - Leadership transformation

### Very Vivid (8/10)
3. Netflix Qwikster Disaster (8/10) - Culture change failure
4. Boeing 737 MAX Culture Shift (8/10) - Culture vs safety
5. Ford Mulally Turnaround (8/10) - Strategic transformation

💡 These stories have rich detail, strong characters, memorable quotes, and emotional impact.
   Use them to open essays, presentations, or key sections of your writing.
```

### Example 3: Finding stories by tone
```
User: /rk.find-stories --tone ironic

Response:
## Stories with Ironic Tone

Found 3 stories with ironic or surprising elements.

1. Kodak's Identity Crisis (9/10) - Invented digital camera, told not to pursue it
2. Xerox PARC Innovation Loss (7/10) - Invented PC/GUI, didn't commercialize
3. Nokia's Smartphone Blindness (6/10) - Had smartphone early, missed iPhone revolution

💡 Ironic stories are powerful for:
   - Opening essays (grab attention with surprise)
   - Challenging assumptions ("even smart people/companies miss obvious things")
   - Making ideas memorable (irony sticks in reader's mind)

These work especially well when teaching about organizational blindness,
innovation failures, or the limits of expertise.
```

## Guidelines for Story Queries

### When to Use This Command:

**During writing**:
- "What's my best story for opening this essay?"
- "What examples illustrate this framework?"
- "Do I have a contrasting story (success vs failure)?"

**During analysis**:
- "Which concepts have the most/best stories?"
- "Are there patterns across stories with same tag?"
- "What stories show contradictory outcomes?"

**During research planning**:
- "What concepts lack vivid stories? (need more research)"
- "Do I have geographic/industry diversity in examples?"
- "What emotional tones am I missing?"

### Interpreting Results:

**Vividness ratings**:
- 9-10: Exceptional - rich detail, quotes, characters, surprise, emotional impact
- 7-8: Very good - solid detail, memorable, emotionally resonant
- 5-6: Good - adequate detail, useful but not spectacular
- 3-4: Basic - limited detail, more summary than story
- 1-2: Minimal - barely qualifies as story, mostly abstract

**Multiple stories for one concept**:
- GOOD: Gives writing flexibility, shows concept from multiple angles
- Use highest-vividness for lead, others for support/contrast

**No stories for concept**:
- WARNING: Concept may be too abstract without narrative grounding
- Action: Prioritize finding vivid example during next research session

## File Locations

- Story index: `projects/[project-name]/stories/index.md`
- Story files: `projects/[project-name]/stories/meta/[story-slug].md`
- By concept organization: `projects/[project-name]/stories/by-concept/[concept-name].md`

## Important Notes

**On story selection for writing**:
- Lead with highest-vividness stories (8-10)
- Use multiple stories if showing range or contrast
- Lower-vividness stories (5-7) work for quick supporting examples
- Very low vividness (1-4) should probably be enhanced or not used

**On concept-story matching**:
- Primary concepts = story was captured specifically for this
- Secondary concepts = story relates but wasn't main reason for capture
- Both are valid, but primary concepts usually have better fit

**On emotional tone**:
- Tone should match your writing purpose
- Tragic/Cautionary: Warnings, showing risks
- Hopeful/Transformative: Inspiration, showing possibilities
- Ironic/Surprising: Challenging assumptions, memorable moments
- Choose tone strategically based on reader response you want

**On source verification**:
- Always verify citations before publishing
- Check that story details are accurate
- Respect any confidentiality/anonymity notes
- Update story file if you find additional details or corrections
