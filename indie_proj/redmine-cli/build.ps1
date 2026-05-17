# Build script for redmine-cli on Windows

$ErrorActionPreference = "Stop"

$version = "1.0.0"
$outputDir = "bin"
$outputFile = Join-Path $outputDir "red-cli.exe"

Write-Host "Building redmine-cli version $version..." -ForegroundColor Green

# Clean old build
if (Test-Path $outputDir) {
    Write-Host "Cleaning old build..." -ForegroundColor Yellow
    Remove-Item $outputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $outputDir | Out-Null

# Get current commit hash for version info
try {
    $commitHash = git rev-parse --short HEAD
    $buildDate = Get-Date -Format "yyyy-MM-dd"
    $ldflags = "-X 'main.Version=$version' -X 'main.Commit=$commitHash' -X 'main.BuildDate=$buildDate'"
} catch {
    $ldflags = "-X 'main.Version=$version'"
}

# Build Windows AMD64 executable
Write-Host "Building Windows AMD64 executable..." -ForegroundColor Yellow
go build -ldflags "$ldflags" -trimpath -o $outputFile ./cmd/red-cli/

# Verify the build
if (Test-Path $outputFile) {
    $fileSize = (Get-Item $outputFile).Length / 1MB
    Write-Host "Build complete!" -ForegroundColor Green
    Write-Host "  Output: $outputFile" -ForegroundColor Cyan
    Write-Host "  Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan

    # Try to get version
    try {
        $versionOutput = & $outputFile --version 2>&1
        Write-Host "  Version: $versionOutput" -ForegroundColor Cyan
    } catch {
        Write-Host "  Version: Unable to retrieve" -ForegroundColor Yellow
    }
} else {
    Write-Error "Build failed - output file not found"
    exit 1
}