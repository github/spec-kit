# Library Gotchas and Workarounds

This file documents known issues, quirks, and workarounds for libraries used in this project. Include specific version numbers and examples.

## Template Format

```markdown
## [Library Name] v[Version]

**Issue**: Brief description of the problem
**Gotcha**: What to watch out for
**Workaround**: How to handle it correctly
**Example**: Code snippet showing the right way

### Critical Issues
- List any breaking changes or major issues

### Common Mistakes
- List frequent errors developers encounter
```

## Example Entry

## FastAPI v0.104.1

**Issue**: Async functions required for database operations
**Gotcha**: Using sync database calls in async endpoints causes blocking
**Workaround**: Always use async database client methods
**Example**:
```python
# Wrong - blocks the event loop
@app.get("/users")
def get_users():
    return db.query(User).all()

# Correct - non-blocking
@app.get("/users")
async def get_users():
    return await db.execute(select(User))
```

### Critical Issues
- Pydantic v2 migration requires model_dump() instead of dict()
- Background tasks must be async if they access the database

### Common Mistakes
- Forgetting `await` with database operations
- Using sync functions in async contexts
- Not handling database connection cleanup

---

*Note: Add your library-specific gotchas below using the template format*