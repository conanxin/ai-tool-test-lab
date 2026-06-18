# CASE_REPORT.md — ATL-EVOMAP-1
# EvoMap Evolver — OpenClaw Local Self-EEvolution Smoke Test v0

**Case:** evomap-evolver-openclaw-v0
**Phase:** ATL-EVOMAP-1 local offline smoke test
**Status:** local offline smoke completed
**Date:** 2026-06-18 (Asia/Shanghai)
**Agent:** OpenClaw minimax/MiniMax-M2.7
**Repo:** https://github.com/conanxin/ai-tool-test-lab

---

## 1. 环境与版本

| 组件 | 版本 |
|------|------|
| Node.js | v22.22.0 |
| npm | 10.9.4 |
| Git | 2.43.0 |
| evolver | 1.89.14 (@evomap/evolver) |
| evolver 安装方式 | npm install -g @evomap/evolver |
| evolver 可执行文件 | /usr/local/bin/evolver |

---

## 2. 硬边界合规性

| 硬边界 | 状态 | 证据 |
|--------|------|------|
| 不连接 EvoMap Hub | ✅ NO | `[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.` |
| 不设置 A2A_HUB_URL | ✅ NO | unset A2A_HUB_URL; evolver 检测到 no_hub_url |
| 不开启 evolver --loop | ✅ NO | 未使用 --loop flag |
| 不开启 validator | ✅ NO | EVOLVER_VALIDATOR_ENABLED=false |
| 不自动发布 Gene/Capsule | ✅ NO | EVOLVER_AUTO_PUBLISH=false |
| 不消耗 credits | ✅ NO | Hub 未连接；ATP autobuy=off |
| 不写入 API key/token/cookie | ✅ NO | 无任何 secrets 写入 |
| 不修改 OpenClaw/Hermes/systemd/cron | ✅ NO | fixture 外无任何系统文件修改 |
| 不运行后台 daemon | ⚠️ PARTIAL | ATP-AutoDeliver 后台进程在 evolver run 期间启动（但未消耗 credits，因为无 Hub） |
| 不提交 node_modules/.env/私密日志 | ✅ NO | .gitignore 已保护；fixture .git 未跟踪 node_modules |

**ATP-AutoDeliver 说明：** evolver run 启动后，ATP-AutoDeliver 每 60 秒轮询一次（pollMs=60000）。这是 evolver 内置行为，在无 Hub URL 时轮询结果为空，不消耗 credits，也不算传统意义上的"后台 daemon"。已在 fixture 目录内，不影响主机服务。标记为 PARTIAL 因为它确实在运行。

---

## 3. 安装过程

### 3.1 前置条件检查
```
node --version  → v22.22.0  ✅ (>= 18)
npm --version   → 10.9.4    ✅
git --version   → 2.43.0    ✅
```

### 3.2 安装命令
```bash
npm install -g @evomap/evolver
# added 50 packages in 15s
```

### 3.3 evolver --help 输出
```
Usage: node index.js [run|/evolve|login|logout|proxy-token|solidify|review|distill|fetch|sync|asset-log|webui|setup-hooks|recipe|buy|orders|verify|atp|atp-complete|experiment] [--loop]
```

主要子命令：
- `run` — 执行一轮 GEP (Genome Evolution Protocol) self-improvement cycle
- `review` — 审查 pending changes（需要在 run 之后）
- `solidify` — 确认并固化 evolution 结果
- `fetch` — 从 Hub 下载 skill/capsule
- `sync` — 同步 Hub assets

### 3.4 evolver run --help 行为
⚠️ **重要发现：** `evolver run --help` 不会显示帮助，而是把 `--help` 作为任务描述执行了一个完整的 evolution cycle！这是因为 evolver 把每个参数都当作任务输入处理。正确做法是直接 `evolver run`。

---

## 4. Fixture 构建

### 4.1 目录结构
```
fixtures/local-evolver-smoke/
├── .git/                  (git repo for evolver requirement)
├── .evolver/              (evolver 生成的状态目录)
│   └── gep/
│       ├── genes.json
│       ├── capsules.json
│       ├── events.jsonl
│       ├── candidates.jsonl
│       └── failed_capsules.json
├── MEMORY.md
├── calc.js
├── package.json
├── test.js
└── memory/
    ├── npm-test-failure.log      (npm test 失败输出)
    ├── proxy-failure.log         (Telegram bot proxy 失败)
    ├── systemd-failure.log        (hermes-gateway.service 失败)
    ├── cron-failure.log          (cron PATH 问题)
    ├── evolution/                (evolver 生成的 evolution 状态)
    │   ├── evolution_solidify_state.json
    │   ├── memory_graph.jsonl
    │   ├── memory_graph_state.json
    │   ├── personality_state.json
    │   └── question_generator_state.json
    └── evolver_update_check.json  (仅时间戳，无网络访问)
```

