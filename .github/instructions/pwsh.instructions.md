---
applyTo: '**/*.{ps1,psm1}'
description: PowerShell style guidelines for consistency across scripts and modules.
---

# PowerShell Style Guidelines

This document defines the PowerShell style guidelines for all PowerShell files in this repository. These rules follow PowerShell best practices, the One True Brace Style (OTBS), and community standards.

## Brace Style (OTBS - One True Brace Style)

- Opening braces on the same line as the statement (OTBS)
- Closing braces on their own line, aligned with the statement
- Use braces even for single-line statements in control structures
- No empty lines immediately after opening braces or before closing braces

**Good:**

```powershell
function Get-Example {
    param($Name)

    if ($Name) {
        Write-Output "Hello, $Name"
    } else {
        Write-Output "Hello, World"
    }
}

foreach ($item in $items) {
    Get-Item $item
}
```

**Bad:**

```powershell
function Get-Example
{
    # Opening brace should be on same line
}

if ($condition)
    Write-Output "Missing braces"

if ($condition) { Write-Output "All on one line" }
```

## Naming Conventions

### Functions and Cmdlets

- Use approved PowerShell verbs (Get, Set, New, Remove, etc.)
- Follow Verb-Noun naming pattern with PascalCase
- Use singular nouns
- Be specific and descriptive

**Good:**

```powershell
function Get-UserProfile { }
function Set-ConfigValue { }
function New-DatabaseConnection { }
function Remove-TempFile { }
```

**Bad:**

```powershell
function GetUser { }  # Missing hyphen
function get-user { }  # Wrong case
function Do-Something { }  # Non-standard verb
function Get-Users { }  # Should be singular unless always plural
```

### Parameters and Variables

- Use PascalCase for parameters and public variables
- Use camelCase for private/local variables
- Use descriptive names, avoid abbreviations unless well-known
- Prefix boolean variables with verbs like `is`, `has`, `should`
- Append 'At' 'In' 'On' for timestamp/location variables
- Use `$_` for pipeline variables
- Avoid using reserved words as names
- Avoid using automatic variables for custom variables
- Parameter and variable names can be alphanumeric and include underscores.
- The colon character `:` and `.` are significant in PowerShell syntax, if they are a part of text, they must be escaped (`).

**Good:**

```powershell
$userName = "John"
$isValid = $true
$hasPermission = $false
$totalCount = 0

param(
    [string]$ConfigPath,
    [switch]$Force
)
```

**Bad:**

```powershell
$usr = "John"  # Too abbreviated
$valid = $true  # Boolean should be $isValid
$TOTAL_COUNT = 0  # Wrong case style
```

### Constants

- Use PascalCase with descriptive names
- Mark as `[System.Management.Automation.Language.ReadOnlyAttribute]` or use `Set-Variable -Option ReadOnly`

**Good:**

```powershell
$MaxRetries = 3
$DefaultTimeout = 30
Set-Variable -Name ApiEndpoint -Value "https://api.example.com" -Option ReadOnly
```

## Parameters

- Always use `[OutputType()]`, `[CmdletBinding()]` and `param()` block at the top of functions
- Use parameter attributes for validation
- Provide meaningful parameter names with PascalCase
- Use type constraints for parameters.
- Have a space between the type and the parameter name
- Group mandatory parameters first
- Use `[switch]` for boolean flags that default to `$false`.
- Add help text with parameter descriptions (inside the param block)


**Good:**

```powershell
function Get-UserData {
    <#
        .SYNOPSIS
        Retrieves user data from the database.

        .DESCRIPTION
        Retrieves user data from the database.

        .EXAMPLE
        Get-UserData -UserId "12345" -IncludeDeleted
    #>
    [CmdletBinding()]
    param(
        # The unique identifier of the user.
        [Parameter(Mandatory, Position = 0)]
        [ValidateNotNullOrEmpty()]
        [string] $UserId,

        # Include deleted users in the results.
        [Parameter()]
        [switch] $IncludeDeleted
    )

    # Function body
}
```

**Bad:**

```powershell
function Get-UserData($id, $del) {
    # No param block, no types, unclear names
}
```

## Indentation and Whitespace

- Use 4 spaces for indentation (not tabs)
- No trailing whitespace at end of lines
- End files with a single newline character
- Use blank lines to separate logical blocks of code
- No blank lines immediately after opening braces or before closing braces
- One space after commas in arrays and parameters
- One space around operators (`=`, `+`, `-`, `-eq`, `-ne`, etc.)

**Good:**

```powershell
function Process-Data {
    <#
        ... Docs
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)]
        [ValidateNotNullOrEmpty()]
        [array] $Items
    )

    $results = @()

    foreach ($item in $Items) {
        $processed = Format-Item $item
        $results += $processed
    }

    return $results
}
```

**Bad:**

```powershell
function Process-Data{
    param($Items)

    $results=@()
    foreach($item in $Items){
        $processed=Format-Item $item
    $results+=$processed
    }

    return $results

}
```

## Comments

- Use `#` for single-line comments
- Use `<# ... #>` for multi-line comments and help documentation
- Place comments on their own line above the code they describe
- Use comment-based help for functions (`.SYNOPSIS`, `.DESCRIPTION`, `.EXAMPLE`)
- Put comment-based help first, inside the function body, before any code. This makes it cleaner to move, and collapse code.
- Do not use '.PARAMETER' for parameters in comment-based help, use inline comments instead inside the param block above
  each of the parameters.
