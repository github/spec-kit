---
description: Semantic search across code, specifications, and documentation to quickly locate relevant information
scripts:
  sh: scripts/bash/semantic-search.sh --json
  ps: scripts/powershell/semantic-search.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the user's natural language query from `$ARGUMENTS`.

## Goal

Enable fast, intelligent search across the entire project (code, specs, plans, AI docs) using natural language queries. Return ranked results with file locations and context.

## Execution Steps

### 1. Parse Search Query

Extract the search query from `$ARGUMENTS`. Examples:
- "Where is authentication handled?"
- "Find task validation logic"
- "Database schema for users"
- "API endpoints for projects"

### 2. Run Semantic Search Script

Execute `{SCRIPT}` with the query:

```bash
# Example: scripts/bash/semantic-search.sh --json "authentication handling"
```

Expected JSON output:
```json
{
  "query": "authentication handling",
  "results": [
    {
      "file": "src/auth/login.py",
      "line": 45,
      "type": "code",
      "context": "def authenticate(username, password):",
      "relevance": 95
    },
    {
      "file": "specs/002-user-auth/ai-doc.md",
      "line": 87,
      "type": "documentation",
      "context": "Authentication flow uses JWT tokens",
      "relevance": 85
    }
  ],
  "total_results": 12,
  "search_time_ms": 45
}
```

### 3. Display Ranked Results

Present results in clear, scannable format:

```
Search Results: "authentication handling"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 12 matches (showing top 5):

1. src/auth/login.py:45 (relevance: 95%)
   🔧 def authenticate(username, password):

2. specs/002-user-auth/ai-doc.md:87 (relevance: 85%)
   📝 Authentication flow uses JWT tokens

3. src/middleware/auth.ts:23 (relevance: 82%)
   🔧 export const authMiddleware = (req, res, next) =>

4. specs/002-user-auth/quick-ref.md:12 (relevance: 78%)
   📝 Entry point: src/auth/login.py:45

5. src/api/users.py:102 (relevance: 71%)
   🔧 @require_auth decorator applied

💡 Tip: Check quick-ref.md files first (lower token cost)
```

### 4. Provide Navigation Guidance

Based on search results, suggest efficient next steps:

**If quick-ref found:**
```
Quick Reference Available:
  specs/002-user-auth/quick-ref.md (~200 tokens)

Read this first for an overview, then dive into code if needed.
```

**If multiple locations found:**
```
Multiple Locations Found:
  Primary: src/auth/login.py (implementation)
  Docs: specs/002-user-auth/ai-doc.md (architecture)
  Tests: tests/test_auth.py (usage examples)

Suggested reading order: docs → primary → tests
```

## Search Strategy

The script uses a multi-layered approach:

### 1. Keyword Extraction
- Extract key terms from query
- Handle synonyms (e.g., "auth" → "authentication", "authorize")
- Remove stop words (the, is, are, etc.)

### 2. Search Locations (Priority Order)
1. **Quick refs** (high value, low token cost)
2. **AI docs** (comprehensive context)
3. **Specs** (requirements and design)
4. **Plans** (implementation details)
5. **Source code** (actual implementation)
6. **Tests** (usage examples)

### 3. Relevance Scoring
```
Score = keyword_matches × 40 +
        proximity_bonus × 30 +
        file_type_bonus × 20 +
        freshness_bonus × 10

keyword_matches: Number of query terms matched
proximity_bonus: Terms close together score higher
file_type_bonus: Quick refs > ai-doc > code
freshness_bonus: Recently modified files score higher
```

### 4. Context Extraction
- Show 1-2 lines before and after match
- Highlight matching terms
- Truncate long lines

## Common Use Cases

### Find Implementation
```bash
/speckit.find "task validation"
```
Returns: Validation functions, rules, tests

### Find Design Decisions
```bash
/speckit.find "why we chose PostgreSQL"
```
Returns: Plan/spec sections explaining choices

### Find Entry Points
```bash
/speckit.find "where to add new API endpoint"
```
Returns: API route definitions, patterns

### Find Examples
```bash
/speckit.find "how to create a task"
```
Returns: Tests, implementation examples

## Output Examples

### Single Clear Match
```
Search Results: "UserRepository class"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 1 exact match:

✓ src/repositories/user_repository.py:15
  class UserRepository:
      """Handles all user data operations"""

This is likely what you're looking for!
```

### Multiple Relevant Matches
```
Search Results: "task status update"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 8 matches across project:

📝 Documentation (2 matches):
  1. specs/001-tasks/quick-ref.md:8 - Task status flow
  2. specs/001-tasks/ai-doc.md:45 - Status update logic

🔧 Implementation (4 matches):
  3. src/models/task.py:67 - update_status() method
  4. src/api/tasks.py:123 - PATCH /tasks/:id/status
  5. src/services/task_service.py:89 - _transition_status()
  6. src/db/migrations/003_add_status.sql:5 - status column

🧪 Tests (2 matches):
  7. tests/test_task_model.py:45 - test_status_transition
  8. tests/test_task_api.py:78 - test_update_status_endpoint
```

### No Matches
```
Search Results: "blockchain integration"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No matches found.

This feature may not exist in the codebase yet.

Similar terms found:
  • "database integration" (6 matches)
  • "API integration" (3 matches)

Try broader terms or check if this feature is planned.
```

## Search Modifiers

### Limit Results
```bash
/speckit.find "validation" --limit 3
```
Shows only top 3 results

### Search Specific Type
```bash
/speckit.find "auth" --type code
/speckit.find "design decisions" --type docs
/speckit.find "usage" --type tests
```

### Search Specific Feature
```bash
/speckit.find "status update" --feature 001-tasks
```
Searches only within that feature's files

## Integration with Workflow

### Before Modifying Code
```bash
# Find where feature is implemented
/speckit.find "task dependencies"
# Returns: src/models/task.py:145

# Load quick ref for context
cat specs/006-task-dependencies/quick-ref.md

# Then read specific implementation
# Read src/models/task.py lines 140-160
```

### Understanding Architecture
```bash
# High-level understanding
/speckit.find "how does authentication work"
# Returns docs first, then code

# Load architecture from quick ref
# Then dive into specific components
```

### Finding Patterns
```bash
# Find similar code
/speckit.find "database query pattern"
# Returns multiple examples of DB queries

# Use most common pattern for new code
```

## Performance

- **Average search time**: 50-150ms for typical projects
- **Large projects (>1000 files)**: 200-500ms
- **Token cost**: ~2-5K tokens per search (includes results + context)
- **Optimization**: Caches file index for 5 minutes

## Limitations

### Current Version
- Keyword-based matching (not semantic AI)
- English queries only
- No fuzzy matching (exact keyword matches)
- Limited to project files (no external docs)

### Future Enhancements
- Embedding-based semantic search
- Multi-language support
- Fuzzy matching for typos
- Search across git history
- Search external documentation

## Context

{ARGS}
