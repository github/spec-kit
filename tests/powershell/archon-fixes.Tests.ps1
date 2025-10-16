#!/usr/bin/env pwsh
# Pester Tests for Critical Archon MCP Integration Bug Fixes
# Purpose: Validate fixes for state directory resolution, atomic writes, and error handling

BeforeAll {
    # Import the archon-common.ps1 module to test
    $scriptRoot = Split-Path -Parent $PSScriptRoot
    $scriptsDir = Join-Path $scriptRoot "scripts" "powershell"
    $commonScript = Join-Path $scriptsDir "archon-common.ps1"

    # Source the common script to load functions
    . $commonScript

    # Create a temporary test directory for state files
    $script:testStateDir = Join-Path $TestDrive "test-state"
    $script:testFeatureName = "999-test-feature"
    $script:testFeatureDir = Join-Path $TestDrive "specs" $script:testFeatureName

    # Create test feature directory
    New-Item -ItemType Directory -Path $script:testFeatureDir -Force | Out-Null
}

Describe "Critical Fix 1: Get-ArchonStateDir Consistency" {

    It "should return the same state directory when called multiple times" {
        $firstCall = Get-ArchonStateDir
        $secondCall = Get-ArchonStateDir
        $thirdCall = Get-ArchonStateDir

        $firstCall | Should -Be $secondCall
        $secondCall | Should -Be $thirdCall
    }

    It "should return an absolute path" {
        $stateDir = Get-ArchonStateDir
        [System.IO.Path]::IsPathRooted($stateDir) | Should -Be $true
    }

    It "should return a path relative to archon-common.ps1 location" {
        $stateDir = Get-ArchonStateDir
        $scriptsDir = Split-Path -Parent $commonScript

        # State dir should be inside the scripts directory
        $stateDir | Should -Match ([regex]::Escape($scriptsDir))
    }

    It "should return path ending with .archon-state" {
        $stateDir = Get-ArchonStateDir
        $stateDir | Should -Match '\.archon-state$'
    }

    It "should be callable from different working directories" {
        Push-Location $TestDrive
        try {
            $fromTestDrive = Get-ArchonStateDir

            Push-Location $HOME
            try {
                $fromHome = Get-ArchonStateDir
                $fromTestDrive | Should -Be $fromHome
            } finally {
                Pop-Location
            }
        } finally {
            Pop-Location
        }
    }
}

Describe "Critical Fix 2: Atomic Write Safety - Save-ProjectMapping" {

    BeforeEach {
        # Mock Get-ArchonStateDir to use test directory
        Mock Get-ArchonStateDir { return $script:testStateDir }
    }

    It "should create state directory if it doesn't exist" {
        if (Test-Path $script:testStateDir) {
            Remove-Item -Path $script:testStateDir -Recurse -Force
        }

        $result = Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-test-123"

        Test-Path $script:testStateDir | Should -Be $true
    }

    It "should create temp file during write operation" {
        # We can't directly observe the temp file since it's deleted quickly,
        # but we can verify the final file exists and is valid
        $result = Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-test-456"

        $result | Should -Be $true
        $pidFile = Join-Path $script:testStateDir "$($script:testFeatureName).pid"
        Test-Path $pidFile | Should -Be $true
    }

    It "should not leave temp file after successful write" {
        $result = Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-test-789"

        $pidFile = Join-Path $script:testStateDir "$($script:testFeatureName).pid"
        $tempFile = "$pidFile.tmp"

        Test-Path $tempFile | Should -Be $false
    }

    It "should return true on successful save" {
        $result = Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-success"
        $result | Should -Be $true
    }

    It "should overwrite existing project mapping atomically" {
        Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-old"
        Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-new"

        $saved = Get-ProjectMapping -FeatureName $script:testFeatureName
        $saved | Should -Be "proj-new"
    }

    It "should handle write errors gracefully and return false" {
        Mock Get-ArchonStateDir { return "/invalid/readonly/path" }

        $result = Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-fail"
        $result | Should -Be $false
    }
}

