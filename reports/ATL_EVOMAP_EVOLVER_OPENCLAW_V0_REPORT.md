# ATL_EVOMAP_EVOLVER_OPENCLAW_V0_REPORT.md
# ATL-EVOMAP-1 · EvoMap Evolver OpenClaw Local Smoke Test · Final Report

**Task:** ATL-EVOMAP-1
**Case:** evomap-evolver-openclaw-v0
**Date:** 2026-06-18 (Asia/Shanghai)
**Agent:** OpenClaw minimax/MiniMax-M2.7
**Repo:** https://github.com/conanxin/ai-tool-test-lab
**Status:** local offline smoke completed

---

## 执行摘要

ATL-EVOMAP-1 在 ai-tool-test-lab 中新增了 EvoMap Evolver 本地 smoke test 案例。

**关键发现：**
- Evolver 安装成功（v1.89.14），Node v22.22.0 + Git 2.43.0 满足要求
- `evolver run` 本地执行成功，GEP Cycle #0001 产出正常
- `[SearchFirst] No hub match (reason: no_hub_url)` — **确认无 Hub 连接，零 credits 消耗**
- 四个测试场景（A. npm test / B. proxy / C. systemd / D. cron）全部 **FAIL** — 根因是测试设计与工具设计不匹配：Evolver 是自进化引擎，不是通用失败日志分析器
- **Evolver 真正的价值：** 自进化（从自身协议失败中生成 Gene/Capsule），而非分析 arbitrary 项目失败日志

