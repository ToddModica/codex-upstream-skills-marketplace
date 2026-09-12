[CmdletBinding()]
param(
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

if ($Check) {
    Write-Output ([bool][Environment]::GetEnvironmentVariable('EXA_API_KEY', 'User'))
    return
}

$secureKey = Read-Host 'Enter the Exa API key' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
    $apiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        throw 'The Exa API key cannot be empty.'
    }
    [Environment]::SetEnvironmentVariable('EXA_API_KEY', $apiKey, 'User')
}
finally {
    if ($pointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
    Remove-Variable apiKey -ErrorAction SilentlyContinue
}

Write-Host 'EXA_API_KEY is saved in the current user environment. Restart Codex before using Exa.'
