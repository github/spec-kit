# Bicep Template Validation PowerShell Script
# Validates Bicep templates using Azure CLI and schema validation

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, HelpMessage = "Path to Bicep template or directory")]
    [string]$TemplatePath,
    
    [Parameter(HelpMessage = "Azure subscription ID for deployment validation")]
    [string]$Subscription,
    
    [Parameter(HelpMessage = "Resource group name for deployment validation")]
    [string]$ResourceGroup,
    
    [Parameter(HelpMessage = "Validation mode: syntax, schema, deployment, all")]
    [ValidateSet("syntax", "schema", "deployment", "all")]
    [string]$ValidationMode = "all",
    
    [Parameter(HelpMessage = "Output format: table, json, detailed")]
    [ValidateSet("table", "json", "detailed")]
    [string]$OutputFormat = "table",
    
    [Parameter(HelpMessage = "Stop on first error")]
    [switch]$StopOnFirstError,
    
    [Parameter(HelpMessage = "Perform what-if deployment analysis")]
    [switch]$WhatIf,
    
    [Parameter(HelpMessage = "Show verbose output")]
    [switch]$Verbose
)

# Set error handling
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Script constants
$SCRIPT_NAME = "Bicep Template Validator"
$SCRIPT_VERSION = "1.0.0"

# Validation result structure
class ValidationResult {
    [string]$TemplateName
    [string]$TemplatePath
    [bool]$IsValid
    [string[]]$Errors
    [string[]]$Warnings
    [string[]]$Info
    [hashtable]$Metadata
    
    ValidationResult([string]$name, [string]$path) {
        $this.TemplateName = $name
        $this.TemplatePath = $path
        $this.IsValid = $true
        $this.Errors = @()
        $this.Warnings = @()
        $this.Info = @()
        $this.Metadata = @{}
    }
    
    [void]AddError([string]$message) {
        $this.Errors += $message
        $this.IsValid = $false
    }
    
    [void]AddWarning([string]$message) {
        $this.Warnings += $message
    }
    
    [void]AddInfo([string]$message) {
        $this.Info += $message
    }
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
    
    $allGood = $true
    
    # Check Azure CLI
    try {
        $azVersion = az --version 2>$null | Select-Object -First 1
        if ($azVersion -match "azure-cli\s+(\d+\.\d+\.\d+)") {
            Write-Success "Azure CLI $($matches[1]) found"
        } else {
            Write-Error "Azure CLI not found or version could not be determined"
            $allGood = $false
        }
    } catch {
        Write-Error "Azure CLI not found in PATH"
        $allGood = $false
    }
    
    # Check Bicep CLI
    try {
        $bicepVersion = bicep --version 2>$null
        if ($bicepVersion) {
            Write-Success "Bicep CLI found: $bicepVersion"
        } else {
            Write-Error "Bicep CLI not found"
            $allGood = $false
        }
    } catch {
        Write-Error "Bicep CLI not found in PATH"
        $allGood = $false
    }
    
    # Check Azure authentication (if subscription provided)
    if ($Subscription) {
        try {
            $account = az account show --subscription $Subscription --output json 2>$null | ConvertFrom-Json
            if ($account) {
                Write-Success "Azure authentication verified for subscription: $($account.name)"
            } else {
                Write-Warning "Could not verify Azure authentication for subscription: $Subscription"
            }
        } catch {
            Write-Warning "Azure authentication check failed. Use 'az login' to authenticate."
        }
    }
    
    return $allGood
}

function Get-BicepTemplates {
    param([string]$Path)
    
    $templates = @()
    
    if (Test-Path $Path -PathType Leaf) {
        # Single file
        if ($Path.EndsWith('.bicep')) {
            $templates += Get-Item $Path
        } else {
            Write-Error "File is not a Bicep template: $Path"
        }
    } elseif (Test-Path $Path -PathType Container) {
        # Directory - find all .bicep files
        $bicepFiles = Get-ChildItem -Path $Path -Filter "*.bicep" -Recurse
        $templates += $bicepFiles
        
        if ($bicepFiles.Count -eq 0) {
            Write-Warning "No Bicep templates found in directory: $Path"
        }
    } else {
        Write-Error "Path not found: $Path"
    }
    
    return $templates
}

