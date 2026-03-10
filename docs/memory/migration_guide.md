# Migration Guide (T085)

## Migrating to SpecKit Memory System

This guide helps you migrate existing projects to use the SpecKit Memory System.

## Scenarios

### Scenario 1: New Project

Easiest - just initialize:

```bash
cd your-new-project
python ~/.claude/spec-kit/scripts/memory/init_memory.py
```

### Scenario 2: Existing Project with CLAUDE.md

You already have `CLAUDE.md` with project notes.

```bash
# 1. Initialize memory
python ~/.claude/spec-kit/scripts/memory/init_memory.py

# 2. Migrate CLAUDE.md content
python ~/.claude/spec-kit/src/specify_cli/memory/install/migrator.py \
  --source ./CLAUDE.md \
  --dest ~/.claude/memory/projects/$(basename $(pwd))
```

The migrator:
- Extracts lessons from "What I learned" sections
- Identifies patterns from "Approach" sections
- Records architecture decisions from "Technical decisions"
- Preserves all content in appropriate files

### Scenario 3: Existing Project with Git History

Extract learnings from commit history:

```bash
python ~/.claude/spec-kit/src/specify_cli/memory/install/migrator.py \
  --source git \
  --analyze-commits 100 \
  --extract-fixes
```

This analyzes:
- Fix commits for lessons
- Refactor commits for patterns
- Large changes for architecture decisions

### Scenario 4: Multiple Projects

Consolidate scattered knowledge:

```bash
# 1. Identify all projects
find ~/projects -name ".git" -type d | while read dir; do
    cd "$(dirname $dir)"
    echo "Processing: $(pwd)"

    # 2. Initialize each project
    python ~/.claude/spec-kit/scripts/memory/init_memory.py

    # 3. Extract git history
    python ~/.claude/spec-kit/src/specify_cli/memory/install/migrator.py \
      --source git --analyze-commits 50
done

# 4. Create cross-project index
python ~/.claude/spec-kit/src/specify_cli/memory/cross_project.py \
  --build-index
```

## Manual Migration

If automated migration doesn't fit your needs:

### Step 1: Review Existing Notes

Gather:
- `CLAUDE.md` or similar notes
- Wiki pages (Confluence, Notion, etc.)
- README sections
- Design documents

### Step 2: Categorize Content

Sort into:

| Content Type | Goes To |
|--------------|----------|
| Mistakes + fixes | lessons.md |
| Reusable solutions | patterns.md |
| Technical decisions | architecture.md |
| Project milestones | projects-log.md |

### Step 3: Use Import Template

```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

memory = MemoryOrchestrator()

# Import lesson
memory.add_lesson(
    title="Error message",
    problem="What went wrong",
    solution="How you fixed it"
)

# Import pattern
memory.add_pattern(
    title="Solution name",
    description="When to use this",
    code="code example"
)

# Import decision
memory.add_architecture(
    title="Decision topic",
    context="Problem/situation",
    decision="What was chosen",
    rationale="Why this choice"
)
```

### Step 4: Verify Import

```bash
# Check imported entries
python -c "
from specify_cli.memory.orchestrator import MemoryOrchestrator
m = MemoryOrchestrator()
print(f'Lessons: {len(m.get_lessons())}')
print(f'Patterns: {len(m.get_patterns())}')
print(f'Architecture: {len(m.get_architecture())}')
"

# Search for specific entries
python ~/.claude/spec-kit/src/specify_cli/memory/ -m orchestrator search "keyword"
```

## Post-Migration

### Clean Up Original Files

After verifying migration success:

```bash
# Archive old notes
mkdir -p .archive
mv CLAUDE.md .archive/
mv NOTES.md .archive/

# Add redirect note to CLAUDE.md
cat > CLAUDE.md << 'EOF'
# Project Memory

Memory has moved to SpecKit Memory System.

View lessons: `~/.claude/memory/projects/$(basename $(pwd))/lessons.md`
View patterns: `~/.claude/memory/projects/$(basename $(pwd))/patterns.md`

Or use CLI:
```bash
cd ~/.claude/spec-kit
python -m specify_cli.memory.orchestrator search "keyword"
```
EOF
```

### Update Team Workflow

1. **Add to onboarding**: Document memory system usage
2. **Update PR template**: Ask for memory updates
3. **Add to standup**: Share recent lessons learned

### Set Up Backups

```bash
# Automatic backups already configured
# Verify backup schedule
crontab -l | grep memory-backup

# Manual backup
cp -r ~/.claude/memory ~/backups/memory-$(date +%Y%m%d)
```

## Verification Checklist

- [ ] All projects initialized
- [ ] Content migrated successfully
- [ ] Search returns expected results
- [ ] Team trained on new system
- [ ] Backups configured
- [ ] Original files archived
- [ ] Documentation updated

## Rollback

If migration has issues:

```bash
# Restore from backup
cp -r ~/backups/memory-YYYYMMDD/* ~/.claude/memory/

# Or re-run migration
rm -rf ~/.claude/memory/projects/your-project
python ~/.claude/spec-kit/scripts/memory/init_memory.py
```

## Troubleshooting

**Migration incomplete?**
```bash
# Check what was imported
python ~/.claude/spec-kit/scripts/memory/verify_install.py

# Re-run specific migration
python ~/.claude/spec-kit/src/specify_cli/memory/install/migrator.py \
  --source ./CLAUDE.md --force
```

**Missing content?**
- Check migrator logs: `~/.claude/memory/logs/migration.log`
- Manually add missing entries
- Report issues to GitHub

**Performance issues?**
- See [Performance Tuning Guide](performance_tuning.md)
- Consider database migration for 10K+ entries

## Need Help?

- Documentation: [README.md](README.md)
- Issues: https://github.com/spec-kit/spec-kit/issues
- Community: https://discord.gg/spec-kit
