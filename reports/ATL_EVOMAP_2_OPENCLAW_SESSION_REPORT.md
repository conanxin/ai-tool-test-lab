# ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md
# ATL-EVOMAP-2 · OpenClaw Session-Context Test · Final Report

**Task:** ATL-EVOMAP-2
**Case:** evomap-evolver-openclaw-v0
**Date:** 2026-06-18 (Asia/Shanghai)
**Agent:** OpenClaw minimax/MiniMax-M2.7
**Repo:** https://github.com/conanxin/ai-tool-test-lab
**Parent:** ATL-EVOMAP-1 (commit d8fc23d, PARTIAL)
**Status:** openclaw session-context test partial

---

## 执行摘要

ATL-EVOMAP-2 在真实 OpenClaw session 内运行 `evolver run` + `evolver review`，验证 Evolver 能否从 session 自身提取 signals 并生成 Gene/Capsule。

**关键发现：**
- Evolver 成功扫描了 OpenClaw 真实 session context（cwd, transcript, system_health）
- `evolver review` 显示 pending run `run_1781789328191`（未执行 solidify）
- 无 Hub、无 credits、无 secrets — 安全边界全部 PASS
- 提取的 signals (`memory_missing|user_missing`) 过于泛化，选中的 Gene (Vercel env-vars) 与 OpenClaw session 真实活动不匹配
- MemoryGraphEvent (hypothesis + attempt) 已记录，但无正式 EvolutionEvent/Capsule
- Evolver 可见但解释度低 — 需要先建立 OpenClaw-specific Gene 库（Phase 3）

**Phase 3 建议：** Skill Distillation（用 `evolver distill` 把 Hermes 失败固化成 OpenClaw-specific Gene） + Custom Signals（配置 OpenClaw-specific signal detector）。

---

## 1. Phase 2 vs Phase 1 关键区别

| 维度 | Phase 1 | Phase 2 |
|------|---------|---------|
| 测试数据 | 4 个 arbitrary .log | 真实 OpenClaw session |
| evolver 输入 | 失败日志内容 | session transcript + cwd + system |
| 评估标准 | "能否修复业务问题" | "能否提取 session signals" |
| 结果 | PARTIAL — 4 场景 FAIL | PARTIAL — signals 泛化 |

**核心转变：** 不再问 evolver "诊断任意 log"，而是问 "从 session 自身学习"。

---

## 2. OpenClaw session 任务

**任务内容（在 evolver 扫描前完成）：**
1. 读取 Phase 1 CASE_REPORT.md
2. 总结错误测试假设
3. 提出 Phase 2 测试策略

**Session 内真实工具调用（被 evolver 捕获）：**
- `exec` × 多次（git status, validator, 目录创建）
- `process` × 1（typo 查找）
- `edit` × 1（typo 修正）
- `read` × 多次（CASE_REPORT.md）

---

## 3. evolver run 关键输出

```
Starting evolver...
[ATP-AutoDeliver] Started (pollMs=60000)
Scanning session logs...
[AssetStore] Seeded /mnt/d/AI/ai-tool-test-lab/.evolver/gep/genes.json
[QuestionGenerator] Generated 1 proactive question(s).
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.

Context [Signals]: ["memory_missing", "user_missing"]
drift_intensity: 0.302
selection_path: distilled_fallback
selected: gene_distilled_s2g-env-vars
```

**evolver review 关键输出：**
```
[Review] Pending evolution run: run_1781789328191
--- Gene ---
  ID:       gene_distilled_s2g-env-vars
  Category: optimize
  Summary:  Vercel environment variable expert guidance
--- Signals ---
  - memory_missing
  - user_missing

--- Diff ---
=== Unstaged Changes ===
diff CASE_REPORT.md
-# Self-EEvolution
+# Self-Evolution

=== Untracked Files ===
.evolver/gep/*
memory/evolution/*.json
```

