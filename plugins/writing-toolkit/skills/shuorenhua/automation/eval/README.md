# Benchmark Eval Harness — 运行说明

> v1.9.0 起使用的模型实跑入口；2026-07-11 起改盲测口径（见下节）。
> Prompt 本体见 `./rewrite-prompt.md` 和 `./judge-prompt.md`。
> 这份 README 只解决"具体怎么跑一次"。

## 盲测口径（2026-07-11 起）

旧口径的问题：被测模型直接读 `evals/benchmark.md`，每条用例的 `预期` / `理由` 就在原文旁边，编号前缀（SF / SNF）和标题也暴露该改还是不该改——测出来的是 instruction-following，不是规则在陌生文本上的泛化。

现口径：

- 被测模型只读 `evals/benchmark-blind.md`：匿名编号（B-xx）、顺序打乱、只含场景和原文。
- judge 用 `evals/benchmark-map.md` 把 B-xx 映射回 SF/SNF 编号，再按 `benchmark.md` 的预期判分。
- 两个盲测文件由 `python3 automation/eval/make_blind.py` 生成（固定种子，可复现）；`benchmark.md` 用例增删后必须重跑，手改生成文件无效。
- 隔离靠 prompt 路径纪律约束，不是硬隔离；如需硬隔离，可在干净目录只放 `SKILL.md`、`references/`、`benchmark-blind.md` 再跑（v2.2.0 硬判脚本时再评估是否内置）。

## 文件约定

工具本体（committed）：

| 角色 | 路径 |
|------|------|
| 被测模型改写 prompt | `automation/eval/rewrite-prompt.md` |
| 交叉判分 prompt | `automation/eval/judge-prompt.md` |
| 盲测生成脚本 | `automation/eval/make_blind.py` |
| 盲测输入（生成物） | `evals/benchmark-blind.md` |
| 盲测映射表（生成物） | `evals/benchmark-map.md` |
| 运行说明 | `automation/eval/README.md`（本文件） |

运行实例（local-only，`tasks/` 在 `.gitignore` 内）：

| 角色 | 路径 |
|------|------|
| Codex 改写输出 | `tasks/current/eval-runs/<YYYY-MM-DD>-codex/rewrite-<batch>.md` |
| Claude 改写输出 | `tasks/current/eval-runs/<YYYY-MM-DD>-claude/rewrite-<batch>.md` |
| Claude 判 Codex | `tasks/current/eval-runs/<YYYY-MM-DD>-judge/claude-judge-codex-<batch>.md` |
| Codex 判 Claude | `tasks/current/eval-runs/<YYYY-MM-DD>-judge/codex-judge-claude-<batch>.md` |

第一次使用前先建目录：

```bash
mkdir -p tasks/current/eval-runs/2026-06-18-codex \
  tasks/current/eval-runs/2026-06-18-claude \
  tasks/current/eval-runs/2026-06-18-judge
```

## 批次划分

默认按 5 批跑（盲测编号连续切段，每批 SF/SNF 天然混排）：

| batch | 区间 |
|-------|------|
| `B01-16` | B-01 到 B-16 |
| `B17-32` | B-17 到 B-32 |
| `B33-48` | B-33 到 B-48 |
| `B49-64` | B-49 到 B-64 |
| `B65-80` | B-65 到 B-80 |

新增或补跑用例可以单独成批：targeted 补跑先查 `benchmark-map.md` 找到对应 B 编号，按 B 编号下发给被测模型（不要把 SF/SNF 编号透给被测模型），输出命名可用 `targeted-vX.Y.Z`。历史批次（v1.9.x 的 `SF01-14` 等命名）是盲测前的旧口径，归档不改。

如果模型或供应商的上下文 / 输出限制跑不下 5 批之一，可以继续细拆，例如把 `B01-16` 拆成 `B01-08` 和 `B09-16`。文件名保持区间可读即可，最终汇总时按原区间合并。

交叉判分固定为：

- Codex 改写 → Claude 判
- Claude 改写 → Codex 判

## 改写批

Codex 改写一批：

```bash
codex exec -C . -s read-only --ephemeral \
  -o tasks/current/eval-runs/<YYYY-MM-DD>-codex/rewrite-B01-16.md \
  '你正在执行说人话 benchmark 盲测改写实跑。

请完整读取 ./automation/eval/rewrite-prompt.md，按其中 text 代码块里的 prompt 行事。
只使用当前工作目录下的 ./SKILL.md、./references/ 和 ./evals/benchmark-blind.md；禁止读取 ./evals/ 下的其他文件，不要读取全局安装的 shuorenhua skill 副本。

本轮只处理 ./evals/benchmark-blind.md 中 B-01 到 B-16。
请直接输出最终结果，不要附加过程叙述。'
```