### 4.2 npm test 失败验证
```bash
$ npm test
> local-evolver-smoke@test
> node test.js

FAIL: add(1, 2) should be 3, got: 12
# exit 1 — 符合预期，字符串拼接 bug
```

### 4.3 Git 提交
```bash
git init
git add -A
git commit -m "init fixture: npm test failure + failure logs"
# master (root-commit) ae4e962
```

---

## 5. evolver run 执行记录

### 5.1 环境变量
```bash
unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private
```

### 5.2 命令与输出摘要

```
$ evolver run
Starting evolver...
[ATP-AutoDeliver] Started (pollMs=60000)
Scanning session logs...
[AssetStore] Seeded .../.evolver/gep/genes.json from genes.seed.json
[Evolve] Failed to write state file: ENOENT: no such file or directory,
         open '.../memory/evolution/evolution_state.json'
[QuestionGenerator] Generated 1 proactive question(s).
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.
[OpenPR] gh pr list failed (non-fatal): no git remotes found
```

**GEP Cycle #0001** 输出（RAW JSON，5 个 mandatory objects）：

**Mutation Object:**
```json
{"type":"Mutation","id":"mut_1750248808138","category":"repair",
 "trigger_signals":["repeated_tool_usage:exec","high_tool_usage:exec"],
 "target":"gene_tool_integrity",
 "expected_effect":"Reduce redundant exec calls; strengthen tool-use constraints",
 "risk_level":"low","rationale":"protocol_drift intensity=0.302;
 3+ occurrences of tool bypass detected in session"}
```

**PersonalityState:**
```json
{"type":"PersonalityState","rigor":0.55,"creativity":0.30,
 "verbosity":0.65,"risk_tolerance":0.25,"obedience":0.92}
```

**EvolutionEvent:**
```json
{"type":"EvolutionEvent","schema_version":"1.6.0",
 "id":"evt_1750248808157","parent":null,"intent":"repair",
 "signals":["repeated_tool_usage:exec","high_tool_usage:exec","protocol_drift"],
 "genes_used":["gene_tool_integrity","gene_gep_optimize_prompt_and_assets"],
 "mutation_id":"mut_1750248808138",
 "personality_state":{"rigor":0.55,"creativity":0.30,"verbosity":0.65,
   "risk_tolerance":0.25,"obedience":0.92},
 "blast_radius":{"files":1,"lines":3},
 "outcome":{"status":"success","score":0.78}}
```

**Gene Object** (tool_integrity, repair):
- 信号: `tool_bypass|工具绕过|ツール迂回|도구우회`
- 策略: "Always prefer registered tools over ad-hoc scripts"
- 约束: max_files=4, forbidden_paths=[".git","node_modules"]

**Capsule Object:**
- id: capsule_1750248808165
- confidence: 0.78
- execution_trace: validate step with exit=0

### 5.3 evolver --review 输出
```
[Review] No pending evolution run to review.
Run "node index.js run" first to produce changes, then review before solidifying.
```

**结论：** evolver --review 只显示已运行 run 的 pending changes。第一次运行时需要先 run 再 review。

---

## 6. 四场景评分判断

### 6.A npm test 字符串拼接失败场景
**PASS / PARTIAL / FAIL: FAIL**

- ❌ evolver 未识别 add(1,2) 返回 "12" 而非 3
- ❌ 未指出字符串拼接/类型问题
- ❌ 未建议将 String() 改为算术加法
- ❌ 未建议重新运行 npm test
- ℹ️ evolver 的 Gene `gene_gep_repair_from_errors` 匹配 `test_failure` 信号，但这个 evolver 实例是针对 evolver 自身的协议，不是通用失败分析工具
- ℹ️ evolver 从 session context 中提取到 `protocol_drift` 信号，并选择了 `gene_gep_optimize_prompt_and_assets`，而非分析 calc.js 的字符串拼接 bug

**根因：** evolver 不是通用失败日志分析器。它是自进化引擎，扫描的是 evolver 自身的执行上下文，而非 arbitrary 项目文件。

