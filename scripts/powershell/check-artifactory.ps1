#!/usr/bin/env pwsh

#
# check-artifactory.ps1 - Query Artifactory for library availability
#
# Usage:
#   ./check-artifactory.ps1 <artifactory-url> <library-name> [api-key]
#   ./check-artifactory.ps1 -ArtifactoryUrl <url> -LibraryName <name> [-ApiKey <key>]
#
# Returns:
#   Exit 0: Library found (prints download URL)
#   Exit 1: Library not found
#   Exit 2: Authentication error
#   Exit 3: API error (network, timeout, etc.)
#   Exit 4: Artifactory URL not configured (skip check)
#

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$ArtifactoryUrl = "",

    [Parameter(Mandatory=$false, Position=1)]
    [string]$LibraryName = "",

    [Parameter(Mandatory=$false, Position=2)]
    [string]$ApiKey = "",

    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: $($MyInvocation.MyCommand.Name) <artifactory-url> <library-name> [api-key]
       $($MyInvocation.MyCommand.Name) -ArtifactoryUrl <url> -LibraryName <name> [-ApiKey <key>]

Query Artifactory for library availability.

Parameters:
  ArtifactoryUrl    URL of the Artifactory instance (e.g., https://artifactory.company.com/api)
  LibraryName       Name of the library to check (e.g., axios, lodash, jackson-databind)
  ApiKey           Optional API key for authentication (or set ARTIFACTORY_API_KEY env var)
  -Help            Show this help message

Exit Codes:
  0  Library found (prints download URL)
  1  Library not found (not whitelisted)
  2  Authentication error
  3  API error (network, timeout, etc.)
  4  Artifactory URL not configured (skip check)

Examples:
  # Check if axios is available
  .\$($MyInvocation.MyCommand.Name) https://artifactory.company.com/api axios

  # With API key
  .\$($MyInvocation.MyCommand.Name) https://artifactory.company.com/api axios YOUR_API_KEY

  # Using named parameters
  .\$($MyInvocation.MyCommand.Name) -ArtifactoryUrl https://artifactory.company.com/api -LibraryName axios

  # Using environment variable for API key
  `$env:ARTIFACTORY_API_KEY = "YOUR_API_KEY"
  .\$($MyInvocation.MyCommand.Name) https://artifactory.company.com/api axios

  # Skip validation if URL not configured
  .\$($MyInvocation.MyCommand.Name) "Not configured" axios
"@
    exit 0
}

# Get from environment if not provided
if ($ArtifactoryUrl -eq "" -and $env:ARTIFACTORY_URL) {
    $ArtifactoryUrl = $env:ARTIFACTORY_URL
}

if ($ApiKey -eq "" -and $env:ARTIFACTORY_API_KEY) {
    $ApiKey = $env:ARTIFACTORY_API_KEY
}

# Function to print status with color
function Print-Status {
    param(
        [string]$Status,
        [string]$Message
    )

    switch ($Status) {
        "FOUND" {
            Write-Host "✅ FOUND: $Message" -ForegroundColor Green
        }
        "NOT_FOUND" {
            Write-Host "❌ NOT FOUND: $Message" -ForegroundColor Yellow
        }
        "SKIPPED" {
            Write-Host "⊘ SKIPPED: $Message" -ForegroundColor Yellow
        }
        "ERROR" {
            Write-Host "⚠️  ERROR: $Message" -ForegroundColor Red
        }
    }
}

# Validate inputs
if ($LibraryName -eq "") {
    Write-Error "ERROR: Library name is required"
    Write-Error "Usage: $($MyInvocation.MyCommand.Name) <artifactory-url> <library-name> [api-key]"
    exit 3
}

# Check if Artifactory URL is configured
if ($ArtifactoryUrl -eq "" -or $ArtifactoryUrl -eq "Not configured" -or $ArtifactoryUrl -eq "null") {
    Print-Status "SKIPPED" "Artifactory URL not configured - skipping validation for $LibraryName"
    exit 4
}

# Build API endpoint
$apiEndpoint = "${ArtifactoryUrl}/api/search/artifact?name=${LibraryName}"

try {
    # Prepare headers
    $headers = @{}
    if ($ApiKey -ne "") {
        $headers["X-JFrog-Art-Api"] = $ApiKey
    }

    # Query Artifactory with timeout
    $response = Invoke-WebRequest -Uri $apiEndpoint `
        -Headers $headers `
        -TimeoutSec 5 `
        -UseBasicParsing `
        -ErrorAction Stop

    $httpCode = $response.StatusCode
    $body = $response.Content

    # Handle successful response
    if ($httpCode -eq 200) {
        try {
            $jsonBody = $body | ConvertFrom-Json
            $resultsCount = $jsonBody.results.Count

            if ($resultsCount -gt 0) {
                $downloadUri = $jsonBody.results[0].downloadUri

                # Try to extract version from URI
                $version = "latest"
                if ($downloadUri -match '([\d\.]+)\.(jar|tar\.gz|zip|whl)') {
                    $version = $matches[1]
                }

                if ($version -ne "latest") {
                    Print-Status "FOUND" "${LibraryName}:${version} available in Artifactory"
                } else {
                    Print-Status "FOUND" "$LibraryName available in Artifactory"
                }

                Write-Output $downloadUri
                exit 0
            } else {
                Print-Status "NOT_FOUND" "$LibraryName not found in Artifactory"
                exit 1
            }
        } catch {
            # Fallback without JSON parsing - simple check
            if ($body -match "downloadUri") {
                Print-Status "FOUND" "$LibraryName available in Artifactory"
                Write-Output $body
                exit 0
            } else {
                Print-Status "NOT_FOUND" "$LibraryName not found in Artifactory"
                exit 1
            }
        }
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__

    if ($statusCode -eq 401 -or $statusCode -eq 403) {
        Print-Status "ERROR" "Authentication failed. Check ARTIFACTORY_API_KEY environment variable"
        exit 2
    } elseif ($null -eq $statusCode -or $statusCode -eq 0) {
        Print-Status "ERROR" "Network error or timeout (Artifactory may be unreachable)"
        exit 3
    } else {
        Print-Status "ERROR" "Artifactory API returned HTTP $statusCode"
        exit 3
    }
}
