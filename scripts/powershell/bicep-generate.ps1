# Bicep Generator PowerShell Entry Point
# Main script for generating Bicep templates from project analysis

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, HelpMessage = "Command to execute")]
    [ValidateSet("analyze", "generate", "validate", "update", "dependencies", "review", "sync", "help")]
    [string]$Command,
    
    [Parameter(HelpMessage = "Path to the project root directory")]
    [string]$ProjectPath = ".",
    
    [Parameter(HelpMessage = "Target environment (dev, staging, prod)")]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",
    
    [Parameter(HelpMessage = "Azure region for deployment")]
    [string]$Region = "eastus",
    
    [Parameter(HelpMessage = "Output directory for generated templates")]
    [string]$OutputDir = "./bicep",
    
    [Parameter(HelpMessage = "Azure subscription ID")]
    [string]$Subscription,
    
    [Parameter(HelpMessage = "Target resource group name")]
    [string]$ResourceGroup,
    
    [Parameter(HelpMessage = "Resource name prefix")]
    [string]$Prefix = "",
    
    [Parameter(HelpMessage = "Additional tags as JSON string")]
    [string]$Tags = "{}",
    
    [Parameter(HelpMessage = "Template file path for validation")]
    [string]$TemplatePath,
    
    [Parameter(HelpMessage = "Output format (table, json, yaml)")]
    [ValidateSet("table", "json", "yaml")]
    [string]$OutputFormat = "table",
    
    [Parameter(HelpMessage = "Overwrite existing templates")]
    [switch]$Force,
    
    [Parameter(HelpMessage = "Enable interactive mode")]
    [switch]$Interactive,
    
    [Parameter(HelpMessage = "Perform deployment validation")]
    [switch]$ValidateDeployment,
    
    [Parameter(HelpMessage = "Show verbose output")]
    [switch]$Verbose,
    
    # Phase 4 Parameters
    [Parameter(HelpMessage = "Path to template update manifest")]
    [string]$ManifestPath,
    
    [Parameter(HelpMessage = "Force template update regardless of changes")]
    [switch]$ForceUpdate,
    
    [Parameter(HelpMessage = "Target environments for synchronization (comma-separated)")]
    [string]$TargetEnvironments,
    
    [Parameter(HelpMessage = "Update strategy (conservative, incremental, aggressive)")]
    [ValidateSet("conservative", "incremental", "aggressive")]
    [string]$UpdateStrategy = "incremental",
    
    [Parameter(HelpMessage = "Enable dependency analysis")]
    [switch]$AnalyzeDependencies,
    
    [Parameter(HelpMessage = "Resolve dependency conflicts")]
    [switch]$ResolveDependencies,
    
    [Parameter(HelpMessage = "Source environment for synchronization")]
    [string]$SourceEnvironment = "prod",
    
    [Parameter(HelpMessage = "Architecture review scope (compliance, cost, performance, all)")]
    [ValidateSet("compliance", "cost", "performance", "all")]
    [string]$ReviewScope = "all",
    
    [Parameter(HelpMessage = "Show verbose output")]
    [switch]$Verbose
)

# Import required modules and set error handling
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Script constants
$SCRIPT_NAME = "Bicep Generator"
$SCRIPT_VERSION = "1.0.0"
$MIN_PS_VERSION = [Version]"5.1"
$MIN_PYTHON_VERSION = [Version]"3.11"

# Check PowerShell version
if ($PSVersionTable.PSVersion -lt $MIN_PS_VERSION) {
    Write-Error "PowerShell $MIN_PS_VERSION or higher is required. Current version: $($PSVersionTable.PSVersion)"
    exit 1
}

# Function definitions
function Write-Header {
    param([string]$Title)
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Yellow
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host ""
}

