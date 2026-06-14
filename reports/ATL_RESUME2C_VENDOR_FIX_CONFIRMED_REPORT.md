# ATL-RESUME-2C — Record Castform Vendor Fix Confirmed by Retest

## 阶段结论

**PASS_VENDOR_FIX_CONFIRMED_BY_RETEST**

## 当前基线

- baseline commit: f208a57 (ATL-RESUME-2B: Record Castform vendor-fix retest launch result)
- next commit: this report's commit

## 阶段目标

记录用户在 Castform UI 观察到的 ATL-RESUME-2B 启动的 vendor-fix retest run 的成功结果，将 Castform case 状态从 `VENDOR_FIX_RECEIVED_RETEST_PENDING` 推进到 `VENDOR_FIX_CONFIRMED_BY_RETEST`。本阶段只记录用户提供的脱敏观察结果，不调用 Castform API、不访问 Castform UI、不上传数据、不启动训练、不重复 launch。Agent 仅做 on-disk verify（pitfall #22 trust-but-verify）+ transcribe。

## Vendor Fix Context

- vendor: Girish (Castform founder)
- vendor-confirmed root cause: raw data dict caused incompatibilities with the Castform trainer
- fix status: confirmed by retest (Castform side)
- credit update: $100 extra credits added to the account
- status progression:
  - `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` (ATL-CLOSEOUT)
  - `VENDOR_FIX_RECEIVED_RETEST_PENDING` (ATL-RESUME-1, vendor response received)
  - `VENDOR_FIX_CONFIRMED_BY_RETEST` (ATL-RESUME-2C, vendor fix confirmed by retest run)

## Old Failure Mode (preserved as audit trail)

| Run | run_id | sample count | status | step | rollouts |
|-----|--------|--------------|--------|------|----------|
| Run 1 (ATL-5B) | `c83f971d-2b2c-42b8-9774-ca64938c1286` | 8 train / 2 eval | failed | 0 | none |
| Run 2 (ATL-6) | `56cb5701-6b3e-424e-b671-fc2efc932aa8` | 16 train / 4 eval | failed | 0 | none |

Both old runs remain recorded as `step 0 failed before rollouts`. They are preserved as audit trail in `CASE_CLOSEOUT.md`, `CASTFORM_SUPPORT_REQUEST_FINAL.md`, `data/cases.json`, the case page, and this report. The new retest run does NOT reference them as input.

## Retest Run Identity (from on-disk result JSON, verified)

| Field | Value (from result JSON) |
|-------|--------------------------|
| run_id | `e4abb2dc-cc68-4b52-8ba5-2195c3f12d1d` ✓ matches user-reported value |
| launch_status | `PASS_CLOUD_SMOKE_LAUNCHED` |
| upload_succeeded | `true` |
| launch_succeeded | `true` |
| train_samples | `16` |
| eval_samples | `4` |
| api_key_recorded | `false` |
| training_started | `true` |
| dataset_uploaded | `true` |
| uploaded_payload_present | `true` (env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path) |
| error_category | `null` |
| uploaded_payload content | clean Castform blob paths only, no signed URLs |

## User-Observed Retest Result (from Castform UI, reported by user)

| Observed field | Value |
|----------------|-------|
| observed status | `complete` |
| step | `1 / 1` |
| started | about 39 minutes before observation |
| display name | `simple-ed08313b` |
| train rollout deepdive | visible |
| train rollouts recorded | `YES` |
| average reward chart | visible |
| response length chart | visible |
| max reward chart | visible |
| solve rate chart | visible |
| reward components visible | `coverage` / `format` / `score` |
| sample rollout rewards observed around | `2.00` / `2.05` / `2.11` / `1.95` / `2.10` / `1.97` |

> Note: the reward values listed above are reported by the user from the Castform UI. They reflect the `format` + `coverage` + `score` components in 0.0~1.0 range × the reward weighting (likely 2x default), per starter-style env scoring.

## Previous Failure Mode vs Current Result

| Aspect | Old failure mode | Current retest |
|--------|------------------|----------------|
| step | 0 (failed) | 1 / 1 (complete) |
| train rollouts | none | recorded (YES) |
| reward charts | none (no data) | all 4 visible (average reward, response length, max reward, solve rate) |
| reward components | none | coverage / format / score all visible |
| sample rollout rewards | none | 2.00 / 2.05 / 2.11 / 1.95 / 2.10 / 1.97 |

The repeated step 0 no rollouts failure shape is resolved.

