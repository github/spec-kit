# Python Corporate Guidelines

**Tech Stack**: Python, Django, Flask, FastAPI, Backend Services, APIs, Data Processing

**Auto-detected from**: `requirements.txt`, `pyproject.toml`, `setup.py`, or `*.py` files

## Scaffolding

**MUST** use corporate command:

```bash
python -m YOUR_ORG.cli create-service <service-name> --framework fastapi
```

Frameworks: `fastapi`, `django`, `flask`

**DO NOT** use: `django-admin startproject`, `flask init`

## Package Registry

Configure `pip.conf`:

```ini
[global]
index-url = https://artifactory.YOUR_DOMAIN.com/artifactory/api/pypi/pypi-virtual/simple
```

## Mandatory Libraries

### FastAPI Starter

**MUST** use corporate FastAPI starter:

```bash
pip install YOUR_ORG-fastapi-starter
```

```python
from YOUR_ORG.fastapi import create_app, AcmecorpConfig

config = AcmecorpConfig(
    service_name="user-service",
    jwt_issuer="https://auth.example.com"
)

app = create_app(config)
app.include_router(users.router, prefix="/api/users")
```

Includes: Security, logging, metrics, error handling, CORS

### Authentication

**MUST** use corporate auth:

```bash
pip install YOUR_ORG-auth
```

```python
from YOUR_ORG.auth import require_auth, require_roles

@router.get("/users")
@require_auth
@require_roles(["user", "admin"])
async def get_users(current_user = Depends(get_current_user)):
    return await user_service.get_users(current_user)
```

### API Client

**MUST** use corporate HTTP client:

```bash
pip install YOUR_ORG-http-client
```

```python
from YOUR_ORG.http import AcmecorpHttpClient

order_client = AcmecorpHttpClient(
    base_url="https://order-service.example.com",
    timeout=5.0,
    retry_attempts=3
)
```

### Database (PostgreSQL/MySQL)

**MUST** use SQLAlchemy with Alembic:

```bash
pip install sqlalchemy alembic psycopg2-binary YOUR_ORG-sqlalchemy-utils
```

```python
from sqlalchemy import Column, Integer, String
from YOUR_ORG.sqlalchemy import AuditMixin

class User(Base, AuditMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
```

### Database (MongoDB)

**MUST** use Motor + Beanie:

```bash
pip install motor beanie
```

### Logging

**MUST** use corporate logger:

```bash
pip install YOUR_ORG-logger
```

```python
from YOUR_ORG.logger import get_logger

logger = get_logger(__name__)
logger.info("User created", extra={"user_id": user.id})
```

### Validation

**MUST** use Pydantic (built into FastAPI):

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    first_name: str = Field(..., max_length=100)
```

## Banned Libraries

**DO NOT USE**:

- `flask-jwt` → use `YOUR_ORG-auth`
- `requests` without wrapper → use `YOUR_ORG-http-client`
- `logging` directly → use `YOUR_ORG-logger`

## Architecture

**Structure** (FastAPI):

```text
app/
├── main.py
├── routers/
├── services/
├── models/
├── schemas/        # Pydantic models
└── config.py
```

Layers: Routers → Services → Models

## Security

- **Secrets**: Environment variables or secrets manager
- **Validation**: Use Pydantic for all inputs
- **SQL Injection**: Use parameterized queries (SQLAlchemy handles)
- **Rate Limiting**: Use `YOUR_ORG-rate-limiter`
- **HTTPS**: Always in production

## Coding Standards

**MUST** use Python 3.10+:

```toml
[tool.poetry]
python = "^3.10"
```

**MUST** use type hints:

```python
async def get_user_by_id(user_id: int) -> Optional[User]:
    return await db.query(User).filter(User.id == user_id).first()
```

**PREFER** async/await for I/O:

```python
async def create_user(request: CreateUserRequest) -> User:
    user = User(**request.dict())
    await db.add(user)
    return user
```

**Naming**:

- Functions/variables: snake_case (`get_user`, `user_id`)
- Classes: PascalCase (`UserService`, `User`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`)

**Code style** - MUST follow PEP 8, use `black`:

```bash
pip install black
black .
```

## Build & Deployment

**Dependencies**:

```toml
[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.100.0"
uvicorn = "^0.23.0"
```

**Docker**:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Observability

**MUST** include:

- Health endpoint (`/health`)
- Metrics (`/metrics` - Prometheus)
- Distributed tracing
- Structured logging (JSON)

Included in corporate FastAPI starter.

**Testing** - minimum 80% coverage:

```bash
pytest --cov=app --cov-report=html
```
