# Java Corporate Guidelines

**Tech Stack**: Java, Spring Boot, Backend Services, Microservices
**Auto-detected from**: `pom.xml`, `build.gradle`, or `*.java` files
**Version**: 1.0

---

## Scaffolding

**MUST**:

- Use corporate scaffolding command (`@YOUR_ORG/create-spring-app`)
- Choose appropriate template (microservice, monolith, batch)

**NEVER**:

- Use public Spring Initializr (`https://start.spring.io`)

**Alternative**: Internal Spring Initializr at `https://spring-init.YOUR_DOMAIN.com`

**Rationale**: Corporate scaffolding includes security, logging, monitoring, compliance from day one

---

## Package Registry

**MUST**:

- Configure Maven/Gradle with corporate artifact repository (Artifactory/Nexus)
- All dependencies resolved through corporate repository only
- Authenticate via `~/.m2/settings.xml` or `~/.gradle/gradle.properties`

**NEVER**:

- Download packages from public Maven Central directly

---

## Mandatory Libraries

### Spring Boot Starter

**MUST** use: Corporate Spring Boot parent POM (`YOUR_ORG-spring-boot-starter-parent`)
**MUST** use: `YOUR_ORG-spring-boot-starter-web` for web applications
**Includes**: Security, logging, monitoring, health checks, exception handling, CORS

### Security & Authentication

**MUST** use: `YOUR_ORG-security-spring-boot-starter` package
**Requirements**:

- Decorate endpoints with `@SecuredEndpoint(roles = {...})` annotation
- Extract authenticated user via `SecurityContextHolder.getCurrentUser()`
- Pass user context to all service layer calls

### API Client

**MUST** use: `YOUR_ORG-api-client` package
**Requirements**:

- Inject `ApiClient<T>` for external service calls
- Use `@CircuitBreaker` annotation with fallback methods
- Never create RestTemplate or WebClient manually

**Features**: Service discovery, load balancing, circuit breaker, retry, distributed tracing

### Database

**MUST** use: Spring Data JPA with `YOUR_ORG-jpa-extensions`
**Requirements**:

- Entities extend `AuditedEntity` for automatic audit trail
- Use repositories extending `JpaRepository` or `CrudRepository`
- Use Flyway for database migrations

### Logging

**MUST** use: SLF4J + Logback (included in corporate starter)
**Requirements**:

- Use `@Slf4j` annotation (Lombok) for logger injection
- Use structured logging with MDC for correlation IDs
- Use `@LogExecution` annotation for method-level logging

**NEVER**:

- Use `System.out.println()` for logging
- Use Log4j 1.x or `java.util.logging`

### Validation

**MUST** use: Jakarta Bean Validation with `YOUR_ORG-validators`
**Requirements**:

- Use `@Valid` annotation on request objects
- Define validation rules using Jakarta annotations (@NotBlank, @Email, etc.)
- Use custom corporate validators (e.g., @ValidCorporateEmail)

---

## Banned Libraries

**NEVER** use:

- Apache HttpClient, OkHttp directly → Use `YOUR_ORG-api-client`
- Log4j 1.x, `java.util.logging` → Use SLF4J + Logback
- `System.out.println()` → Use proper logging

**Rationale**: Corporate libraries enforce security, observability, compliance

---

## Architecture

### Project Structure

**MUST** follow: Layered architecture (Controller → Service → Repository)

- **Controller**: REST endpoints, request/response handling
- **Service**: Business logic layer
- **Repository**: Data access layer (Spring Data JPA)
- **Model/Entity**: Domain models and database entities
- **DTO**: Data transfer objects for API contracts

### Separation of Concerns

**MUST**:

- Keep controllers thin (routing, validation, response formatting only)
- Put business logic in service layer
- Use repository interfaces for database access
- Never put business logic in controllers or repositories

### DTOs vs Entities

**MUST**:

