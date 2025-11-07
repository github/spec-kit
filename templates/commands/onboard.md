# Project Onboarding Command

**Purpose:** Onboard existing projects discovered in Phase 1/2 by creating a parallel `.speckit/` structure without modifying existing code.

**Token Optimization:** Non-invasive (0 tokens - no code analysis, pure file operations)

---

## Usage

```bash
# Onboard all discovered projects
/speckit.onboard --all

# Onboard specific projects
/speckit.onboard --projects="api,frontend"

# Use discovery cache
/speckit.onboard --all --from-discovery

# Choose constitution type
/speckit.onboard --all --constitution=microservices

# Dry run (see what would happen)
/speckit.onboard --all --dry-run

# Force re-onboarding
/speckit.onboard --all --force
```

---

## What It Does

### 1. Creates Directory Structure

```
.speckit/                   ← Spec-kit metadata (gitignore optional)
  ├── config.json           ← Main configuration
  ├── metadata/             ← Per-project metadata
  │   ├── api.json
  │   ├── frontend.json
  │   └── ...
  └── cache/                ← Discovery cache (Phase 1/2)
      └── discovery.json

specs/                      ← Specifications (commit to git)
  ├── constitution.md       ← Platform principles
  └── projects/             ← Per-project specs
      ├── api/
      │   ├── README.md
      │   ├── 001-existing-code/  ← Reverse-engineered (Phase 4)
      │   └── 002-new-feature/    ← New development
      ├── frontend/
      │   └── README.md
      └── ...
```

### 2. Generates Configuration

**`.speckit/config.json`:**
```json
{
  "version": "1.0",
  "initialized_at": "2025-11-07T16:00:00Z",
  "repo_root": "/path/to/repo",
  "discovery": {
    "last_scan": "2025-11-07T15:00:00Z",
    "total_projects": 3,
    "deep_analysis_enabled": true
  },
  "projects": [
    {
      "id": "api",
      "name": "api",
      "path": "services/api",
      "type": "backend-api",
      "technology": "nodejs",
      "framework": "Express",
      "onboarded_at": "2025-11-07T16:00:00Z",
      "spec_dir": "projects/api",
      "metadata_file": "metadata/api.json",
      "constitution": "constitution.md",
      "status": "onboarded"
    }
  ],
  "constitution": {
    "type": "universal",
    "path": "constitution.md"
  },
  "settings": {
    "auto_discovery": false,
    "deep_analysis_default": false,
    "template_preference": "standard"
  }
}
```

### 3. Creates Project Metadata

**`.speckit/metadata/api.json`:**
```json
{
  "id": "api",
  "name": "api",
  "path": "services/api",
  "type": "backend-api",
  "technology": "nodejs",
  "framework": "Express",
  "onboarded_at": "2025-11-07T16:00:00Z",
  "discovery_info": {
    "size_bytes": 262144,
    "file_count": 45,
    "last_modified": "2025-11-06T14:22:00Z",
    "indicator_file": "package.json"
  },
  "runtime": "nodejs",
  "runtime_version": "18.x",
  "build_tools": ["typescript", "webpack"],
  "test_frameworks": ["jest"],
  "key_dependencies": ["express", "pg", "jsonwebtoken"]
}
```

### 4. Creates Project README

**`specs/projects/api/README.md`:**
- Project overview
- Technology stack
- Quick reference
- Getting started guide
- Links to existing code

### 5. Sets Up Constitution

Copies appropriate constitution template:
- **Universal:** For mixed projects (default)
- **Microservices:** For microservices architecture
- **Custom:** User-provided template

---

## Output Example

```
================================
 Spec-Kit Onboarding (Phase 3)
================================

Step 1: Initializing spec-kit structure...
  Created: .speckit
  Created: .speckit/metadata
  Created: .speckit/cache
  Created: specs
  Created: specs/projects

Step 2: Loading discovery results...
  Found 3 projects

Step 3: Loading configuration...
  Creating new spec-kit configuration

Step 4: Setting up constitution...
  Created constitution: specs/constitution.md (universal)

Step 5: Selecting projects...
  Selected: All 3 projects

Step 6: Onboarding projects...

Onboarding: api
  ID: services-api
  Path: services/api
  Type: backend-api
  Technology: nodejs
  Framework: Express
  ✓ Onboarded successfully

Onboarding: frontend
  ID: apps-frontend
  Path: apps/frontend
  Type: frontend
  Technology: nodejs
  Framework: React
  ✓ Onboarded successfully

Onboarding: mobile
  ID: apps-mobile
  Path: apps/mobile
  Type: mobile
  Technology: nodejs
  Framework: React Native
  ✓ Onboarded successfully

Step 7: Saving configuration...

================================
 Onboarding Complete!
================================

Results:
  ✓ Successfully onboarded: 3

Structure created:
  .speckit/config.json        - Configuration
  .speckit/metadata/          - Project metadata
  specs/constitution.md       - Platform principles
  specs/projects/*/           - Project specifications

Next steps:
  1. Review specs/constitution.md and customize
  2. Explore specs/projects/{project-id}/ for each project
  3. Use /speckit.specify to create new features
  4. Run Phase 4 reverse engineering: /speckit.reverse-engineer
```

---

## JSON Output Example

```bash
# Get structured JSON output
/speckit.onboard --all --from-discovery --json
```

```json
{
  "success": true,
  "onboarded": 3,
  "skipped": 0,
  "total": 3,
  "config_file": ".speckit/config.json",
  "constitution": "specs/constitution.md",
  "projects": [
    {
      "id": "api",
      "name": "api",
      "spec_dir": "projects/api",
      "status": "onboarded"
    },
    {
      "id": "frontend",
      "name": "frontend",
      "spec_dir": "projects/frontend",
      "status": "onboarded"
    },
    {
      "id": "mobile",
      "name": "mobile",
      "spec_dir": "projects/mobile",
      "status": "onboarded"
    }
  ]
}
```

