## Windows on-demand startup (Marketplace policy)

Probe `/health` before use. If the default local service at
`http://127.0.0.1:8765` is unavailable, run the plugin-root `Start-Service.ps1`
with PowerShell 7 (`../../Start-Service.ps1` relative to this Skill directory).
It starts Python from `%USERPROFILE%/watermarks-remover-service`, waits for
health, and leaves the service running after use. Report startup errors and stop
until health succeeds. For a custom remote URL, report connection failure instead
of starting a local service. Keep login startup disabled.
This policy takes precedence over upstream local-service startup instructions.
