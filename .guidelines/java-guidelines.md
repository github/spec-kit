# Java Corporate Guidelines

**Tech Stack**: Java, Spring Boot, Backend Services, Microservices

**Auto-detected from**: `pom.xml`, `build.gradle`, or `*.java` files

## Scaffolding

**MUST** use corporate command:

```bash
npx @YOUR_ORG/create-spring-app <app-name> --template microservice
```

Templates: `microservice`, `monolith`, `batch`

**DO NOT** use public Spring Initializr: `https://start.spring.io`

Alternative: Internal Spring Initializr at `https://spring-init.YOUR_DOMAIN.com`

## Package Registry

**Maven** - configure `pom.xml`:

```xml
<repositories>
    <repository>
        <id>YOUR_ORG-releases</id>
        <url>https://artifactory.YOUR_DOMAIN.com/artifactory/libs-release</url>
    </repository>
</repositories>
```

**Authentication** - `~/.m2/settings.xml`:

```xml
<servers>
    <server>
        <id>YOUR_ORG-releases</id>
        <username>${env.ARTIFACTORY_USER}</username>
        <password>${env.ARTIFACTORY_PASSWORD}</password>
    </server>
</servers>
```

## Mandatory Libraries

### Spring Boot Starter

**MUST** use corporate Spring Boot parent:

```xml
<parent>
    <groupId>com.YOUR_ORG</groupId>
    <artifactId>YOUR_ORG-spring-boot-starter-parent</artifactId>
    <version>2.1.0</version>
</parent>

<dependencies>
    <dependency>
        <groupId>com.YOUR_ORG</groupId>
        <artifactId>YOUR_ORG-spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

Includes: Security, logging, monitoring, health checks, exception handling, CORS

### Security & Authentication

**MUST** use corporate security library:

```xml
<dependency>
    <groupId>com.YOUR_ORG</groupId>
    <artifactId>YOUR_ORG-security-spring-boot-starter</artifactId>
</dependency>
```

```java
import com.YOUR_ORG.security.annotation.SecuredEndpoint;
import com.YOUR_ORG.security.context.SecurityContextHolder;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping
    @SecuredEndpoint(roles = {"USER", "ADMIN"})
    public List<UserDTO> getAllUsers() {
        User currentUser = SecurityContextHolder.getCurrentUser();
        return userService.getAllUsers(currentUser);
    }
}
```

### API Client

**MUST** use corporate API client:

```xml
<dependency>
    <groupId>com.YOUR_ORG</groupId>
    <artifactId>YOUR_ORG-api-client</artifactId>
</dependency>
```

```java
import com.YOUR_ORG.client.ApiClient;
import com.YOUR_ORG.client.annotation.CircuitBreaker;

@Service
public class UserService {
    private final ApiClient<OrderServiceClient> orderClient;

    @CircuitBreaker(fallbackMethod = "getOrdersFallback")
    public List<Order> getUserOrders(String userId) {
        return orderClient.get().getOrdersByUserId(userId);
    }
}
```

Features: Service discovery, load balancing, circuit breaker, retry

### Database

**MUST** use Spring Data JPA with corporate extensions:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>com.YOUR_ORG</groupId>
    <artifactId>YOUR_ORG-jpa-extensions</artifactId>
</dependency>
```

```java
import com.YOUR_ORG.jpa.audit.AuditedEntity;

@Entity
@Table(name = "users")
public class User extends AuditedEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;
}
```

### Database Migration

**MUST** use Flyway:

```xml
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
</dependency>
```

Migrations: `src/main/resources/db/migration/V1__create_users_table.sql`

### Logging

**MUST** use SLF4J + Logback (included in corporate starter):

```java
import lombok.extern.slf4j.Slf4j;
import com.YOUR_ORG.logging.annotation.LogExecution;

@Service
@Slf4j
public class UserService {
    @LogExecution
    public UserDTO createUser(CreateUserRequest request) {
        log.info("Creating user with email: {}", request.getEmail());
        // ...
    }
}
```

### Validation

**MUST** use Jakarta Bean Validation with corporate validators:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
<dependency>
    <groupId>com.YOUR_ORG</groupId>
    <artifactId>YOUR_ORG-validators</artifactId>
</dependency>
```

```java
import javax.validation.constraints.*;
import com.YOUR_ORG.validation.annotation.ValidCorporateEmail;

public class CreateUserRequest {
    @NotBlank
    @Email
    @ValidCorporateEmail
    private String email;

    @NotBlank
    @Size(min = 12)
    private String password;
}
```

## Banned Libraries

**DO NOT USE**:

- Apache HttpClient, OkHttp directly → use `YOUR_ORG-api-client`
- Log4j 1.x, java.util.logging → use SLF4J + Logback
- System.out.println for logging

## Architecture

**Structure**:

```text
src/main/java/com/YOUR_ORG/userservice/
├── UserServiceApplication.java
├── controller/
├── service/
├── repository/
├── model/
├── dto/
└── config/
```

**Layers**: Controller → Service → Repository → Database

**MUST** separate DTOs from entities:

```java
// Entity (internal)
@Entity
public class User {
    private String passwordHash;  // Never expose
}

// DTO (API)
public record UserDTO(Long id, String email, String firstName) {}
```

**MUST** use centralized exception handling:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handle(ResourceNotFoundException ex) {
        return ResponseEntity.status(NOT_FOUND).body(...);
    }
}
```

## Security

**Input validation** - ALWAYS validate:

```java
@PostMapping("/api/users")
public ResponseEntity<UserDTO> createUser(@Valid @RequestBody CreateUserRequest request) {
    return ResponseEntity.ok(userService.createUser(request));
}
```

**SQL injection** - use parameterized queries:

```java
@Query("SELECT u FROM User u WHERE u.email = :email")
Optional<User> findByEmail(@Param("email") String email);
```

**Secrets** - NEVER hardcode:

```java
@Value("${YOUR_ORG.api.key}")
private String apiKey;
```

## Coding Standards

**MUST** use Java 17+:

```xml
<properties>
    <java.version>17</java.version>
</properties>
```

**RECOMMENDED** - use Lombok:

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {
    private final UserRepository userRepository;
}
```

**Naming**:

- Classes: PascalCase (`UserService`)
- Methods: camelCase (`createUser`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- Packages: lowercase (`com.YOUR_ORG.userservice`)

## Build & Deployment

**Build**:

```bash
mvn clean install
```

**Docker**:

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Observability

**MUST** include:

- Health checks (`/actuator/health`)
- Metrics (`/actuator/metrics`)
- Distributed tracing
- Structured logging

Included in corporate Spring Boot starter.