---

## Options

### Constitution Types

**Universal (default):**
- General-purpose principles
- Works for any architecture
- Includes: quality, testing, security, deployment standards

**Microservices:**
- Service-specific guidelines
- API and event contracts
- Service boundaries and ownership
- Inter-service communication

**Custom:**
- Provide your own constitution template
- Place at `templates/constitution-custom.md`

### Selection Modes

**All Projects:**
```bash
/speckit.onboard --all
```

**Specific Projects:**
```bash
# By ID (from discovery)
/speckit.onboard --projects="api,frontend"
```

### Dry Run Mode

```bash
# See what would happen without making changes
/speckit.onboard --all --dry-run
```

**Output:**
```
[DRY RUN] Would create: .speckit
[DRY RUN] Would create: specs
[DRY RUN] Would copy constitution: templates/constitution-universal.md
[DRY RUN] Would create spec directory: specs/projects/api
[DRY RUN] Would save metadata: .speckit/metadata/api.json
[DRY RUN] Would save config: .speckit/config.json
```

### Force Mode

```bash
# Re-onboard already onboarded projects
/speckit.onboard --all --force
```

**Use cases:**
- Update metadata after discovery changes
- Regenerate README files
- Switch constitution type

---

## Integration with Other Commands

### Complete Workflow

```bash
# Step 1: Discover projects (Phase 1/2)
/speckit.discover --deep-analysis

# Step 2: Onboard projects (Phase 3)
/speckit.onboard --all --from-discovery

# Step 3: Reverse engineer existing code (Phase 4)
/speckit.reverse-engineer --project=api

# Step 4: Generate project catalog (Phase 5)
/speckit.project-catalog

# Step 5: Start developing new features
cd specs/projects/api
mkdir 002-oauth-integration
/speckit.specify
/speckit.plan
/speckit.implement
```

---

## Configuration Management

### View Configuration

```bash
# View current configuration
cat .speckit/config.json | jq
```

### View Project Metadata

```bash
# View specific project metadata
cat .speckit/metadata/api.json | jq
```

### Update Configuration

Configuration can be updated manually or via re-onboarding:

```bash
# Re-onboard with force to update
/speckit.onboard --all --force
```

---

## Gitignore Recommendations

### Option 1: Commit Everything (Recommended)

```gitignore
# In .gitignore:
.speckit/cache/       # Exclude only cache
```

**Rationale:**
- Configuration tracks onboarded projects
- Metadata is useful for team members
- Specifications should be in version control

### Option 2: Exclude .speckit/ Entirely

```gitignore
# In .gitignore:
.speckit/             # Exclude all spec-kit metadata
```

**Rationale:**
- Each developer onboards independently
- Good for experimenting with spec-kit
- Configuration not shared across team

### Option 3: Commit Only Specs

```gitignore
# In .gitignore:
.speckit/             # Exclude all metadata
```

**Rationale:**
- Specs are the source of truth
- Metadata can be regenerated
- Simplest approach

---

## Troubleshooting

### Error: Discovery cache not found

**Problem:**
```
Discovery cache not found at: .speckit/cache/discovery.json
```

**Solution:**
```bash
# Run discovery first
/speckit.discover --deep-analysis

# Then onboard
/speckit.onboard --all --from-discovery
```

### Warning: Project already onboarded

**Problem:**
```
Already onboarded (use -Force to re-onboard)
```

**Solution:**
```bash
# Re-onboard with force
/speckit.onboard --all --force
```

### Error: Must specify -All or -Projects

**Problem:**
```
Must specify -All or -Projects <ids>
```

**Solution:**
```bash
# Specify which projects to onboard
/speckit.onboard --all
# OR
/speckit.onboard --projects="api,frontend"
```

---

## Token Optimization

| Operation | Token Usage | Time |
|-----------|-------------|------|
| **Onboarding** | 0 tokens | < 1 second |
| **No code analysis** | N/A | File operations only |
| **Pure structure creation** | N/A | No AI inference needed |

**Key:** Onboarding is purely file operations—no code reading, no AI inference, no tokens!

---

## Next Steps After Onboarding

### 1. Review Constitution

```bash
# Open and customize
vi specs/constitution.md
```

Add project-specific:
- Coding standards
- Deployment processes
- Team conventions
- Security requirements

### 2. Explore Project Specs

```bash
# Navigate to project
cd specs/projects/api

# Review README
cat README.md
```

### 3. Run Reverse Engineering (Phase 4)

```bash
# Extract APIs and data models from existing code
/speckit.reverse-engineer --project=api
```

### 4. Start New Feature Development

```bash
# Create new feature
cd specs/projects/api
mkdir 002-oauth-integration

# Use spec-kit workflow
/speckit.specify
/speckit.plan
/speckit.implement
```

---

## Implementation

**Script:** `scripts/powershell/onboard.ps1`

**Key functions:**
- `Initialize-SpeckitStructure` - Create directory structure
- `Get-DiscoveryResults` - Load discovery cache
- `Get-SpeckitConfig` - Load/create configuration
- `New-ProjectMetadata` - Generate metadata
- `Invoke-ProjectOnboarding` - Onboard single project
- `Copy-ConstitutionTemplate` - Set up constitution

---

## Requirements

- PowerShell 5.1+ (Windows) or PowerShell Core 7+ (cross-platform)
- Discovery cache (run `/speckit.discover` first)
- Write permissions to repository
- No external dependencies

---

**Status:** ✅ Phase 3 Ready - Non-invasive onboarding complete
