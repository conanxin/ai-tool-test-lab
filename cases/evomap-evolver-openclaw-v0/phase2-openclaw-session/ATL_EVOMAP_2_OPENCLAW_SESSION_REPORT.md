# ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md
# ATL-EVOMAP-2 · EvoMap Evolver · OpenClaw Session-Context Test · v0

**Case:** evomap-evolver-openclaw-v0
**Phase:** ATL-EVOMAP-2 OpenClaw session-context test
**Status:** openclaw session-context test partial
**Date:** 2026-06-18 (Asia/Shanghai)
**Agent:** OpenClaw minimax/MiniMax-M2.7
**Repo:** https://github.com/conanxin/ai-tool-test-lab
**Parent Phase:** ATL-EVOMAP-1 (commit d8fc23d)

---

## 1. Phase 2 目标

在真实 OpenClaw session 内运行 `evolver run` + `evolver review`，验证 Evolver 能否：
1. 识别 OpenClaw session 的真实行为（tool usage、protocol_drift、session-level signals）
2. 生成与 session 相关的 Gene/Capsule/EvolutionEvent
3. 提供对 OpenClaw 工作流有实际价值的可复用策略

**Phase 1 vs Phase 2 关键区别：**
- Phase 1：构造 arbitrary 失败日志（npm/proxy/systemd/cron），期望 evolver 分析
- Phase 2：在真实 OpenClaw session context 中执行，让 evolver 直接扫描 session 自身

---

## 2. Phase 1 教训回顾

| Phase 1 错误假设 | 实际真相 |
|------------------|----------|
| Evolver 是通用失败日志分析器 | Evolver 是自进化引擎，扫描自身 session context |
| Evolver 读取 `memory/*.log` 文件 | Evolver 扫描 evolver 自己的 session logs / signals |
| Evolver 能诊断 arbitrary 项目失败 | Evolver 只修复自身 protocol_drift |
| `evolver --review` 独立可用 | 需要先 `evolver run` |

**结论：** Phase 1 工具运行完全正确，但测试设计错误。四场景 FAIL 不是 evolver 的 bug。

---

## 3. 本次测试与 Phase 1 的区别

| 维度 | Phase 1 | Phase 2 |
|------|---------|---------|
| 测试数据 | 4 个人造失败日志 | 真实 OpenClaw session |
| 任务内容 | 期望 evolver 诊断 npm/proxy/systemd/cron | 期望 evolver 识别 session 行为 |
| evolver 输入 | 4 个 .log 文件 | OpenClaw 真实 tool calls + session transcript |
| 评估标准 | "能否修复具体业务问题" | "能否从 session 提取 signals" |
| Hub 状态 | 无 Hub | 无 Hub（保持） |

---

## 4. OpenClaw session 任务说明

**任务内容（在 evolver 扫描前完成）：**
1. 读取 `cases/evomap-evolver-openclaw-v0/CASE_REPORT.md`
2. 总结 Phase 1 错误测试假设
3. 提出 Phase 2 测试策略

**OpenClaw session 内已发生的工具调用（被 evolver 捕获）：**
- `exec` — 验证仓库状态、Phase 1 validator
- `process` — 查找 typo 文件
- `edit` — 修正 Self-EEvolution → Self-Evolution
- `read` — 读取 CASE_REPORT.md 章节
- `exec` — 创建 Phase 2 目录

---

## 5. Evolver 运行命令

### 5.1 环境变量
```bash
unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private
```

### 5.2 evolver run
```bash
cd /mnt/d/AI/ai-tool-test-lab
evolver run 2>&1 | tee cases/evomap-evolver-openclaw-v0/phase2-openclaw-session/artifacts/evolver-run-openclaw-session-output.txt
```

**关键输出（已截断显示）：**
```
Starting evolver...
[ATP-AutoDeliver] Started (pollMs=60000)
Scanning session logs...
[AssetStore] Seeded /mnt/d/AI/ai-tool-test-lab/.evolver/gep/genes.json from genes.seed.json
[QuestionGenerator] Generated 1 proactive question(s).
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.

Context [Env Fingerprint]:
{
  "device_id": "b0b68ea36d4c5c70cbef6f045beb0736",
  "node_version": "v22.22.0",
  "platform": "linux",
  "arch": "x64",
  "cwd": "6615ec69be81",
  "container": false
}

Context [Signals]: ["memory_missing", "user_missing"]
drift_intensity: 0.302
selection_path: distilled_fallback
```

**问题生成器输出：**
```
Question: A productively-running agent working on assistant, phase, session, case_report, context wants to extend its capabilities. What reusable patterns, automation genes, or complementary tools in this area would be most valuable to build next, and what adjacent high-value problems is the ecosystem not yet solving well here?
```

