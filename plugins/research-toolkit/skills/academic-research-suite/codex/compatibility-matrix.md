# ARS Codex Compatibility Matrix

Audit date: 2026-07-17

## Provenance

| Surface | Evidence |
|---|---|
| Codex package repo | `academic-research-skills-codex` current working tree before release commit |
| Upstream Claude Code repo | Tracked in `skills/academic-research-suite/manifest.json` |
| Upstream suite version | `v3.17.0` |
| Codex package version | `0.1.19` |
| License | CC BY-NC 4.0 in upstream and Codex package |
| Upstream sync status | Vendored `ars/` content synced to ARS release `v3.17.0` (`039d94f`); Codex adapter profile retained |
| Codex-only adapter location | `skills/academic-research-suite/codex/` |

## Matrix

| Capability | Default Codex Status | Optional Full-Runtime Profile | Parity Level | Implementation Location | Verification Method | Remaining Risk |
|---|---|---|---|---|---|---|
| Install / update | One Codex skill path, not a Claude plugin | No change; install remains the root skill path | partial | `README.md`, `manifest.json` | `/skills`; `single-root-skill` gate | No native Claude marketplace lifecycle in Codex |
| `ars-*` aliases | Root router emulates Claude command intent | Deterministic planner emits the same alias route metadata | near | `SKILL.md`, `codex/full-runtime-manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | adapter pytest; manifest gate | Slash-prefixed input can still be intercepted by a client |
| Vague paper-topic routing | Root router sends vague paper topics to Socratic scoping | Planner preserves the same override | near | `SKILL.md`, `codex/scripts/ars_codex_full_runtime.py` | adapter pytest; upstream router tests | Natural-language routing is still heuristic outside smoke cases |
| Agent prompts | `agents/*.md` are read inline as role/phase prompts | `codex/agents/*.md` provides opt-in agent-team templates pointing back to source prompts | near | `ars/*/agents/*.md`, `codex/agents/*.md` | manifest gate; reviewer fixture gate | Actual subagent availability depends on the active Codex runtime |
| Agent least privilege | Protected top-level agent `tools:` allowlists remain role boundaries; inline use does not widen authority | Dispatched protected roles receive no Bash or network transport; the dispatcher owns cross-model transport | near | `ars/agents/*.md`, `ars/scripts/check_tools_allowlist.py`, `SKILL.md` | upstream tools-allowlist lint and tests | Actual enforcement still depends on the active Codex runtime's tool controls |
| Reviewer independence | Inline mode must preserve independent reviewer sections before synthesis | Agent-team planner orders independent reviewer sections before editorial synthesis | near | `codex/agents/paper-reviewer-panel.md`, `codex/tests/fixtures/reviewer_full_independent_sections.md` | reviewer fixture gate; adapter pytest | Inline runs rely on faithfully preserving section boundaries |
| Executable panel synthesis | Reviewer artifacts can be checked with the vendored closed-grammar panel checker | Planner exposes the checker as a review quality gate | near | `ars/scripts/check_panel_synthesis.py`, `codex/full-runtime-manifest.json` | upstream panel checker tests | The checker validates artifact self-consistency, not substantive correctness |
| Hooks | Upstream Claude hooks are metadata only | Disabled-by-default read-only Codex hook pack | partial | `codex/hooks/hooks.json`, `codex/scripts/ars_codex_hook.py` | `hook-safety` gate | Hook installation format can differ by Codex client |
| Model routing | Claude `opus` / `sonnet` hints are metadata | Planner reports model hints without forcing model changes | partial | `codex/full-runtime-manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | adapter pytest; plan inspection | Not equivalent to Claude Code model pinning |
| ARS model tiering | Unset preserves the active Codex model | Planner surfaces `economy` / `quality-boost` as advisory metadata; classification is applied only when per-dispatch model selection exists | partial | `ars/shared/model_tiering.md`, `ars/scripts/model_tiering_manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | upstream tiering lint; adapter pytest | Codex runtimes may not expose relative-tier or per-dispatch model control |
| Material Passport | Prompt/procedure plus vendored validators | Full-runtime manifest exposes passport reset as a quality gate | near | `ars/scripts/check_passport_reset_contract.py`, `codex/full-runtime-manifest.json` | upstream validator; adapter gate | Runtime context isolation is procedural, not a hard sandbox |
| Citation / claim / temporal integrity | Vendored validators can be run when needed | Planner surfaces relevant gates in the route plan | partial | `ars/scripts/*claim*`, `ars/scripts/temporal_integrity_audit.py`, `codex/full-runtime-manifest.json` | upstream validators; adapter tests | External metadata/API checks require configuration |
| Cross-model verification | Disabled by default; explicit provider configuration and user consent required | Canonical handoff envelope is validated by the dispatcher; only the payload is transported and unavailable results are reported | near | `README.md`, `SKILL.md`, `ars/shared/cross_model_verification.md`, `ars/scripts/cross_model_handoff.py`, `codex/full-runtime-manifest.json` | hermetic handoff and contract tests | External-provider availability depends on user-supplied API credentials |
| Degradation provenance | Machine-readable registry records each graceful-degradation mechanism and its downstream effect | Planner exposes the registry checker as an integrity gate | near | `ars/shared/contracts/degradation_registry.json`, `ars/scripts/check_degradation_registry.py` | upstream registry tests | Runtime outages still require honest reporting to the user |
| Pipeline terminal semantics | Stage 5 entry/completion and Stage 6 decline/terminal acknowledgement follow the pinned upstream contract | Planner exposes the whole-file boundary lock | near | `ars/academic-pipeline/WORKFLOW.md`, `ars/scripts/check_pipeline_boundary_semantics.py` | upstream boundary tests | Interactive clients may express acknowledgement with different natural language |
| Upstream lock provenance | `manifest.json` pins upstream commits | Quality gate checks the package manifest has a full upstream SHA and required included paths | near | `manifest.json`, `codex/scripts/ars_codex_quality_gates.py` | `upstream-lock` gate | Future upstream syncs still require deliberate manifest updates |

## Exact Degradations Relative To Claude Code

- Codex does not register native Claude slash commands; `ars-*` aliases are
  parsed by the root skill and optional full-runtime planner.
- Codex full-runtime agent-team mode is opt-in and planner/template based.
  Inline execution remains the default.
- Claude Code plugin marketplace install/update is not reproduced.
- Claude Code `SessionStart` and future `SubagentStop` hooks are not installed
  automatically. The Codex hook pack is manual and read-only.
- `opus` / `sonnet` command frontmatter is preserved as metadata; the active
  Codex model is used unless the user/runtime provides an explicit override.
- `ARS_MODEL_TIERING` preserves the upstream agent classification, but cannot
  force economy or quality-boost routing without a runtime model override.
- External cross-model verification is never simulated silently.
- Dispatched owner roles do not perform cross-model transport themselves; the
  dispatching Codex context validates the canonical envelope and transports
  only its payload after the existing consent gate.