- Each section of comment-based help should have a blank line between them.
- The comment-based help must be indented to align with the function definition.
- Keep comments up to date with code changes.
- The code should say what it is doing, comments should explain why.

**Good:**

```powershell
function New-UserAccount {
<#
    .SYNOPSIS
    Creates a new user account.

    .DESCRIPTION
    Creates a new user account with the specified username and email.
    Validates the email format before creation.

    .EXAMPLE
    New-UserAccount -UserName 'jdoe' -Email 'jdoe@example.com'

    Creates a new user account for jdoe with email jdoe@example.com.

    .LINK
    https://example.com/docs/New-UserAccount
#>
    [CmdletBinding()]
    param(
        # The username for the new account.
        [Parameter(Mandatory)]
        [string] $UserName,

        # The email address for the new account.
        [Parameter(Mandatory)]
        [string] $Email
    )

    # Validate email format before processing
    if ($Email -notmatch '^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$') {
        throw "Invalid email format"
    }

    # Create the user account
    New-Object PSObject -Property @{
        UserName = $UserName
        Email = $Email
    }
}
```

**Bad:**

```powershell
function New-UserAccount {
    param($UserName, $Email)
    # Check email
    if ($Email -notmatch '^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$') { throw "Invalid email format" }
    New-Object PSObject -Property @{UserName = $UserName; Email = $Email}  # Create user
}
```

## String Handling

- Use single quotes for strings that don't need variable expansion
- Use double quotes only for strings with variables or escape sequences
- Use here-strings (`@"..."@` or `@'...'@`) for multi-line strings
- Use `-f` operator or string interpolation for formatting
- Avoid string concatenation with `+` in loops (use arrays or StringBuilder)

**Good:**

```powershell
$name = 'John'
$greeting = "Hello, $name"
$path = 'C:\Temp\file.txt'
$message = "The value is: {0}" -f $value

$multiLine = @"
This is a
multi-line string
with variable: $name
"@
```

**Bad:**

```powershell
$name = "John"  # Should use single quotes (no variables)
$greeting = 'Hello, $name'  # Variable won't expand
$message = "The value is: " + $value  # Use formatting instead
```

## Control Structures

### If/Else Statements

- Always use braces, even for single statements
- Opening brace on same line (OTBS)
- Use `elseif` (one word) not `else if`
- One space before opening brace
- Comparison operators on separate lines for readability in complex conditions

**Good:**

```powershell
if ($condition) {
    Do-Something
} elseif ($otherCondition) {
    Do-SomethingElse
} else {
    Do-Default
}

# Complex condition
if ($user.IsActive -and
    $user.HasPermission -and
    $user.Age -gt 18) {
    Grant-Access
}
```

**Bad:**

```powershell
if ($condition)
{  # Brace should be on same line
    Do-Something
}

if ($condition) Do-Something  # Missing braces

if($condition){  # Missing spaces
    Do-Something
}
```

### Loops

- Use appropriate loop construct (foreach, for, while, do-while)
- Always use braces
- Opening brace on same line (OTBS)
- Prefer `foreach` for collections over `for` when index not needed

**Good:**

```powershell
foreach ($item in $collection) {
    Process-Item $item
}

for ($i = 0; $i -lt $count; $i++) {
    Process-Index $i
}

while ($condition) {
    Update-Condition
}
```

**Bad:**

```powershell
foreach ($item in $collection)
{  # Brace should be on same line
    Process-Item $item
}

foreach ($item in $collection) Process-Item $item  # Missing braces
```

### Switch Statements

- Opening brace on same line
- Indent case statements by 4 spaces
- Use `break` or `continue` explicitly when needed
- Use `default` for fallback cases

**Good:**

```powershell
switch ($value) {
    'Option1' {
        Do-FirstThing
    }
    'Option2' {
        Do-SecondThing
    }
    default {
        Do-DefaultThing
    }
}
```

## Error Handling

