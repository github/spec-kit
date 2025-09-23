[CmdletBinding()]
param()

# Import Azure DevOps PowerShell module functions
. "$PSScriptRoot\..\..\scripts\common.ps1"

# Task parameters
$targetBranch = Get-VstsInput -Name 'targetBranch' -Require
$createPR = Get-VstsInput -Name 'createPR' -AsBool
$prTitle = Get-VstsInput -Name 'prTitle'
$prDescription = Get-VstsInput -Name 'prDescription'
$overwriteExisting = Get-VstsInput -Name 'overwriteExisting' -AsBool
$customTemplatesPath = Get-VstsInput -Name 'customTemplatesPath'

# Environment variables
$systemAccessToken = $env:SYSTEM_ACCESSTOKEN
$teamProject = $env:SYSTEM_TEAMPROJECT
$repositoryName = $env:BUILD_REPOSITORY_NAME
$organizationUri = $env:SYSTEM_TEAMFOUNDATIONCOLLECTIONURI

Write-Host "Starting Spec Kit repository seeding..."
Write-Host "Target Branch: $targetBranch"
Write-Host "Create PR: $createPR"
Write-Host "Repository: $repositoryName"

try {
    # Validate inputs
    if (-not $systemAccessToken) {
        throw "System.AccessToken is required. Make sure to enable 'Allow scripts to access the OAuth token' in the agent job."
    }

    # Set up authentication headers
    $headers = @{
        'Authorization' = "Bearer $systemAccessToken"
        'Content-Type' = 'application/json'
    }

    # Get repository information
    $repoUrl = "$organizationUri$teamProject/_apis/git/repositories/$repositoryName" + "?api-version=7.0"
    $repoResponse = Invoke-RestMethod -Uri $repoUrl -Headers $headers -Method Get
    $repositoryId = $repoResponse.id
    $defaultBranch = $repoResponse.defaultBranch -replace 'refs/heads/', ''

    Write-Host "Repository ID: $repositoryId"
    Write-Host "Default Branch: $defaultBranch"

    # Create seed branch
    $seedBranchName = "spec-kit-seed-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $seedBranchRef = "refs/heads/$seedBranchName"

    # Get the latest commit from target branch
    $targetBranchRef = "refs/heads/$targetBranch"
    $refsUrl = "$organizationUri$teamProject/_apis/git/repositories/$repositoryId/refs" + "?filter=heads/$targetBranch&api-version=7.0"
    $refsResponse = Invoke-RestMethod -Uri $refsUrl -Headers $headers -Method Get
    
    if ($refsResponse.count -eq 0) {
        throw "Target branch '$targetBranch' not found in repository"
    }
    
    $latestCommitId = $refsResponse.value[0].objectId

    # Create new branch
    $createBranchBody = @{
        name = $seedBranchRef
        oldObjectId = "0000000000000000000000000000000000000000"
        newObjectId = $latestCommitId
    } | ConvertTo-Json

    $createBranchUrl = "$organizationUri$teamProject/_apis/git/repositories/$repositoryId/refs" + "?api-version=7.0"
    $branchResponse = Invoke-RestMethod -Uri $createBranchUrl -Headers $headers -Method Post -Body "[$createBranchBody]"

    Write-Host "Created seed branch: $seedBranchName"

    # Define template files
    $templateFiles = @(
        @{
            Path = ".github/prompts/specify.md"
            Content = Get-SpecifyTemplate
        },
        @{
            Path = ".github/prompts/plan.md"
            Content = Get-PlanTemplate
        },
        @{
            Path = ".github/prompts/tasks.md"
            Content = Get-TasksTemplate
        },
        @{
            Path = ".github/prompts/constitution.md"
            Content = Get-ConstitutionTemplate
        },
        @{
            Path = ".specify/config.yml"
            Content = Get-ConfigTemplate
        },
        @{
            Path = ".specify/templates/user-story.md"
            Content = Get-UserStoryTemplate
        },
        @{
            Path = ".specify/templates/feature.md"
            Content = Get-FeatureTemplate
        },
        @{
            Path = ".specify/guardrails/security.yml"
            Content = Get-SecurityGuardrailsTemplate
        },
        @{
            Path = ".specify/guardrails/performance.yml"
            Content = Get-PerformanceGuardrailsTemplate
        }
    )

    # Load custom templates if specified
    if ($customTemplatesPath -and (Test-Path $customTemplatesPath)) {
        Write-Host "Loading custom templates from: $customTemplatesPath"
        $customFiles = Get-ChildItem -Path $customTemplatesPath -Recurse -File
        foreach ($file in $customFiles) {
            $relativePath = $file.FullName.Substring($customTemplatesPath.Length + 1)
            $templateFiles += @{
                Path = $relativePath
                Content = Get-Content -Path $file.FullName -Raw
            }
        }
    }

    # Check existing files if not overwriting
    $existingFiles = @()
    if (-not $overwriteExisting) {
        foreach ($file in $templateFiles) {
            $checkUrl = "$organizationUri$teamProject/_apis/git/repositories/$repositoryId/items" + "?path=/$($file.Path)&versionDescriptor.version=$targetBranch&api-version=7.0"
            try {
                Invoke-RestMethod -Uri $checkUrl -Headers $headers -Method Get | Out-Null
                $existingFiles += $file.Path
            }
            catch {
                # File doesn't exist, which is what we want
            }
        }

        if ($existingFiles.Count -gt 0) {
            Write-Warning "The following files already exist and will be skipped:"
            $existingFiles | ForEach-Object { Write-Warning "  $_" }
            $templateFiles = $templateFiles | Where-Object { $_.Path -notin $existingFiles }
        }
    }

    if ($templateFiles.Count -eq 0) {
        Write-Warning "No files to add. All Spec Kit files already exist."
        return
    }

    # Prepare commit changes
    $changes = @()
    foreach ($file in $templateFiles) {
        $encodedContent = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($file.Content))
        $changes += @{
            changeType = "add"
            item = @{
                path = "/$($file.Path)"
            }
            newContent = @{
                content = $encodedContent
                contentType = "base64encoded"
            }
        }
    }

    # Create commit
    $commitBody = @{
        refUpdates = @(
            @{
                name = $seedBranchRef
                oldObjectId = $latestCommitId
            }
        )
        commits = @(
            @{
                comment = "Add Spec Kit configuration and templates"
                changes = $changes
            }
        )
    } | ConvertTo-Json -Depth 10

    $pushUrl = "$organizationUri$teamProject/_apis/git/repositories/$repositoryId/pushes" + "?api-version=7.0"
    $pushResponse = Invoke-RestMethod -Uri $pushUrl -Headers $headers -Method Post -Body $commitBody

    Write-Host "Committed $($templateFiles.Count) files to branch $seedBranchName"

    # Set output variables
    Write-Host "##vso[task.setvariable variable=seedBranch;isOutput=true]$seedBranchName"
    Write-Host "##vso[task.setvariable variable=filesAdded;isOutput=true]$($templateFiles.Count)"

    # Create pull request if requested
    if ($createPR) {
        $prBody = @{
            sourceRefName = $seedBranchRef
            targetRefName = $targetBranchRef
            title = $prTitle
            description = $prDescription
        } | ConvertTo-Json

        $prUrl = "$organizationUri$teamProject/_apis/git/repositories/$repositoryId/pullrequests" + "?api-version=7.0"
        $prResponse = Invoke-RestMethod -Uri $prUrl -Headers $headers -Method Post -Body $prBody

        Write-Host "Created pull request #$($prResponse.pullRequestId): $($prResponse.title)"
        Write-Host "Pull request URL: $($prResponse.url)"

        # Set PR output variables
        Write-Host "##vso[task.setvariable variable=pullRequestId;isOutput=true]$($prResponse.pullRequestId)"
        Write-Host "##vso[task.setvariable variable=pullRequestUrl;isOutput=true]$($prResponse.url)"
    }

    Write-Host "Spec Kit seeding completed successfully!"

} catch {
    Write-Error "Error during Spec Kit seeding: $_"
    Write-Host "##vso[task.logissue type=error]$_"
    exit 1
}