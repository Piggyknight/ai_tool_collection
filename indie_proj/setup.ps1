# One-click setup script for OpenSpec + Redmine development environment

param(
    [string[]]$ProjectDirs = @(),
    [string[]]$Workspaces = @(),
    [string]$RedmineConfigDir = "",
    [string]$InstanceName = "default",
    [string]$RedmineServer = "",
    [string]$RedmineApiKey = "",
    [int]$RedmineProjectId = 0,
    [string]$OpenSpecTools = "codex",
    [switch]$LinkUserRedConfig,
    [switch]$ForceLinks,
    [switch]$ForceOpenSpecConfig,
    [switch]$AddToUserPath,
    [switch]$NonInteractive,
    [switch]$SkipBuild,
    [switch]$SkipProjectInit,
    [switch]$SkipOpenSpecConfig
)

$ErrorActionPreference = "Stop"

function Resolve-SetupPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $initialDir $Path))
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "  Created: $Path" -ForegroundColor Cyan
    }
}

function Read-YesNo {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [bool]$Default = $true
    )

    $suffix = if ($Default) { "[Y/n]" } else { "[y/N]" }
    $answer = Read-Host "$Message $suffix"
    if ([string]::IsNullOrWhiteSpace($answer)) {
        return $Default
    }

    return $answer.Trim().ToLowerInvariant().StartsWith("y")
}