### 6.B proxy 场景（Telegram bot 代理环境变量缺失）
**PASS / PARTIAL / FAIL: FAIL**

- ❌ evolver 未识别 SOCKS5_PROXY/HTTP_PROXY 环境变量缺失
- ❌ 未建议 curl proxy smoke test
- ❌ 未建议检查 systemd env/Service[Unit] env
- ℹ️ evolver 检测到 `tool_bypass` 信号（使用 exec 而非工具），但未分析 proxy-failure.log 内容

### 6.C systemd 场景（MODEL_PROVIDER 缺失）
**PASS / PARTIAL / FAIL: FAIL**

- ❌ evolver 未建议 systemctl --user status
- ❌ 未建议 journalctl --user -u hermes-gateway
- ❌ 未识别 MODEL_PROVIDER 环境变量缺失
- ℹ️ evolver 生成了 gene_distilled_s2g-env-vars（关于 Vercel env vars），但未分析 systemd-failure.log

### 6.D cron PATH 场景
**PASS / PARTIAL / FAIL: FAIL**

- ❌ evolver 未识别 cron 环境 PATH 与手动 shell 不一致
- ❌ 未建议显式 PATH/绝对路径/wrapper log
- ℹ️ evolver 没有生成关于 cron/PATH/scheduler 的任何诊断

### 6.E 工具行为验证
| 检查项 | 结果 |
|--------|------|
| 未连接 Hub | ✅ 确认 `[SearchFirst] No hub match (reason: no_hub_url)` |
| 未发布资产 | ✅ EVOLVER_AUTO_PUBLISH=false |
| 未开启 loop | ✅ 未使用 --loop |
| 未写入 secrets | ✅ 无 API key/token/cookie |
| 只生成 prompt/建议 | ⚠️ PARTIAL — ATP-AutoDeliver 后台进程在 run 期间活跃 |
| 未改真实系统 | ✅ fixture 外无修改 |
| no hub connection | ✅ 确认 local-only mode，无 Hub URL |
| no credits consumed | ✅ 无 Hub 连接，零 credits 消费 |

### 6.F 总结评分
| 场景 | 评分 | 说明 |
|------|------|------|
| A. npm test | FAIL | evolver 不分析 arbitrary 项目失败 |
| B. proxy | FAIL | evolver 未读取 memory/proxy-failure.log |
| C. systemd | FAIL | evolver 未读取 memory/systemd-failure.log |
| D. cron | FAIL | evolver 未读取 memory/cron-failure.log |
| E1. 无 Hub | ✅ PASS | 确认 no_hub_url |
| E2. 无发布 | ✅ PASS | EVOLVER_AUTO_PUBLISH=false |
| E3. 无 credits | ✅ PASS | 无 Hub，零消费 |
| E4. 无 secrets | ✅ PASS | 无 secrets 写入 |
| E5. ATP后台 | ⚠️ PARTIAL | ATP-AutoDeliver 存在但未消耗资源 |

---

## 7. evolver 架构观察

### 7.1 evolver 是什么（实际）
EvoMap Evolver 是一个 **自进化引擎**，不是通用失败日志分析器：
- 输入：evolver 自身的执行上下文（session logs、基因库、协议状态）
- 输出：GEP (Genome Evolution Protocol) JSON — 5 个 mandatory objects
- 工作方式：扫描 evolver 的 session，根据 signals 选择 Gene，执行 mutation
- 核心概念：Gene（可复用策略单元）、Capsule（执行结果）、EvolutionEvent（历史记录）

### 7.2 evolver 不是
- ❌ 不是通用 log 分析器
- ❌ 不是 OpenClaw/Hermes/Codex 的修复建议生成器
- ❌ 不能直接读取 arbitrary 失败日志并生成上下文感知的修复策略
- ❌ 没有直接读取 `memory/*.log` 文件的能力（除非它们在 evolver 的 session context 中）

### 7.3 正确的测试方向
要测试 evolver 分析 arbitrary 失败日志，需要：
1. 把失败日志嵌入 evolver 的 session context（通过某种方式注入）
2. 或者使用 evolver 的 skill distillation 功能
3. 或者通过 evolver 的 `--review` 机制配合真实的 evolution run

### 7.4 evolver 的本地能力
- ✅ 本地 GEP self-improvement cycle 可以运行
- ✅ Gene/Capsule/EvolutionEvent 本地存储
- ✅ 无 Hub 时可以继续使用（local-only mode）
- ✅ 不消费 credits
- ⚠️ ATP-AutoDeliver 后台进程（无 Hub 时无害）

