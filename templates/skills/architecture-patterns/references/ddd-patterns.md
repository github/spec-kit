# Domain-Driven Design Patterns

> Strategic and tactical patterns for complex domains.

## Strategic Patterns

### Bounded Context

A bounded context defines the boundary within which a particular domain model applies.

```
┌─────────────────────────────────────────────────────────────────┐
│                        E-Commerce System                         │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Sales Context │  │ Shipping Context│  │ Billing Context │  │
│  │                 │  │                 │  │                 │  │
│  │  • Order        │  │  • Shipment     │  │  • Invoice      │  │
│  │  • Customer     │  │  • Address      │  │  • Payment      │  │
│  │  • Product      │  │  • Carrier      │  │  • Customer     │  │
│  │                 │  │                 │  │                 │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │            │
│           └──────────┬─────────┴────────────────────┘            │
│                      │                                           │
│              Context Mapping (Events, APIs)                      │
└─────────────────────────────────────────────────────────────────┘
```

**Note:** "Customer" means different things in each context:
- Sales: Name, contact, preferences
- Shipping: Delivery address
- Billing: Payment methods, billing address

### Context Mapping Patterns

| Pattern | When to Use |
|---------|-------------|
| **Shared Kernel** | Two contexts share a subset of domain model |
| **Customer-Supplier** | Upstream serves downstream's needs |
| **Conformist** | Downstream adopts upstream's model |
| **Anti-Corruption Layer** | Translate between incompatible models |
| **Published Language** | Documented shared language (events, APIs) |

## Tactical Patterns

### Entities

Objects with identity that persists across time.

```python
class Order:
    """Entity: identity matters, not just attributes"""

    def __init__(self, order_id: OrderId):
        self.id = order_id  # Identity
        self.items: list[OrderItem] = []
        self.status = OrderStatus.DRAFT

    def add_item(self, product: Product, quantity: int) -> None:
        """Business behavior on entity"""
        if self.status != OrderStatus.DRAFT:
            raise InvalidOperationError("Cannot modify placed order")
        self.items.append(OrderItem(product, quantity))

    def place(self) -> None:
        if not self.items:
            raise InvalidOperationError("Cannot place empty order")
        self.status = OrderStatus.PLACED

    def __eq__(self, other):
        if not isinstance(other, Order):
            return False
        return self.id == other.id  # Identity-based equality
```

### Value Objects

Immutable objects defined by their attributes.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    """Value Object: immutable, equality by value"""
    amount: Decimal
    currency: str

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: Decimal) -> "Money":
        return Money(self.amount * factor, self.currency)

@dataclass(frozen=True)
class Address:
    """Value Object: complete address"""
    street: str
    city: str
    postal_code: str
    country: str

    def __post_init__(self):
        if not self.postal_code:
            raise ValueError("Postal code required")
```

### Aggregates

Cluster of entities/value objects treated as a unit.

```python
class Order:
    """Aggregate Root: controls access to OrderItems"""

    def __init__(self, order_id: OrderId, customer: CustomerId):
        self.id = order_id
        self.customer = customer
        self._items: list[OrderItem] = []  # Private, access through root
        self.status = OrderStatus.DRAFT

    @property
    def items(self) -> tuple[OrderItem, ...]:
        return tuple(self._items)  # Immutable view

    @property
    def total(self) -> Money:
        return sum((item.subtotal for item in self._items), Money(0, "USD"))

    def add_item(self, product_id: ProductId, quantity: int, price: Money) -> None:
        """All modifications go through aggregate root"""
        if self.status != OrderStatus.DRAFT:
            raise InvalidOperationError("Cannot modify placed order")

        existing = self._find_item(product_id)
        if existing:
            existing.increase_quantity(quantity)
        else:
            self._items.append(OrderItem(product_id, quantity, price))

    def remove_item(self, product_id: ProductId) -> None:
        self._items = [i for i in self._items if i.product_id != product_id]

    def _find_item(self, product_id: ProductId) -> Optional[OrderItem]:
        return next((i for i in self._items if i.product_id == product_id), None)


