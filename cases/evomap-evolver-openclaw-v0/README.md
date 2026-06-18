# EvoMap Evolver — OpenClaw Local Self-Evolution Smoke Test v0

**Case slug:** `evomap-evolver-openclaw-v0`
**Phase:** ATL-EVOMAP-1 local offline smoke test
**Status:** local offline smoke completed
**Date:** 2026-06-18 (Asia/Shanghai)
**Repo:** https://github.com/conanxin/ai-tool-test-lab

---

## 1. 测试对象是什么

### EvoMap
EvoMap 是一个 AI agent 自进化/经验复用基础设施，通过 Gene（可复用策略单元）和 Capsule（执行结果）实现 agent 从失败中学习。

### @evomap/evolver
EvoMap 的本地 CLI 工具（npm 包），需要在 git repo 中运行。
- 核心命令：`evolver run`（执行 GEP self-improvement cycle）、`evolver review`（审查 pending changes）、`evolver solidify`（固化结果）
- 不需要 Hub 连接即可运行本地 evolution
- 关键文件：`.evolver/gep/`（Gene/Capsule/EvolutionEvent 存储）

### 本地 OpenClaw 工作流中的使用方式
理论上：让 OpenClaw agent 从失败日志中学习，生成可复用的修复 prompt。但 smoke test 发现 **Evolver 是自进化引擎，不是通用失败日志分析器**。

---

## 2. 为什么测试

- 验证 EvoMap Evolver 能否做"Agent 错题本 / 维修手册"
- 验证它能否从失败日志（npm test、systemd、proxy、cron）生成下一步修复策略
- 验证是否适合接入 OpenClaw / Hermes / Codex 的自动验证循环

**关键发现：** EvoMap Evolver 是 **自进化引擎**（分析自身协议状态，生成 Gene/Capsule），不是通用失败日志分析器。

---

## 3. 本地电脑负责什么

- ✅ 安装 Evolver（`npm install -g @evomap/evolver`）
- ✅ 构造本地失败日志 fixture
- ✅ 运行 `evolver run` + `evolver review`
- ✅ 保存输出到 artifacts/
- ✅ 运行 Python stdlib 验证脚本

---

## 4. 云端平台负责什么

- ❌ 本次不使用 EvoMap Hub
- ❌ 不连接、不发布、不消费 credits
- 未来可选：只读 `evolver fetch` / `evolver sync --dry-run` 测试

**Hub 状态：** `[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.`

---

## 5. 测试场景

| 场景 | 描述 | 评分 |
|------|------|------|
| A. npm test 失败 | add(1,2) 返回 "12" 而非 3（字符串拼接 bug） | **FAIL** |
| B. proxy failure | Telegram bot 代理环境变量缺失，ETIMEDOUT | **FAIL** |
| C. systemd failure | hermes-gateway.service 缺 MODEL_PROVIDER | **FAIL** |
| D. cron failure | cron 环境 PATH 缺失 uv/node 路径 | **FAIL** |

**说明：** Evolver 是自进化引擎，不直接读取 arbitrary 失败日志。这些 FAIL 不是 bug，而是测试设计与工具设计的不匹配。

### 工具行为验证

| 检查项 | 结果 |
|--------|------|
| 未连接 Hub | ✅ `[SearchFirst] No hub match (reason: no_hub_url)` |
| 未发布资产 | ✅ EVOLVER_AUTO_PUBLISH=false |
| 未开启 loop | ✅ 未使用 --loop flag |
| 未消耗 credits | ✅ 无 Hub 连接，零消费 |
| no hub connection | ✅ 确认 local-only mode，no_hub_url |
| no credits consumed | ✅ 无 Hub 连接，零 credits 消费 |
| 未写入 secrets | ✅ 无 API key/token/cookie 写入 |
| ATP 后台进程 | ⚠️ ATP-AutoDeliver 在 run 期间启动（无 Hub 时无害） |

