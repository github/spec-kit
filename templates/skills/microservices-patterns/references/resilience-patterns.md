# Microservices Resilience Patterns

> Patterns for building fault-tolerant distributed systems.

## Circuit Breaker

Prevents cascade failures by failing fast when a service is unhealthy.

**States:**
- **Closed**: Normal operation, requests pass through
- **Open**: Service unhealthy, requests fail immediately
- **Half-Open**: Testing recovery, limited requests allowed

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def _should_attempt_reset(self):
        return time.time() - self.last_failure_time >= self.recovery_timeout
```

## Retry with Exponential Backoff

```python
async def retry_with_backoff(
    func,
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2
):
    for attempt in range(max_retries):
        try:
            return await func()
        except RetryableError as e:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            delay *= (0.5 + random.random())  # Jitter
            await asyncio.sleep(delay)
```

## Bulkhead Pattern

Isolate failures to prevent resource exhaustion.

```python
class Bulkhead:
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(self, func, *args, **kwargs):
        async with self.semaphore:
            return await func(*args, **kwargs)

# Usage: Separate bulkheads for different services
payment_bulkhead = Bulkhead(max_concurrent=10)
inventory_bulkhead = Bulkhead(max_concurrent=20)
```

## Timeout Pattern

```python
async def with_timeout(func, timeout_seconds: float):
    try:
        return await asyncio.wait_for(func(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise ServiceTimeoutError(f"Operation timed out after {timeout_seconds}s")
```

## Health Checks

```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "downstream_service": await check_downstream(),
    }

    healthy = all(checks.values())
    return {
        "status": "healthy" if healthy else "unhealthy",
        "checks": checks
    }

@app.get("/ready")
async def readiness_check():
    """Can this instance handle traffic?"""
    return {"ready": True}

@app.get("/live")
async def liveness_check():
    """Is this instance alive?"""
    return {"alive": True}
```

## Fallback Strategies

```python
class ServiceWithFallback:
    async def get_recommendations(self, user_id: str):
        try:
            return await self.recommendation_service.get(user_id)
        except ServiceUnavailableError:
            # Fallback: Return cached or default recommendations
            cached = await self.cache.get(f"recommendations:{user_id}")
            if cached:
                return cached
            return self.get_default_recommendations()
```

## Best Practices

1. **Timeouts everywhere**: Never make a call without a timeout
2. **Circuit breakers on external calls**: Protect against slow dependencies
3. **Bulkheads for isolation**: Separate thread pools per dependency
4. **Health checks**: Implement liveness and readiness probes
5. **Graceful degradation**: Always have a fallback strategy
6. **Observability**: Log circuit state changes, track failure rates
