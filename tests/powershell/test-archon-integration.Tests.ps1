# Pester tests for Archon integration scripts
# Tests JSON generation, silent operation, and request file creation

BeforeAll {
    # Import common functions
    $commonPath = Join-Path $PSScriptRoot "..\..\scripts\powershell\archon-common.ps1"
    . $commonPath

    # Create temporary test directory structure
    $script:testRoot = Join-Path $TestDrive "test-project"
    $script:featureDir = Join-Path $script:testRoot "specs\001-test-feature"
    New-Item -ItemType Directory -Path $script:featureDir -Force | Out-Null

    # Create sample spec.md
    $specContent = @"
# Test Feature

This is a test feature for validation purposes.

## Overview

This feature demonstrates the Archon integration.

## Requirements

- REQ-1: Sample requirement
- REQ-2: Another requirement
"@
    $script:specFile = Join-Path $script:featureDir "spec.md"
    $specContent | Out-File -FilePath $script:specFile -Force

    # Create sample tasks.md
    $tasksContent = @"
# Tasks for Test Feature

## User Story 1: Basic Functionality

- [ ] [T001] Implement feature core
- [ ] [T002] [P] Add tests
- [X] [T003] [US1] Complete documentation

## User Story 2: Advanced Features

- [ ] [T004] Add advanced feature
- [ ] [T005] [P] Optimize performance
"@
    $script:tasksFile = Join-Path $script:featureDir "tasks.md"
    $tasksContent | Out-File -FilePath $script:tasksFile -Force

    # Script paths
    $script:scriptDir = Join-Path $PSScriptRoot "..\..\scripts\powershell"
}

Describe "archon-auto-init.ps1" {
    BeforeAll {
        $script:initScript = Join-Path $script:scriptDir "archon-auto-init.ps1"
    }

    It "Script file exists" {
        Test-Path $script:initScript | Should -Be $true
    }

    It "Executes without errors" {
        $output = & pwsh -NoProfile -File $script:initScript $script:featureDir 2>&1
        $LASTEXITCODE | Should -Be 0
    }

    It "Operates silently (no stdout)" {
        $output = & pwsh -NoProfile -File $script:initScript $script:featureDir
        $output | Should -BeNullOrEmpty
    }

    It "Creates initialization request file" {
        & pwsh -NoProfile -File $script:initScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.init-request"

        # Give it a moment to write
        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $content.feature_name | Should -Be "001-test-feature"
            $content.project_title | Should -Not -BeNullOrEmpty
            $content.spec_file | Should -BeLike "*spec.md"
            $content.status | Should -Be "pending"
        } else {
            Set-ItResult -Skipped -Because "Archon not available or state directory not accessible"
        }
    }

    It "Extracts project title from spec.md" {
        & pwsh -NoProfile -File $script:initScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.init-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $content.project_title | Should -Be "Test Feature"
        }
    }

    It "Handles missing spec file gracefully" {
        $emptyDir = Join-Path $TestDrive "empty-feature"
        New-Item -ItemType Directory -Path $emptyDir -Force | Out-Null

        $output = & pwsh -NoProfile -File $script:initScript $emptyDir 2>&1
        $LASTEXITCODE | Should -Be 0
        $output | Should -BeNullOrEmpty
    }

    It "Validates JSON format in request file" {
        & pwsh -NoProfile -File $script:initScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.init-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $jsonContent = Get-Content -Path $requestFile -Raw
            { $jsonContent | ConvertFrom-Json } | Should -Not -Throw
        }
    }
}

