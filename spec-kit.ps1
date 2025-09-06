<#
.SYNOPSIS
    Specify CLI - Setup tool for Specify projects

.DESCRIPTION
    A PowerShell implementation of the Specify CLI tool for initializing and managing
    specification-driven development projects.

.EXAMPLE
    .\spec-kit.ps1 init my-project
    .\spec-kit.ps1 init --here
    .\spec-kit.ps1 check
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Command,
    
    [Parameter(Position = 1)]
    [string]$ProjectName,
    
    [Parameter()]
    [ValidateSet('claude', 'gemini', 'copilot')]
    [string]$AI,
    
    [Parameter()]
    [switch]$NoGit,
    
    [Parameter()]
    [switch]$Here,
    
    [Parameter()]
    [switch]$IgnoreAgentTools
)

# Constants
$VERSION = "1.0.0"
$TEMPLATE_REPO = "windsurf-ai/specify-templates"
$MIN_PYTHON_VERSION = [Version]"3.11.0"
$REQUIRED_TOOLS = @(
    @{Name = "Python"; Command = "python --version"; VersionPattern = "Python (\d+\.\d+\.\d+)"; MinVersion = $MIN_PYTHON_VERSION},
    @{Name = "Git"; Command = "git --version"; Optional = $true}
)

# Colors for console output
$COLORS = @{
    Reset = "`e[0m"
    Bold = "`e[1m"
    Red = "`e[91m"
    Green = "`e[92m"
    Yellow = "`e[93m"
    Blue = "`e[94m"
    Magenta = "`e[95m"
    Cyan = "`e[96m"
}

# Helper Functions
function Write-Color {
    param(
        [string]$Message,
        [string]$Color = ""
    )
    
    if ($Color -and $COLORS.ContainsKey($Color)) {
        Write-Host $COLORS[$Color] -NoNewline
    }
    
    Write-Host $Message -NoNewline
    
    if ($Color) {
        Write-Host $COLORS.Reset -NoNewline
    }
}

function Write-Info {
    param([string]$Message)
    Write-Color "[i] " -Color "Cyan"
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Color "[✓] " -Color "Green"
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Color "[!] " -Color "Yellow"
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Color "[✗] " -Color "Red"
    Write-Host $Message -ForegroundColor Red
}

function Show-Banner {
    Clear-Host
    Write-Color "╔═╗╔═╗╔═╗╔═╗╦╔═╗╦ ╦" -Color "Cyan"
    Write-Host ""
    Write-Color "╚═╗╠═╝╠═╣║  ║╠═╝╚╦╝" -Color "Cyan"
    Write-Host ""
    Write-Color "╚═╝╩  ╩ ╩╚═╝╩╩   ╩ " -Color "Cyan"
    Write-Host ""
    Write-Host ""
    Write-Color "Specify CLI v$VERSION" -Color "Yellow"
    Write-Host ""
    Write-Host ""
}

