# Component: workflow launcher; target: developer workstation; task: fork workflow.
# Windows PowerShell 5.1. Arguments are forwarded as an array, never shell source.
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $OutputEncoding
if ($args.Count -lt 1 -or $args[0] -notin @('context', 'progress')) {
    [Console]::Error.WriteLine('Usage: workflow.ps1 context STAGE | progress ACTION [options]')
    exit 1
}
$helper = if ($args[0] -eq 'context') { 'workflow_context.py' } else { 'code_progress.py' }
$forward = @()
if ($args.Count -gt 1) { $forward = @($args[1..($args.Count - 1)]) }
$override = if ($env:SPECKIT_PYTHON_EXECUTABLE) { $env:SPECKIT_PYTHON_EXECUTABLE } else { $env:SPECKIT_PYTHON }
$candidates = @($override, (Join-Path $PSScriptRoot '../../../.venv/Scripts/python.exe'), 'python', 'python3')
foreach ($executable in $candidates) {
    if (-not $executable -or -not (Get-Command $executable -ErrorAction SilentlyContinue)) { continue }
    & $executable -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' 2>$null
    if ($LASTEXITCODE -ne 0) { continue }
    & $executable (Join-Path $PSScriptRoot "../python/$helper") @forward
    exit $LASTEXITCODE
}
[Console]::Error.WriteLine('ERROR: Python 3.11+ is required; set SPECKIT_PYTHON_EXECUTABLE to its executable.')
exit 1
