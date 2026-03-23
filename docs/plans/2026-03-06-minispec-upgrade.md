# `minispec upgrade` Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `minispec upgrade` command that updates scaffolding files from the latest release while preserving user content.

**Architecture:** Reuses the existing `download_template_from_github()` to fetch the release ZIP. Extracts to a temp directory, then applies files in three tiers: silent overwrite for internal scaffolding, deep merge for JSON config files, and diff-and-prompt for agent command files. Reports every file action in a detailed summary.

**Tech Stack:** Python 3.11+, Typer, Rich, httpx, difflib (stdlib)

---

## Tasks

### Task 1: Add `_detect_project_config()` helper

Detects which agent and script type are installed in the current project by scanning for known directory patterns.

**Files:**

- Modify: `src/minispec_cli/__init__.py` (add function after `AGENT_COMMAND_CONFIG` block, around line 260)
- Test: `tests/test_upgrade.py`

**Step 1: Write the failing test**

```python
# tests/test_upgrade.py
"""Tests for minispec upgrade command."""

from pathlib import Path

import pytest

from minispec_cli import _detect_project_config


class TestDetectProjectConfig:
    def test_detects_claude_sh(self, tmp_path):
        (tmp_path / ".claude" / "commands").mkdir(parents=True)
        (tmp_path / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        agent, script = _detect_project_config(tmp_path)
        assert agent == "claude"
        assert script == "sh"

    def test_detects_copilot_ps(self, tmp_path):
        (tmp_path / ".github" / "agents").mkdir(parents=True)
        (tmp_path / ".minispec" / "scripts" / "powershell").mkdir(parents=True)
        agent, script = _detect_project_config(tmp_path)
        assert agent == "copilot"
        assert script == "ps"

    def test_detects_cursor(self, tmp_path):
        (tmp_path / ".cursor" / "commands").mkdir(parents=True)
        (tmp_path / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        agent, script = _detect_project_config(tmp_path)
        assert agent == "cursor-agent"
        assert script == "sh"

    def test_no_agent_found(self, tmp_path):
        (tmp_path / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        with pytest.raises(SystemExit):
            _detect_project_config(tmp_path)

    def test_no_script_found(self, tmp_path):
        (tmp_path / ".claude" / "commands").mkdir(parents=True)
        (tmp_path / ".minispec").mkdir(parents=True)
        with pytest.raises(SystemExit):
            _detect_project_config(tmp_path)

    def test_no_minispec_dir(self, tmp_path):
        with pytest.raises(SystemExit):
            _detect_project_config(tmp_path)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_upgrade.py -v`
Expected: FAIL — `_detect_project_config` not found

**Step 3: Write minimal implementation**

```python
def _detect_project_config(project_path: Path) -> tuple[str, str]:
    """Detect which agent and script type are installed in a MiniSpec project.

    Returns (agent_key, script_type) or exits with error if ambiguous/missing.
    """
    if not (project_path / ".minispec").is_dir():
        console.print("[red]Error:[/red] No .minispec directory found. Is this a MiniSpec project?")
        raise typer.Exit(1)

    # Detect agent by checking AGENT_COMMAND_CONFIG paths
    detected_agents = []
    for agent_key, cmd_config in AGENT_COMMAND_CONFIG.items():
        cmd_path = project_path / cmd_config["path"]
        if cmd_path.is_dir() and any(cmd_path.iterdir()):
            detected_agents.append(agent_key)

    if not detected_agents:
        console.print("[red]Error:[/red] Could not detect AI agent. Use --ai to specify.")
        raise typer.Exit(1)
    if len(detected_agents) > 1:
        agents_str = ", ".join(detected_agents)
        console.print(f"[red]Error:[/red] Multiple agents detected ({agents_str}). Use --ai to specify which one.")
        raise typer.Exit(1)

    # Detect script type
    scripts_dir = project_path / ".minispec" / "scripts"
    detected_script = None
    if (scripts_dir / "bash").is_dir():
        detected_script = "sh"
    elif (scripts_dir / "powershell").is_dir():
        detected_script = "ps"

    if not detected_script:
        console.print("[red]Error:[/red] Could not detect script type. Use --script to specify.")
        raise typer.Exit(1)

    return detected_agents[0], detected_script
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_upgrade.py -v`
Expected: PASS (all 6 tests)

**Step 5: Commit**

