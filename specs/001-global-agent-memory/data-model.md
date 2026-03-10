# Data Model: Global Agent Memory Integration

> **Generated**: 2025-03-10  
> **Status**: Complete

---

## Core Entities

### 1. MemoryEntry
**Purpose**: Represents a single memory record in vector storage

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | Auto-generated |
| project_id | string | Project identifier | Required, format: {name} |
| type | enum | Memory type | Required: episodic, semantic, procedural, working |
| content | string | Structured markdown | Required, template-based |
| embedding | float[] | Vector representation | Optional (generated if missing) |
| embedding_model | string | Model used | Default: mxbai-embed-large |
| created_at | timestamp | Creation time | Auto-generated |
| updated_at | timestamp | Last update | Auto-generated on change |
| accessed_at | timestamp | Last access | Updated on recall |
| importance | float | 0.0-1.0 | Default: 0.5 |
| tags | string[] | Search tags | Optional |
| task_id | string | Related task | Optional |
| source_project | string | Origin project | Required, for cross-reference |
| related_projects | string[] | Projects to update | Optional, for cross-project updates |

---

### 2. ProjectMemory
**Purpose**: File-based memory structure for a project

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| project_id | string | Unique identifier | Required |
| path | string | Project directory | Required, must exist |
| lessons | MarkdownFile | Learned lessons | File: lessons.md |
| patterns | MarkdownFile | Improvement patterns | File: patterns.md |
| projects_log | MarkdownFile | Task history | File: projects-log.md |
| architecture | MarkdownFile | Arch decisions | File: architecture.md |
| handoff | MarkdownFile | Session context | File: handoff.md |

**File Structure**:
```
.memory/projects/{project_id}/
├── lessons.md
├── patterns.md
├── projects-log.md
├── architecture.md
└── handoff.md
```

---

### 3. ProjectConfig
**Purpose**: Project identification and settings

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| project_id | string | Unique identifier | Required, URL-safe |
| project_name | string | Display name | Required |
| memory_enabled | boolean | Enable memory | Default: true |
| created_at | timestamp | Creation time | Auto-generated |

**Location**: `.spec-kit/project.json`

---

### 4. SearchQuery
**Purpose**: Smart search query with scope

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| query | string | Search text | Required |
| scope | enum | Search scope | global, local, auto |
| project_id | string | Current project | Required for local |
| explicit_markers | string[] | User markers | Detected |
| intent | enum | Query intent | fix, find, best_practice |
| limit | number | Max results | Default: 10 |

**Scope Determination Logic**:
1. Check explicit_markers (override all)
2. Classify intent if no markers
3. Auto: local first, <3 results → global
4. Learn from feedback

---

## Relationships

```
ProjectMemory (1) ──── (1) ProjectConfig
    ├── (N) MemoryEntry
    └── (N) SkillRecord
```

---

*Data model updated: 2025-03-10 (Round 7: AI Classification, Prompt Templates)*


---

### 5. ImportanceScore
**Purpose**: AI-классификация для определения важности решений (Round 7)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| content | string | Analyzed content | Required |
| semantic_importance | float | Word-based score | 0.0-1.0 |
| context_complexity | float | Discussion length | 0.0-1.0 |
| technical_impact | float | Architecture influence | 0.0-1.0 |
| repeatability | float | Similar solutions | 0.0-1.0 |
| final_score | float | Weighted average | 0.0-1.0 |
| routing_target | enum | Target file | architecture, patterns, log |
| confidence | float | AI confidence | 0.0-1.0 |

**Scoring Logic**:
```
final_score = (semantic * 0.3) + (complexity * 0.2) + (impact * 0.3) + (repeatability * 0.2)

if final_score > 0.7:
    routing_target = "architecture.md"
elif final_score > 0.4:
    routing_target = "patterns.md"
else:
    routing_target = "projects-log.md"
```

**Explicit User Markers** (override AI):
- "документируй это в architecture.md" → final_score = 1.0
- "запомни это как паттерн" → routing_target = "patterns.md"
- "ошибка X важна, запиши" → routing_target = "lessons.md"

---

### 6. MemoryHeaders
**Purpose**: Headers-First reading with one-line summary (Round 7)

| Field | Type | Description | Format |
|-------|------|-------------|--------|
| file_type | enum | File type | lessons, patterns, architecture, log |
| header_level | number | H1-H6 | 1-6 |
| title | string | Section title | Required |
| summary | string | One-line summary | Max 100 chars |
| full_path | string | Header location | For navigation |
| relevance_score | float | Match to task | 0.0-1.0 |

**Header Format Examples**:
```markdown
## lessons.md:
## Ошибка: JWT - expire через 15 мин, нужен refresh token flow
## Урок: Env vars - всегда валидировать при старте

## patterns.md:
## Паттерн: Graceful Degradation - работает без внешних зависимостей
## Паттерн: Repository - отделить бизнес-логику от данных

## architecture.md:
## Memory System - 4-уровневая память агентов
## Frontend: TypeScript + React - UI компоненты и state
```

**Context Usage**:
- ~80-120 tokens для 10 headers
- Agent видит суть каждой секции
- При необходимости → углубляется в конкретную секцию

---

### 7. PromptTemplate
**Purpose**: Memory-Aware workflow template (Round 7)

| Section | Purpose | Content |
|---------|---------|---------|
| Before Task | Headers-First read | grep "^## " lessons.md, patterns.md, architecture.md |
| Check Relevance | Determine if deep dive needed | Analyze header relevance to current task |
| When Stuck | Vector search + deep dive | memory_search → read full section |
| Cross-Project | Show global if <3 local | "Показать решения из других проектов?" |
| After Task | Auto-document | AI classification → save to appropriate file |

**Token Usage**:
- Before Task: ~80-120 tokens (headers only)
- When Stuck: ~500-2000 tokens (on-demand)
- After Task: Save only (no context cost)

---

## Updated Relationships (Round 7)

```
MemoryEntry (1) ──── (1) ImportanceScore
    └── routes to ───> (1) MemoryHeaders

ProjectMemory (1) ──── (N) MemoryEntry
    ├── (N) MemoryHeaders (for navigation)
    └── (1) PromptTemplate (workflow)
```

---

*Data model updated: 2025-03-10 (Round 7: AI Classification, Prompt Templates)*
