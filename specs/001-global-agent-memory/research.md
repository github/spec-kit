# Research Findings: Global Agent Memory Integration

> **Generated**: 2025-03-10  
> **Status**: Complete

---

## 1. agent-memory-mcp Integration

### Source: GitHub Analysis
**Repository**: https://github.com/ipiton/agent-memory-mcp  
**Language**: Go  
**License**: MIT

### Key Findings

**MCP Protocol**:
- **Transport**: stdio (default) or HTTP/JSON-RPC
- **Configuration**: Environment variables
- **Detection**: Check for binary in PATH or MCP client config

**CLI Mode** (critical for integration):
```bash
# Can be used WITHOUT MCP client
agent-memory-mcp store -content "..." -type procedural -tags "go,chi"
agent-memory-mcp recall "router middleware"
agent-memory-mcp list -type procedural
agent-memory-mcp search "authentication flow"
agent-memory-mcp stats -json
```

**Graceful Fallback** (already built-in):
- Jina AI (primary) → OpenAI (fallback) → Ollama (local fallback)
- Automatic provider switching on failure
- All produce 1024-dimensional vectors

### Decision: Use CLI mode

**Rationale**: CLI mode allows direct integration without MCP client dependency. Graceful fallback already implemented.

**Alternatives Considered**:
- MCP stdio mode: Requires MCP client, adds complexity
- MCP HTTP mode: Requires HTTP server running
- **CLI mode chosen**: Simpler, works standalone, existing fallback logic

---

## 2. SkillsMP Web Scraping

### Source: SkillsMP.com Analysis
**URL**: https://skillsmp.com  
**Total Skills**: 425,573 (and growing)  
**Quality Filter**: Minimum 2 GitHub stars

### Key Findings

**Site Structure**:
- **Type**: React/TypeScript SPA
- **Content**: Loaded dynamically from JSON APIs
- **Categories**: Organized by use case
- **Search**: AI semantics + keyword search

### Decision: GitHub API + SkillsMP Hybrid

**Rationale**:
- SkillsMP has no official API
- GitHub API is stable, rate-limited (5000/hour authenticated)
- SkillsMP as backup/enrichment source
- Local cache to reduce API calls

**Rate Limiting**:
- GitHub API: 5000 requests/hour (authenticated)
- Implement exponential backoff
- Cache results locally (SQLite)

---

## 3. Ollama Embeddings API

### Source: Ollama Documentation
**Endpoint**: POST /api/embed  
**Base URL**: http://localhost:11434

### Key Findings

**API Format**:
```bash
curl http://localhost:11434/api/embed -d '"model": "mxbai-embed-large", "input": "text"'
```

**Batch Support**: Yes (array of strings)
**Rate Limits**: None documented (local service)
**Recommended Model**: mxbai-embed-large (1024d, best for Russian)

### Decision: Direct HTTP API

**Rationale**:
- Simple HTTP POST
- No authentication required (local)
- Batch support for efficiency
- Graceful fallback: if Ollama unavailable → skip vector memory

---

## 4. File Watching (Cross-Platform)

### Research: Existing Libraries

**Decision: Use watchdog library**

**Rationale**:
- Mature, cross-platform
- Active maintenance
- Simple API
- Handles edge cases (duplicate events, etc.)

---

## 5. Library Decisions Summary

| Component | Library/Approach | Why Chosen |
|-----------|-----------------|-------------|
| Vector Memory | agent-memory-mcp CLI | Existing graceful fallback, CLI mode |
| Ollama Embeddings | requests (HTTP) | Simple, standard library |
| SkillsMP Search | GitHub API + watchdog | Stable API, rate-limited |
| File Watching | watchdog | Cross-platform, mature |
| Config Management | Custom (backup+merge) | Project-specific logic |
| Markdown Processing | python-frontmatter | Parse YAML metadata |

---

## Recommendations

