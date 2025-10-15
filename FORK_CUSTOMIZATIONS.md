# Fork Customizations - aloyxa1226/spec-kit

This document tracks all customizations made to this fork of `github/spec-kit`. It serves as a reference for upstream sync operations and helps prevent accidental loss of custom changes.

## Repository Information

- **Parent Repository**: `github/spec-kit`
- **Fork Repository**: `aloyxa1226/spec-kit`
- **Fork Created**: 2025-10-15
- **Purpose**: Custom enhancements and modifications to the Spec-Driven Development workflow

## Last Upstream Sync

- **Date**: Not yet performed (initial fork)
- **Upstream Commit**: [Record SHA on first sync]
- **Conflicts Resolved**: None yet
- **Status**: ✅ Clean fork

## Modified Files

### Documentation Files

#### `.claude/CLAUDE.md`
- **Status**: Added (fork-specific)
- **Reason**: Comprehensive guidance for Claude Code working in this repository
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-15
- **Upstream Conflicts**: None (fork-specific file)
- **Notes**: This file provides architectural overview and fork management guidelines

#### `FORK_CUSTOMIZATIONS.md`
- **Status**: Added (fork-specific)
- **Reason**: Track all fork customizations and sync history
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-15
- **Upstream Conflicts**: None (fork-specific file)
- **Notes**: This file itself

---

## Unmodified Files (Safe to Update from Upstream)

The following files remain unmodified and should be updated directly from upstream during syncs:

### Core Templates
- `templates/spec-template.md`
- `templates/plan-template.md`
- `templates/tasks-template.md`
- `templates/agent-file-template.md`
- `templates/checklist-template.md`

### Command Templates (if unmodified)
- `templates/commands/constitution.md`
- `templates/commands/specify.md`
- `templates/commands/plan.md`
- `templates/commands/tasks.md`
- `templates/commands/implement.md`
- `templates/commands/clarify.md`
- `templates/commands/analyze.md`
- `templates/commands/checklist.md`

### Scripts (if unmodified)
- `scripts/bash/common.sh`
- `scripts/bash/create-new-feature.sh`
- `scripts/bash/setup-plan.sh`
- `scripts/bash/check-prerequisites.sh`
- `scripts/bash/update-agent-context.sh`
- `scripts/powershell/*.ps1`

### CLI Source
- `src/specify_cli/__init__.py`
- `pyproject.toml`

### Documentation
- `README.md`
- `spec-driven.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `docs/*.md`

---

## Planned Customizations

Document planned modifications here before implementing them:

### High Priority
- [ ] None currently planned

### Medium Priority
- [ ] None currently planned

### Low Priority
- [ ] None currently planned

---

## Sync History

### Initial Fork (2025-10-15)
- **Action**: Forked from `github/spec-kit`
- **Upstream Commit**: e2f0f06 (Update installation commands in README)
- **Changes**: Added `.claude/CLAUDE.md` and `FORK_CUSTOMIZATIONS.md`
- **Status**: ✅ Successfully created fork with initial documentation

---

## Merge Conflict Resolution Guidelines

### Automatic Resolution (Keep Ours)
Use `git checkout --ours <file>` for:
- `.claude/CLAUDE.md`
- `FORK_CUSTOMIZATIONS.md`
- Any file explicitly listed as "Keep ours" in Modified Files section

### Automatic Resolution (Keep Theirs)
Use `git checkout --theirs <file>` for:
- Files listed in "Unmodified Files" section
- Security patches and bug fixes
- Core functionality improvements

### Manual Review Required
Carefully merge both changes for:
- Command templates with custom modifications
- Scripts with fork-specific logic additions
- Templates with extended sections
- CLI modifications that need upstream bug fixes

### Priority Rules
1. **Security fixes**: ALWAYS take upstream immediately
2. **Bug fixes**: Prefer upstream, verify doesn't break customizations
3. **New features**: Evaluate compatibility with fork customizations
4. **Documentation**: Merge both (upstream + fork-specific additions)
5. **Custom enhancements**: Keep fork version, cherry-pick useful upstream changes

---

## Testing Checklist After Sync

After each upstream sync, verify:

- [ ] CLI installs correctly: `uvx --from . specify init test-project`
- [ ] All slash commands work: `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`
- [ ] Scripts execute without errors: `bash scripts/bash/check-prerequisites.sh --json`
- [ ] Templates generate correctly: Verify `spec.md`, `plan.md`, `tasks.md` format
- [ ] No merge conflict artifacts remain in files (search for `<<<<<<<`, `=======`, `>>>>>>>`)
- [ ] Custom modifications still present and functional
- [ ] Documentation updated with sync information

---

## Notes

- Always create backup branch before syncing: `git branch backup-fork-main-$(date +%Y%m%d)`
- Test thoroughly in a separate test project before merging to main
- Update this file immediately after each sync with new modifications and resolutions
- Keep commit messages descriptive: `sync: Merge upstream changes (SHA)`
- Document any breaking changes or major differences from upstream

---

## Contact

For questions about these customizations:
- **Repository**: https://github.com/aloyxa1226/spec-kit
- **Parent Repository**: https://github.com/github/spec-kit

---

**Last Updated**: 2025-10-15
