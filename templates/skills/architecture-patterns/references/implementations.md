# Architecture Pattern Implementations

> Production-ready code examples for each architecture pattern.

## Clean Architecture Example

### Project Structure

```
src/
├── domain/
│   ├── entities/
│   │   └── user.py           # Core business entity
│   └── repositories/
│       └── user_repository.py # Repository interface
├── application/
│   └── use_cases/
│       └── create_user.py    # Application business rules
├── infrastructure/
│   ├── persistence/
│   │   └── postgres_user_repo.py  # Repository implementation
│   └── web/
│       └── user_controller.py     # HTTP adapter
└── main.py                   # Dependency injection setup
```

### Domain Layer (Entities)

```python
# domain/entities/user.py
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class Email:
    """Value Object with validation"""
    value: str

    def __post_init__(self):
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", self.value):
            raise ValueError(f"Invalid email: {self.value}")

@dataclass
class User:
    """Entity with business rules"""
    id: Optional[str]
    email: Email
    name: str
    is_active: bool = True

    def deactivate(self) -> None:
        if not self.is_active:
            raise ValueError("User is already inactive")
        self.is_active = False

    def can_perform_action(self, action: str) -> bool:
        """Business rule: only active users can perform actions"""
        return self.is_active
```

### Domain Layer (Repository Interface)

```python
# domain/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user import User

class UserRepository(ABC):
    """Port: defines what the domain needs from persistence"""

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass
```

### Application Layer (Use Cases)

```python
# application/use_cases/create_user.py
from dataclasses import dataclass
from domain.entities.user import User, Email
from domain.repositories.user_repository import UserRepository

@dataclass
class CreateUserRequest:
    email: str
    name: str

@dataclass
class CreateUserResponse:
    user_id: str
    email: str
    name: str

class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        # Business rule: email must be unique
        existing = await self.user_repository.find_by_email(request.email)
        if existing:
            raise ValueError(f"Email already registered: {request.email}")

        # Create entity with validation
        user = User(
            id=None,
            email=Email(request.email),
            name=request.name
        )

        # Persist through repository
        saved_user = await self.user_repository.save(user)

        return CreateUserResponse(
            user_id=saved_user.id,
            email=saved_user.email.value,
            name=saved_user.name
        )
```

### Infrastructure Layer (Adapter)

```python
# infrastructure/persistence/postgres_user_repo.py
from typing import Optional
import uuid
from domain.entities.user import User, Email
from domain.repositories.user_repository import UserRepository

class PostgresUserRepository(UserRepository):
    """Adapter: implements repository for PostgreSQL"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def save(self, user: User) -> User:
        user_id = user.id or str(uuid.uuid4())
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (id, email, name, is_active)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE
                SET email = $2, name = $3, is_active = $4
            """, user_id, user.email.value, user.name, user.is_active)

        return User(
            id=user_id,
            email=user.email,
            name=user.name,
            is_active=user.is_active
        )

    async def find_by_id(self, user_id: str) -> Optional[User]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )
            return self._to_entity(row) if row else None

    async def find_by_email(self, email: str) -> Optional[User]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1", email
            )
            return self._to_entity(row) if row else None

    def _to_entity(self, row) -> User:
        return User(
            id=row["id"],
            email=Email(row["email"]),
            name=row["name"],
            is_active=row["is_active"]
        )
```

### Infrastructure Layer (Web Controller)

```python
# infrastructure/web/user_controller.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from application.use_cases.create_user import CreateUserUseCase, CreateUserRequest

router = APIRouter()

class CreateUserDTO(BaseModel):
    email: str
    name: str

@router.post("/users")
async def create_user(
    dto: CreateUserDTO,
    use_case: CreateUserUseCase = Depends()
):
    try:
        result = await use_case.execute(
            CreateUserRequest(email=dto.email, name=dto.name)
        )
        return {"id": result.user_id, "email": result.email, "name": result.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Hexagonal Architecture Example

### Ports (Interfaces)

```python
# ports/inbound/order_service.py
from abc import ABC, abstractmethod
from domain.order import Order

