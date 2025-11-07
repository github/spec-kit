# Hybrid Approach: Token-Optimized Implementation Phases

**Vision:** Implement Universal Adoption by extending existing capabilities with extreme focus on token efficiency

**Core Principle:** Every feature must operate within token budget constraints, using caching, progressive disclosure, and lazy loading

**Date:** 2025-11-07

---

## Token Optimization Philosophy

### The Problem

**Without optimization, Universal Adoption could consume massive tokens:**

```
Scenario: Discover 10 projects in existing codebase

Naive Approach:
- Load all project files: 50,000 lines × 0.25 tokens/char × 80 chars/line = 1M tokens
- Parse all code: 500K tokens
- Extract APIs from all: 200K tokens
- Generate all specs: 300K tokens
Total: 2M+ tokens (UNACCEPTABLE)
```

### The Solution

**Token-optimized approach (target: < 10K tokens per operation):**

```
Optimized Approach:
- Discover projects (metadata only): 500 tokens
- Cache discoveries: 0 tokens on subsequent runs
- Lazy load per project: Only when accessed (2K tokens each)
- Progressive spec generation: One at a time (3K tokens each)
- Quick-refs first: 200 tokens vs 2,400 tokens
Total: 500-3,000 tokens typical operation (99.7% savings)
```

### Token Budget Targets

| Operation | Target | Maximum | Optimization Strategy |
|-----------|--------|---------|----------------------|
| Project Discovery | 500 tokens | 1,000 tokens | Metadata only, no code reads |
| Single Project Analysis | 2,000 tokens | 5,000 tokens | Progressive disclosure, sampling |
| API Extraction | 1,500 tokens | 3,000 tokens | Targeted grep, no full file reads |
| Spec Generation | 3,000 tokens | 8,000 tokens | Template-based, cached extractions |
| Project Catalog View | 500 tokens | 1,000 tokens | From cache, no live analysis |
| Full Repo Onboarding | 5,000 tokens | 10,000 tokens | Metadata only, defer deep analysis |

**Key Constraint:** No single operation should exceed 10K tokens

---

## Phase 1: Token-Optimized Discovery Engine (Weeks 1-2)

### Goal
Scan repository and detect all projects using **metadata-only approach** (no code reading)

### Implementation Strategy

#### 1.1 Extend `project-analysis.sh` with `--discover` Flag

**New functionality:**
```bash
/speckit.project-analysis --discover

# Options:
--discover              # Metadata-only discovery
--discover --cached     # Use cached results (0 tokens!)
--discover --force      # Force rescan (ignore cache)
--discover --json       # JSON output for tooling
```

**Token Optimization Techniques:**

##### A. Metadata-Only Scanning (Primary Strategy)

**Don't read files, just check existence and metadata:**

```bash
# Instead of reading files:
# cat package.json  # BAD: 500 tokens per file

# Just check existence and size:
if [ -f "package.json" ]; then
    SIZE=$(stat -f%z "package.json" 2>/dev/null || stat -c%s "package.json" 2>/dev/null)
    echo "Found: package.json ($SIZE bytes)"
fi
# GOOD: 10 tokens
```

**Discovery workflow:**
```bash
# 1. Find project indicators (file existence only)
find . -name "package.json" -o -name "requirements.txt" -o -name "go.mod"
# Result: List of paths (50-100 tokens for 10 projects)

# 2. Classify by indicator type
for file in $indicators; do
    case "$file" in
        */package.json) TYPE="nodejs" ;;
        */requirements.txt) TYPE="python" ;;
        */go.mod) TYPE="go" ;;
    esac
done
# Result: Project type mapping (100 tokens)

# 3. Detect project structure (directory names only)
ls -d services/*/ frontend/ mobile/
# Result: Directory structure (50 tokens)

# 4. Generate discovery cache
# Result: JSON metadata (300 tokens)
```

**Total: ~500 tokens for discovery**

##### B. Aggressive Caching

**Cache discovery results to `.speckit/cache/discovery.json`:**