**Phase 2 建议：** 在真实 OpenClaw session 内测试 evolver（而非 memory/*.log）。

---

## 1. 任务目标回顾

在 ai-tool-test-lab 中新增 EvoMap Evolver 测试案例，验证本地 Evolver 能否帮助 OpenClaw 总结失败日志、生成修复策略，同时严格遵守 12 条硬边界。

---

## 2. 硬边界合规性

| # | 硬边界 | 状态 |
|---|--------|------|
| 1 | 不连接 EvoMap Hub | ✅ NO — `no_hub_url` |
| 2 | 不设置 A2A_HUB_URL | ✅ NO — unset |
| 3 | 不开启 evolver --loop | ✅ NO — 未用 --loop |
| 4 | 不开启 validator | ✅ NO — EVOLVER_VALIDATOR_ENABLED=false |
| 5 | 不自动发布 Gene/Capsule | ✅ NO — EVOLVER_AUTO_PUBLISH=false |
| 6 | 不消耗 credits | ✅ NO — 无 Hub，零消费 |
| 7 | 不写入 API key/token/cookie | ✅ NO — 无 secrets |
| 8 | 不修改 OpenClaw/Hermes/systemd/cron | ✅ NO |
| 9 | 不运行后台 daemon | ⚠️ PARTIAL — ATP-AutoDeliver 在 run 期间活跃（无 Hub 时无害） |
| 10 | 不提交 node_modules/.env/私密日志 | ✅ NO — .gitignore 保护 |
| 11 | 只在 ai-tool-test-lab 内操作 | ✅ YES |
| 12 | 只安装 @evomap/evolver | ✅ YES |

---

## 3. 安装验证

| 步骤 | 结果 |
|------|------|
| node --version | v22.22.0 ✅ |
| npm --version | 10.9.4 ✅ |
| git --version | 2.43.0 ✅ |
| npm install -g @evomap/evolver | ✅ added 50 packages |
| evolver --help | ✅ 显示完整 usage |

**Evolver 版本：** 1.89.14
**安装路径：** /usr/local/bin/evolver

---

## 4. Fixture 构建

```
fixtures/local-evolver-smoke/
├── calc.js        — 有 bug：String(a)+String(b) 导致 1+2="12"
├── test.js        — npm test 脚本
├── MEMORY.md      — 项目上下文
├── package.json   — npm init
└── memory/
    ├── npm-test-failure.log     — FAIL: add(1, 2) should be 3, got: 12
    ├── proxy-failure.log        — Telegram bot SOCKS5 proxy ETIMEDOUT
    ├── systemd-failure.log      — hermes-gateway.service MODEL_PROVIDER 缺失
    └── cron-failure.log          — cron PATH 缺失 uv/node
```

**Git 初始化：** master branch, root commit `ae4e962`

---

## 5. evolver run 执行结果

### 5.1 环境变量配置
```bash
unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private
```

### 5.2 关键输出
```
[ATP-AutoDeliver] Started (pollMs=60000)
[Evolve] Failed to write state file: ENOENT .../memory/evolution/evolution_state.json
[QuestionGenerator] Generated 1 proactive question(s).
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.
[OpenPR] gh pr list failed (non-fatal): no git remotes found
```

**GEP Cycle #0001 摘要：**
- Signal: `protocol_drift` (intensity=0.302)
- Intent: repair
- Selected Gene: `gene_gep_optimize_prompt_and_assets` (optimize) + `gene_tool_integrity` (repair)
- Outcome: SUCCESS, score=0.78, blast_radius=1 file/3 lines

### 5.3 evolver --review 结果
```
[Review] No pending evolution run to review.
Run "node index.js run" first to produce changes, then review before solidifying.
```
（需要先 run 再 review）

---

## 6. 四场景评分

| 场景 | 评分 | 关键发现 |
|------|------|----------|
| A. npm test (字符串拼接) | **FAIL** | evolver 未识别 add(1,2)="12" bug；未指出类型问题；未建议修复 |
| B. proxy (Telegram SOCKS5) | **FAIL** | evolver 未读取 memory/proxy-failure.log；未建议 proxy smoke test |
| C. systemd (MODEL_PROVIDER) | **FAIL** | evolver 未读取 memory/systemd-failure.log；未建议 journalctl |
| D. cron (PATH 差异) | **FAIL** | evolver 未读取 memory/cron-failure.log；未建议绝对路径 |
| E1. 无 Hub 连接 | ✅ PASS | `no_hub_url` confirmed |
| E2. 无资产发布 | ✅ PASS | EVOLVER_AUTO_PUBLISH=false |
| E3. 无 credits 消费 | ✅ PASS | 无 Hub，零消费 |
| E4. 无 secrets 写入 | ✅ PASS | 无 API key/token/cookie |
| E5. 无 --loop | ✅ PASS | 未使用 --loop |
| E6. 未改真实系统 | ✅ PASS | fixture 外无修改 |
| no hub connection | ✅ PASS | 确认 local-only mode |
| no credits consumed | ✅ PASS | 无 Hub，零 credits 消费 |

**四场景全部 FAIL 的根因：** EvoMap Evolver 是 **自进化引擎**（分析自身协议状态、生成 Gene/Capsule），不是 **通用失败日志分析器**（直接读 arbitrary *.log、生成上下文感知修复建议）。测试设计期望后者，但工具是前者。

---

## 7. evolver 架构发现

### 7.1 实际工作方式
1. `evolver run` 启动，扫描自身 session context（不是项目的 memory/*.log）
2. 提取 signals（protocol_drift、tool_bypass 等）
3. 从本地 Gene library（`.evolver/gep/`）选择匹配的 Gene
4. 执行 GEP mutation cycle，输出 5 个 mandatory JSON objects
5. 如果有 Hub URL，尝试 hub search；无则本地继续

### 7.2 evolver 不是
- ❌ 通用失败日志分析器
- ❌ 直接读 arbitrary 项目文件的工具
- ❌ OpenClaw/Hermes 的修复建议生成器
- ❌ 直接消费 memory/*.log 的工具

### 7.3 evolver 是什么
- ✅ 自进化引擎（从自身协议失败中学习）
- ✅ Gene/Capsule/EvolutionEvent 管理工具
- ✅ 本地 GEP 存储库
- ✅ 无 Hub 仍可运行的本地工具

---

## 8. 新增文件清单

```
cases/evomap-evolver-openclaw-v0/
├── README.md              (4,984 bytes) — case 概览
├── CASE_REPORT.md         (11,600 bytes) — 完整技术报告
├── artifacts/
│   ├── evolver-review-output.txt   (127 bytes)
│   └── evolver-run-output.txt       (51,395 bytes)
└── fixtures/local-evolver-smoke/
    ├── MEMORY.md / calc.js / test.js / package.json
    └── memory/*.log (4 个失败日志)

scripts/validate_evomap_evolver_openclaw_case.py  (新验证脚本)

reports/ATL_EVOMAP_EVOLVER_OPENCLAW_V0_REPORT.md   (本报告)
```

**同时更新：**
- `data/cases.json` — 新增第二个 case 条目
- `README.md` — 新增第二个案例说明

---

## 9. 结论与建议

### 结论

| 问题 | 结论 |
|------|------|
| evolver 是否可用作 OpenClaw 经验复用工具 | ⚠️ 条件性可用，但需要正确使用方式 |
| evolver 是否适合作为 OpenClaw 失败日志分析器 | ❌ 不适合；应使用专门的 log 分析方法 |
| evolver 是否适合自进化（self-repair） | ✅ 适合 |
| Hub 连接建议 | ✅ 继续不接 Hub，本地模式已验证 |
| evolver 接入 OpenClaw 的正确方式 | 让 evolver 分析 OpenClaw 自身 session，而非 memory/*.log |

### 后续建议（Phase 2-4）

**Phase 2：** 在真实 OpenClaw session 内调用 evolver
- 把 OpenClaw 的 session 上下文注入 evolver
- 验证 evolver 能否从 OpenClaw 的 protocol_drift 中生成 Gene
- 关注 evolver 是否能识别 OpenClaw 的高频 tool bypass 模式

**Phase 3：** Skill Distillation 测试
- 用 `evolver distill` 把 Hermes 真实失败固化成 Gene
- 验证 distill 输出的 Gene 质量
- 不需要 Hub 连接

**Phase 4：** Hub fetch/directory 只读测试
```bash
evolver fetch --skill=<id> --out=./skills/    # 只下载不下发
evolver sync --scope=purchased --dry-run        # 预览不下发
```

**暂不测试：** --loop / validator / auto-publish / ATP autobuy / Hub 连接

---

## 10. 执行记录

```
ATL-EVOMAP-1 completed: 2026-06-18 20:56-21:30 GMT+8
Evolver installed: YES (v1.89.14)
evolvers run: YES (GEP Cycle #0001, SUCCESS)
Hub connection: NO (no_hub_url)
Credits consumed: 0
Hard boundaries: 11/12 PASS, 1/12 PARTIAL (ATP-AutoDeliver)
Four test scenarios: 4 FAIL (design mismatch, not tool bug)
Overall verdict: PARTIAL — tool works, wrong test design
Next: Phase 2 with OpenClaw session context injection
```
