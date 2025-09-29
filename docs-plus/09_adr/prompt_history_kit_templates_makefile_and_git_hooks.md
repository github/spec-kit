# Prompt History Kit (PHR)

Drop these files into your repo to start treating prompts as first‑class artifacts alongside ADRs. The kit includes:
- **Templates** for prompts and ADRs
- **Makefile targets** to create and index prompts
- **Git hooks** to nudge contributors to link or add prompts when code changes

> Paths are suggestions; adjust to your repo.

---

## 1) Directory layout
```
docs/
  adr/
    0000-template.md
  prompts/
    0000-template.prompt.md
scripts/
  prompt_new.py
  prompt_index.py
  prompt_guard.py
.githooks/
  pre-commit
  commit-msg
Makefile
```

---

## 2) Templates

### 2.1 `docs/prompts/0000-template.prompt.md`
```markdown
---
id: 0000
title: <short title>
stage: architect           # architect | red | green | refactor | explainer | adr-draft | pr-draft
date: YYYY-MM-DD
surface: cursor-composer   # cursor-inline | cursor-chat | cursor-composer | codex-cloud | codex-cli
model: gpt-5-codex
repo_ref: <branch or commit>
scope_files: []            # ["path/one.py", "tests/test_x.py"]
links:
  adr: null
  issue: null
  pr: null
acceptance: []             # Given/When/Then bullets
constraints:
  - minimal diff, no new deps
  - offline tests (mocks)
out_of_scope: []
secrets_policy: "No secrets; use .env"
labels: []                 # ["api", "streaming", "guardrails"]
---

<PASTE THE EXACT PROMPT YOU USED>

### Outcome (fill after run)
- Files changed: ...
- Tests added: ...
- Next prompts: ...
- Notes: ...
```

### 2.2 `docs/adr/0000-template.md`
```markdown
# ADR-0000: <Title>
- **Status:** Proposed | Accepted | Superseded | Deprecated
- **Date:** YYYY-MM-DD

## Context
<Problem, constraints, forces>

## Options
- **A)** ... (pros/cons)
- **B)** ...

## Decision
<Chosen option and why>

## Consequences
- Positive: ...
- Negative: ...

## References
- Links to PRs, issues, benchmarks
- Related Prompts: PHR-####, PHR-####
```

---

## 3) Makefile
```makefile
# --- Prompt History targets ---
PHR_DIR := docs/prompts
ADR_DIR := docs/adr

## Create a new prompt file
## Usage: make prompt-new SLUG=chat-endpoint STAGE=architect
prompt-new:
	@python3 scripts/prompt_new.py --dir $(PHR_DIR) --slug $(SLUG) --stage $(STAGE)

## Rebuild prompt index (docs/prompts/index.md)
prompt-index:
	@python3 scripts/prompt_index.py --dir $(PHR_DIR)

## Validate staged changes reference a prompt (run manually if no hooks)
prompt-guard:
	@python3 scripts/prompt_guard.py
```

---

## 4) Scripts

### 4.1 `scripts/prompt_new.py`
```python
#!/usr/bin/env python3
import argparse, pathlib, re, datetime, sys

TPL = """---
id: {id}
title: {title}
stage: {stage}
date: {date}
surface: cursor-composer
model: gpt-5-codex
repo_ref: <branch-or-commit>
scope_files: []
links:\n  adr: null\n  issue: null\n  pr: null
acceptance: []
constraints:\n  - minimal diff, no new deps\n  - offline tests (mocks)
out_of_scope: []
secrets_policy: "No secrets; use .env"
labels: []
---

<PASTE THE EXACT PROMPT YOU USED>

### Outcome
- Files changed:
- Tests added:
- Next prompts:
- Notes:
"""

def next_id(dir: pathlib.Path) -> int:
    ids = []
    for p in dir.glob("*.prompt.md"):
        m = re.match(r"(\d{4})-", p.name)
        if m:
            ids.append(int(m.group(1)))
    return max(ids) + 1 if ids else 1

parser = argparse.ArgumentParser()
parser.add_argument("--dir", required=True)
parser.add_argument("--slug", required=True)
parser.add_argument("--stage", required=True, choices=["architect","red","green","refactor","explainer","adr-draft","pr-draft"])
parser.add_argument("--title", default=None)
args = parser.parse_args()

root = pathlib.Path(args.dir)
root.mkdir(parents=True, exist_ok=True)
_id = next_id(root)
id_str = f"{_id:04d}"
slug = re.sub(r"[^a-z0-9-]","-", args.slug.lower())
fn = root / f"{id_str}-{slug}-{args.stage}.prompt.md"

content = TPL.format(
    id=id_str,
    title=(args.title or args.slug.replace("-"," ")).title(),
    stage=args.stage,
    date=datetime.date.today().isoformat(),
)
fn.write_text(content)
print(str(fn))
```