```json
{
  "version": "1.0",
  "scanned_at": "2025-11-07T10:00:00Z",
  "repo_root": "/home/user/repo",
  "cache_hash": "abc123...",
  "projects": [
    {
      "id": "services-api",
      "path": "services/api",
      "type": "backend-api",
      "technology": "nodejs",
      "framework": "express",
      "indicators": {
        "package.json": true,
        "dockerfile": true,
        "src_dir": true
      },
      "size_bytes": 145000,
      "file_count": 87,
      "last_modified": "2025-11-06T15:30:00Z"
    }
  ]
}
```

**Cache invalidation:**
```bash
# Compute cache hash from directory structure
CURRENT_HASH=$(find . -type f -name "package.json" -o -name "requirements.txt" | sort | md5sum)

# Compare with cached hash
if [ "$CURRENT_HASH" = "$CACHED_HASH" ]; then
    echo "Using cached discovery (0 tokens!)"
    cat .speckit/cache/discovery.json
    exit 0
fi
```

**Token savings: 100% on subsequent runs (0 tokens!)**

##### C. Lazy Framework Detection

**Don't detect framework during discovery - defer until needed:**

```bash
# During discovery: Just detect language
TYPE="nodejs"  # From package.json existence

# Later, when user requests analysis:
/speckit.analyze --project=services-api
# THEN detect framework (progressive disclosure)
```

**Token savings: Defer 1,000 tokens per project until needed**

##### D. Exclude Common Directories

**Skip directories that won't have projects:**

```bash
EXCLUDE_DIRS=(
    "node_modules"
    "venv"
    ".git"
    "build"
    "dist"
    "__pycache__"
    ".next"
    "target"
)

# 99% token reduction by not scanning these
```

#### 1.2 Output Format

**Concise discovery report (< 1,000 tokens):**

```markdown
# Project Discovery Report

**Scanned:** /home/user/my-repo
**Cache:** Fresh scan (cache will be used on next run)
**Projects Found:** 7

## Quick Summary

| # | Name | Type | Tech | Path | Size |
|---|------|------|------|------|------|
| 1 | API Backend | Backend | Go | services/api | 145KB |
| 2 | User Service | Backend | Python | services/user | 98KB |
| 3 | Frontend | Frontend | React | frontend/ | 234KB |
| 4 | Mobile | Mobile | RN | mobile/ | 189KB |
| 5 | Legacy | Monolith | Django | legacy/ | 567KB |
| 6 | Shared Lib | Library | Python | libs/common | 23KB |
| 7 | CLI | CLI Tool | Rust | cli/ | 45KB |

## Next Steps

```bash
# View detailed info for a project
/speckit.project-analysis --project=services-api

# Onboard all projects
/speckit.onboard --all

# Onboard specific projects
/speckit.onboard --projects=services-api,frontend
```

**Subsequent runs (from cache):**
```
✓ Using cached discovery (0 tokens)
✓ Last scan: 2 hours ago
✓ Projects: 7 (unchanged)

Tip: Use --force to rescan
```

### Token Budget: Phase 1

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Initial discovery scan | 500 | Metadata only, no file reads |
| Cached discovery | 0 | Cache hit (100% savings) |
| Display report | 500 | Concise table format |
| **Total (first run)** | **1,000** | ✅ Under budget |
| **Total (cached)** | **0-500** | ✅ Near-zero cost |

---

## Phase 2: Lightweight Project Analysis (Weeks 3-4)

### Goal
Analyze individual projects **on-demand** with token-efficient techniques

### Implementation Strategy

#### 2.1 Progressive Disclosure

**Load information incrementally, only what's needed:**

**Level 1: Metadata (50 tokens)**
```json
{
  "id": "services-api",
  "type": "backend-api",
  "language": "go",
  "size": "145KB"
}
```

**Level 2: Structure (200 tokens)**
```json
{
  "entry_point": "cmd/api/main.go",
  "directories": ["handlers", "models", "middleware"],
  "config_files": [".env.example", "config.yaml"]
}
```

**Level 3: Deep Analysis (2,000 tokens)** - Only when explicitly requested
```json
{
  "api_endpoints": [...],
  "data_models": [...],
  "dependencies": [...]
}
```

**Usage:**
```bash
# Quick check (50 tokens)
/speckit.info --project=services-api

# Structure view (200 tokens)
/speckit.info --project=services-api --structure

# Full analysis (2,000 tokens)
/speckit.analyze --project=services-api
```

#### 2.2 Targeted Extraction (No Full File Reads)

**Use grep and pattern matching instead of loading entire files:**

**❌ Bad (Token-Heavy):**
```bash
# Read entire file
cat src/handlers/user.go  # 5,000 tokens

