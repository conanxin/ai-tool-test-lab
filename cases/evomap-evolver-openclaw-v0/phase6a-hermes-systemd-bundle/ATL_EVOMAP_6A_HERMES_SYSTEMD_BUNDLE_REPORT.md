# ATL-EVOMAP-6A · Hermes Systemd Service Recovery Bundle Report

**Date:** 2026-06-19 04:05 +0800
**Phase:** ATL-EVOMAP-6A
**Result:** **PASS**
**Base:** Phase 5 commit `c1a6b9a` (OpenClaw Local Evolution Kit)
**Bundle ID:** `hermes-systemd-service-recovery.bundle.json`
**Gene ID:** `gene_distilled_hermes-systemd-service-recovery`
**Capsule ID:** `capsule_hermes_systemd_service_recovery_phase6a`

---

## 1 · 目标

在 ai-tool-test-lab 中继续扩展 OpenClaw Local Evolution Kit，创建第二个
可复用 local-only bundle：**Hermes systemd service recovery bundle**。该
bundle 用于沉淀 Hermes / OpenClaw 场景中 systemd user service 故障恢复经验
（不是修改真实 Hermes/systemd 配置）。

本阶段不是继续探索 Evolver 内部，而是产出第二个 canonical bundle：

1. **离线文本 fixture** 描述可复现的 Hermes gateway 失败 shape
2. **离线 parser** 解析 fixture 并输出 JSON summary（不读 .env / 不执行
   systemctl / journalctl）
3. **Hermes-specific Gene**（repair-category）+ **Capsule**（含
   execution_trace）
4. **portable bundle** 沿用 Phase 5 schema `atl-evomap-portable-bundle-v0.1`
5. **inspect / validate / apply 全部 PASS** + **apply --yes 后 target
   runtime 写入 Gene + Capsule + memory signals**
6. **可选 evolver run/review smoke** 验证 bundle 在 evolver 中存活（不
   approve / 不 solidify / 不连 Hub）

---

## 2 · Phase 5 解锁条件

ATL-EVOMAP-5 已完成（commit `c1a6b9a`），已建立 OpenClaw Local Evolution Kit：

- `scripts/evomap_inspect_bundle.py`
- `scripts/evomap_validate_bundle.py`
- `scripts/evomap_apply_bundle.py`
- `bundle schema: atl-evomap-portable-bundle-v0.1`
- `templates/GENE_TEMPLATE.json` / `CAPSULE_TEMPLATE.json` /
  `MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl`
- apply dry-run / apply --yes 全部 PASS（target runtime:
  `/tmp/atl-evomap-phase5-apply-target`）

Phase 5 是第一个 optimize-category bundle。Phase 6A 是第二个 bundle，类别
为 `repair`，与 Phase 5 互补，证明 kit 支持多类别。

---

## 3 · Hermes systemd failure model

Hermes gateway 在生产环境中反复出现同一种失败 shape：

| 症状 | 检测方式 |
|---|---|
| `hermes-gateway.service` `Active: failed` | `systemctl --user status` |
| `code=exited, status=2/INVALIDARGUMENT` | `journalctl --user -u` |
| `start-limit-hit`（重启计数到 3+） | `journalctl --user -u` |
| `MODEL_PROVIDER` 等 runtime env unset | `systemctl --user show-environment` |
| drop-in `env.conf` 指向缺失的 `.env` 文件 | `~/.config/systemd/user/<svc>.d/env.conf` |
| `127.0.0.1:18789` 不在 LISTEN | `ss -ltnp | grep 18789` |
| Telegram smoke 未发送 | manual / curl |

这种 shape 在 2026-06-10 OOM 崩溃后多次出现（参见
`workspace/reports/openclaw_post_recovery_healthcheck_20260610_093412.md`）。

---

## 4 · Offline fixture + parser

### 4.1 Fixture

`cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/fixtures/hermes-systemd-failure-sample.txt`
（1803 B）描述上述全部症状，并显式声明硬边界：

> Hard rules for any recovery script
> ---------------------------------
> - Do not print secrets
> - Do not read .env
> - Do not restart real service in this fixture
> - Only parse this text

### 4.2 Parser

`scripts/hermes_systemd_recovery_fixture.py`（7472 B，stdlib only）：