class OrderItem:
    """Entity within aggregate: no independent lifecycle"""

    def __init__(self, product_id: ProductId, quantity: int, price: Money):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

    @property
    def subtotal(self) -> Money:
        return self.price.multiply(self.quantity)

    def increase_quantity(self, amount: int) -> None:
        self.quantity += amount
```

### Domain Events

Record of something that happened in the domain.

```python
@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class OrderPlacedEvent(DomainEvent):
    order_id: str
    customer_id: str
    total: Money
    items: tuple[OrderItemDTO, ...]

@dataclass(frozen=True)
class PaymentReceivedEvent(DomainEvent):
    order_id: str
    payment_id: str
    amount: Money

class Order:
    def __init__(self, order_id: OrderId):
        self.id = order_id
        self._domain_events: list[DomainEvent] = []

    def place(self) -> None:
        if not self.items:
            raise InvalidOperationError("Cannot place empty order")

        self.status = OrderStatus.PLACED
        self._domain_events.append(OrderPlacedEvent(
            order_id=str(self.id),
            customer_id=str(self.customer),
            total=self.total,
            items=tuple(OrderItemDTO.from_item(i) for i in self._items)
        ))

    def collect_events(self) -> list[DomainEvent]:
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

### Repositories

Abstract persistence of aggregates.

```python
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    """Repository: persistence abstraction for Order aggregate"""

    @abstractmethod
    async def save(self, order: Order) -> None:
        """Save aggregate (insert or update)"""
        pass

    @abstractmethod
    async def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        """Load complete aggregate"""
        pass

    @abstractmethod
    async def next_identity(self) -> OrderId:
        """Generate new aggregate ID"""
        pass


class PostgresOrderRepository(OrderRepository):
    async def save(self, order: Order) -> None:
        async with self.db.transaction():
            # Save aggregate root
            await self._upsert_order(order)
            # Save child entities
            await self._sync_order_items(order)
            # Publish domain events
            for event in order.collect_events():
                await self.event_publisher.publish(event)

    async def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        # Load complete aggregate in one query
        row = await self.db.fetchrow("""
            SELECT o.*, json_agg(i.*) as items
            FROM orders o
            LEFT JOIN order_items i ON i.order_id = o.id
            WHERE o.id = $1
            GROUP BY o.id
        """, str(order_id))
        return self._to_aggregate(row) if row else None
```

### Domain Services

Operations that don't belong to a single entity.

```python
class OrderPricingService:
    """Domain Service: pricing logic spanning multiple entities"""

    def __init__(
        self,
        discount_policy: DiscountPolicy,
        tax_calculator: TaxCalculator
    ):
        self.discount_policy = discount_policy
        self.tax_calculator = tax_calculator

    def calculate_total(self, order: Order, customer: Customer) -> OrderTotal:
        subtotal = order.subtotal

        # Apply discounts based on customer tier
        discount = self.discount_policy.calculate(customer.tier, subtotal)
        after_discount = subtotal.subtract(discount)

        # Calculate tax
        tax = self.tax_calculator.calculate(after_discount, order.shipping_address)

        return OrderTotal(
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total=after_discount.add(tax)
        )
```

## Aggregate Design Rules

1. **Reference by identity**: Aggregates reference each other by ID, not object reference
2. **One aggregate per transaction**: Modify only one aggregate per transaction
3. **Small aggregates**: Keep aggregates small for concurrency
4. **Eventual consistency**: Accept eventual consistency between aggregates

```python
class Order:
    """References Customer by ID, not object"""
    customer_id: CustomerId  # ✓ Reference by ID

    # NOT: customer: Customer  # ✗ Object reference

class OrderService:
    async def place_order(self, order: Order) -> None:
        # Load customer aggregate separately if needed
        customer = await self.customer_repo.find_by_id(order.customer_id)
        if not customer.can_place_orders():
            raise InvalidOperationError("Customer cannot place orders")

        order.place()
        await self.order_repo.save(order)

        # Update customer asynchronously (eventual consistency)
        await self.event_bus.publish(OrderPlacedEvent(...))
```