- Use try/catch/finally blocks for error handling
- Be specific with catch blocks (catch specific exception types)
- Always provide meaningful error messages
- Use `throw` for unrecoverable errors
- Use `Write-Error` for non-terminating errors
- Set `$ErrorActionPreference` appropriately

**Good:**

```powershell
function Get-FileContent {
    param([string]$Path)

    try {
        if (-not (Test-Path $Path)) {
            throw "File not found: $Path"
        }

        $content = Get-Content -Path $Path -ErrorAction Stop
        return $content
    } catch [System.IO.IOException] {
        Write-Error "IO error reading file: $_"
        throw
    } catch {
        Write-Error "Unexpected error: $_"
        throw
    } finally {
        # Cleanup code here
    }
}
```

**Bad:**

```powershell
function Get-FileContent {
    param([string]$Path)

    try {
        Get-Content -Path $Path
    } catch {
        # Swallowing errors silently
    }
}
```

## Output and Logging

- Use `Write-Output` for function return values (or implicit return)
- Avoid `Write-Host` use `Write-Information` or `Write-Output` instead.
- Use `Write-Verbose` for detailed operation information
- Use `Write-Debug` for debugging information
- Use `Write-Warning` for warnings
- Use `Write-Error` for errors
- Use `Write-Information` for informational messages (PS 5.0+)

**Good:**

```powershell
function Get-ProcessedData {
    [CmdletBinding()]
    param($Data)

    Write-Verbose "Processing $($Data.Count) items"

    $result = Process-Data $Data

    if ($result.Warnings) {
        Write-Warning "Processing completed with warnings"
    }

    Write-Output $result
}
```

**Bad:**

```powershell
function Get-ProcessedData {
    param($Data)

    Write-Host "Processing data..."  # Should use Write-Verbose

    $result = Process-Data $Data

    Write-Host $result  # Should use Write-Output
}
```

## Pipeline

- Design functions to accept pipeline input when appropriate
- Use `[Parameter(ValueFromPipeline = $true)]` for pipeline parameters
- Implement `process` block for pipeline-aware functions
- Use `begin` and `end` blocks when initialization or cleanup needed

**Good:**

```powershell
function Update-Item {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [PSCustomObject]$Item
    )

    begin {
        $count = 0
    }

    process {
        # Process each item from pipeline
        $Item.LastModified = Get-Date
        $count++
        Write-Output $Item
    }

    end {
        Write-Verbose "Processed $count items"
    }
}

# Usage
$items | Update-Item
```

## Arrays and Hashtables

- Use `@()` for empty arrays
- Use `@{}` for empty hashtables
- Use consistent formatting for multi-line collections
- One item per line for readability in multi-line collections
- Trailing comma optional but allowed on last item
- Align key-value pairs in hashtables for readability
- Use splatting for functions with many parameters

**Good:**

```powershell
$emptyArray = @()
$numbers = @(1, 2, 3, 4, 5)

$multiLineArray = @(
    'First item'
    'Second item'
    'Third item'
)

$hashtable = @{
    Name = 'John'
    Age  = 30
    City = 'Seattle'
}

$complexHash = @{
    Server = @{
        Name = 'WebServer01'
        Port = 8080
    }
    Database = @{
        Name = 'MainDB'
        Port = 5432
    }
}
```

**Bad:**

```powershell
$array = 1, 2, 3, 4, 5  # Use @() syntax

$hashtable = @{Name = 'John'; Age = 30; City = 'Seattle'}  # Multi-line for readability
```

## Splatting

- Use splatting for functions with many parameters
- Create hashtable with parameters before splatting
- Use `@` symbol for splatting (not `$`)

**Good:**

```powershell
$params = @{
    Path        = 'C:\Temp'
    Filter      = '*.txt'
    Recurse     = $true
    ErrorAction = 'Stop'
}

Get-ChildItem @params
```

**Bad:**

```powershell
Get-ChildItem -Path 'C:\Temp' -Filter '*.txt' -Recurse $true -ErrorAction 'Stop'
```

## Comparison Operators

- Use PowerShell comparison operators (`-eq`, `-ne`, `-gt`, `-lt`, `-ge`, `-le`)
- Don't use C-style operators (`==`, `!=`, `>`, `<`)
- Use `-like` for wildcard matching, `-match` for regex
- Use `-contains` for collection membership, not `-eq`
- Add `-i` prefix for case-insensitive (default) or `-c` for case-sensitive
- Caution with $null comparisons. Comparison order is important depending if the variable is a single item or a collection.
  - `$null -eq $var` is usually safer for collections as it won't error if $var is $null or empty.

**Good:**

