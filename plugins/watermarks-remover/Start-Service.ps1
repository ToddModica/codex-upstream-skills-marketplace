[CmdletBinding()]
param([string]$ServiceDirectory = (Join-Path $env:USERPROFILE 'watermarks-remover-service'))
$ErrorActionPreference = 'Stop'
$env:Path += ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
try {
    $health = Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 2
    if ($health.ok) { Write-Output 'Watermarks service is ready.'; exit 0 }
} catch {}
$root = (Resolve-Path -LiteralPath $ServiceDirectory).Path
$server = Join-Path $root 'service\scripts\server.py'
if (-not (Test-Path -LiteralPath $server)) { throw "Service source missing: $server" }
$python = (Get-Command python -ErrorAction Stop).Source
$process = Start-Process -FilePath $python -ArgumentList @(('"' + $server + '"'), '--host', '127.0.0.1', '--port', '8765') -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $root 'native.stdout.log') -RedirectStandardError (Join-Path $root 'native.stderr.log')
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Seconds 1
    if ($process.HasExited) { throw 'Service exited; inspect native.stderr.log in the service directory.' }
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 2
        if ($health.ok) { Write-Output "Watermarks service ready, PID $($process.Id)."; exit 0 }
    } catch {}
}
throw 'Watermarks service health check timed out.'
