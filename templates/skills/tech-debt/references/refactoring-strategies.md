# Refactoring Strategies

## Safe Refactoring Principles

### The Golden Rules

1. **Never refactor without tests**
   - Add characterization tests first
   - Tests describe current behavior
   - They'll catch regressions

2. **Small, incremental changes**
   - One refactoring at a time
   - Commit frequently
   - Easy to bisect if broken

3. **Separate refactoring from feature work**
   - Don't mix behavior changes
   - Pure refactoring = same behavior
   - Easier to review and rollback

4. **Use automated refactoring tools**
   - IDE refactorings are safer
   - Extract, rename, move
   - Less error-prone than manual

## Refactoring Techniques

### Extract Method
**When:** Long method, repeated code, complex conditional

```python
# Before
def process_order(order):
    # validation logic (10 lines)
    # pricing logic (15 lines)
    # notification logic (10 lines)

# After
def process_order(order):
    validate_order(order)
    calculate_pricing(order)
    send_notifications(order)
```

### Extract Class
**When:** Class has multiple responsibilities

```python
# Before
class User:
    def authenticate(self): ...
    def send_email(self): ...
    def calculate_discount(self): ...

# After
class User: ...
class AuthenticationService: ...
class EmailService: ...
class DiscountCalculator: ...
```

### Replace Conditional with Polymorphism
**When:** Switch/if-else on type

```python
# Before
def calculate_area(shape):
    if shape.type == "circle":
        return pi * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height

# After
class Circle:
    def area(self): return pi * self.radius ** 2

class Rectangle:
    def area(self): return self.width * self.height
```

### Introduce Parameter Object
**When:** Multiple parameters travel together

```python
# Before
def search(query, page, page_size, sort_by, sort_order, filters):
    ...

# After
@dataclass
class SearchParams:
    query: str
    page: int = 1
    page_size: int = 20
    sort_by: str = "relevance"
    sort_order: str = "desc"
    filters: dict = None

def search(params: SearchParams):
    ...
```

### Replace Magic Numbers with Constants
**When:** Hard-coded values without context

```python
# Before
if response.status_code == 429:
    time.sleep(60)

# After
RATE_LIMIT_STATUS = 429
RATE_LIMIT_COOLDOWN_SECONDS = 60

if response.status_code == RATE_LIMIT_STATUS:
    time.sleep(RATE_LIMIT_COOLDOWN_SECONDS)
```

## Large-Scale Refactoring Patterns

### Strangler Fig Pattern
**Use for:** Replacing legacy systems

1. Create new implementation alongside old
2. Route traffic gradually to new system
3. Strangle old system over time
4. Remove old code when fully migrated

```
[Client] → [Router] → [New System]
                   ↘ [Legacy System]
```

### Branch by Abstraction
**Use for:** Replacing implementations safely

1. Create abstraction over existing code
2. All clients use abstraction
3. Implement new version behind abstraction
4. Switch implementations via config
5. Remove old implementation

```python
# Step 1: Abstract
class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, payment): ...

# Step 2: Wrap legacy
class LegacyPaymentProcessor(PaymentProcessor):
    def process(self, payment):
        return legacy_payment_code(payment)

# Step 3: New implementation
class NewPaymentProcessor(PaymentProcessor):
    def process(self, payment):
        return new_payment_code(payment)

# Step 4: Toggle
processor = NewPaymentProcessor() if feature_flag else LegacyPaymentProcessor()
```

### Parallel Change (Expand and Contract)
**Use for:** Changing interfaces safely

1. **Expand**: Add new interface alongside old
2. **Migrate**: Move clients to new interface
3. **Contract**: Remove old interface

```python
# Phase 1: Expand
def get_user(user_id):  # Old
    ...

def get_user_by_id(user_id):  # New
    return get_user(user_id)

# Phase 2: Migrate clients to get_user_by_id

# Phase 3: Contract
def get_user_by_id(user_id):
    ...  # Now contains the logic
# Remove get_user
```

## Prioritization Framework

### Debt Quadrant Analysis

```
                    High Business Value
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    │   SCHEDULE SPRINT    │    DO FIRST          │
    │   (Plan carefully)   │    (Quick wins +     │
    │                      │     high impact)     │
    │                      │                      │
Low ├──────────────────────┼──────────────────────┤ High
Effort                     │                      Effort
    │                      │                      │
    │   QUICK WINS         │    DEFER/CONSIDER    │
    │   (Boy Scout rule)   │    (Is it worth it?) │
    │                      │                      │
    └──────────────────────┼──────────────────────┘
                           │
                    Low Business Value
```

### Decision Matrix

| Factor | Weight | Questions to Ask |
|--------|--------|------------------|
| Risk | 30% | What breaks if we don't fix? |
| Value | 25% | How much faster/safer/better? |
| Cost | 20% | How long to fix properly? |
| Dependencies | 15% | What else is blocked? |
| Team | 10% | Who can do this work? |

## Metrics to Track

### Before Refactoring
- Cyclomatic complexity
- Code coverage
- Build time
- Test execution time
- Bug rate in area

### After Refactoring
- Same metrics (should improve)
- No regression in behavior
- Team velocity (should improve over time)
- Developer satisfaction
