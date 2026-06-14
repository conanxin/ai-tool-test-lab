# ATL-RESUME-2B — Record Castform Vendor-Fix Retest Launch Result

## 阶段结论

**PASS_CLOUD_SMOKE_LAUNCHED_MONITORING_REQUIRED**

## 当前基线

- baseline commit: 07dafbe (ATL-RESUME-2A: Prepare Castform vendor fix retest)
- next commit: this report's commit

## 阶段目标

在用户本地 WSL shell 手动执行 `atl_resume2_vendor_fix_retest.py` 后，transcribe 真实结果到 case page / cases.json / README / 报告。本阶段 agent **不调用 Castform API**、**不访问 Castform UI**、**不上传数据**、**不启动训练**、**不重复运行 retest**、**不读取 API key 任何片段**、**不伪造 sample count 或 monitoring 状态**。仅做 on-disk verify（pitfall #22 trust-but-verify）+ transcribe。

## Vendor Fix Context

- vendor: Girish (Castform founder)
- vendor-confirmed root cause: raw data dict caused incompatibilities with the Castform trainer
- fix status: received (Castform side)
- credit update: $100 extra credits added to the account
- case status: `VENDOR_FIX_RECEIVED_RETEST_PENDING` (preserved as audit trail)

## Local Validate Env Result (from on-disk result JSON)

```
VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)
```

## Upload Result (from on-disk result JSON)

- upload_attempted: `true`
- upload_succeeded: `true`
- uploaded_payload_present: `true` (env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path saved)
- uploaded_payload content (clean Castform blob paths only, no signed URLs):
  - `env_cls_path`: `envs/hermes-phase-closer-vendor-fix-retest/<hash>/env-cls.pkl`
  - `env_metadata_path`: `envs/hermes-phase-closer-vendor-fix-retest/<hash>/env-metadata.json`
  - `train_dataset_path`: `datasets/hermes-phase-closer-vendor-fix-retest/<hash>/train.jsonl`
  - `eval_dataset_path`: `datasets/hermes-phase-closer-vendor-fix-retest/<hash>/eval.jsonl`

## Launch Result (from on-disk result JSON)

- launch_attempted: `true`
- launch_succeeded: `true`
- dataset_uploaded: `true`
- training_started: `true`
- error_category: `null`
- result status: `PASS_CLOUD_SMOKE_LAUNCHED`

## Run Identity (from on-disk result JSON)

| Field | Value |
|-------|-------|
| run_id | `e4abb2dc-cc68-4b52-8ba5-2195c3f12d1d` |
| experiment_url | `https://app.castform.com/experiments/e4abb2dc-cc68-4b52-8ba5-2195c3f12d1d` |
| expected actual UI URL | `https://app.castform.com/train/e4abb2dc-cc68-4b52-8ba5-2195c3f12d1d?tab=train` |
| actual_ui_url | `null` (user-side UI discovery pending; backfill in ATL-RESUME-2C) |
| base_model | `Qwen/Qwen3.5-4B` |
| run_name | `hermes-phase-closer-vendor-fix-retest` |

## Sample Count (from on-disk result JSON — AUTHORITATIVE)

| Field | Value |
|-------|-------|
| train_samples | `16` |
| eval_samples | `4` |

> **Note on user's "5 行训练数据" comment:** the "5" was local validate_env's 5-row preview slice used for the local smoke check, **not** the cloud upload. The cloud upload was the full 16 train / 4 eval starter-style preview subset. The on-disk result JSON is the authoritative source.

## Hard Boundary Compliance

| Hard boundary | Status |
|---------------|--------|
| agent did NOT call Castform API | YES (0 API calls) |
| agent did NOT access Castform UI | YES |
| agent did NOT upload data | YES |
| agent did NOT start training | YES |
| agent did NOT re-run retest script | YES |
| agent did NOT read API key in any form | YES |
| agent did NOT record API key / email / screenshot / cookie / Authorization header / credit card | YES |
| agent did NOT create .env | YES |
| agent did NOT commit .venv | YES |
| agent did NOT fake sample count (16/4 from JSON, not 5) | YES |
| agent did NOT fake monitoring status (`MONITORING_REQUIRED`) | YES |
| agent did NOT rewrite historical facts (Run 1 + Run 2 still step 0 failed) | YES |
| agent did NOT reference old run_ids as new retest input | YES |

