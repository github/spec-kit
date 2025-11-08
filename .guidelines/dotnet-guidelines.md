# .NET Corporate Guidelines

**Tech Stack**: .NET 6+, C#, ASP.NET Core, Backend Services, Microservices

**Auto-detected from**: `*.csproj`, `*.sln`, or `*.cs` files

## Scaffolding

**MUST** use corporate templates:

```bash
dotnet new YOUR_ORG_template -n MyService
```

Templates: `YOUR_ORG-webapi`, `YOUR_ORG-minimal-api`, `YOUR_ORG-worker`, `YOUR_ORG-blazor`

**Installation**:

```bash
dotnet new --install YOUR_ORG.Templates::1.0.0 --nuget-source https://nuget.YOUR_DOMAIN.com/v3/index.json
```

**DO NOT** use default templates: `dotnet new webapi`

## Package Registry

**Configure** `nuget.config`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <add key="YOUR_ORG" value="https://nuget.YOUR_DOMAIN.com/v3/index.json" />
  </packageSources>
</configuration>
```

## Mandatory Libraries

### ASP.NET Core Starter

**MUST** use corporate starter package:

```xml
<PackageReference Include="YOUR_ORG.AspNetCore.Starter" Version="2.1.0" />
```

```csharp
using YOUR_ORG.AspNetCore;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddYourOrgServices(builder.Configuration);

var app = builder.Build();
app.UseYourOrgMiddleware();
```

Includes: Security, logging, monitoring, health checks, exception handling, CORS

### Security & Authentication

**MUST** use corporate security library:

```xml
<PackageReference Include="YOUR_ORG.Security" Version="3.0.0" />
```

```csharp
using YOUR_ORG.Security;

[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpGet]
    [SecuredEndpoint(Roles = "User,Admin")]
    public async Task<IActionResult> GetUsers()
    {
        var currentUser = User.GetCurrentUser();
        return Ok(await _userService.GetUsers(currentUser));
    }
}
```

### API Client

**MUST** use corporate HTTP client:

```xml
<PackageReference Include="YOUR_ORG.HttpClient" Version="1.5.0" />
```

```csharp
using YOUR_ORG.HttpClient;

public class UserService
{
    private readonly IYourOrgHttpClient _orderClient;

    public UserService(IYourOrgHttpClientFactory clientFactory)
    {
        _orderClient = clientFactory.CreateClient("OrderService");
    }

    [CircuitBreaker(FallbackMethod = nameof(GetOrdersFallback))]
    public async Task<List<Order>> GetUserOrders(string userId)
    {
        return await _orderClient.GetAsync<List<Order>>($"/api/orders?userId={userId}");
    }
}
```

Features: Service discovery, circuit breaker, retry, distributed tracing

### Database

**MUST** use Entity Framework Core with corporate extensions:

```xml
<PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />
<PackageReference Include="YOUR_ORG.EntityFrameworkCore.Extensions" Version="1.2.0" />
```

```csharp
using YOUR_ORG.EntityFrameworkCore;

public class User : AuditedEntity
{
    public long Id { get; set; }
    public string Email { get; set; }
    public string PasswordHash { get; set; }
}

public class AppDbContext : DbContext
{
    public DbSet<User> Users { get; set; }
}
```

### Database Migration

**MUST** use EF Core migrations:

```bash
dotnet ef migrations add CreateUsersTable
dotnet ef database update
```

### Logging

**MUST** use corporate logger (built on Microsoft.Extensions.Logging):

```xml
<PackageReference Include="YOUR_ORG.Logging" Version="2.0.0" />
```

```csharp
using Microsoft.Extensions.Logging;

public class UserService
{
    private readonly ILogger<UserService> _logger;

    public async Task<User> CreateUser(CreateUserRequest request)
    {
        _logger.LogInformation("Creating user {Email}", request.Email);
        // ...
    }
}
```

### Validation

**MUST** use FluentValidation with corporate validators:

```xml
<PackageReference Include="FluentValidation.AspNetCore" Version="11.3.0" />
<PackageReference Include="YOUR_ORG.Validators" Version="1.1.0" />
```

```csharp
using FluentValidation;
using YOUR_ORG.Validators;

public class CreateUserRequestValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress().CorporateEmail();
        RuleFor(x => x.Password).NotEmpty().MinimumLength(12);
    }
}
```

## Banned Libraries

**DO NOT USE**:

- `HttpClient` directly → use `YOUR_ORG.HttpClient`
- Serilog without corporate wrapper → use `YOUR_ORG.Logging`
- Console.WriteLine for logging

## Architecture

**Structure**:

```text
src/
├── UserService.Api/
│   ├── Controllers/
│   ├── Program.cs
│   └── appsettings.json
├── UserService.Core/
│   ├── Services/
│   └── Models/
└── UserService.Infrastructure/
    ├── Data/
    └── Repositories/
```

**Layers**: Controllers → Services → Repositories → Database

**MUST** use DTOs:

```csharp
// Entity (internal)
public class User
{
    public string PasswordHash { get; set; }  // Never expose
}

// DTO (API)
public record UserDto(long Id, string Email, string FirstName);
```

**MUST** use centralized exception handling:

```csharp
app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        context.Response.StatusCode = 500;
        await context.Response.WriteAsJsonAsync(new { error = "Internal server error" });
    });
});
```

## Security

**Input validation** - ALWAYS validate:

```csharp
[HttpPost]
public async Task<IActionResult> CreateUser([FromBody] CreateUserRequest request)
{
    if (!ModelState.IsValid)
        return BadRequest(ModelState);

    return Ok(await _userService.CreateUser(request));
}
```

**SQL injection** - use parameterized queries (EF Core handles):

```csharp
var user = await _context.Users
    .Where(u => u.Email == email)
    .FirstOrDefaultAsync();
```

**Secrets** - NEVER hardcode:

```csharp
var apiKey = builder.Configuration["YourOrg:ApiKey"];
```

Use Azure Key Vault or corporate secrets manager.

## Coding Standards

**MUST** use .NET 6+ with nullable reference types:

```xml
<PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
</PropertyGroup>
```

**Use**:

- Async/await for I/O operations
- Dependency injection
- Record types for DTOs
- Pattern matching

**Naming**:

- Classes: PascalCase (`UserService`)
- Methods: PascalCase (`CreateUser`)
- Properties: PascalCase (`FirstName`)
- Local variables: camelCase (`userId`)
- Constants: PascalCase (`MaxRetries`)

## Build & Deployment

**Build**:

```bash
dotnet build
dotnet publish -c Release
```

**Docker**:

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY *.csproj ./
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 80
ENTRYPOINT ["dotnet", "UserService.Api.dll"]
```

## Observability

**MUST** include:

- Health checks (`/health`)
- Metrics (`/metrics`)
- Distributed tracing
- Structured logging

Included in corporate ASP.NET Core starter.