function Test-BicepSyntax {
    param(
        [string]$TemplatePath,
        [ValidationResult]$Result
    )
    
    Write-Host "  Checking syntax..." -NoNewline
    
    try {
        # Use bicep build to check syntax
        $buildOutput = bicep build $TemplatePath --stdout 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✅" -ForegroundColor Green
            $Result.AddInfo("Syntax validation passed")
            return $true
        } else {
            Write-Host " ❌" -ForegroundColor Red
            
            # Parse error messages
            $errorLines = $buildOutput -split "`n" | Where-Object { $_ -match "Error|Warning" }
            foreach ($errorLine in $errorLines) {
                if ($errorLine -match "Error") {
                    $Result.AddError("Syntax error: $errorLine")
                } elseif ($errorLine -match "Warning") {
                    $Result.AddWarning("Syntax warning: $errorLine")
                }
            }
            
            return $false
        }
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        $Result.AddError("Syntax validation failed: $_")
        return $false
    }
}

function Test-BicepSchema {
    param(
        [string]$TemplatePath,
        [ValidationResult]$Result
    )
    
    Write-Host "  Checking schema..." -NoNewline
    
    try {
        # Read template content for analysis
        $content = Get-Content -Path $TemplatePath -Raw
        
        # Check for common schema issues
        $schemaIssues = @()
        
        # Check for required resource properties
        $resourceBlocks = [regex]::Matches($content, "resource\s+\w+\s+'([^']+)'")
        foreach ($match in $resourceBlocks) {
            $resourceType = $match.Groups[1].Value
            $Result.AddInfo("Found resource type: $resourceType")
        }
        
        # Check for parameter definitions without descriptions
        $paramBlocks = [regex]::Matches($content, "param\s+(\w+)")
        $descriptionBlocks = [regex]::Matches($content, "@description\(")
        
        if ($paramBlocks.Count -gt 0 -and $descriptionBlocks.Count -eq 0) {
            $Result.AddWarning("Parameters found without @description decorators")
        }
        
        # Check for output definitions
        $outputBlocks = [regex]::Matches($content, "output\s+(\w+)")
        if ($outputBlocks.Count -gt 0) {
            $Result.AddInfo("Template defines $($outputBlocks.Count) output(s)")
        }
        
        Write-Host " ✅" -ForegroundColor Green
        $Result.AddInfo("Schema validation completed")
        return $true
        
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        $Result.AddError("Schema validation failed: $_")
        return $false
    }
}

function Test-BicepDeployment {
    param(
        [string]$TemplatePath,
        [string]$Subscription,
        [string]$ResourceGroup,
        [bool]$WhatIf,
        [ValidationResult]$Result
    )
    
    if (-not $Subscription) {
        $Result.AddWarning("Deployment validation skipped - no subscription provided")
        return $true
    }
    
    Write-Host "  Checking deployment..." -NoNewline
    
    try {
        # Build deployment command
        $deployArgs = @(
            "deployment", "group"
        )
        
        if ($WhatIf) {
            $deployArgs += "what-if"
        } else {
            $deployArgs += "validate"
        }
        
        $deployArgs += @(
            "--resource-group", $ResourceGroup
            "--template-file", $TemplatePath
            "--subscription", $Subscription
        )
        
        # Check for parameter file
        $paramFile = $TemplatePath -replace '\.bicep$', '.parameters.json'
        if (Test-Path $paramFile) {
            $deployArgs += "--parameters", $paramFile
            $Result.AddInfo("Using parameter file: $paramFile")
        } else {
            # Look for bicepparam file
            $bicepParamFile = $TemplatePath -replace '\.bicep$', '.bicepparam'
            if (Test-Path $bicepParamFile) {
                $deployArgs += "--parameters", $bicepParamFile
                $Result.AddInfo("Using Bicep parameter file: $bicepParamFile")
            }
        }
        
        # Execute validation
        $deployOutput = az @deployArgs --output json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✅" -ForegroundColor Green
            
            if ($WhatIf) {
                $Result.AddInfo("What-if analysis completed successfully")
                
                # Parse what-if output for insights
                try {
                    $whatIfResult = $deployOutput | ConvertFrom-Json
                    if ($whatIfResult.changes) {
                        $changeCount = $whatIfResult.changes.Count
                        $Result.AddInfo("What-if analysis shows $changeCount potential change(s)")
                    }
                } catch {
                    $Result.AddInfo("What-if analysis completed (output parsing failed)")
                }
            } else {
                $Result.AddInfo("Deployment validation passed")
            }
            
            return $true
        } else {
            Write-Host " ❌" -ForegroundColor Red
            
            # Parse deployment errors
            $errorLines = $deployOutput -split "`n" | Where-Object { $_ -match "ERROR|Error" }
            if ($errorLines.Count -gt 0) {
                foreach ($errorLine in $errorLines) {
                    $Result.AddError("Deployment error: $errorLine")
                }
            } else {
                $Result.AddError("Deployment validation failed (see output above)")
            }
            
            return $false
        }
        
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        $Result.AddError("Deployment validation failed: $_")
        return $false
    }
}

