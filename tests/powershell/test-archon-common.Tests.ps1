# Pester tests for archon-common.ps1
# Tests silent operation, state management, and cross-platform compatibility

BeforeAll {
    # Import the module under test
    $scriptPath = Join-Path $PSScriptRoot "..\..\scripts\powershell\archon-common.ps1"
    . $scriptPath

    # Create temporary test directory
    $script:testDir = Join-Path $TestDrive "archon-tests"
    New-Item -ItemType Directory -Path $script:testDir -Force | Out-Null
}

Describe "Test-ArchonAvailable" {
    It "Returns boolean value" {
        $result = Test-ArchonAvailable
        $result | Should -BeOfType [bool]
    }

    It "Operates silently (no output)" {
        $output = Test-ArchonAvailable | Out-String
        $output | Should -BeNullOrEmpty
    }

    It "Does not throw exceptions" {
        { Test-ArchonAvailable } | Should -Not -Throw
    }
}

Describe "Get-ArchonStateDir" {
    It "Returns a valid path" {
        $result = Get-ArchonStateDir
        $result | Should -Not -BeNullOrEmpty
        $result | Should -BeLike "*\.archon-state"
    }

    It "Returns consistent path on multiple calls" {
        $path1 = Get-ArchonStateDir
        $path2 = Get-ArchonStateDir
        $path1 | Should -Be $path2
    }
}

Describe "Save-ProjectMapping and Get-ProjectMapping" {
    BeforeEach {
        $script:featureName = "test-feature-$(Get-Random)"
        $script:projectId = "proj-$(New-Guid)"
    }

    It "Saves project mapping silently" {
        $result = Save-ProjectMapping -FeatureName $script:featureName -ProjectId $script:projectId
        $result | Should -Be $true
    }

    It "Retrieves saved project mapping" {
        Save-ProjectMapping -FeatureName $script:featureName -ProjectId $script:projectId
        $retrieved = Get-ProjectMapping -FeatureName $script:featureName
        $retrieved | Should -Be $script:projectId
    }

    It "Returns empty string for non-existent mapping" {
        $retrieved = Get-ProjectMapping -FeatureName "nonexistent-feature-$(Get-Random)"
        $retrieved | Should -BeNullOrEmpty
    }

    It "Handles special characters in feature name" {
        $specialName = "feature-with-spaces and-chars-$(Get-Random)"
        Save-ProjectMapping -FeatureName $specialName -ProjectId $script:projectId
        $retrieved = Get-ProjectMapping -FeatureName $specialName
        $retrieved | Should -Be $script:projectId
    }

    It "Overwrites existing mapping" {
        $newProjectId = "proj-$(New-Guid)"
        Save-ProjectMapping -FeatureName $script:featureName -ProjectId $script:projectId
        Save-ProjectMapping -FeatureName $script:featureName -ProjectId $newProjectId
        $retrieved = Get-ProjectMapping -FeatureName $script:featureName
        $retrieved | Should -Be $newProjectId
    }
}

