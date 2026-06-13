# ATL-5C — First Castform Run Failed at Step 0 — Report

**Date**: 2026-06-13
**Phase**: ATL-5C
**Status**: **FAILED_STEP_0_NO_ROLLOUTS**
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Current baseline commit**: `dd465c5` (ATL-5B: Record Castform cloud smoke launch result)

## 阶段结论

`FAILED_STEP_0_NO_ROLLOUTS` — ATL-5B 用户手动运行的 cloud smoke run 实际启动了 Castform 上的训练 run（`run_id=c83f971d-2b2c-42b8-9774-ca64938c1286`），但在第一步 rollout 之前就失败了。documented `/experiments/<run_id>` 路径在 live UI 中返回 Not Found；实际可访问的 URL 是 `/train/<run_id>?tab=train`。UI 显示 status = `failed`, step = `0`, train/eval/rollouts 全部为空；compare tab 的 external gpt-5.4 batch eval 已完成（reward 10.000, $0.01/request），但我们自己的模型没有产生任何 rollout。failure reason 在 UI 中不可见。Agent 在本阶段只记录用户观察结果并创建 read-only SDK status probe；未调用 API、未访问 UI、未重复 launch、未伪造任何指标。

## ATL-5B launch result summary

| Item | Value |
|------|-------|
| `local_validate_env_result` | `VALIDATE_ENV_LOCAL_PASS` |
| `upload_succeeded` | `true` |
| `launch_succeeded` | `true` |
| `status` | `PASS_CLOUD_SMOKE_LAUNCHED` |
| `run_id` | `c83f971d-2b2c-42b8-9774-ca64938c1286` |
| `training_started` | `true` |
| `api_key_recorded` | `false` |

(`validate_atl5b_second_upload_retry_result.py` PASS on the on-disk result JSON; ATL-5 result file is intact; retry result file is in `atl5b_second_upload_launch_retry_result.json`.)

## Run identity (user-observed via Castform UI)

| Field | Value |
|-------|-------|
| `run_id` | `c83f971d-2b2c-42b8-9774-ca64938c1286` |
| documented experiment URL | `https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286` |
| actual UI URL | `https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train` |
| display name | `simple-28de6dd2` |
| status | `failed` |
| step | `0` |
| started | about 39–41 min ago |

## User-observed status (Castform UI, copy verbatim from observation)

- **status**: `failed`
- **step**: `0`
- **train tab**: no train data available
- **train rollout deepdive**: no rollouts recorded yet
- **eval tab**: no eval data available
- **eval rollout deepdive**: no rollouts recorded yet
- **compare tab**: external gpt-5.4 batch eval **completed**
- **compare tab**: your model has not generated rollouts yet
- **compare reward for gpt-5.4**: 10.000
- **compare inference cost shown**: about $0.01/request

## Config observations (visible in config tab)

- model = `Qwen/Qwen3.5-4B`
- `env_cls_path` / `env_metadata_path` / `train_dataset_path` / `eval_dataset_path` — visible (set by upload step)
- LoRA save/load paths — visible
- `lr` = 0.00001
- `max_turns` = 1
- `n_samples_per_prompt` = 2
- `n_samples_per_eval_prompt` = 2
- `num_epoch` = 1
- rollout / eval max response length = 512
- environment code — visible
- `dataset_preprocess` / `load_dataset` / `list_tools` / `run_tool` / `compute_reward` — visible

## Settings observations (visible in settings tab)

- download checkpoint button — visible
- Hugging Face connect button — visible
- external batch eval section — visible
- delete training run button — visible
- explicit worker logs in screenshots — **none visible**

## Train / eval / compare observations

- **train data available**: NO
- **train rollouts recorded**: NO
- **eval data available**: NO
- **eval rollouts recorded**: NO
- **compare external gpt-5.4**: completed (reward 10.000, $0.01/request)
- **your model generated rollouts**: NO

## Interpretation

