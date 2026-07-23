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

## v2.1.0 全量盲测 + targeted 多模型回归（2026-07-23）

- 评测集：`benchmark.md` @ v2.1.0（82 条：46 SF + 36 SNF）；范围 = 82 条全量 + 10 条核心 targeted + 6 条共同问题最终 targeted
- 口径：全量双模型交叉（Codex 改写 → Claude 判；Claude 改写 → Codex 判）；盲测 = 是（种子 `20260711`）；Grok / Gemini 只作 targeted 模型差异诊断
- 被测模型：Codex CLI `gpt-5.6-sol`；Claude Code `opus→claude-opus-4-8`；Grok `grok-4.5→grok-4.5-build`；Agy `gemini-3.6-flash-medium→Gemini 3.6 Flash (Medium)`
- judge 模型：Claude Code `claude-opus-4-8` 判 Codex；Codex CLI `gpt-5.6-sol` 判 Claude / Grok / Gemini
- CLI 版本：codex 0.145.0 / claude 2.1.218 / grok 0.2.111 / agy 1.1.5
- 全量结果：Codex SF 38/46、SNF 误杀 1/36；Claude SF 26/46、SNF 误杀 1/36；全量发生在最终 6 条共享问题修复前，修复后只重跑 targeted
- 核心 targeted：Codex SF 9/9、SNF 误杀 0/1；Claude SF 6/9、SNF 误杀 0/1
- provenance：三体 live doctor 全绿；Grok session verifier 与 Agy conversation verifier 均通过；Grok targeted 因 B-11 标题前夹过程叙述而不计正式 harness 分数
- 最终入口合同微测：对齐 `SKILL.md` / rewrite prompt / README 后补跑 B-11 + B-61；Codex 与 Claude 均按新合同处理无源数字与 bounded 删除清单，不重算全量分数
- 归档：`results-v2.1.0.md`
- 原始输出：`tasks/current/eval-runs/2026-07-23-v2.1.0-{targeted,full,final-targeted}/`（未入库）

## v2.1.0 Fable 结构修复后双列协议 smoke（2026-07-23）

- 评测集：`benchmark.md` @ v2.1.0（82 条：46 SF + 36 SNF）；范围 = B-05 / B-13 / B-19 / B-40 / B-45 / B-55（SF-36 / SF-05 / SF-40 / SF-42 / SF-18 / SNF-34）
- 口径：复用 Fable 结构修复后生成的双模型盲改写，在最终 judge 协议上重新交叉判分；目的 = 验证 audit-only、方向认证、L3 可接受集与 SNF/L1 分列，不替代 82 条全量
- 被测模型：Codex CLI `gpt-5.6-sol`；Claude Code `opus→claude-opus-4-8`
- judge 模型：Claude Code `claude-opus-4-8` 判 Codex；Codex CLI `gpt-5.6-sol` 判 Claude
- CLI 版本：codex 0.145.0 / claude 2.1.218
- 结果：两边 L1 硬约束失败均为 0，SF 均为 5/5；Claude 输出 SNF 误杀 0/1，Codex 输出在 SNF-34 发生普通标点误杀 1/1。新版协议把后者稳定判为「硬约束 ✅、SNF 误杀 ❌」，没有再误算成 L1
- 归档：`results-v2.1.0.md` §6
- 原始输出：`tasks/current/eval-runs/2026-07-23-v2.1.0-rc-verify/`（未入库）

## v2.1.0 最终 82 条全量（2026-07-23）