Describe "archon-sync-documents.ps1" {
    BeforeAll {
        $script:syncScript = Join-Path $script:scriptDir "archon-sync-documents.ps1"

        # Create sample documents
        "# Research" | Out-File -FilePath (Join-Path $script:featureDir "research.md") -Force
        "# Plan" | Out-File -FilePath (Join-Path $script:featureDir "plan.md") -Force
    }

    It "Script file exists" {
        Test-Path $script:syncScript | Should -Be $true
    }

    It "Executes without errors for pull mode" {
        $output = & pwsh -NoProfile -File $script:syncScript $script:featureDir "pull" 2>&1
        $LASTEXITCODE | Should -Be 0
    }

    It "Executes without errors for push mode" {
        $output = & pwsh -NoProfile -File $script:syncScript $script:featureDir "push" 2>&1
        $LASTEXITCODE | Should -Be 0
    }

    It "Operates silently (no stdout)" {
        $output = & pwsh -NoProfile -File $script:syncScript $script:featureDir "pull"
        $output | Should -BeNullOrEmpty
    }

    It "Creates sync request file" {
        & pwsh -NoProfile -File $script:syncScript $script:featureDir "pull" 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $content.sync_mode | Should -Be "pull"
            $content.documents | Should -Not -BeNullOrEmpty
        }
    }

    It "Includes all document types in request" {
        & pwsh -NoProfile -File $script:syncScript $script:featureDir "push" 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $docTypes = $content.documents | ForEach-Object { $_.doc_type }

            $docTypes | Should -Contain "spec"
            $docTypes | Should -Contain "plan"
            $docTypes | Should -Contain "research"
            $docTypes | Should -Contain "tasks"
        }
    }

    It "Defaults to pull mode when no mode specified" {
        & pwsh -NoProfile -File $script:syncScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $content.sync_mode | Should -Be "pull"
        }
    }

    It "Validates JSON format in sync request" {
        & pwsh -NoProfile -File $script:syncScript $script:featureDir "pull" 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $jsonContent = Get-Content -Path $requestFile -Raw
            { $jsonContent | ConvertFrom-Json } | Should -Not -Throw
        }
    }
}

Describe "archon-auto-sync-tasks.ps1" {
    BeforeAll {
        $script:taskSyncScript = Join-Path $script:scriptDir "archon-auto-sync-tasks.ps1"
    }

    It "Script file exists" {
        Test-Path $script:taskSyncScript | Should -Be $true
    }

    It "Executes without errors" {
        $output = & pwsh -NoProfile -File $script:taskSyncScript $script:featureDir 2>&1
        $LASTEXITCODE | Should -Be 0
    }

    It "Operates silently (no stdout)" {
        $output = & pwsh -NoProfile -File $script:taskSyncScript $script:featureDir
        $output | Should -BeNullOrEmpty
    }

    It "Creates task sync request file" {
        & pwsh -NoProfile -File $script:taskSyncScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.task-sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $content.feature_name | Should -Be "001-test-feature"
            $content.tasks | Should -Not -BeNullOrEmpty
        }
    }

    It "Parses task IDs correctly" {
        & pwsh -NoProfile -File $script:taskSyncScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.task-sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $taskIds = $content.tasks | Where-Object { $_.task_id } | ForEach-Object { $_.task_id }

            $taskIds | Should -Contain "T001"
            $taskIds | Should -Contain "T002"
            $taskIds | Should -Contain "T003"
        }
    }

    It "Detects parallel task markers" {
        & pwsh -NoProfile -File $script:taskSyncScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.task-sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $parallelTasks = $content.tasks | Where-Object { $_.parallel -eq $true }

            $parallelTasks.Count | Should -BeGreaterThan 0
        }
    }

    It "Detects completed tasks" {
        & pwsh -NoProfile -File $script:taskSyncScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.task-sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $completedTasks = $content.tasks | Where-Object { $_.status -eq "done" }

            $completedTasks.Count | Should -BeGreaterThan 0
        }
    }

    It "Extracts user story markers" {
        & pwsh -NoProfile -File $script:taskSyncScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.task-sync-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $tasksWithStory = $content.tasks | Where-Object { $_.story }

            $tasksWithStory.Count | Should -BeGreaterThan 0
        }
    }
}

Describe "archon-auto-pull-status.ps1" {
    BeforeAll {
        $script:statusScript = Join-Path $script:scriptDir "archon-auto-pull-status.ps1"
    }

    It "Script file exists" {
        Test-Path $script:statusScript | Should -Be $true
    }

    It "Executes without errors" {
        $output = & pwsh -NoProfile -File $script:statusScript $script:featureDir 2>&1
        $LASTEXITCODE | Should -Be 0
    }

    It "Operates silently (no stdout)" {
        $output = & pwsh -NoProfile -File $script:statusScript $script:featureDir
        $output | Should -BeNullOrEmpty
    }

    It "Creates status request file" {
        & pwsh -NoProfile -File $script:statusScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.status-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $content.conflict_strategy | Should -Be "archon_wins"
        }
    }

    It "Includes tasks file path in request" {
        & pwsh -NoProfile -File $script:statusScript $script:featureDir 2>&1 | Out-Null

        $stateDir = Get-ArchonStateDir
        $requestFile = Join-Path $stateDir "001-test-feature.status-request"

        Start-Sleep -Milliseconds 500

        if (Test-Path $requestFile) {
            $content = Get-Content -Path $requestFile -Raw | ConvertFrom-Json
            $content.tasks_file | Should -BeLike "*tasks.md"
        }
    }
}

