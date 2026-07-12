[CmdletBinding()]
param(
    [string]$RepositoryPath = (Split-Path -Parent $PSScriptRoot),
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$marketplaceName = 'research-toolkit-marketplace'
$plugins = @('research-toolkit', 'writing-toolkit', 'codex-utility-toolkit')

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'Codex CLI was not found on PATH. Install or update Codex CLI, reopen PowerShell, then run this script again.'
}
$repository = (Resolve-Path -LiteralPath $RepositoryPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $repository '.agents\plugins\marketplace.json') -PathType Leaf)) {
    throw "Marketplace manifest missing under: $repository"
}

& codex plugin marketplace add $repository
if ($LASTEXITCODE -ne 0) { throw "Could not add Marketplace '$repository' (Codex exit code $LASTEXITCODE)." }
if (-not $SkipInstall) {
    foreach ($plugin in $plugins) {
        & codex plugin add "$plugin@$marketplaceName"
        if ($LASTEXITCODE -ne 0) { throw "Could not install $plugin (Codex exit code $LASTEXITCODE)." }
    }
}
Write-Host "Marketplace '$marketplaceName' is configured. Start a new Codex task to load newly installed Skills and MCP tools."
