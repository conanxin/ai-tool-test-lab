# ATL-RESUME-2A — Prepare Castform Vendor-Fix Retest Script

## 阶段结论

SCRIPT_READY_NO_CLOUD_CALL

## 当前基线

- baseline commit: 35bdd71 (ATL-RESUME-1: Record Castform vendor fix response)
- next commit: this report's commit

## 阶段目标

在 Castform vendor fix 已被官方确认（raw data dict trainer incompatibility 修复 + $100 credits added）后，准备 ATL-RESUME-2 的 vendor-fix retest 脚本、验证器、说明文档、案例页更新、cases.json 更新与报告。本阶段只准备脚本和文档，不调用 Castform API、不上传数据、不启动训练。真实 retest 必须由用户在本地 WSL shell 中显式授权后手动运行。

## Vendor Fix Summary

- vendor: Girish (Castform founder)
- vendor-confirmed root cause: raw data dict caused incompatibilities with the Castform trainer
- fix status: received (Castform side)
- credit update: $100 extra credits added to the account
- case status moved: `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` → `VENDOR_FIX_RECEIVED_RETEST_PENDING` (ATL-RESUME-1)

## Retest Purpose

Verify whether the step-0 failure is fixed after Castform's vendor-side patch. Specifically: confirm that a fresh, independent training run progresses beyond step 0 and produces real rollout data (train data / eval data / rollouts / terminal status ≠ failed at step 0).

## Retest Configuration (inherited from ATL-6 starter-style)

| Field | Value |
|-------|-------|
| dataset | 16 train / 4 eval preview subset (reused from `starter-style-redeploy/`) |
| environment | `HermesPhaseCloserStarterStyleEnv` (no-tools, `list_tools=[]`, `run_tool=""` no raise) |
| reward | 0.0~1.0 (format / coverage / score) |
| base model | `Qwen/Qwen3.5-4B` |
| run_name | `hermes-phase-closer-vendor-fix-retest` (fresh, independent from ATL-5B / ATL-6) |
| launcher_args | `model`, `learning_rate: 1e-5`, `num_epochs: 1`, `group_size: 2`, `max_rollout_len: 512`, `max_turns: 1`, `lora_rank: 16`, `lora_alpha: 32` (no `batch_size`) |
| env override | no custom `load_dataset` override (BaseEnv default) |
| result file | `cases/castform-hermes-phase-closer-v0/vendor-fix-retest/atl_resume2_vendor_fix_retest_result.json` (separate from ATL-5 / ATL-5B / ATL-6 result JSON) |
| authorization string | `I AUTHORIZE ATL-RESUME-2 CASTFORM RETEST AFTER VENDOR FIX` |

## Created Files

| Path | Type | Purpose |
|------|------|---------|
| `cases/castform-hermes-phase-closer-v0/vendor-fix-retest/atl_resume2_vendor_fix_retest.py` | new | retest script (gate check → 本地 validate_env → upload → launch → 独立 result JSON) |
| `cases/castform-hermes-phase-closer-v0/vendor-fix-retest/ATL_RESUME2_VENDOR_FIX_RETEST_NOTES.md` | new | retest notes (vendor fix context / expected signal / authorization / hard rules) |
| `scripts/validate_atl_resume2_vendor_fix_retest.py` | new | stdlib 验证器（SKIPPED 模式 / result JSON 检查） |
| `reports/ATL_RESUME2A_VENDOR_FIX_RETEST_PREP_REPORT.md` | new | this report |

## Updated Files

| Path | Change |
|------|--------|
| `README.md` | current-status header → ATL-RESUME-2A；新增 ATL-RESUME-2A 收口段 |
| `cases/castform-hermes-phase-closer-v0/index.html` | 新增 "ATL-RESUME-2A — Vendor-Fix Retest Prepared" 模块；更新 footer |
| `data/cases.json` | Castform case phase=`ATL-RESUME-2A vendor-fix retest prepared` · status=`vendor fix recorded; retest script ready` · final_status=`VENDOR_FIX_RECEIVED_RETEST_PENDING`（保留作为审计） · canonical_example / workflow_reference 保留 · updated_at=2026-06-14 |

## Sensitive Information Exclusion

This phase does NOT include or record:

