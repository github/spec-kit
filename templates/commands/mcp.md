---
description: Generate a project-specific MCP server for automated testing, process management, and browser automation
handoffs:
  - label: Validate with MCP
    agent: speckit.validate
    prompt: Run integration tests using the MCP server
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

# Generate Project MCP Server

You are a **DevOps Engineer**. Your job is to create and configure an MCP (Model Context Protocol) server tailored to the project's technology stack.

## User Input

```text
$ARGUMENTS
```

Consider user input for customization (tech stack, services, ports).

---

## What This Command Does

Creates a custom MCP server in `.mcp/project-server/` that provides Claude Code with tools to:

1. **Manage Services**: Start/stop backend, frontend, databases, microservices
2. **Monitor Logs**: View and filter logs from running processes
3. **Browser Testing**: Automate web UI testing with Playwright
4. **API Testing**: Make HTTP requests and validate responses
5. **Docker**: Manage Docker Compose services

---

## Phase 1: Project Analysis

### Step 1.1: Detect Technology Stack

Analyze the project to identify:

```bash
# Check for common project markers
ls -la package.json pom.xml build.gradle Cargo.toml go.mod requirements.txt Gemfile 2>/dev/null

# Check for Docker
ls -la docker-compose.yml docker-compose.yaml Dockerfile 2>/dev/null

# Check for frontend frameworks
ls -la vite.config.* next.config.* nuxt.config.* angular.json 2>/dev/null
```

Create a stack profile:

| Component | Detection | Typical Command |
|-----------|-----------|-----------------|
| **Java/Spring** | `pom.xml`, `build.gradle` | `./mvnw spring-boot:run` |
| **Node.js** | `package.json` | `npm run dev` or `npm start` |
| **Python** | `requirements.txt`, `pyproject.toml` | `python -m flask run` or `uvicorn` |
| **Go** | `go.mod` | `go run .` |
| **Rust** | `Cargo.toml` | `cargo run` |
| **Ruby** | `Gemfile` | `rails server` |
| **Frontend (Vite)** | `vite.config.*` | `npm run dev` (port 5173) |
| **Frontend (Next)** | `next.config.*` | `npm run dev` (port 3000) |
| **Docker** | `docker-compose.yml` | `docker compose up` |

### Step 1.2: Identify Services

Based on project structure, identify services to manage:

```
project/
├── backend/          → Service: backend (Java/Node/Python)
├── frontend/         → Service: frontend (Vite/Next/etc.)
├── api/              → Service: api (if separate)
├── gateway/          → Service: gateway (if microservices)
├── docker-compose.yml → Docker services (db, redis, etc.)
└── services/
    ├── auth/         → Service: auth
    └── orders/       → Service: orders
```

### Step 1.3: Detect Ports and Health Endpoints

Read configuration files to find ports:

```bash
# From application.properties/yml
grep -r "server.port" . 2>/dev/null

# From package.json scripts
grep -E '"(dev|start)"' package.json 2>/dev/null

# From docker-compose.yml
grep -A5 "ports:" docker-compose.yml 2>/dev/null
```

Common health endpoints:
- Spring Boot: `/actuator/health`
- Express: `/health` or `/api/health`
- Django: `/health/`
- FastAPI: `/health`

---

## Phase 2: Generate MCP Server

### Step 2.1: Create Directory Structure

```bash
mkdir -p .mcp/project-server/src/tools
```

### Step 2.2: Copy Template Files

Copy from `templates/mcp/project-server/`:

| Source | Destination |
|--------|-------------|
| `package.json` | `.mcp/project-server/package.json` |
| `tsconfig.json` | `.mcp/project-server/tsconfig.json` |
| `src/index.ts` | `.mcp/project-server/src/index.ts` |
| `src/tools/*.ts` | `.mcp/project-server/src/tools/*.ts` |
| `README.md` | `.mcp/project-server/README.md` |

### Step 2.3: Generate Configuration

Create `.mcp/project-server/src/config.ts` with detected services:

```typescript
export const config: ProjectConfig = {
  name: "{{PROJECT_NAME}}",
  rootDir: "{{ABSOLUTE_PROJECT_PATH}}",

  services: [
    // Generated based on detected stack
    {
      name: "backend",
      command: "{{DETECTED_COMMAND}}",
      cwd: "{{DETECTED_PATH}}",
      env: { /* detected env vars */ },
      healthCheck: {
        url: "{{DETECTED_HEALTH_URL}}",
        expectedStatus: 200,
        timeout: 60000
      }
    },
    // ... more services
  ],

  docker: {
    composeFile: "docker-compose.yml",
    services: [/* detected docker services */]
  },

  browser: {
    baseUrl: "{{FRONTEND_URL}}",
    headless: false
  },

  api: {
    baseUrl: "{{API_BASE_URL}}",
    defaultHeaders: {
      "Content-Type": "application/json"
    }
  }
};
```

