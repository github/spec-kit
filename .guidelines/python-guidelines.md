# Python Corporate Guidelines

**Tech Stack**: Python, Django, Flask, FastAPI, Backend Services, APIs, Data Processing
**Auto-detected from**: `requirements.txt`, `pyproject.toml`, `setup.py`, or `*.py` files
**Version**: 1.0

---

## Scaffolding

**MUST**:

- Use corporate scaffolding command (`YOUR_ORG.cli create-service`)
- Choose appropriate framework template (fastapi, django, flask)

**NEVER**:

- Use public `django-admin startproject` or `flask init` directly

**Rationale**: Corporate scaffolding includes security, logging, monitoring, compliance from day one

---

## Package Registry

**MUST**:

- Configure `pip.conf` with corporate PyPI repository (Artifactory/Nexus)
- All packages resolved through corporate registry only

**NEVER**:

- Install packages from public pypi.org directly

---

## Mandatory Libraries

### Framework Starter

**MUST** use: `YOUR_ORG-fastapi-starter` or equivalent for chosen framework
**Includes**: Security, logging, metrics, error handling, CORS, health checks
**Integration**: Use `create_app()` factory function with corporate configuration

### Authentication

**MUST** use: `YOUR_ORG-auth` package
**Requirements**:

- Decorate endpoints with `@require_auth` and `@require_roles()` decorators
- Extract authenticated user via `get_current_user()` dependency
- Pass user context to all service layer calls

### API Client

**MUST** use: `YOUR_ORG-http-client` package
**Requirements**:

- Use `AcmecorpHttpClient` class for external API calls
- Configure timeout, retry attempts, circuit breaker
- Never use raw `requests` or `httpx` directly

**Features**: Automatic retry, timeout handling, distributed tracing, circuit breaking

### Database (SQL)

**MUST** use: SQLAlchemy with Alembic for migrations
**MUST** use: `YOUR_ORG-sqlalchemy-utils` for corporate extensions
**Requirements**:

- Entities inherit from `AuditMixin` for automatic audit trail (created_by, created_at, updated_by, updated_at)
- Use Alembic for schema migrations
- Apply migrations on deployment

### Database (NoSQL)

**SHOULD** use: Motor (async MongoDB) or corporate MongoDB wrapper if available

### Logging

**MUST** use: Standard Python logging with corporate configuration
**Requirements**:

- Use structured logging with JSON formatter
- Include correlation ID in all log statements
- Never log PII, secrets, passwords, or tokens

**NEVER**:

- Use `print()` statements for logging

### Validation

**MUST** use: Pydantic for request/response validation
**Requirements**:

- Define Pydantic models for all API requests and responses
- Use field validators for custom validation logic
- Return 422 Unprocessable Entity for validation errors

---

## Banned Libraries

**NEVER** use:

- Raw `requests` or `httpx` → Use `YOUR_ORG-http-client`
- Direct JWT handling → Use `YOUR_ORG-auth`
- `print()` statements → Use proper logging

**Rationale**: Corporate libraries enforce security, observability, compliance

---

## Architecture

### Project Structure

**MUST** follow: Layered architecture (Routes → Services → Repositories)

- **Routes/Controllers**: Endpoint definitions, request/response handling
- **Services**: Business logic layer
- **Repositories**: Data access layer
- **Models**: Database entities and Pydantic schemas

### Separation of Concerns

**MUST**:

- Keep route handlers thin (validation, serialization only)
- Put business logic in service layer
- Use repository pattern for database access
- Never put business logic in routes or repositories

### Type Hints

**MUST**:

- Use type hints for all function parameters and return values
- Use `typing` module for complex types (List, Dict, Optional, Union)
- Enable type checking with mypy or pyright

### Error Handling

**MUST**:

- Use exception handling middleware for centralized error responses
- Return generic error messages to clients (no internal details)
- Log full exception details server-side with traceback

---

## Security

### Input Validation

**MUST**:

- Validate all API inputs using Pydantic models
- Return 422 Unprocessable Entity for validation failures
- Sanitize user inputs before processing

### SQL Injection Prevention

**MUST**:

- Use SQLAlchemy ORM (parameterized queries automatic)
- Never concatenate strings for SQL queries
- Use query parameters for all dynamic values

### Secrets Management

**MUST**:

- Store secrets in environment variables or corporate secrets manager
- Load secrets via configuration management (never hardcode)
- Use `.env` files for local development (gitignored)

**NEVER**:

- Hardcode secrets in code or configuration files
- Commit secrets to source control

### Authentication & Authorization

**MUST**:

- Validate user roles before resource access
- Use `@require_auth` and `@require_roles()` decorators on protected endpoints
- Implement principle of least privilege

---

## Coding Standards

### Python Version

**MUST**:

- Use Python 3.10+ (prefer latest stable version)
- Use modern Python features (dataclasses, type hints, pattern matching)

### Code Style

**MUST**:

- Follow PEP 8 style guide
- Use Black formatter for consistent formatting
- Use isort for import sorting
- Use flake8 or ruff for linting

### Naming Conventions

**MUST** follow:

- Functions, variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`
- Modules: `lowercase` or `snake_case`

### Async/Await

**SHOULD**:

- Use async/await for I/O-bound operations (database, HTTP, file system)
- Use asyncio-compatible libraries (motor, httpx, asyncpg)
- Choose FastAPI for async workloads, Django for sync

### Code Quality

**SHOULD**:

- Keep functions under 50 lines
- Limit cyclomatic complexity (< 10 per function)
- Write docstrings for public functions and classes
- Use meaningful names (no abbreviations, no single letters except loops)

---

## Dependency Management

### Requirements Files

**MUST**:

- Use `requirements.txt` for production dependencies
- Use `requirements-dev.txt` for development dependencies
- Pin versions for reproducible builds

**SHOULD**:

- Use `poetry` or `pipenv` for advanced dependency management
- Use virtual environments for all projects

### Virtual Environments

**MUST**:

- Use virtual environments (venv, virtualenv, poetry, pipenv)
- Never install packages globally
- Document Python version in `runtime.txt` or `pyproject.toml`

---

## Testing

**MUST**:

- Write unit tests with pytest
- Write integration tests for API endpoints
- Aim for 80%+ coverage on critical paths

**SHOULD**:

- Use fixtures for test data
- Use factories (factory_boy) for model creation
- Mock external dependencies (APIs, databases)

---

## Build & Deployment

### Build Process

**MUST**:

- Run tests before deployment (`pytest`)
- Run linters before deployment (flake8, mypy, black)
- Use CI/CD pipeline for automated testing

### Docker

**MUST**:

- Use multi-stage builds (install dependencies in build stage)
- Use official Python base images (python:3.11-slim)
- Run as non-root user in container
- Copy only necessary files (use .dockerignore)

**SHOULD**:

- Keep container images small (< 200MB for simple services)
- Use layer caching for faster builds

---

## Observability

**MUST** include:

- Health checks endpoint (`/health`) for readiness/liveness probes
- Metrics endpoint (`/metrics`) for monitoring (Prometheus format)
- Distributed tracing with correlation IDs
- Structured logging with JSON format

**Note**: Corporate FastAPI/Django starter includes all observability features by default

---

## Non-Compliance

If corporate library unavailable or causes blocking issue:

1. Document violation in `.guidelines-todo.md` with justification
2. Create ticket to resolve (target: next sprint)
3. Proceed with alternative, mark with `# TODO: GUIDELINE-VIOLATION` comment for tracking
