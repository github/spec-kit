# API Requests Guard Type

## Overview

The `api-requests` guard type validates API endpoints using the httpx library. It tests HTTP endpoints for availability, correct status codes, and response times.

## What This Guard Type Validates

- **API Availability**: Endpoints are accessible and responding
- **Status Codes**: HTTP responses match expected codes
- **Response Times**: API performance monitoring
- **HTTP Methods**: Support for GET, POST, PUT, PATCH, DELETE, etc.
- **Headers**: Custom headers and authentication
- **SSL/TLS**: Certificate validation
- **Redirects**: Follow redirect behavior

## When to Use It

### ✅ Use This Guard Type When:

- Validating API health and availability
- Testing API contracts and status codes
- Monitoring API performance
- Checking authentication endpoints
- Verifying external API integrations
- Smoke testing API deployments

### ❌ Don't Use This Guard Type When:

- Testing complex business logic (use `unit-pytest` instead)
- Testing UI functionality (use `ui-playwright` instead)
- Checking code quality (use `static-analysis-python` instead)
- Need detailed response schema validation (consider extending this guard type)

## Installation

Ensure httpx is installed:

```bash
uv pip install httpx
```

## Example Configurations

### PyPI API Health Check

```yaml
id: G004
guard_type: api-requests
name: pypi-health
params:
  base_url: https://pypi.org/pypi
  timeout: 10
  verify_ssl: true
  follow_redirects: true
  endpoints:
    - path: /specify-cli/json
      method: GET
      expected_status: 200
```

### Internal API Smoke Test

```yaml
id: G005
guard_type: api-requests
name: api-smoke
params:
  base_url: https://api.example.com
  timeout: 5
  verify_ssl: true
  endpoints:
    - path: /health
      method: GET
      expected_status: 200
    - path: /api/v1/status
      method: GET
      expected_status: 200
    - path: /api/v1/users
      method: GET
      expected_status: 401  # Expect auth required
```

### Authenticated API Test

```yaml
id: G006
guard_type: api-requests
name: authenticated-api
params:
  base_url: https://api.example.com
  timeout: 10
  verify_ssl: true
  endpoints:
    - path: /api/v1/profile
      method: GET
      expected_status: 200
      headers:
        Authorization: Bearer ${API_TOKEN}
    - path: /api/v1/settings
      method: GET
      expected_status: 200
      headers:
        Authorization: Bearer ${API_TOKEN}
```

### POST Request with Body

```yaml
id: G007
guard_type: api-requests
name: api-create-test
params:
  base_url: https://api.example.com
  timeout: 15
  verify_ssl: true
  endpoints:
    - path: /api/v1/users
      method: POST
      expected_status: 201
      headers:
        Content-Type: application/json
        Authorization: Bearer ${API_TOKEN}
      body:
        name: Test User
        email: test@example.com
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | string | `""` | Base URL for API endpoints |
| `endpoints` | array | `[]` | List of endpoint configurations |
| `timeout` | integer | `10` | Request timeout in seconds |
| `verify_ssl` | boolean | `true` | Verify SSL certificates |
| `follow_redirects` | boolean | `true` | Follow HTTP redirects |

### Endpoint Configuration

Each endpoint in the `endpoints` array supports:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Endpoint path (relative to base_url) |
| `method` | string | Yes | HTTP method (GET, POST, PUT, DELETE, etc.) |
| `expected_status` | integer | Yes | Expected HTTP status code |
| `headers` | object | No | Custom headers to include |
| `body` | object | No | Request body (for POST/PUT/PATCH) |

## Creating a Guard Instance

```bash
# Create a guard for API health checks
specify guard create --type api-requests --name api-health

