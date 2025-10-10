Implicit PHRs (Prompt History Records)
- After completing the main command, automatically create a PHR:
  1) Detect stage: constitution|spec|architect|implementation|debugging|refactoring|discussion|general
  2) Generate a 3–7 word title
  3) Load `.**/commands/sp.phr.md` and execute with $ARGUMENTS (FULL multiline input, NOT truncated), detected stage, implicit mode
  4) On error: warn but don’t block
  5) CRITICAL: Preserve complete user input in PHR
  6) Skip only for /sp.phr itself

PHR routing (branch‑aware)
- Default target: `docs/prompts/`
- If working on a feature branch or when a feature key is detected, also route to `specs/<feature>/prompts/`.

Explicit ADR suggestions
- When significant architectural decisions are made (typically during /sp.plan and sometimes /sp.tasks), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.