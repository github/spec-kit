# spec-driven-blueprint skill

A Claude Code skill that walks the user through Spec-Driven Development end-to-end and produces a single consolidated `BLUEPRINT.md` that drives implementation.

## What this skill does

Instead of running `/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, and `/speckit.tasks` as separate steps and ending up with five files, this skill runs one guided interview and produces **one** Markdown file. The blueprint contains:

- Constitutional gates the implementer must respect
- Prioritized user scenarios (P1/P2/P3) with Given/When/Then acceptance criteria
- Functional requirements (with at most 3 `[NEEDS CLARIFICATION]` markers)
- Measurable, technology-agnostic success criteria
- Technical context (language, deps, storage, performance, scale)
- Concrete project structure
- A strict, sequenced task list organized by user story
- Dependencies, parallel opportunities, and an implementation strategy

The blueprint is designed to be handed to an implementing agent (or `/speckit.implement`) without further preparation.

## Files in this skill

| File                       | Purpose                                                             |
|----------------------------|---------------------------------------------------------------------|
| `SKILL.md`                 | The skill itself — instructions Claude follows when invoked.         |
| `blueprint-template.md`    | The empty blueprint structure the skill fills in.                    |
| `example-blueprint.md`     | A worked example (URL shortener) for pattern-matching.               |
| `README.md`                | This file — installation and usage notes.                            |

## Installing

### Option A: Project-scoped (lives with the repo)

The skill is already at `.claude/skills/spec-driven-blueprint/SKILL.md`. Anyone who clones the repo and runs Claude Code from its root gets the skill automatically.

### Option B: Personal scope (use it on any project)

Copy the directory into your personal Claude config:

```bash
mkdir -p ~/.claude/skills
cp -r .claude/skills/spec-driven-blueprint ~/.claude/skills/
```

### Option C: Plugin

If you maintain a Claude plugin, drop this skill directory into the plugin's `skills/` folder and ship it like any other capability.

## Using the skill

Once installed, trigger it with any of these:

- "Walk me through spec-driven development for [feature idea]."
- "Create an SDD blueprint for [feature idea]."
- "Drive the development of [feature] with a spec."
- "Guide me through the spec-kit workflow."

Claude will run the 14-phase workflow defined in `SKILL.md`:

1. Detect environment (spec-kit repo? constitution present?).
2. Capture the idea.
3. Generate short-name and confirm output path.
4. Constitutional gates.
5. User scenarios (WHAT).
6. Functional requirements + entities.
7. Clarify (only if `[NEEDS CLARIFICATION]` markers remain).
8. Success criteria.
9. Technical context (HOW, high level).
10. Constitution re-check.
11. Project structure.
12. Tasks.
13. Write `BLUEPRINT.md`.
14. Self-validate, then report.

The output is written to `specs/<NNN>-<short-name>/BLUEPRINT.md` in spec-kit-initialized repos, or `./BLUEPRINT.md` otherwise. The path is always confirmed with the user before writing.

## Why one file instead of five

- Easier to review in a PR description or chat thread.
- Easier to hand to an implementing agent without losing cross-references.
- Easier to keep in sync — one file evolves, no risk of drift between `spec.md` and `plan.md`.
- Easier to lift sections back out into separate spec-kit artifacts later if needed; the section structure mirrors the spec-kit templates.

## Relationship to spec-kit core commands

This skill **does not replace** spec-kit. If your team already uses `/speckit.specify`, `/speckit.plan`, `/speckit.tasks` and the discrete-artifact workflow, keep using them. This skill is for the case where you want a single consolidated blueprint — for personal projects, quick prototypes, blog posts, design reviews, or feeding another agent.
