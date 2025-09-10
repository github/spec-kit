---
name: plan
description: "Create a technical implementation plan based on the current specification."
---

Create a technical implementation plan for the current feature specification.

Given the technical requirements and architecture choices provided as arguments, do this:

1. Read the current specification from `specs/[FEATURE_NAME]/spec.md`
2. Load `templates/plan-template.md` to understand required sections
3. Create implementation plan in `specs/[FEATURE_NAME]/plan.md` with:
   - Technology stack decisions
   - Architecture overview
   - Implementation phases
   - File structure
   - Dependencies and prerequisites
4. Generate necessary contract files (API specs, data models, etc.)
5. Create research document for any uncertain technical aspects

**Cursor-specific notes:**
- Use Cursor's multi-file editing capabilities to create comprehensive plans
- Leverage Cursor's knowledge of modern development practices
- Consider Cursor's built-in tools and extensions ecosystem
- Focus on practical, implementable technical decisions