- Use separate DTOs for API contracts (never expose entities directly)
- Keep sensitive fields (passwordHash, internalId) in entities only
- Use Java records for immutable DTOs (Java 14+)

### Exception Handling

**MUST**:

- Use `@RestControllerAdvice` for centralized exception handling
- Map domain exceptions to HTTP status codes
- Return generic error messages to clients (no internal details)
- Log full exception details server-side with stack traces

---

## Security

### Input Validation

**MUST**:

- Validate all API inputs using `@Valid` annotation
- Return 400 Bad Request for validation failures
- Reject requests before reaching business logic

### SQL Injection Prevention

**MUST**:

- Use Spring Data JPA (parameterized queries automatic)
- Use `@Query` annotation with named parameters (`:paramName`)
- Never concatenate strings for SQL queries

### Secrets Management

**MUST**:

- Store secrets in corporate secrets manager or environment variables
- Access secrets via Spring's `@Value` annotation or `Environment`
- Use Spring Cloud Config for centralized configuration

**NEVER**:

- Hardcode secrets in code or application.properties
- Commit secrets to source control

### Authentication & Authorization

**MUST**:

- Validate user roles before resource access
- Use `@SecuredEndpoint` annotation on all protected endpoints
- Implement principle of least privilege

---

## Coding Standards

### Java Version

**MUST**:

- Use Java 17+ (prefer latest LTS version)
- Use modern Java features (records, pattern matching, sealed classes)

### Code Style

**SHOULD**:

- Use Lombok to reduce boilerplate (`@Data`, `@RequiredArgsConstructor`, `@Slf4j`)
- Follow Google Java Style Guide or corporate style guide
- Use Checkstyle or SpotBugs for code quality checks

### Naming Conventions

**MUST** follow:

- Classes, Interfaces: `PascalCase`
- Methods, variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Packages: `lowercase` (e.g., `com.yourorg.userservice`)

### Dependency Injection

**MUST**:

- Use constructor injection (recommended over field injection)
- Use `@RequiredArgsConstructor` (Lombok) for automatic constructor generation
- Avoid `@Autowired` on fields (use constructor injection instead)

### Code Quality

**SHOULD**:

- Keep methods under 50 lines
- Limit cyclomatic complexity (< 10 per method)
- Follow SOLID principles
- Write meaningful names (no abbreviations, no single letters except loops)

---

## Testing

**MUST**:

- Write unit tests with JUnit 5
- Write integration tests for API endpoints (@SpringBootTest)
- Aim for 80%+ coverage on critical paths

**SHOULD**:

- Use Mockito for mocking dependencies
- Use TestContainers for integration tests with databases
- Use AssertJ for fluent assertions

---

## Build & Deployment

### Build Process

**MUST**:

- Use Maven (`mvn clean install`) or Gradle (`gradle build`)
- Run tests before deployment
- Use CI/CD pipeline for automated testing and deployment

### Docker

**MUST**:

- Use multi-stage builds (Maven/Gradle build stage + JRE runtime stage)
- Use official Eclipse Temurin base images (e.g., `eclipse-temurin:17-jre-alpine`)
- Run as non-root user in container
- Copy only JAR file to runtime image (use .dockerignore)

**SHOULD**:

- Keep container images small (< 200MB for simple services)
- Use layer caching for faster builds

---

## Observability

**MUST** include:

- Health checks (`/actuator/health`) for readiness/liveness probes
- Metrics (`/actuator/metrics`) for monitoring (Prometheus format)
- Distributed tracing with correlation IDs
- Structured logging with JSON format

**Note**: Corporate Spring Boot starter includes Spring Boot Actuator with all observability features by default

---

## Non-Compliance

If corporate library unavailable or causes blocking issue:

1. Document violation in `.guidelines-todo.md` with justification
2. Create ticket to resolve (target: next sprint)
3. Proceed with alternative, mark with `// TODO: GUIDELINE-VIOLATION` comment for tracking
