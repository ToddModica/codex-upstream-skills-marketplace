# Codex 上游 Skills Marketplace

这是一个公开的 Codex Git Marketplace，用于分发具有明确上游来源和可再分发许可证的科研、写作、文档及开发工作流。每个第三方 Skill 保留原目录、脚本、参考资料、资源文件和许可证；版本与 commit SHA 记录在 `sources.json`。

自行编写的 Skill 位于访问受限的 [`ToddModica/codex-personal-skills-marketplace`](https://github.com/ToddModica/codex-personal-skills-marketplace)。两座 Marketplace 可以同时安装。

## 许可证边界

仓库根目录的 MIT License 只适用于本仓库新增的包装脚本、清单、校验器和文档，不会改变第三方内容的许可证。

特别注意：Academic Research Skills 与其 Codex 版本使用 **CC-BY-NC-4.0**，要求署名并限制商业使用。其他已打包来源使用 MIT 或 Apache-2.0。完整归属见 `THIRD_PARTY_NOTICES.md`，每个 Skill 的锁定许可证位置见 `sources.json`。

## 快速安装

需要 Codex CLI 和 Git：

```powershell
git clone https://github.com/ToddModica/codex-upstream-skills-marketplace.git
Set-Location .\codex-upstream-skills-marketplace
pwsh -NoLogo -NoProfile -File .\scripts\Initialize-Marketplace.ps1
```

也可以直接注册 Git Marketplace 并按需安装：

```powershell
codex plugin marketplace add https://github.com/ToddModica/codex-upstream-skills-marketplace.git --ref main
codex plugin add research-toolkit@research-toolkit-marketplace
codex plugin add writing-toolkit@research-toolkit-marketplace
codex plugin add codex-utility-toolkit@research-toolkit-marketplace
codex plugin add ponytail@research-toolkit-marketplace
codex plugin add watermarks-remover@research-toolkit-marketplace
codex plugin add no-negative-echo@research-toolkit-marketplace
```

安装后新建 Codex 任务，使 Skills、Hooks 和 MCP 工具加载。

## 插件与 Skills

### research-toolkit

- Academic Research：`deep-research`、`academic-paper`、`academic-paper-reviewer`、`academic-pipeline`、`academic-research-suite`
- 中国专利：`patent-disclosure-skill` 及其申请、检索、解读、审查答复和专利地图工作流
- Nature：`nature-academic-search`、`nature-citation`、`nature-data`、`nature-figure`、`nature-paper2ppt`、`nature-polishing`、`nature-reader`、`nature-response`、`nature-writing`
- SciPilot：`scipilot-cite-skill`、`scipilot-figure-skill`、`scipilot-writing-skill`
- ITASCA MCP：通过 `uvx itasca-mcp` 启动；桥接文件位于 `plugins/research-toolkit/assets/itasca-mcp-addon.py`

### writing-toolkit

- `humanizer`
- `humanizer-zh`
- `shuorenhua`
- `stop-slop`

### codex-utility-toolkit

- `bilibili-page-reader`
- `design-taste-frontend`
- `doc`
- `grilling`
- `imagegen`
- `openai-docs`
- `pdf`
- `powershell-safe-invocation`
- `ppt-master`
- `skill-creator`
- `skill-installer`

### ponytail

完整保留上游插件的 Skills、Hooks、资源、测试和版本：`ponytail`、`ponytail-review`、`ponytail-audit`、`ponytail-debt`、`ponytail-gain`、`ponytail-help`。

### no-negative-echo

保留上游 Skill 与生命周期 Hooks，用于在任务启动、恢复、压缩和子代理启动时加载最终交付面检查规则。首次启用 Hooks 时应通过 `/hooks` 审查并信任。

### watermarks-remover

面向用户拥有或获授权处理的内容，检测并清理不可见 Unicode、C2PA、EXIF、XMP 和常见文档容器元数据。Skill 连接本机回环地址上的原生 Python 服务；核心路径要求 Python 3.10+，ExifTool 与 QPDF 可增强文件处理能力。

启动与检查：

```powershell
git clone https://github.com/guillaumemeyer/watermarks-remover.git "$env:USERPROFILE\watermarks-remover-service"
python "$env:USERPROFILE\watermarks-remover-service\service\scripts\server.py" --host 127.0.0.1 --port 8765
curl.exe -s http://127.0.0.1:8765/health
```

插件内 `Start-Service.ps1` 支持按需隐藏启动，使用结束后保持运行。远程服务地址和鉴权通过本机环境变量配置。

## 主要本机依赖

### PPT Master

完整 Skill、脚本、模板和 `requirements.txt` 随插件分发。首次使用前，在已安装的 Skill 目录运行：

```powershell
python -m pip install -r .\requirements.txt
```

它可能按任务启动本机预览服务、访问用户指定网页、调用外部转换程序或可选图像服务。只处理可信输入，并把可选服务凭据保存在本机环境变量或私有配置中。

### 专利工具

Markdown 主流程无需额外 Python 包。按需安装：

| 功能 | 依赖 |
|---|---|
| Word/PPT、公式与交付文件 | `requirements.txt` |
| 国知局检索 | `tools/requirements-cnipa.txt` 与 Playwright Chromium |
| PDF 专利解读 | `tools/patent_reader/requirements.txt` |
| Mermaid 图片 | Node.js 与 `tools/` 内 npm 依赖 |

涉及浏览器运行时下载或写入 Obsidian 库时，应先确认目标路径和数据范围。

### Hooks

Ponytail 与 No Negative Echo 的生命周期 Hooks 需要 PATH 中可用的 Node.js。初始化和更新脚本会检查运行时。

## 更新

在仓库目录运行：

```powershell
git pull --ff-only
pwsh -NoLogo -NoProfile -File .\scripts\Update-Marketplace.ps1
```

也可以直接刷新：

```powershell
codex plugin marketplace upgrade research-toolkit-marketplace
codex plugin add research-toolkit@research-toolkit-marketplace
codex plugin add writing-toolkit@research-toolkit-marketplace
codex plugin add codex-utility-toolkit@research-toolkit-marketplace
codex plugin add ponytail@research-toolkit-marketplace
codex plugin add watermarks-remover@research-toolkit-marketplace
codex plugin add no-negative-echo@research-toolkit-marketplace
```

更新后新建 Codex 任务。

## 自动同步

`.github/workflows/sync-sources.yml` 每天北京时间 01:47 检查上游，也支持手动触发。流程会：

1. 更新 `sources.json` 中的上游 commit SHA；
2. 只复制已确认可再分发的 Skill、插件或指定子目录；
3. 保留许可证并拒绝越界路径、符号链接和凭据类文件；
4. 更新发生内容变化的插件补丁版本；
5. 校验 Marketplace、全部插件清单、SKILL.md、MCP 配置和来源锁；
6. 只在全部校验通过且内容发生变化时提交。

## 卸载

```powershell
codex plugin remove research-toolkit@research-toolkit-marketplace
codex plugin remove writing-toolkit@research-toolkit-marketplace
codex plugin remove codex-utility-toolkit@research-toolkit-marketplace
codex plugin remove ponytail@research-toolkit-marketplace
codex plugin remove watermarks-remover@research-toolkit-marketplace
codex plugin remove no-negative-echo@research-toolkit-marketplace
codex plugin marketplace remove research-toolkit-marketplace
```

## 版本回退

把 Marketplace 固定到已知提交：

```powershell
codex plugin marketplace remove research-toolkit-marketplace
codex plugin marketplace add https://github.com/ToddModica/codex-upstream-skills-marketplace.git --ref <commit-sha>
codex plugin add research-toolkit@research-toolkit-marketplace
```

恢复最新版本时重新注册 `--ref main`，再运行更新脚本。

## 多设备部署

公开上游 Skills 只需提供：

```text
https://github.com/ToddModica/codex-upstream-skills-marketplace
```

需要完整个人配置时，再提供私有仓库地址并在新设备登录有访问权的 GitHub 账号：

```text
https://github.com/ToddModica/codex-personal-skills-marketplace
```

每台设备分别安装必要运行时，并在本机配置 API Key、Token、Cookie 或其他凭据。这些值不进入 Marketplace 仓库。

## ZCode

ZCode 可使用根目录 `.zcode-plugin/marketplace.json`，Codex 使用 `.agents/plugins/marketplace.json`；两份清单指向相同 `plugins/` 内容。

## 维护者校验

```powershell
python .\scripts\update_sources.py
python .\scripts\sync_sources.py --remote
python .\scripts\validate_catalog.py
python .\tests\test_generate_sources.py
```

上游许可证与来源锁的详细状态见 `sources.json` 和 `THIRD_PARTY_NOTICES.md`。
