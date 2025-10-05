param([switch]$Json)

$RepoRoot = git rev-parse --show-toplevel
$DocsDir = Join-Path $RepoRoot "docs"
New-Item -ItemType Directory -Force -Path $DocsDir | Out-Null

$Template = Join-Path $RepoRoot "templates\product-vision-template.md"
$ProductVisionFile = Join-Path $DocsDir "product-vision.md"

if (Test-Path $Template) {
    Copy-Item $Template $ProductVisionFile
} else {
    New-Item -ItemType File -Path $ProductVisionFile | Out-Null
}

if ($Json) {
    @{PRODUCT_VISION_FILE=$ProductVisionFile} | ConvertTo-Json -Compress
} else {
    Write-Output "PRODUCT_VISION_FILE: $ProductVisionFile"
}
