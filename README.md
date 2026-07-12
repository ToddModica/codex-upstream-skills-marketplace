# Codex 科研工具 Marketplace

这是一个可直接安装到 Codex 的私有 GitHub Marketplace，用于统一分发、锁定版本并自动更新科研、写作和通用工具 Skills。仓库中的第三方 Skill 均保留原始目录结构、脚本、参考资料、资源文件及许可证。

## 插件与 Skills

### research-toolkit

科研检索、论文写作、引用、数据作图和 ITASCA 数值模拟工具：

- Academic Research 系列：`deep-research`、`academic-paper`、`academic-paper-reviewer`、`academic-pipeline`、`academic-research-suite`
- Nature 系列：`nature-academic-search`、`nature-citation`、`nature-data`、`nature-figure`、`nature-paper2ppt`、`nature-polishing`、`nature-reader`、`nature-response`、`nature-writing`
- SciPilot 系列：`scipilot-cite-skill`、`scipilot-figure-skill`、`scipilot-writing-skill`
- MCP：`itasca-mcp`，通过 `uvx itasca-mcp` 启动；ITASCA 端桥接文件位于 `plugins/research-toolkit/assets/itasca-mcp-addon.py`

### writing-toolkit

中英文自然化、去模板化与文字润色工具：

- `humanizer`
- `humanizer-zh`
- `shuorenhua`
- `stop-slop`

### codex-utility-toolkit

文档、媒体读取、PowerShell、前端设计和 Codex Skill 开发工具：

- `bilibili-page-reader`
- `doc`
- `pdf`
- `imagegen`
- `openai-docs`
- `powershell-safe-invocation`
- `design-taste-frontend`
- `skill-creator`
- `skill-installer`

## Windows 安装

需要先安装 Codex CLI。克隆本仓库后，在 PowerShell 7 中运行：

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\Initialize-Marketplace.ps1
```

脚本会检查 Codex CLI、注册 `research-toolkit-marketplace`，并安装三个插件。安装完成后请新建一个 Codex 任务，使新 Skills 和 MCP 工具生效。

也可以手动安装：

```powershell
codex plugin marketplace add .
codex plugin add research-toolkit@research-toolkit-marketplace
codex plugin add writing-toolkit@research-toolkit-marketplace
codex plugin add codex-utility-toolkit@research-toolkit-marketplace
```

## 更新

拉取仓库更新后运行：

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\Update-Marketplace.ps1
```

更新完成后同样需要新建 Codex 任务。

## 自动更新

`.github/workflows/sync-sources.yml` 已启用以下流程：

- 每天北京时间 11:17 自动检查上游；
- 支持在 GitHub Actions 页面手动运行；
- 按 `sources.json` 锁定的仓库和 Skill 子目录同步内容；
- 同步 Academic Research、Nature、SciPilot、Bilibili 阅读器、PowerShell 安全调用、Taste 前端设计及其他已打包 Skills；
- 自动更新来源 commit SHA；
- 校验 Marketplace、插件清单、全部 `SKILL.md`、MCP 配置和上游许可证；
- 仅在内容发生变化时提升受影响插件的补丁版本并提交；
- 任一校验失败时不提交更新。

Academic Research、Nature、agent-skills 和 taste-skill 都可能是 monorepo。同步脚本只复制 `sources.json` 指定的 `upstream_subpath`，不会把整个上游仓库错误地复制到单个 Skill 目录。

## 校验兼容性说明

仓库使用 `scripts/validate_catalog.py` 按当前 Codex 插件运行要求校验 Skill 名称、描述、目标路径、来源 SHA、许可证、MCP 配置、符号链接和凭据类文件。部分原版第三方 Skill 还包含 `author`、`version` 或 `compatibility` 等扩展 front matter，旧版 `skill-creator/quick_validate.py` 会将这些扩展字段报告为作者格式警告，但当前 Codex 能正常加载；为保持上游内容完整，本仓库不擅自删除这些字段。

## 来源锁与许可证

`sources.json` 记录每个 Skill 的：

- 上游 GitHub 仓库；
- 分支和当前 commit SHA；
- 上游子目录；
- 插件目标目录；
- 许可证及许可证作用范围；
- 是否允许自动复制。

主要第三方许可证：

- `Imbad0202/academic-research-skills`：CC-BY-NC-4.0；
- `Imbad0202/academic-research-skills-codex`：CC-BY-NC-4.0；
- `Yuan1z0825/nature-skills`：Apache-2.0；
- `Misaka-Mikoto-Tech/agent-skills`：MIT；
- SciPilot Skills：MIT；
- `Leonxlnx/taste-skill`：MIT；
- `itasca-mcp`：MIT。

对于许可证位于 monorepo 根目录的 Skill，同步时会在对应 Skill 目录写入 `UPSTREAM_LICENSE`。未确认允许再分发的 Skill 只保留来源记录，不复制到插件中。详细归属见 `THIRD_PARTY_NOTICES.md`。

## 回退版本

```powershell
git checkout <标签或提交SHA>
pwsh -NoLogo -NoProfile -File .\scripts\Update-Marketplace.ps1
```

恢复最新版本：

```powershell
git switch main
git pull --ff-only
pwsh -NoLogo -NoProfile -File .\scripts\Update-Marketplace.ps1
```

## 多设备部署

在其他设备克隆本私有仓库，首次运行初始化脚本，以后执行 `git pull --ff-only` 和更新脚本即可。不要向仓库提交 Token、Cookie、`.env`、私钥或本机 Codex 配置。

## 维护者命令

从本机安装目录重新生成来源锁：

```powershell
python .\scripts\generate_sources.py `
  --skills-root <skills目录> `
  --mcp-root <itasca-mcp目录>
```

从 GitHub 锁定版本同步并校验：

```powershell
python .\scripts\update_sources.py
python .\scripts\sync_sources.py --remote
python .\scripts\validate_catalog.py
```

用户明确排除的 `agently-mail` 和 `netease-uu-booster` 仅保留为来源记录，不会安装到插件中；`agents`、`commands`、`shared` 不包含独立 `SKILL.md`，因此不作为 Skill 封装。`ai-flavor-remover` 当前上游仓库未提供许可证文件，因此只记录来源，不直接复制进插件。