function Read-SecretText {
    param([Parameter(Mandatory = $true)][string]$Message)

    $secure = Read-Host $Message -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Test-ReparsePoint {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    $item = Get-Item -LiteralPath $Path -Force
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Get-LinkTarget {
    param([Parameter(Mandatory = $true)][string]$Path)

    $item = Get-Item -LiteralPath $Path -Force
    if ($null -ne $item.Target) {
        return [System.IO.Path]::GetFullPath($item.Target)
    }

    return ""
}

function Backup-ExistingPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $backupPath = "$Path.backup-$timestamp"
    Move-Item -LiteralPath $Path -Destination $backupPath
    Write-Warning "  Existing path moved to: $backupPath"
}

function Ensure-DirectorySymlink {
    param(
        [Parameter(Mandatory = $true)][string]$LinkPath,
        [Parameter(Mandatory = $true)][string]$TargetPath
    )

    $fullTarget = [System.IO.Path]::GetFullPath($TargetPath)

    if (Test-Path -LiteralPath $LinkPath) {
        if (Test-ReparsePoint $LinkPath) {
            $currentTarget = Get-LinkTarget $LinkPath
            if ($currentTarget -and ([System.IO.Path]::GetFullPath($currentTarget) -eq $fullTarget)) {
                Write-Host "  Link exists: $LinkPath -> $fullTarget" -ForegroundColor Cyan
                return
            }

            if (-not $ForceLinks) {
                Write-Warning "  Link exists with different target, skipping: $LinkPath"
                Write-Warning "    Current: $currentTarget"
                Write-Warning "    Wanted : $fullTarget"
                Write-Warning "    Re-run with -ForceLinks to replace it."
                return
            }

            Remove-Item -LiteralPath $LinkPath -Force
        } else {
            $existingFullPath = [System.IO.Path]::GetFullPath($LinkPath)
            if ($existingFullPath -eq $fullTarget) {
                Write-Host "  Using central Redmine config directory: $LinkPath" -ForegroundColor Cyan
                return
            }

            $hasContent = $false
            if ((Get-Item -LiteralPath $LinkPath -Force).PSIsContainer) {
                $hasContent = $null -ne (Get-ChildItem -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue | Select-Object -First 1)
            }

            if ($hasContent -and -not $ForceLinks) {
                Write-Warning "  Existing directory is not a link, skipping: $LinkPath"
                Write-Warning "    Re-run with -ForceLinks to back it up and create the link."
                return
            }

            if ($hasContent) {
                Backup-ExistingPath $LinkPath
            } else {
                Remove-Item -LiteralPath $LinkPath -Force
            }
        }
    }

    try {
        New-Item -ItemType SymbolicLink -Path $LinkPath -Target $fullTarget | Out-Null
        Write-Host "  Linked: $LinkPath -> $fullTarget" -ForegroundColor Green
    } catch {
        Write-Warning "  Failed to create symlink, trying directory junction: $LinkPath -> $fullTarget"
        try {
            New-Item -ItemType Junction -Path $LinkPath -Target $fullTarget | Out-Null
            Write-Host "  Junction linked: $LinkPath -> $fullTarget" -ForegroundColor Green
        } catch {
            Write-Warning "  Failed to create link: $LinkPath -> $fullTarget"
            Write-Warning "  $_"
            Write-Warning "  Enable Windows Developer Mode or run PowerShell as Administrator, then re-run setup."
        }
    }
}

function ConvertTo-YamlSingleQuoted {
    param([Parameter(Mandatory = $true)][string]$Value)
    return "'" + ($Value -replace "'", "''") + "'"
}

function Invoke-InteractiveConfiguration {
    if ($NonInteractive) {
        return
    }

    Write-Host "Interactive configuration" -ForegroundColor Green

    if ($ProjectDirs.Count -eq 0 -and $Workspaces.Count -eq 0) {
        $projectInput = Read-Host "Project directories to initialize and link to ~/.red (comma-separated, empty = this directory)"
        if (-not [string]::IsNullOrWhiteSpace($projectInput)) {
            $script:ProjectDirs = @($projectInput.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        }
    }

    if (-not $SkipOpenSpecConfig -and -not ($RedmineServer -and $RedmineApiKey -and $RedmineProjectId -gt 0)) {
        if (Read-YesNo "Configure Redmine now?" $true) {
            $instanceInput = Read-Host "Instance name (empty = $InstanceName)"
            if (-not [string]::IsNullOrWhiteSpace($instanceInput)) {
                $script:InstanceName = $instanceInput.Trim()
            }

            while ([string]::IsNullOrWhiteSpace($script:RedmineServer)) {
                $script:RedmineServer = (Read-Host "Redmine server URL").Trim()
            }

            while ([string]::IsNullOrWhiteSpace($script:RedmineApiKey)) {
                $script:RedmineApiKey = Read-SecretText "Redmine API key"
            }

            while ($script:RedmineProjectId -le 0) {
                $projectIdInput = Read-Host "Redmine project ID"
                $projectId = 0
                if ([int]::TryParse($projectIdInput, [ref]$projectId) -and $projectId -gt 0) {
                    $script:RedmineProjectId = $projectId
                } else {
                    Write-Warning "  Please enter a positive integer project ID."
                }
            }
        } else {
            $script:SkipOpenSpecConfig = $true
        }
    }

    if (-not $AddToUserPath) {
        $script:AddToUserPath = Read-YesNo "Add local command shims to your user PATH?" $true
    }

    if (-not $SkipProjectInit) {
        $toolsInput = Read-Host "OpenSpec tools for project init (codex/all/none/comma list, empty = $OpenSpecTools)"
        if (-not [string]::IsNullOrWhiteSpace($toolsInput)) {
            $script:OpenSpecTools = $toolsInput.Trim()
        }
    }
}

function New-RedmineCliConfigObject {
    return [ordered]@{
        "version" = "2.0"
        "servers" = @()
        "default-server" = 0
        "editor" = ""
        "pager" = ""
        "issue" = [ordered]@{
            "view-journal" = $false
        }
    }
}

function Write-CmdShim {
    param(
        [Parameter(Mandatory = $true)][string]$ShimPath,
        [Parameter(Mandatory = $true)][string]$CommandLine
    )

    $content = @"
@echo off
$CommandLine %*
"@
    Set-Content -LiteralPath $ShimPath -Value $content -Encoding ASCII
    Write-Host "  Created command: $ShimPath" -ForegroundColor Green
}

function Ensure-CommandShims {
    param(
        [Parameter(Mandatory = $true)][string]$BinDir,
        [Parameter(Mandatory = $true)][string]$OpenSpecScript,
        [Parameter(Mandatory = $true)][string]$RedmineExe
    )

    Ensure-Directory $BinDir

    if (Test-Path -LiteralPath $OpenSpecScript) {
        Write-CmdShim -ShimPath (Join-Path $BinDir "openspec-cn.cmd") -CommandLine "node `"$OpenSpecScript`""
        Write-CmdShim -ShimPath (Join-Path $BinDir "openspec.cmd") -CommandLine "node `"$OpenSpecScript`""
    } else {
        Write-Warning "  OpenSpec script not found, command shim not created: $OpenSpecScript"
    }

    if (Test-Path -LiteralPath $RedmineExe) {
        Write-CmdShim -ShimPath (Join-Path $BinDir "red-cli.cmd") -CommandLine "`"$RedmineExe`""
    } else {
        Write-Warning "  red-cli.exe not found, command shim not created: $RedmineExe"
    }
}

function Ensure-UserPath {
    param([Parameter(Mandatory = $true)][string]$PathToAdd)

    $fullPath = [System.IO.Path]::GetFullPath($PathToAdd)
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $pathItems = @()
    if (-not [string]::IsNullOrWhiteSpace($userPath)) {
        $pathItems = @($userPath.Split(";") | Where-Object { $_ })
    }

    $exists = $pathItems | Where-Object {
        [System.IO.Path]::GetFullPath($_).TrimEnd("\") -ieq $fullPath.TrimEnd("\")
    } | Select-Object -First 1

    if ($exists) {
        Write-Host "  User PATH already contains: $fullPath" -ForegroundColor Cyan
    } else {
        $newUserPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $fullPath } else { "$userPath;$fullPath" }
        [System.Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
        Write-Host "  Added to user PATH: $fullPath" -ForegroundColor Green
    }

    $currentItems = @($env:Path.Split(";") | Where-Object { $_ })
    $currentExists = $currentItems | Where-Object {
        [System.IO.Path]::GetFullPath($_).TrimEnd("\") -ieq $fullPath.TrimEnd("\")
    } | Select-Object -First 1
    if (-not $currentExists) {
        $env:Path = "$env:Path;$fullPath"
    }
}

function Initialize-OpenSpecProjects {
    param(
        [Parameter(Mandatory = $true)][string]$OpenSpecCommand,
        [Parameter(Mandatory = $true)][string[]]$ProjectPaths,
        [Parameter(Mandatory = $true)][string]$Tools
    )

    if ($SkipProjectInit) {
        Write-Host "  Skipping project initialization (-SkipProjectInit)." -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path -LiteralPath $OpenSpecCommand)) {
        Write-Warning "  OpenSpec command not found, project initialization skipped: $OpenSpecCommand"
        return
    }

    foreach ($projectPath in $ProjectPaths) {
        Ensure-Directory $projectPath
        Write-Host "  Initializing OpenSpec project: $projectPath" -ForegroundColor Cyan
        $initArgs = @("init", $projectPath, "--tools", $Tools)
        & $OpenSpecCommand @initArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "  OpenSpec init failed for: $projectPath"
        }
    }
}

function Ensure-RedmineCliConfig {
    param([Parameter(Mandatory = $true)][string]$ConfigDir)

    Ensure-Directory $ConfigDir

    $configPath = Join-Path $ConfigDir "config.json"
    if (Test-Path -LiteralPath $configPath) {
        try {
            $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json -AsHashtable
        } catch {
            Write-Warning "  Existing Redmine CLI config is invalid JSON: $configPath"
            if (-not $ForceLinks) {
                Write-Warning "    Re-run with -ForceLinks to replace it."
                return
            }
            Backup-ExistingPath $configPath
            $config = New-RedmineCliConfigObject
        }
    } else {
        $config = New-RedmineCliConfigObject
    }

    if ($RedmineServer -and $RedmineApiKey -and $RedmineProjectId -gt 0) {
        $serverConfig = [ordered]@{
            "name" = $InstanceName
            "server" = $RedmineServer
            "api-key" = $RedmineApiKey
            "project" = ""
            "project-id" = $RedmineProjectId
            "user-id" = 0
        }

        $servers = @()
        if ($config.Contains("servers") -and $null -ne $config["servers"]) {
            $servers = @($config["servers"])
        }

        $updated = $false
        for ($i = 0; $i -lt $servers.Count; $i++) {
            if ($servers[$i]["name"] -eq $InstanceName) {
                $servers[$i] = $serverConfig
                $updated = $true
                break
            }
        }

        if (-not $updated) {
            $servers += $serverConfig
        }

        $config["version"] = "2.0"
        $config["servers"] = $servers
        if (-not $config.Contains("default-server")) { $config["default-server"] = 0 }
        if (-not $config.Contains("editor")) { $config["editor"] = "" }
        if (-not $config.Contains("pager")) { $config["pager"] = "" }
        if (-not $config.Contains("issue")) { $config["issue"] = [ordered]@{ "view-journal" = $false } }

        $config | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $configPath -Encoding UTF8
        Write-Host "  Updated Redmine CLI instance '$InstanceName': $configPath" -ForegroundColor Green
        return
    }

    if (Test-Path -LiteralPath $configPath) {
        Write-Host "  Redmine CLI config exists: $configPath" -ForegroundColor Cyan
    } else {
        $config | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $configPath -Encoding UTF8
        Write-Host "  Created Redmine CLI config: $configPath" -ForegroundColor Green
    }
}

function Ensure-OpenSpecRedmineConfig {
    param(
        [Parameter(Mandatory = $true)][string]$ConfigPath,
        [Parameter(Mandatory = $true)][string]$CliPath,
        [Parameter(Mandatory = $true)][string[]]$WorkspacePaths
    )

    if ($SkipOpenSpecConfig) {
        Write-Host "  Skipping OpenSpec Redmine config (-SkipOpenSpecConfig)." -ForegroundColor Yellow
        return
    }

    if (-not ($RedmineServer -and $RedmineApiKey -and $RedmineProjectId -gt 0)) {
        Write-Host "  OpenSpec config not written; pass -RedmineServer, -RedmineApiKey, and -RedmineProjectId to register an instance." -ForegroundColor Yellow
        return
    }

    Ensure-Directory ([System.IO.Path]::GetDirectoryName($ConfigPath))

    if ((Test-Path -LiteralPath $ConfigPath) -and -not $ForceOpenSpecConfig) {
        Write-Warning "  OpenSpec config exists, skipping: $ConfigPath"
        Write-Warning "    Re-run with -ForceOpenSpecConfig to replace the redmine config file."
        return
    }

    $primaryWorktree = if ($WorkspacePaths.Count -gt 0) { $WorkspacePaths[0] } else { $initialDir }
    $yaml = @"
redmine:
  enabled: true
  active-instance: auto
  instances:
    - name: $(ConvertTo-YamlSingleQuoted $InstanceName)
      server: $(ConvertTo-YamlSingleQuoted $RedmineServer)
      apiKey: $(ConvertTo-YamlSingleQuoted $RedmineApiKey)
      projectId: $RedmineProjectId
      cliPath: $(ConvertTo-YamlSingleQuoted $CliPath)
      gitWorktree: $(ConvertTo-YamlSingleQuoted $primaryWorktree)
"@

    Set-Content -LiteralPath $ConfigPath -Value $yaml -Encoding UTF8
    Write-Host "  Wrote OpenSpec Redmine config: $ConfigPath" -ForegroundColor Green

    if ($WorkspacePaths.Count -gt 1) {
        Write-Warning "  OpenSpec auto-detection currently stores one gitWorktree per instance."
        Write-Warning "  Additional workspaces have .red links, but add separate instances manually if they need different project IDs."
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OpenSpec + Redmine Dev Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Store the setup directory
$initialDir = if ($PSScriptRoot) {
    [System.IO.Path]::GetFullPath($PSScriptRoot)
} else {
    [System.IO.Path]::GetFullPath((Get-Location).Path)
}
Set-Location $initialDir

Invoke-InteractiveConfiguration

if (-not $RedmineConfigDir) {
    $RedmineConfigDir = Join-Path $HOME ".red"
}
$redmineConfigRoot = Resolve-SetupPath $RedmineConfigDir

if ($ProjectDirs.Count -eq 0 -and $Workspaces.Count -gt 0) {
    $ProjectDirs = $Workspaces
}

if ($ProjectDirs.Count -eq 0) {
    $ProjectDirs = @($initialDir)
}
$projectPaths = @($ProjectDirs | ForEach-Object { Resolve-SetupPath $_ })

# Step 1: Build redmine-cli
Write-Host "Step 1: Building redmine-cli..." -ForegroundColor Green
if ($SkipBuild) {
    Write-Host "  Skipping build (-SkipBuild)." -ForegroundColor Yellow
} elseif (Test-Path "redmine-cli") {
    Set-Location redmine-cli
    if (Test-Path "build.ps1") {
        & .\build.ps1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to build redmine-cli"
            Set-Location $initialDir
            exit 1
        }
        Write-Host "  redmine-cli built successfully!" -ForegroundColor Green
    } else {
        Write-Warning "  build.ps1 not found, skipping redmine-cli build"
    }
    Set-Location $initialDir
} else {
    Write-Warning "  redmine-cli directory not found, skipping"
}

# Step 2: Check Node.js and pnpm
Write-Host "Step 2: Checking Node.js..." -ForegroundColor Green
try {
    $nodeVersion = node --version
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Cyan
} catch {
    Write-Error "Node.js not found. Please install Node.js >= 20.19.0"
    exit 1
}

# Check pnpm
Write-Host "Step 2.1: Checking pnpm..." -ForegroundColor Green
try {
    $pnpmVersion = pnpm --version
    Write-Host "  pnpm: $pnpmVersion" -ForegroundColor Cyan
} catch {
    Write-Warning "  pnpm not found"
    Write-Host "  Installing pnpm..." -ForegroundColor Yellow
    corepack enable
    corepack prepare pnpm@latest --activate
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "  corepack failed, trying npm install..."
        npm install -g pnpm
    }
    $pnpmVersion = pnpm --version
    Write-Host "  pnpm installed: $pnpmVersion" -ForegroundColor Cyan
}

# Step 3: Build OpenSpec
Write-Host "Step 3: Building OpenSpec..." -ForegroundColor Green
$openspecDir = "OpenSpec-cn"
$foundOpenspec = $false

if (Test-Path $openspecDir) {
    $foundOpenspec = $true
} elseif (Test-Path "openspec-cn") {
    $openspecDir = "openspec-cn"
    $foundOpenspec = $true
}

if ($SkipBuild) {
    Write-Host "  Skipping OpenSpec build (-SkipBuild)." -ForegroundColor Yellow
} elseif ($foundOpenspec) {
    Write-Host "  Found OpenSpec directory: $openspecDir" -ForegroundColor Cyan
    Set-Location $openspecDir
    if (Test-Path "package.json") {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "  Installing dependencies..." -ForegroundColor Yellow
            pnpm install
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install dependencies"
                Set-Location $initialDir
                exit 1
            }
        }

        # Build
        Write-Host "  Building OpenSpec..." -ForegroundColor Yellow
        pnpm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to build OpenSpec"
            Set-Location $initialDir
            exit 1
        }
        Write-Host "  OpenSpec built successfully!" -ForegroundColor Green
    } else {
        Write-Warning "  package.json not found, skipping OpenSpec build"
    }
    Set-Location $initialDir
} else {
    Write-Warning "  OpenSpec-cn directory not found, skipping"
}

# Step 4: Setup PATH
Write-Host "Step 4: Setting up PATH..." -ForegroundColor Green
$redminePath = Join-Path $initialDir "redmine-cli\bin\red-cli.exe"
$openspecPath = Join-Path $initialDir "$openspecDir\bin\openspec.js"
$toolBinDir = Join-Path $HOME ".openspec-cn\bin"

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

Ensure-CommandShims -BinDir $toolBinDir -OpenSpecScript $openspecPath -RedmineExe $redminePath

if ($AddToUserPath) {
    Ensure-UserPath $toolBinDir
} else {
    Write-Host "  PATH not updated. Use -AddToUserPath or add this directory manually: $toolBinDir" -ForegroundColor Yellow
}

# Step 5: Configure Redmine directories and workspace links
Write-Host "Step 5: Configuring Redmine directories..." -ForegroundColor Green
Ensure-RedmineCliConfig $redmineConfigRoot

foreach ($projectPath in $projectPaths) {
    Ensure-Directory $projectPath
    $projectRedDir = Join-Path $projectPath ".red"
    if ([System.IO.Path]::GetFullPath($projectRedDir) -eq [System.IO.Path]::GetFullPath($redmineConfigRoot)) {
        Write-Host "  Project uses primary Redmine config directory: $projectRedDir" -ForegroundColor Cyan
    } else {
        Ensure-DirectorySymlink -LinkPath $projectRedDir -TargetPath $redmineConfigRoot
    }
}

if ($LinkUserRedConfig) {
    $userRedDir = Join-Path $HOME ".red"
    if ([System.IO.Path]::GetFullPath($userRedDir) -eq [System.IO.Path]::GetFullPath($redmineConfigRoot)) {
        Write-Host "  User-level ~/.red is the primary Redmine config directory." -ForegroundColor Cyan
    } else {
        Ensure-DirectorySymlink -LinkPath $userRedDir -TargetPath $redmineConfigRoot
    }
} else {
    Write-Host "  User-level ~/.red is the primary Redmine config directory." -ForegroundColor Cyan
}

$openspecGlobalConfig = Join-Path $HOME ".openspec\config.yaml"
$openspecRedmineConfigArgs = @{
    ConfigPath = $openspecGlobalConfig
    CliPath = $redminePath
    WorkspacePaths = [string[]]$projectPaths
}
Ensure-OpenSpecRedmineConfig @openspecRedmineConfigArgs

# Step 6: Initialize project OpenSpec directories
Write-Host "Step 6: Initializing project OpenSpec directories..." -ForegroundColor Green
$openspecCmd = Join-Path $toolBinDir "openspec.cmd"
Initialize-OpenSpecProjects -OpenSpecCommand $openspecCmd -ProjectPaths $projectPaths -Tools $OpenSpecTools

# Step 7: Verify installations
Write-Host "Step 7: Verifying installations..." -ForegroundColor Green

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
        $openspecCnCmd = Join-Path $toolBinDir "openspec-cn.cmd"
        if (Test-Path -LiteralPath $openspecCnCmd) {
            & $openspecCnCmd --version
        } else {
            node $openspecPath --version
        }
        Write-Host "  openspec-cn verified!" -ForegroundColor Green
    } catch {
        Write-Warning "  openspec-cn verification failed"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open a new terminal if PATH was updated." -ForegroundColor White
Write-Host "2. Test CLI: openspec --version" -ForegroundColor White
Write-Host "3. Use OpenSpec from a project directory: cd <project>; openspec list" -ForegroundColor White
Write-Host "4. Test Redmine: openspec redmine current; openspec redmine test" -ForegroundColor White
Write-Host ""
