#!/usr/bin/env pwsh
# Create Azure DevOps work items using Azure CLI with OAuth (no PAT required)
# Requires: Azure CLI with devops extension

param(
    [Parameter(Mandatory=$true)]
    [string]$SpecFile,
    
    [Parameter(Mandatory=$false)]
    [string]$Organization = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Project = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Stories = "all",
    
    [Parameter(Mandatory=$false)]
    [string]$AreaPath = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$FromTasks = $false
)

# Check if Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI not found. Please install from: https://aka.ms/installazurecliwindows"
    exit 1
}

# Check if devops extension is installed
$extensions = az extension list --output json | ConvertFrom-Json
if (-not ($extensions | Where-Object { $_.name -eq "azure-devops" })) {
    Write-Host "Installing Azure DevOps extension for Azure CLI..."
    az extension add --name azure-devops
}

# Check authentication
Write-Host "Checking Azure authentication..."
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not authenticated. Running 'az login' with OAuth..."
    az login --use-device-code
}

# Validate required parameters
if ([string]::IsNullOrEmpty($Organization)) {
    Write-Error "Organization parameter is required. Please provide -Organization parameter."
    exit 1
}
if ([string]::IsNullOrEmpty($Project)) {
    Write-Error "Project parameter is required. Please provide -Project parameter."
    exit 1
}
if ([string]::IsNullOrEmpty($AreaPath)) {
    Write-Error "AreaPath parameter is required. Please provide -AreaPath parameter."
    exit 1
}

# Save configuration for future reference
$configDir = Join-Path $env:USERPROFILE ".speckit"
$configFile = Join-Path $configDir "ado-config.json"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}
$config = @{
    Organization = $Organization
    Project = $Project
    AreaPath = $AreaPath
    LastUpdated = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}
$config | ConvertTo-Json | Set-Content $configFile

Write-Host "Using Azure DevOps configuration:" -ForegroundColor Cyan
Write-Host "  Organization: $Organization" -ForegroundColor Yellow
Write-Host "  Project: $Project" -ForegroundColor Yellow
Write-Host "  Area Path: $AreaPath" -ForegroundColor Yellow
Write-Host ""

# Set defaults for Azure CLI
az devops configure --defaults organization="https://dev.azure.com/$Organization" project="$Project"

# Parse user stories from spec.md
function Get-UserStories {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        Write-Error "Spec file not found: $FilePath"
        exit 1
    }
    
    $content = Get-Content -Path $FilePath -Raw
    $parsedStories = [System.Collections.ArrayList]::new()
    
    # Match: ### User Story X - Title (Priority: PX)
    $pattern = '###\s+User\s+Story\s+(\d+)\s*-\s*([^\(]+)\s*\(Priority:\s*P(\d+)\)'
    $regexMatches = [regex]::Matches($content, $pattern)
    
    foreach ($match in $regexMatches) {
        $storyNum = $match.Groups[1].Value
        $title = $match.Groups[2].Value.Trim()
        $priority = $match.Groups[3].Value
        
        # Extract story content (everything until next ### or ## section)
        $startPos = $match.Index
        $nextStoryPattern = '###\s+User\s+Story\s+\d+'
        $nextMatch = [regex]::Match($content.Substring($startPos + 1), $nextStoryPattern)
        
        if ($nextMatch.Success) {
            $endPos = $startPos + $nextMatch.Index + 1
            $storyContent = $content.Substring($startPos, $endPos - $startPos)
        } else {
            # Find next ## level section (Edge Cases, Requirements, etc.)
            $endMatch = [regex]::Match($content.Substring($startPos), '\n##\s+(Edge Cases|Requirements|Success Criteria|Assumptions|Out of Scope)')
            if ($endMatch.Success) {
                $storyContent = $content.Substring($startPos, $endMatch.Index)
            } else {
                $storyContent = $content.Substring($startPos)
            }
        }
        
        # Extract sections
        $description = ""
        if ($storyContent -match '(?s)Priority: P\d+\)\s*\n\s*\n(.+?)(?=\*\*Why this priority|###|##\s+|$)') {
            $description = $Matches[1].Trim()
        }
        
        $whyPriority = ""
        if ($storyContent -match '\*\*Why this priority\*\*:\s*(.+?)(?=\n\n|\*\*Independent Test|###|$)') {
            $whyPriority = $Matches[1].Trim()
        }
        
        $independentTest = ""
        if ($storyContent -match '\*\*Independent Test\*\*:\s*(.+?)(?=\n\n|\*\*Acceptance|###|$)') {
            $independentTest = $Matches[1].Trim()
        }
        
        $acceptanceCriteria = ""
        if ($storyContent -match '(?s)\*\*Acceptance Scenarios\*\*:\s*\n\s*\n(.+?)(?=###|##\s+Edge Cases|##\s+Requirements|$)') {
            $acceptanceCriteria = $Matches[1].Trim()
        }
        
        [void]$parsedStories.Add([PSCustomObject]@{
            Number = $storyNum
            Title = $title
            Priority = $priority
            Description = $description
            Why = $whyPriority
            Test = $independentTest
            Acceptance = $acceptanceCriteria
        })
    }
    
    return ,$parsedStories
}