## Final Status

`VENDOR_FIX_CONFIRMED_BY_RETEST` — Castform fix confirmed for this test case.

## Hard Boundary Compliance

| Hard boundary | Status |
|---------------|--------|
| agent did NOT call Castform API | YES (0 API calls) |
| agent did NOT access Castform UI | YES |
| agent did NOT upload data | YES |
| agent did NOT start training | YES |
| agent did NOT re-run retest script | YES |
| agent did NOT re-launch | YES |
| agent did NOT read API key in any form | YES |
| agent did NOT record API key / email / screenshot / cookie / Authorization header / credit card | YES |
| agent did NOT create .env | YES |
| agent did NOT commit .venv | YES |
| agent did NOT fake metrics (sample rewards / chart list from user report) | YES |
| agent did NOT rewrite historical facts (Run 1 + Run 2 still step 0 failed) | YES |
| agent did NOT reference old run_ids as new retest input | YES |

## Validation Results

| Script | Result |
|--------|--------|
| `validate_jsonl.py` | PASS |
| `validate_site.py` | PASS (canonical_example + workflow_reference preserved) |
| `check_secrets.py` | PASS |
| `validate_atl_resume2_vendor_fix_retest.py` | PASS (result JSON invariants verified) |
| `validate_vendor_fix_confirmed.py` | PASS (new — VENDOR_FIX_CONFIRMED.md + VENDOR_FIX_CONFIRMED_BY_RETEST + run_id + data/cases.json final_status + secret scan clean) |
| `validate_vendor_fix_response.py` | FAIL (expected — phase 已从 `VENDOR-FIX-RECEIVED` 推进到 `ATL-RESUME-2C vendor fix confirmed by retest`，验证器对 phase/status 的断言恰恰验证状态机正确转移，与 ATL-RESUME-1 / ATL-RESUME-2A / ATL-RESUME-2B 阶段同模式) |
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
| `validate_case_closeout.py` | FAIL (expected — phase 已从 `CASE-CLOSEOUT` 推进到 `ATL-RESUME-2C vendor fix confirmed by retest`，验证器对 phase/status 的断言恰恰验证状态机正确转移) |

Repo-wide key-prefix grep (literal pattern, exact command per user spec):

`# command pattern: forbidden key prefix (literal key-shape pattern, deliberately not echoed to avoid self-match; the spec-mandated command was executed by agent against repo before commit)`

Execution result: zero hits. No real key prefix leaked across repo.

## git status

```
M  README.md
M  cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md
M  cases/castform-hermes-phase-closer-v0/index.html
M  data/cases.json
A  cases/castform-hermes-phase-closer-v0/VENDOR_FIX_CONFIRMED.md
A  reports/ATL_RESUME2C_VENDOR_FIX_CONFIRMED_REPORT.md
A  scripts/validate_vendor_fix_confirmed.py
```

## Whether Pushed

Yes — push to `origin main` after per-file `git add` + commit.

## 下一步建议

**Update final closeout / Begin next AI Tool Test Lab case**

Castform case 的状态机已推进到 `VENDOR_FIX_CONFIRMED_BY_RETEST`，完整 canonical example 已落地。下一步：

1. **Update final closeout doc**：把 `CASE_CLOSEOUT.md` 的 "Final Status" 从 `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` 改为 `VENDOR_FIX_CONFIRMED_BY_RETEST`，并保留全部历史 closeout 段作为 audit trail。
2. **Begin next case**：per ATL-STD-1 模板的 case workflow，开始下一个 AI Tool Test Lab 案例的 ATL-0 scaffold 阶段。
3. **可选**：新增 case 候选可以从两个方向选 — (a) 第二个 RL post-training 平台（例如另一个 RL 工具）；(b) 第二个训练范式（不同模型族或不同训练模式）。具体方向等用户决定。

## 已知限制

- 本报告**不**记录 API key / API key 前缀或片段
- 本报告**不**记录用户邮箱 / 截图 / 信用卡 / cookie / Authorization header
- agent **不调用 Castform API**、**不访问 Castform UI**、**不上传数据**、**不启动训练**、**不重复 launch**
- agent 仅做 `read_file` 读取 on-disk result JSON + transcribe 用户报告的脱敏 UI 观察结果
- sample rollout rewards / chart 列表均来自用户报告，agent 未伪造
- 历史 Run 1 + Run 2 仍记录为 step 0 failed，作为 audit trail 保留
