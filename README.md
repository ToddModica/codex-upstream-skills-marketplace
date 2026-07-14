# Codex 科研工具 Marketplace

这是一个可直接安装到 Codex 的私有 GitHub Marketplace，用于统一分发、锁定版本并自动更新科研、写作和通用工具 Skills。仓库中的第三方 Skill 均保留原始目录结构、脚本、参考资料、资源文件及许可证。

## 本仓库许可证

本仓库新增的包装脚本、Marketplace 清单、README 和维护代码采用 MIT License，见 `LICENSE`。第三方 Skills 不因本仓库添加 MIT License 而改变授权方式；它们仍分别适用各自上游仓库的许可证和随包保留的许可证文件。SciPilot Skills 的上游作者主页为 `https://github.com/Haojae`，自动更新仍使用其具体 Skill 仓库地址。

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

演示文稿、文档、媒体读取、PowerShell、前端设计和 Codex Skill 开发工具：

- `bilibili-page-reader`
- `doc`
- `pdf`
- `ppt-master`：把 PDF、DOCX、网页或文本生成原生可编辑的 PowerPoint；完整脚本、模板和参考资源随 Skill 安装
- `imagegen`
- `openai-docs`
- `powershell-safe-invocation`
- `design-taste-frontend`
- `skill-creator`
- `skill-installer`

## Windows 安装

需要先安装 Codex CLI 和 Git for Windows。初始化脚本默认把 Marketplace 注册为 Git 源 `ToddModica/codex-skills-github-marketplace@main`，并会启用 Windows Git 长路径支持：

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\Initialize-Marketplace.ps1
```

脚本会检查 Codex CLI 和 Git、注册 `research-toolkit-marketplace`，并安装三个插件。若 Git Marketplace 注册失败，脚本会回退到当前本地仓库路径，避免 Codex 设置中的“插件 / 市场”来源丢失。安装完成后请新建一个 Codex 任务，使新 Skills 和 MCP 工具生效。

也可以手动安装：

```powershell
git config --global core.longpaths true
codex plugin marketplace add ToddModica/codex-skills-github-marketplace --ref main
codex plugin add research-toolkit@research-toolkit-marketplace
codex plugin add writing-toolkit@research-toolkit-marketplace
codex plugin add codex-utility-toolkit@research-toolkit-marketplace
```

如果是在一台新电脑上，不需要先复制本机的 Skills 目录。只要该电脑已经登录到有权限访问本私有仓库的 GitHub 账号，并安装了 Codex CLI 与 Git for Windows，就可以直接把 GitHub 仓库地址交给 Codex 注册为 Git Marketplace：

```powershell
codex plugin marketplace add https://github.com/ToddModica/codex-skills-github-marketplace.git --ref main
codex plugin add research-toolkit@research-toolkit-marketplace
codex plugin add writing-toolkit@research-toolkit-marketplace
codex plugin add codex-utility-toolkit@research-toolkit-marketplace
```

如果已经克隆了本仓库，也可以用初始化脚本显式指定 GitHub 地址：

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\Initialize-Marketplace.ps1 `
  -MarketplaceSource https://github.com/ToddModica/codex-skills-github-marketplace.git `
  -MarketplaceRef main
```

## 更新

刷新 Git Marketplace 快照并重新安装插件：

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\Update-Marketplace.ps1
```

更新脚本会执行 Git Marketplace 注册/刷新、校验 Marketplace 仍可见，并重新安装三个插件。更新完成后同样需要新建 Codex 任务。

## 自动更新

`.github/workflows/sync-sources.yml` 已启用以下流程：

- 每天北京时间 01:17 自动检查上游；
- 支持在 GitHub Actions 页面手动运行；
- 按 `sources.json` 锁定的仓库和 Skill 子目录同步内容；
- 同步 Academic Research、Nature、SciPilot、PPT Master、Bilibili 阅读器、PowerShell 安全调用、Taste 前端设计及其他已打包 Skills；
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
- SciPilot Skills（`https://github.com/Haojae`）：MIT；
- `Leonxlnx/taste-skill`：MIT；
- `hugohe3/ppt-master`：MIT；
- `itasca-mcp`：MIT。

`ppt-master` 的插件包包含其上游 `skills/ppt-master` 完整目录和 Python 依赖清单，但 Codex 安装插件时不会自动执行第三方依赖安装。首次实际使用前，请在已安装的 Skill 目录运行：

```powershell
python -m pip install -r .\requirements.txt
```

该 Skill 可选调用多个图像生成或素材检索服务。API Key 只应保存在环境变量或用户私有配置中，不要提交到本 Marketplace 仓库。

安全提示：`ppt-master` 的上游脚本会按工作流需要启动本机预览服务、访问用户指定网页或第三方图像/API 服务、调用外部转换程序，并清理其项目目录内生成的临时资源。请仅处理可信输入，使用前检查目标项目路径，并只为确实需要的可选服务配置 API Key。

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

在其他设备上，只要该设备能访问本私有 GitHub 仓库，就可以直接使用仓库地址完成 Git Marketplace 注册和插件安装；不需要提前同步 `D:\OneDrive\cc-switch\.cc-switch\skills`。保留本地克隆主要用于维护、回退或离线兜底。不要向仓库提交 Token、Cookie、`.env`、私钥或本机 Codex 配置。

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