# Parse tasks from tasks.md file
function Get-Tasks {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        Write-Error "Tasks file not found: $FilePath"
        exit 1
    }
    
    $content = Get-Content -Path $FilePath -Raw
    $parsedTasks = [System.Collections.ArrayList]::new()
    
    # Match: - [ ] TXXX [P] [Story] Description
    $pattern = '-\s*\[\s*\]\s+T(\d+)\s+(?:\[P\]\s+)?(?:\[([^\]]+)\]\s+)?(.+)'
    $regexMatches = [regex]::Matches($content, $pattern)
    
    Write-Verbose "Found $($regexMatches.Count) task matches in tasks file"
    
    foreach ($match in $regexMatches) {
        $taskNum = $match.Groups[1].Value
        $story = $match.Groups[2].Value.Trim()
        $description = $match.Groups[3].Value.Trim()
        
        # Default priority to 2 (medium) for tasks
        $priority = 2
        
        # If story tag exists, extract priority (US1=P1, etc.)
        if ($story -match 'US(\d+)') {
            $priority = [int]$Matches[1]
            if ($priority -gt 4) { $priority = 4 }
        }
        
        # Title as task number + description (truncate if too long)
        $title = "T$taskNum - $description"
        if ($title.Length -gt 100) {
            $title = $title.Substring(0, 97) + "..."
        }
        
        # Full description includes story tag
        $fullDescription = $description
        if (-not [string]::IsNullOrEmpty($story)) {
            $fullDescription = "[$story] $description"
        }
        
        [void]$parsedTasks.Add([PSCustomObject]@{
            Number = $taskNum
            Title = $title
            Priority = $priority
            Description = $fullDescription
            Story = $story
        })
    }
    
    return ,$parsedTasks
}

# Filter stories based on selection
function Get-SelectedStories {
    param([array]$AllStories, [string]$Selection)
    
    if ($Selection -eq "all" -or [string]::IsNullOrEmpty($Selection)) {
        return $AllStories
    }
    
    $selectedNumbers = @()
    $parts = $Selection -split ','
    
    foreach ($part in $parts) {
        $part = $part.Trim()
        if ($part -match '^(\d+)-(\d+)$') {
            $start = [int]$Matches[1]
            $end = [int]$Matches[2]
            $selectedNumbers += $start..$end
        }
        elseif ($part -match '^\d+$') {
            $selectedNumbers += [int]$part
        }
    }
    
    return $AllStories | Where-Object { $selectedNumbers -contains [int]$_.Number }
}

Write-Host ""
Write-Host "=============================================="
if ($FromTasks) {
    Write-Host "Azure DevOps Work Items from Tasks"
} else {
    Write-Host "Azure DevOps Work Item Creation (OAuth)"
}
Write-Host "=============================================="
Write-Host "Organization: $Organization"
Write-Host "Project: $Project"
Write-Host "File: $SpecFile"
Write-Host ""

$featureName = Split-Path (Split-Path $SpecFile -Parent) -Leaf

# Parse and filter items (tasks or stories)
if ($FromTasks) {
    $allStories = Get-Tasks -FilePath $SpecFile
    $itemType = "Task"
    $itemLabel = "tasks"
} else {
    $allStories = Get-UserStories -FilePath $SpecFile
    $itemType = "User Story"
    $itemLabel = "user stories"
}

$selectedStories = Get-SelectedStories -AllStories $allStories -Selection $Stories

Write-Host "Found $($allStories.Count) $itemLabel"
Write-Host "Syncing $($selectedStories.Count) $itemLabel"
Write-Host ""

