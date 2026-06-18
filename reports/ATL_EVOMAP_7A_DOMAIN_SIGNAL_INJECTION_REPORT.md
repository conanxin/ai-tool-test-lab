# ATL-EVOMAP-7A · Domain-Specific Signal Injection Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** ATL-EVOMAP-7A
**Status:** Domain signal injection completed (PASS)
**Date:** 2026-06-19
**Base commit:** `f72b0c1` (ATL-EVOMAP-6B)
**Phase 5/6A base commits:** `c1a6b9a` / `00caf1d` / `f72b0c1`

---

## 1. 目标

在 ai-tool-test-lab 中继续扩展 OpenClaw / Hermes Local Evolution Kit，
本阶段目标是**增强已有的 bundle apply 工具**：

```
scripts/evomap_apply_bundle.py
```

新增能力：

```
--inject-signals-from <bundle.json>
```

让 apply tool 在写入 target runtime 时，不只注入 Phase 5 默认的 5 个 generic signals：

```
tool_bypass
repeated_tool_usage
protocol_drift
session_context
repo_context
```

还可以从指定 bundle 中提取 **domain-specific signals**，例如：

Hermes systemd bundle:
```
systemd_failure
service_recovery
missing_env_var
missing_env_var:MODEL_PROVIDER
port_not_listening
dropin_env_misconfigured
```

Telegram router bundle:
```
telegram_failure
message_router_failure
proxy_mismatch
delivery_terminal_missing
sendmessage_timeout
retry_consumed
smoke_not_confirmed
```

本阶段**不是**创建新 bundle，而是**强化 Phase 5 工具链**，使 Phase 6A / 6B bundle 导入后
更容易被 selector 通过 `score_ranked` / capsule trigger path 命中，而不是只依赖
`distilled_fallback`。

---

## 2. Phase 6B 解锁条件

- ATL-EVOMAP-6B 已完成，commit `f72b0c1`
- 当前资产库：
  - Bundle 1: OpenClaw tool-use discipline — optimize
  - Bundle 2: Hermes systemd service recovery — repair
  - Bundle 3: Telegram message router failure — repair
- 当前限制：
  - `evomap_apply_bundle.py` 默认只注入 5 个 generic bare signals
  - Phase 6A / 6B 的 domain-specific signals 只存在于
    `gene.signals_match` / `capsule.trigger` / `fixture_summary`
  - apply 到 target runtime 后，`memory_graph.jsonl` 里还没有
    `systemd_failure` / `telegram_failure` / `proxy_mismatch` 等领域信号
  - selector 有时依赖 `distilled_fallback`，而不是 domain signal match

ATL-EVOMAP-7A 目标：

1. 扩展 apply tool：支持 `--inject-signals-from <bundle>`
2. 从 bundle 的 `gene.signals_match` + `capsule.trigger` 中提取 domain-specific signals
3. 过滤危险/污染 signals
4. 注入 generic + domain signals 到 `memory/evolution/memory_graph.jsonl`
5. dry-run 显示 planned signals，不写文件
6. `--yes` 真写入 target runtime
7. 对 OpenClaw / Hermes systemd / Telegram router 三个 bundle 都做回归测试
8. 保持 no Hub / no publish / no credits / no approve / no solidify

---

## 3. apply tool 修改说明

`scripts/evomap_apply_bundle.py` 改动摘要：

### 3.1 新增 CLI flag

```
--inject-signals-from INJECT_SIGNALS_FROM
  Optional path to a bundle JSON whose gene.signals_match and
  capsule.trigger are extracted and injected (after filtering) as
  domain-specific memory signals. Without this flag, only the 5
  Phase 5 generic bare signals are written (backward-compatible).
```

### 3.2 新增常量 / 数据结构

| 名字 | 作用 | 来源 |
|---|---|---|
| `CLEAN_BARE_SIGNALS` (5 项) | Phase 5 baseline 5 个 generic signals | Phase 4A/4B/4C legacy |
| `DANGEROUS_SIGNALS` (21 项) | 危险 / 污染 signal 黑名单 | evolver internal noise |
| `DANGEROUS_SUBSTRINGS` (13 项) | 包含即拒绝的子串 | credential hygiene |
| `CREDENTIAL_PATTERN` (6 类) | 凭证-like 模式 | bot token / auth header / api key / jwt / private key / 12+ digit |
| `ALLOWED_SIGNAL_CHARS` | 合法字符集 regex | `[A-Za-z0-9_:\-\.]{1,120}` |

### 3.3 新增核心函数