function Invoke-TemplateValidation {
    param(
        [System.IO.FileInfo]$Template,
        [string]$ValidationMode,
        [string]$Subscription,
        [string]$ResourceGroup,
        [bool]$WhatIf,
        [bool]$StopOnFirstError
    )
    
    $result = [ValidationResult]::new($Template.Name, $Template.FullName)
    
    Write-Host ""
    Write-Host "Validating: $($Template.Name)" -ForegroundColor Yellow
    Write-Host "Path: $($Template.FullName)"
    
    # Add template metadata
    $result.Metadata["Size"] = $Template.Length
    $result.Metadata["LastModified"] = $Template.LastWriteTime
    
    # Perform validations based on mode
    $validationPassed = $true
    
    if ($ValidationMode -in @("syntax", "all")) {
        $syntaxResult = Test-BicepSyntax -TemplatePath $Template.FullName -Result $result
        if (-not $syntaxResult -and $StopOnFirstError) {
            return $result
        }
        $validationPassed = $validationPassed -and $syntaxResult
    }
    
    if ($ValidationMode -in @("schema", "all")) {
        $schemaResult = Test-BicepSchema -TemplatePath $Template.FullName -Result $result
        if (-not $schemaResult -and $StopOnFirstError) {
            return $result
        }
        $validationPassed = $validationPassed -and $schemaResult
    }
    
    if ($ValidationMode -in @("deployment", "all")) {
        $deploymentResult = Test-BicepDeployment -TemplatePath $Template.FullName -Subscription $Subscription -ResourceGroup $ResourceGroup -WhatIf $WhatIf -Result $result
        if (-not $deploymentResult -and $StopOnFirstError) {
            return $result
        }
        $validationPassed = $validationPassed -and $deploymentResult
    }
    
    # Update final validation status
    if (-not $validationPassed) {
        $result.IsValid = $false
    }
    
    # Summary
    if ($result.IsValid) {
        Write-Success "Validation passed"
    } else {
        Write-Error "Validation failed with $($result.Errors.Count) error(s)"
    }
    
    return $result
}