# Show preview of items to be created
Write-Host "Items to be created:" -ForegroundColor Cyan
Write-Host ""
foreach ($story in $selectedStories) {
    Write-Host "  [$($story.Number)] P$($story.Priority) - $($story.Title)" -ForegroundColor Yellow
    if (-not $FromTasks) {
        $desc = $story.Description.Substring(0, [Math]::Min(80, $story.Description.Length))
        if ($story.Description.Length -gt 80) { $desc += "..." }
        Write-Host "      $desc" -ForegroundColor Gray
    } else {
        Write-Host "      Story: $($story.Story)" -ForegroundColor Gray
    }
}
Write-Host ""

$createdItems = @()

# Load parent user story mapping for tasks
$parentMapping = @{}
if ($FromTasks) {
    $mappingFile = Join-Path (Split-Path $SpecFile -Parent) ".speckit\azure-devops-mapping.json"
    if (Test-Path $mappingFile) {
        $mapping = Get-Content $mappingFile -Raw | ConvertFrom-Json
        foreach ($item in $mapping.workItems) {
            # Map story number to work item ID (e.g., "1" -> workItemId)
            if ($item.StoryNumber -match '^\d+$') {
                $parentMapping[$item.StoryNumber] = $item.WorkItemId
            }
        }
        Write-Host "Loaded parent user story mappings: $($parentMapping.Count) stories" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "Warning: No user story mapping found. Tasks will be created without parent links." -ForegroundColor Yellow
        Write-Host "Run the script on spec.md first to create user stories, then create tasks." -ForegroundColor Yellow
        Write-Host ""
    }
}

foreach ($story in $selectedStories) {
    if ($FromTasks) {
        $workItemTitle = $story.Title
        $fullDescription = $story.Description
        $tags = "spec-kit;$featureName;task"
        if ($story.Story) {
            $tags += ";$($story.Story)"
        }
        Write-Host "Creating Task $($story.Number): $($story.Description.Substring(0, [Math]::Min(60, $story.Description.Length)))..."
    } else {
        $workItemTitle = "User Story $($story.Number) - $($story.Title)"
        $fullDescription = $story.Description
        
        if ($story.Why) {
            $fullDescription += "`n`n**Why this priority**: $($story.Why)"
        }
        if ($story.Test) {
            $fullDescription += "`n`n**Independent Test**: $($story.Test)"
        }
        
        $tags = "spec-kit;$featureName;user-story"
        Write-Host "Creating User Story $($story.Number): $($story.Title)..."
    }
    

    # Create work item using Azure CLI
    try {
        # Escape special characters in field values
        # For title: escape quotes by doubling them for Azure CLI
        $cleanTitle = $workItemTitle -replace '"', '""'
        $cleanDesc = $fullDescription -replace '"', '\"' -replace '\r?\n', ' '
        
        # Build field arguments
        $fieldArgs = @(
            "System.Description=$cleanDesc"
            "Microsoft.VSTS.Common.Priority=$($story.Priority)"
            "System.Tags=$tags"
            "System.AssignedTo="  # Explicitly leave unassigned
        )
        
        # Add Original Estimate for Tasks (required field in Azure DevOps)
        if ($FromTasks) {
            $fieldArgs += "Microsoft.VSTS.Scheduling.OriginalEstimate=0"
        }
        
        # Add acceptance criteria only for user stories
        if (-not $FromTasks -and $story.Acceptance) {
            $cleanAcceptance = $story.Acceptance -replace '"', '\"' -replace '\r?\n', ' '
            $fieldArgs += "Microsoft.VSTS.Common.AcceptanceCriteria=$cleanAcceptance"
        }
        
        if ($AreaPath) {
            $fieldArgs += "System.AreaPath=$AreaPath"
        }
        
        # Build complete command arguments array
        $azArgs = @(
            'boards', 'work-item', 'create'
            '--type', $itemType
            '--title', $cleanTitle
            '--organization', "https://dev.azure.com/$Organization"
            '--project', $Project
            '--fields'
        ) + $fieldArgs + @('--output', 'json')
        
        Write-Verbose "Total args: $($azArgs.Count)"
        Write-Verbose "Args: $($azArgs -join ' | ')"
        
        # Execute command
        $result = & az @azArgs 2>&1
        $resultString = $result | Out-String
        
        if ($LASTEXITCODE -eq 0 -and $resultString -notmatch "ERROR") {
            try {
                $workItem = $resultString | ConvertFrom-Json
            } catch {
                Write-Host "  [FAIL] Failed to parse response"
                Write-Host "  Error: $_"
                Write-Host ""
                continue
            }
            $workItemId = $workItem.id
            $workItemUrl = "https://dev.azure.com/$Organization/$Project/_workitems/edit/$workItemId"
            
            Write-Host "  [OK] Created work item #$workItemId"
            Write-Host "  -> $workItemUrl"
            Write-Host ""
            
            $createdItems += [PSCustomObject]@{
                StoryNumber = $story.Number
                Title = $story.Title
                Priority = "P$($story.Priority)"
                WorkItemId = $workItemId
                WorkItemUrl = $workItemUrl
                ParentStoryNumber = if ($FromTasks) { $story.Story } else { $null }
                Status = "Created"
            }
        } else {
            Write-Host "  [FAIL] Failed to create work item"
            Write-Host "  Error: $resultString"
            Write-Host ""
        }
    }
    catch {
        Write-Host "  [ERROR] Error: $_"
        Write-Host ""
    }
}