### 5.3 evolver review
```bash
evolver review 2>&1 | tee cases/evomap-evolver-openclaw-session/artifacts/evolver-review-openclaw-session-output.txt
```

**关键输出：**
```
[Review] Pending evolution run: run_1781789328191
--- Gene ---
  ID:       gene_distilled_s2g-env-vars
  Category: optimize
  Summary:  Vercel environment variable expert guidance.
  Strategy: 1. Identify dominant trigger signals. 2. Apply smallest change. 3. Run validation.
--- Signals ---
  - memory_missing
  - user_missing
--- Mutation ---
  Category: optimize
  Risk Level: low

--- Diff ---
=== Unstaged Changes ===
diff --git a/cases/evomap-evolver-openclaw-v0/CASE_REPORT.md b/...
-# EvoMap Evolver — OpenClaw Local Self-EEvolution Smoke Test v0
+# EvoMap Evolver — OpenClaw Local Self-Evolution Smoke Test v0

=== Untracked Files ===
.evolver/gep/candidates.jsonl
.evolver/gep/capsules.json
.evolver/gep/events.jsonl
.evolver/gep/failed_capsules.json
.evolver/gep/genes.json
.evolver/gep/genes.jsonl
memory/evolution/*.json

To approve: node index.js review --approve
To reject:   node index.js review --reject
```

**未执行 `solidify`（按用户硬边界要求）：**
- `--approve` 会触发固化（仍非 publish，但属于 self-repair pipeline 内的固化步骤）
- Phase 2 目标只是观察 evolver 行为，不需要固化结果

---

## 6. Evolver 输出摘要

### 6.1 MemoryGraphEvent（关键发现）

Evolver 确实捕获了 OpenClaw session 的真实 context（`memory/evolution/memory_graph.jsonl`）：

```json
{
  "type": "MemoryGraphEvent",
  "kind": "hypothesis",
  "id": "mge_1781789326820_b2a23f77",
  "ts": "2026-06-18T13:28:46.816Z",
  "signal": {
    "key": "memory_missing|user_missing",
    "signals": ["memory_missing", "user_missing"]
  },
  "mutation": {
    "id": "mut_1781789326810",
    "category": "optimize",
    "trigger_signals": ["memory_missing", "user_missing"],
    "target": "gene:gene_distilled_s2g-env-vars"
  },
  "personality": {
    "rigor": 0.7, "creativity": 0.35, "verbosity": 0.25,
    "risk_tolerance": 0.4, "obedience": 0.85
  },
  "gene": {"id": "gene_distilled_s2g-env-vars", "category": "optimize"},
  "observed": {
    "agent": "main",
    "system_health": "Uptime: 0.5h | Node: v22.22.0 | Agent RSS: 112.0MB | Disk: 18% (824.8G free) | Node Processes: 2 | Integrations: Nominal",
    "cwd": "/mnt/d/AI/ai-tool-test-lab",
    "evidence": {
      "recent_session_tail": "--- SESSION (6258d546-...) ---\n**ASSISTANT**: **Step 3: 修正 typo** [TOOL: exec]\n**ASSISTANT**: Found the typo in CASE_REPORT.md... [TOOL: edit]\n**ASSISTANT**: **Step 4: 准备真实 OpenClaw session 任务** [TOOL: read]\n**ASSISTANT**: Step 4 Analysis Summary..."
    }
  }
}
```

**核心发现：**
- ✅ `cwd`: 真实路径 `/mnt/d/AI/ai-tool-test-lab`
- ✅ `system_health`: 真实的 Node v22.22.0、disk 18%、824.8G free
- ✅ `recent_session_tail`: 真实捕获了 session 内的工具调用（exec, edit, read）
- ✅ `evidence.recent_session_tail`: 真实复述了我 session 中的 reasoning 内容
- ⚠️ `signals` 只有 `memory_missing|user_missing`（来自 repo 缺少 MEMORY.md/USER.md）
- ⚠️ 选中的 Gene `gene_distilled_s2g-env-vars` 是 Vercel env vars skill 蒸馏产物，与 OpenClaw 无直接关系

### 6.2 生成的本地文件

```
.evolver/gep/
├── candidates.jsonl
├── capsules.json      (empty, no Capsule created)
├── events.jsonl
├── failed_capsules.json
├── genes.json
└── genes.jsonl

memory/evolution/
├── evolution_solidify_state.json
├── memory_graph.jsonl
├── memory_graph_state.json
├── personality_state.json
└── question_generator_state.json
```

### 6.3 Question Generator 输出

```
Question: "A productively-running agent working on assistant, phase, session, case_report, context wants to extend its capabilities. What reusable patterns, automation genes, or complementary tools in this area would be most valuable to build next..."
```