## Validation Results

| Script | Result |
|--------|--------|
| `validate_atl_resume2_vendor_fix_retest.py` | PASS (on-disk result JSON present, all invariants verified, 16 secret patterns + 1 forbidden literal scan clean) |
| `check_secrets.py` | PASS |
| `validate_jsonl.py` | PASS |
| `validate_site.py` | PASS (canonical_example + workflow_reference preserved) |
| `validate_vendor_fix_response.py` | PASS (ATL-RESUME-1 invariants preserved — historical `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` still in CASE_CLOSEOUT.md, both old run_ids preserved) |
| `validate_castform_local_scaffold.py` | PASS |
| `validate_atl3c_sdk_mapping.py` | PASS |
| `validate_atl4a_preflight_scaffold.py` | PASS |
| `validate_atl4b_cloud_smoke_config.py` | PASS |
| `validate_atl4c_guarded_preflight.py` | PASS |
| `validate_atl5_cloud_smoke_result.py` | PASS |
| `validate_atl5a_launch_args_fix.py` | PASS |
| `validate_atl5b_second_upload_retry_result.py` | PASS |
| `validate_atl6_starter_style_redeploy.py` | PASS |
| `validate_atl6c_support_request.py` | PASS |
| `validate_case_closeout.py` | FAIL (expected — phase 已从 `CASE-CLOSEOUT` 推进到 `ATL-RESUME-2B vendor-fix retest launched`，验证器对 phase/status 的断言恰恰验证状态机正确转移，与 ATL-RESUME-1 / ATL-RESUME-2A 阶段同模式) |

Repo-wide key-prefix grep (literal pattern, exact command per user spec):

`# command pattern: forbidden key prefix (literal key-shape pattern, deliberately not echoed to avoid self-match; the spec-mandated command was executed by agent against repo before commit)`

Execution result: zero hits. No real key prefix leaked across repo.

## git status

```
M  README.md
M  cases/castform-hermes-phase-closer-v0/index.html
M  data/cases.json
A  cases/castform-hermes-phase-closer-v0/vendor-fix-retest/atl_resume2_vendor_fix_retest_result.json
A  reports/ATL_RESUME2B_VENDOR_FIX_RETEST_LAUNCH_RESULT_REPORT.md
```

## Whether Pushed

Yes — push to `origin main` after per-file `git add` + commit.

## 下一步建议

**ATL-RESUME-2C — Monitor vendor-fix retest run**

在 Castform UI 中打开 expected actual UI URL：`https://app.castform.com/train/e4abb2dc-cc68-4b52-8ba5-2195c3f12d1d?tab=train`，观察：

1. **run 是否突破 step 0**：如果 launch 真的产生了 train data / eval data / rollouts（与 ATL-5B / ATL-6 run 的"step 0 failed before rollouts"不同），则 vendor fix 实际生效。
2. **run 终态**：观察 terminal state — `completed` / `failed` / `running` / `queued`。
3. **display name**：观察 run 的 display name（应类似 `simple-xxxxxxxx`）。
4. **metrics**：观察训练 metrics（reward / loss / step count）。

agent 在 ATL-RESUME-2C 阶段仍不调用 Castform API、不访问 UI、不上传、不训练，仅做 result-recording（pitfall #22 on-disk verify first）。

retest 成功（launch SUCCESS 且 status ≠ failed at step 0）→ 更新 `phase` / `status` / `final_status`；retest 仍失败 → 停止本地 retry，回到 support 路径，把 vendor-fix context 附在新的 support bundle 顶部。

## 已知限制

- 本报告**不**记录 API key / API key 前缀或片段
- 本报告**不**记录用户邮箱 / 截图 / 信用卡 / cookie / Authorization header
- `actual_ui_url` 在 result JSON 中为 `null`；将在 ATL-RESUME-2C 阶段由用户在 Castform UI 实际发现后 backfill
- 本阶段使用 `read -s` 临时注入 API key（用户本地 WSL shell），**agent 端从未读取 API key 值**
- on-disk result JSON 来源于用户本地 WSL shell 手动运行；agent 仅做 `read_file` 读取 + transcribe，**未执行 retest 脚本**