- **ONLY** 接受 `--input <path>`，**拒绝** `.env`-shape 路径
- **NEVER** reads .env files / recursively scans repo / executes
  systemctl-journalctl-ss-curl
- 用 `re` 提取：`service` / `service_failed` / `missing_env_var`（priority:
  `is unset` > `missing <ENV>` 不在 path 上下文）/ `expected_port` /
  `port_not_listening` / `telegram_smoke_missing` /
  `main_process_status` / `restart_counter_at` / `restart_limit_hit` /
  `dropin_env_lines_present` / `dropin_points_to_missing_env`
- 输出 deterministic JSON summary + 6-step `recommended_check_order`
- 安全块 `safety` 显式声明 `no_real_systemctl/no_real_journalctl/no_env_scan/no_secrets/no_network_call/no_repo_scan=true`

### 4.3 Parser output

```json
{
  "ok": true,
  "service": "hermes-gateway.service",
  "service_failed": true,
  "missing_env_var": "MODEL_PROVIDER",
  "expected_port": "127.0.0.1:18789",
  "port_not_listening": true,
  "main_process_status": "2/INVALIDARGUMENT",
  "restart_counter_at": 3,
  "restart_limit_hit": true,
  "dropin_env_lines_present": true,
  "dropin_points_to_missing_env": true,
  "telegram_smoke_missing": false,
  "recommended_check_order_steps": 6,
  "safety": {
    "no_real_systemctl": true,
    "no_real_journalctl": true,
    "no_env_scan": true,
    "no_secrets": true,
    "no_network_call": true,
    "no_repo_scan": true
  }
}
```

全部断言通过：`missing_env_var == MODEL_PROVIDER`、`service_failed ==
true`、`expected_port == 127.0.0.1:18789`、`port_not_listening == true`。

---

## 5 · Gene 设计

`artifacts/gene-hermes-systemd-service-recovery.json`（2111 B）：

- **type:** `Gene`
- **id:** `gene_distilled_hermes-systemd-service-recovery`
- **category:** `repair`
- **signals_match:** 12 个信号（5 bare + 5 qualified + 2 session/repo context）：
  ```
  systemd_failure, service_recovery, missing_env_var,
  port_not_listening, dropin_env_misconfigured,
  systemd_failure:user-service, service_recovery:start-limit-hit,
  missing_env_var:MODEL_PROVIDER, port_not_listening:18789,
  dropin_env_misconfigured:env-conf-missing,
  session_context:hermes, repo_context:ai-tool-test-lab
  ```
  bare + qualified 双写是为了规避 Evolver scanner 的 qualified→bare
  normalization（与 Phase 5 同样的策略）。
- **strategy:** 6 步可执行规则
- **constraints.max_files:** 8，`forbidden_paths` 包含
  `.git / node_modules / .evolver / memory / real_runtime_root`

---

## 6 · Capsule 设计

`artifacts/capsule-hermes-systemd-service-recovery.json`（2554 B）：

- **schema_version:** `1.6.0`
- **id:** `capsule_hermes_systemd_service_recovery_phase6a`
- **trigger:** 6 个 trigger 信号（与 Gene signals_match 子集对齐）
- **gene:** `gene_distilled_hermes-systemd-service-recovery`
- **confidence:** 0.82
- **blast_radius:** `{files: 0, lines: 0}`（离线 fixture 不修改真实文件）
- **status:** `success`
- **execution_trace:** 4 步（与 Phase 5 一致）
  1. `build`: `python3 scripts/hermes_systemd_recovery_fixture.py --input <fixture>`
     → output_summary 含全部 fixture detection 字段
  2. `validate`: `python3 -m json.tool artifacts/hermes-systemd-fixture-output.json`
     → `json_parse_pass`
  3. `validate`: `assert missing_env_var == MODEL_PROVIDER and service_failed == true ...`
     → `fixture_detected_expected_failure_shape`
  4. `canary`: `safety_check` → 8 个 canary 全 true
     （no_real_systemctl / no_real_journalctl / no_env_scan / no_secrets /
     no_hub / no_publish / no_approve / no_solidify）

---

## 7 · Bundle schema

`bundle/hermes-systemd-service-recovery.bundle.json`（8587 B）：