- ATL-5B launch succeeded and the run exists in the Castform training runs list.
- The documented `/experiments/<run_id>` path returned **Not Found**, but `/train/<run_id>?tab=train` works — the documented path is a stale reference; the live URL is the `/train/<run_id>` form with `?tab=train` selecting the train tab.
- The run **failed before the first model rollout** (step 0, no rollouts recorded on either train or eval side).
- The external GPT-5.4 batch eval *did* complete and produced a reward score (10.000) plus per-request cost ($0.01/request), but our own model never reached the rollout stage.
- We do not have a UI-visible traceback, worker log, or backend error message — only the high-level `failed` status at step 0.
- Exact root cause: **unknown**.
- **Current monitoring status**: `FAILED_STEP_0_NO_ROLLOUTS`.

## Validation results

| Script | Result |
|--------|--------|
| `validate_jsonl.py` | PASS |
| `validate_site.py` | PASS |
| `check_secrets.py` | PASS |
| `validate_castform_local_scaffold.py` | PASS |
| `validate_atl3c_sdk_mapping.py` | PASS |
| `validate_atl4a_preflight_scaffold.py` | PASS |
| `validate_atl4b_cloud_smoke_config.py` | PASS |
| `validate_atl4c_guarded_preflight.py` | PASS |
| `validate_atl5_cloud_smoke_result.py` | PASS (ATL-5 placeholder JSON still valid) |
| `validate_atl5a_launch_args_fix.py` | PASS (ATL-5A baseline still compliant) |
| `validate_atl5b_second_upload_retry_result.py` | PASS (ATL-5B on-disk result JSON still compliant) |
| `validate_atl5c_failed_step0_record.py` | **PASS** (record md + template md + probe script exist; record md contains run_id + actual UI URL + "failed" + "step 0" + "no rollouts" + `FAILED_STEP_0_NO_ROLLOUTS`; no forbidden secret literal in any of the three files; probe script compiles + contains `READ_ONLY_PREFIXES` / `DESTRUCTIVE_KEYWORDS` / `NO_READ_ONLY_STATUS_METHOD_FOUND` / `_scrub` symbols) |

Extra `<PATTERN_REDACTED>` key-prefix scan (full tree, using the pattern in `scripts/validate_atl5c_failed_step0_record.py` `SECRET_LITERALS`):

```
$ grep -R --line-number <PATTERN_REDACTED> README.md cases data docs reports scripts && echo "FAIL" || echo "PASS: no <PATTERN_REDACTED> prefix found"
PASS: no <PATTERN_REDACTED> prefix found
```

## git status (before commit)

```
M  README.md
M  cases/castform-hermes-phase-closer-v0/index.html
A  cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c-first-run-failed-step0.md
A  cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c-failure-diagnostics-template.md
A  cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c_readonly_status_probe.py
M  data/cases.json
A  reports/ATL5C_FIRST_RUN_FAILED_STEP0_REPORT.md
A  scripts/validate_atl5c_failed_step0_record.py
```

(8 file changes; 5 new + 3 modified; 0 deletions.)

## Commit hash

To be recorded after `git commit` succeeds (see git push result below).

## Whether pushed

Push runs after commit; result captured in Telegram wrap-up.

## 明确说明（agent 硬边界）

- **agent 未调用 Castform API**：本阶段无任何到 Castform 的网络请求。
- **agent 未访问 Castform UI**：本阶段无任何到 `app.castform.com` 的 UI 抓取；所有 UI 观察均由用户在本地浏览器完成并报告。
- **agent 未上传数据**：未触发 `upload_training_run`；未触碰任何数据上传路径。
- **agent 未训练**：未触发 `launch_training_run`；training run 由 ATL-5B 阶段用户手动运行启动。
- **agent 未重复 launch**：未运行 `atl5b_second_upload_launch_retry.py`；也未运行 read-only probe（probe 留给用户）。
- **API key 未记录**：result JSON `api_key_recorded=false`（ATL-5B）；本阶段无 `.env` 创建；无 API key 任何形式落盘。
- **API key 前缀或片段未记录**：retry 脚本 gate 日志已硬化（ATL-5B-RESULT），4 字符前缀和片段都不会输出；本阶段也未触发 retry 脚本运行；用户终端中出现的 key 4 字符前缀未引用到任何文件 / 报告 / commit / Telegram 消息。`grep -R <PATTERN_REDACTED>`（pattern 见 `SECRET_LITERALS`）在 README / cases / data / docs / reports / scripts 全树 0 命中。
- **未提交 .env**：`.gitignore` 已包含 `.env*`；本阶段未创建任何 `.env` 文件。
- **未提交 .venv**：`.venv-castform-local/` 仍在 `.gitignore` 中；`validate_atl3c_sdk_mapping.py` 确认 `.venv-castform-local NOT tracked`。
- **未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图**：报告中只引用 `run_id`（UUID）、公开 URL（documented experiment URL 与 actual UI URL）、不引用 cookie / auth header / 信用卡 / 邮箱 / 截图。