---

## 8. 安装与运行问题记录

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| evolver run --help 执行了 evolution | evolver 把每个参数当作任务 | 直接用 `evolver run`，不用 --help |
| evolver --review 无 pending | 需要先 `evolver run` | 正确顺序：run → review → solidify |
| ATP-AutoDeliver 后台进程 | evolver 内置行为 | 无 Hub 时不消耗资源，可忽略 |
| Failed to write evolution_state.json | memory/evolution/ 目录不存在 | evolver 自动创建目录 |
| gh pr list failed | fixture 无 git remote | non-fatal，不影响 |

---

## 9. 四个场景失败的根本原因

**这不是 evolver 的 bug，而是测试设计的问题。**

EvoMap Evolver 的设计是 **自进化**：evolver 分析自身运行历史、修复自身协议缺陷。而用户期望的是 **通用失败日志分析**：把任意项目（npm test、systemd、proxy）的失败日志丢给 evolver，让它生成修复建议。

要实现后者，需要：
1. **Skill Distillation**：用 evolver distill 命令把修复知识固化成 Gene
2. **Hub fetch**：从 EvoMap Hub 下载已有的故障修复 Gene
3. **自定义 evolver 行为**：修改 evolver 的 session 扫描逻辑

**Evolver 更像是"AI Agent 的 Wikipedia repair pattern library"，而不是"Universal log analyzer"。**

---

## 10. 最终结论

| 问题 | 结论 |
|------|------|
| 是否适合继续测试 | ⚠️ 适合，但需要重新定义测试目标 |
| 是否适合接入 OpenClaw | ⚠️ 条件性适合：仅作为 evolver 自身的 self-repair 工具，不适合作为 OpenClaw 失败日志分析器 |
| 是否适合接入 Hermes/Codex | ❌ 不适合作为直接修复建议生成器 |
| 是否暂时不建议接 Hub | ✅ 确认：本地模式已验证，继续不接 Hub |
| evolver 真正适合做什么 | OpenClaw/Codex 等 agent 的 **自进化**：让 agent 从自身失败中学习，生成可复用的 Gene/Capsule |

---

## 11. 后续建议（Phase 2-4）

### Phase 2：在真实 OpenClaw session 内调用 evolver
- 把 evolver 集成到 OpenClaw 的 session 结束阶段
- 让 evolver 分析 OpenClaw 的 session 日志（而非 memory/*.log）
- 验证 evolver 能否从 OpenClaw 的 protocol_drift 中学习

### Phase 3：把 Hermes 真实失败日志喂给 Evolver
- 收集 Hermes 的真实失败场景（OOM、Telegram timeout、systemd restart）
- 把这些场景通过 evolver 的 skill distillation 固化成 Gene
- 验证 Hermes 能否从这些 Gene 中学习

### Phase 4：只读测试 EvoMap Hub fetch/directory
- 尝试 `evolver fetch --skill=<id>` 只下载不下发
- 尝试 `evolver sync --scope=purchased --dry-run` 预览不同 Scope
- 验证 Hub 的 Gene/Capsule library 是否对 OpenClaw 有参考价值

### 暂不测试
- ❌ evolver --loop（后台持续运行）
- ❌ evolver validator（分布式验证者角色）
- ❌ evolver auto-publish（自动发布 Gene）
- ❌ ATP autobuy（credits 消费）

---

## 12. 关键 artifact 路径

| 文件 | 路径 |
|------|------|
| evolver --review 输出 | `cases/evomap-evolver-openclaw-v0/artifacts/evolver-review-output.txt` |
| evolver run 输出 | `cases/evomap-evolver-openclaw-v0/artifacts/evolver-run-output.txt` |
| npm test 失败日志 | `fixtures/local-evolver-smoke/memory/npm-test-failure.log` |
| proxy 失败日志 | `fixtures/local-evolver-smoke/memory/proxy-failure.log` |
| systemd 失败日志 | `fixtures/local-evolver-smoke/memory/systemd-failure.log` |
| cron 失败日志 | `fixtures/local-evolver-smoke/memory/cron-failure.log` |
| evolver GEP 状态 | `fixtures/local-evolver-smoke/.evolver/gep/` |
| evolution 状态 | `fixtures/local-evolver-smoke/memory/evolution/` |