Claude 改写一批：

```bash
claude --print --model opus \
  --name shuorenhua-eval-rewrite-B01-16 \
  --disallowedTools Edit Write \
  > tasks/current/eval-runs/<YYYY-MM-DD>-claude/rewrite-B01-16.md <<'EOF'
你正在执行说人话 benchmark 盲测改写实跑。

请完整读取 ./automation/eval/rewrite-prompt.md，按其中 text 代码块里的 prompt 行事。
只使用当前工作目录下的 ./SKILL.md、./references/ 和 ./evals/benchmark-blind.md；禁止读取 ./evals/ 下的其他文件，不要读取全局安装的 shuorenhua skill 副本。

本轮只处理 ./evals/benchmark-blind.md 中 B-01 到 B-16。
请直接输出最终结果，不要附加过程叙述。
EOF
```

其余批次只替换区间和输出文件名。

## 判分批

Claude 判 Codex 改写：

```bash
claude --print --model opus \
  --name shuorenhua-eval-judge-codex-B01-16 \
  --disallowedTools Edit Write \
  > tasks/current/eval-runs/<YYYY-MM-DD>-judge/claude-judge-codex-B01-16.md <<'EOF'
你正在执行说人话 benchmark 交叉判分。

请完整读取 ./automation/eval/judge-prompt.md，按其中 text 代码块里的 prompt 行事。
只使用当前工作目录下的 ./evals/、./SKILL.md、./references/ 和被测输出文件，不要读取全局安装的 shuorenhua skill 副本。

盲测区间：B-01 到 B-16
被测输出：./tasks/current/eval-runs/<YYYY-MM-DD>-codex/rewrite-B01-16.md

请直接输出判分表和汇总，不要重写被测输出。
EOF
```

Codex 判 Claude 改写：

```bash
codex exec -C . -s read-only --ephemeral \
  -o tasks/current/eval-runs/<YYYY-MM-DD>-judge/codex-judge-claude-B01-16.md \
  '你正在执行说人话 benchmark 交叉判分。

请完整读取 ./automation/eval/judge-prompt.md，按其中 text 代码块里的 prompt 行事。
只使用当前工作目录下的 ./evals/、./SKILL.md、./references/ 和被测输出文件，不要读取全局安装的 shuorenhua skill 副本。

盲测区间：B-01 到 B-16
被测输出：./tasks/current/eval-runs/<YYYY-MM-DD>-claude/rewrite-B01-16.md

请直接输出判分表和汇总，不要重写被测输出。'
```

其余批次只替换区间、被测输出和输出文件名。

## 小样试跑

调 prompt 时先跑小样，不要直接上全量：

```bash
mkdir -p tasks/current/eval-runs/<YYYY-MM-DD>-smoke

codex exec -C . -s read-only --ephemeral \
  -o tasks/current/eval-runs/<YYYY-MM-DD>-smoke/rewrite-B01-08.md \
  '请完整读取 ./automation/eval/rewrite-prompt.md，按其中 text 代码块里的 prompt 行事。
只使用当前工作目录下的 ./SKILL.md、./references/ 和 ./evals/benchmark-blind.md；禁止读取 ./evals/ 下的其他文件，不要读取全局安装的 shuorenhua skill 副本。

本轮只处理 ./evals/benchmark-blind.md 中 B-01 到 B-08。
请直接输出最终结果，不要附加过程叙述。'

claude --print --model opus \
  --name shuorenhua-eval-smoke-judge \
  --disallowedTools Edit Write \
  > tasks/current/eval-runs/<YYYY-MM-DD>-smoke/judge-B01-08.md <<'EOF'
请完整读取 ./automation/eval/judge-prompt.md，按其中 text 代码块里的 prompt 行事。
只使用当前工作目录下的 ./evals/、./SKILL.md、./references/ 和被测输出文件，不要读取全局安装的 shuorenhua skill 副本。

盲测区间：B-01 到 B-08
被测输出：./tasks/current/eval-runs/<YYYY-MM-DD>-smoke/rewrite-B01-08.md

请直接输出判分表和汇总，不要重写被测输出。
EOF
```

小样只看格式是否可对照：

- 每条改写输出都有 `## <编号>`。
- 每条都有固定判定链。
- judge 只输出固定三列表格。
- 汇总里有 SF 通过、SNF 误杀、⚠️ / ❌ 清单。

如果格式不顺，最多改 prompt 后再跑一轮；第二轮仍不顺就停下，不要继续全量。
