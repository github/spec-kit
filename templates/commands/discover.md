# Project Discovery Command

**Purpose:** Automatically discover all projects in the repository, regardless of technology or architecture.

**Token Optimization:** Metadata-only scanning (500-1,000 tokens first run, 0 tokens when cached)

---

## Usage

```bash
# Basic discovery (scan repository for all projects)
/speckit.discover

# Use cached results (instant, 0 tokens)
/speckit.discover --cached

# Force rescan (ignore cache)
/speckit.discover --force

# JSON output (for programmatic use)
/speckit.discover --json
```

---

## What It Does

1. **Scans repository** for project indicators:
   - Node.js: package.json
   - Python: requirements.txt, pyproject.toml, setup.py
   - Go: go.mod
   - Rust: Cargo.toml
   - Java: pom.xml, build.gradle
   - C#: *.csproj, *.sln
   - Ruby: Gemfile
   - PHP: composer.json
   - C/C++: CMakeLists.txt, Makefile

2. **Extracts metadata** (no file content reads):
   - Project location and name
   - Technology and framework detection
   - Project type classification
   - Size metrics (file count, total bytes)

3. **Classifies projects**:
   - Backend API (FastAPI, Express, Gin, Spring Boot, ASP.NET Core)
   - Frontend (React, Vue, Angular, Svelte)
   - CLI Tool (Rust binaries, Python scripts)
   - Library (shared code, packages)
   - Mobile App (React Native, Flutter)
   - Monolith (Django, Rails)

4. **Caches results**:
   - Saves to `.speckit/cache/discovery.json`
   - Uses MD5 hash for cache invalidation
   - Detects structural changes automatically

---

## Output Example

```
===============================================
 PROJECT DISCOVERY REPORT
===============================================
Scanned: 2025-11-07T15:30:00Z
Repository: C:\repos\my-app
Total Projects: 3

-----------------------------------------------
PROJECT: spec-kit
-----------------------------------------------
Type: python (library)
Framework: Not detected
Location: .
Indicator: pyproject.toml
Size: 127 files (1.2 MB)
Last Modified: 2025-11-07T10:15:00Z

-----------------------------------------------
PROJECT: api
-----------------------------------------------
Type: nodejs (backend-api)
Framework: Express (detected from package.json)
Location: services\api
Indicator: package.json
Size: 45 files (256 KB)
Last Modified: 2025-11-06T14:22:00Z

-----------------------------------------------
PROJECT: frontend
-----------------------------------------------
Type: nodejs (frontend)
Framework: React (detected from package.json)
Location: apps\frontend
Indicator: package.json
Size: 89 files (512 KB)
Last Modified: 2025-11-07T09:45:00Z

===============================================
SUMMARY
===============================================
- Python projects: 1
- Node.js projects: 2
- Backend APIs: 1
- Frontend apps: 1
- Libraries: 1

Cache saved to: .speckit\cache\discovery.json
Run with --cached flag for instant results (0 tokens)
```

---

## JSON Output Example

```json
{
  "version": "1.0",
  "scanned_at": "2025-11-07T15:30:00Z",
  "repo_root": "C:\\repos\\my-app",
  "cache_hash": "a3f2b9c8d7e6f5a4b3c2d1e0f9a8b7c6",
  "total_projects": 3,
  "projects": [
    {
      "id": "spec-kit",
      "name": "spec-kit",
      "path": ".",
      "abs_path": "C:\\repos\\my-app",
      "type": "python",
      "technology": {
        "language": "python",
        "framework": null
      },
      "indicator_file": "pyproject.toml",
      "classification": "library",
      "size_bytes": 1258291,
      "file_count": 127,
      "last_modified": "2025-11-07T10:15:00Z"
    }
  ]
}
```

---

## Token Optimization

| Scenario | Token Usage | Time |
|----------|-------------|------|
| **First scan** | 500-1,000 | 2-5 seconds |
| **Cached scan** | 0 | < 100ms |
| **Force rescan** | 500-1,000 | 2-5 seconds |

**Cache invalidation:** Automatic when:
- New project added (new indicator file)
- Project removed (indicator file deleted)
- Project moved (path changed)

**Cache preserved when:**
- Code changes within existing projects
- Documentation updates
- Configuration changes

---

## Integration with Other Commands

After discovery, use other commands:

```bash
# 1. Discover all projects
/speckit.discover

# 2. Onboard projects (create specs structure)
/speckit.onboard --all

# 3. Reverse engineer existing code
/speckit.reverse-engineer --project=api

# 4. Generate unified catalog
/speckit.project-catalog

# 5. Analyze specific project
/speckit.project-analysis --project=api
```

---

## Cache Management

**Cache location:** `.speckit/cache/discovery.json`

**Cache structure:**
```json
{
  "version": "1.0",
  "scanned_at": "2025-11-07T15:30:00Z",
  "repo_root": "C:\\repos\\my-app",
  "cache_hash": "a3f2b9c8d7e6f5a4b3c2d1e0f9a8b7c6",
  "total_projects": 3,
  "projects": [...]
}
```

**Manual cache clear:**
```bash
# Delete cache file
Remove-Item .speckit\cache\discovery.json

# Or force rescan
/speckit.discover --force
```

---

## Excluded Directories

Discovery automatically skips:
- node_modules/
- .venv/, venv/, env/
- .git/
- dist/, build/, out/
- target/ (Rust)
- bin/, obj/ (C#)
- __pycache__/, *.pyc
- .next/, .nuxt/
- coverage/

---

## Implementation

**Script:** `scripts/powershell/project-analysis.ps1`

**Key functions:**
- `Get-ProjectIndicators` - Pattern definitions
- `Find-Projects` - Metadata scanning
- `Invoke-ProjectDiscovery` - Orchestration
- `Get-CacheHash` - Cache validation
- `Format-DiscoveryReport` - Output formatting

---

## Requirements

- PowerShell 5.1+ (Windows) or PowerShell Core 7+ (cross-platform)
- No external dependencies
- Works on any repository structure

---

## Next Steps After Discovery

1. **Review discovered projects:**
   - Verify detection accuracy
   - Check project classifications
   - Note any missing projects

2. **Onboard selected projects:**
   ```bash
   /speckit.onboard --project=api
   /speckit.onboard --all
   ```

3. **Start using spec-kit workflows:**
   - Create specs for new features
   - Reverse engineer existing code
   - Generate documentation

---

**Status:** ✅ Phase 1 Complete - Discovery engine ready for Windows testing