function Test-CommandExists {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Get-VersionFromCommand {
    param([string]$Command, [string]$Pattern)
    try {
        $output = & cmd /c $Command 2>&1 | Out-String
        if ($output -match $Pattern) {
            return [Version]($matches[1])
        }
    } catch {
        return $null
    }
    return $null
}

function Test-Requirements {
    $allOk = $true
    
    foreach ($tool in $REQUIRED_TOOLS) {
        $exists = Test-CommandExists $tool.Command.Split(' ')[0]
        $version = $null
        
        if ($exists -and $tool.VersionPattern) {
            $version = Get-VersionFromCommand -Command $tool.Command -Pattern $tool.VersionPattern
        }
        
        $status = if ($exists) { "found" } else { "not found" }
        $versionText = if ($version) { " (v$version)" } else { "" }
        
        if ($exists) {
            if ($version -and $tool.MinVersion -and $version -lt $tool.MinVersion) {
                Write-Error "$($tool.Name) version $version is too old. Minimum required: $($tool.MinVersion)"
                $allOk = $false
            } else {
                Write-Success "$($tool.Name)$versionText: $status"
            }
        } elseif (-not $tool.Optional) {
            Write-Error "$($tool.Name) is required but not found. Please install it and try again."
            $allOk = $false
        } else {
            Write-Warning "$($tool.Name) (optional): $status"
        }
    }
    
    return $allOk
}

function Initialize-Project {
    [CmdletBinding()]
    param(
        [string]$ProjectName,
        [string]$AI,
        [switch]$NoGit,
        [switch]$Here,
        [switch]$IgnoreAgentTools
    )
    
    Show-Banner
    
    # Validate parameters
    if (-not $Here -and -not $ProjectName) {
        Write-Error "Project name is required when not using --here flag"
        return
    }
    
    # Set up project directory
    $projectPath = if ($Here) {
        $pwd.Path
    } else {
        Join-Path $pwd.Path $ProjectName
    }
    
    # Check if directory exists and is empty
    if (Test-Path $projectPath) {
        if ((Get-ChildItem -Path $projectPath -Force | Measure-Object).Count -gt 0) {
            Write-Error "Directory '$projectPath' is not empty. Please choose a different location or use --here to use the current directory."
            return
        }
    } else {
        New-Item -ItemType Directory -Path $projectPath | Out-Null
    }
    
    Write-Info "Initializing project in: $projectPath"
    
    # Check requirements
    Write-Info "Checking system requirements..."
    if (-not (Test-Requirements)) {
        Write-Error "System requirements not met. Please install the required tools and try again."
        return
    }
    
    # Select AI assistant if not specified
    if (-not $AI) {
        $aiOptions = @{
            'claude' = 'Claude Code (Anthropic)'
            'gemini' = 'Gemini (Google)'
            'copilot' = 'GitHub Copilot'
        }
        
        $aiChoice = Show-Menu -Title "Select AI Assistant" -Options $aiOptions
        $AI = $aiChoice
    }
    
    Write-Info "Selected AI assistant: $AI"
    
    # Download and extract template
    try {
        $tempDir = Join-Path $env:TEMP "specify-template-$(Get-Random -Minimum 1000 -Maximum 9999)"
        New-Item -ItemType Directory -Path $tempDir | Out-Null
        
        Write-Info "Downloading template..."
        $templateZip = Join-Path $tempDir "template.zip"
        $templateUrl = "https://github.com/$TEMPLATE_REPO/releases/latest/download/$AI-template.zip"
        
        $progressPreference = 'silentlyContinue'
        Invoke-WebRequest -Uri $templateUrl -OutFile $templateZip
        $progressPreference = 'Continue'
        
        Write-Info "Extracting template..."
        Expand-Archive -Path $templateZip -DestinationPath $tempDir -Force
        
        # Copy files to project directory
        $templateDir = Get-ChildItem -Path $tempDir -Directory | Select-Object -First 1
        Copy-Item -Path "$templateDir\*" -Destination $projectPath -Recurse -Force
        
        # Initialize git repository if not disabled
        if (-not $NoGit) {
            Write-Info "Initializing git repository..."
            Set-Location $projectPath
            git init | Out-Null
            git add . | Out-Null
            git commit -m "Initial commit" | Out-Null
        }
        
        Write-Success "Project initialized successfully at: $projectPath"
        
    } catch {
        Write-Error "Failed to initialize project: $_"
    } finally {
        # Clean up temp directory
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Show-Menu {
    [CmdletBinding()]
    param(
        [string]$Title,
        [hashtable]$Options,
        [string]$Prompt = "Select an option"
    )
    
    $selectedIndex = 0
    $optionsArray = @($Options.GetEnumerator() | Sort-Object Key)
    
    function Show-MenuItems {
        for ($i = 0; $i -lt $optionsArray.Count; $i++) {
            $option = $optionsArray[$i]
            $prefix = if ($i -eq $selectedIndex) { "${COLORS.Green}❯${COLORS.Reset} " } else { "  " }
            Write-Host "$prefix$($option.Value)"
        }
    }
    
    $key = $null
    do {
        Clear-Host
        Write-Host "$Title`n" -ForegroundColor Cyan
        Show-MenuItems
        Write-Host "`n$Prompt (↑/↓ to navigate, Enter to select)"
        
        $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown").VirtualKeyCode
        
        switch ($key) {
            38 { # Up arrow
                $selectedIndex = [Math]::Max(0, $selectedIndex - 1)
            }
            40 { # Down arrow
                $selectedIndex = [Math]::Min($optionsArray.Count - 1, $selectedIndex + 1)
            }
        }
    } while ($key -ne 13) # Enter key
    
    return $optionsArray[$selectedIndex].Key
}

# Main execution
function Main {
    Show-Banner
    
    if (-not $Command) {
        $Command = Show-Menu -Title "Specify CLI" -Options @{
            "init" = "Initialize a new project"
            "check" = "Check system requirements"
            "exit" = "Exit"
        } -Prompt "Select a command"
        
        if ($Command -eq "exit") {
            return
        }
    }
    
    switch ($Command.ToLower()) {
        "init" {
            Initialize-Project -ProjectName $ProjectName -AI $AI -NoGit:$NoGit -Here:$Here -IgnoreAgentTools:$IgnoreAgentTools
        }
        "check" {
            Show-Banner
            Test-Requirements | Out-Null
        }
        default {
            Write-Error "Unknown command: $Command"
            Write-Host "`nAvailable commands:"
            Write-Host "  init [project-name] - Initialize a new project"
            Write-Host "  check              - Check system requirements"
        }
    }
}

# Start the script
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Main
    } catch {
        Write-Error "An error occurred: $_"
        exit 1
    }
}
