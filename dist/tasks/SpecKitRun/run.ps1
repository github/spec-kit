[CmdletBinding()]
param()

# Import common functions
. "$PSScriptRoot\..\..\scripts\common.ps1"

# Task parameters
$workflow = Get-VstsInput -Name 'workflow' -Require
$workItemId = Get-VstsInput -Name 'workItemId' -Require
$llmConnection = Get-VstsInput -Name 'llmConnection' -Require
$temperature = [float](Get-VstsInput -Name 'temperature' -Default '0.7')
$maxTokens = [int](Get-VstsInput -Name 'maxTokens' -Default '2000')
$includeWikiPages = Get-VstsInput -Name 'includeWikiPages'
$outputLocation = Get-VstsInput -Name 'outputLocation' -Default 'repo'
$createWorkItems = Get-VstsInput -Name 'createWorkItems' -AsBool -Default $true
$customPrompt = Get-VstsInput -Name 'customPrompt'

# Environment variables
$systemAccessToken = $env:SYSTEM_ACCESSTOKEN
$teamProject = $env:SYSTEM_TEAMPROJECT
$organizationUri = $env:SYSTEM_TEAMFOUNDATIONCOLLECTIONURI
$buildNumber = $env:BUILD_BUILDNUMBER
$sourceVersion = $env:BUILD_SOURCEVERSION

Write-Host "Starting Spec Kit workflow execution..."
Write-Host "Workflow: $workflow"
Write-Host "Work Item ID: $workItemId"
Write-Host "Output Location: $outputLocation"

$startTime = Get-Date

