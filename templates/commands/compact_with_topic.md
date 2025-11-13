---
description: Automatically analyze recent conversation topics and run /compact with intelligent focus
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This command enhances the `/compact` feature by automatically analyzing conversation history to identify key topics and generate an optimized compact focus area. Instead of manually determining what to preserve, this command intelligently extracts the conversation essence.

1. **Analyze Conversation History**: Review recent messages to identify:
   - Primary topics discussed
   - Key decisions made
   - Important context that should be preserved
   - Recurring themes

2. **Generate Smart Topic Summary**: Create a concise focus area that:
   - Captures the essence of the conversation
   - Identifies what must be preserved
   - Removes noise and tangential discussions

3. **Execute /compact Command**: Automatically invoke `/compact` with the generated focus

4. **Report Results**: Confirm compaction with preserved topics

## Execution Flow

### Phase 1: Conversation Analysis

**IMPORTANT**: This analysis happens BEFORE compaction. Review the last 30-50 messages (or user-specified window).

1. **Extract Key Topics**:

   For each message in the analysis window:
   - Identify main subjects discussed
   - Track technical decisions made
   - Note any explicit user requests or requirements
   - Identify file paths and code references
   - Extract error messages or debugging context

2. **Categorize Content**:

   ```text
   PRIMARY TOPICS: [Main subjects - e.g., "implementing authentication", "debugging CORS issue"]

   TECHNICAL DECISIONS: [Key choices - e.g., "using JWT tokens", "switched to PostgreSQL"]

   ACTIVE CONTEXT: [Current work - e.g., "refactoring UserService", "writing unit tests"]

   IMPORTANT REFERENCES: [Preserve - e.g., "API endpoint structure in api-spec.md", "error in line 42 of auth.py"]

   NOISE/TANGENTS: [Can drop - e.g., "off-topic discussion about tool preferences"]
   ```

3. **Identify Preservation Priorities**:

   **MUST PRESERVE** (high priority):
   - Unresolved issues or bugs
   - Recent technical decisions (last 10 messages)
   - Active implementation context
   - User's explicit requirements or constraints
   - File paths and code references from recent work

   **SHOULD PRESERVE** (medium priority):
   - General architectural decisions
   - Project constraints or conventions
   - Important links or references

   **CAN DROP** (low priority):
   - Resolved issues
   - Superseded approaches
   - Tangential discussions
   - Repetitive confirmations

### Phase 2: Focus Generation

Generate a compact, well-structured focus area that captures what matters:

```markdown
## Compact Focus: [Concise Title - 3-5 words]

### Primary Topics
- [Topic 1]: [Brief description]
- [Topic 2]: [Brief description]
[Max 3-4 primary topics]

### Key Context to Preserve
- **Current Work**: [What we're actively working on]
- **Technical Decisions**: [Recent architectural choices]
- **Active Issues**: [Unresolved problems or bugs]
- **Important References**: [File paths, docs, error messages]

### Can Drop
- [Resolved issues or superseded approaches]
- [Off-topic discussions]
```

**Example Focus Areas:**

```markdown
# Example 1: Feature Development
## Compact Focus: User Authentication Implementation

### Primary Topics
- JWT-based authentication system
- User registration and login flows
- Password hashing with bcrypt

### Key Context to Preserve
- **Current Work**: Implementing UserService in src/services/user_service.py
- **Technical Decisions**: Using JWT tokens (not sessions), bcrypt for passwords
- **Active Issues**: CORS error when calling /auth/login endpoint
- **Important References**: API spec in contracts/auth-api.json, error on line 42 of auth.py

### Can Drop
- Initial discussion about OAuth vs JWT (decision already made)
- Fixed TypeError in validation logic (resolved)
```