**重大发现：** `evolver review` **看到了**我刚在 session 中做的 typo 修正（Self-EEvolution → Self-Evolution）！这证明 evolver 真的在扫描 session context。

---

## 4. evolver session context 捕获

`memory/evolution/memory_graph.jsonl` 包含 MemoryGraphEvent：

```json
{
  "type": "MemoryGraphEvent",
  "kind": "hypothesis",
  "signal": {"key": "memory_missing|user_missing", "signals": ["memory_missing", "user_missing"]},
  "observed": {
    "agent": "main",
    "system_health": "Uptime: 0.5h | Node: v22.22.0 | Disk: 18% (824.8G free)",
    "cwd": "/mnt/d/AI/ai-tool-test-lab",
    "evidence": {
      "recent_session_tail": "--- SESSION (6258d546-...) ---\n**ASSISTANT**: **Step 3: 修正 typo** [TOOL: exec]\n**ASSISTANT**: Found the typo in CASE_REPORT.md... [TOOL: edit]\n**ASSISTANT**: **Step 4: 准备真实 OpenClaw session 任务** [TOOL: read]"
    }
  }
}
```

**捕获到的真实 OpenClaw session 内容：**
- ✅ `cwd`: `/mnt/d/AI/ai-tool-test-lab`
- ✅ `system_health`: Node v22.22.0, 18% disk
- ✅ `recent_session_tail`: 真实的 assistant 消息 + tool calls (exec, edit, read)
- ✅ Evidence 包含我 session 中的 reasoning 文本

---

## 5. 四项评分

| 维度 | 评分 | 关键发现 |
|------|------|----------|
| A. Session context 可见性 | **PARTIAL** | 捕获 cwd/transcript/system，但 signals 只有 `memory_missing\|user_missing`（泛化） |
| B. Gene/Capsule 生成 | **PARTIAL** | MemoryGraphEvent hypothesis+attempt 已生成；Gene 选中但 generic (Vercel env-vars)；无 Capsule |
| C. 本地安全边界 | **PASS** ✅ | 无 Hub、无 publish、无 validator、无 --loop、无 credits、无 secrets |
| D. 对 OpenClaw 实际价值 | **PARTIAL** | 能扫描 session，但 signal 提取泛化、Gene 非 OpenClaw-specific |

---

## 6. 关键限制

### 6.0 硬边界安全表

| 边界 | 状态 | 证据 |
|------|------|------|
| no hub | ✅ PASS | `[SearchFirst] No hub match (reason: no_hub_url)` |
| no credits | ✅ PASS | 无 Hub 连接，零 credits 消费 |
| no auto-publish | ✅ PASS | `EVOLVER_AUTO_PUBLISH=false` |
| no validator | ✅ PASS | `EVOLVER_VALIDATOR_ENABLED=false` |
| no --loop | ✅ PASS | 未使用 --loop flag |

### 6.1 Signals 泛化
`memory_missing|user_missing` 来自 repo 缺少 MEMORY.md/USER.md 文件 — **与 ATL-EVOMAP-2 测试目标完全无关**。Evolver 没有把"测试 evolver 在 OpenClaw session"这个核心目标作为 signal。

### 6.2 Gene 不匹配
选中的 `gene_distilled_s2g-env-vars` 是 Vercel env-vars skill 蒸馏产物 — 与 OpenClaw session 真实活动（修 typo、读 case report、运行 evolver）**零关系**。`selection_path: distilled_fallback` 表明 Evolver 没有找到更好的本地 Gene。

### 6.3 无 Capsule / 无 EvolutionEvent
- `capsules.json` 仍是 `{"version":1, "capsules":[]}`
- 没有正式 `type=EvolutionEvent` 对象
- 没有 outcome (status, score)
- Phase 2 故意不执行 `--approve`（避免固化）

