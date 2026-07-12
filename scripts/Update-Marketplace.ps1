[CmdletBinding()]
param(
    [string]$RepositoryPath = (Split-Path -Parent $PSScriptRoot),
    [string]$MarketplaceSource = 'ToddModica/codex-skills-github-marketplace',
    [string]$MarketplaceRef = 'main'
)

$ErrorActionPreference = 'Stop'
$marketplaceName = 'research-toolkit-marketplace'
$plugins = @('research-toolkit', 'writing-toolkit', 'codex-utility-toolkit')

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
foreach ($plugin in $plugins) {
    Invoke-Native -FilePath 'codex' -ArgumentList @('plugin', 'add', "$plugin@$marketplaceName") -FailureMessage "Could not refresh $plugin"
}
Write-Host 'Marketplace refreshed. Start a new Codex task to use updated Skills and MCP tools.'