### Step 2.4: Replace Placeholders

Replace all `{{PLACEHOLDER}}` tokens in copied files:

| Placeholder | Value |
|-------------|-------|
| `{{PROJECT_NAME}}` | Directory name or from package.json |
| `{{PROJECT_ROOT}}` | Absolute path to project root |
| `{{MCP_PATH}}` | Absolute path to `.mcp/project-server` |

---

## Phase 3: Interactive Configuration

### Step 3.1: Confirm Detected Services

Present detected configuration to user:

```markdown
## Detected Services

| Service | Command | Health Check |
|---------|---------|--------------|
| backend | `./mvnw spring-boot:run` | http://localhost:8080/actuator/health |
| frontend | `npm run dev` | http://localhost:5173 |

## Docker Services

- db (PostgreSQL)
- redis

## Configuration

- **API Base URL**: http://localhost:8080/api
- **Browser Base URL**: http://localhost:5173

Is this correct? (yes/no/edit)
```

### Step 3.2: Handle Edits

If user wants to edit:

1. Ask which service to modify
2. Ask for correct values (command, port, health endpoint)
3. Update configuration

### Step 3.3: Add Custom Services

Ask if user wants to add additional services:

```markdown
Do you have additional services to configure?

Examples:
- "auth service on port 8081"
- "worker process: npm run worker"
- "microservice in services/payments"

Enter service details or "done" to continue:
```

---

## Phase 4: Installation

### Step 4.1: Install Dependencies

```bash
cd .mcp/project-server && npm install
```

### Step 4.2: Build Server

```bash
cd .mcp/project-server && npm run build
```

### Step 4.3: Install Playwright (if browser testing)

```bash
cd .mcp/project-server && npx playwright install chromium
```

---

## Phase 5: Claude Code Integration

### Step 5.1: Generate MCP Configuration

Create or update `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "project": {
      "command": "node",
      "args": ["{{PROJECT_ROOT}}/.mcp/project-server/dist/index.js"]
    }
  }
}
```

### Step 5.2: Add to .gitignore

Ensure `.mcp/project-server/node_modules/` and `.mcp/project-server/dist/` are ignored:

```bash
echo ".mcp/project-server/node_modules/" >> .gitignore
echo ".mcp/project-server/dist/" >> .gitignore
```

---

## Phase 6: Validation

### Step 6.1: Test MCP Server

```bash
cd .mcp/project-server && npm run inspect
```

Verify all tools are listed:
- Process tools: `start_service`, `stop_service`, etc.
- Browser tools: `browser_open`, `browser_click`, etc.
- API tools: `api_get`, `api_post`, etc.

### Step 6.2: Test Service Start

Quick validation:

```bash
# Start Docker if configured
docker compose up -d

# Verify services can be started (dry run)
node .mcp/project-server/dist/index.js --test
```

---

## Output

### Summary Report

```markdown
## MCP Server Generated

**Location**: `.mcp/project-server/`

### Configured Services

| Service | Command | Port | Health |
|---------|---------|------|--------|
| backend | ./mvnw spring-boot:run | 8080 | ✓ |
| frontend | npm run dev | 5173 | ✓ |

### Docker Services

- db (PostgreSQL:5432)
- redis (6379)

### Available Tools

**Process Management**: start_service, stop_service, services_status, service_logs, health_check
**Browser Testing**: browser_open, browser_click, browser_fill, browser_screenshot, ...
**API Testing**: api_get, api_post, api_put, api_delete, api_test

### Next Steps

1. Restart Claude Code to load the MCP server
2. Use `/speckit.validate` to run integration tests
3. Or use tools directly: `start_service backend`

### Files Created

- `.mcp/project-server/` - MCP server code
- `.claude/mcp.json` - Claude Code configuration
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Cannot find module" | Run `npm run build` in `.mcp/project-server/` |
| "Playwright not found" | Run `npx playwright install chromium` |
| "Port already in use" | Check for existing processes on detected ports |
| "Health check failed" | Verify health endpoint URL and timeout |

### Manual Configuration

If auto-detection fails, manually edit `.mcp/project-server/src/config.ts`:

```typescript
services: [
  {
    name: "my-service",
    command: "my-command",
    cwd: "path/to/service",
    healthCheck: {
      url: "http://localhost:PORT/health",
      timeout: 30000
    }
  }
]
```

Then rebuild: `npm run build`