### 6.4 PersonalityState 保守
```json
{"rigor": 0.7, "creativity": 0.35, "verbosity": 0.25, "risk_tolerance": 0.4, "obedience": 0.85}
```
适合 evolver 自身保守进化，但限制了在 OpenClaw 上的创新探索。

---

## 7. 最终结论

| 问题 | 结论 |
|------|------|
| Evolver 是否适合作为 OpenClaw 自进化层 | ⚠️ 条件性适合：能扫描 session context，但 signal 提取泛化、缺少 OpenClaw-specific Gene |
| 是否仍不适合作为 arbitrary log analyzer | ✅ 确认不适合 |
| 是否应该继续测试 skill distillation | ✅ 建议继续（Phase 3） |
| 是否继续不接 Hub | ✅ 继续不接 Hub |

**整体：** PARTIAL — Evolver 真的扫描了 OpenClaw session，但提取的 signal 泛化，Gene 来自 Vercel env-vars 不相关。要在 OpenClaw 上使用 evolver，需要先建立 OpenClaw-specific Gene 库。

---

## 8. Phase 3 建议

| Phase | 任务 | 理由 |
|-------|------|------|
| **3a** | `evolver distill` 把 Hermes 真实失败固化成 Gene | 直接绕过 generic signal 提取 |
| **3b** | 配置 OpenClaw-specific signal detector | 识别 `tool_bypass:exec-on-grep`、`protocol_drift:telegram-pending` |
| **3c** | `evolver review --approve` 真实固化 | 验证 EvolutionEvent 跨 session 复用 |
| **3d** | `evolver fetch --dry-run` 只读 Hub | 测试 Hub Gene 库对 OpenClaw 价值 |

**暂不测：** --loop / validator / auto-publish / ATP autobuy / Hub 连接

---

## 9. 执行记录

```
ATL-EVOMAP-2 timeline:
- 21:24 Phase 1 report received
- 21:25 Phase 1 validator: PASS (state reproducible)
- 21:26 typo fix: Self-EEvolution → Self-Evolution
- 21:27 Phase 2 dir created
- 21:28 evolver run: SUCCESS (MemoryGraphEvent captured)
- 21:28 evolver review: pending run_1781789328191 (no solidify)
- 21:30 4-dimension scoring: A=PARTIAL, B=PARTIAL, C=PASS, D=PARTIAL
- 21:32 Phase 2 reports written
```

---

## 10. 新增/修改文件

**修改 (1)：**
- `cases/evomap-evolver-openclaw-v0/CASE_REPORT.md` — typo fix

**新建 (Phase 2 + report)：**
```
cases/evomap-evolver-openclaw-v0/phase2-openclaw-session/
├── ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md
└── artifacts/
    ├── evolver-run-openclaw-session-output.txt
    ├── evolver-review-openclaw-session-output.txt
    └── evolver-generated-files.txt

reports/ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md  (本报告)
```

**将新建（commit 前）：**
- `scripts/validate_evomap_phase2_openclaw_session.py`
- 更新 `cases/evomap-evolver-openclaw-v0/README.md`（追加 Phase 2）
- 更新 `data/cases.json`（phase → ATL-EVOMAP-2）

---

## 11. Phase 1 vs Phase 2 总结

| Phase | 目标 | 结果 | 主要教训 |
|-------|------|------|----------|
| **ATL-EVOMAP-1** | 测试 evolver 能否诊断 arbitrary 失败日志 | PARTIAL — 4 场景 FAIL | Evolver 不是通用 log analyzer |
| **ATL-EVOMAP-2** | 测试 evolver 能否从 OpenClaw session 学习 | PARTIAL — signals 泛化、Gene 不匹配 | Evolver 真的能看 session，但 signal 提取需要 OpenClaw-specific Gene 库 |

**整体趋势：** Evolver 的"看见"能力 ✅，"理解"能力 ⚠️。下一步是 build OpenClaw-specific Gene 库（Phase 3）让 Evolver 的理解力匹配其看见力。