```bash
git add src/minispec_cli/__init__.py tests/test_upgrade.py
git commit -m "feat(upgrade): add _detect_project_config helper"
```

---

### Task 2: Add `_classify_upgrade_file()` helper

Classifies each file from the template into one of three tiers: `overwrite`, `merge`, or `prompt`.

**Files:**

- Modify: `src/minispec_cli/__init__.py` (add function after `_detect_project_config`)
- Test: `tests/test_upgrade.py`

**Step 1: Write the failing test**

```python
from minispec_cli import _classify_upgrade_file


class TestClassifyUpgradeFile:
    def test_scripts_are_overwrite(self):
        assert _classify_upgrade_file(".minispec/scripts/bash/common.sh") == "overwrite"
        assert _classify_upgrade_file(".minispec/scripts/powershell/setup-plan.ps1") == "overwrite"

    def test_templates_are_overwrite(self):
        assert _classify_upgrade_file(".minispec/templates/design-template.md") == "overwrite"
        assert _classify_upgrade_file(".minispec/templates/knowledge/module-template.md") == "overwrite"

    def test_hooks_are_overwrite(self):
        assert _classify_upgrade_file(".minispec/hooks/scripts/claude-protect-main.sh") == "overwrite"
        assert _classify_upgrade_file(".minispec/hooks/hooks.yaml") == "overwrite"
        assert _classify_upgrade_file(".minispec/hooks/adapters/claude-code.json") == "overwrite"

    def test_settings_json_are_merge(self):
        assert _classify_upgrade_file(".claude/settings.json") == "merge"
        assert _classify_upgrade_file(".vscode/settings.json") == "merge"

    def test_agent_commands_are_prompt(self):
        assert _classify_upgrade_file(".claude/commands/minispec.design.md") == "prompt"
        assert _classify_upgrade_file(".cursor/commands/minispec.tasks.md") == "prompt"
        assert _classify_upgrade_file(".github/agents/minispec.next.agent.md") == "prompt"

    def test_constitution_is_skip(self):
        assert _classify_upgrade_file(".minispec/memory/constitution.md") == "skip"

    def test_unknown_files_are_overwrite(self):
        assert _classify_upgrade_file("GEMINI.md") == "overwrite"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_upgrade.py::TestClassifyUpgradeFile -v`
Expected: FAIL — `_classify_upgrade_file` not found

**Step 3: Write minimal implementation**

```python
def _classify_upgrade_file(rel_path: str) -> str:
    """Classify a file for upgrade handling.

    Returns one of: 'overwrite', 'merge', 'prompt', 'skip'.
    """
    parts = Path(rel_path).parts

    # Never touch user content
    if rel_path.startswith(".minispec/memory/") or rel_path.startswith("specs/") or rel_path.startswith(".minispec/knowledge/"):
        return "skip"

    # Deep merge JSON config files
    if rel_path.endswith("settings.json") and parts[0] in (".claude", ".vscode"):
        return "merge"

    # Prompt for agent command files (minispec.* pattern)
    for agent_key, cmd_config in AGENT_COMMAND_CONFIG.items():
        cmd_prefix = cmd_config["path"]
        if rel_path.startswith(cmd_prefix + "/") and "minispec." in rel_path:
            return "prompt"

    # Everything else: silent overwrite
    return "overwrite"
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_upgrade.py::TestClassifyUpgradeFile -v`
Expected: PASS (all 7 tests)

**Step 5: Commit**

```bash
git add src/minispec_cli/__init__.py tests/test_upgrade.py
git commit -m "feat(upgrade): add _classify_upgrade_file helper"
```

---

### Task 3: Add `_diff_files()` helper

Generates a colored unified diff between two files for the prompt UX.

**Files:**

- Modify: `src/minispec_cli/__init__.py` (add after `_classify_upgrade_file`)
- Test: `tests/test_upgrade.py`

**Step 1: Write the failing test**

```python
from minispec_cli import _diff_files


class TestDiffFiles:
    def test_identical_files_returns_none(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("hello\nworld\n")
        b.write_text("hello\nworld\n")
        assert _diff_files(a, b) is None

    def test_different_files_returns_diff(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("line1\nline2\n")
        b.write_text("line1\nchanged\n")
        result = _diff_files(a, b)
        assert result is not None
        assert "-line2" in result
        assert "+changed" in result

    def test_new_file_returns_diff(self, tmp_path):
        a = tmp_path / "a.md"  # doesn't exist
        b = tmp_path / "b.md"
        b.write_text("new content\n")
        result = _diff_files(a, b)
        assert result is not None
        assert "+new content" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_upgrade.py::TestDiffFiles -v`