---

## 6. 实际执行记录

### 版本信息
- Node.js: v22.22.0
- npm: 10.9.4
- Git: 2.43.0
- evolver: 1.89.14 (@evomap/evolver)

### 命令摘要
```bash
# 安装
npm install -g @evomap/evolver  # ✅ 成功

# Fixture 构建
cd fixtures/local-evolver-smoke
git init && npm init -y
npm pkg set scripts.test="node test.js"
npm test  # FAIL: add(1, 2) should be 3, got: 12  ✅ 符合预期

# evolver review（无 pending）
evolver --review  # → "No pending evolution run to review. Run 'evolver run' first."

# evolver run（主测试）
unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private
evolver run  # ✅ 成功，产生 GEP Cycle #0001
```

### Artifact 路径
- `artifacts/evolver-review-output.txt` — `evolver --review` 输出
- `artifacts/evolver-run-output.txt` — `evolver run` 完整输出（51KB）

---

## 7. 问题与解决

| 问题 | 说明 |
|------|------|
| `evolver run --help` 执行了 evolution | evolver 把参数当作任务，正确用法是直接 `evolver run` |
| evolver 未读取 failure logs | evolver 扫描自身 session，不直接读 arbitrary 文件 |
| evolver 不是通用 log 分析器 | 设计如此 — evolver 是自进化工具，不是失败分析工具 |
| ATP-AutoDeliver 后台进程 | evolver 内置行为，无 Hub 时无害且不消耗资源 |
| evolution_state.json 不存在 | evolver 自动创建 memory/evolution/ 目录 |

---

## 8. 最终结论

| 问题 | 结论 |
|------|------|
| 是否适合继续测试 | ⚠️ 适合，但需要重新定义测试目标 |
| 是否适合接入 OpenClaw | ⚠️ 条件性：仅适合 evolver 自进化，不适合通用失败日志分析 |
| 是否适合接入 Hermes/Codex | ❌ 不适合作为直接修复建议生成器 |
| 是否暂时不建议接 Hub | ✅ 确认：本地模式可用，继续不接 Hub |
| evolver 真正适合做什么 | OpenClaw/Codex 的 **自进化**：从自身协议失败中学习，生成 Gene/Capsule |

**核心发现：** EvoMap Evolver 更像是"AI Agent 的 Wikipedia repair pattern library"，而非"Universal log analyzer"。

---

## 9. 后续建议