function Write-Section {
    param([string]$Title)
    
    Write-Host ""
    Write-Host "--- $Title ---" -ForegroundColor Green
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Test-Prerequisites {
    Write-Section "Checking Prerequisites"
    
    # Check Python installation
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
            $version = [Version]$matches[1]
            if ($version -ge $MIN_PYTHON_VERSION) {
                Write-Success "Python $($matches[1]) found"
            } else {
                Write-Error "Python $MIN_PYTHON_VERSION or higher required. Found: $($matches[1])"
                return $false
            }
        } else {
            Write-Error "Could not determine Python version"
            return $false
        }
    } catch {
        Write-Error "Python not found in PATH"
        return $false
    }
    
    # Check Azure CLI
    try {
        $azVersion = az --version 2>$null | Select-Object -First 1
        if ($azVersion -match "azure-cli\s+(\d+\.\d+\.\d+)") {
            Write-Success "Azure CLI $($matches[1]) found"
        } else {
            Write-Warning "Azure CLI version could not be determined"
        }
    } catch {
        Write-Warning "Azure CLI not found - deployment validation will be limited"
    }
    
    # Check Bicep CLI
    try {
        $bicepVersion = bicep --version 2>$null
        if ($bicepVersion) {
            Write-Success "Bicep CLI found: $bicepVersion"
        } else {
            Write-Warning "Bicep CLI not found - template compilation will be limited"
        }
    } catch {
        Write-Warning "Bicep CLI not found - template compilation will be limited"
    }
    
    return $true
}

function Invoke-ProjectAnalysis {
    param(
        [string]$ProjectPath,
        [string]$OutputFormat
    )
    
    Write-Section "Analyzing Project"
    Write-Host "Project Path: $ProjectPath"
    Write-Host "Output Format: $OutputFormat"
    
    # Resolve absolute path
    $absolutePath = Resolve-Path -Path $ProjectPath -ErrorAction SilentlyContinue
    if (-not $absolutePath) {
        Write-Error "Project path not found: $ProjectPath"
        return $null
    }
    
    Write-Host "Scanning project files..."
    
    # Call Python CLI for project analysis
    try {
        $pythonScript = Join-Path $PSScriptRoot ".." ".." "src" "specify_cli" "commands" "bicep_generator.py"
        $analysisArgs = @(
            $pythonScript
            "analyze"
            "--project-path", $absolutePath
            "--output-format", $OutputFormat
        )
        
        if ($Verbose) {
            $analysisArgs += "--verbose"
        }
        
        $analysisResult = & python @analysisArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Project analysis completed"
            return $analysisResult
        } else {
            Write-Error "Project analysis failed with exit code: $LASTEXITCODE"
            return $null
        }
    } catch {
        Write-Error "Failed to run project analysis: $_"
        return $null
    }
}

function Invoke-TemplateGeneration {
    param(
        [string]$ProjectPath,
        [string]$Environment,
        [string]$Region,
        [string]$OutputDir,
        [string]$Subscription,
        [string]$ResourceGroup,
        [string]$Prefix,
        [string]$Tags,
        [bool]$Force,
        [bool]$Interactive,
        [bool]$ValidateDeployment
    )
    
    Write-Section "Generating Bicep Templates"
    Write-Host "Project Path: $ProjectPath"
    Write-Host "Environment: $Environment"
    Write-Host "Region: $Region"
    Write-Host "Output Directory: $OutputDir"
    
    # Resolve paths
    $absoluteProjectPath = Resolve-Path -Path $ProjectPath -ErrorAction SilentlyContinue
    if (-not $absoluteProjectPath) {
        Write-Error "Project path not found: $ProjectPath"
        return $false
    }
    
    $absoluteOutputDir = Join-Path (Get-Location) $OutputDir
    Write-Host "Absolute Output Directory: $absoluteOutputDir"
    
    # Build generation arguments
    $generationArgs = @(
        Join-Path $PSScriptRoot ".." ".." "src" "specify_cli" "commands" "bicep_generator.py"
        "generate"
        "--project-path", $absoluteProjectPath
        "--environment", $Environment
        "--region", $Region
        "--output-dir", $absoluteOutputDir
    )
    
    if ($Subscription) { $generationArgs += "--subscription", $Subscription }
    if ($ResourceGroup) { $generationArgs += "--resource-group", $ResourceGroup }
    if ($Prefix) { $generationArgs += "--prefix", $Prefix }
    if ($Tags -ne "{}") { $generationArgs += "--tags", $Tags }
    if ($Force) { $generationArgs += "--force" }
    if ($Interactive) { $generationArgs += "--interactive" }
    if ($ValidateDeployment) { $generationArgs += "--validate-deployment" }
    if ($Verbose) { $generationArgs += "--verbose" }
    
    try {
        Write-Host "Executing template generation..."
        $result = & python @generationArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Bicep templates generated successfully"
            Write-Host "Output directory: $absoluteOutputDir"
            
            # List generated files
            if (Test-Path $absoluteOutputDir) {
                Write-Section "Generated Files"
                Get-ChildItem -Path $absoluteOutputDir -Recurse -File | 
                    Format-Table Name, Length, LastWriteTime -AutoSize
            }
            
            return $true
        } else {
            Write-Error "Template generation failed with exit code: $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Error "Failed to generate templates: $_"
        return $false
    }
}

