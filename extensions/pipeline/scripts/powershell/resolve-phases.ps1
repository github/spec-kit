# Thin PowerShell wrapper: resolve the Spec Kit pipeline phase plan.
# Delegates to the pure-Python resolver so there is one source of truth.
# Usage: resolve-phases.ps1 [--skip a,b] [--add x,y] [--json|--list]
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$resolver = Join-Path $here "..\resolve_phases.py"
python3 $resolver @args
exit $LASTEXITCODE
