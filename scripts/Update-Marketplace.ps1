[CmdletBinding()]
param(
    [string]$RepositoryPath = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$marketplaceName = 'research-toolkit-marketplace'
$plugins = @('research-toolkit', 'writing-toolkit', 'codex-utility-toolkit')
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'Codex CLI was not found on PATH. Install or update Codex CLI, reopen PowerShell, then run this script again.'
}
$repository = (Resolve-Path -LiteralPath $RepositoryPath).Path
& codex plugin marketplace add $repository
if ($LASTEXITCODE -ne 0) { throw "Could not refresh Marketplace (Codex exit code $LASTEXITCODE)." }
foreach ($plugin in $plugins) {
    & codex plugin add "$plugin@$marketplaceName"
    if ($LASTEXITCODE -ne 0) { throw "Could not refresh $plugin (Codex exit code $LASTEXITCODE)." }
}
Write-Host 'Marketplace refreshed. Start a new Codex task to use updated Skills and MCP tools.'