Expected: FAIL — `_diff_files` not found

**Step 3: Write minimal implementation**

```python
import difflib

def _diff_files(existing: Path, new: Path) -> str | None:
    """Generate a unified diff between existing and new file.

    Returns the diff string, or None if files are identical.
    If existing doesn't exist, diffs against empty.
    """
    old_lines = []
    if existing.exists():
        old_lines = existing.read_text(encoding="utf-8").splitlines(keepends=True)

    new_lines = new.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile=str(existing.name) + " (current)",
        tofile=str(existing.name) + " (new)",
        lineterm="",
    ))

    if not diff:
        return None

    return "\n".join(diff)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_upgrade.py::TestDiffFiles -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/minispec_cli/__init__.py tests/test_upgrade.py
git commit -m "feat(upgrade): add _diff_files helper"
```

---

### Task 4: Add `_apply_upgrade()` core logic

Walks the extracted template, classifies each file, and applies the appropriate action. Returns a list of `(rel_path, action)` tuples for the summary.

**Files:**

- Modify: `src/minispec_cli/__init__.py`
- Test: `tests/test_upgrade.py`

**Step 1: Write the failing test**

```python
import json

from minispec_cli import _apply_upgrade


class TestApplyUpgrade:
    def _setup_project(self, tmp_path):
        """Create a minimal existing MiniSpec project."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        (project / ".minispec" / "templates").mkdir(parents=True)
        (project / ".minispec" / "memory").mkdir(parents=True)
        (project / ".minispec" / "memory" / "constitution.md").write_text("my principles")
        (project / ".claude" / "commands").mkdir(parents=True)
        (project / ".claude" / "commands" / "minispec.design.md").write_text("old design prompt")
        (project / ".claude" / "settings.json").write_text(json.dumps({"user_key": True}))
        return project

    def _setup_template(self, tmp_path):
        """Create a minimal extracted template."""
        template = tmp_path / "template"
        template.mkdir()
        (template / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        (template / ".minispec" / "scripts" / "bash" / "common.sh").write_text("#!/bin/bash\n# new")
        (template / ".minispec" / "templates").mkdir(parents=True)
        (template / ".minispec" / "templates" / "design-template.md").write_text("# new template")
        (template / ".minispec" / "memory").mkdir(parents=True)
        (template / ".minispec" / "memory" / "constitution.md").write_text("new constitution")
        (template / ".claude" / "commands").mkdir(parents=True)
        (template / ".claude" / "commands" / "minispec.design.md").write_text("new design prompt")
        (template / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"new": True}}))
        return template

    def test_overwrites_scripts(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        results = _apply_upgrade(project, template, force=True)
        assert (project / ".minispec" / "scripts" / "bash" / "common.sh").read_text() == "#!/bin/bash\n# new"
        assert any(r[1] == "created" for r in results if "common.sh" in r[0])

    def test_preserves_constitution(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        _apply_upgrade(project, template, force=True)
        assert (project / ".minispec" / "memory" / "constitution.md").read_text() == "my principles"

    def test_merges_settings_json(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        _apply_upgrade(project, template, force=True)
        with open(project / ".claude" / "settings.json") as f:
            data = json.load(f)
        assert data["user_key"] is True
        assert data["hooks"]["new"] is True

    def test_force_overwrites_commands(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        results = _apply_upgrade(project, template, force=True)
        assert (project / ".claude" / "commands" / "minispec.design.md").read_text() == "new design prompt"
        assert any(r[1] == "overwritten (auto)" for r in results if "minispec.design.md" in r[0])
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_upgrade.py::TestApplyUpgrade -v`
Expected: FAIL — `_apply_upgrade` not found

**Step 3: Write minimal implementation**

