# Python Corporate Guidelines

**Tech Stack**: Python, Django, Flask, FastAPI, Backend Services, APIs, Data Processing

**Auto-detected from**: `requirements.txt`, `pyproject.toml`, `setup.py`, or `*.py` files

## 1. Scaffolding

**Corporate Command**:

```bash
python -m YOUR_ORG.cli create-service <service-name> --framework fastapi
```

**Example**:

```bash
python -m acmecorp.cli create-service user-service --framework fastapi
```

**Frameworks**:

- `fastapi` - FastAPI (modern, async, type-hints)
- `django` - Django (full-featured)
- `flask` - Flask (lightweight)

**DO NOT USE**: `django-admin startproject`, `flask init` (bypass corporate config)

## 2. Package Registry

**Configuration** (`pip.conf` or `~/.config/pip/pip.conf`):

```ini
[global]
index-url = https://artifactory.acmecorp.com/artifactory/api/pypi/pypi-virtual/simple
trusted-host = artifactory.acmecorp.com

[install]
extra-index-url = https://pypi.org/simple
```

**Authentication** (`.netrc`):

```text
machine artifactory.acmecorp.com
login your-username
password your-api-key
```

## 3. Mandatory Libraries

### Corporate FastAPI Starter

**MUST USE**:

```bash
pip install acmecorp-fastapi-starter
```

**Includes**: Security, logging, metrics, error handling, CORS, OpenAPI

**Usage** (`main.py`):

```python
from acmecorp.fastapi import create_app, AcmecorpConfig
from app.routers import users

config = AcmecorpConfig(
    service_name="user-service",
    jwt_issuer="https://auth.acmecorp.com",
    jwt_audience="acmecorp-services",
)

app = create_app(config)

# Your routes
app.include_router(users.router, prefix="/api/users", tags=["users"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Security & Authentication

**MUST USE**:

```bash
pip install acmecorp-auth
```

**Usage**:

```python
from acmecorp.auth import require_auth, require_roles
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/users")
@require_auth
@require_roles(["user", "admin"])
async def get_users(current_user = Depends(get_current_user)):
    # current_user populated by acmecorp.auth
    users = await user_service.get_users(current_user)
    return users
```

### API Client

**MUST USE**:

```bash
pip install acmecorp-http-client
```

**Usage**:

```python
from acmecorp.http import AcmecorpHttpClient

order_client = AcmecorpHttpClient(
    base_url="https://order-service.acmecorp.com",
    timeout=5.0,
    retry_attempts=3,
    circuit_breaker=True,
)

orders = await order_client.get("/api/orders", params={"user_id": user_id})
```

### Database (PostgreSQL/MySQL)

**MUST USE**: SQLAlchemy with Alembic migrations

```bash
pip install sqlalchemy alembic psycopg2-binary
pip install acmecorp-sqlalchemy-utils
```

**Model**:

```python
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from acmecorp.sqlalchemy import AuditMixin
from datetime import datetime
import enum

Base = declarative_base()

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class User(Base, AuditMixin):  # AuditMixin adds created_at, updated_at, etc.
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)

    # Audit fields from AuditMixin:
    # created_at, created_by, updated_at, updated_by
```

**Migration** (Alembic):

```bash
alembic init migrations
alembic revision --autogenerate -m "Create users table"
alembic upgrade head
```

### Database (MongoDB)

**MUST USE**: Motor (async MongoDB driver) + Beanie ODM

```bash
pip install motor beanie
```

**Model**:

```python
from beanie import Document
from pydantic import EmailStr
from datetime import datetime

class User(Document):
    email: EmailStr
    password_hash: str
    status: str = "active"
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"
        indexes = [
            "email",
            "status",
        ]
```

### Logging

**MUST USE**:

```bash
pip install acmecorp-logger
```

**Usage**:

```python
from acmecorp.logger import get_logger

logger = get_logger(__name__)

