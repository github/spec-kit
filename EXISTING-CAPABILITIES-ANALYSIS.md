# Existing Capabilities Analysis

**Purpose:** Before implementing Universal Adoption, analyze what capabilities already exist in spec-kit to avoid duplication and identify what can be reused or extended.

**Date:** 2025-11-07

---

## Summary

Spec-kit **already has significant analysis and discovery capabilities** that can be leveraged for Universal Adoption. However, these are designed for codebases that **already use spec-kit**, not for discovering and onboarding **existing projects**.

---

## Existing Commands & Capabilities

### 1. `/speckit.project-analysis` ✅ (Highly Relevant)

**Location:** `templates/commands/project-analysis.md`
**Script:** `scripts/bash/project-analysis.sh`

**What it does:**
- Analyzes **ALL specifications** in the project (comprehensive, not single-feature)
- Validates specification completeness (spec.md, plan.md, tasks.md)
- Checks code-specification alignment
- **Code pattern analysis** (Security, DRY, KISS, SOLID) with `--check-patterns` flag
- Detects language and source directories
- Generates comprehensive Markdown report

**Token Optimizations:**
- `--incremental`: Only analyze changed files (70-90% reduction)
- `--diff-only`: Git-based differential (80-95% reduction)
- `--summary`: Metrics only (90% reduction)
- `--sample-size=N`: Limit code analysis to N files
- Progressive disclosure: Load specs incrementally

**Limitations for Universal Adoption:**
- ❌ **Assumes specs already exist** - Won't work for projects without spec-kit
- ❌ **No project discovery** - Doesn't find microservices, monoliths, libraries, etc.
- ❌ **No reverse engineering** - Can't generate specs from existing code
- ❌ **Spec-centric** - Analyzes specs → code, not code → specs

**Reuse Potential:** ⭐⭐⭐⭐⭐ (80%)
- Code pattern analysis engine can be reused
- Language detection logic can be reused
- Source directory detection can be reused
- Report generation can be adapted

---

### 2. `/speckit.analyze` ✅ (Somewhat Relevant)

**Location:** `templates/commands/analyze.md`
**Script:** `scripts/bash/check-prerequisites.sh`

**What it does:**
- Analyzes **single feature** (not whole project)
- Cross-artifact consistency (spec.md, plan.md, tasks.md)
- Detects duplications, ambiguities, underspecification
- Constitution compliance checking

**Limitations for Universal Adoption:**
- ❌ Single-feature focused
- ❌ Requires existing specs
- ❌ No project discovery
- ❌ No reverse engineering

**Reuse Potential:** ⭐⭐ (20%)
- Validation logic might be useful
- Constitution checking can be adapted

---

### 3. `/speckit.find` ✅ (Highly Relevant)

**Location:** `templates/commands/find.md`
**Script:** `scripts/bash/semantic-search.sh`

**What it does:**
- **Semantic search** across code, specs, plans, AI docs
- Natural language queries
- Ranked results with file locations
- Relevance scoring

**Example:**
```bash
/speckit.find "authentication handling"
# Returns:
# - src/auth/login.py:45 (95% relevance)
# - specs/002-user-auth/ai-doc.md:87 (85% relevance)
```

**Reuse Potential:** ⭐⭐⭐⭐⭐ (100%)
- **Can be used directly for Universal Adoption**
- Perfect for finding APIs, models, configurations
- Already searches across code and specs
- Just needs to work without specs existing

---

### 4. `/speckit.document` ✅ (Relevant for Reverse Engineering)

**Location:** `templates/commands/document.md`

**What it does:**
- Generates `ai-doc.md` (comprehensive documentation)
- Generates `quick-ref.md` (200-token summary)
- Can generate for all features with `--all`
- Token-optimized

**Limitations:**
- ❌ Requires existing specs and implementations
- ❌ Documents what's already specified, doesn't discover

**Reuse Potential:** ⭐⭐⭐ (40%)
- Quick-ref generation format is useful
- Documentation templates can be adapted

---