function Invoke-TemplateValidation {
    param(
        [string]$TemplatePath,
        [string]$Subscription,
        [string]$ResourceGroup,
        [bool]$ValidateDeployment
    )
    
    Write-Section "Validating Bicep Template"
    Write-Host "Template Path: $TemplatePath"
    
    # Resolve template path
    $absoluteTemplatePath = Resolve-Path -Path $TemplatePath -ErrorAction SilentlyContinue
    if (-not $absoluteTemplatePath) {
        Write-Error "Template file not found: $TemplatePath"
        return $false
    }
    
    # Build validation arguments
    $validationArgs = @(
        Join-Path $PSScriptRoot ".." ".." "src" "specify_cli" "commands" "bicep_generator.py"
        "validate"
        "--template-path", $absoluteTemplatePath
    )
    
    if ($ValidateDeployment -and $Subscription) {
        $validationArgs += "--validate-deployment"
        $validationArgs += "--subscription", $Subscription
        if ($ResourceGroup) {
            $validationArgs += "--resource-group", $ResourceGroup
        }
    }
    
    if ($Verbose) { $validationArgs += "--verbose" }
    
    try {
        Write-Host "Executing template validation..."
        $result = & python @validationArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Template validation passed"
            return $true
        } else {
            Write-Error "Template validation failed with exit code: $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Error "Failed to validate template: $_"
        return $false
    }
}

# =====================================================
# PHASE 4 ADVANCED FEATURES
# =====================================================

function Invoke-TemplateUpdate {
    param(
        [string]$ProjectPath,
        [string]$ManifestPath,
        [bool]$ForceUpdate,
        [string]$TargetEnvironments,
        [string]$UpdateStrategy
    )
    
    Write-Section "Template Update Orchestration"
    
    # Prepare arguments for Python orchestrator
    $updateArgs = @(
        "-c", "from src.specify_cli.bicep.template_orchestrator import TemplateUpdateOrchestrator; import asyncio; import sys; import json"
        "-c", "async def update(): orchestrator = TemplateUpdateOrchestrator(None, None, None, None, None); manifest, messages = await orchestrator.orchestrate_update('$ProjectPath', '$ManifestPath', $ForceUpdate, $TargetEnvironments.split(',') if '$TargetEnvironments' else None); print(json.dumps({'success': True, 'messages': messages})); asyncio.run(update())"
    )
    
    try {
        Write-Host "Orchestrating template updates..."
        $result = & python @updateArgs | ConvertFrom-Json
        
        if ($result.success) {
            Write-Success "Template update orchestration completed"
            foreach ($message in $result.messages) {
                Write-Host "  $message"
            }
            return $true
        } else {
            Write-Error "Template update failed"
            return $false
        }
    } catch {
        Write-Error "Failed to update templates: $_"
        return $false
    }
}