```python
def _apply_upgrade(project_path: Path, template_path: Path, force: bool = False) -> list[tuple[str, str]]:
    """Apply upgrade from extracted template to project.

    Walks template files, classifies each, and applies the appropriate action.
    For 'prompt' files, shows diff and asks unless force=True.

    Returns list of (relative_path, action) tuples.
    """
    results: list[tuple[str, str]] = []

    for source_file in sorted(template_path.rglob("*")):
        if not source_file.is_file():
            continue

        rel_path = str(source_file.relative_to(template_path))
        dest_file = project_path / rel_path
        tier = _classify_upgrade_file(rel_path)

        if tier == "skip":
            results.append((rel_path, "skipped (user content)"))
            continue

        if tier == "merge":
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if dest_file.exists():
                try:
                    with open(source_file, "r", encoding="utf-8") as f:
                        new_content = json.load(f)
                    merged = merge_json_files(dest_file, new_content)
                    with open(dest_file, "w", encoding="utf-8") as f:
                        json.dump(merged, f, indent=4)
                        f.write("\n")
                    results.append((rel_path, "merged"))
                except Exception:
                    shutil.copy2(source_file, dest_file)
                    results.append((rel_path, "overwritten (merge failed)"))
            else:
                shutil.copy2(source_file, dest_file)
                results.append((rel_path, "created"))
            continue

        if tier == "prompt":
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if not dest_file.exists():
                shutil.copy2(source_file, dest_file)
                results.append((rel_path, "created (new)"))
                continue

            diff = _diff_files(dest_file, source_file)
            if diff is None:
                results.append((rel_path, "skipped (unchanged)"))
                continue

            if force:
                shutil.copy2(source_file, dest_file)
                results.append((rel_path, "overwritten (auto)"))
                continue

            # Interactive prompt
            console.print(f"\n[cyan]--- {rel_path} ---[/cyan]")
            console.print(diff)
            accept = typer.confirm("Apply this change?", default=False)
            if accept:
                shutil.copy2(source_file, dest_file)
                results.append((rel_path, "overwritten (accepted)"))
            else:
                results.append((rel_path, "skipped (user declined)"))
            continue

        # tier == "overwrite"
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        is_new = not dest_file.exists()
        shutil.copy2(source_file, dest_file)
        results.append((rel_path, "created" if is_new else "overwritten"))

    return results
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_upgrade.py::TestApplyUpgrade -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add src/minispec_cli/__init__.py tests/test_upgrade.py
git commit -m "feat(upgrade): add _apply_upgrade core logic"
```

---

### Task 5: Wire up the `upgrade` CLI command

The main `upgrade` command that ties detection, download, extraction, apply, and summary together.

**Files:**

- Modify: `src/minispec_cli/__init__.py` (add `upgrade` command after `init` function, around line 1280)

**Step 1: Write the implementation**