# Display summary
if ($createdItems.Count -gt 0) {
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "[SUCCESS] Azure DevOps Sync Complete"
    Write-Host "=============================================="
    Write-Host ""
    Write-Host "Organization: $Organization"
    Write-Host "Project: $Project"
    Write-Host "Feature: $featureName"
    $selectionLabel = if ($FromTasks) { "tasks" } else { "user stories" }
    $selectedCount = if ($null -ne $selectedStories) { $selectedStories.Count } else { 0 }
    Write-Host "Created: $($createdItems.Count) of $selectedCount $selectionLabel"
    Write-Host ""
    Write-Host "Created Work Items:"
    Write-Host ""
    
    foreach ($item in $createdItems) {
        Write-Host "  [$($item.StoryNumber)] $($item.Title) ($($item.Priority))"
        Write-Host "      Work Item: #$($item.WorkItemId)"
        Write-Host "      Link: $($item.WorkItemUrl)"
        Write-Host ""
    }
    
    Write-Host "View in Azure DevOps:"
    Write-Host "  Boards: https://dev.azure.com/$Organization/$Project/_boards"
    Write-Host "  Work Items: https://dev.azure.com/$Organization/$Project/_workitems"
    Write-Host ""
    
    # Link tasks to parent user stories if FromTasks mode
    if ($FromTasks -and $parentMapping.Count -gt 0) {
        Write-Host "Linking tasks to parent user stories..." -ForegroundColor Cyan
        Write-Host ""
        
        foreach ($item in $createdItems) {
            if ($item.ParentStoryNumber) {
                # Extract story number from "US1" format
                $storyNum = $null
                if ($item.ParentStoryNumber -match 'US(\d+)') {
                    $storyNum = $Matches[1]
                } elseif ($item.ParentStoryNumber -match '^\d+$') {
                    $storyNum = $item.ParentStoryNumber
                }
                
                if ($storyNum -and $parentMapping.ContainsKey($storyNum)) {
                    $parentId = $parentMapping[$storyNum]
                    Write-Host "  Linking Task #$($item.WorkItemId) -> User Story #$parentId..." -NoNewline
                    
                    $linkArgs = @(
                        'boards', 'work-item', 'relation', 'add'
                        '--id', $item.WorkItemId
                        '--relation-type', 'Parent'
                        '--target-id', $parentId
                        '--organization', "https://dev.azure.com/$Organization"
                        '--output', 'json'
                    )
                    $linkResult = & az @linkArgs 2>&1 | Out-String
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host " [OK]" -ForegroundColor Green
                    } else {
                        Write-Host " [FAIL]" -ForegroundColor Yellow
                        Write-Host "    Error: $linkResult" -ForegroundColor Gray
                    }
                }
            }
        }
        Write-Host ""
    }
    Write-Host ""
    
    # Save mapping
    $mappingDir = Join-Path (Split-Path $SpecFile -Parent) ".speckit"
    if (-not (Test-Path $mappingDir)) {
        New-Item -ItemType Directory -Path $mappingDir -Force | Out-Null
    }
    
    $mappingFile = Join-Path $mappingDir "azure-devops-mapping.json"
    $mapping = @{
        feature = $featureName
        organization = $Organization
        project = $Project
        syncDate = Get-Date -Format "o"
        workItems = $createdItems
    }
    
    $mapping | ConvertTo-Json -Depth 10 | Out-File -FilePath $mappingFile -Encoding UTF8
    Write-Host "Mapping saved: $mappingFile"
    Write-Host ""
}