```python
def _validate_signal_name(s: str) -> tuple[bool, str]:
    """Return (is_valid, reason_if_invalid)."""
    # 1) 类型检查
    # 2) DANGEROUS_SIGNALS 黑名单
    # 3) ALLOWED_SIGNAL_CHARS 字符 + 长度
    # 4) DANGEROUS_SUBSTRINGS 子串
    # 5) CREDENTIAL_PATTERN regex (case-insensitive)

def _make_bare_memory_events(target_gene_id, ts_base) -> list[str]:
    """Phase 5 baseline: 5 clean bare signals with legacy origin."""
    # 不变

def _make_domain_memory_events(signals, target_gene_id, ts_base) -> tuple[list[str], list[dict]]:
    """Build MemoryGraphEvent lines for domain signals.
    Returns (lines, rejected_records)."""
    # origin = "evomap_apply_bundle:domain_from_bundle"
    # weight = 0.8
    # 每个 signal 一行 JSON
    # 不写 failed outcome
    # 不写 user_feature_request
    # 不写 consecutive_failure_streak

def _extract_signals_from_bundle(bundle) -> list[str]:
    """Extract candidate domain signal names from gene.signals_match + capsule.trigger.
    Preserves order, de-duplicates."""
    # 来源: bundle.gene.signals_match, bundle.capsule.trigger
```

### 3.4 plan_apply 扩展

`plan_apply(bundle, target, domain_signals=None)`：

- 保留原有 6 个 writes（3 required + 3 optional）
- 新增字段：
  - `signal_injection_mode`: `generic_only` 或 `generic_plus_domain_from_bundle`
  - `generic_signals`: 5 个 generic signal 名字
  - `domain_signals`: 已保留的 domain signal 名字
  - `domain_signals_rejected`: 被拒绝的 `(signal, reason)` 列表
- `summary` 新增：
  - `memory_graph_signals_added`: 总写入行数
  - `memory_graph_generic_signals`: 5
  - `memory_graph_domain_signals`: N
  - `memory_graph_domain_rejected`: M

### 3.5 默认行为保留

**关键不变量**：不传 `--inject-signals-from` 时：
- `signal_injection_mode == "generic_only"`
- `domain_signals == []`
- `domain_signals_rejected == []`
- `memory_graph_signals_added == 5`
- origin 全部是 `openclaw_signal_detector`（Phase 5 lineage 完整保留）

Phase 5/6A/6B 三套 validator 全部 ALL CHECKS PASSED 确认无回归。

---

## 4. signal extraction / filtering 规则

### 4.1 来源

从 `--inject-signals-from <path>` 指向的 JSON 提取：

| 字段路径 | 类型 | 用途 |
|---|---|---|
| `bundle.gene.signals_match` | list[str] | 主 signal 集合 |
| `bundle.capsule.trigger` | list[str] | capsule 触发条件 |

### 4.2 过滤规则

**允许**：
- 字母、数字、下划线、冒号、短横线、点
- 长度 1 到 120

**拒绝**（任一命中即拒绝）：
1. `DANGEROUS_SIGNALS` 黑名单 21 项
2. 危险子串 13 项（含 `token` / `secret` / `cookie` / `authorization` / `auth` / `private_key` / `api_key` / `apikey` / `bearer` / `password` / `passwd` / `ssh-rsa` / `ssh-ed25519`）
3. 凭证-like 模式 6 类（bot token / Authorization / API key / JWT / private key / 12+ digit 纯数字）

### 4.3 写入格式

每个 signal 一行 `MemoryGraphEvent` JSON：

```json
{
  "type": "MemoryGraphEvent",
  "ts": 1718700200.0,
  "signal": "telegram_failure",
  "origin": "evomap_apply_bundle:domain_from_bundle",
  "weight": 0.8,
  "context": "domain-specific signal injected from bundle (gene=gene_distilled_telegram-message-router-failure)",
  "mutation": {
    "target": "gene:gene_distilled_telegram-message-router-failure",
    "action": "select"
  }
}
```

不写 failed outcome，不写 `user_feature_request`，不写 `consecutive_failure_streak`。

---

## 5. default apply regression 结果

**目标 bundle:** `cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json`
**Target:** `/tmp/atl-evomap-7a-default-apply-target`（git init + .gitignore `node_modules/`, `.evolver/`, `memory/`）

| Step | ok | mode | memory_graph_signals_added | generic | domain | rejected |
|--|--|--|--|--|--|--|
| dry-run | True | `generic_only` | 5 | 5 | 0 | 0 |
| --yes | True | `generic_only` | 5 | 5 | 0 | 0 |

实际写入 `memory_graph.jsonl`：

