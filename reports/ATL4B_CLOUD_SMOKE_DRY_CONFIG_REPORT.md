# ATL-4B-CONFIG — Castform Cloud Smoke Run Dry Configuration Report

**Date**: 2026-06-13
**Phase**: ATL-4B-CONFIG
**Status**: **PASS_WITH_LAUNCH_BLOCKED**
**Commit**: 2e9a5c8
**Baseline**: ff22241 (ATL-4A) · 5f06de9 (ATL-3C)
**Current baseline commit**: `ff22241` (ATL-4A)
**Reference baseline**: ATL-3C commit `5f06de9`
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Report path**: `reports/ATL4B_CLOUD_SMOKE_DRY_CONFIG_REPORT.md`

---

## 1. 阶段结论

| 维度 | 结论 |
| --- | --- |
| 阶段结论 | **PASS_WITH_LAUNCH_BLOCKED** |
| Cloud launch allowed | **false**（硬性锁死） |
| Current readiness | `BLOCKED_BY_UNCLEAR_CHARGES`（硬性锁死） |
| API key created | **NO** |
| API call | **none** |
| Upload | **none** |
| Training | **none** |
| 真实 CASTFORM_API_KEY 注入 | **NO**（仅占位符 `<CASTFORM_API_KEY>` 出现在文档中） |
| `.env` 文件 | **未创建** |
| 真实 secret 泄露 | **0**（`check_secrets.py` PASS） |

**判断依据**：所有验证脚本 PASS；`cloud_launch_guard.py` 在标准环境与 `CASTFORM_API_KEY` 已设环境下均拒绝 launch 并退出 1；preview 子集生成 8/2 行；`cloud_smoke_config.json` 字段全部就位；所有硬性边界（17 条）严格遵守；用户尚未确认 credit / billing / auto-charge / cost visibility。

---

## 2. 用户人工观察摘要（Castform Web App）

用户在 ATL-4A 阶段已人工进入 Castform Web App，本阶段继承以下观察：

- 登录状态：可登录
- Workspace / dashboard：可见
- New training run 页面：可访问
- Example setup flows（Setup Flows）可访问：
  - `starter task`：可见
  - `rag agent`：可见
  - `agent traces`：可见
- Training template pages 可见：
  - `rag agent`
  - `agent traces`
  - （Build your own / SDK 通过 export to VSCode 路径接入）
- API key 页面：可访问；当前状态 **No API keys yet**
- **Export to VSCode** 按钮：可见（PASS）
- base model `Qwen/Qwen3.5-4B` 在 setup pages 中：可见
- Billing / credit / auto-charge / cost estimate：**NOT CHECKED**（未在 UI 中确认）
- Data deletion / run cancellation / model ownership：**NOT CHECKED**（未在 UI 中确认）

结论：账号侧 UI 可见性 OK；账户侧可访问性 OK；**资金侧（credit / billing / cost visibility）未确认** → 维持 BLOCKED。

---

## 3. 选型结论：Build your own / SDK path

| 路径 | 选 | 理由摘要 |
| --- | --- | --- |
| Build your own / SDK | **YES** | 与 prompt + ground_truth JSONL（ATL-2）/ 本地 env candidate（ATL-3C）/ rule-based reward 匹配度最高；暴露最小可用平台链路；不引入模板特定假设 |
| RAG Agent | NO | 模板面向文档 corpus + 检索 + 引用；当前没有 production 文档 corpus；会引入检索侧算力，浪费 smoke 预算 |
| Agent Traces | NO | 模板面向生产 agent traces provider；本地数据是合成 prompt + ground_truth，不是真实 agent traffic；smoke run 误用会混淆"平台能 ingest traces"和"训练是 sane 的"两种信号 |

**详细论证**：见 `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/README.md`。

---

## 4. cloud smoke config（最终配置）

来源：`cases/castform-hermes-phase-closer-v0/cloud-smoke-run/cloud_smoke_config.json`

| 字段 | 值 |
| --- | --- |
| `phase` | `ATL-4B-CONFIG` |
| `run_name` | `hermes-phase-closer-smoke` |
| `template_path` | `build_your_own_sdk` |
| `base_model` | `Qwen/Qwen3.5-4B` |
| `train_sample_count` | `8` |
| `eval_sample_count` | `2` |
| `dataset_source` | `../sample-train.jsonl` + `../sample-eval.jsonl`（ATL-2 redacted） |
| `environment_source` | `../local-validate-env/environment_validate_candidate.py`（ATL-3C） |
| `reward_source` | `../local-validate-env/reward.py` |
| `tools` | `[]` |
| `external_network_tools` | `[]` |
| `max_turns` | `1` |
| `objective` | prove upload + launch + monitoring can start, not train a useful model |
| `cloud_launch_allowed` | **`false`**（硬性锁死） |
| `current_readiness` | **`BLOCKED_BY_UNCLEAR_CHARGES`**（硬性锁死） |
| `requires_user_credit_billing_confirmation` | `true` |
| `requires_explicit_user_api_key_authorization` | `true` |

