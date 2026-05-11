# Infrastructure Resource Registry

Track all infrastructure compositions and their current status.

## Status Reference

| Symbol | Meaning |
|--------|---------|
| 🔵 `initializing` | Track created, spec in progress |
| 📝 `spec-generated` | Spec confirmed, ready for plan |
| 📋 `planned` | Plan generated, ready for implementation |
| ⚙️ `in-progress` | Implementation underway |
| ✅ `done` | Implementation complete and reviewed |
| ❌ `blocked` | Blocked, needs attention |

---

## Tracks

| Track | Type | Directory | Status | Created |
|-------|------|-----------|--------|---------|
| `xpostgresql-instance-20260415-101500` | create | `compositions/xpostgresql-instance/` | ✅ done | 2026-04-15 |