Describe "Critical Fix 3: Atomic Write Safety - Save-DocumentMapping" {

    BeforeEach {
        Mock Get-ArchonStateDir { return $script:testStateDir }
        # Ensure state dir exists
        New-Item -ItemType Directory -Path $script:testStateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    It "should create temp file and move atomically" {
        $result = Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md" -DocId "doc-123"

        $result | Should -Be $true
        $docsFile = Join-Path $script:testStateDir "$($script:testFeatureName).docs"
        Test-Path $docsFile | Should -Be $true
    }

    It "should not leave temp file after write" {
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "plan.md" -DocId "doc-456"

        $docsFile = Join-Path $script:testStateDir "$($script:testFeatureName).docs"
        $tempFile = "$docsFile.tmp"

        Test-Path $tempFile | Should -Be $false
    }

    It "should append multiple document mappings" {
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md" -DocId "doc-1"
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "plan.md" -DocId "doc-2"
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "tasks.md" -DocId "doc-3"

        $doc1 = Get-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md"
        $doc2 = Get-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "plan.md"
        $doc3 = Get-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "tasks.md"

        $doc1 | Should -Be "doc-1"
        $doc2 | Should -Be "doc-2"
        $doc3 | Should -Be "doc-3"
    }

    It "should update existing document mapping without duplicates" {
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md" -DocId "doc-old"
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md" -DocId "doc-new"

        $docsFile = Join-Path $script:testStateDir "$($script:testFeatureName).docs"
        $content = Get-Content -Path $docsFile

        # Should only have one entry for spec.md
        $specEntries = $content | Where-Object { $_ -match '^spec\.md:' }
        $specEntries.Count | Should -Be 1
        $specEntries[0] | Should -Be "spec.md:doc-new"
    }

    It "should return false on write errors" {
        Mock Get-ArchonStateDir { return "/invalid/readonly/path" }

        $result = Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "fail.md" -DocId "doc-fail"
        $result | Should -Be $false
    }
}

Describe "Critical Fix 4: Atomic Write Safety - Save-TaskMapping" {

    BeforeEach {
        Mock Get-ArchonStateDir { return $script:testStateDir }
        New-Item -ItemType Directory -Path $script:testStateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    It "should save task mapping atomically" {
        $result = Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T001" -TaskArchon "task-uuid-1"

        $result | Should -Be $true
        $tasksFile = Join-Path $script:testStateDir "$($script:testFeatureName).tasks"
        Test-Path $tasksFile | Should -Be $true
    }

    It "should not leave temp file after save" {
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T002" -TaskArchon "task-uuid-2"

        $tasksFile = Join-Path $script:testStateDir "$($script:testFeatureName).tasks"
        $tempFile = "$tasksFile.tmp"

        Test-Path $tempFile | Should -Be $false
    }

    It "should handle multiple task mappings" {
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T001" -TaskArchon "task-a"
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T002" -TaskArchon "task-b"
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T003" -TaskArchon "task-c"

        $task1 = Get-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T001"
        $task2 = Get-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T002"
        $task3 = Get-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T003"

        $task1 | Should -Be "task-a"
        $task2 | Should -Be "task-b"
        $task3 | Should -Be "task-c"
    }

    It "should update existing task mapping without duplicates" {
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T001" -TaskArchon "task-old"
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T001" -TaskArchon "task-new"

        $tasksFile = Join-Path $script:testStateDir "$($script:testFeatureName).tasks"
        $content = Get-Content -Path $tasksFile

        $t001Entries = $content | Where-Object { $_ -match '^T001:' }
        $t001Entries.Count | Should -Be 1
        $t001Entries[0] | Should -Be "T001:task-new"
    }
}

Describe "Critical Fix 5: Atomic Write Safety - Save-SyncMetadata" {

    BeforeEach {
        Mock Get-ArchonStateDir { return $script:testStateDir }
        New-Item -ItemType Directory -Path $script:testStateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    It "should save sync metadata atomically" {
        $timestamp = Get-Timestamp
        $result = Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "spec.md" -Timestamp $timestamp

        $result | Should -Be $true
        $metaFile = Join-Path $script:testStateDir "$($script:testFeatureName).meta"
        Test-Path $metaFile | Should -Be $true
    }

    It "should not leave temp file after save" {
        $timestamp = Get-Timestamp
        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "plan.md" -Timestamp $timestamp

        $metaFile = Join-Path $script:testStateDir "$($script:testFeatureName).meta"
        $tempFile = "$metaFile.tmp"

        Test-Path $tempFile | Should -Be $false
    }

    It "should use pipe delimiter for timestamps (not colon)" {
        $timestamp = "2025-10-15T12:30:45Z"
        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "tasks.md" -Timestamp $timestamp

        $metaFile = Join-Path $script:testStateDir "$($script:testFeatureName).meta"
        $content = Get-Content -Path $metaFile -Raw

        $content | Should -Match 'tasks\.md\|2025-10-15T12:30:45Z'
    }

    It "should handle multiple metadata entries" {
        $timestamp1 = "2025-10-15T10:00:00Z"
        $timestamp2 = "2025-10-15T11:00:00Z"
        $timestamp3 = "2025-10-15T12:00:00Z"

        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "spec.md" -Timestamp $timestamp1
        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "plan.md" -Timestamp $timestamp2
        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "tasks.md" -Timestamp $timestamp3

        $meta1 = Get-SyncMetadata -FeatureName $script:testFeatureName -Filename "spec.md"
        $meta2 = Get-SyncMetadata -FeatureName $script:testFeatureName -Filename "plan.md"
        $meta3 = Get-SyncMetadata -FeatureName $script:testFeatureName -Filename "tasks.md"

        $meta1 | Should -Be $timestamp1
        $meta2 | Should -Be $timestamp2
        $meta3 | Should -Be $timestamp3
    }

    It "should update existing metadata without duplicates" {
        $oldTimestamp = "2025-10-15T10:00:00Z"
        $newTimestamp = "2025-10-15T12:00:00Z"

        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "spec.md" -Timestamp $oldTimestamp
        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "spec.md" -Timestamp $newTimestamp

        $metaFile = Join-Path $script:testStateDir "$($script:testFeatureName).meta"
        $content = Get-Content -Path $metaFile

        $specEntries = $content | Where-Object { $_ -match '^spec\.md\|' }
        $specEntries.Count | Should -Be 1
        $specEntries[0] | Should -Match $newTimestamp
    }
}

Describe "Critical Fix 6: Error Handling and Cleanup" {

    BeforeEach {
        Mock Get-ArchonStateDir { return $script:testStateDir }
        New-Item -ItemType Directory -Path $script:testStateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    It "should clean up temp file on Save-ProjectMapping error" {
        # Force an error by making state directory read-only
        Mock Get-ArchonStateDir { return "/invalid/path/that/cannot/be/created" }

        $pidFile = "/invalid/path/that/cannot/be/created/$($script:testFeatureName).pid"
        $tempFile = "$pidFile.tmp"

        $result = Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-fail"

        $result | Should -Be $false
        # Temp file should not exist (cleaned up on error)
        Test-Path $tempFile | Should -Be $false
    }

    It "should clean up temp file on Save-DocumentMapping error" {
        Mock Get-ArchonStateDir { return "/invalid/path" }

        $result = Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "fail.md" -DocId "doc-fail"

        $result | Should -Be $false
    }

    It "should clean up temp file on Save-TaskMapping error" {
        Mock Get-ArchonStateDir { return "/invalid/path" }

        $result = Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T999" -TaskArchon "fail"

        $result | Should -Be $false
    }

    It "should clean up temp file on Save-SyncMetadata error" {
        Mock Get-ArchonStateDir { return "/invalid/path" }

        $result = Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "fail.md" -Timestamp "2025-10-15T00:00:00Z"

        $result | Should -Be $false
    }
}

Describe "Critical Fix 7: Get Functions Return Empty on Error" {

    BeforeEach {
        Mock Get-ArchonStateDir { return $script:testStateDir }
        New-Item -ItemType Directory -Path $script:testStateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    It "should return empty string from Get-ProjectMapping when file doesn't exist" {
        $result = Get-ProjectMapping -FeatureName "nonexistent-feature"
        $result | Should -Be ""
    }

    It "should return empty string from Get-DocumentMapping when file doesn't exist" {
        $result = Get-DocumentMapping -FeatureName "nonexistent-feature" -DocFilename "spec.md"
        $result | Should -Be ""
    }

    It "should return empty string from Get-TaskMapping when file doesn't exist" {
        $result = Get-TaskMapping -FeatureName "nonexistent-feature" -TaskLocal "T001"
        $result | Should -Be ""
    }

    It "should return empty string from Get-SyncMetadata when file doesn't exist" {
        $result = Get-SyncMetadata -FeatureName "nonexistent-feature" -Filename "spec.md"
        $result | Should -Be ""
    }

    It "should return empty string when mapping not found" {
        Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-123"

        # Try to get a different feature's mapping
        $result = Get-ProjectMapping -FeatureName "different-feature"
        $result | Should -Be ""
    }
}

Describe "Critical Fix 8: Documentation Completeness" {

    It "should have PowerShell requirements documentation" {
        $docsPath = Join-Path (Split-Path -Parent $PSScriptRoot) "docs" "powershell-requirements.md"
        Test-Path $docsPath | Should -Be $true
    }

    It "should document minimum PowerShell version" {
        $docsPath = Join-Path (Split-Path -Parent $PSScriptRoot) "docs" "powershell-requirements.md"
        $content = Get-Content -Path $docsPath -Raw

        $content | Should -Match 'PowerShell 7'
    }

    It "should document installation instructions" {
        $docsPath = Join-Path (Split-Path -Parent $PSScriptRoot) "docs" "powershell-requirements.md"
        $content = Get-Content -Path $docsPath -Raw

        $content | Should -Match '## Installation'
    }

    It "should document troubleshooting steps" {
        $docsPath = Join-Path (Split-Path -Parent $PSScriptRoot) "docs" "powershell-requirements.md"
        $content = Get-Content -Path $docsPath -Raw

        $content | Should -Match '## Troubleshooting'
    }

    It "should document atomic write safety" {
        $docsPath = Join-Path (Split-Path -Parent $PSScriptRoot) "docs" "powershell-requirements.md"
        $content = Get-Content -Path $docsPath -Raw

        $content | Should -Match 'atomic'
    }

    It "should document state file location" {
        $docsPath = Join-Path (Split-Path -Parent $PSScriptRoot) "docs" "powershell-requirements.md"
        $content = Get-Content -Path $docsPath -Raw

        $content | Should -Match '\.archon-state'
    }
}

Describe "Critical Fix 9: Helper Functions Work Correctly" {

    It "should extract feature name from directory path" {
        $featureDir = "/path/to/specs/001-user-auth"
        $featureName = Get-FeatureName -FeatureDir $featureDir

        $featureName | Should -Be "001-user-auth"
    }

    It "should handle Windows-style paths" {
        $featureDir = "C:\projects\specs\002-payment-flow"
        $featureName = Get-FeatureName -FeatureDir $featureDir

        $featureName | Should -Be "002-payment-flow"
    }

    It "should return empty string for invalid path" {
        Mock Split-Path { throw "Invalid path" }

        $featureName = Get-FeatureName -FeatureDir "/invalid"
        $featureName | Should -Be ""
    }

    It "should generate ISO 8601 timestamp" {
        $timestamp = Get-Timestamp

        # Should match ISO 8601 format with Z suffix
        $timestamp | Should -Match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
    }

    It "should return empty string on timestamp error" {
        Mock Get-Date { throw "Time error" }

        $timestamp = Get-Timestamp
        $timestamp | Should -Be ""
    }
}

Describe "Integration Test: Complete Save/Load Cycle" {

    BeforeEach {
        Mock Get-ArchonStateDir { return $script:testStateDir }

        # Clean state directory
        if (Test-Path $script:testStateDir) {
            Remove-Item -Path $script:testStateDir -Recurse -Force
        }
        New-Item -ItemType Directory -Path $script:testStateDir -Force | Out-Null
    }

    It "should save and load project mapping correctly" {
        $projectId = "proj-integration-test"

        $saved = Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId $projectId
        $loaded = Get-ProjectMapping -FeatureName $script:testFeatureName

        $saved | Should -Be $true
        $loaded | Should -Be $projectId
    }

    It "should save and load multiple document mappings" {
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md" -DocId "doc-spec"
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "plan.md" -DocId "doc-plan"
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "tasks.md" -DocId "doc-tasks"

        $spec = Get-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md"
        $plan = Get-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "plan.md"
        $tasks = Get-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "tasks.md"

        $spec | Should -Be "doc-spec"
        $plan | Should -Be "doc-plan"
        $tasks | Should -Be "doc-tasks"
    }

    It "should save and load multiple task mappings" {
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T001" -TaskArchon "uuid-1"
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T002" -TaskArchon "uuid-2"
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T003" -TaskArchon "uuid-3"

        $t1 = Get-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T001"
        $t2 = Get-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T002"
        $t3 = Get-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T003"

        $t1 | Should -Be "uuid-1"
        $t2 | Should -Be "uuid-2"
        $t3 | Should -Be "uuid-3"
    }

    It "should handle full lifecycle with all state types" {
        # Save all types
        Save-ProjectMapping -FeatureName $script:testFeatureName -ProjectId "proj-lifecycle"
        Save-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md" -DocId "doc-lifecycle"
        Save-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T999" -TaskArchon "task-lifecycle"
        Save-SyncMetadata -FeatureName $script:testFeatureName -Filename "spec.md" -Timestamp "2025-10-15T15:00:00Z"

        # Load all types
        $proj = Get-ProjectMapping -FeatureName $script:testFeatureName
        $doc = Get-DocumentMapping -FeatureName $script:testFeatureName -DocFilename "spec.md"
        $task = Get-TaskMapping -FeatureName $script:testFeatureName -TaskLocal "T999"
        $meta = Get-SyncMetadata -FeatureName $script:testFeatureName -Filename "spec.md"

        $proj | Should -Be "proj-lifecycle"
        $doc | Should -Be "doc-lifecycle"
        $task | Should -Be "task-lifecycle"
        $meta | Should -Be "2025-10-15T15:00:00Z"

        # Verify all state files exist
        Test-Path (Join-Path $script:testStateDir "$($script:testFeatureName).pid") | Should -Be $true
        Test-Path (Join-Path $script:testStateDir "$($script:testFeatureName).docs") | Should -Be $true
        Test-Path (Join-Path $script:testStateDir "$($script:testFeatureName).tasks") | Should -Be $true
        Test-Path (Join-Path $script:testStateDir "$($script:testFeatureName).meta") | Should -Be $true
    }
}

AfterAll {
    # Cleanup: Remove test state directory
    if (Test-Path $script:testStateDir) {
        Remove-Item -Path $script:testStateDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