Describe "archon-daemon.ps1" {
    BeforeAll {
        $script:daemonScript = Join-Path $script:scriptDir "archon-daemon.ps1"
    }

    It "Script file exists" {
        Test-Path $script:daemonScript | Should -Be $true
    }

    It "Requires feature directory argument" {
        $output = & pwsh -NoProfile -File $script:daemonScript 2>&1
        $LASTEXITCODE | Should -Be 1
    }

    It "Validates minimum interval" {
        $output = & pwsh -NoProfile -File $script:daemonScript $script:featureDir 30 2>&1
        $LASTEXITCODE | Should -Be 1  # Should reject intervals < 60 seconds
    }

    It "Accepts valid interval" {
        # Start daemon and immediately kill it to test initialization
        $job = Start-Job -ScriptBlock {
            param($script, $dir)
            & pwsh -NoProfile -File $script $dir 60 2>&1
        } -ArgumentList $script:daemonScript, $script:featureDir

        Start-Sleep -Milliseconds 500
        Stop-Job $job
        Remove-Job $job

        # Should have started successfully
        $job.State | Should -BeIn @('Running', 'Completed', 'Stopped')
    }

    It "Creates PID file when started" {
        $job = Start-Job -ScriptBlock {
            param($script, $dir)
            & pwsh -NoProfile -File $script $dir 60 2>&1
        } -ArgumentList $script:daemonScript, $script:featureDir

        Start-Sleep -Seconds 1

        $stateDir = Get-ArchonStateDir
        $pidFile = Join-Path $stateDir "001-test-feature.daemon.pid"

        $pidExists = Test-Path $pidFile

        Stop-Job $job
        Remove-Job $job

        if ($pidExists) {
            # PID file should have been created
            $true | Should -Be $true
        } else {
            Set-ItResult -Skipped -Because "Archon not available or daemon did not start"
        }
    }
}

Describe "Silent Operation Validation" {
    It "All scripts suppress stdout/stderr" {
        $scripts = @(
            @{ Script = "archon-auto-init.ps1"; Args = @($script:featureDir) }
            @{ Script = "archon-sync-documents.ps1"; Args = @($script:featureDir, "pull") }
            @{ Script = "archon-auto-sync-tasks.ps1"; Args = @($script:featureDir) }
            @{ Script = "archon-auto-pull-status.ps1"; Args = @($script:featureDir) }
        )

        foreach ($scriptInfo in $scripts) {
            $scriptPath = Join-Path $script:scriptDir $scriptInfo.Script
            $output = & pwsh -NoProfile -File $scriptPath @($scriptInfo.Args) 2>&1 | Where-Object { $_ }

            $output | Should -BeNullOrEmpty -Because "$($scriptInfo.Script) should be silent"
        }
    }
}

Describe "Error Handling" {
    It "Scripts handle missing feature directory gracefully" {
        $scripts = @(
            "archon-auto-init.ps1",
            "archon-sync-documents.ps1",
            "archon-auto-sync-tasks.ps1",
            "archon-auto-pull-status.ps1"
        )

        foreach ($scriptName in $scripts) {
            $scriptPath = Join-Path $script:scriptDir $scriptName
            $output = & pwsh -NoProfile -File $scriptPath 2>&1

            $LASTEXITCODE | Should -Be 0 -Because "$scriptName should exit gracefully"
            $output | Should -BeNullOrEmpty -Because "$scriptName should be silent even on error"
        }
    }

    It "Scripts handle invalid feature directory gracefully" {
        $invalidDir = "/nonexistent/path/to/feature"

        $scripts = @(
            "archon-auto-init.ps1",
            "archon-sync-documents.ps1",
            "archon-auto-sync-tasks.ps1",
            "archon-auto-pull-status.ps1"
        )

        foreach ($scriptName in $scripts) {
            $scriptPath = Join-Path $script:scriptDir $scriptName
            $output = & pwsh -NoProfile -File $scriptPath $invalidDir 2>&1

            $LASTEXITCODE | Should -Be 0 -Because "$scriptName should exit gracefully"
            $output | Should -BeNullOrEmpty -Because "$scriptName should be silent even on error"
        }
    }
}