---

## 5. 生成文件清单

新增 / 修改的全部文件路径（相对项目根 `/mnt/d/AI/ai-tool-test-lab`）：

```
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/cloud_smoke_config.json     [new]
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/README.md                   [new]
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/API_KEY_HANDLING.md         [new]
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/COST_GUARD.md               [new]
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/prepare_cloud_smoke_subset.py [new]
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/cloud_launch_guard.py      [new]
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/smoke-train.preview.jsonl  [new, 8 rows]
cases/castform-hermes-phase-closer-v0/cloud-smoke-run/smoke-eval.preview.jsonl   [new, 2 rows]
scripts/validate_atl4b_cloud_smoke_config.py                                      [new]
cases/castform-hermes-phase-closer-v0/index.html                                  [modified: +ATL-4B module, status line, timeline, footer]
cases/castform-hermes-phase-closer-v0/account-billing-preflight.md                [modified: ATL-4A→ATL-4B-CONFIG gated; +ATL-4A observation summary; +ATL-4B config summary]
docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md                                        [modified: header + +ATL-4B-CONFIG 衔接 section]
data/cases.json                                                                   [modified: phase → ATL-4B-CONFIG, status → cloud smoke config ready; launch blocked by unclear charges]
README.md                                                                         [modified: 当前状态 block 整体更新]
reports/ATL4B_CLOUD_SMOKE_DRY_CONFIG_REPORT.md                                    [new, this file]
```

---

## 6. 关键脚本执行结果

### 6.1 `prepare_cloud_smoke_subset.py`

```
[INFO] ATL-4B-CONFIG prepare_cloud_smoke_subset.py
[INFO] dry subset extraction only — no API, no upload, no training
[OK] wrote 8 rows -> cases/castform-hermes-phase-closer-v0/cloud-smoke-run/smoke-train.preview.jsonl
[OK] wrote 2 rows -> cases/castform-hermes-phase-closer-v0/cloud-smoke-run/smoke-eval.preview.jsonl
[OK] preview subset prepared; files are .preview.jsonl (not for upload)
```

- 行为：仅本地 std-lib 读源 JSONL，按 N 取前 N 行，写到 `*.preview.jsonl`。
- 边界：不调用 API · 不上传 · 不训练 · 不导入 `upload_training_run` / `launch_training_run` / `TrainerClient`。
- 验证：validator 同时通过存在性、行数、清洁性三道检查。

### 6.2 `cloud_launch_guard.py`

```
[INFO] ATL-4B-CONFIG cloud_launch_guard.py
ATL-4B-CONFIG dry configuration only
cloud_launch_allowed=false
BLOCKED_BY_UNCLEAR_CHARGES
no API call
no upload
no training
[GUARD] launch refused (ATL-4B-CONFIG default)
```

- 行为：默认 `ALLOWED = False`，打印六行 blocked banner，退出 1。
- 边界：脚本中保留 `FORBIDDEN_CALLABLES = ("upload_training_run", "launch_training_run", "TrainerClient")` 字符串（用于反-自检，不调用）；不导入 `castform` 包；不调用任何 Castform API。
- 防护深度：即使用户手动 `export CASTFORM_API_KEY=***`，脚本依然拒绝 launch 并打印"key present, guard still refuses"。

### 6.3 `validate_atl4b_cloud_smoke_config.py`

```
RESULT: PASS
```

- 7 类检查全部通过：目录、文件存在、JSON 合法且字段齐全、`cloud_launch_allowed=false`、`current_readiness=BLOCKED_BY_UNCLEAR_CHARGES`、preview 行数、清洁性（无 secret-shaped 字符串、无 `upload_training_run(` 等可执行调用）、guard 实际拒绝行为。

### 6.4 全套验证脚本

| 脚本 | 结果 |
| --- | --- |
| `validate_jsonl.py` | PASS（42 train + 7 eval） |
| `validate_site.py` | PASS |
| `check_secrets.py` | PASS |
| `validate_castform_local_scaffold.py` | PASS |
| `validate_atl3c_sdk_mapping.py` | PASS |
| `validate_atl4a_preflight_scaffold.py` | PASS |
| `validate_atl4b_cloud_smoke_config.py` | **PASS**（new） |

---

## 7. git 状态

执行 commit 前 `git status --short`：