- API key
- API key prefix or fragment (no 4-character / 12-character / end-substring anywhere)
- Authorization header
- Cookie
- Bearer token
- user email
- screenshot from vendor
- credit card information
- Castform account password
- `.env` file
- `.venv/` directory

## Agent Hard Boundary Compliance

| Hard boundary | Status |
|---------------|--------|
| agent did NOT call Castform API | YES |
| agent did NOT access Castform UI | YES |
| agent did NOT upload data | YES |
| agent did NOT start training | YES |
| agent did NOT run ATL-5B / ATL-6 / new retest script | YES |
| agent did NOT read API key in any form | YES |
| agent did NOT record API key / email / screenshot / cookie / Authorization header / credit card | YES |
| agent did NOT create .env | YES |
| agent did NOT commit .venv | YES |
| agent did NOT rewrite historical facts (Run 1 + Run 2 still step 0 failed) | YES |
| agent did NOT reference old run_ids as new retest input | YES |
| agent did NOT fabricate retest success | YES |

## Validation Results

| Script | Result |
|--------|--------|
| `validate_jsonl.py` | PASS |
| `validate_site.py` | PASS |
| `check_secrets.py` | PASS |
| `validate_vendor_fix_response.py` | PASS (ATL-RESUME-1 invariants preserved) |
| `validate_atl_resume2_vendor_fix_retest.py` | PASS (SKIPPED_RESULT_NOT_PRESENT mode; retest script is prep-only, not run) |
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
| `validate_case_closeout.py` | FAIL (expected — phase 已从 `CASE-CLOSEOUT` 推进到 `ATL-RESUME-2A vendor-fix retest prepared`，验证器对 phase/status 的断言恰恰验证状态机正确转移) |

Repo-wide key-prefix grep (literal pattern, exact command per user spec):

`# command pattern: forbidden key prefix (literal key-shape pattern, deliberately not echoed to avoid self-match; the spec-mandated command was executed by agent against repo before commit)`

Execution result: zero hits. No real key prefix leaked across repo.

## git status

```
M  README.md
M  cases/castform-hermes-phase-closer-v0/index.html
M  data/cases.json
?? cases/castform-hermes-phase-closer-v0/vendor-fix-retest/
?? reports/ATL_RESUME2A_VENDOR_FIX_RETEST_PREP_REPORT.md
?? scripts/validate_atl_resume2_vendor_fix_retest.py
```

## Whether Pushed

Yes — push to `origin main` after per-file `git add` + commit.

## 下一步建议

**ATL-RESUME-2B — User local WSL runs vendor-fix retest (then agent records result)**

在本地 WSL shell 中：

```
export ATL_USER_AUTHORIZATION="I AUTHORIZE ATL-RESUME-2 CASTFORM RETEST AFTER VENDOR FIX"
export ATL_ALLOW_CASTFORM_UPLOAD="YES"
export ATL_ALLOW_CASTFORM_LAUNCH="YES"
read -s CASTFORM_API_KEY && export CASTFORM_API_KEY

cd /mnt/d/AI/ai-tool-test-lab
.venv-castform-local/bin/python cases/castform-hermes-phase-closer-v0/vendor-fix-retest/atl_resume2_vendor_fix_retest.py
python3 scripts/validate_atl_resume2_vendor_fix_retest.py
```

agent 在 ATL-RESUME-2B 阶段的行为：

1. **on-disk verify first**（pitfall #22）：`read_file` 验证 `atl_resume2_vendor_fix_retest_result.json` 真的存在 + 字段值与用户叙述匹配
2. result-recording 到 case page / cases.json / 报告
3. agent 仍不调用 Castform API / 不访问 UI / 不上传 / 不启动训练

retest 成功（launch SUCCESS 且 status ≠ failed）→ 更新 `phase` / `status` / `final_status`；retest 仍失败 → 停止本地 retry，回到 support 路径，把 vendor-fix context 附在新的 dual-run support bundle 顶部。

## 已知限制

- 本报告**不**记录 Castform 创始人 Girish 原文截图（用户硬规则）
- 本报告**不**记录用户邮箱（用于联系 Castform）
- 本报告**不**记录 Castform 官方账号的任何 credential
- retest 真实 Castform API 调用仍由用户在本地 WSL 手动执行（agent 边界不变）