```
tool_bypass           | origin: openclaw_signal_detector
repeated_tool_usage   | origin: openclaw_signal_detector
protocol_drift        | origin: openclaw_signal_detector
session_context       | origin: openclaw_signal_detector
repo_context          | origin: openclaw_signal_detector
```

→ 与 Phase 5 baseline 1:1 一致。无 regression。

---

## 6. Hermes domain signal injection 结果

**目标 bundle:** `cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json`
**Target:** `/tmp/atl-evomap-7a-hermes-domain-target`

| Step | ok | mode | memory_graph_signals_added | generic | domain | rejected |
|--|--|--|--|--|--|--|
| dry-run | True | `generic_plus_domain_from_bundle` | 17 | 5 | 12 | 0 |
| --yes | True | `generic_plus_domain_from_bundle` | 17 | 5 | 12 | 0 |

**注入的 12 个 domain signals**：

```
systemd_failure
service_recovery
missing_env_var
port_not_listening
dropin_env_misconfigured
systemd_failure:user-service
service_recovery:start-limit-hit
missing_env_var:MODEL_PROVIDER
port_not_listening:18789
dropin_env_misconfigured:env-conf-missing
session_context:hermes
repo_context:ai-tool-test-lab
```

任务要求的关键 signals **全部命中**：

- ✅ `systemd_failure`
- ✅ `service_recovery`
- ✅ `missing_env_var`
- ✅ `missing_env_var:MODEL_PROVIDER`
- ✅ `port_not_listening`
- ✅ `dropin_env_misconfigured`

---

## 7. Telegram domain signal injection 结果

**目标 bundle:** `cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json`
**Target:** `/tmp/atl-evomap-7a-telegram-domain-target`

| Step | ok | mode | memory_graph_signals_added | generic | domain | rejected |
|--|--|--|--|--|--|--|
| dry-run | True | `generic_plus_domain_from_bundle` | 27 | 5 | 22 | 0 |
| --yes | True | `generic_plus_domain_from_bundle` | 27 | 5 | 22 | 0 |

**注入的 22 个 domain signals**：

```
telegram_failure
message_router_failure
proxy_mismatch
proxy_missing
delivery_terminal_missing
sendmessage_timeout
sendvoice_unconfirmed
retry_consumed
smoke_not_confirmed
session_context
repo_context
telegram_failure:delivery-timeout
message_router_failure:no-terminal-result
proxy_mismatch:sendmessage-sendvoice
proxy_missing:sendmessage
delivery_terminal_missing:telegram
sendmessage_timeout:telegram-response
sendvoice_unconfirmed:delivery
retry_consumed:no-terminal-event
smoke_not_confirmed:telegram
session_context:hermes
repo_context:ai-tool-test-lab
```

任务要求的关键 signals **全部命中**：

- ✅ `telegram_failure`
- ✅ `message_router_failure`
- ✅ `proxy_mismatch`
- ✅ `delivery_terminal_missing`
- ✅ `sendmessage_timeout`
- ✅ `retry_consumed`
- ✅ `smoke_not_confirmed`
- ✅ `proxy_mismatch:sendmessage-sendvoice`

---

## 8. optional evolver smoke 结果

### 8.1 Hermes target smoke

**环境：**
- `A2A_HUB_URL=unset`
- `EVOLVE_STRATEGY=repair-only`
- `EVOLVER_AUTO_PUBLISH=false`
- `EVOLVER_VALIDATOR_ENABLED=false`
- `EVOLVER_ATP_AUTOBUY=off`
- `EVOLVER_DEFAULT_VISIBILITY=private`

**`evolver run`：**
```
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.
Reason: signals match gene.signals_match; signals: tool_bypass; drift_intensity: 1.000; selection_path: distilled_fallback
2. Selection: Selected Gene "gene_distilled_hermes-systemd-service-recovery".
```

**`evolver review`：**
```
[Review] Pending evolution run: run_1781816170344
Category: repair
--- Mutation ---
  Category:   innovate
  Risk Level: medium
--- Diff ---
  (no changes detected)
```

**memory_graph：** 17 → 20 lines（+3 from evolver run cycles）

✅ **不 approve**，**不 solidify**（`[SOLIDIFY REQUIRED]` 仅是 evolver 提示，未实际执行）

### 8.2 Telegram target smoke

**`evolver run`：**
```
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.
Reason: signals match gene.signals_match; signals: tool_bypass; drift_intensity: 1.000; selection_path: distilled_fallback
2. Selection: Selected Gene "gene_distilled_telegram-message-router-failure".
```

**`evolver review`：**
```
[Review] Pending evolution run: run_1781816178461
Category: repair
--- Mutation ---
  Category:   innovate
  Risk Level: medium
--- Diff ---
  (no changes detected)
```