```
 M README.md
 M cases/castform-hermes-phase-closer-v0/account-billing-preflight.md
 M cases/castform-hermes-phase-closer-v0/index.html
 M data/cases.json
 M docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md
?? cases/castform-hermes-phase-closer-v0/cloud-smoke-run/
?? scripts/validate_atl4b_cloud_smoke_config.py
```

commit 计划：`ATL-4B: Prepare Castform cloud smoke dry configuration`

commit hash：见步骤 20-22 实际结果（在本报告 §10 中记录）。

---

## 8. 严格声明（hard no-go list）

- [x] **未调用 Castform API**
- [x] **未上传数据**
- [x] **未训练模型**
- [x] **未创建 API key**
- [x] **未使用真实 CASTFORM_API_KEY**
- [x] **未创建 .env**
- [x] **未读取 / 提交 .env、token、API key、Telegram bot token、私有 cookie**
- [x] **未记录用户邮箱**
- [x] **未记录信用卡信息**
- [x] **未提交截图**
- [x] **未运行 upload_training_run**
- [x] **未运行 launch_training_run**
- [x] **未运行 TrainerClient**
- [x] **未伪造 cloud smoke run 成功**
- [x] **已创建** dry-run 配置文件、文档、脚本占位、报告（这是允许项）

---

## 9. 已知限制

1. **billing / credit 未确认** — Castform Web App 中 credit / billing / auto-charge / cost visibility 仍未在 UI 中确认；这是 launch 被 block 的核心原因。
2. **cloud smoke run 未启动** — 故意未启动；`cloud_launch_guard.py` 主动拒绝。
3. **preview subset 不代表最终训练数据质量** — `smoke-train.preview.jsonl`（8 行）/ `smoke-eval.preview.jsonl`（2 行）只是为了在 `cloud_smoke_config.json` 中固定一个具体数字，使配置可被复现，并不代表 8/2 是最优训练规模。
4. **ATL-2 合成样本比例 71%** — `cases/castform-hermes-phase-closer-v0/dataset-notes.md` 已记录；smoke run 应理解为"平台链路通断验证"，不是"模型质量验证"。
5. **base model 候选** `Qwen/Qwen3.5-4B` 是用户在 Castform setup pages 中可见的候选；用户在 ATL-4A-CREDIT / ATL-4C 阶段可调整。
6. **没有跑过真实网络** — 本阶段无任何网络出口；guard 在 `CASTFORM_API_KEY` 已设环境下也拒绝 launch，但真实网络条件下 guard 之外的防护层未在本阶段被验证（这是 ATL-4C / ATL-4D 的工作）。

---

## 10. commit / push 记录

> 本节在 commit 与 push 之后由本报告生成脚本回填。

（见 §10.x commit / push results，由执行 commit / push 的步骤填入）

---

## 11. 下一步建议

**首选**：**ATL-4A-CREDIT** — verify credit / billing / auto-charge / cost visibility
- 用户在 Castform Web App 中逐项确认：
  - free credit 余额
  - billing method（绑卡 / 不绑卡）
  - auto-charge 开关
  - 启动前 cost estimate 可见性
  - run cancellation / data deletion / model ownership 可控性
- 把 `Ready status` 从 `BLOCKED_BY_UNCLEAR_CHARGES` 改为 `READY_FOR_CLOUD_SMOKE_RUN`（在 `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md`）。

**次选**：用户显式声明 `READY_FOR_CLOUD_SMOKE_RUN` → 进入 **ATL-4C** guarded upload preflight。
- ATL-4C 阶段会：检查 `cloud_smoke_config.json` 字段仍为合法状态；检查 `cloud_launch_guard.py` 仍为拒绝状态；准备上传文件的最终形态（去掉 `.preview` 后缀）；做"dry upload" rehearsal（不发真实 HTTP）。
- ATL-4C 完成后才有 **ATL-4D** guarded launch preflight，最后才是 **ATL-4E** real smoke run。

**禁止**：
- 在没有 `READY_FOR_CLOUD_SMOKE_RUN` 的情况下人工改 `cloud_launch_guard.py` 的 `ALLOWED = True`。
- 在没有逐项 §9 限制 1 完成的情况下 commit 把 `cloud_launch_allowed` 改为 `true` 的版本。
- 在没有 `READY_FOR_CLOUD_SMOKE_RUN` 的情况下手动 `export CASTFORM_API_KEY=***` 并运行任何 launch 脚本。

---

## 12. 关联文档

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/README.md`
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/cloud_smoke_config.json`
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/API_KEY_HANDLING.md`
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/COST_GUARD.md`
- `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md`（更新）
- `docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md`（更新）
- `cases/castform-hermes-phase-closer-v0/index.html`（更新）
- `data/cases.json`（更新）
- `README.md`（更新）
- `scripts/validate_atl4b_cloud_smoke_config.py`（新增）

---

**报告结束**。