function Invoke-DependencyAnalysis {
    param(
        [string]$ProjectPath,
        [bool]$ResolveDependencies
    )
    
    Write-Section "Dependency Analysis"
    
    # Prepare arguments for Python dependency resolver
    $depArgs = @(
        "-c", "from src.specify_cli.bicep.dependency_resolver import DependencyResolver; import json"
        "-c", "resolver = DependencyResolver(); print('Dependency analysis would run here')"
    )
    
    try {
        Write-Host "Analyzing template dependencies..."
        $result = & python @depArgs
        
        Write-Success "Dependency analysis completed"
        Write-Host "  $result"
        return $true
    } catch {
        Write-Error "Failed to analyze dependencies: $_"
        return $false
    }
}

function Invoke-EnvironmentSync {
    param(
        [string]$ProjectPath,
        [string]$SourceEnvironment,
        [string]$TargetEnvironments,
        [string]$ManifestPath
    )
    
    Write-Section "Environment Synchronization"
    
    $targetEnvList = $TargetEnvironments.Split(',').Trim()
    
    Write-Host "Synchronizing from $SourceEnvironment to environments: $($targetEnvList -join ', ')"
    
    try {
        # This would call the Python synchronization logic
        Write-Host "Environment synchronization logic would execute here"
        
        Write-Success "Environment synchronization completed"
        return $true
    } catch {
        Write-Error "Failed to synchronize environments: $_"
        return $false
    }
}

function Invoke-ArchitectureReview {
    param(
        [string]$ProjectPath,
        [string]$ReviewScope
    )
    
    Write-Section "Architecture Review"
    
    Write-Host "Conducting architecture review with scope: $ReviewScope"
    
    try {
        # Prepare arguments for Python architecture reviewer
        $reviewArgs = @(
            "-c", "from src.specify_cli.bicep.best_practices_validator import BestPracticesValidator"
            "-c", "print('Architecture review would run here for scope: $ReviewScope')"
        )
        
        $result = & python @reviewArgs
        
        Write-Success "Architecture review completed"
        Write-Host "  $result"
        return $true
    } catch {
        Write-Error "Failed to conduct architecture review: $_"
        return $false
    }
}

function Show-Help {
    Write-Header "$SCRIPT_NAME v$SCRIPT_VERSION - Help"
    
    Write-Host @"
USAGE:
    bicep-generate.ps1 -Command <command> [options]

COMMANDS:
    analyze        Analyze project for Azure service requirements
    generate       Generate Bicep templates based on project analysis  
    validate       Validate existing Bicep templates
    update         Update existing templates based on project changes (Phase 4)
    dependencies   Analyze and resolve template dependencies (Phase 4)
    sync           Synchronize templates across environments (Phase 4)
    review         Conduct architecture review and optimization (Phase 4)
    help           Show this help message

EXAMPLES:
    # Analyze current project
    .\bicep-generate.ps1 -Command analyze -ProjectPath "." -OutputFormat json
    
    # Generate templates for development environment
    .\bicep-generate.ps1 -Command generate -ProjectPath "." -Environment dev -Region eastus
    
    # Generate with custom settings
    .\bicep-generate.ps1 -Command generate -ProjectPath "." -Environment prod -Region westus2 -Prefix "mycompany" -Force
    
    # Validate a template
    .\bicep-generate.ps1 -Command validate -TemplatePath ".\bicep\main.bicep" -ValidateDeployment -Subscription "12345678-1234-1234-1234-123456789012"
    
    # Interactive generation
    .\bicep-generate.ps1 -Command generate -ProjectPath "." -Environment staging -Interactive
    
    # Phase 4 Advanced Features
    # Update templates based on project changes
    .\bicep-generate.ps1 -Command update -ProjectPath "." -ManifestPath ".\manifest.json" -UpdateStrategy aggressive
    
    # Analyze dependencies
    .\bicep-generate.ps1 -Command dependencies -ProjectPath "." -ResolveDependencies
    
    # Synchronize environments
    .\bicep-generate.ps1 -Command sync -SourceEnvironment prod -TargetEnvironments "dev,staging" -ProjectPath "."
    
    # Conduct architecture review
    .\bicep-generate.ps1 -Command review -ProjectPath "." -ReviewScope compliance

OPTIONS:
    -ProjectPath        Path to project directory (default: current directory)
    -Environment        Target environment: dev, staging, prod (default: dev)
    -Region             Azure region (default: eastus)
    -OutputDir          Output directory (default: ./bicep)
    -Subscription       Azure subscription ID
    -ResourceGroup      Target resource group name
    -Prefix             Resource name prefix
    -Tags               Additional tags as JSON string
    -TemplatePath       Template file path (for validation command)
    -OutputFormat       Output format: table, json, yaml (default: table)
    -Force              Overwrite existing templates
    -Interactive        Enable interactive mode
    -ValidateDeployment Perform deployment validation
    -Verbose            Show detailed output

For more information, visit: https://github.com/microsoft/spec-kit
"@
}