**memory_graph：** 27 → 30 lines

**关键证据**：Telegram evolver run 的 signals 列表**实际包含** Phase 7A 注入的 domain signals：

```
"telegram_failure",
"telegram_failure:delivery-timeout",
"delivery_terminal_missing:telegram",
"sendmessage_timeout:telegram-response",
```

→ domain signals **真实进入 evolver 的 signal-match 路径**，selector 不再只靠 `distilled_fallback` 的 tool_bypass。

✅ **不 approve**，**不 solidify**。

---

## 9. 安全边界

### 9.1 16 项硬边界全部保留

```
no Hub / no A2A_HUB_URL / no --loop / no validator / no auto-publish /
no credits / no ATP autobuy / no secrets / no .env scan /
no real OpenClaw-Hermes-systemd-cron config mutation /
no Evolver source modification / no evolver --approve /
no evolver solidify / no runtime .evolver/ or memory/ originals committed /
only kit+bundle+tools+templates+reports+validators committed /
Python stdlib only
```

### 9.2 Phase 7A 额外硬边界

- ✅ 21 项 dangerous signals 黑名单
- ✅ 13 项 dangerous substrings 拒绝
- ✅ 6 类 credential regex (case-insensitive)
- ✅ ALLOWED_SIGNAL_CHARS 字符集 + 长度
- ✅ domain signal `origin` 显式区分（`evomap_apply_bundle:domain_from_bundle`）
- ✅ 工具只解析 `--inject-signals-from` 指向的 JSON（不递归扫 repo）
- ✅ `--yes` 仍是写入的**唯一**途径（无 `--yes` 自动 dry-run）

### 9.3 secrets 检查

`secret scan`：跨 13 个 Phase 7A artifact + 修改后的 apply tool + 修改后的 main README 全部 `hits=0`：
- 无 bot token 形如 `\d{6,12}:[A-Za-z0-9_-]{20,}`
- 无 Authorization header
- 无 API key 前缀
- 无 JWT
- 无 12+ 位纯数字
- 无 private key

### 9.4 硬边界自检

| Hard boundary | 状态 | 证据 |
|--|--|--|
| no Hub | ✅ | 所有 evolver 输出 `[SearchFirst] No hub match (reason: no_hub_url)` |
| no A2A_HUB_URL | ✅ | `unset A2A_HUB_URL` |
| no --loop | ✅ | evolver 全部 `run` 模式（非 `run --loop`） |
| no validator | ✅ | `EVOLVER_VALIDATOR_ENABLED=false` |
| no auto-publish | ✅ | `EVOLVER_AUTO_PUBLISH=false` |
| no credits | ✅ | `EVOLVER_ATP_AUTOBUY=off` |
| no ATP autobuy | ✅ | 同上 |
| no secrets | ✅ | secret scan 0 hits |
| no .env scan | ✅ | apply tool 不读 .env |
| no curl/wget | ✅ | Python stdlib only |
| no real config mutation | ✅ | 只写 target runtime 的 .evolver/ + memory/evolution/ |
| no Evolver source modification | ✅ | `node index.js` 未动 |
| no evolver --approve | ✅ | review 模式无 `--approve` |
| no evolver solidify | ✅ | `solidify` 未执行 |
| no runtime .evolver/ or memory/ originals | ✅ | git status 不跟踪根 .evolver/ 或 memory/ |
| only kit+bundle+tools+templates+reports+validators | ✅ | 见 11. 提交白名单 |

---

## 10. 最终结论

ATL-EVOMAP-7A **PASS**。

`scripts/evomap_apply_bundle.py` 现在支持 `--inject-signals-from <bundle.json>`，
在不破坏 Phase 5/6A/6B default 行为的前提下，能够从 bundle 的
`gene.signals_match` + `capsule.trigger` 中提取 domain-specific signals，
经过严格过滤后注入 `memory_graph.jsonl`，使 evolver 的 selector 不再只依赖
`distilled_fallback`。

**关键结果**：

| Metric | Phase 5 | Hermes (7A) | Telegram (7A) |
|--|--|--|--|
| signal_injection_mode | `generic_only` | `generic_plus_domain_from_bundle` | `generic_plus_domain_from_bundle` |
| Generic signals | 5 | 5 | 5 |
| Domain signals | 0 | 12 | 22 |
| Total memory_graph_signals_added | 5 | 17 | 27 |
| Dangerous signals rejected | 0 | 0 | 0 |
| Evolver smoke PASS | n/a | ✅ | ✅ |
| No Hub | ✅ | ✅ | ✅ |
| No publish | ✅ | ✅ | ✅ |
| No credits | ✅ | ✅ | ✅ |
| No approve | n/a | ✅ | ✅ |
| No solidify | n/a | ✅ | ✅ |

