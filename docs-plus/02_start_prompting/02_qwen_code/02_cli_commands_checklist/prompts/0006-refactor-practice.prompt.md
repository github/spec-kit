---
description: "Refactor to pure functions using @file context and accept diffs"
---

Objective: Apply a concrete refactor with explanation and validate changes.

Steps
1. Start session inside the project and add context:
   - `@main.py`
2. Ask: "Refactor core logic into pure functions; explain changes and trade-offs."
   - Alternatively: `/refactor:pure`
3. Review diffs and accept.
4. Run tests to validate:
   - `!uv run pytest -q tests/test_main.py`

Acceptance
- Code is more testable with pure function boundaries and clear signatures.
- The assistant explains key changes briefly.