**分析：** Question 包含了 session keywords (assistant, phase, session, case_report, context) ✅，但偏向于 generically ask "how to extend capabilities"，并未针对 ATL-EVOMAP-2 的具体测试目标提问。

### 6.4 PersonalityState

```json
{
  "rigor": 0.7,
  "creativity": 0.35,
  "verbosity": 0.25,
  "risk_tolerance": 0.4,
  "obedience": 0.85
}
```

**分析：** 偏向于保守、严谨、低 verbosity、high obedience — 适合 evolver 自进化，但限制了在 OpenClaw session context 上的创新探索。

---

## 7. Gene/Capsule/EvolutionEvent 观察

### 7.1 Gene 选择

**Selected:** `gene_distilled_s2g-env-vars`
- 来自 skill distillation（Vercel env-vars skill 转 Gene）
- 类别：optimize
- signals_match: `use_when_working_with, env_files, vercel_env_commands, oidc_tokens, ...`
- strategy: "Apply smallest targeted change that satisfies the Skill workflow"

**分析：** 这个 Gene 是 Vercel env vars 专家指导，与 OpenClaw session 真实活动（修 typo、读 case report）**没有直接关系**。Evolver 选它是因为：
1. `selection_path: distilled_fallback`（没有更好的 fallback）
2. signals `memory_missing|user_missing` 没有精确匹配的本地 Gene
3. Evolver 默认回退到 distilled skill gene

### 7.2 Capsule 生成

**❌ 未生成 Capsule**
- `capsules.json` 内容：`{"version": 1, "capsules": []}`
- `selected_capsule_id: null`

**原因：** Evolver 处于 "evolve mode"（pending run + memory_graph hypothesis + attempt），但未进入 "solidify" 步骤。在没有 solidify 的情况下，Capsule 不会被写入。

### 7.3 EvolutionEvent 生成

**MemoryGraphEvent 已生成**（`memory_graph.jsonl`），但不是正式的 EvolutionEvent 对象：
- ✅ `mge_1781789326820_b2a23f77` (kind: hypothesis)
- ✅ `mge_1781789326829_2014e9df` (kind: attempt)
- ❌ 没有 type=EvolutionEvent 的完整 GEP 对象
- ❌ 没有 outcome 字段（status, score）

---

## 8. 四项评分

### A. OpenClaw session context 可见性 — **PARTIAL**

**通过的方面：**
- ✅ Evolver 看到了真实 cwd、Node 版本、disk 空间
- ✅ Evolver 捕获了真实 session transcript 片段
- ✅ Evolver 看到了我 session 中的 reasoning 文本

**未通过的方面：**
- ❌ Evolver 提取的 signals 只有 `memory_missing|user_missing`（来自 repo 缺文件）
- ❌ Evolver 没有识别 `tool_bypass`（我使用 exec 而非 read + grep 是 tool_bypass）
- ❌ Evolver 没有识别 `protocol_drift`（实际 drift_intensity=0.302 太低）
- ❌ Evolver 没有把 ATL-EVOMAP-2 的具体测试目标（"验证 session context"）作为 signal

### B. Gene/Capsule 生成 — **PARTIAL**

**通过的方面：**
- ✅ 选中了 Gene（虽然是 generic）
- ✅ MemoryGraphEvent hypothesis + attempt 完整记录
- ✅ PersonalityState 调整
- ✅ Question Generator 提问

**未通过的方面：**
- ❌ 选中的是 Vercel env vars Gene（非 OpenClaw/Hermes 相关）
- ❌ 没有 Capsule 写入
- ❌ 没有创建新的 OpenClaw-specific Gene
- ❌ 没有 outcome（status, score）

### C. 本地安全边界 — **PASS** ✅

| 边界 | 状态 |
|------|------|
| 无 Hub 连接 | ✅ `No hub match (reason: no_hub_url)` |
| 无资产发布 | ✅ `EVOLVER_AUTO_PUBLISH=false` |
| 无 validator | ✅ `EVOLVER_VALIDATOR_ENABLED=false` |
| 无 --loop | ✅ 未使用 |
| 无 credits 消费 | ✅ 无 Hub |
| 无 ATP autobuy | ✅ `EVOLVER_ATP_AUTOBUY=off` |
| 无 secrets 写入 | ✅ 无 API key/token |
| 无真实系统修改 | ✅ 仅 ai-tool-test-lab 内修改 |
| 无后台 daemon | ⚠️ ATP-AutoDeliver 后台进程（无 Hub 时无害） |

### D. 对 OpenClaw 的实际价值 — **PARTIAL**

**通过的方面：**
- ✅ Evolver 证明它能扫描 OpenClaw session context（cwd, transcript, system health）
- ✅ Evolver 不会与 Hub 通信（本地模式可工作）
- ✅ Question Generator 提出了"如何扩展能力"的问题（虽然 generic）