### Phase 2：在真实 OpenClaw session 内调用 evolver
让 evolver 分析 OpenClaw 的真实 session 上下文（而非 memory/*.log），验证能否从 protocol_drift 中生成 Gene。

### Phase 3：Skill Distillation 测试
使用 `evolver distill` 把 OpenClaw/Hermes 的真实失败模式固化成 Gene，验证 distill 质量。

### Phase 4：Hub fetch/directory 只读测试
```bash
evolver fetch --skill=<id> --out=./skills/  # 只下载不下发
evolver sync --scope=purchased --dry-run      # 预览不下发
```

### 暂不测试
- ❌ `evolver --loop`（后台持续运行）
- ❌ `evolver validator`（分布式验证者）
- ❌ `evolver auto-publish`（自动发布）
- ❌ ATP autobuy（credits 消费）
- ❌ EvoMap Hub 连接（Phase 4 前）

---

## 10. 文件结构

```
cases/evomap-evolver-openclaw-v0/
├── README.md              ← 本文件
├── CASE_REPORT.md         ← 完整技术报告
├── artifacts/
│   ├── evolver-review-output.txt   (127 bytes)
│   └── evolver-run-output.txt      (51KB)
└── fixtures/local-evolver-smoke/
    ├── .evolver/gep/       (evolver GEP 状态)
    ├── .git/
    ├── MEMORY.md
    ├── calc.js
    ├── package.json
    ├── test.js
    └── memory/
        ├── npm-test-failure.log
        ├── proxy-failure.log
        ├── systemd-failure.log
        ├── cron-failure.log
        ├── evolution/               (evolver 生成)
        └── evolver_update_check.json  (仅时间戳)
```

---

## Phase 2: OpenClaw Session-Context Test (ATL-EVOMAP-2)

**Status:** openclaw session-context test partial
**报告:** [phase2-openclaw-session/ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md](phase2-openclaw-session/ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md)

### Phase 2 目标

不在“构造任意失败日志”期望 evolver 分析，而是让 evolver 扫描真实 OpenClaw session context（cwd、system_health、session_transcript、recent tool calls）。

### Phase 2 关键发现

- ✅ evolver run 成功 — 扫描了 OpenClaw 真实 session context
- ✅ evolver review 出现 pending run（`run_1781789328191`）
- ✅ MemoryGraphEvent 记录了我的 session transcript：my tool calls (exec/edit/read) + reasoning 文本
- ✅ evolver review 看到了我的 typo 修正（Self-EEvolution → Self-Evolution）
- ✅ 安全边界全部 PASS：no Hub / no publish / no auto-publish / no validator / no --loop / no credits / no secrets

### Phase 2 关键限制

- ⚠️ Signals 过于泛化：`memory_missing|user_missing`（来自 repo 缺 MEMORY.md/USER.md），与 ATL-EVOMAP-2 测试目标完全无关
- ⚠️ 选中的 Gene 是 `gene_distilled_s2g-env-vars`（Vercel env-vars skill 蒸馏产物），与 OpenClaw session 零关系
- ⚠️ 没有正式 Capsule / EvolutionEvent 生成
- ⚠️ 未执行 `solidify`（遵循 hard boundary）

### Phase 2 评分

| 维度 | 评分 |
|------|------|
| A. Session context 可见性 | PARTIAL — 看见 session，但 signal 泛化 |
| B. Gene/Capsule 生成 | PARTIAL — MemoryGraphEvent 有，Gene/Capsule 无 |
| C. 本地安全边界 | PASS — 全部 hard boundary 遵守 |
| D. 对 OpenClaw 实际价值 | PARTIAL — 可扫描但需 OpenClaw-specific Gene 库 |

### Phase 2 结论

> Evolver 能看 OpenClaw session（capture cwd, transcript, system_health, recent tool calls），
> 但 signal 提取泛化，Gene 来自 Vercel env-vars 不相关。
> 要在 OpenClaw 真正使用 evolver，需先建立 OpenClaw-specific Gene 库（Phase 3: skill distillation）。

### Phase 2 Artifact 路径

```
phase2-openclaw-session/
├── ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md
└── artifacts/
    ├── evolver-run-openclaw-session-output.txt
    ├── evolver-review-openclaw-session-output.txt
    └── evolver-generated-files.txt
```

### Phase 2 下一步

- **Phase 3a:** `evolver distill` 把 Hermes 真实失败固化成 OpenClaw-specific Gene
- **Phase 3b:** 配置 OpenClaw-specific signal detector（识别 tool_bypass:exec-on-grep、protocol_drift:telegram-pending）
- **Phase 3c:** `evolver review --approve` 真实固化（验证跨 session 复用）
- **Phase 3d:** `evolver fetch --dry-run` 只读 Hub 测试

**暂不测：** --loop / validator / auto-publish / ATP autobuy / Hub 连接

---

## 阶段总览

| 阶段 | 状态 | 结论 |
|------|------|------|
| **ATL-EVOMAP-1** | local offline smoke completed | PARTIAL — evolver 成功运行，4 个 arbitrary log 场景全部 FAIL（evolver 不是通用 log analyzer） |
| **ATL-EVOMAP-2** | openclaw session-context test partial | PARTIAL — evolver 能扫描 session context，但 signal 提取泛化，需 Phase 3 建立 OpenClaw-specific Gene 库 |