class OrderServicePort(ABC):
    """Inbound port: what the application offers"""

    @abstractmethod
    async def create_order(self, customer_id: str, items: list) -> Order:
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        pass

# ports/outbound/payment_gateway.py
class PaymentGatewayPort(ABC):
    """Outbound port: what the application needs"""

    @abstractmethod
    async def charge(self, amount: float, payment_method: str) -> str:
        pass

# ports/outbound/notification_port.py
class NotificationPort(ABC):
    """Outbound port: notifications"""

    @abstractmethod
    async def send_order_confirmation(self, order: Order) -> None:
        pass
```

### Domain Core

```python
# domain/order_service.py
from ports.inbound.order_service import OrderServicePort
from ports.outbound.payment_gateway import PaymentGatewayPort
from ports.outbound.notification_port import NotificationPort

class OrderService(OrderServicePort):
    """Domain service implementing inbound port, using outbound ports"""

    def __init__(
        self,
        order_repository: OrderRepository,
        payment_gateway: PaymentGatewayPort,
        notification: NotificationPort
    ):
        self.order_repository = order_repository
        self.payment_gateway = payment_gateway
        self.notification = notification

    async def create_order(self, customer_id: str, items: list) -> Order:
        order = Order.create(customer_id, items)

        # Use outbound port for payment
        payment_id = await self.payment_gateway.charge(
            order.total, order.payment_method
        )
        order.mark_paid(payment_id)

        # Persist
        await self.order_repository.save(order)

        # Use outbound port for notification
        await self.notification.send_order_confirmation(order)

        return order
```

### Adapters

```python
# adapters/inbound/rest_adapter.py
from fastapi import APIRouter
from ports.inbound.order_service import OrderServicePort

class RestAdapter:
    """Inbound adapter: REST API"""

    def __init__(self, order_service: OrderServicePort):
        self.order_service = order_service
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/orders")
        async def create_order(request: CreateOrderRequest):
            return await self.order_service.create_order(
                request.customer_id, request.items
            )

# adapters/outbound/stripe_adapter.py
class StripePaymentAdapter(PaymentGatewayPort):
    """Outbound adapter: Stripe implementation"""

    def __init__(self, api_key: str):
        self.client = stripe.Client(api_key)

    async def charge(self, amount: float, payment_method: str) -> str:
        charge = await self.client.charges.create(
            amount=int(amount * 100),
            currency="usd",
            source=payment_method
        )
        return charge.id

# adapters/outbound/sendgrid_adapter.py
class SendGridNotificationAdapter(NotificationPort):
    """Outbound adapter: SendGrid for emails"""

    def __init__(self, api_key: str):
        self.client = SendGridClient(api_key)

    async def send_order_confirmation(self, order: Order) -> None:
        await self.client.send(
            to=order.customer_email,
            template="order_confirmation",
            data={"order_id": order.id, "items": order.items}
        )
```

## Testing Benefits

```python
# tests/test_create_user.py
import pytest
from application.use_cases.create_user import CreateUserUseCase, CreateUserRequest

class InMemoryUserRepository(UserRepository):
    """Test double for repository"""
    def __init__(self):
        self.users = {}

    async def save(self, user: User) -> User:
        user.id = user.id or str(uuid.uuid4())
        self.users[user.id] = user
        return user

    async def find_by_email(self, email: str):
        for user in self.users.values():
            if user.email.value == email:
                return user
        return None

@pytest.mark.asyncio
async def test_create_user_success():
    # No real database needed!
    repo = InMemoryUserRepository()
    use_case = CreateUserUseCase(repo)

    result = await use_case.execute(
        CreateUserRequest(email="test@example.com", name="Test User")
    )

    assert result.email == "test@example.com"
    assert result.user_id is not None
```