try {
    # Validate inputs
    if (-not $systemAccessToken) {
        throw "System.AccessToken is required. Make sure to enable 'Allow scripts to access the OAuth token' in the agent job."
    }

    if ($temperature -lt 0.0 -or $temperature -gt 1.0) {
        throw "Temperature must be between 0.0 and 1.0"
    }

    # Generate unique run ID
    $runId = "run_$(Get-Date -Format 'yyyyMMddHHmmss')_$([System.Guid]::NewGuid().ToString().Substring(0,8))"
    Write-Host "Run ID: $runId"

    # Set up authentication headers
    $headers = @{
        'Authorization' = "Bearer $systemAccessToken"
        'Content-Type' = 'application/json'
    }

    # Get work item details
    Write-Host "Fetching work item details..."
    $workItemUrl = "$organizationUri$teamProject/_apis/wit/workitems/$workItemId" + "?api-version=7.0"
    $workItem = Invoke-RestMethod -Uri $workItemUrl -Headers $headers -Method Get

    $workItemTitle = $workItem.fields.'System.Title'
    $workItemDescription = $workItem.fields.'System.Description'
    $workItemType = $workItem.fields.'System.WorkItemType'
    $acceptanceCriteria = $workItem.fields.'Microsoft.VSTS.Common.AcceptanceCriteria'

    Write-Host "Work Item: #$workItemId - $workItemTitle"
    Write-Host "Type: $workItemType"

    # Get LLM service connection details
    Write-Host "Getting LLM connection details..."
    $llmConnectionDetails = Get-ServiceConnectionDetails -ConnectionId $llmConnection

    # Build constitution from wiki pages
    $constitution = ""
    if ($includeWikiPages) {
        Write-Host "Building constitution from wiki pages..."
        $wikiPages = $includeWikiPages -split "`n" | Where-Object { $_.Trim() -ne "" }
        foreach ($page in $wikiPages) {
            $pageContent = Get-WikiPageContent -ProjectName $teamProject -PagePath $page.Trim() -Headers $headers
            $constitution += "`n## $($page.Trim())`n`n$pageContent`n"
        }
    }

    # Load workflow prompt template
    $promptTemplate = Get-WorkflowPrompt -Workflow $workflow
    
    # Build context
    $context = @{
        workItem = @{
            id = $workItemId
            title = $workItemTitle
            description = $workItemDescription
            type = $workItemType
            acceptanceCriteria = $acceptanceCriteria
        }
        constitution = $constitution
        customPrompt = $customPrompt
        buildInfo = @{
            buildNumber = $buildNumber
            sourceVersion = $sourceVersion
        }
    }

    # Execute workflow
    Write-Host "Executing $workflow workflow..."
    $result = Invoke-SpecKitWorkflow -Workflow $workflow -Context $context -LLMConnection $llmConnectionDetails -Temperature $temperature -MaxTokens $maxTokens

    $duration = ((Get-Date) - $startTime).TotalMilliseconds

    # Save artifacts
    $artifactsPath = "$env:AGENT_TEMPDIRECTORY\spec-kit-$runId"
    New-Item -Path $artifactsPath -ItemType Directory -Force | Out-Null

    $artifactFiles = @()
    foreach ($artifact in $result.artifacts) {
        $fileName = "$workflow-$workItemId-$(Get-Date -Format 'yyyyMMdd-HHmmss').$($artifact.extension)"
        $filePath = Join-Path $artifactsPath $fileName
        $artifact.content | Out-File -FilePath $filePath -Encoding UTF8
        $artifactFiles += $filePath
        Write-Host "Created artifact: $fileName"
    }

    # Output to specified locations
    switch ($outputLocation) {
        "repo" {
            Write-Host "Saving artifacts to repository..."
            Save-ArtifactsToRepository -Artifacts $result.artifacts -WorkItemId $workItemId -Workflow $workflow -Headers $headers
        }
        "wiki" {
            Write-Host "Publishing artifacts to wiki..."
            Publish-ArtifactsToWiki -Artifacts $result.artifacts -WorkItemId $workItemId -Workflow $workflow -Headers $headers
        }
        "both" {
            Write-Host "Saving artifacts to repository and wiki..."
            Save-ArtifactsToRepository -Artifacts $result.artifacts -WorkItemId $workItemId -Workflow $workflow -Headers $headers
            Publish-ArtifactsToWiki -Artifacts $result.artifacts -WorkItemId $workItemId -Workflow $workflow -Headers $headers
        }
        "artifacts" {
            Write-Host "Artifacts saved to build artifacts only"
        }
    }

    # Create child work items for tasks workflow
    $workItemsCreated = 0
    if ($workflow -eq "tasks" -and $createWorkItems -and $result.tasks) {
        Write-Host "Creating child work items..."
        $workItemsCreated = Create-ChildWorkItems -ParentWorkItemId $workItemId -Tasks $result.tasks -Headers $headers
        Write-Host "Created $workItemsCreated child work items"
    }

    # Upload artifacts to build
    Write-Host "##vso[artifact.upload artifactname=spec-kit-$workflow]$artifactsPath"

    # Set output variables
    Write-Host "##vso[task.setvariable variable=runId;isOutput=true]$runId"
    Write-Host "##vso[task.setvariable variable=success;isOutput=true]true"
    Write-Host "##vso[task.setvariable variable=cost;isOutput=true]$($result.cost)"
    Write-Host "##vso[task.setvariable variable=duration;isOutput=true]$duration"
    Write-Host "##vso[task.setvariable variable=artifactsPath;isOutput=true]$artifactsPath"
    Write-Host "##vso[task.setvariable variable=workItemsCreated;isOutput=true]$workItemsCreated"

    # Add work item comment
    $comment = "Spec Kit $workflow workflow completed successfully.`n`n" +
               "Run ID: $runId`n" +
               "Duration: $([math]::Round($duration/1000, 2)) seconds`n" +
               "Cost: `$$($result.cost)`n" +
               "Artifacts: $($result.artifacts.Count)"

    if ($workItemsCreated -gt 0) {
        $comment += "`nChild work items created: $workItemsCreated"
    }

    Add-WorkItemComment -WorkItemId $workItemId -Comment $comment -Headers $headers

    Write-Host "Spec Kit workflow completed successfully!"
    Write-Host "Duration: $([math]::Round($duration/1000, 2)) seconds"
    Write-Host "Cost: `$$($result.cost)"

} catch {
    $duration = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Error "Error during Spec Kit workflow execution: $_"
    Write-Host "##vso[task.logissue type=error]$_"
    
    # Set failure output variables
    Write-Host "##vso[task.setvariable variable=runId;isOutput=true]$runId"
    Write-Host "##vso[task.setvariable variable=success;isOutput=true]false"
    Write-Host "##vso[task.setvariable variable=duration;isOutput=true]$duration"
    
    # Add error comment to work item
    $errorComment = "Spec Kit $workflow workflow failed.`n`n" +
                   "Run ID: $runId`n" +
                   "Error: $_`n" +
                   "Duration: $([math]::Round($duration/1000, 2)) seconds"
    
    try {
        Add-WorkItemComment -WorkItemId $workItemId -Comment $errorComment -Headers $headers
    } catch {
        Write-Warning "Failed to add error comment to work item: $_"
    }
    
    exit 1
}