# PowerShell Requirements for Archon Integration

## Minimum Version

- **PowerShell 7.0 or later** (required)
- **Why**: Uses modern syntax like `2>$null`, native JSON handling, cross-platform paths, and improved error handling

## Installation

### Windows
PowerShell 7+ is not pre-installed on Windows. Download and install from:
- [Microsoft PowerShell Releases](https://github.com/PowerShell/PowerShell/releases)
- Or via winget: `winget install Microsoft.PowerShell`

### macOS
```bash
brew install powershell
```

### Linux
See official installation guide:
- [Installing PowerShell on Linux](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-linux)

**Ubuntu/Debian:**
```bash
# Download the Microsoft repository GPG keys
wget -q https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb

# Register the Microsoft repository GPG keys
sudo dpkg -i packages-microsoft-prod.deb

# Update the list of packages after adding packages.microsoft.com
sudo apt-get update

# Install PowerShell
sudo apt-get install -y powershell

# Start PowerShell
pwsh
```

## Verification

Check your PowerShell version:

```powershell
$PSVersionTable.PSVersion
```

**Expected output:**
```
Major  Minor  Patch  PreReleaseLabel BuildLabel
-----  -----  -----  --------------- ----------
7      4      1
```

The major version should be **7 or higher**.

## Script Locations

All Archon MCP integration scripts are located in:
```
scripts/powershell/
├── archon-common.ps1            # Core utilities (silent)
├── archon-auto-init.ps1         # Project initialization
├── archon-sync-documents.ps1    # Document synchronization
├── archon-auto-sync-tasks.ps1   # Task synchronization
├── archon-auto-pull-status.ps1  # Status synchronization
└── archon-daemon.ps1            # Background sync daemon (advanced)
```

## Known Limitations

### State File Location
- State files are stored in: `scripts/powershell/.archon-state/`
- All scripts must have read/write permissions to this directory
- State directory is relative to `archon-common.ps1` location

### Error Handling
- Daemon script uses `ErrorActionPreference = 'Stop'` (different from other scripts which use `'SilentlyContinue'`)
- All errors are silently suppressed to maintain zero-output requirement
- Failed operations return `$false` but don't display error messages

### File Permissions
- Scripts require write permissions in `scripts/powershell/` directory
- Temporary files (`.tmp` suffix) are created during atomic writes
- Ensure sufficient disk space for state file operations

### Cross-Platform Considerations
- Path separators are handled automatically by PowerShell 7+
- `Join-Path` works correctly on all platforms
- `$PSCommandPath` behaves consistently across Windows/macOS/Linux

## Troubleshooting

### Scripts fail silently

**Symptoms**: No output, no state files created, no errors displayed

**Solutions**:
1. Check PowerShell version: `$PSVersionTable.PSVersion` (must be 7.0+)
2. Verify state directory permissions:
   ```powershell
   Test-Path "scripts/powershell/.archon-state" -PathType Container
   ```
3. Check disk space: `Get-PSDrive`
4. Try creating a test file:
   ```powershell
   "test" | Out-File "scripts/powershell/.archon-state/test.txt"
   ```

### Import errors (archon-common.ps1 not found)

**Symptoms**: Functions like `Test-ArchonAvailable`, `Get-FeatureName` not recognized

**Solutions**:
1. Ensure `archon-common.ps1` exists in `scripts/powershell/`
2. Check that all scripts use correct import path:
   ```powershell
   . (Join-Path $scriptDir "archon-common.ps1")
   ```
3. Verify `$scriptDir` points to the correct directory

### Corrupted JSON state files

**Symptoms**: State files are empty, contain partial JSON, or cause parse errors

**Solutions**:
1. **Prevention**: All Save functions now use atomic writes (temp file + move)
2. **Recovery**: Delete corrupted state files and re-run initialization:
   ```powershell
   Remove-Item "scripts/powershell/.archon-state/*.pid" -Force
   Remove-Item "scripts/powershell/.archon-state/*.docs" -Force
   Remove-Item "scripts/powershell/.archon-state/*.tasks" -Force
   Remove-Item "scripts/powershell/.archon-state/*.meta" -Force
   ```
3. Check file system health if corruption persists

### Daemon won't start or stops immediately

**Symptoms**: PID file not created, or daemon exits without error

**Solutions**:
1. Check minimum sync interval (must be ≥ 60 seconds)
2. Verify feature directory exists and is accessible
3. Ensure Archon MCP is available (Claude Code running)
4. Check for existing daemon process:
   ```powershell
   Get-Content "scripts/powershell/.archon-state/<feature>.daemon.pid"
   Get-Process -Id <pid>
   ```
5. Kill stale daemon if needed:
   ```powershell
   Stop-Process -Id <pid> -Force
   Remove-Item "scripts/powershell/.archon-state/<feature>.daemon.pid"
   ```

## Advanced Usage

### Background Sync Daemon (Optional)

The daemon is **NOT started automatically** and is intended for advanced users only.

**Start daemon:**
```powershell
pwsh scripts/powershell/archon-daemon.ps1 /path/to/specs/001-feature 300
```

**Parameters:**
- Argument 1: Feature directory path (required)
- Argument 2: Sync interval in seconds (default: 300, minimum: 60)

**Stop daemon:**
```powershell
# Find PID
$pid = Get-Content "scripts/powershell/.archon-state/001-feature.daemon.pid"

# Kill process
Stop-Process -Id $pid -Force

# Cleanup PID file
Remove-Item "scripts/powershell/.archon-state/001-feature.daemon.pid"
```

## Development and Testing

### Running Scripts Manually

All scripts accept feature directory as first argument:

```powershell
# Initialize project
pwsh scripts/powershell/archon-auto-init.ps1 /path/to/specs/001-feature

# Sync documents (pull)
pwsh scripts/powershell/archon-sync-documents.ps1 /path/to/specs/001-feature pull

# Sync documents (push)
pwsh scripts/powershell/archon-sync-documents.ps1 /path/to/specs/001-feature push

# Sync tasks
pwsh scripts/powershell/archon-auto-sync-tasks.ps1 /path/to/specs/001-feature

# Pull status updates
pwsh scripts/powershell/archon-auto-pull-status.ps1 /path/to/specs/001-feature
```

### Debugging

Enable error output temporarily (for debugging only):

```powershell
# Modify ErrorActionPreference at top of script
$ErrorActionPreference = 'Continue'  # Instead of 'SilentlyContinue'
```

**Remember**: Revert to `'SilentlyContinue'` before committing to maintain silent operation.

### State File Inspection

View current state mappings:

```powershell
# Project ID
Get-Content "scripts/powershell/.archon-state/001-feature.pid"

# Document mappings
Get-Content "scripts/powershell/.archon-state/001-feature.docs"

# Task mappings
Get-Content "scripts/powershell/.archon-state/001-feature.tasks"

# Sync metadata
Get-Content "scripts/powershell/.archon-state/001-feature.meta"
```

## Security Considerations

### State Files Contain Sensitive Data

State files may contain:
- Archon project IDs (UUIDs)
- Document IDs (UUIDs)
- Task IDs (UUIDs)
- Sync timestamps

**Recommendations**:
1. Add `.archon-state/` to `.gitignore` (already done in fork)
2. Do not commit state files to version control
3. Backup state files if needed for disaster recovery
4. Restrict file permissions on multi-user systems:
   ```powershell
   # Unix-like systems only
   chmod 700 scripts/powershell/.archon-state
   ```

## FAQ

**Q: Can I use PowerShell 5.1 (Windows PowerShell)?**
A: No. PowerShell 7+ is required for cross-platform compatibility and modern syntax.

**Q: Why are all scripts silent?**
A: Archon integration is designed to be completely transparent to users. Scripts run in the background without user interaction.

**Q: What happens if MCP is not available?**
A: Scripts detect MCP availability and exit gracefully (status 0) if unavailable. No errors are thrown.

**Q: Can I run multiple daemons for different features?**
A: Yes, but each feature needs its own daemon process. PID files prevent duplicate daemons for the same feature.

**Q: How do I disable Archon integration?**
A: Archon integration is MCP-gated. If Claude Code is not running or Archon MCP server is unavailable, integration is automatically disabled.

## Support

For issues related to PowerShell Archon integration:
1. Check this documentation first
2. Review error logs (enable debugging temporarily)
3. Verify PowerShell version and file permissions
4. Open an issue in the repository with:
   - PowerShell version (`$PSVersionTable.PSVersion`)
   - Operating system
   - State directory contents
   - Steps to reproduce

---

**Last Updated**: 2025-10-16
**Minimum PowerShell Version**: 7.0
**Status**: Production-ready after critical fixes applied