- 评测集：`benchmark.md` @ v2.1.0（82 条：46 SF + 36 SNF）；范围 = B-01–82，五批完整运行
- 行为合同 diff-id：`41da53fc8f7db08140d695ecc838002186a516ad`；冻结后只追加结果归档，不改规则、benchmark 或 prompt
- 口径：双模型盲改写 + 固定交叉判分；Codex 改写 → Claude 判，Claude 改写 → Codex 判；judge 使用硬约束 / 风格或 SNF 误杀双列协议
- 被测模型：Codex CLI `gpt-5.6-sol`；Claude Code `opus→claude-opus-4-8`
- judge 模型：Claude Code `claude-opus-4-8` 判 Codex；Codex CLI `gpt-5.6-sol` 判 Claude
- CLI 版本：codex 0.145.0 / claude 2.1.218
- 完整性：两套改写均 82/82；两套 judge 均 82/82；无缺号、重复或 L0 作废批次
- Codex 结果：L1 失败 0；L2 41/43；L3 3/3；旧口径 SF 44/46；SNF 误杀 1/36
- Claude 结果：L1 失败 1（SF-27 / B-48）；L2 30/43；L3 3/3；旧口径 SF 33/46；SNF 误杀 3/36
- L1 争议审计：Claude 审计建议只记第二列，Codex 审计建议记 L1；按 `SKILL.md` 信息留存硬指标与 `protected-spans.md` 的 code-context 真实行为保护，最终维持 L1 ❌
- 发布判断：SNF 均 <10%，但 Claude 存在 1 个 L1 失败；正式 v2.1.0 不达门槛
- 归档：`results-v2.1.0.md` §7
- 原始输出：`tasks/current/eval-runs/2026-07-23-v2.1.0-final-full-41da53f/`（未入库）

## v2.1.0 关系保真修复后正式版验证（2026-07-23）

- 评测集：`benchmark.md` @ v2.1.0（82 条：46 SF + 36 SNF）；范围 = Codex / Claude 各一轮 B-01–82 + Claude 一次预先声明的完整稳定性确认轮
- 行为合同 diff-id：`d8408ce9edad998cba0cefcbc6372e84f3f07fb2`；确认轮前后未改规则、benchmark、blind 输入或 prompt
- 口径：82 条盲改写 + 双列 judge；Codex 输出由 Claude Opus 4.8 判。Claude 首轮 B-01–16 由 Codex 判，Codex CLI 随后触发用量上限（提示 2026-07-30 11:25 恢复），B-17–82 与确认轮改由 Grok 4.5 按同一 judge prompt 独立判分
- 被测模型：Codex CLI `gpt-5.6-sol`；Claude Code `opus→claude-opus-4-8`
- judge 模型：Claude Code `claude-opus-4-8`；Codex CLI `gpt-5.6-sol`（仅 Claude 首轮 B-01–16）；Grok `grok-4.5`（替代其余 Claude 输出 judge）
- CLI 版本：codex 0.145.0 / claude 2.1.218；Grok 当前默认模型清单确认 `grok-4.5`
- 完整性：Codex 全量、Claude 首轮、Claude 确认轮的改写与 judge 均为 82/82；无缺号或重复
- Codex 结果：L1 失败 0；L2 37/43；L3 3/3；旧口径 SF 40/46；SNF 误杀 2/36
- Claude 首轮：L1 失败 1（SF-07 / B-71）；L2 36/43；L3 3/3；旧口径 SF 39/46；SNF 误杀 3/36
- Claude 确认轮：不改规则后完整重跑；L1 失败 0；L2 36/43；L3 3/3；旧口径 SF 39/46；SNF 误杀 1/36
- targeted：B-53 / B-65 双模型 L1 均为 0；SF-12 残留单个 `避坑` 按分层记 L2 `⚠️`，不阻塞发布
- 发布判断：Codex 全量与 Claude 确认轮均满足 L1=0、SNF<10%；正式 v2.1.0 可发布。Claude 首轮 SF-07 失败作为随机不服从证据并列保留，不宣称所有运行全绿
- 归档：`results-v2.1.0.md` §8
- 原始输出：`tasks/current/eval-runs/2026-07-23-v2.1.0-release-final-d8408ce/`、`tasks/current/eval-runs/2026-07-23-v2.1.0-release-confirmation-d8408ce/`（未入库）

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