### Priority 1: Build on Existing Tools
- Use agent-memory-mcp CLI mode (don't rebuild)
- Use watchdog for file watching (don't build custom)
- Leverage existing graceful fallback logic

### Priority 2: Graceful Degradation Everywhere
- Check availability at startup
- Provide clear warnings once per session
- Fall back to file-based operations
- Never block on external dependencies

### Priority 3: Performance
- Batch embeddings where possible
- Cache SkillsMP results locally
- Debounce file system events
- Lazy load optional components

---

*Research completed: 2025-03-10 (Updated: Round 7)*
*All unknowns resolved including AI classification and prompt templates*

---

## 6. AI Importance Classification (Round 7)

### Research: LLM-based Importance Scoring

**Problem**: Automatically determine importance of decisions for routing to appropriate memory files.

**Findings**:

**Approach 1: Keyword-based Scoring**
- Simple word matching: "architecture", "design", "critical" → high importance
- Pros: Fast, deterministic
- Cons: Misses context, high false positive rate

**Approach 2: Multi-Factor AI Scoring (CHOSEN)**
- Analyze multiple dimensions:
  - Semantic importance (key terms, domain vocabulary)
  - Context complexity (discussion length, alternatives considered)
  - Technical impact (affects core architecture vs peripheral)
  - Repeatability (novel vs common pattern)
- Weighted average → 0.0-1.0 score
- Routes to appropriate file based on thresholds

**Implementation**:
```python
def calculate_importance(content, context):
    semantic = analyze_semantic_content(content)  # 0.0-1.0
    complexity = calculate_complexity(context)     # 0.0-1.0
    impact = estimate_technical_impact(content)    # 0.0-1.0
    repeatability = check_repeatability(content)    # 0.0-1.0
    
    # Weighted average
    score = (semantic * 0.3) + (complexity * 0.2) + 
            (impact * 0.3) + (repeatability * 0.2)
    
    return score

def route_to_file(score):
    if score > 0.7:
        return "architecture.md"  # High importance
    elif score > 0.4:
        return "patterns.md"       # Medium importance
    else:
        return "projects-log.md"   # Basic logging
```

**Decision**: Use multi-factor AI scoring with explicit user override capability.

---

## 7. Prompt Template Best Practices (Round 7)

### Research: Structured Prompting for Memory-Aware Agents

**Key Findings**:

**1. Headers-First Approach**
- Read only headers with one-line summary before task
- ~80-120 tokens vs ~2000 tokens for full content
- Agent sees "map" of memory, can navigate intelligently
- Deep dive only when relevant header found

**2. Structured Sections (Before/When/After)**

**Before Task** (always execute):
```
1. Read headers (grep "^## " for all memory files)
2. Check relevance (any header match current task?)
3. If relevant → read full section
4. If not → proceed with task
```

**When Stuck** (on-demand):
```
1. Vector search: memory_search(query="problem context")
2. Deep dive: read full relevant section
3. Cross-project: if <3 local results → offer global
```

**After Task** (always execute):
```
1. AI classify importance (0.0-1.0 score)
2. Route to appropriate file based on score
3. Save to vector memory with structured template
```

**3. One-line Summary Format**

Header format must include brief description:
```markdown
## Ошибка: JWT - expire через 15 мин, нужен refresh token flow
## Паттерн: Repository - отделить бизнес-логику от данных
## Memory System - 4-уровневая память агентов
```

**Benefits**:
- Agent understands essence without reading full content
- Human can scan memory quickly
- Reduces context usage by 95%

**Decision**: Implement structured Memory-Aware Prompt Template with one-line summary headers.

---

## Updated Recommendations (Round 7)

### Priority 1: Memory-Aware Workflow (NEW)
- Implement Headers-First reading strategy
- Use structured Before/When/After prompt template
- One-line summary in all memory file headers
- Context optimization: ~80-120 tokens (vs 2000)

### Priority 2: AI Importance Classification (NEW)
- Multi-factor scoring for decision importance
- Route to appropriate file based on score
- Explicit user markers override AI
- Self-learning from feedback

### Priority 3: Build on Existing Tools (unchanged)
- Use agent-memory-mcp CLI mode
- Use watchdog for file watching
- Leverage existing graceful fallback logic

### Priority 4: Graceful Degradation Everywhere (unchanged)
- Check availability at startup
- Provide clear warnings once per session
- Fall back to file-based operations
- Never block on external dependencies

---

*Research completed: 2025-03-10 (Updated: Round 7)*
*All unknowns resolved including AI classification and prompt templates*
