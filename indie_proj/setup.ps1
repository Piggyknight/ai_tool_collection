# One-click setup script for OpenSpec + Redmine development environment

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OpenSpec + Redmine Dev Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the indie_proj directory
$pwd = Get-Location
if ($pwd.Name -ne "indie_proj") {
    Write-Warning "Not in indie_proj directory. Please navigate to indie_proj and run this script."
    exit 1
}

# Step 1: Build redmine-cli
Write-Host "Step 1: Building redmine-cli..." -ForegroundColor Green
if (Test-Path "redmine-cli") {
    Set-Location redmine-cli
    if (Test-Path "build.ps1") {
        & .\build.ps1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to build redmine-cli"
            Set-Location $pwd
            exit 1
        }
        Write-Host "  redmine-cli built successfully!" -ForegroundColor Green
    } else {
        Write-Warning "  build.ps1 not found, skipping redmine-cli build"
    }
    Set-Location $pwd
} else {
    Write-Warning "  redmine-cli directory not found, skipping"
}

# Step 2: Check Node.js
Write-Host "Step 2: Checking Node.js..." -ForegroundColor Green
try {
    $nodeVersion = node --version
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Cyan
} catch {
    Write-Error "Node.js not found. Please install Node.js >= 20.19.0"
    exit 1
}

# Step 3: Build OpenSpec
Write-Host "Step 3: Building OpenSpec..." -ForegroundColor Green
if (Test-Path "openspec-cn") {
    Set-Location openspec-cn
    if (Test-Path "package.json") {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "  Installing dependencies..." -ForegroundColor Yellow
            pnpm install
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install dependencies"
                Set-Location $pwd
                exit 1
            }
        }

        # Build
        Write-Host "  Building OpenSpec..." -ForegroundColor Yellow
        pnpm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to build OpenSpec"
            Set-Location $pwd
            exit 1
        }
        Write-Host "  OpenSpec built successfully!" -ForegroundColor Green
    } else {
        Write-Warning "  package.json not found, skipping OpenSpec build"
    }
    Set-Location $pwd
} else {
    Write-Warning "  openspec-cn directory not found, skipping"
}

# Step 4: Setup PATH
Write-Host "Step 4: Setting up PATH..." -ForegroundColor Green
$redminePath = Join-Path $pwd "redmine-cli\bin\red-cli.exe"
$openspecPath = Join-Path $pwd "openspec-cn\bin\openspec.js"

if (Test-Path $redminePath) {
    Write-Host "  redmine-cli: $redminePath" -ForegroundColor Cyan
} else {
    Write-Warning "  redmine-cli not built yet"
}

if (Test-Path $openspecPath) {
    Write-Host "  openspec: $openspecPath" -ForegroundColor Cyan
} else {
    Write-Warning "  openspec not built yet"
}

# Step 5: Verify installations
Write-Host "Step 5: Verifying installations..." -ForegroundColor Green

if (Test-Path $redminePath) {
    try {
        & $redminePath --version
        Write-Host "  redmine-cli verified!" -ForegroundColor Green
    } catch {
        Write-Warning "  redmine-cli verification failed"
    }
}

if (Test-Path $openspecPath) {
    try {
        node $openspecPath --version
        Write-Host "  openspec verified!" -ForegroundColor Green
    } catch {
        Write-Warning "  openspec verification failed"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure Redmine: openspec redmine setup" -ForegroundColor White
Write-Host "2. Create your first sprint: openspec sprint create my-sprint" -ForegroundColor White
Write-Host "3. Plan stories: openspec sprint plan my-sprint" -ForegroundColor White
Write-Host ""