```markdown
# Example 2: Debugging Session
## Compact Focus: CORS and API Integration Issues

### Primary Topics
- CORS configuration problems
- API endpoint connectivity
- Environment variable setup

### Key Context to Preserve
- **Current Work**: Fixing CORS errors blocking frontend-backend communication
- **Technical Decisions**: Using CORS middleware with specific origin whitelist
- **Active Issues**: Preflight OPTIONS requests failing on /api/users endpoint
- **Important References**: CORS config in src/middleware/cors.py, frontend calling from localhost:3000

### Can Drop
- Earlier discussion about API design patterns (not relevant to current bug)
- Successful test cases (focus on failing ones)
```

### Phase 3: Execute Compact

1. **Prepare Compact Command**:

   Format the focus area for optimal preservation:
   ```text
   /compact Preserve context about [PRIMARY_TOPICS].
   Keep: [KEY_CONTEXT_BULLETS].
   Current work: [ACTIVE_WORK].
   Can drop: [TANGENTS_AND_RESOLVED].
   ```

2. **Invoke /compact**:

   Execute the agent's `/compact` command with the generated focus.

   > **Note:** The `/compact` command may not be available in all AI agents or environments. If `/compact` is not supported, manually summarize and condense the conversation using the generated focus area above, or consult your agent's documentation for equivalent compaction functionality.

3. **Verify Compaction**:

   After compaction, briefly confirm:
   - Topics preserved
   - Estimated context reduction
   - Any critical information that might need restating

## Guidelines for Topic Analysis

### What Makes a "Topic"?

A topic is a **coherent thread of discussion** with clear technical content:

- ✅ **VALID TOPICS**:
  - "Implementing user authentication with JWT"
  - "Debugging CORS errors in API calls"
  - "Refactoring database schema for performance"
  - "Setting up CI/CD pipeline with GitHub Actions"

- ❌ **NOT TOPICS** (too vague or meta):
  - "Discussing the code"
  - "Working on the project"
  - "Asking questions"
  - "General development"

### Noise Detection

Identify and exclude from focus:

- **Greetings and pleasantries**: "Thanks!", "Sounds good", "Let's get started"
- **Process discussions**: "Should we use X or Y?" (after decision made)
- **Tool troubleshooting**: "Command failed" → "Fixed typo" (if resolved)
- **Superseded approaches**: "Initially tried X" (when now using Y)
- **Repetitive confirmations**: Multiple "okay", "understood", "correct" messages

### Context Density

Aim for **high information density** in the focus area:

- **GOOD** (specific): "JWT token expiry set to 7 days, refresh tokens in Redis"
- **BAD** (vague): "Discussed authentication settings"

- **GOOD** (actionable): "CORS error on OPTIONS /api/users - need to add preflight handling"
- **BAD** (generic): "Having some API issues"

## Special Cases

### Case 1: User Provides Explicit Focus (via ARGUMENTS)

If user provides specific focus in `$ARGUMENTS`:

```text
User: /compact_with_topic Keep only the database migration discussion
```

**Action**:
1. Acknowledge user's specified focus
2. Scan conversation for that specific topic
3. Generate focus area centered on user's request
4. Add any critical related context not mentioned by user
5. Execute compact with combined focus

### Case 2: Multiple Distinct Topics (Branching Discussion)

If conversation covers 3+ unrelated topics:

```markdown
## Compact Focus: Multiple Active Threads

### Topic 1: [Name] - [Priority: HIGH/MEDIUM]
- [Key points]

### Topic 2: [Name] - [Priority: HIGH/MEDIUM]
- [Key points]

### Can Drop
- [Resolved or low-priority items]
```

**Prioritization**:
- HIGH: Active work, unresolved issues
- MEDIUM: Important but not immediately blocking
- Drop: Resolved, tangential, or superseded

### Case 3: Primarily Debugging/Troubleshooting

For conversations dominated by error resolution:

```markdown
## Compact Focus: [Error/Issue Name]

### Problem
- [Error description and context]

### Solutions Attempted
- [What didn't work - can often drop]
- [What worked - KEEP]

### Current Status
- [Where we are now]
- [Next steps if unresolved]

### References
- [File paths, line numbers, error messages]
```

### Case 4: Long Exploratory Discussion

