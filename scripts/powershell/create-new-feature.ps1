function Get-NextBranchNumber {
    param(
        [string]$SpecsDir
    )

    $remoteBranches = $remoteRefs | Where-Object { $_ -match "refs/heads/(\d{3})-" } | ForEach-Object {
        if ($_ -match "refs/heads/(\d{3})-") {
            # Your existing logic here
        }
    }

    $localBranches = $allBranches | Where-Object { $_ -match "^\*?\s*(\d{3})-" } | ForEach-Object {
        if ($_ -match "(\d{3})-") {
            # Your existing logic here
        }
    }

    $specDirs = Get-ChildItem -Path $SpecsDir -Directory | Where-Object { $_.Name -match "^(\d{3})-" } | ForEach-Object {
        if ($_.Name -match "^(\d{3})-") {
            # Your existing logic here
        }
    }

    $Number = Get-NextBranchNumber -SpecsDir $specsDir
    return $Number
}