function Format-ValidationResults {
    param(
        [ValidationResult[]]$Results,
        [string]$OutputFormat
    )
    
    switch ($OutputFormat) {
        "json" {
            $jsonResults = $Results | ForEach-Object {
                @{
                    TemplateName = $_.TemplateName
                    TemplatePath = $_.TemplatePath
                    IsValid = $_.IsValid
                    Errors = $_.Errors
                    Warnings = $_.Warnings
                    Info = $_.Info
                    Metadata = $_.Metadata
                }
            }
            return ($jsonResults | ConvertTo-Json -Depth 10)
        }
        
        "table" {
            Write-Host ""
            Write-Section "Validation Summary"
            
            $Results | ForEach-Object {
                $status = if ($_.IsValid) { "✅ PASSED" } else { "❌ FAILED" }
                $errorCount = $_.Errors.Count
                $warningCount = $_.Warnings.Count
                
                Write-Host "$status $($_.TemplateName) " -NoNewline
                if ($errorCount -gt 0) {
                    Write-Host "($errorCount errors)" -ForegroundColor Red -NoNewline
                }
                if ($warningCount -gt 0) {
                    Write-Host " ($warningCount warnings)" -ForegroundColor Yellow -NoNewline
                }
                Write-Host ""
            }
        }
        
        "detailed" {
            Write-Host ""
            Write-Section "Detailed Validation Results"
            
            foreach ($result in $Results) {
                Write-Host ""
                Write-Host "Template: $($result.TemplateName)" -ForegroundColor Cyan
                Write-Host "Path: $($result.TemplatePath)"
                Write-Host "Status: " -NoNewline
                
                if ($result.IsValid) {
                    Write-Host "✅ PASSED" -ForegroundColor Green
                } else {
                    Write-Host "❌ FAILED" -ForegroundColor Red
                }
                
                if ($result.Errors.Count -gt 0) {
                    Write-Host ""
                    Write-Host "  ERRORS:" -ForegroundColor Red
                    foreach ($error in $result.Errors) {
                        Write-Host "    • $error" -ForegroundColor Red
                    }
                }
                
                if ($result.Warnings.Count -gt 0) {
                    Write-Host ""
                    Write-Host "  WARNINGS:" -ForegroundColor Yellow
                    foreach ($warning in $result.Warnings) {
                        Write-Host "    • $warning" -ForegroundColor Yellow
                    }
                }
                
                if ($result.Info.Count -gt 0 -and $Verbose) {
                    Write-Host ""
                    Write-Host "  INFO:" -ForegroundColor Cyan
                    foreach ($info in $result.Info) {
                        Write-Host "    • $info" -ForegroundColor Cyan
                    }
                }
                
                Write-Host ""
                Write-Host "  Metadata:" -ForegroundColor Gray
                foreach ($key in $result.Metadata.Keys) {
                    Write-Host "    $key`: $($result.Metadata[$key])" -ForegroundColor Gray
                }
            }
        }
    }
}

# Main script execution
function Main {
    Write-Header "$SCRIPT_NAME v$SCRIPT_VERSION"
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Error "Prerequisites check failed. Please install missing components."
        exit 1
    }
    
    # Get templates to validate
    $templates = Get-BicepTemplates -Path $TemplatePath
    
    if ($templates.Count -eq 0) {
        Write-Error "No Bicep templates found to validate."
        exit 1
    }
    
    Write-Host ""
    Write-Host "Found $($templates.Count) template(s) to validate" -ForegroundColor Cyan
    Write-Host "Validation Mode: $ValidationMode"
    
    # Validate each template
    $results = @()
    $overallSuccess = $true
    
    foreach ($template in $templates) {
        $result = Invoke-TemplateValidation -Template $template -ValidationMode $ValidationMode -Subscription $Subscription -ResourceGroup $ResourceGroup -WhatIf $WhatIf.IsPresent -StopOnFirstError $StopOnFirstError.IsPresent
        
        $results += $result
        
        if (-not $result.IsValid) {
            $overallSuccess = $false
            
            if ($StopOnFirstError) {
                Write-Warning "Stopping validation due to -StopOnFirstError parameter"
                break
            }
        }
    }
    
    # Display results
    if ($OutputFormat -eq "json") {
        $jsonOutput = Format-ValidationResults -Results $results -OutputFormat "json"
        Write-Output $jsonOutput
    } else {
        Format-ValidationResults -Results $results -OutputFormat $OutputFormat
    }
    
    # Summary
    $passCount = ($results | Where-Object { $_.IsValid }).Count
    $failCount = $results.Count - $passCount
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "  VALIDATION SUMMARY" -ForegroundColor Yellow
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "  Total Templates: $($results.Count)"
    Write-Host "  Passed: $passCount" -ForegroundColor Green
    Write-Host "  Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
    Write-Host "  Overall Status: " -NoNewline
    
    if ($overallSuccess) {
        Write-Host "✅ ALL PASSED" -ForegroundColor Green
    } else {
        Write-Host "❌ SOME FAILED" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
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