```powershell
if ($value -eq 10) { }
if ($name -like 'John*') { }
if ($email -match '^[\w-\.]+@') { }
if ($list -contains $item) { }
if ($name -ceq 'JOHN') { }  # Case-sensitive
if ($null -eq $collection) { }  # Safe null check for collections
```

**Bad:**

```powershell
if ($value == 10) { }  # Wrong operator
if ($list -eq $item) { }  # Use -contains for collections
if ($collection -eq $null) { }  # Can error if $collection is $null or empty
```

## Script Structure

- Use `#Requires` statements at the top for version/module requirements
- Place param block after `#Requires` and comment-based help
- Group related functions together
- Separate sections with comments
- End script with single newline

**Good:**

```powershell
#Requires -Version 7.4

<#
    .SYNOPSIS
    Script for managing user accounts.

    .DESCRIPTION
    This script provides functions to create, update, and delete user accounts.
#>

[CmdletBinding()]
param(
    [string]$ConfigPath = ".\config.json"
)

# Script-level variables
$ErrorActionPreference = 'Stop'

#region Helper functions
function Get-ConfigData {
    param([string]$Path)
    # Implementation
}

function New-UserAccount {
    param($UserName, $Email)
    # Implementation
}
#endregion

# Script execution
try {
    $config = Get-ConfigData -Path $ConfigPath
    # Main logic
} catch {
    Write-Error "Script failed: $_"
    exit 1
}
```

## Performance Considerations

- Avoid `Write-Host` in production scripts, instead use `Write-Information`
- Use `ArrayList` collection instead of `@()` arrays in loops.
- Use `-Filter` parameter instead of piping to `Where-Object` when available
- Avoid unnecessary pipeline operations
- Use `.ForEach()` and `.Where()` methods for better performance on large collections

**Good:**

```powershell
# Efficient array building
$results = [System.Collections.Generic.List[PSObject]]::new()
foreach ($item in $collection) {
    $results.Add($processedItem)
}

# Efficient filtering
Get-ChildItem -Path C:\Temp -Filter *.txt

# Method syntax for performance
$filtered = $collection.Where({ $_.Value -gt 10 })
```

**Bad:**

```powershell
# Inefficient array building
$results = @()
foreach ($item in $collection) {
    $results += $processedItem  # Creates new array each iteration
}

# Inefficient filtering
Get-ChildItem -Path C:\Temp | Where-Object { $_.Name -like '*.txt' }
```

## Line Length

- Wrap lines at 100-120 characters
- Use backtick (`` ` ``) for line continuation (sparingly), prefer splatting
- Prefer breaking at natural points (after commas, operators, pipes)
- Align continued lines for readability

**Good:**

```powershell
$result = Get-Something -Parameter1 $value1 `
    -Parameter2 $value2 `
    -Parameter3 $value3

# Better: Use splatting
$params = @{
    Parameter1 = $value1
    Parameter2 = $value2
    Parameter3 = $value3
}
$result = Get-Something @params
```

## Testing

- Write Pester tests for all functions
- Name test files `*.Tests.ps1`
- Group tests with `Describe` and `Context` blocks
- Use `It` blocks for individual test cases
- Use `Should` assertions
- Use `BeforeAll` and `AfterAll` for setup/teardown

**Good:**

```powershell
Describe 'Get-UserAccount' {
    Context 'When user exists' {
        It 'Should return user object' {
            $result = Get-UserAccount -UserId '123'
            $result | Should -Not -BeNullOrEmpty
            $result.UserId | Should -Be '123'
        }
    }

    Context 'When user does not exist' {
        It 'Should throw error' {
            { Get-UserAccount -UserId '999' } | Should -Throw
        }
    }
}
```

## Security Best Practices

- Never hardcode credentials or secrets
- Use `SecureString` for sensitive data
- Use `Get-Credential` for credential prompts
- Validate all user input
- Use `-WhatIf` and `-Confirm` for destructive operations
- Avoid `Invoke-Expression` with user input

**Good:**

```powershell
function Remove-UserData {
    [CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$UserId
    )

    if ($PSCmdlet.ShouldProcess($UserId, "Remove user data")) {
        # Perform deletion
    }
}

# Get credentials securely
$cred = Get-Credential -Message "Enter admin credentials"
```

**Bad:**

```powershell
$password = "MyPassword123"  # Hardcoded password
Invoke-Expression $userInput  # Security risk
```

## Related Resources

- [PowerShell Practice and Style Guide](https://poshcode.gitbook.io/powershell-practice-and-style/)
- [PowerShell Best Practices](https://docs.microsoft.com/en-us/powershell/scripting/developer/cmdlet/cmdlet-development-guidelines)
- [PSScriptAnalyzer Rules](https://github.com/PowerShell/PSScriptAnalyzer)