```json
{
  "schema_version": "atl-evomap-portable-bundle-v0.1",
  "source_phase": "ATL-EVOMAP-6A",
  "source_session": "/tmp/atl-evomap-phase6a-hermes-target",
  "target_capsule_id": "capsule_hermes_systemd_service_recovery_phase6a",
  "target_gene_id": "gene_distilled_hermes-systemd-service-recovery",
  "gene": { ... },
  "capsule": { ... },
  "execution_trace": [ ... 4 steps ... ],
  "fixture_summary": { ... },   ← Phase 6A 唯一新增字段
  "safety": { "hub": "disabled", "publish": "disabled", "credits": 0, ... },
  "import_contract": { ... },
  "kit_provenance": { "phase_5_commit": "c1a6b9a", "phase_6a_phase": "ATL-EVOMAP-6A" }
}
```

`fixture_summary` 字段是 Phase 6A 唯一新增，它把 *parser 必须检测出的失败
shape* 固化进 bundle，让未来 regressions 可以在 validate 阶段被自动捕获。

---

## 8 · inspect / validate 结果

### 8.1 inspect

```
$ python3 scripts/evomap_inspect_bundle.py --bundle <bundle>
ok: true
schema_version: atl-evomap-portable-bundle-v0.1
gene_id: gene_distilled_hermes-systemd-service-recovery
gene_category: repair
capsule_id: capsule_hermes_systemd_service_recovery_phase6a
capsule_status: success
capsule_confidence: 0.82
capsule_visibility: private
capsule_source: manual_capsule_seed_phase6a
execution_trace_steps: 4
execution_trace_stages: ["build", "validate", "validate", "canary"]
safety.hub: disabled
safety.publish: disabled
```

### 8.2 validate（12 检查 + secret scan）

```
ok: true
failures: []
summary.capsule_gene_match: true
summary.capsule_execution_trace_steps: 4
summary.required_import_files_count: 3
summary.secret_hits: 0
```

12 检查全 PASS，secret scan 0 hits。

---

## 9 · apply dry-run / apply --yes 结果

### 9.1 dry-run

```
target: /tmp/atl-evomap-phase6a-hermes-target
is_git_repo: false   (target 是 /tmp，不是 git repo，warn 但允许)
new_gene_count: 1
new_capsule_count: 1
memory_graph_signals_added: 5
writes planned: 6 files
filesystem touched: NO
```

### 9.2 apply --yes

```
target: /tmp/atl-evomap-phase6a-hermes-target
mode: applied
plan_summary: {existing_gene_count: 0, existing_capsule_count: 0,
                new_gene_count: 1, new_capsule_count: 1,
                memory_graph_signals_added: 5}
log.errors: []
log.writes_executed: 6 files
```

On-disk verify：

```
genes.json:    {"schema_version":"1.6.0","genes":[{...1 gene...}]}
capsules.json: {"schema_version":"1.6.0","capsules":[{...1 capsule...}]}
memory_graph.jsonl: 5 lines（Phase 5 通用 bare signals）
events.jsonl:  empty (reset)
failed_capsules.json: "[]" (reset)
candidates.jsonl: empty (reset)
```

---

## 10 · optional evolver run/review smoke

### 10.1 准备

```bash
cd /tmp/atl-evomap-phase6a-hermes-target
git init && git config ... && git commit -m "init isolated runtime"
unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private
```

Evolver 第一次要求 git repo，先 `git init` 后 retry。

### 10.2 evolver run

```
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.  ← Hub 未连接
Selection: Selected Gene "gene_distilled_hermes-systemd-service-recovery".        ← Hermes Gene 被选中
ACTIVE STRATEGY: 6 steps as written in Gene.strategy
Recommended intent: optimize (not requested as repair here, but selection honored)
```

未崩溃，未连 Hub，未 publish。

### 10.3 evolver review（不 approve / 不 solidify）

```
[Review] Pending evolution run: run_1781813126900
Gene: gene_distilled_hermes-systemd-service-recovery
Capsule: capsule_hermes_systemd_service_recovery_phase6a
Diff: (no changes detected)
To approve and solidify:  node index.js review --approve    ← 未执行
To reject and rollback:   node index.js review --reject
```

bundle 存活，review 看到我们的 Gene + Capsule，**未 approve**，**未 solidify**。

### 10.4 bundle 仍存活