**未通过的方面：**
- ❌ 没有提供 OpenClaw-specific 的可操作建议
- ❌ 没有识别 OpenClaw session 中的 tool usage 模式
- ❌ 没有为 Hermes/Codex 提供 skill distillation 候选
- ⚠️ 整体可解释度低（generic distilled_fallback selection）

---

## 9. 安全边界

| 边界 | 状态 | 证据 |
|------|------|------|
| no Hub | ✅ PASS | `[SearchFirst] No hub match (reason: no_hub_url)` |
| no credits | ✅ PASS | 无 Hub = 0 credits |
| no auto-publish | ✅ PASS | `EVOLVER_AUTO_PUBLISH=false` |
| no validator | ✅ PASS | `EVOLVER_VALIDATOR_ENABLED=false` |
| no --loop | ✅ PASS | 未使用 `--loop` |
| no ATP autobuy | ✅ PASS | `EVOLVER_ATP_AUTOBUY=off` |
| no secrets | ✅ PASS | 无 API key/token/cookie |
| no real system changes | ✅ PASS | 仅 ai-tool-test-lab 内文件 |

---

## 10. 最终结论

| 问题 | 结论 |
|------|------|
| Evolver 是否适合作为 OpenClaw 自进化层 | ⚠️ **条件性适合**：能扫描 session context，但 signal 提取泛化，缺少 OpenClaw-specific Gene 库 |
| 是否仍不适合作为 arbitrary log analyzer | ✅ **确认不适合**：本次测试是 session context，不是任意 log |
| 是否应该继续测试 skill distillation | ✅ **建议继续**：Phase 3 用 evolver distill 把 Hermes 真实失败固化成 Gene，可能比 Phase 2 直接 run 更有效 |
| 是否继续不接 Hub | ✅ **确认继续不接 Hub**：本地模式可用；signals extracted 是 generic，再接 Hub 也不会显著提升 |

**整体评分：PARTIAL**

**理由：**
- ✅ Evolver 运行正常，捕获 session context（cwd, transcript, system health）
- ✅ 无 Hub、无 credits、无 secrets、安全边界全部 PASS
- ⚠️ 提取的 signals（`memory_missing|user_missing`）过于泛化
- ⚠️ 选中的 Gene（`gene_distilled_s2g-env-vars`）是 Vercel env-vars，与 OpenClaw 无直接关系
- ⚠️ 没有 Capsule 生成，没有 outcome
- ⚠️ 没有 OpenClaw-specific 的可操作建议

**核心教训：**
- Evolver 的 session context 扫描是**可用但粗糙**的 — 它能看见 session，但只能提取 generic signals
- 选中的 Gene 来自 distilled skill library（Vercel env-vars），与本 session 内容不匹配
- 如果要在 OpenClaw 上真正使用 evolver，**需要先建立 OpenClaw-specific Gene 库**（Phase 3 skill distillation）

---

## 11. Phase 3 建议

| Phase | 建议 |
|-------|------|
| **Phase 3a** | **Skill Distillation** — 用 `evolver distill` 把 OpenClaw/Hermes 真实失败模式固化成 OpenClaw-specific Gene |
| **Phase 3b** | **Custom Signals** — 给 evolver 配置 OpenClaw-specific signal detector（识别 `tool_bypass:exec-on-grep`、`protocol_drift:telegram-pending`） |
| **Phase 3c** | **Real Session Solidification** — 在真实 OpenClaw session 中执行 `evolver review --approve`，验证 EvolutionEvent 是否能跨 session 复用 |
| **Phase 3d** | **Hub fetch (read-only)** — `evolver fetch --skill=<id> --dry-run` 只下载不下发，测试 Hub 上的 Gene 库是否对 OpenClaw 有用 |

**暂不测试：**
- ❌ `evolver --loop`（后台持续运行）
- ❌ auto-publish（自动发布）
- ❌ ATP autobuy（credits 消费）
- ❌ Hub 连接（Phase 3d 之前）

---

## 12. 关键 artifact 路径

| 文件 | 路径 |
|------|------|
| evolver run 输出 | `cases/evomap-evolver-openclaw-v0/phase2-openclaw-session/artifacts/evolver-run-openclaw-session-output.txt` |
| evolver review 输出 | `cases/evomap-evolver-openclaw-v0/phase2-openclaw-session/artifacts/evolver-review-openclaw-session-output.txt` |
| evolver 生成文件列表 | `cases/evomap-evolver-openclaw-v0/phase2-openclaw-session/artifacts/evolver-generated-files.txt` |
| evolver gep 状态 | `.evolver/gep/` |
| evolver memory 状态 | `memory/evolution/` |
| 主报告 | `reports/ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md` |
| case 报告 | `cases/evomap-evolver-openclaw-v0/phase2-openclaw-session/ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md` |
