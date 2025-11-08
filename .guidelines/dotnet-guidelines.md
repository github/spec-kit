# .NET Corporate Guidelines

**Tech Stack**: .NET, C#, ASP.NET Core, Backend Services, Microservices
**Auto-detected from**: `*.csproj`, `*.sln`, or `*.cs` files
**Version**: 1.0

---

## Scaffolding

**MUST**:

- Use corporate dotnet templates (YOUR_ORG-webapi, YOUR_ORG-minimal-api, YOUR_ORG-worker, YOUR_ORG-blazor)
- Install templates from corporate NuGet source

**NEVER**:

- Use default Microsoft templates (`dotnet new webapi`)

**Rationale**: Corporate templates include security, logging, monitoring, compliance from day one

---

## Package Registry

**MUST**:

- Configure `nuget.config` with corporate NuGet source (YOUR_ORG NuGet registry)
- All packages resolved through corporate registry only

**NEVER**:

- Install packages from public NuGet.org directly

---

## Mandatory Libraries

### ASP.NET Core Starter

**MUST** use: `YOUR_ORG.AspNetCore.Starter` package
**Includes**: Security, logging, monitoring, health checks, exception handling, CORS
**Integration**: Register services via `AddYourOrgServices()`, apply middleware via `UseYourOrgMiddleware()`

### Security & Authentication

**MUST** use: `YOUR_ORG.Security` package
**Requirements**:

- Decorate endpoints with `[SecuredEndpoint(Roles = "...")]` attribute
- Extract authenticated user context via `User.GetCurrentUser()`
- Pass user context to all service layer calls

### HTTP Client

**MUST** use: `YOUR_ORG.HttpClient` package
**Requirements**:

- Inject via `IYourOrgHttpClientFactory`, never create HttpClient directly
- Use circuit breaker pattern with fallback methods
- All external API calls auto-instrumented for distributed tracing

**Features**: Service discovery, circuit breaker, retry logic, timeout handling, distributed tracing

### Database

**MUST** use: Entity Framework Core with `YOUR_ORG.EntityFrameworkCore.Extensions`
**Requirements**:

- Entities inherit from `AuditedEntity` for automatic audit trail (CreatedBy, CreatedAt, UpdatedBy, UpdatedAt)
- Use EF Core migrations for schema changes (`dotnet ef migrations add`)
- Apply migrations on deployment (`dotnet ef database update`)

### Logging

**MUST** use: `YOUR_ORG.Logging` package (built on Microsoft.Extensions.Logging)
**Requirements**:

- Inject `ILogger<T>` via dependency injection
- Use structured logging with named parameters
- Include correlation ID in all log statements (auto-added by corporate middleware)

**NEVER**:

- Use `Console.WriteLine()` for logging
- Log PII, secrets, passwords, or authentication tokens

### Validation

**MUST** use: FluentValidation with `YOUR_ORG.Validators` extensions
**Requirements**:

- Create validator classes inheriting `AbstractValidator<T>`
- Use corporate validators for common patterns (e.g., `CorporateEmail()`)
- Validate all API inputs before processing

---

## Banned Libraries

**NEVER** use:

- `HttpClient` directly → Use `YOUR_ORG.HttpClient`
- Serilog without corporate wrapper → Use `YOUR_ORG.Logging`
- `Console.WriteLine()` → Use `ILogger<T>`

**Rationale**: Corporate wrappers add security, monitoring, compliance, circuit breaking

---

## Architecture

### Project Structure

**MUST** follow: Layered architecture (API → Core → Infrastructure)

- **API Layer**: Controllers, Program.cs, appsettings.json
- **Core Layer**: Services, Domain Models, Interfaces
- **Infrastructure Layer**: Data, Repositories, External Integrations

### Separation of Concerns

**MUST**:

- Keep controllers thin (routing, validation, response formatting only)
- Put business logic in service layer
- Use repository pattern for data access
- Never put business logic in controllers or repositories

### DTOs (Data Transfer Objects)

**MUST**:

- Use separate DTOs for API contracts (never expose entities directly)
- Keep sensitive fields (PasswordHash, InternalId) in entities only
- Use `record` types for immutable DTOs

### Exception Handling

**MUST**:

- Use centralized exception handling middleware
- Return generic error messages to clients (no internal details)
- Log full exception details server-side with correlation ID

---

## Security

### Input Validation

**MUST**:

- Validate all API inputs (ModelState, FluentValidation)
- Return 400 Bad Request for validation failures
- Reject requests before reaching business logic

### SQL Injection Prevention

**MUST**:

- Use Entity Framework Core (parameterized queries automatic)
- Never concatenate strings for SQL queries
- Use LINQ or stored procedures only

### Secrets Management

**MUST**:

- Store secrets in Azure Key Vault or corporate secrets manager
- Access secrets via configuration (`builder.Configuration["YourOrg:ApiKey"]`)

**NEVER**:

- Hardcode secrets in code or appsettings.json
- Commit secrets to source control

### Authentication & Authorization

**MUST**:

- Validate user roles before resource access
- Use `[SecuredEndpoint]` attribute on all protected endpoints
- Implement principle of least privilege

---

## Coding Standards

### .NET Version & Features

**MUST**:

- Target .NET 6+ (prefer latest LTS version)
- Enable nullable reference types (`<Nullable>enable</Nullable>`)
- Use modern C# features (record types, pattern matching, global usings)

### Async/Await

**MUST**:

- Use async/await for all I/O operations (database, HTTP, file system)
- Never block on async calls (no `.Result` or `.Wait()`)
- Use `ValueTask<T>` for hot paths if applicable

### Dependency Injection

**MUST**:

- Use constructor injection for all dependencies
- Register services with appropriate lifetime (Singleton, Scoped, Transient)
- Never use `new` for services (except POCOs, DTOs)

### Naming Conventions

**MUST** follow:

- Classes, Methods, Properties: `PascalCase`
- Local variables, parameters: `camelCase`
- Private fields: `_camelCase` with underscore prefix
- Constants: `PascalCase`
- Interfaces: `IPascalCase` with I prefix

### Code Quality

**SHOULD**:

- Keep methods under 50 lines
- Limit cyclomatic complexity (< 10 per method)
- Follow SOLID principles
- Write meaningful names (no abbreviations, no single letters except loop counters)

---

## Build & Deployment

### Build Process

**MUST**:

- Use `dotnet build` for compilation
- Use `dotnet publish -c Release` for deployment packages
- Run tests before deployment (`dotnet test`)

### Docker

**MUST**:

- Use multi-stage builds (SDK for build, runtime for runtime)
- Use official Microsoft base images (mcr.microsoft.com/dotnet)
- Run as non-root user in container
- Copy only necessary files (use .dockerignore)

**SHOULD**:

- Keep container images small (runtime-only, no SDK)
- Use layer caching for faster builds

---

## Observability

**MUST** include:

- Health checks endpoint (`/health`) for readiness/liveness probes
- Metrics endpoint (`/metrics`) for monitoring (Prometheus format)
- Distributed tracing with correlation IDs
- Structured logging with context (user, request, operation)

**Note**: Corporate ASP.NET Core starter includes all observability features by default

---

## Non-Compliance

If corporate library unavailable or causes blocking issue:

1. Document violation in `.guidelines-todo.md` with justification
2. Create ticket to resolve (target: next sprint)
3. Proceed with alternative, mark with `// TODO: GUIDELINE-VIOLATION` comment for tracking