## 下一步

**用户本地 WSL 运行 read-only status probe：**

```bash
export CASTFORM_API_KEY=<YOUR_CASTFORM_API_KEY>   # runtime only; do NOT write to .env
cd /mnt/d/AI/ai-tool-test-lab
.venv-castform-local/bin/python \
  cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c_readonly_status_probe.py \
  --run-id c83f971d-2b2c-42b8-9774-ca64938c1286
```

Probe 输出分支：

- **若 probe 打印 backend error / traceback**（任一 candidate method 返回带 traceback 的 response）→ 进入 **ATL-5D — failure root cause record**：把 probe 输出贴到 `cases/.../monitoring/atl5c-failure-diagnostics-template.md`，更新页面 / cases.json / README / 报告。
- **若 probe 打印 `NO_READ_ONLY_STATUS_METHOD_FOUND`**（SDK 中无 `get_*` / `list_*` / `status_*` / `describe_*` / `fetch_*` 等 read-only candidate）→ 进入 **ATL-5E — support-ready failure bundle**：把 UI 截图 + 配置 + 已知失败状态整理为可发送给 Castform 支持的 bundle。

**两步都假定 agent 不调用 Castform API**（probe 是用户本地运行的；任何后续 ATL-5D / ATL-5E 仍遵守同一硬边界）。

## 修改文件清单（本次 commit）

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c-first-run-failed-step0.md`（新增）
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c-failure-diagnostics-template.md`（新增）
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c_readonly_status_probe.py`（新增）
- `cases/castform-hermes-phase-closer-v0/index.html`（修改：测试摘要 + 新 ATL-5C 模块 + timeline + footer）
- `data/cases.json`（修改：phase = `ATL-5C first run failed before rollouts`，status = `cloud smoke launched; failed at step 0 before rollouts`，summary 追加 ATL-5C 段）
- `README.md`（修改：顶部状态 + 新增 ATL-5C 收口 / 交付 / 硬边界 / 下一步段）
- `reports/ATL5C_FIRST_RUN_FAILED_STEP0_REPORT.md`（新增）
- `scripts/validate_atl5c_failed_step0_record.py`（新增）

## 风险评估

- **本阶段 agent 无新风险**：仅记录用户观察 + 创建 probe scaffold + 更新静态资源；未调用 API、未访问 UI、未触发任何 Castform 后端调用。
- **遗留风险**（继承自 ATL-5B / ATL-4A-CREDIT-FILL）：billing / auto-charge / cost visibility 仍多项 UNKNOWN；本次 retry 之所以能 launch 成功很可能与 `Free credit $50 visible: YES` 仍在生效有关；本次 training run 实际消耗 credit 数量未在 UI 中可见。
- **failure reason 缺失风险**：UI 中无 traceback / worker log；如果 read-only probe 也无法访问 backend error stream，可能需要 Castform 支持介入（ATL-5E bundle）。
- **probe 自身风险**：probe 在用户本地运行，不会泄露 API key（`CASTFORM_API_KEY present: True|False` 报告；所有 secret-shaped pattern 在 stdout 前 `_scrub` 替换为 `<SECRET_REDACTED>`）；不调用任何 destructive verb（`get_*` / `list_*` / `status_*` / `describe_*` / `fetch_*` 之外的动词被 `DESTRUCTIVE_KEYWORDS` 拒绝）；不调用 `upload_training_run` / `launch_training_run` / `delete_*` / `cancel_*` / `update_*` / `create_*` / `download_*`。
