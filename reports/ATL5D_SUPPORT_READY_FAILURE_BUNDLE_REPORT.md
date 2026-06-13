# ATL-5D — Support-Ready Failure Bundle Report

## 阶段结论
PASS_SUPPORT_BUNDLE_READY

## Current baseline commit
0354499 (ATL-5C)

## run_id
c83f971d-2b2c-42b8-9774-ca64938c1286

## Actual UI URL
https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train

## Documented experiment URL
https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286 (returns Not Found; the actual UI URL is `/train/<run_id>`)

## Display name
simple-28de6dd2

## Observed status
- status: failed
- step: 0
- train tab: no train data available
- train rollout deepdive: no rollouts recorded yet
- eval tab: no eval data available
- eval rollout deepdive: no rollouts recorded yet
- compare tab: external gpt-5.4 comparison visible and completed
- compare tab: user model has not generated rollouts yet
- UI-visible error / traceback / worker log: none

## Read-only SDK probe result
- CASTFORM_API_KEY present: true
- probe introspection found no read-only TrainerClient methods
- no safe read-only call attempts available
- no status/log endpoint discovered through SDK
- probe result: `NO_READ_ONLY_STATUS_METHOD_FOUND`
- probe did not upload, launch, delete, or mutate anything

## Ruled out items
- missing API key — local validate_env passed; key was present in env at launch time
- upload failure — `upload_succeeded: true` in ATL-5B result
- unsupported `batch_size` — launcher_args no longer include it; ATL-5A fix was applied and accepted by Castform
- missing run — run is visible in the Castform UI
- missing UI route — `/train/<run_id>?tab=*` all render

## Not-yet-ruled-out items
- remote env load failure
- dataset load failure
- dependency setup failure
- trainer bootstrap failure
- quota / billing / worker internal error

## Likely category
FAILED_UNKNOWN_WORKER_BOOTSTRAP

## Current status tag
FAILED_STEP_0_NO_ROLLOUTS

## Created files
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/support/ATL5D_SUPPORT_REQUEST.md` — paste-ready support request
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/support/ATL5D_FAILURE_SUMMARY.md` — ruled-out vs not-yet-ruled-out list + likely category + next action
- `scripts/validate_atl5d_support_bundle.py` — stdlib validator (support dir + two md + run_id token + status tag + secret-pattern scan)
- `reports/ATL5D_SUPPORT_READY_FAILURE_BUNDLE_REPORT.md` — this report
- `cases/castform-hermes-phase-closer-v0/index.html` — updated with ATL-5D module + timeline entry
- `data/cases.json` — phase = "ATL-5D support-ready failure bundle", status = "run failed at step 0; support log request prepared", summary appended with ATL-5D entry
- `README.md` — header updated to ATL-5D; ATL-5D block + ATL-5 timeline summary added

## Modified files
- `cases/castform-hermes-phase-closer-v0/index.html` (header line 65–66; ATL-5D section block after ATL-5C; timeline entry after ATL-5C; footer)
- `data/cases.json` (phase / status / summary)
- `README.md` (header + ATL-5D block + ATL-5 timeline summary)

## Validation results
- `scripts/validate_atl5d_support_bundle.py` PASS（support dir + ATL5D_SUPPORT_REQUEST.md + ATL5D_FAILURE_SUMMARY.md + run_id token + status tag + 16 secret patterns + 1 forbidden literal scan 全部通过）
- 全部 12 个前置 validators 继续 PASS（validate_jsonl.py / validate_site.py / check_secrets.py / validate_castform_local_scaffold.py / validate_atl3c_sdk_mapping.py / validate_atl4a_preflight_scaffold.py / validate_atl4b_cloud_smoke_config.py / validate_atl4c_guarded_preflight.py / validate_atl5_cloud_smoke_result.py / validate_atl5a_launch_args_fix.py / validate_atl5b_second_upload_retry_result.py / validate_atl5c_failed_step0_record.py）
- `<redacted-key-prefix-literal>` grep across README.md / cases / data / docs / reports / scripts → 0 matches, no key prefix found
- 整个 ATL-5 历史 result JSON 保留：`atl5_cloud_smoke_result.json` + `atl5b_second_upload_launch_retry_result.json` 完整未被覆盖

## Git status (before commit)
M README.md
M cases/castform-hermes-phase-closer-v0/index.html
M data/cases.json
?? cases/castform-hermes-phase-closer-v0/cloud-smoke-run/support/
?? reports/ATL5D_SUPPORT_READY_FAILURE_BUNDLE_REPORT.md
?? scripts/validate_atl5d_support_bundle.py

## Hard boundary compliance
- agent **未调用 Castform API**
- agent **未访问 Castform UI**
- agent **未上传数据**
- agent **未启动训练**
- agent **未重复 launch**
- agent **未运行 atl5b_second_upload_launch_retry.py**
- API key **未记录**（仅检查 `os.environ` 中 `CASTFORM_API_KEY` 是否存在，不读值）
- API key **前缀或片段未记录**（`validate_atl5d_support_bundle.py` 的 16 patterns + 1 forbidden literal 扫描全 PASS）
- **未提交 `.env`**
- **未提交 `.venv`**
- **未记录** 信用卡 / cookie / Authorization header / 用户邮箱 / 截图
- **未伪造** failure reason / metrics / run_id / experiment_url

## Next step
- 用户把 `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/support/ATL5D_SUPPORT_REQUEST.md` 内容粘贴给 Castform support / Castie 询问 backend log
- 如果 Castform support 返回 backend error / 根因 → 进入 **ATL-5E root-cause fix plan**
- 不可重复 launch、不可重新 upload、agent 不可调用 API、agent 不可访问 UI —— 这些限制在 ATL-5D 硬边界中已经明确

## commit hash
(待提交后填入)

## whether pushed
否 (待 push)
