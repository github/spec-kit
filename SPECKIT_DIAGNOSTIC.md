# SpecKit Installation Diagnostic

> **Run this in a fresh Claude Code session to verify SpecKit installation**

---

## Instructions for Claude

Please verify the current SpecKit installation and provide a detailed status report.

---

## 1. Command Verification

**Check speckit commands availability:**

```bash
ls -la ~/.claude/commands/speckit.*.md
```

Expected output: 11 command files

**Check modification dates:**

```bash
ls -lt ~/.claude/commands/speckit.*.md | head -10
```

Expected: Most files dated 2025-03-11 or later

---

## 2. Model Configuration

**Verify embedding model in code:**

```bash
grep -r "mxbai-embed-large" src/specify_cli/memory/
```

Expected: Found in ollama_client.py and ollama_checker.py

**Check project config:**

```bash
cat .spec-kit/project.json | grep embedding_model
```

Expected: `"embedding_model": "mxbai-embed-large"`

---

## 3. Ollama Status

**Check container status:**

```bash
docker ps | grep ollama
```

Expected: Container running

**Verify model:**

```bash
docker exec ollama ollama list | grep mxbai-embed-large
```

Expected: mxbai-embed-large:latest listed

**Test API:**

```bash
curl -s http://localhost:11434/api/tags | head -c 200
```

Expected: JSON response with models

---

## 4. Memory Structure

**Check memory directories:**

```bash
ls -la ~/.claude/memory/projects/
```

Expected: F--IdeaProjects-spec-kit directory exists

**Verify symlink:**

```bash
ls -la ~/.claude/spec-kit
```

Expected: Symlink to F:/IdeaProjects/spec-kit

---

## 5. File Sync Status

**Compare commands with templates:**

```bash
cd ~/.claude/commands
for cmd in specify plan tasks clarify analyze implement checklist constitution taskstoissues; do
  echo -n "speckit.$cmd.md: "
  diff -q "speckit.$cmd.md" "../spec-kit/templates/commands/$cmd.md" && echo "✓ SYNCED" || echo "✗ DIFFERS"
done
```

Expected: All show "✓ SYNCED"

---

## 6. Features Command

**Verify /speckit.features exists:**

```bash
ls -la ~/.claude/commands/speckit.features.md
```

Expected: File exists (custom command)

**Check content:**

```bash
head -30 ~/.claude/commands/speckit.features.md
```

Expected: Description mentions "Quick feature generation"

---

## Report Format

Please provide results in this format:

### ✅ SpecKit Diagnostic Report

| Check | Status | Details |
|-------|--------|---------|
| Commands available | ✅/⚠️/❌ | [count] commands found |
| Command dates | ✅/⚠️/❌ | Most recent: [date] |
| Model configured | ✅/⚠️/❌ | mxbai-embed-large in [N] files |
| Ollama running | ✅/⚠️/❌ | Container: [status] |
| Model available | ✅/⚠️/❌ | mxbai-embed-large: [size] |
| Memory structure | ✅/⚠️/❌ | Projects: [count] |
| Symlink valid | ✅/⚠️/❌ | Target: [path] |
| Files synced | ✅/⚠️/❌ | [N]/[N] commands match |
| Features cmd | ✅/⚠️/❌ | Custom command present |

### Summary

[Overall assessment: INSTALLATION COMPLETE / NEEDS ATTENTION / FAILED]

### Issues Found

[List any ❌ or ⚠️ items with details]

### Recommendations

[Actions needed if any]

---

*Diagnostic Script v1.0 - Compatible with SpecKit Global Agent Memory*