### 5. CLI: `specify init` ✅ (Partially Relevant)

**Location:** `src/specify_cli/__init__.py`

**What it does:**
- Initializes **new project** with spec-kit
- Downloads templates from GitHub
- Sets up directory structure
- Detects if git repo exists
- Ensures executable scripts

**Limitations for Universal Adoption:**
- ❌ **Greenfield only** - Assumes empty or new project
- ❌ **No discovery** - Doesn't scan for existing projects
- ❌ **Overwrites approach** - Downloads templates to root
- ❌ **Single AI agent** - User selects one (claude, gemini, etc.)

**Reuse Potential:** ⭐⭐⭐ (40%)
- Template download mechanism can be reused
- Git detection can be reused
- Script setup can be reused
- **Needs major changes for existing codebases**

---

### 6. Scripts: Language & Source Detection 🔍 (Hidden Gem!)

**Location:** `scripts/bash/project-analysis.sh` (lines 183-245)

**What it does (discovered in the script):**
```bash
# Detect programming languages
DETECTED_LANGUAGES=""
if find "$REPO_ROOT" -name "*.py" -type f | head -1 | grep -q "."; then
    DETECTED_LANGUAGES="Python"
fi
if find "$REPO_ROOT" -name "*.js" -o -name "*.ts" -type f | head -1 | grep -q "."; then
    if [ -n "$DETECTED_LANGUAGES" ]; then
        DETECTED_LANGUAGES="$DETECTED_LANGUAGES,JavaScript/TypeScript"
    else
        DETECTED_LANGUAGES="JavaScript/TypeScript"
    fi
fi

# Detect source directories
SOURCE_DIRS=""
for dir in "src" "lib" "app" "backend" "frontend"; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        if [ -z "$SOURCE_DIRS" ]; then
            SOURCE_DIRS="$dir"
        else
            SOURCE_DIRS="$SOURCE_DIRS,$dir"
        fi
    fi
done
```

**Reuse Potential:** ⭐⭐⭐⭐ (60%)
- Basic language detection exists
- Can be significantly extended
- Good starting point

---

## What's MISSING for Universal Adoption

### ❌ 1. Project Discovery System

**Not implemented:**
- Detecting multiple projects in a repo (microservices, monoliths, libraries)
- Technology stack detection (beyond basic Python/JS)
- Framework detection (FastAPI, Express, Django, Spring, etc.)
- Architecture classification (microservice, monolith, frontend, CLI, etc.)
- Project relationship mapping (dependencies between services)

**Needed:**
- Scan for project indicators (package.json, requirements.txt, go.mod, etc.)
- Classify project types
- Build project inventory
- `/speckit.discover` command

---

### ❌ 2. Non-Invasive Onboarding

**Not implemented:**
- Creating parallel `.speckit/` structure without modifying existing code
- Project metadata management
- Multi-project configuration
- Adaptive structure (respecting existing conventions)

**Needed:**
- Parallel directory structure creation
- Configuration management (`.speckit.config.json`)
- Metadata cache (`.speckit/cache/`)
- `/speckit.onboard` command

---

### ❌ 3. Reverse Engineering

**Not implemented:**
- Generating specs from existing code
- API endpoint extraction from frameworks
- Data model extraction from ORMs
- Event schema detection
- Confidence scoring for auto-generated content

**Needed:**
- Code parsing for APIs (FastAPI, Express, Spring, Gin, etc.)
- ORM model extraction (SQLAlchemy, TypeORM, GORM, etc.)
- Spec generation from extracted information
- `/speckit.reverse-engineer` command

---

### ❌ 4. Universal Project Catalog

**We added `/speckit.service-catalog` for microservices, but need:**
- Multi-type project catalog (not just services)
- Works for monoliths, libraries, CLIs, frontends, mobile apps
- Cross-project dependency visualization
- `/speckit.project-catalog` command (different from service-catalog)

---

### ❌ 5. Deep Technology Detection

**Current detection is basic (just Python/JS file existence).**

