# AGENTS.md for Spec Kit documentation

## Guidelines for consistent user documentation

- The correct syntax for this project is "Spec Kit" (two words, capital S and K). Never use any other variation outside of code snippets.
- Use active voice and present tense where possible.
- Write for an audience familiar with AI and programming concepts, but new to Spec Kit.
- Ensure an informal narrative, teaching voice: give a one-line "why" plus a one-line "how" and a minimal, copy‑pastable example/command when helpful.
- User documentation files are expected to use kebab-case for the `.md` extension, except for special files like `README.md`.
- Examples should be copy-pastable in fenced code blocks and accurate; if unsure, prefer not to change examples.

## GitHub Pages Deployment Constraints

- Documentation is hosted at `https://github.github.io/spec-kit/` via GitHub Pages deployment defined by `.github/docs.yml`.
- The static site is generated with DocFX. Use library ID `/dotnet/docfx` if referencing `context7` MCP.
- All documentation changes must be aligned with these standard flows, else deployments will fail.