Describe "Save-DocumentMapping and Get-DocumentMapping" {
    BeforeEach {
        $script:featureName = "test-feature-$(Get-Random)"
        $script:docFilename = "spec.md"
        $script:docId = "doc-$(New-Guid)"
    }

    It "Saves document mapping silently" {
        $result = Save-DocumentMapping -FeatureName $script:featureName -DocFilename $script:docFilename -DocId $script:docId
        $result | Should -Be $true
    }

    It "Retrieves saved document mapping" {
        Save-DocumentMapping -FeatureName $script:featureName -DocFilename $script:docFilename -DocId $script:docId
        $retrieved = Get-DocumentMapping -FeatureName $script:featureName -DocFilename $script:docFilename
        $retrieved | Should -Be $script:docId
    }

    It "Returns empty string for non-existent document" {
        $retrieved = Get-DocumentMapping -FeatureName $script:featureName -DocFilename "nonexistent.md"
        $retrieved | Should -BeNullOrEmpty
    }

    It "Handles multiple documents for same feature" {
        $doc1 = "spec.md"
        $doc2 = "plan.md"
        $docId1 = "doc-$(New-Guid)"
        $docId2 = "doc-$(New-Guid)"

        Save-DocumentMapping -FeatureName $script:featureName -DocFilename $doc1 -DocId $docId1
        Save-DocumentMapping -FeatureName $script:featureName -DocFilename $doc2 -DocId $docId2

        $retrieved1 = Get-DocumentMapping -FeatureName $script:featureName -DocFilename $doc1
        $retrieved2 = Get-DocumentMapping -FeatureName $script:featureName -DocFilename $doc2

        $retrieved1 | Should -Be $docId1
        $retrieved2 | Should -Be $docId2
    }

    It "Handles filenames with colons correctly" {
        $docWithColon = "file:with:colons.md"
        Save-DocumentMapping -FeatureName $script:featureName -DocFilename $docWithColon -DocId $script:docId
        $retrieved = Get-DocumentMapping -FeatureName $script:featureName -DocFilename $docWithColon
        $retrieved | Should -Be $script:docId
    }
}

Describe "Save-TaskMapping and Get-TaskMapping" {
    BeforeEach {
        $script:featureName = "test-feature-$(Get-Random)"
        $script:taskLocal = "T001"
        $script:taskArchon = "task-$(New-Guid)"
    }

    It "Saves task mapping silently" {
        $result = Save-TaskMapping -FeatureName $script:featureName -TaskLocal $script:taskLocal -TaskArchon $script:taskArchon
        $result | Should -Be $true
    }

    It "Retrieves saved task mapping" {
        Save-TaskMapping -FeatureName $script:featureName -TaskLocal $script:taskLocal -TaskArchon $script:taskArchon
        $retrieved = Get-TaskMapping -FeatureName $script:featureName -TaskLocal $script:taskLocal
        $retrieved | Should -Be $script:taskArchon
    }

    It "Returns empty string for non-existent task" {
        $retrieved = Get-TaskMapping -FeatureName $script:featureName -TaskLocal "T999"
        $retrieved | Should -BeNullOrEmpty
    }

    It "Handles multiple tasks for same feature" {
        $task1 = "T001"
        $task2 = "T002"
        $taskId1 = "task-$(New-Guid)"
        $taskId2 = "task-$(New-Guid)"

        Save-TaskMapping -FeatureName $script:featureName -TaskLocal $task1 -TaskArchon $taskId1
        Save-TaskMapping -FeatureName $script:featureName -TaskLocal $task2 -TaskArchon $taskId2

        $retrieved1 = Get-TaskMapping -FeatureName $script:featureName -TaskLocal $task1
        $retrieved2 = Get-TaskMapping -FeatureName $script:featureName -TaskLocal $task2

        $retrieved1 | Should -Be $taskId1
        $retrieved2 | Should -Be $taskId2
    }
}

Describe "Save-SyncMetadata and Get-SyncMetadata" {
    BeforeEach {
        $script:featureName = "test-feature-$(Get-Random)"
        $script:filename = "spec.md"
        $script:timestamp = "2025-10-15T12:34:56Z"
    }

    It "Saves sync metadata silently" {
        $result = Save-SyncMetadata -FeatureName $script:featureName -Filename $script:filename -Timestamp $script:timestamp
        $result | Should -Be $true
    }

    It "Retrieves saved sync metadata" {
        Save-SyncMetadata -FeatureName $script:featureName -Filename $script:filename -Timestamp $script:timestamp
        $retrieved = Get-SyncMetadata -FeatureName $script:featureName -Filename $script:filename
        $retrieved | Should -Be $script:timestamp
    }

    It "Returns empty string for non-existent metadata" {
        $retrieved = Get-SyncMetadata -FeatureName $script:featureName -Filename "nonexistent.md"
        $retrieved | Should -BeNullOrEmpty
    }

    It "Handles ISO 8601 timestamps with colons" {
        $timestampWithColons = "2025-10-15T12:34:56.789Z"
        Save-SyncMetadata -FeatureName $script:featureName -Filename $script:filename -Timestamp $timestampWithColons
        $retrieved = Get-SyncMetadata -FeatureName $script:featureName -Filename $script:filename
        $retrieved | Should -Be $timestampWithColons
    }

    It "Uses pipe delimiter to avoid timestamp colon conflicts" {
        $stateDir = Get-ArchonStateDir
        $metaFile = Join-Path $stateDir "${script:featureName}.meta"

        Save-SyncMetadata -FeatureName $script:featureName -Filename $script:filename -Timestamp $script:timestamp

        if (Test-Path $metaFile) {
            $content = Get-Content -Path $metaFile -Raw
            $content | Should -Match "\|"
            $content | Should -Not -Match "${script:filename}:${script:timestamp}"
        }
    }
}