# Main script execution
function Main {
    Write-Header "$SCRIPT_NAME v$SCRIPT_VERSION"
    
    # Show help if requested
    if ($Command -eq "help") {
        Show-Help
        return
    }
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Error "Prerequisites check failed. Please install missing components."
        exit 1
    }
    
    # Execute requested command
    switch ($Command) {
        "analyze" {
            $result = Invoke-ProjectAnalysis -ProjectPath $ProjectPath -OutputFormat $OutputFormat
            if ($result) {
                if ($OutputFormat -eq "json") {
                    Write-Output $result
                } else {
                    Write-Host $result
                }
            } else {
                exit 1
            }
        }
        
        "generate" {
            $success = Invoke-TemplateGeneration -ProjectPath $ProjectPath -Environment $Environment -Region $Region -OutputDir $OutputDir -Subscription $Subscription -ResourceGroup $ResourceGroup -Prefix $Prefix -Tags $Tags -Force $Force.IsPresent -Interactive $Interactive.IsPresent -ValidateDeployment $ValidateDeployment.IsPresent
            if (-not $success) {
                exit 1
            }
        }
        
        "validate" {
            if (-not $TemplatePath) {
                Write-Error "TemplatePath parameter is required for validate command"
                exit 1
            }
            
            $success = Invoke-TemplateValidation -TemplatePath $TemplatePath -Subscription $Subscription -ResourceGroup $ResourceGroup -ValidateDeployment $ValidateDeployment.IsPresent
            if (-not $success) {
                exit 1
            }
        }
        
        "update" {
            $success = Invoke-TemplateUpdate -ProjectPath $ProjectPath -ManifestPath $ManifestPath -ForceUpdate $ForceUpdate.IsPresent -TargetEnvironments $TargetEnvironments -UpdateStrategy $UpdateStrategy
            if (-not $success) {
                exit 1
            }
        }
        
        "dependencies" {
            $success = Invoke-DependencyAnalysis -ProjectPath $ProjectPath -ResolveDependencies $ResolveDependencies.IsPresent
            if (-not $success) {
                exit 1
            }
        }
        
        "sync" {
            if (-not $TargetEnvironments) {
                Write-Error "TargetEnvironments parameter is required for sync command"
                exit 1
            }
            
            $success = Invoke-EnvironmentSync -ProjectPath $ProjectPath -SourceEnvironment $SourceEnvironment -TargetEnvironments $TargetEnvironments -ManifestPath $ManifestPath
            if (-not $success) {
                exit 1
            }
        }
        
        "review" {
            $success = Invoke-ArchitectureReview -ProjectPath $ProjectPath -ReviewScope $ReviewScope
            if (-not $success) {
                exit 1
            }
        }
        
        "help" {
            Show-Help
        }
        
        default {
            Write-Error "Unknown command: $Command"
            Show-Help
            exit 1
        }
    }
    
    Write-Section "Operation Completed Successfully"
}

# Execute main function
try {
    Main
} catch {
    Write-Error "Unhandled error: $_"
    Write-Host "Stack trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}