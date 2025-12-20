# Microservices Data Patterns

> Patterns for managing data in distributed systems.

## Database per Service

Each microservice owns its database. No shared access.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  OrderService   │    │ PaymentService  │    │ InventoryService│
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
    ┌────▼────┐            ┌────▼────┐            ┌────▼────┐
    │ Orders  │            │Payments │            │Inventory│
    │   DB    │            │   DB    │            │   DB    │
    └─────────┘            └─────────┘            └─────────┘
```

**Benefits:**
- Independent scaling
- Technology freedom (SQL, NoSQL, etc.)
- Fault isolation
- Independent deployments

## Saga Pattern

Manage distributed transactions through compensating actions.

### Choreography (Event-Based)

```python
# Order Service publishes event
class OrderService:
    async def create_order(self, order: Order):
        order = await self.repository.save(order)
        await self.event_bus.publish(OrderCreatedEvent(
            order_id=order.id,
            items=order.items,
            total=order.total
        ))
        return order

# Payment Service reacts
class PaymentService:
    @event_handler(OrderCreatedEvent)
    async def handle_order_created(self, event: OrderCreatedEvent):
        try:
            payment = await self.process_payment(event.order_id, event.total)
            await self.event_bus.publish(PaymentCompletedEvent(
                order_id=event.order_id,
                payment_id=payment.id
            ))
        except PaymentFailedError:
            await self.event_bus.publish(PaymentFailedEvent(
                order_id=event.order_id,
                reason="Insufficient funds"
            ))

# Order Service compensates on failure
class OrderService:
    @event_handler(PaymentFailedEvent)
    async def handle_payment_failed(self, event: PaymentFailedEvent):
        await self.repository.update_status(event.order_id, "CANCELLED")
```

### Orchestration (Central Coordinator)

```python
class OrderSagaOrchestrator:
    def __init__(self):
        self.steps = [
            SagaStep(
                action=self.reserve_inventory,
                compensation=self.release_inventory
            ),
            SagaStep(
                action=self.process_payment,
                compensation=self.refund_payment
            ),
            SagaStep(
                action=self.create_shipment,
                compensation=self.cancel_shipment
            ),
        ]

    async def execute(self, order: Order):
        completed_steps = []

        for step in self.steps:
            try:
                await step.action(order)
                completed_steps.append(step)
            except Exception as e:
                # Compensate in reverse order
                for completed in reversed(completed_steps):
                    await completed.compensation(order)
                raise SagaFailedError(f"Saga failed at {step}: {e}")

        return order
```

## Event Sourcing

Store state as a sequence of events.

```python
class OrderAggregate:
    def __init__(self, order_id: str):
        self.id = order_id
        self.status = None
        self.items = []
        self.events = []

    def apply(self, event: DomainEvent):
        if isinstance(event, OrderCreatedEvent):
            self.status = "CREATED"
            self.items = event.items
        elif isinstance(event, OrderPaidEvent):
            self.status = "PAID"
        elif isinstance(event, OrderShippedEvent):
            self.status = "SHIPPED"

    @classmethod
    def from_events(cls, order_id: str, events: list[DomainEvent]):
        aggregate = cls(order_id)
        for event in events:
            aggregate.apply(event)
        return aggregate

# Event Store
class EventStore:
    async def append(self, aggregate_id: str, events: list[DomainEvent]):
        for event in events:
            await self.db.insert({
                "aggregate_id": aggregate_id,
                "event_type": type(event).__name__,
                "data": event.to_dict(),
                "timestamp": datetime.utcnow(),
                "version": self.get_next_version(aggregate_id)
            })

    async def get_events(self, aggregate_id: str) -> list[DomainEvent]:
        rows = await self.db.query(
            "SELECT * FROM events WHERE aggregate_id = ? ORDER BY version",
            aggregate_id
        )
        return [self.deserialize(row) for row in rows]
```

## CQRS (Command Query Responsibility Segregation)

Separate read and write models.

```python
# Write Model (Commands)
class OrderCommandService:
    async def create_order(self, cmd: CreateOrderCommand) -> str:
        order = Order.create(cmd.customer_id, cmd.items)
        await self.repository.save(order)
        await self.event_bus.publish(OrderCreatedEvent(order))
        return order.id

# Read Model (Queries)
class OrderQueryService:
    async def get_order_summary(self, order_id: str) -> OrderSummaryDTO:
        # Read from denormalized read-optimized view
        return await self.read_db.query_one(
            "SELECT * FROM order_summaries WHERE id = ?",
            order_id
        )

    async def search_orders(self, criteria: SearchCriteria) -> list[OrderSummaryDTO]:
        # Complex queries on read model
        return await self.elasticsearch.search(criteria)

# Event Handler updates read model
class OrderProjection:
    @event_handler(OrderCreatedEvent)
    async def on_order_created(self, event: OrderCreatedEvent):
        await self.read_db.insert("order_summaries", {
            "id": event.order_id,
            "customer_id": event.customer_id,
            "status": "CREATED",
            "item_count": len(event.items),
            "total": event.total,
            "created_at": event.timestamp
        })
```

## Outbox Pattern

Ensure reliable event publishing with database transactions.

```python
class OrderService:
    async def create_order(self, order: Order):
        async with self.db.transaction():
            # 1. Save order
            await self.repository.save(order)

            # 2. Save event to outbox (same transaction)
            await self.outbox.save(OutboxMessage(
                aggregate_type="Order",
                aggregate_id=order.id,
                event_type="OrderCreated",
                payload=order.to_event_dict()
            ))

# Background worker publishes from outbox
class OutboxPublisher:
    async def run(self):
        while True:
            messages = await self.outbox.get_unpublished(limit=100)
            for msg in messages:
                try:
                    await self.event_bus.publish(msg.to_event())
                    await self.outbox.mark_published(msg.id)
                except Exception:
                    await self.outbox.increment_retry(msg.id)
            await asyncio.sleep(1)
```

## Best Practices

1. **Eventual consistency**: Accept it, design for it
2. **Idempotent operations**: Handle duplicate messages gracefully
3. **Event versioning**: Plan for schema evolution
4. **Correlation IDs**: Trace requests across services
5. **Dead letter queues**: Handle failed messages
6. **Compensating transactions**: Always plan the "undo" path