logger.info("User created", extra={"user_id": user.id, "email": user.email})
logger.error("Failed to create user", extra={"error": str(e), "email": email})
```

**Structured JSON output** - automatic context injection (service, trace ID, user ID).

### Validation

**MUST USE**: Pydantic (built into FastAPI)

```python
from pydantic import BaseModel, EmailStr, Field, validator
import re

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)

    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('Password must contain special character')
        return v

    @validator('email')
    def validate_corporate_email(cls, v):
        if not v.endswith('@acmecorp.com'):
            raise ValueError('Must use corporate email')
        return v

@router.post("/users")
async def create_user(request: CreateUserRequest):
    # Pydantic automatically validates
    user = await user_service.create_user(request)
    return user
```

### Testing

**MUST USE**: pytest + httpx (async HTTP client)

```bash
pip install pytest pytest-asyncio httpx
```

**Test example**:

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/users", json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
        })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
```

## 4. Banned Libraries

❌ **BANNED**:

- `flask-jwt` (use `acmecorp-auth`)
- `requests` without corporate wrapper (use `acmecorp-http-client`)
- `logging` directly (use `acmecorp-logger`)

## 5. Architecture

**Structure** (FastAPI):

```text
app/
├── main.py
├── routers/
│   ├── __init__.py
│   ├── users.py
│   └── orders.py
├── services/
│   ├── __init__.py
│   └── user_service.py
├── models/
│   ├── __init__.py
│   └── user.py
├── schemas/
│   ├── __init__.py
│   └── user.py        # Pydantic models
├── dependencies.py     # FastAPI dependencies
└── config.py
```

**Layers**: Routers → Services → Models/Repositories

## 6. Security

- **Secrets**: Use environment variables or corporate secrets manager
- **Validation**: Use Pydantic for input validation
- **SQL Injection**: Use parameterized queries (SQLAlchemy handles this)
- **Rate Limiting**: Use `acmecorp-rate-limiter`
- **HTTPS**: Always use HTTPS in production

**Example**:

```python
# ❌ NEVER
API_KEY = "sk-12345-abcdef"

# ✅ DO THIS
import os
API_KEY = os.getenv("ACMECORP_API_KEY")
```

## 7. Coding Standards

### Python Version

**MUST** use Python 3.10+ (preferably 3.11+):

```toml
# pyproject.toml
[tool.poetry]
python = "^3.10"
```

### Type Hints

**MUST** use type hints:

```python
from typing import List, Optional

async def get_user_by_id(user_id: int) -> Optional[User]:
    return await db.query(User).filter(User.id == user_id).first()

async def get_all_users() -> List[User]:
    return await db.query(User).all()
```

### Async/Await

**PREFER** async/await for I/O operations:

```python
# ✅ Good
async def create_user(request: CreateUserRequest) -> User:
    user = User(**request.dict())
    await db.add(user)
    await db.commit()
    return user

# ❌ Avoid blocking operations in async code
def create_user_blocking(request: CreateUserRequest) -> User:
    # Don't mix sync and async
    pass
```

### Naming Conventions

- **Functions/Variables**: snake_case (`get_user`, `user_id`)
- **Classes**: PascalCase (`UserService`, `UserModel`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `API_VERSION`)
- **Private**: Leading underscore (`_internal_function`)

### Code Style

**MUST** follow PEP 8. Use `black` for formatting:

```bash
pip install black
black .
```

## 8. Build & Deployment

### Dependencies

**Use** `requirements.txt` or `pyproject.toml`:

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.100.0"
uvicorn = "^0.23.0"
sqlalchemy = "^2.0.0"
acmecorp-fastapi-starter = "^1.0.0"
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 9. Performance

- Use async/await for I/O operations
- Implement caching (Redis via `acmecorp-cache`)
- Use database connection pooling
- Optimize queries (indexes, select specific fields)
- Use pagination for large result sets

## 10. Observability

**MUST** include:

- Health endpoint (`/health`)
- Metrics (`/metrics` - Prometheus)
- Distributed tracing (OpenTelemetry)
- Structured logging (JSON)

**Included** in corporate FastAPI starter.

## 11. Testing

**Coverage requirement**: Minimum 80% code coverage

```bash
pytest --cov=app --cov-report=html
```

## See Also

- `README.md` - Guidelines overview
- Internal Python best practices guide
- Internal developer portal
