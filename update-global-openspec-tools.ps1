# Update global OpenSpec-cn and red-cli tooling from the local indie_proj checkout.

param(
    [string]$IndieProj = "G:\tools\ai_tool_collection\indie_proj",
    [string]$GlobalRoot = $HOME,
    [string]$Tools = "codex,claude",
    [switch]$Watch,
    [int]$DebounceSeconds = 2,
    [switch]$Force,
    [switch]$SkipOpenSpecBuild,
    [switch]$SkipRedCliBuild,
    [switch]$SkipArtifactUpdate,
    [switch]$SkipUserPath
)

$ErrorActionPreference = "Stop"

function Resolve-FullPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path)
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = (Get-Location).Path
    )

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
        }
    } finally {
        Pop-Location
    }
}

function Write-CmdShim {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$CommandLine
    )

    $content = @"
@echo off
$CommandLine %*
"@
    Set-Content -LiteralPath $Path -Value $content -Encoding ASCII
}

function Ensure-UserPath {
    param([Parameter(Mandatory = $true)][string]$Directory)

    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @()
    if (-not [string]::IsNullOrWhiteSpace($current)) {
        $parts = $current -split ";" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    }

    $alreadyPresent = $parts | Where-Object {
        try {
            [System.IO.Path]::GetFullPath($_).TrimEnd("\") -ieq [System.IO.Path]::GetFullPath($Directory).TrimEnd("\")
        } catch {
            $_ -ieq $Directory
        }
    }

    if (-not $alreadyPresent) {
        $newPath = if ([string]::IsNullOrWhiteSpace($current)) { $Directory } else { "$current;$Directory" }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "Added to user PATH: $Directory" -ForegroundColor Green
    }
}

function Update-GlobalOpenSpecTools {
    $indieRoot = Resolve-FullPath $IndieProj
    $openspecDir = Join-Path $indieRoot "OpenSpec-cn"
    $redCliDir = Join-Path $indieRoot "redmine-cli"
    $redCliExe = Join-Path $redCliDir "bin\red-cli.exe"
    $openspecScript = Join-Path $openspecDir "bin\openspec.js"
    $toolBinDir = Join-Path $GlobalRoot ".openspec-cn\bin"
    $globalOpenSpecDir = Join-Path $GlobalRoot "openspec"

    if (-not (Test-Path -LiteralPath $openspecDir)) {
        throw "OpenSpec-cn directory not found: $openspecDir"
    }
    if (-not (Test-Path -LiteralPath $redCliDir)) {
        throw "redmine-cli directory not found: $redCliDir"
    }

    Write-Host "Updating global OpenSpec tools from: $indieRoot" -ForegroundColor Cyan

    if (-not $SkipRedCliBuild) {
        $buildScript = Join-Path $redCliDir "build.ps1"
        if (Test-Path -LiteralPath $buildScript) {
            Write-Host "Building red-cli..." -ForegroundColor Cyan
            Invoke-Checked -FilePath "powershell" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $buildScript) -WorkingDirectory $redCliDir
        } else {
            Write-Warning "red-cli build script not found: $buildScript"
        }
    }

    if (-not $SkipOpenSpecBuild) {
        Write-Host "Building OpenSpec-cn..." -ForegroundColor Cyan
        if (-not (Test-Path -LiteralPath (Join-Path $openspecDir "node_modules"))) {
            Invoke-Checked -FilePath "pnpm" -Arguments @("install") -WorkingDirectory $openspecDir
        }
        Invoke-Checked -FilePath "pnpm" -Arguments @("run", "build") -WorkingDirectory $openspecDir
    }

    Ensure-Directory $toolBinDir

    if (Test-Path -LiteralPath $openspecScript) {
        Write-CmdShim -Path (Join-Path $toolBinDir "openspec-cn.cmd") -CommandLine "node `"$openspecScript`""
        Write-CmdShim -Path (Join-Path $toolBinDir "openspec.cmd") -CommandLine "node `"$openspecScript`""
    } else {
        throw "OpenSpec entry script not found: $openspecScript"
    }

    if (Test-Path -LiteralPath $redCliExe) {
        Write-CmdShim -Path (Join-Path $toolBinDir "red-cli.cmd") -CommandLine "`"$redCliExe`""
    } else {
        throw "red-cli executable not found: $redCliExe"
    }

    if (-not $SkipUserPath) {
        Ensure-UserPath $toolBinDir
    }

    if (-not $SkipArtifactUpdate) {
        Ensure-Directory $globalOpenSpecDir
        $openspecCmd = Join-Path $toolBinDir "openspec.cmd"
        $artifactArgs = @()

        $hasGlobalArtifacts = (Test-Path -LiteralPath (Join-Path $GlobalRoot ".codex\prompts")) -or
            (Test-Path -LiteralPath (Join-Path $GlobalRoot ".claude\commands")) -or
            (Test-Path -LiteralPath (Join-Path $GlobalRoot ".opencode"))

        if ($hasGlobalArtifacts) {
            $artifactArgs = @("update", $GlobalRoot)
            if ($Force) {
                $artifactArgs += "--force"
            }
        } else {
            $artifactArgs = @("init", $GlobalRoot, "--tools", $Tools, "--force")
        }

        Write-Host "Refreshing global skills and commands in: $GlobalRoot" -ForegroundColor Cyan
        Invoke-Checked -FilePath $openspecCmd -Arguments $artifactArgs -WorkingDirectory $GlobalRoot
    }

    Write-Host "Done." -ForegroundColor Green
}

function Start-ToolWatcher {
    $indieRoot = Resolve-FullPath $IndieProj
    $paths = @(
        (Join-Path $indieRoot "OpenSpec-cn\src"),
        (Join-Path $indieRoot "OpenSpec-cn\bin"),
        (Join-Path $indieRoot "OpenSpec-cn\schemas"),
        (Join-Path $indieRoot "OpenSpec-cn\openspec"),
        (Join-Path $indieRoot "redmine-cli\cmd"),
        (Join-Path $indieRoot "redmine-cli\internal"),
        (Join-Path $indieRoot "redmine-cli\docs")
    ) | Where-Object { Test-Path -LiteralPath $_ }

    if ($paths.Count -eq 0) {
        throw "No watchable tool paths found under: $indieRoot"
    }

    $script:lastRun = Get-Date "2000-01-01"
    $script:running = $false
    $script:watchDebounceSeconds = $DebounceSeconds

    foreach ($path in $paths) {
        $watcher = New-Object System.IO.FileSystemWatcher
        $watcher.Path = $path
        $watcher.IncludeSubdirectories = $true
        $watcher.NotifyFilter = [System.IO.NotifyFilters]"FileName, DirectoryName, LastWrite, Size"
        $watcher.EnableRaisingEvents = $true

        $action = {
            $now = Get-Date
            if ($script:running) { return }
            if (($now - $script:lastRun).TotalSeconds -lt $script:watchDebounceSeconds) { return }

            $script:running = $true
            $script:lastRun = $now
            try {
                Write-Host ""
                Write-Host "Change detected; updating global tools..." -ForegroundColor Yellow
                Update-GlobalOpenSpecTools
            } catch {
                Write-Error $_
            } finally {
                $script:running = $false
            }
        }

        Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $action | Out-Null
        Register-ObjectEvent -InputObject $watcher -EventName Created -Action $action | Out-Null
        Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action $action | Out-Null
        Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $action | Out-Null
    }

    Write-Host "Watching tool sources. Press Ctrl+C to stop." -ForegroundColor Green
    while ($true) {
        Start-Sleep -Seconds 1
    }
}

Update-GlobalOpenSpecTools

if ($Watch) {
    Start-ToolWatcher
}
