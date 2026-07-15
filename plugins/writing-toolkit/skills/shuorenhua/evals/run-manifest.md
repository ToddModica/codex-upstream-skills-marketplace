# 评测运行清单 | Run Manifest

> 2026-07-11 新增（发布前 deep review 反馈：外部读者无法核对实跑口径）。每次基线 / targeted 实跑在这里登记元数据；`results-*.md` 只放判分结论和硬指标，这里放"怎么跑出来的"。
> 原始模型输出在维护者本地 `tasks/current/eval-runs/`（gitignored），默认不入库；外部复现按 `automation/eval/README.md` 的命令自跑。
> 历史轮次按当时记录回填，缺项如实标「未记录」，从下一轮起按模板补齐。

## v1.9.0 全量双模型基线（2026-06-18）

- 评测集：`benchmark.md` @ v1.9.0（73 条：41 SF + 32 SNF）；仓库同期含 `real-samples.md` 19 条场景样本，本轮未纳入批跑（批次只覆盖 SF/SNF，无 RS-xx 运行记录）
- 口径：双模型交叉——Codex 改写 → Claude 判；Claude 改写 → Codex 判。盲测未启用（当时被测模型可见预期；盲测 2026-07-11 起才有）
- 被测 / 判分模型：Codex CLI（具体模型版本未记录）；Claude Code `--model opus`（Claude Opus 4.8，dated model id 未记录）
- CLI 版本：未记录
- 归档：`results-v1.9.0.md`（含 token / 成本 / 判分汇总）
- 原始输出：本地 `tasks/current/eval-runs/2026-06-18-{codex,claude,judge}/`（未入库）

## v1.9.1 targeted 单模型回归（2026-07-01）

- 评测集：`benchmark.md` @ v1.9.1（75 条：42 SF + 33 SNF）；范围 = v1.9.0 的 8 个边界用例 + #5 回归用例
- 口径：targeted 单模型回归 + 静态规则检查，非全量实跑
- 模型：具体版本未记录
- 归档：`results-v1.9.1.md`
- 原始输出：本地 `tasks/current/eval-runs/2026-07-01-v1.9.1-targeted/`（未入库）

## v1.9.2 targeted 交叉回归（2026-07-05）

- 评测集：`benchmark.md` @ v1.9.2（80 条：45 SF + 35 SNF）；范围 = 新增 5 条（SF-43/44/45、SNF-34/35）
- 口径：targeted 交叉回归（Codex 改写 + Claude 判读），非全量实跑
- 模型：具体版本未记录
- 归档：`results-v1.9.2.md`
- 原始输出：本地 `tasks/current/eval-runs/2026-07-05-v1.9.2-targeted/`（未入库）

## v2.0.0 盲测口径 smoke（2026-07-15）

- 评测集：`benchmark.md` @ v2.0.0（80 条：45 SF + 35 SNF）；范围 = B-01–08 流程 smoke + B-58/B-78 定向（SF-23/SF-15 预期修订专项），共 10 条
- 口径：盲测首跑（`benchmark-blind.md` 生成于 2026-07-15 工作区，种子 20260711）；目的 = 端到端流程验证 + 保真合同专项，非基线，判分结果不计入版本指标
- 被测模型：Codex CLI（盲改写；模型版本未记录）
- judge 模型：Codex 同线程自判一份（偏离交叉惯例，留档对照）+ Claude Code（Claude Fable 5，`claude-fable-5`）按固定配对补做独立交叉判分
- CLI 版本：codex 未记录 / claude 2.1.210
- 结论：格式合同全对齐（B 编号标题、四项判定链、三列判分表、汇总四件套）；B-58/B-78 输出无编造数据或技术选型，SF-15/SF-23 修订后合同端到端生效；判分汇总（交叉判）SF 3/7 ✅、SNF 误杀 0/3、❌ 无
- 已知缺口：`make_blind.py` 不传递 benchmark J 节的节级 scope 指令（SF-39 保长度 / SF-40 in-place），被测模型只见 `public-writing / long` 会按默认 bounded 处理；修掉之前 judge 对这两条不因 scope 判定记 ❌，修法待 v2.1.0 评估
- 原始输出：`tasks/current/eval-runs/2026-07-15-smoke/`（未入库）

## 登记模板（新一轮实跑照抄填写）

```markdown
## vX.Y.Z <全量基线|targeted 回归>（YYYY-MM-DD）

- 评测集：`benchmark.md` @ vX.Y.Z（N 条：a SF + b SNF）；范围 = <全量|用例列表>
- 口径：<双模型交叉|targeted>；盲测 = 是（benchmark-blind.md 生成于 <日期/commit>）
- 被测模型：<CLI + 确切模型版本，如 dated model id>
- judge 模型：<CLI + 确切模型版本>
- CLI 版本：codex <ver> / claude <ver>
- 归档：`results-vX.Y.Z.md`
- 原始输出：`tasks/current/eval-runs/<目录>`（未入库；如对外公开争议判定，摘录脱敏片段进归档）
```