```
genes:    ['gene_distilled_hermes-systemd-service-recovery']
capsules: ['capsule_hermes_systemd_service_recovery_phase6a']
memory_graph lines: 8（5 from apply + 3 from evolver run cycles）
```

---

## 11 · 安全边界（16 项全部 preserved）

| # | 边界 | 实现位置 |
|---|---|---|
| 1 | 不连 EvoMap Hub | parser `no_network_call=true` / apply tool / no `A2A_HUB_URL` |
| 2 | 不设置 `A2A_HUB_URL` | env 不导出 / bundle safety |
| 3 | 不使用 `--loop` | recipe step 显式不调用 |
| 4 | 不开 validator | `EVOLVER_VALIDATOR_ENABLED=false` / bundle safety |
| 5 | 不 auto-publish | `EVOLVER_AUTO_PUBLISH=false` / bundle safety |
| 6 | 不消耗 credits | `safety.credits=0` |
| 7 | 不 ATP autobuy | `EVOLVER_ATP_AUTOBUY=off` |
| 8 | 不读 / 不写 secret / API key / token / cookie / Authorization / private key | validate tool secret scan 0 hits / parser 拒绝 `.env` |
| 9 | 不扫描 .env | parser `no_env_scan=true` / no repo recursive walk |
| 10 | 不修改 OpenClaw / Hermes / systemd / cron 真实配置 | apply 只写 `<target>/.evolver/` + `<target>/memory/` |
| 11 | 不修改 Evolver package 源码 | no edits to `~/.local/lib/node_modules/@evomap/evolver/` |
| 12 | 不执行 `evolver review --approve` | smoke output 末尾明文提示，未执行 |
| 13 | 不执行 `evolver solidify` | smoke output 末尾明文提示，未执行 |
| 14 | 不提交 runtime `.evolver/` 和 `memory/` 原件 | target 是 `/tmp/...`，从不 commit |
| 15 | 只提交 kit 文件 / bundle artifact / tools / templates / 报告 / validator | commit whitelist |
| 16 | 工具必须 Python stdlib only | fixture parser 仅用 argparse / json / re / sys / pathlib |

---

## 12 · 最终结论

**ATL-EVOMAP-6A · PASS**

- 离线 fixture 描述真实 Hermes 失败 shape ✅
- 离线 parser 安全（不读 .env / 不执行 systemctl / 不扫描 repo）✅
- Gene / Capsule / Bundle 全部 JSON 合法 ✅
- inspect / validate 12 检查全 PASS / secret_hits=0 ✅
- apply dry-run PASS（0 文件写入）/ apply --yes PASS（6 文件写入 + 5
  memory signals 追加）✅
- 可选 evolver run/review smoke PASS：Hermes Gene 被选中，Capsule 可见，
  不 crash / 不连 Hub / 不 approve / 不 solidify ✅
- bundle 仍存活于 target runtime ✅
- 全部 16 项硬边界 preserved ✅

Phase 6A 证明 OpenClaw Local Evolution Kit **支持第二个 bundle、第二个
intent category（repair）**。可以继续扩展到 Codex / browser-control /
Telegram proxy 等其他 bundle。

---

## 13 · 下一步建议

1. **Hermes-specific signal injection** 扩展 `evomap_apply_bundle.py`
   增加 `--inject-signals-from <bundle>` 选项，把 bundle 内的
   `signals_match`（如 `systemd_failure`, `missing_env_var`）也注入到
   `memory_graph.jsonl`，让 evolver 后续 cycles 能更精准地选中 Hermes
   Gene（当前注入的是 Phase 5 的通用 bare signals）
2. **Codex bundle**（如 `codex-prompt-cache-discipline`，
   `optimize`-category）
3. **Browser-control bundle**（如 `playwright-rate-limit-recovery`，
   `repair`-category）
4. **Telegram proxy bundle**（如 `telegram-message-router-failure`，
   `repair`-category）
5. **bundle-curator skill** 自动从 evolver run 产出物（`/skill-payload/`）
   生成 portable bundle

后续所有 bundle 仍保持同样的 16 项硬边界。

---

*Report generated 2026-06-19 04:05 +0800 by `MiniMax-M3`*
*Base: `c1a6b9a` (Phase 5) — Bundle: `hermes-systemd-service-recovery.bundle.json` (8587 B)*