```python
@app.command()
def upgrade(
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant (auto-detected if omitted)"),
    script_type: str = typer.Option(None, "--script", help="Script type: sh or ps (auto-detected if omitted)"),
    force: bool = typer.Option(False, "--force", help="Accept all command changes without prompting"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output"),
    github_token: str = typer.Option(None, "--github-token", help="GitHub token for API requests"),
):
    """Upgrade MiniSpec scaffolding to the latest version.

    Updates scripts, templates, hooks, and commands from the latest release
    while preserving your specs, knowledge, constitution, and other user content.

    Agent and script type are auto-detected from your project. Use --ai and
    --script to override if detection fails or you want to switch.

    Command files (minispec.*.md) are diffed and you're prompted before
    overwriting. Use --force to accept all changes automatically.
    """
    project_path = Path.cwd()

    show_banner()

    # Get current version
    current_version = _get_version()
    console.print(f"[dim]Current CLI version: {current_version}[/dim]")
    console.print()

    # Detect or use provided config
    if ai_assistant and ai_assistant not in AGENT_CONFIG:
        console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
        raise typer.Exit(1)
    if script_type and script_type not in SCRIPT_TYPE_CHOICES:
        console.print(f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
        raise typer.Exit(1)

    detected_ai, detected_script = _detect_project_config(project_path)

    selected_ai = ai_assistant or detected_ai
    selected_script = script_type or detected_script

    console.print(f"[cyan]Agent:[/cyan]  {AGENT_CONFIG[selected_ai]['name']}" + (" [dim](detected)[/dim]" if not ai_assistant else ""))
    console.print(f"[cyan]Script:[/cyan] {SCRIPT_TYPE_CHOICES[selected_script]}" + (" [dim](detected)[/dim]" if not script_type else ""))
    console.print()

    # Download template to temp directory
    console.print("[cyan]Downloading latest template...[/cyan]")
    verify = not skip_tls
    local_ssl_context = ssl_context if verify else False
    local_client = httpx.Client(verify=local_ssl_context)

    try:
        with tempfile.TemporaryDirectory() as download_dir:
            zip_path, meta = download_template_from_github(
                selected_ai,
                Path(download_dir),
                script_type=selected_script,
                verbose=False,
                show_progress=False,
                client=local_client,
                debug=debug,
                github_token=github_token,
            )
            console.print(f"[green]Downloaded release {meta['release']}[/green]")

            # Extract to temp location
            with tempfile.TemporaryDirectory() as extract_dir:
                extract_path = Path(extract_dir)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)

                # Flatten if single nested directory
                extracted_items = list(extract_path.iterdir())
                template_root = extract_path
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    template_root = extracted_items[0]

                # Apply upgrade
                console.print("[cyan]Applying upgrade...[/cyan]")
                console.print()
                results = _apply_upgrade(project_path, template_root, force=force)

                # Ensure scripts are executable
                ensure_executable_scripts(project_path)

    except Exception as e:
        console.print(f"[red]Upgrade failed:[/red] {e}")
        if debug:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)

    # Print summary
    console.print()
    table = Table(title="Upgrade Summary")
    table.add_column("File", style="cyan")
    table.add_column("Action")

    action_styles = {
        "created": "[green]created[/green]",
        "created (new)": "[green]created (new)[/green]",
        "overwritten": "[yellow]overwritten[/yellow]",
        "overwritten (auto)": "[yellow]overwritten (auto)[/yellow]",
        "overwritten (accepted)": "[yellow]overwritten (accepted)[/yellow]",
        "overwritten (merge failed)": "[red]overwritten (merge failed)[/red]",
        "merged": "[green]merged[/green]",
        "skipped (unchanged)": "[dim]skipped (unchanged)[/dim]",
        "skipped (user content)": "[dim]skipped (user content)[/dim]",
        "skipped (user declined)": "[blue]skipped (user declined)[/blue]",
    }

    for rel_path, action in results:
        styled_action = action_styles.get(action, action)
        table.add_row(rel_path, styled_action)

    console.print(table)

    counts = {}
    for _, action in results:
        bucket = action.split(" (")[0]  # group by base action
        counts[bucket] = counts.get(bucket, 0) + 1

    parts = [f"{v} {k}" for k, v in sorted(counts.items())]
    console.print(f"\n[green]Upgrade complete.[/green] {', '.join(parts)}.")
```

**Step 2: Test manually**

Run: `minispec upgrade --help`
Expected: Shows help text with all options

**Step 3: Commit**

```bash
git add src/minispec_cli/__init__.py
git commit -m "feat(upgrade): wire up upgrade CLI command"
```

---

### Task 6: Add `difflib` import

**Files:**

- Modify: `src/minispec_cli/__init__.py` (add `import difflib` to existing imports around line 27)

**Step 1: Add the import**

Add `import difflib` after `import subprocess` (line 28).

**Step 2: Verify no import errors**

Run: `uv run python -c "from minispec_cli import _diff_files"`
Expected: No errors

**Step 3: Commit (combine with Task 3 if not yet committed)**

This is a dependency of Task 3. If implementing sequentially, add the import when writing `_diff_files`.

---

### Task 7: Update docs

**Files:**

- Modify: `README.md` (add `upgrade` to commands table)
- Modify: `CLAUDE.md` (add `upgrade` to development commands)

**Step 1: Update README.md commands table**

Add after the `minispec init` / `minispec init --here` rows in the commands table:

```markdown
| `minispec upgrade`        | Upgrade scaffolding to latest release         |
```

**Step 2: Update CLAUDE.md development commands**

Add to the Development Commands section:

```markdown
# Upgrade existing project
minispec upgrade              # auto-detect agent and script type
minispec upgrade --ai claude  # explicit agent
minispec upgrade --force      # accept all command changes
```

**Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: add upgrade command to README and CLAUDE.md"
```

---

### Task 8: Bump version and final commit

**Files:**

- Modify: `pyproject.toml` (bump version)

**Step 1: Bump version**

Change `version = "0.3.0"` to `version = "0.4.0"` in `pyproject.toml`.

**Step 2: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass (existing + new)

**Step 3: Final commit**

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.4.0"
```

**Step 4: Reinstall globally**

Run: `uv tool install -e . --force`
Expected: `minispec 0.4.0`

**Step 5: Push**

```bash
git push
```