Describe "Get-FeatureName" {
    It "Extracts feature name from absolute path" {
        $path = "/path/to/specs/001-feature-name"
        $result = Get-FeatureName -FeatureDir $path
        $result | Should -Be "001-feature-name"
    }

    It "Handles Windows paths" {
        $path = "C:\path\to\specs\001-feature-name"
        $result = Get-FeatureName -FeatureDir $path
        $result | Should -Be "001-feature-name"
    }

    It "Handles paths with trailing slashes" {
        $path = "/path/to/specs/001-feature-name/"
        $result = Get-FeatureName -FeatureDir $path
        # Split-Path -Leaf handles trailing slashes
        $result | Should -Not -BeNullOrEmpty
    }

    It "Returns empty string for invalid path" {
        $result = Get-FeatureName -FeatureDir ""
        $result | Should -BeNullOrEmpty
    }
}

Describe "Get-Timestamp" {
    It "Returns ISO 8601 format timestamp" {
        $result = Get-Timestamp
        $result | Should -Match "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    }

    It "Returns UTC timestamp" {
        $result = Get-Timestamp
        $result | Should -BeLike "*Z"
    }

    It "Returns consistent format on multiple calls" {
        $ts1 = Get-Timestamp
        Start-Sleep -Milliseconds 100
        $ts2 = Get-Timestamp

        $ts1 | Should -Match "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        $ts2 | Should -Match "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        $ts2 | Should -Not -Be $ts1  # Time should have advanced
    }
}

Describe "Silent Operation Validation" {
    It "All functions suppress errors silently" {
        # Test with invalid inputs - should not throw or output
        $output = @()

        $output += Save-ProjectMapping -FeatureName "" -ProjectId "" 2>&1
        $output += Get-ProjectMapping -FeatureName "" 2>&1
        $output += Save-DocumentMapping -FeatureName "" -DocFilename "" -DocId "" 2>&1
        $output += Get-DocumentMapping -FeatureName "" -DocFilename "" 2>&1
        $output += Save-TaskMapping -FeatureName "" -TaskLocal "" -TaskArchon "" 2>&1
        $output += Get-TaskMapping -FeatureName "" -TaskLocal "" 2>&1
        $output += Save-SyncMetadata -FeatureName "" -Filename "" -Timestamp "" 2>&1
        $output += Get-SyncMetadata -FeatureName "" -Filename "" 2>&1

        # Should produce no error output
        $errorOutput = $output | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] }
        $errorOutput | Should -BeNullOrEmpty
    }
}

Describe "Cross-Platform Compatibility" {
    It "State directory path uses correct separators" {
        $stateDir = Get-ArchonStateDir
        # Should work on both Windows and Unix
        Test-Path (Split-Path $stateDir -Parent) -IsValid | Should -Be $true
    }

    It "File operations work with platform-specific paths" {
        $featureName = "cross-platform-test-$(Get-Random)"
        $projectId = "proj-$(New-Guid)"

        Save-ProjectMapping -FeatureName $featureName -ProjectId $projectId
        $retrieved = Get-ProjectMapping -FeatureName $featureName

        $retrieved | Should -Be $projectId
    }
}