**Not implemented:**
- Framework detection (FastAPI vs Flask vs Django)
- Version detection (Python 3.11, Node 18, Go 1.21)
- Dependency file parsing (requirements.txt, package.json, go.mod)
- Build system detection (webpack, vite, cargo, maven, gradle)
- Database detection (PostgreSQL, MongoDB, Redis)

**Needed:**
- Sophisticated file pattern matching
- Configuration file parsing
- Dependency analysis
- Framework-specific indicators

---

## Mapping: Universal Adoption Plans → Existing Capabilities

| Planned Feature | Existing Capability | Gap | Reuse % |
|----------------|---------------------|-----|---------|
| **Project Discovery** | Language detection (basic) | Missing: project classification, tech stack, architecture | 20% |
| **Technology Detection** | Python/JS file detection | Missing: frameworks, versions, dependencies | 15% |
| **API Extraction** | None | Missing: endpoint parsing from frameworks | 0% |
| **Data Model Extraction** | None | Missing: ORM model parsing | 0% |
| **Code Pattern Analysis** | ✅ `/speckit.project-analysis --check-patterns` | Works! Just needs adaptation | 80% |
| **Semantic Search** | ✅ `/speckit.find` | Works! Already perfect for this | 100% |
| **Spec Generation** | None | Missing: reverse engineering from code | 0% |
| **Quick-refs** | ✅ `/speckit.document` generates quick-ref.md | Works! Template can be reused | 60% |
| **Project Catalog** | `/speckit.service-catalog` (microservices only) | Missing: multi-type projects | 30% |
| **Non-invasive Setup** | `specify init` (overwrites) | Missing: parallel structure, metadata | 15% |
| **Analysis Reports** | ✅ `/speckit.project-analysis` | Works! Report format can be reused | 70% |
| **Incremental Analysis** | ✅ `--incremental`, `--diff-only` flags | Works! Already optimized | 100% |
| **Token Optimization** | ✅ Multiple flags, progressive disclosure | Works! Already best-in-class | 100% |

---

## Recommendations

### Strategy 1: Extend Existing Commands ⭐ (Recommended)

**Leverage what exists, add what's missing:**

1. **Extend `/speckit.project-analysis`** for discovery:
   - Add `--discover` flag to find all projects
   - Add project classification logic
   - Add technology stack detection
   - Keep existing analysis for projects with specs

2. **Create `/speckit.reverse-engineer`** (NEW):
   - Reuse code pattern analysis from `project-analysis`
   - Add API extraction logic
   - Add data model extraction logic
   - Generate specs in new format

3. **Extend `specify init`** for existing codebases:
   - Add `--existing` flag for non-invasive mode
   - Create parallel `.speckit/` structure
   - Don't overwrite existing files
   - Support multi-project repos

4. **Adapt `/speckit.service-catalog`** → `/speckit.project-catalog`:
   - Support all project types (not just services)
   - Reuse catalog generation logic
   - Extend for monoliths, libraries, frontends, etc.

**Pros:**
- ✅ Reuses 50-60% of existing code
- ✅ Consistent command naming
- ✅ Leverages proven patterns
- ✅ Faster implementation

**Cons:**
- ⚠️  Some commands become "swiss army knives" with many flags

---

### Strategy 2: All-New Commands

**Create separate commands for Universal Adoption:**

- `/speckit.discover` (new)
- `/speckit.onboard` (new)
- `/speckit.reverse-engineer` (new)
- `/speckit.project-catalog` (new, separate from service-catalog)

**Pros:**
- ✅ Clean separation of concerns
- ✅ Easier to understand
- ✅ No risk of breaking existing functionality

**Cons:**
- ❌ More duplication
- ❌ Longer implementation time
- ❌ More commands to maintain

---

## Proposed Hybrid Approach ⭐⭐⭐ (Best)

**Combine both strategies:**

### Phase 1: Discovery & Analysis

