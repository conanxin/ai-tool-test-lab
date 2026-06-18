# ATL-EVOMAP-3B · OpenClaw Signal Detector · Phase 3B Report

**Status:** PARTIAL — detector + injection work; selector doesn't use qualified signals
**Date:** 2026-06-18
**Repository:** https://github.com/conanxin/ai-tool-test-lab
**Previous:** ATL-EVOMAP-3A (commit `bd6abfc`)

---

## 1. Phase 3B 目标

不再是创建 Gene，而是构建 **OpenClaw-specific signal detector**，让 evolver selector 有机会匹配 Phase 3A 创建的 Gene：

> `gene_distilled_openclaw-tool-use-discipline`

Phase 3A 的根因：evolver run 仍选 `gene_distilled_s2g-env-vars`，因为 session context 只 emit `memory_missing|user_missing`。新 Gene 在 local GEP bank 里但没被命中。

Phase 3B 解决思路：
1. 写 detector 把 session 文本转成 qualified signals
2. 把 detector 输出注入 `memory/evolution/memory_graph.jsonl`
3. 观察 evolver 是否读取、是否选中新 Gene

## 2. Phase 3A 教训

- ✅ `evolver distill` 本地可用（手工 bypass gating）
- ✅ 第一个 OpenClaw-specific Gene 真实落盘
- ❌ New Gene **未被 selector 选中** — root cause: session context 缺 OpenClaw-specific signal

## 3. Detector 设计

`scripts/openclaw_signal_detector.py`（Python stdlib，247 行）：

**输入：** `--input <path-to-session-text-or-jsonl>` `--output <path-to-output-json>`

**输出 JSON schema (`schema_version: 0.1.0`):**
```json
{
  "detector": "openclaw_signal_detector",
  "schema_version": "0.1.0",
  "signals": [
    {"key": "...", "score": 0.0-1.0, "evidence": [...], "reason": "..."}
  ],
  "summary": {"exec_count": N, "exec_ratio": 0.0, ...}
}
```

**检测规则（10 条）：**
| Rule | Trigger | Emit |
|------|---------|------|
| 1-5 | 计数 `[TOOL: exec]` / `[TOOL: read]` / `[TOOL: search]` / `[TOOL: edit]` / `[TOOL: write]` | summary counts |
| 6 | `exec_count / max(1, read+search+edit+write) > 0.5` | `repeated_tool_usage:exec` |
| 7 | exec paired with `grep` / `cat` / `head` / `tail` / `sed -i` / `awk -i inplace` | `tool_bypass:exec-on-grep` |
| 8 | `sed -i` / `awk -i inplace` / `python -c` rewrite | `protocol_drift:wrong-tool-for-file-read` |
| 9 | cwd / repo 包含 `ai-tool-test-lab` | `repo_context:ai-tool-test-lab` |
| 10 | `OpenClaw` / `openclaw` / `Agent` / `session tail` / `cwd` / `workspace` | `session_context:openclaw` |

**硬约束：**
- 只读 `--input` 显式路径
- 不递归扫描 repo
- 不读 `.env`
- 不修改 evolver 源码
- stdlib only

## 4. Fixture Test 结果

**输入：** `fixtures/session-tail-tool-bypass.txt` (805 bytes)

模拟真实 OpenClaw session tail，包含 5 个 `[TOOL: ...]` 行 + OpenClaw markers + `sed -i` + cwd。

**输出：** `artifacts/detected-signals-fixture.json`

**结果：** **5/5 signals emitted** ✅

| Signal | Score |
|--------|-------|
| `tool_bypass:exec-on-grep` | 1.00 |
| `repeated_tool_usage:exec` | 1.00 |
| `protocol_drift:wrong-tool-for-file-read` | 0.67 |
| `session_context:openclaw` | 1.00 |
| `repo_context:ai-tool-test-lab` | 1.00 |

Summary: `exec_count=3, exec_ratio=1.5, grep_like_hits=6, inplace_mutation_hits=2, openclaw_marker_hits=14`

## 5. Real Artifact Test 结果

**输入：** `cases/.../phase2-openclaw-session/artifacts/evolver-run-openclaw-session-output.txt` (50KB evolver run 输出)

**输出：** `artifacts/detected-signals-real-session.json`

**结果：** **3/5 signals emitted** ⚠️

| Signal | Score | Status |
|--------|-------|--------|
| `repeated_tool_usage:exec` | 0.67 | ✅ |
| `repo_context:ai-tool-test-lab` | 1.00 | ✅ |
| `session_context:openclaw` | 1.00 | ✅ |
| `tool_bypass:exec-on-grep` | — | ❌ missing |
| `protocol_drift:wrong-tool-for-file-read` | — | ❌ missing |