For conversations exploring options or learning:

```markdown
## Compact Focus: [Exploration Topic]

### Final Decision
- [What was decided - HIGH priority]

### Key Learnings
- [Important insights to remember]

### Exploration History (Can Drop)
- [Initial ideas that were rejected]
- [Alternatives considered and dismissed]
```

## Error Handling

- **If conversation too short** (<10 messages):
  - WARN "Conversation history is brief. Compaction may not be necessary."
  - Ask user: "Do you still want to compact? (y/n)"

- **If cannot identify clear topics**:
  - Present conversation summary to user
  - Ask: "What would you like to preserve in the compact?"
  - Use user's response as focus

- **If /compact command fails**:
  - ERROR "Compaction failed: [reason]"
  - Provide the generated focus area for user to manually run `/compact`

## Output Format

After successful compaction:

```markdown
# ✅ Compacted Conversation

## Preserved Topics
1. [Topic 1]
2. [Topic 2]
3. [Topic 3]

## Context Reduction
- Messages before: [N]
- Estimated context saving: ~[X]%

## Preserved Key Information
- [Bullet list of critical context that was kept]

## What Was Dropped
- [General categories of removed content]

---

You can now continue the conversation with reduced context overhead while maintaining essential information about [topics].
```

## Usage Examples

### Example 1: Feature Development

```bash
User: /compact_with_topic
```

**Analysis Result**:
```
Primary Topics: User authentication, JWT implementation, database schema
Active Context: Implementing login endpoint in auth.py
Key Issues: CORS error on /auth/login, password hashing question
Noise: Initial discussion about OAuth (decision made), greeting messages
```

**Generated Focus**:
```
Preserve context about JWT authentication implementation.
Keep: login endpoint in auth.py, CORS error on /auth/login endpoint, bcrypt password hashing decision, database User model schema.
Current work: debugging CORS preflight for authentication endpoints.
Can drop: OAuth exploration (chose JWT instead), resolved validation errors.
```

### Example 2: User-Specified Focus

```bash
User: /compact_with_topic Keep only the API design discussion
```

**Analysis Result**:
```
Scanning for "API design" topic...
Found: REST endpoint structure, versioning strategy, error response format
Related: OpenAPI spec file location (will include)
```

**Generated Focus**:
```
Preserve context about API design decisions.
Keep: REST endpoint structure with /api/v1 prefix, error response format (code, message, details), OpenAPI spec at contracts/api-spec.json.
Current work: documenting API conventions.
Can drop: everything not related to API design patterns.
```

### Example 3: Debugging Session

```bash
User: /compact_with_topic
```

**Analysis Result**:
```
Primary Topics: CORS errors, database connection issues
Active Context: Fixing CORS middleware in src/middleware/cors.py
Resolved: Database timeout (fixed by connection pooling)
Still Open: Preflight OPTIONS requests failing
```

**Generated Focus**:
```
Preserve context about CORS debugging.
Keep: Preflight OPTIONS requests failing on /api/users, CORS middleware config in src/middleware/cors.py line 15-23, frontend origin localhost:3000.
Current work: debugging why OPTIONS requests return 404.
Can drop: database connection timeout (already fixed with pooling), initial CORS setup discussion.
```

## Best Practices

1. **Be Specific**: Focus areas should be immediately actionable
2. **Preserve Recent**: Last 5-10 messages usually most important
3. **Keep Unresolved**: Any open issues must be preserved
4. **Drop Resolved**: Closed issues can usually be dropped
5. **Maintain File Paths**: Always preserve specific file/line references
6. **Context Over Conversation**: Preserve technical context, not conversational flow
7. **User Intent First**: If user specifies focus, honor it while adding critical context

## Final Notes

- This command is **destructive** - it reduces conversation history
- Run only when context window is becoming constrained
- Generated focus aims for ~70-80% context reduction while keeping 100% of essential information
- Can be run multiple times as conversation evolves
- Consider running after major topic shifts or when conversation exceeds 100+ messages
