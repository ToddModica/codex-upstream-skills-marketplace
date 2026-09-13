[CmdletBinding()]
param(
    [string]$RepositoryPath = (Split-Path -Parent $PSScriptRoot),
    [string]$MarketplaceSource = 'ToddModica/upstream-skills',
    [string]$MarketplaceRef = 'main'
)

$ErrorActionPreference = 'Stop'
$marketplaceName = 'research-toolkit-marketplace'
$plugins = @('research-toolkit', 'writing-toolkit', 'codex-utility-toolkit', 'ponytail', 'watermarks-remover', 'no-negative-echo')

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code $LASTEXITCODE)."
    }
}

function Assert-MarketplaceVisible {
    $marketplaces = & codex plugin marketplace list
    if ($LASTEXITCODE -ne 0) {
        throw "Could not list Codex marketplaces (exit code $LASTEXITCODE)."
    }
    if (-not ($marketplaces -match "^$([regex]::Escape($marketplaceName))\s+")) {
        throw "Marketplace '$marketplaceName' is not visible to Codex after refresh."
    }
}

function Assert-WatermarksRemoverRuntime {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw 'watermarks-remover requires Python 3.10+ and Python was not found. Install Python, reopen PowerShell, then run this script again. No pip packages are required for its core cleanup scripts.'
        }
        Invoke-Native -FilePath $winget.Source -ArgumentList @('install', '--id', 'Python.Python.3.13', '--exact', '--scope', 'user', '--accept-package-agreements', '--accept-source-agreements') -FailureMessage 'Could not install Python for watermarks-remover'
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            throw 'Python was installed for watermarks-remover. Reopen PowerShell once, then run this script again.'
        }
    }
    & $python.Source -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'
    if ($LASTEXITCODE -ne 0) {
        throw 'watermarks-remover requires Python 3.10+.'
    }
}

function Assert-HookRuntime {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        return
    }
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'Ponytail and no-negative-echo Hooks require Node.js on PATH.'
    }
    Invoke-Native -FilePath $winget.Source -ArgumentList @('install', '--id', 'OpenJS.NodeJS.LTS', '--exact', '--scope', 'user', '--accept-package-agreements', '--accept-source-agreements') -FailureMessage 'Could not install Node.js for plugin Hooks'
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        throw 'Node.js was installed for plugin Hooks. Reopen PowerShell once, then run this script again.'
    }
}

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'Codex CLI was not found on PATH. Install or update Codex CLI, reopen PowerShell, then run this script again.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git was not found on PATH. Install Git for Windows, reopen PowerShell, then run this script again.'
}
$repository = (Resolve-Path -LiteralPath $RepositoryPath).Path

Invoke-Native -FilePath 'git' -ArgumentList @('config', '--global', 'core.longpaths', 'true') -FailureMessage 'Could not enable Git long path support'
try {
    Invoke-Native -FilePath 'codex' -ArgumentList @('plugin', 'marketplace', 'add', $MarketplaceSource, '--ref', $MarketplaceRef) -FailureMessage "Could not add Git Marketplace '$MarketplaceSource'"
    Invoke-Native -FilePath 'codex' -ArgumentList @('plugin', 'marketplace', 'upgrade', $marketplaceName) -FailureMessage "Could not upgrade Git Marketplace '$marketplaceName'"
} catch {
    Write-Warning $_.Exception.Message
    Write-Warning "Falling back to the local repository Marketplace at '$repository' so the Settings > Plugins > Marketplace tab keeps a valid source."
    Invoke-Native -FilePath 'codex' -ArgumentList @('plugin', 'marketplace', 'add', $repository) -FailureMessage "Could not add fallback local Marketplace '$repository'"
}
Assert-MarketplaceVisible
Assert-WatermarksRemoverRuntime
Assert-HookRuntime
foreach ($plugin in $plugins) {
    Invoke-Native -FilePath 'codex' -ArgumentList @('plugin', 'add', "$plugin@$marketplaceName") -FailureMessage "Could not refresh $plugin"
}
Write-Host 'Marketplace refreshed. Start a new Codex task to use updated Skills and MCP tools.'