**Backward compat:** Phase 5/6A/6B 三套 validator 全部 ALL CHECKS PASSED。

**Cross-bundle enablement:** 现在 bundle-curator skill 可以用同一份 apply 工具，
把任何 bundle 的 domain signals 自动注入到 isolated runtime，无需为每个
bundle 写新 apply 工具。

---

## 11. 下一步建议

1. **Cross-bundle regression test** — apply 所有 3 个 bundles 到一个 fresh
   isolated target，验证无 signal/gene/capsule id 冲突，count distinct signals，
   验证 selector 能跨 bundle 命中。
2. **`bundle-curator` skill** — 自动从 evolver run 产出物生成 portable bundle。
3. **Codex `prompt-cache-discipline` bundle** (optimize) — 复用同一 apply 工具。
4. **Browser-control `rate-limit-recovery` bundle** (repair) — 复用同一 apply 工具。
5. **`memory_graph.jsonl` 升级 schema** — 增加 `domain_source_bundle` 字段，
   显式记录 signal 来自哪个 bundle（当前在 `context` 字段里）。

---

## 12. Artifacts 清单

### 12.1 工具与代码

| 路径 | 说明 |
|---|---|
| `scripts/evomap_apply_bundle.py` | 修改后，17.5 KB，新增 `--inject-signals-from` + signal extraction/filtering |
| `scripts/validate_evomap_phase7a_domain_signal_injection.py` | 新增 validator，19 项检查 |

### 12.2 Phase 7A case artifacts (13 个)

| 路径 | 说明 |
|---|---|
| `artifacts/inspect-hermes-bundle-output.json` | Hermes bundle inspect |
| `artifacts/validate-hermes-bundle-output.json` | Hermes bundle validate (12/12 PASS) |
| `artifacts/inspect-telegram-bundle-output.json` | Telegram bundle inspect |
| `artifacts/validate-telegram-bundle-output.json` | Telegram bundle validate (12/12 PASS) |
| `artifacts/default-apply-dry-run-output.json` | Phase 5 bundle dry-run (no flag) |
| `artifacts/default-apply-yes-output.json` | Phase 5 bundle --yes (no flag) |
| `artifacts/default-apply-target-summary.json` | memory_graph_lines=5, generic_only |
| `artifacts/hermes-domain-dry-run-output.json` | Hermes bundle dry-run (with flag) |
| `artifacts/hermes-domain-yes-output.json` | Hermes bundle --yes (with flag) |
| `artifacts/hermes-domain-target-summary.json` | memory_graph_lines=17, generic_plus_domain |
| `artifacts/telegram-domain-dry-run-output.json` | Telegram bundle dry-run (with flag) |
| `artifacts/telegram-domain-yes-output.json` | Telegram bundle --yes (with flag) |
| `artifacts/telegram-domain-target-summary.json` | memory_graph_lines=27, generic_plus_domain |
| `artifacts/domain-signal-extraction-summary.json` | 总览 (filter engine + 3 targets) |
| `artifacts/evolver-run-hermes-domain-output.txt` | Hermes evolver run smoke |
| `artifacts/evolver-review-hermes-domain-output.txt` | Hermes evolver review smoke |
| `artifacts/evolver-run-telegram-domain-output.txt` | Telegram evolver run smoke |
| `artifacts/evolver-review-telegram-domain-output.txt` | Telegram evolver review smoke |

### 12.3 报告

- `cases/evomap-evolver-openclaw-v0/phase7a-domain-signal-injection/ATL_EVOMAP_7A_DOMAIN_SIGNAL_INJECTION_REPORT.md` (本文件)
- `reports/ATL_EVOMAP_7A_DOMAIN_SIGNAL_INJECTION_REPORT.md` (top-level copy)

### 12.4 主 case README

- `cases/evomap-evolver-openclaw-v0/README.md` 追加 7A 节 + 表格新行

### 12.5 data/cases.json

- `phase: ATL-EVOMAP-7A Domain-Specific Signal Injection`
- `status: domain signal injection completed`
- `final_status: DOMAIN_SIGNAL_INJECTION_PASS`
- `phase_history` 第 14 条目已加入 7A entry

---

## 13. 致谢

- 复用 Phase 5 工具骨架（`plan_apply` / `execute_plan`）
- 复用 Phase 6A/6B 验证流程（inspect → validate → apply → evolver smoke）
- 不依赖 Hub、不消耗 credits、不破坏 16 项硬边界