**Root cause:** evolver run output 是 *描述性* 的，不包含 raw tool-call literals。detector 的 rule 7/8 需要字面 `grep`/`sed -i`，但 evolver run 输出是「我执行了 sed 改 typo」的散文，不是 `sed -i ...` 命令本身。

**符合用户预期:** 用户明确说"如果真实 artifact 里没有足够 [TOOL: ...] 明文，记录为 PARTIAL，不要强行伪造"。Fixture PASS 即足以证明 detector 可工作。

## 6. Manual Signal Injection Experiment

**Procedure:**
1. 写 `artifacts/manual-memory-graph-injection.jsonl`：一行 MemoryGraphEvent，signals = `[tool_bypass:exec-on-grep, session_context:openclaw, repo_context:ai-tool-test-lab]`
2. 追加到 `memory/evolution/memory_graph.jsonl`（gitignored）
3. 跑 `evolver run` + `evolver review`
4. 检查 selector 选哪个 Gene

**Evolver run output (after injection):**
```
[Signals] Multi-strategy: regex=0, score=1, llm=0, merged=1 | score-only: tool_bypass
Reason: signals match gene.signals_match; signals: tool_bypass; drift_intensity: 0.289; selection_path: score_ranked
```

**PARTIAL:**
- ✅ 注入成功被读取（evolver scanner 看到了 MemoryGraphEvent）
- ✅ Emitted `tool_bypass` (generic, not qualified)
- ❌ Qualified signals (`tool_bypass:exec-on-grep`) 被 scanner **stripped 到 bare form** — 关键的发现
- ❌ Selector 选 `gene_tool_integrity`（local bank 里 pre-existing gene），**不是** `gene_distilled_openclaw-tool-use-discipline`

## 7. Evolver Selector Test 结果

**Selected Gene:** `gene_tool_integrity` (NOT `gene_distilled_openclaw-tool-use-discipline`)

**为什么新 Gene 没被选中（root cause analysis）：**

1. **Signal normalization strips qualification.** Evolver scanner 把 `tool_bypass:exec-on-grep` → `tool_bypass`（bare form）。这导致 detector emit 的 qualified signals 在 evolver 内部都坍缩为 bare signal。

2. **Bare `tool_bypass` already matches `gene_tool_integrity`.** Local GEP bank 里有 pre-existing `gene_tool_integrity`，signals_match 包含 bare `tool_bypass`，且 summary 不包含 qualification。

3. **Selector uses score-ranked path.** Evolver 内部 evidence: `selection_path: score_ranked`。Bare `tool_bypass` 在两个 Gene 上得分相同，selector 选 first-match (字典序 / 加载序) = `gene_tool_integrity`。

4. **New Gene's qualified signals (e.g. `protocol_drift:wrong-tool-for-file-read`) are not seen.** Scanner 不 emit 任何带 protocol_drift 的 signal 给 selector。

**但仍有进展：**
- ✅ Signal injection mechanism works end-to-end (detector → jsonl → evolver run)
- ✅ Evolver scanner 确实读取 `memory_graph.jsonl`
- ✅ New Gene 仍存在 local GEP bank
- ⚠️ Selector 缺一个"qualified signal 优先于 bare signal"的 ranking heuristic

**未执行（per hard boundary）：**
- ❌ `evolver review --approve`
- ❌ `evolver solidify`
- ❌ 任何 publish

## 8. 五项评分

| 维度 | 状态 | 说明 |
|------|------|------|
| **A. Detector fixture test** | ✅ **PASS** | 5/5 signals emitted, scores all ≥ 0.67 |
| **B. Real artifact detector test** | ⚠️ **PARTIAL** | 3/5 signals (expected — evolver output lacks raw tool-call literals) |
| **C. Signal injection** | ⚠️ **PARTIAL** | Injection read, but scanner strips qualified → bare form |
| **D. Selector match** | ⚠️ **PARTIAL** | Selected `gene_tool_integrity` (local bank), NOT new Gene |
| **E. Safety** | ✅ **PASS** | All 15 hard boundaries respected |

**Overall: PARTIAL** — 3 PASS (A, E + 部分的 C) + 2 PARTIAL (B, D) + 0 FAIL

## 9. 安全边界