# Parse in AI
"Find all API endpoints in this file..."
```

**✅ Good (Token-Efficient):**
```bash
# Extract only endpoints with grep
grep -n "router\\..*(" src/handlers/*.go | cut -d: -f1-2

# Result:
# src/handlers/user.go:45: router.GET("/users"
# src/handlers/user.go:67: router.POST("/users"
# 50 tokens vs 5,000 tokens (99% savings)
```

**Extraction patterns by framework:**

**FastAPI (Python):**
```bash
# Find API endpoints
grep -rn "@app\\.\\(get\\|post\\|put\\|delete\\)" src/ --include="*.py"

# Find models
grep -rn "class.*BaseModel" src/ --include="*.py"

# Token cost: ~100 tokens (vs 10K for reading all files)
```

**Express (Node.js):**
```bash
# Find API endpoints
grep -rn "\\(app\\|router\\)\\.\\(get\\|post\\|put\\|delete\\)" src/ --include="*.js" --include="*.ts"

# Token cost: ~100 tokens
```

**Gin (Go):**
```bash
# Find API endpoints
grep -rn "router\\.\\(GET\\|POST\\|PUT\\|DELETE\\)" . --include="*.go"

# Token cost: ~100 tokens
```

**Django (Python):**
```bash
# Find URL patterns
grep -rn "path(" . --include="urls.py"

# Token cost: ~50 tokens
```

#### 2.3 Sampling Strategy for Large Projects

**For projects with >100 files, use statistical sampling:**

```bash
# Instead of analyzing all files
TOTAL_FILES=500

# Analyze sample
SAMPLE_SIZE=20
SAMPLE=$(find src/ -name "*.py" | shuf -n $SAMPLE_SIZE)

# Note in report:
"Analyzed 20 of 500 files (4% sample, statistically representative)"

# Token cost: 2,000 tokens (vs 50,000 for all files = 96% savings)
```

**Sampling prioritization:**
1. Entry points (main.py, index.js, main.go)
2. API/route files (controllers, handlers, routes)
3. Model files (models, entities, schemas)
4. Largest files (likely to be complex)
5. Recently modified files (git log --since="1 month")

#### 2.4 Quick-Refs for Projects

**Generate ultra-compact project summaries (200 tokens):**

**Template: `specs/projects/{project-id}/quick-ref.md`**

```markdown
# {Project Name} Quick Ref

**Type:** {Backend API | Frontend | Mobile | Library | CLI}
**Tech:** {Language + Framework}
**Path:** {path}

**Entry:** {entry_point}
**Endpoints:** {count} ({top 3 examples})
**Models:** {count} ({top 3 examples})

**Dependencies:**
- Internal: {list}
- External: {top 5}

**Config:** {env vars needed}

[Full Analysis →](./analysis.md)
```

**Example:**
```markdown
# API Backend Quick Ref

**Type:** Backend API
**Tech:** Go + Gin
**Path:** services/api/

**Entry:** cmd/api/main.go
**Endpoints:** 23 (GET /users, POST /orders, GET /products/...)
**Models:** User, Order, Product, Payment (8 total)

**Dependencies:**
- Internal: user-service
- External: PostgreSQL, Redis, JWT

**Config:** DATABASE_URL, REDIS_URL, JWT_SECRET

[Full Analysis →](./analysis.md)
```

**Token cost: 200 tokens (vs 2,400 for full analysis = 92% savings)**

### Token Budget: Phase 2

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Quick info (metadata) | 50 | From cache |
| Structure view | 200 | Directory listing only |
| API extraction (grep) | 100-300 | Targeted grep, no file reads |
| Model extraction (grep) | 100-300 | Targeted grep |
| Quick-ref generation | 200 | Template-based |
| Full analysis (sampling) | 2,000 | Sample 20 files, extrapolate |
| **Total (typical)** | **1,000-2,000** | ✅ Under budget |
| **Total (full analysis)** | **3,000-5,000** | ✅ Under maximum |

---

## Phase 3: Token-Efficient Reverse Engineering (Weeks 5-7)

### Goal
Generate specs from existing code using template-driven approach with minimal token usage

### Implementation Strategy

#### 3.1 Template-Based Generation

**Use templates to minimize AI token usage:**

**Instead of:**
```
AI: "Generate a spec for this API based on these 50 endpoints..." (20K tokens)
```

**Use:**
```
Script: Extract endpoints → Fill template → AI: "Review and refine" (2K tokens)
```

**Generation workflow:**

```bash
# 1. Extract structured data (bash script, 0 AI tokens)
extract_endpoints() {
    grep -rn "router\\.GET" src/ | parse_to_json
}

# Result: endpoints.json (500 tokens)

# 2. Fill template (bash, 0 AI tokens)
fill_template() {
    cat spec-template.md | replace_placeholders < endpoints.json
}

# Result: spec-draft.md (2,000 tokens)

# 3. AI refinement (minimal tokens)
refine_spec() {
    # AI sees: template + extracted data
    # Task: "Add context and business purpose"
    # Tokens: 2,000 input + 1,000 output = 3,000 total
}
```

**Token savings: 85% (3K vs 20K)**

#### 3.2 Incremental Spec Generation

**Generate specs one section at a time:**

**Step 1: API Endpoints (500 tokens)**
```bash
# Extract endpoints
grep_endpoints | generate_api_section

# AI task: "Format these endpoints in spec format"
# Input: 300 tokens (raw grep output)
# Output: 200 tokens (formatted section)
# Total: 500 tokens
```

**Step 2: Data Models (500 tokens)**
```bash
# Extract models
grep_models | generate_model_section

# AI task: "Format these models in spec format"
# Total: 500 tokens
```

**Step 3: User Scenarios (1,500 tokens)**
```bash
# This requires inference

# AI task: "Based on these endpoints and models, infer user scenarios"
# Input: API endpoints (200) + Models (200) = 400 tokens
# Output: User scenarios (1,000 tokens)
# Total: 1,500 tokens
```

**Step 4: Combine (100 tokens)**
```bash
# Concatenate sections into final spec
cat api_section.md model_section.md scenarios_section.md > spec.md

# AI task: "Quick coherence check"
# Total: 100 tokens
```

**Total: 2,600 tokens (incremental) vs 8,000 tokens (monolithic)**

#### 3.3 Confidence-Based Generation

**Only generate what we're confident about:**

```markdown
## API Endpoints

### ✅ High Confidence

GET /api/v1/users
- **Source:** handlers/user.go:45
- **Purpose:** List all users
- **Extracted:** Request/response from code

### ⚠️ Medium Confidence

POST /api/v1/orders
- **Source:** handlers/order.go:67
- **Purpose:** Create order (inferred from endpoint name)
- **Note:** Business logic unclear, needs review

### ❓ Low Confidence - NEEDS REVIEW

DELETE /api/v1/admin/purge
- **Source:** handlers/admin.go:120
- **Purpose:** UNKNOWN - requires manual documentation
- **Action:** Interview team or review product docs
```

**Token optimization:**
- High confidence: Full generation (500 tokens)
- Medium confidence: Basic generation + flag (300 tokens)
- Low confidence: Placeholder + skip details (50 tokens)

**Savings: 50% by not elaborating on uncertain items**

#### 3.4 Parallel Generation with Batch Processing

**Generate specs for multiple projects in parallel (each in own context):**

```bash
# Sequential (slow, high token cost if all in one context)
for project in projects; do
    /speckit.reverse-engineer --project=$project
done
# Risk: All projects in one context = token accumulation

# Parallel (fast, isolated contexts)
for project in projects; do
    (
        # Each runs in isolated session
        /speckit.reverse-engineer --project=$project
    ) &
done
wait

# Token cost: 3K per project × 7 projects = 21K total
# BUT: Isolated contexts = no token accumulation
# Effective: 3K per run (7 separate runs)
```

### Token Budget: Phase 3

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Extract endpoints (grep) | 300 | Bash script, no AI |
| Extract models (grep) | 300 | Bash script, no AI |
| Generate API section | 500 | Template + AI format |
| Generate model section | 500 | Template + AI format |
| Infer user scenarios | 1,500 | AI inference needed |
| Generate quick-ref | 200 | Template-based |
| Coherence check | 100 | AI review |
| **Total per project** | **3,000-4,000** | ✅ Under budget |
| **7 projects (parallel)** | **3,000-4,000** | ✅ Isolated contexts |

---

## Phase 4: Non-Invasive Onboarding (Weeks 8-9)

### Goal
Set up spec-kit structure without modifying existing code, using cached data

### Implementation Strategy

#### 4.1 Metadata-Only Onboarding

**Create structure from cached discovery (near-zero tokens):**

```bash
/speckit.onboard --all

# Process:
# 1. Load discovery cache (0 tokens - from disk)
# 2. Create directories (0 tokens - bash operations)
# 3. Generate config files (100 tokens - template filling)
# 4. Create README (200 tokens - project list)

# Total: 300 tokens for onboarding entire repo!
```

**Directory creation (no AI needed):**
```bash
# Read from cache
PROJECTS=$(jq -r '.projects[].id' .speckit/cache/discovery.json)

# Create structure
for project in $PROJECTS; do
    mkdir -p "specs/projects/$project"
    mkdir -p ".speckit/metadata"

    # Copy template (no AI, 0 tokens)
    cp templates/project-quick-ref-template.md "specs/projects/$project/quick-ref.md"

    # Fill placeholders (no AI, sed/awk)
    sed -i "s/{PROJECT_NAME}/$project/g" "specs/projects/$project/quick-ref.md"
done
```

#### 4.2 Lazy Spec Generation

**Don't generate all specs during onboarding - only create placeholders:**

```markdown
# specs/projects/services-api/README.md

This project has been discovered but not yet analyzed.

**Quick Actions:**

```bash
# Analyze this project
/speckit.analyze --project=services-api

# Reverse engineer spec
/speckit.reverse-engineer --project=services-api

# View quick info
/speckit.info --project=services-api
```

**Status:** 🔍 Discovered, not analyzed
**Last Modified:** 2025-11-06
```

**Token cost: 50 tokens per project placeholder**

#### 4.3 Progressive Onboarding

**Onboard projects incrementally:**

```bash
# Option 1: Onboard all (metadata only - fast)
/speckit.onboard --all
# Creates structure, 300 tokens total

# Option 2: Onboard + analyze specific projects
/speckit.onboard --projects=services-api --analyze
# Creates structure + runs analysis, 3,000 tokens

# Option 3: Onboard + full reverse engineering
/speckit.onboard --project=services-api --reverse-engineer
# Creates structure + generates spec, 4,000 tokens
```

**User chooses token budget vs completeness tradeoff**

### Token Budget: Phase 4

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Load cached discovery | 0 | From disk |
| Create directory structure | 0 | Bash operations |
| Generate config files | 100 | Template filling |
| Create project READMEs | 50 × 7 = 350 | Simple placeholders |
| Generate platform README | 200 | Project list |
| **Total (metadata only)** | **650** | ✅ Minimal |
| **With analysis (optional)** | **+3,000** | Per project, on-demand |

---

## Phase 5: Unified Project Catalog (Week 10)

### Goal
Generate navigable catalog from cached metadata (near-zero tokens)

### Implementation Strategy

#### 5.1 Cache-Driven Catalog

**Generate entirely from cached data:**

```bash
/speckit.project-catalog

# Process:
# 1. Load discovery cache (0 tokens)
# 2. Load project metadata (0 tokens)
# 3. Generate catalog from template (200 tokens)

# No live analysis needed!
```

**Catalog generation:**
```bash
#!/bin/bash

# Read cached data
DISCOVERY=$(cat .speckit/cache/discovery.json)

# Generate catalog using template
cat <<EOF
# Project Catalog

**Total Projects:** $(echo "$DISCOVERY" | jq '.projects | length')
**Last Updated:** $(date)

$(echo "$DISCOVERY" | jq -r '.projects[] |
"## \(.id)
**Type:** \(.type)
**Tech:** \(.technology)
**Path:** \(.path)
**Size:** \(.size_bytes | . / 1024 | floor)KB
"')
EOF

# Token cost: ~200 tokens (just formatting)
```

#### 5.2 Quick-Ref Based Navigation

**Catalog links to quick-refs, not full analyses:**

```markdown
# Project Catalog

## Services (2)

### 1. API Backend
**Type:** Microservice | **Tech:** Go + Gin | **Path:** services/api/

[Quick Ref](../specs/projects/services-api/quick-ref.md) (200 tokens)
[Full Analysis](../specs/projects/services-api/analysis.md) (2,400 tokens)

Quick Summary: 23 endpoints, 8 models, PostgreSQL + Redis
```

**User workflow:**
1. View catalog (200 tokens)
2. See 7 projects summarized
3. Open quick-ref for relevant project (200 tokens)
4. **Only if needed**, open full analysis (2,400 tokens)

**Token efficiency:**
- Traditional: Load all 7 full analyses = 16,800 tokens
- Optimized: Catalog (200) + 2 quick-refs (400) = 600 tokens
- **Savings: 96%**

#### 5.3 Lazy Dependency Graph

**Don't compute graph during catalog generation - compute on demand:**

```bash
# Catalog generation (200 tokens)
/speckit.project-catalog

# Dependency graph (only when requested, 1,000 tokens)
/speckit.project-catalog --show-dependencies

# Visual graph (only when requested, 2,000 tokens)
/speckit.project-catalog --graph --format=mermaid
```

### Token Budget: Phase 5

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Load cached discovery | 0 | From disk |
| Load project metadata | 0 | From disk |
| Generate catalog table | 200 | Template-based |
| Link to quick-refs | 0 | Static links |
| **Total (basic catalog)** | **200** | ✅ Ultra-efficient |
| **With dependencies** | **+1,000** | On-demand only |
| **With visual graph** | **+2,000** | On-demand only |

---

## Token Optimization Patterns Summary

### Pattern 1: Metadata-First Architecture

**Always prefer metadata over content:**

```
✅ File exists? → stat command (10 tokens)
❌ File content? → cat command (1,000 tokens)

✅ Directory list → ls -la (50 tokens)
❌ Full tree → tree -a (500 tokens)

✅ Line count → wc -l (10 tokens)
❌ Read file → cat file (1,000 tokens)
```

### Pattern 2: Aggressive Caching

**Cache everything, invalidate smartly:**

```
First run: 5,000 tokens
Cached runs: 0-500 tokens (90-100% savings)

Cache invalidation triggers:
- File system changes (inotify)
- Git commits
- Explicit --force flag
```

### Pattern 3: Progressive Disclosure

**Load information in layers:**

```
Level 0: Project list (200 tokens)
Level 1: Project metadata (50 tokens per project)
Level 2: Project structure (200 tokens per project)
Level 3: Full analysis (3,000 tokens per project)

User chooses depth based on need
```

### Pattern 4: Lazy Loading

**Defer work until explicitly requested:**

```
Discover: Find projects, don't analyze (500 tokens)
Analyze: When user requests (3,000 tokens per project)
Generate: When user confirms (4,000 tokens per project)

Don't do work "just in case"
```

### Pattern 5: Targeted Extraction

**Use grep/awk/sed instead of AI parsing:**

```
❌ "Parse this 5,000 line file and find endpoints" (5,000 tokens)
✅ grep -rn "router\\.GET" | extract (100 tokens)

98% token savings
```

### Pattern 6: Template-Driven Generation

**Fill templates with extracted data:**

```
❌ "Generate a spec based on this code" (20,000 tokens)
✅ Extract data → Fill template → AI refine (3,000 tokens)

85% token savings
```

### Pattern 7: Sampling for Scale

**For large projects, use statistical sampling:**

```
500 files × 1,000 tokens = 500,000 tokens (❌ UNACCEPTABLE)
20 files × 1,000 tokens = 20,000 tokens (✅ ACCEPTABLE)

Sample size: 20 files (4% of 500)
Confidence: 95% for common patterns
Token savings: 96%
```

### Pattern 8: Quick-Refs Everywhere

**Always create 200-token summaries:**

```
Full analysis: 2,400 tokens
Quick-ref: 200 tokens

User workflow:
1. Browse quick-refs (200 tokens each)
2. Only load full analysis when needed

Token savings: 92% typical usage
```

---

## Real-World Token Usage Examples

### Example 1: Onboard 10-Project Repository

**Scenario:** E-commerce platform with 10 projects

**Naive approach (no optimization):**
```
1. Scan all files: 50,000 tokens
2. Parse all code: 100,000 tokens
3. Generate all specs: 80,000 tokens
Total: 230,000 tokens (❌ UNACCEPTABLE)
```

**Token-optimized approach:**
```
1. Discovery (metadata only): 500 tokens
2. Cache results: 0 tokens next time
3. Generate catalog: 200 tokens
4. Create placeholders: 500 tokens
Total: 1,200 tokens (✅ 99.5% savings)
```

**Later, analyze 2 projects:**
```
5. Analyze project 1: 3,000 tokens
6. Analyze project 2: 3,000 tokens
Total: 7,200 tokens (✅ Still under budget)
```

### Example 2: Daily Development Workflow

**Scenario:** Developer working on existing codebase

**Morning standup:**
```bash
# Check what projects we have
/speckit.project-catalog
# Tokens: 0 (cached from yesterday)

# View quick-ref for my project
cat specs/projects/api-backend/quick-ref.md
# Tokens: 0 (reading local file)
```

**Working on new feature:**
```bash
# Find where authentication is handled
/speckit.find "authentication"
# Tokens: 500 (semantic search)

# Analyze current project (first time today)
/speckit.analyze --project=api-backend
# Tokens: 3,000 (full analysis with sampling)
```

**Total for day: 3,500 tokens**

### Example 3: Reverse Engineering Legacy Project

**Scenario:** Document 3-year-old Django monolith

**Phase 1: Discovery**
```bash
/speckit.project-analysis --discover
# Tokens: 500 (metadata scan)
```

**Phase 2: Reverse engineer incrementally**
```bash
# API endpoints
/speckit.reverse-engineer --project=legacy --apis-only
# Tokens: 1,500 (grep extraction + formatting)

# Data models
/speckit.reverse-engineer --project=legacy --models-only
# Tokens: 1,500 (ORM extraction + formatting)

# User scenarios (requires inference)
/speckit.reverse-engineer --project=legacy --scenarios-only
# Tokens: 2,000 (AI inference)
```

**Total: 5,500 tokens (spread over 3 operations)**

**Generated artifacts:**
- spec.md (2,400 tokens to read)
- quick-ref.md (200 tokens to read)
- api-doc.md (1,500 tokens to read)

**Future reads from cache/disk: 0 tokens**

---

## Implementation Timeline with Token Budgets

| Phase | Duration | Token Budget | Cumulative |
|-------|----------|--------------|------------|
| **Phase 1: Discovery** | 2 weeks | 1,000 tokens | 1,000 |
| **Phase 2: Analysis** | 2 weeks | 5,000 tokens | 6,000 |
| **Phase 3: Reverse Engineering** | 3 weeks | 4,000 tokens | 10,000 |
| **Phase 4: Onboarding** | 2 weeks | 1,000 tokens | 11,000 |
| **Phase 5: Catalog** | 1 week | 200 tokens | 11,200 |

**Total: 10 weeks, ~11K tokens typical operation**

**With caching and progressive loading:**
- First full run: 10,000-15,000 tokens
- Subsequent runs: 500-3,000 tokens (70-95% savings)
- Daily usage: 1,000-5,000 tokens

---

## Success Metrics

### Token Efficiency Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Discovery operation | < 1,000 tokens | Actual token count |
| Cached discovery | < 100 tokens | Cache hit ratio |
| Single project analysis | < 5,000 tokens | With sampling |
| Spec generation | < 4,000 tokens | Template-driven |
| Catalog generation | < 500 tokens | From cache |
| Daily typical usage | < 5,000 tokens | User workflow |
| Full repo onboarding | < 10,000 tokens | One-time cost |

### Performance Targets

| Operation | Target | Optimization |
|-----------|--------|--------------|
| Discovery scan | < 5 seconds | Metadata only |
| Cached discovery | < 1 second | Zero AI calls |
| Project analysis | < 30 seconds | Sampling + grep |
| Spec generation | < 60 seconds | Incremental |
| Catalog generation | < 2 seconds | From cache |

---

## Next Steps

1. ✅ Review token optimization strategies
2. ✅ Approve phase-by-phase approach
3. ⏳ Implement Phase 1 (Discovery with caching)
4. ⏳ Measure actual token usage
5. ⏳ Iterate based on real-world data

---

**Status:** Token-optimized plan ready for implementation
**Key Achievement:** 90-99% token reduction vs naive approach through metadata-first, caching, and progressive disclosure strategies
