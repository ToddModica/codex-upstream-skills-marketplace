# Research Toolkit Marketplace for Codex

This repository is a local/GitHub Marketplace that repackages selected Codex
Skills from a configurable local Skill root. It does not change that source
directory. Each copied Skill keeps its upstream files, including
`references`, `scripts`, and `assets`.

## Plugins

| Plugin | Bundled Skills | Notes |
|---|---|---|
| `research-toolkit` | `scipilot-cite-skill`, `scipilot-figure-skill`, `scipilot-writing-skill` | Also configures optional `itasca-mcp` via `uvx`. Copy `assets/itasca-mcp-addon.py` into the ITASCA engine as documented upstream. |
| `writing-toolkit` | `humanizer`, `humanizer-zh`, `shuorenhua`, `stop-slop` | MIT-licensed Chinese/English prose editing tools. |
| `codex-utility-toolkit` | `doc`, `pdf`, `imagegen`, `openai-docs`, `skill-creator`, `skill-installer` | Apache-2.0 utilities. |

`sources.json` is the source lock: it records every discovered non-excluded
Skill, source URL, branch, commit SHA, license result, and either a destination
or a record-only reason.

## License policy

Only Skills whose locked local source contained an MIT or Apache-2.0 license
were copied. The following Skill families are listed in `sources.json` but not
redistributed because their locked revisions lacked a license file:

- Academic Research Skills and Academic Research Suite
- Nature Skills
- `ai-flavor-remover`, `bilibili-page-reader`, `codex-windows-fast-patch`
- `design-taste-frontend`, `powershell-safe-invocation`

The user-excluded `agently-mail` and `netease-uu-booster` are retained in the
source lock as `record-only` entries but are not packaged. `agents`, `commands`,
and `shared` were not Skills (they contain no `SKILL.md`).

## Install on Windows

Open PowerShell 7 at the repository root and run:

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\Initialize-Marketplace.ps1
```

The script checks that `codex` is on `PATH`, adds this repository as the
`research-toolkit-marketplace`, installs all three plugins, and stops with an
explicit error if any Codex command fails. Start a new Codex task afterwards.

For manual installation:

```powershell
codex plugin marketplace add .
codex plugin add research-toolkit@research-toolkit-marketplace
codex plugin add writing-toolkit@research-toolkit-marketplace
codex plugin add codex-utility-toolkit@research-toolkit-marketplace
```

## Update and rollback

After pulling the latest repository revision, refresh all installed plugins:

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\Update-Marketplace.ps1
```

To roll back, check out a known Git tag or commit, then run the update script:

```powershell
git checkout <tag-or-commit>
pwsh -NoLogo -NoProfile -File .\scripts\Update-Marketplace.ps1
```

To remove a plugin, use the Codex CLI command supported by your installed CLI
version (typically `codex plugin remove <plugin>`), then optionally remove this
Marketplace with `codex plugin marketplace remove research-toolkit-marketplace`.

## Multiple devices

Push this repository to a private or public GitHub repository. On another
device, clone it, run the initialization script once, then use the update
script after `git pull`. Do not commit tokens, cookies, `.env` files, private
keys, or local Codex configuration; the sync script excludes common credential
file names and private-key extensions.

## Maintainer sync

```powershell
python .\scripts\update_sources.py
python .\scripts\sync_sources.py --local-skills-root <skills-root> --itasca-mcp-root <itasca-mcp-root>
python .\scripts\validate_catalog.py
```

`sync_sources.py --remote` clones only locked GitHub sources into a temporary
directory. Sources without an identified GitHub remote are deliberately
skipped in remote CI. GitHub Actions runs daily and on manual dispatch; it
updates source SHAs, syncs eligible content, validates the catalog, bumps
changed plugin patch versions, and commits only validated diffs.