**Extend existing:**
```bash
# Add discovery mode to project-analysis
/speckit.project-analysis --discover

# Output:
# - Discovered projects: 7
# - Project types: microservices (2), monolith (1), frontend (1), etc.
# - Ready for onboarding

# Then analyze (existing functionality)
/speckit.project-analysis --check-patterns
```

**Why:** Reuses 80% of project-analysis.sh logic

---

### Phase 2: Onboarding

**Extend existing CLI:**
```bash
# Add flag to specify CLI
specify init . --existing --discover

# Behavior:
# - Scans for existing projects (doesn't overwrite)
# - Creates .speckit/ structure (parallel)
# - Asks which projects to onboard
```

**Why:** Reuses template download, git detection, script setup

---

### Phase 3: Reverse Engineering

**NEW command** (no existing equivalent):
```bash
/speckit.reverse-engineer --project=api

# Generates:
# - specs/projects/api/001-existing-code/spec.md
# - specs/projects/api/001-existing-code/quick-ref.md
```

**Why:** No overlap, needs fresh implementation

---

### Phase 4: Unified Catalog

**Extend service-catalog:**
```bash
# Works for all project types, not just services
/speckit.service-catalog --all-projects

# Or create alias:
/speckit.project-catalog
# (internally calls service-catalog with --all-projects)
```

**Why:** Reuses catalog generation logic

---

## Implementation Order (Based on Dependencies)

```
1. Enhance project-analysis.sh with discovery logic
   ├─ Add project type detection
   ├─ Add framework detection
   ├─ Add dependency parsing
   └─ Keep existing analysis features

2. Create reverse-engineering engine (NEW)
   ├─ API extraction per framework
   ├─ Data model extraction per ORM
   └─ Spec generation templates

3. Extend specify init for existing codebases
   ├─ Add --existing flag
   ├─ Create parallel structure
   └─ Multi-project support

4. Create project catalog (extend service-catalog)
   ├─ Support all project types
   └─ Reuse visualization logic

5. Integrate everything
   ├─ Update commands to work together
   └─ Documentation
```

---

## Estimated Effort Savings

| Task | From Scratch | With Reuse | Savings |
|------|-------------|------------|---------|
| Discovery | 2 weeks | 1 week | 50% |
| Analysis | 2 weeks | 0.5 weeks | 75% (mostly exists) |
| Pattern Detection | 2 weeks | 0.2 weeks | 90% (exists) |
| Reverse Engineering | 3 weeks | 3 weeks | 0% (new) |
| Onboarding | 2 weeks | 1 week | 50% |
| Catalog | 2 weeks | 1 week | 50% |
| Integration | 3 weeks | 2 weeks | 33% |
| **Total** | **16 weeks** | **8.7 weeks** | **46%** |

---

## Key Findings

1. ✅ **50-60% of needed capabilities already exist**
2. ✅ **Code pattern analysis is production-ready** (`--check-patterns`)
3. ✅ **Token optimization is world-class** (multiple modes)
4. ✅ **Semantic search is perfect** for Universal Adoption
5. ❌ **Discovery and reverse-engineering are net-new**
6. ⚠️  **Existing commands assume specs exist** - need adaptation

---

## Recommendation: Proceed with Hybrid Approach

**Phase 1 (2-3 weeks):**
- Extend `project-analysis.sh` with `--discover` flag
- Build project detection for top 4 languages
- Reuse existing analysis capabilities

**Phase 2 (3 weeks):**
- Create reverse-engineering engine
- API and data model extraction

**Phase 3 (2 weeks):**
- Extend `specify init` for existing codebases
- Non-invasive onboarding

**Phase 4 (1 week):**
- Extend service-catalog to project-catalog
- Integration and testing

**Total: 8-9 weeks** (vs 12 weeks from scratch)

---

## Next Steps

1. ✅ Get approval on hybrid approach
2. Start with Phase 1: Enhanced discovery in project-analysis
3. Prototype API extraction for 2 frameworks (FastAPI + Express)
4. Test on real repositories
5. Iterate based on findings

---

**Status:** Ready to proceed with hybrid approach, pending approval