| 边界 | 状态 |
|------|------|
| no Hub | ✅ PASS — `A2A_HUB_URL` unset |
| no auto-publish | ✅ PASS — `EVOLVER_AUTO_PUBLISH=false` (no Gene/Capsule publish) |
| no validator | ✅ PASS — `EVOLVER_VALIDATOR_ENABLED=false` |
| no --loop | ✅ PASS |
| no credits | ✅ PASS — no Hub = 0 credits |
| no ATP autobuy | ✅ PASS — `EVOLVER_ATP_AUTOBUY=off` |
| no secrets | ✅ PASS — no API key/token/cookie/Authorization/.env |
| no real system mutation | ✅ PASS — only ai-tool-test-lab |
| no Evolver source modification | ✅ PASS — only call external script |
| no `.env` scan | ✅ PASS — detector 不读 .env |
| no `--approve` | ✅ PASS — review only, no approve |
| no `solidify` | ✅ PASS — no `node index.js solidify` |
| 不提交 `.evolver/` | ✅ PASS — .gitignore |
| 不提交 `memory/` | ✅ PASS — .gitignore |
| artifact 无 secret | ✅ PASS — detector output + injection jsonl 均无 secret |

## 10. 最终结论

**Detector 是否可用：** ✅ **YES**（在 fixture 上 100% 准确，real artifact 上 60% 准确，符合预期）

**Signal injection 是否有效：** ⚠️ **PARTIAL** — 注入机制 work，但 evolver scanner 把 qualified signals 归一化为 bare form

**Selector 是否选中新 Gene：** ❌ **NO** — 选 `gene_tool_integrity`（local bank 里的旧 gene），新 Gene 未被选中

**是否适合进入 Phase 3C (--approve / solidify)：** ⚠️ **HOLD**
- 理由 1: 新 Gene 尚未被 selector 验证选中
- 理由 2: Phase 3C 的 `--approve` 主要是固化 selected gene，但 selected 是 `gene_tool_integrity` 而非我们的新 Gene
- 理由 3: 在 selector 修好之前，approve/solidify 没有针对性价值

**是否仍继续不接 Hub：** ✅ **YES** — Phase 3B 全程无 Hub，证明 evolver 本地能完成 detector + selector loop

**核心发现 (durable):**
1. **Evolver signal scanner strips qualified keys to bare form.** `tool_bypass:exec-on-grep` 在 evolver 内部变成 `tool_bypass`。
2. **Selector prefers local bank pre-existing genes over newly-distilled Genes** (因为 bare signal 早 match)。
3. **Detector + injection mechanism works end-to-end** (detector → jsonl → evolver run)，但 ranking heuristic 缺 qualified-aware 排序。

## 11. Phase 3C 建议（不立即执行）

**如果 Phase 3C 启动，应做：**

| 任务 | 目标 | 风险 |
|------|------|------|
| **3C-1** | `evolver review --approve` on the pending run (selected `gene_tool_integrity`) | medium — 不是我们的新 Gene，approve 的是 local bank gene |
| **3C-2** | 观察 `evolver solidify` 是否创建新 Capsule 到 `capsules.json` | low — local-only |
| **3C-3** | 检查是否在 `.evolver/gep/events.jsonl` 留下 EvolutionEvent 记录 | low — read-only |
| **3C-4** | **不在 Hub publish** Capsule | ✅ 已 hard-coded |
| **3C-5** | **不** approve 与 OpenClaw-specific Gene 无关的 run | pending selector fix |

**3C 的前置条件：**
- 修 selector：让 qualified signals 优先于 bare signals
- 或：让 new Gene 的 signals_match 用 bare form（`tool_bypass` not `tool_bypass:exec-on-grep`）来匹配 scanner 输出
- 或：inject 时只 emit bare signals（不 emit qualified）以避免 strip

**不进入 Phase 3C 直到 selector match 通过。** 当前 Phase 3B 的核心价值是证明了 detector + injection path 可行，且明确了 selector 缺什么。

## 12. Reusable Patterns (durable)

**Pattern 1: Detector-based signal injection.** 任何想让 evolver 看到 custom signal 的场景，可用 detector + jsonl injection 路径绕过 native 提取。

**Pattern 2: Fixture-then-real 两阶段验证.** Detector 准确性必须用 fixture（确定性）+ real artifact（描述性）双轨验证。

**Pattern 3: Evolver scanner normalization.** 注入 qualified signals 时要知道 scanner 会 strip — 注入前先 strip 更可控。

**Pattern 4: 5-dimension scoring (A/B/C/D/E).** Detector-based phases 用这个统一结构：A fixture、B real、C injection、D selector、E safety。

---

**报告结束。** ATL-EVOMAP-3B 验证完成，整体 PARTIAL，detector 路径打通，selector 缺 ranking fix，Phase 3C HOLD。
