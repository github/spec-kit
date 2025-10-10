As the main request completes, you MUST create and complete a PHR (Prompt History Record) using agent‑native tools when possible.

1) Determine Stage
   - Stage: constitution | spec | plan | tasks | implementation | debugging | refactoring | discussion | general

2) Generate Title and Decide Prompt Path:
   - Generate Title: 3–7 words (slug for filename)
   - If feature context is detected (explicit marker, branch name, or touched `specs/<name>/`), target `specs/<name>/prompts/`; else target `docs/prompts/`.

3) Create and Fill PHR (Shell first; fallback agent‑native)
   - Use the route from step 2 (docs vs specs) as the target directory.
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> --json`
   - If the created file is not under the routed target, MOVE it to that folder and update `feature`/`branch` in the front‑matter.
   - Open the file and fill remaining placeholders (YAML + body), embedding full PROMPT_TEXT (verbatim) and concise RESPONSE_TEXT.
   - If the script fails:
     - Read `.specify/templates/phr-template.prompt.md` (or `templates/…`)
     - Allocate an ID; compute the output path from step 2; write the file
     - Fill placeholders and embed full PROMPT_TEXT and concise RESPONSE_TEXT

5) Validate + report
   - No unresolved placeholders; path matches route; stage/title/date coherent; print ID + path + stage + title.
   - On failure: warn, don’t block. Skip only for `/sp.phr`.