# Edit the generated guard.yaml to configure endpoints
# Then run the guard
specify guard run G00X
```

## Common Failure Patterns

### 1. Unexpected Status Code

**Symptom**: "Expected 200, got 404"
**Cause**: Endpoint path incorrect, resource doesn't exist, or API changed
**Fix**:
- Verify endpoint path in guard.yaml
- Check API documentation for correct paths
- Update expected_status if API behavior changed
- Ensure base_url is correct

### 2. Timeout

**Symptom**: "Request timed out after Xs"
**Cause**: API slow to respond, network issues, server down
**Fix**:
- Increase timeout parameter
- Check API server status
- Verify network connectivity
- Check for API rate limiting

### 3. SSL Certificate Error

**Symptom**: "SSL verification failed"
**Cause**: Invalid or expired SSL certificate
**Fix**:
- For development: Set `verify_ssl: false` (not recommended for production)
- Update certificates
- Check certificate expiration
- Verify SSL configuration

### 4. Connection Refused

**Symptom**: "Connection refused" or "Cannot connect"
**Cause**: Server not running, wrong URL, firewall blocking
**Fix**:
- Verify base_url is correct
- Check server is running
- Test URL manually: `curl https://api.example.com/health`
- Check firewall/network rules

## Debugging Failures

### View Guard History

```bash
# List recent runs
specify guard history G00X

# View detailed output for specific run
specify guard history G00X --run-id <run-id>
```

### Test Endpoints Manually

```bash
# Test with curl
curl -v https://api.example.com/health

# Test with httpx Python
uv run python3 -c "
import httpx
r = httpx.get('https://api.example.com/health')
print(f'Status: {r.status_code}')
print(r.text)
"
```

### Enable Detailed Output

Review the guard history details JSON for:
- Exact URLs being tested
- Response status codes
- Response times
- Error messages

## Integration with Workflow

### In Plan Phase

Identify API validation checkpoints:

```markdown
## Guard Validation Strategy

| Checkpoint | Guard Type | Command |
|------------|------------|---------|
| API endpoints | api-requests | `specify guard create --type api-requests --name user-api` |
```

### In Tasks Phase

Tag API implementation tasks with guard validation:

```markdown
- [ ] T030 Implement user API endpoint [Guard: G004]
- [ ] T031 Add authentication middleware [Guard: G004]
```

### In Implementation Phase

Run guards after implementing API endpoints:

```bash
# After implementing API endpoints
specify guard run G004

# If failures occur
specify guard history G004  # Review failures
curl -v https://api.example.com/endpoint  # Debug manually
```

## Best Practices

1. **Organize Endpoints**: Group related endpoints in separate guards
2. **Expected Statuses**: Test both success and expected error codes
3. **Timeouts**: Set appropriate timeouts for different endpoint types
4. **Authentication**: Use environment variables for tokens/secrets
5. **Health Checks**: Include basic health/status endpoints
6. **Response Times**: Monitor performance with response time data
7. **Error Scenarios**: Test 401, 403, 404 responses explicitly
8. **Idempotency**: Ensure POST/PUT tests are idempotent or use test data

## Environment Variables

Use environment variables for sensitive data:

```yaml
endpoints:
  - path: /api/v1/profile
    headers:
      Authorization: Bearer ${API_TOKEN}
```

Set before running:

```bash
export API_TOKEN=your-token-here
specify guard run G00X
```

## Response Time Monitoring

The guard tracks response times:

```json
{
  "details": {
    "results": [
      {
        "endpoint": "/health",
        "response_time_ms": 150
      }
    ]
  }
}
```

Use this to:
- Monitor API performance over time
- Identify slow endpoints
- Set SLA thresholds

## Related Guard Types

- **unit-pytest**: For testing API business logic
- **ui-playwright**: For testing UI interactions with APIs
- **static-analysis-python**: For code quality checks

## Troubleshooting

### httpx not found

```bash
# Install httpx
uv pip install httpx
```

### Base URL not configured

Edit guard.yaml and set:

```yaml
params:
  base_url: https://api.example.com
```

### No endpoints configured

Edit guard.yaml and add endpoints:

```yaml
params:
  endpoints:
    - path: /health
      method: GET
      expected_status: 200
```

### Rate limiting

If hitting rate limits:
- Reduce number of endpoints tested
- Increase delays between requests (extend guard template)
- Use dedicated test environment

---

**Guard Type**: api-requests  
**Category**: api  
**Library**: httpx  
**Language**: Python