### 4.2 `scripts/prompt_index.py`
```python
#!/usr/bin/env python3
import argparse, pathlib, re
from datetime import date

parser = argparse.ArgumentParser()
parser.add_argument("--dir", required=True)
args = parser.parse_args()
root = pathlib.Path(args.dir)
rows = []
for p in sorted(root.glob("*.prompt.md")):
    head = p.read_text().split("---",2)
    meta = head[1] if len(head) > 2 else ""
    def get(k):
        m = re.search(rf"\n{k}:\s*(.*)", meta)
        return (m.group(1).strip() if m else "").strip()
    rid = get("id") or p.name[:4]
    title = get("title") or p.stem
    stage = get("stage") or "?"
    date_val = get("date") or ""
    rows.append((rid, title, stage, date_val, p.name))

index = ["# Prompt History Index\n", "| ID | Title | Stage | Date | File |\n", "|---|---|---|---|---|\n"]
for r in rows:
    index.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |\n")
(root/"index.md").write_text("".join(index))
print("Wrote", root/"index.md")
```

### 4.3 `scripts/prompt_guard.py`
```python
#!/usr/bin/env python3
"""Fail if staged code changes lack a prompt reference or a new prompt file.
- If any staged file under app/, src/, or tests/ changes -> require either:
  * a staged file matching docs/prompts/*.prompt.md, or
  * commit message contains PHR-#### (checked in commit-msg hook instead)
This script is used in pre-commit to nudge authors.
"""
import subprocess, sys, re

# staged files
res = subprocess.run(["git","diff","--cached","--name-only"], capture_output=True, text=True)
staged = [p.strip() for p in res.stdout.splitlines() if p.strip()]

code_changed = any(p.startswith(("app/","src/","tests/")) for p in staged)
prompt_added = any(p.startswith("docs/prompts/") and p.endswith(".prompt.md") for p in staged)

if code_changed and not prompt_added:
    print("\n[PHR] Staged code changes detected but no prompt file added.")
    print("Add a prompt via: make prompt-new SLUG=<slug> STAGE=<stage>\n")
    sys.exit(1)
sys.exit(0)
```

> Make the scripts executable: `chmod +x scripts/*.py`

---

## 5) Git hooks

### 5.1 Use a repo-local hooks path
Run once:
```
git config core.hooksPath .githooks
```

### 5.2 `.githooks/pre-commit`
```bash
#!/usr/bin/env bash
set -euo pipefail

# Ensure prompt guard passes (requires Python)
if [ -f scripts/prompt_guard.py ]; then
  python3 scripts/prompt_guard.py
fi

# Basic lint: block secrets in prompts
if git diff --cached --name-only | grep -E '^docs/prompts/.+\.prompt\.md$' >/dev/null; then
  if git diff --cached | grep -E 'AKIA|SECRET_KEY|BEGIN RSA PRIVATE KEY' >/dev/null; then
    echo "[PHR] Possible secret found in prompt file. Abort." >&2
    exit 1
  fi
fi
```

### 5.3 `.githooks/commit-msg`
```bash
#!/usr/bin/env bash
set -euo pipefail
MSG_FILE="$1"
MSG_CONTENT=$(cat "$MSG_FILE")

# Allow revert/merge commits
if echo "$MSG_CONTENT" | grep -Eqi '^(Merge|Revert)'; then
  exit 0
fi

# If code changed and no prompt file was added, require a PHR reference in the message
CHANGED=$(git diff --cached --name-only)
if echo "$CHANGED" | grep -E '^(app/|src/|tests/)' >/dev/null; then
  if ! echo "$CHANGED" | grep -E '^docs/prompts/.+\.prompt\.md$' >/dev/null; then
    if ! echo "$MSG_CONTENT" | grep -E 'PHR-\d{4}' >/dev/null; then
      echo "[PHR] Add a prompt reference like 'refs: PHR-0123' to the commit message or stage a prompt file." >&2
      exit 1
    fi
  fi
fi
```

> Make hooks executable: `chmod +x .githooks/*`

---

## 6) Usage examples

### Create an architect prompt
```
make prompt-new SLUG=chat-endpoint STAGE=architect
```
Open the created file in `docs/prompts/####-chat-endpoint-architect.prompt.md`, paste your prompt, run it in Cursor, then append the **Outcome**.

### Add tests (red)
```
make prompt-new SLUG=chat-endpoint STAGE=red
```

### Implement minimal diff (green) & refactor
```
make prompt-new SLUG=chat-endpoint STAGE=green
make prompt-new SLUG=chat-endpoint STAGE=refactor
```

### Rebuild the index
```
make prompt-index
```

---

## 7) PR template snippet
```markdown
### Prompt History
- Architect: docs/prompts/00xx-*-architect.prompt.md
- Red: docs/prompts/00xx-*-red.prompt.md
- Green: docs/prompts/00xx-*-green.prompt.md

### ADR
- docs/adr/00yy-*.md
```

You’re ready to ship with **prompts as artifacts**: small, test‑guarded steps with a replayable history.

