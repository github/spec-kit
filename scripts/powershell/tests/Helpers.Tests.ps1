Import-Module Pester

Describe 'PowerShell helper scripts' {
    BeforeAll {
        $script:testRoot = if ($PSScriptRoot) { $PSScriptRoot } elseif ($PSCommandPath) { Split-Path -Parent $PSCommandPath } else { (Get-Location).Path }
        $script:repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $script:testRoot))
        $script:featureName = '999-test-feature'
        $script:featureDir = Join-Path $script:repoRoot "specs/$script:featureName"
        $script:planPath = Join-Path $script:featureDir 'plan.md'
        $script:specPath = Join-Path $script:featureDir 'spec.md'

        New-Item -ItemType Directory -Path (Split-Path $script:featureDir -Parent) -Force | Out-Null
        New-Item -ItemType Directory -Path $script:featureDir -Force | Out-Null
        Set-Content -LiteralPath $script:specPath -Value '# Temporary spec'
    }

    AfterAll {
        if (Test-Path $script:featureDir) { Remove-Item -Path $script:featureDir -Recurse -Force }
        Remove-Item Env:SPECIFY_FEATURE -ErrorAction SilentlyContinue
    }

    BeforeEach {
        Set-Content -LiteralPath $script:planPath -Value '# Temporary plan'
        $env:SPECIFY_FEATURE = $script:featureName
    }

    Context 'check-prerequisites.ps1' {
        It 'emits compact JSON when using -Json -PathsOnly' {
            $result = & pwsh -NoLogo -NoProfile -File (Join-Path $script:repoRoot 'scripts/powershell/check-prerequisites.ps1') -Json -PathsOnly
            $parsed = $result | ConvertFrom-Json
            $parsed.FEATURE_DIR | Should -Be $script:featureDir
            $parsed.FEATURE_SPEC | Should -Be (Join-Path $script:featureDir 'spec.md')
        }

        It 'returns structured JSON errors when plan is missing' {
            Remove-Item -LiteralPath $script:planPath -Force
            $result = & pwsh -NoLogo -NoProfile -File (Join-Path $script:repoRoot 'scripts/powershell/check-prerequisites.ps1') -Json 2>$null
            $parsed = $result | ConvertFrom-Json
            $parsed.status | Should -Be 'error'
            $parsed.message | Should -Match 'plan.md'
        }
    }

    Context 'setup-plan.ps1' {
        It 'copies template and emits JSON when -Json is specified' {
            Remove-Item -LiteralPath $script:planPath -Force -ErrorAction SilentlyContinue
            $result = & pwsh -NoLogo -NoProfile -File (Join-Path $script:repoRoot 'scripts/powershell/setup-plan.ps1') -Json
            $parsed = $result | ConvertFrom-Json
            $parsed.IMPL_PLAN | Should -Be $script:planPath
            Test-Path $script:planPath | Should -BeTrue
        }
    }
}
