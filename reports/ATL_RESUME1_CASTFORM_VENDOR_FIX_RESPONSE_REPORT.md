# ATL-RESUME-1 — Record Castform Vendor Fix Response

## 阶段结论

PASS_VENDOR_FIX_RECORDED

## 当前基线

- baseline commit: 2fc426b (ATL-STD-1: fill report commit hash and push status)

## 阶段目标

记录 Castform 创始人 Girish 的官方修复反馈；将 Castform case 状态从 `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` 更新为 `VENDOR_FIX_RECEIVED_RETEST_PENDING`。本阶段只更新文档、案例页、cases.json 与报告，不调用 Castform API、不访问 UI、不上传数据、不启动训练、不读取 API key。

## Vendor Response Summary

Castform confirmed that the issue was fixed.

> "Castform confirmed the issue was fixed. The root cause was a raw data dict causing incompatibilities with their trainer. They also added $100 in extra credits to the account."

Vendor: Girish (Castform founder). Reply delivered to user; original screenshot supplied but not committed to the repo per sensitive-information exclusion rules.

## Vendor-Confirmed Root Cause

The raw data dict caused incompatibilities with the Castform trainer.

This shifts prior speculation: the failure shape (`failed` at step 0, no rollouts) was likely a trainer-side incompatibility, not solely local project configuration. Historical Run 1 (`c83f971d-2b2c-42b8-9774-ca64938c1286`) and Run 2 (`56cb5701-6b3e-424e-b671-fc2efc932aa8`) remain valid evidence and remain recorded as `step 0 failed before rollouts`.

## Credit Update

Castform added $100 in extra credits to the account.

## Old Status

`PAUSED_PENDING_CASTFORM_BACKEND_LOGS` (preserved as historical audit trail in CASE_CLOSEOUT.md and CASTFORM_SUPPORT_REQUEST_FINAL.md).

## New Status

`VENDOR_FIX_RECEIVED_RETEST_PENDING` — case can be resumed for retest after the vendor fix.

## Files Updated

| Path | Change |
|------|--------|
| `cases/castform-hermes-phase-closer-v0/VENDOR_FIX_RESPONSE.md` | new — full vendor fix response record |
| `cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md` | append-only — new `Vendor Fix Update` section; historical closeout preserved |
| `cases/castform-hermes-phase-closer-v0/CASTFORM_SUPPORT_REQUEST_FINAL.md` | prepend — `Follow-up` section; original support request preserved verbatim |
| `cases/castform-hermes-phase-closer-v0/index.html` | new `Vendor fix received` section + updated footer |
| `data/cases.json` | Castform case: phase `VENDOR-FIX-RECEIVED`, status `vendor fix received; retest pending`, final_status `VENDOR_FIX_RECEIVED_RETEST_PENDING`, updated_at `2026-06-14`; canonical_example / workflow_reference preserved |
| `README.md` | current-status header updated; new `ATL-RESUME-1 收口` block + `Castform case 当前状态` block added |
| `scripts/validate_vendor_fix_response.py` | new stdlib validator |
| `reports/ATL_RESUME1_CASTFORM_VENDOR_FIX_RESPONSE_REPORT.md` | this report |

## Sensitive Information Exclusion

This phase does NOT include or record:

- API key
- API key prefix (no literal 4-character / 12-character / end fragment)
- API key in any form (full / prefix / fragment / Authorization header / Cookie / Bearer)
- user email
- screenshot from vendor (not committed)
- cookie
- Authorization header
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
| agent did NOT run ATL-5 / ATL-6 / redeploy scripts | YES |
| agent did NOT read API key in any form | YES |
| agent did NOT record API key / email / screenshot / cookie / Authorization header / credit card | YES |
| agent did NOT create .env | YES |
| agent did NOT commit .venv | YES |
| agent did NOT rewrite historical facts (two old runs still recorded as step 0 failed) | YES |
| agent did NOT fabricate retest success | YES |

## Validation Results

| Script | Result |
|--------|--------|
| `validate_jsonl.py` | PASS |
| `validate_site.py` | PASS |
| `check_secrets.py` | PASS |
| `validate_case_closeout.py` | PASS (historical closeout invariants preserved) |
| `validate_vendor_fix_response.py` | PASS (new ATL-RESUME-1 validator, 16 secret patterns + 1 forbidden literal scan clean) |
| `validate_castform_local_scaffold.py` | PASS |
| `validate_atl3c_sdk_mapping.py` | PASS |
| `validate_atl4a_preflight_scaffold.py` | PASS |
| `validate_atl4b_cloud_smoke_config.py` | PASS |
| `validate_atl4c_guarded_preflight.py` | PASS |
| `validate_atl5_cloud_smoke_result.py` | PASS |
| `validate_atl5a_launch_args_fix.py` | PASS |
| `validate_atl5b_second_upload_retry_result.py` | PASS |
| `validate_atl5c_failed_step0_record.py` | PASS |
| `validate_atl5d_support_bundle.py` | PASS |
| `validate_atl6_starter_style_redeploy.py` | PASS |
| `validate_atl6c_support_request.py` | PASS |

Repo-wide key-prefix grep (literal pattern, exact command per user spec):

`# command pattern: forbidden key prefix (literal key-shape pattern, deliberately not echoed to avoid self-match; the spec-mandated command was executed by agent against repo before commit)`

Execution result: zero hits. No real key prefix leaked across repo.

## git status

```
M  README.md
M  cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md
M  cases/castform-hermes-phase-closer-v0/CASTFORM_SUPPORT_REQUEST_FINAL.md
M  cases/castform-hermes-phase-closer-v0/index.html
M  data/cases.json
?? cases/castform-hermes-phase-closer-v0/VENDOR_FIX_RESPONSE.md
?? reports/ATL_RESUME1_CASTFORM_VENDOR_FIX_RESPONSE_REPORT.md
?? scripts/validate_vendor_fix_response.py
```

## Whether Pushed

Yes — push to `origin main` after per-file `git add` + commit.

## 下一步建议

**ATL-RESUME-2 — Retest Castform starter-style run after vendor fix**

基于 Castform 官方修复 + $100 credits，case 现在可以 resume。在 ATL-RESUME-2 中：

- 用户本地 WSL 手动运行 starter-style redeploy 脚本（不依赖 agent 自动 launch）
- 使用与 ATL-6A 相同的 16 train / 4 eval preview
- 复用已有的 launcher_args（含 `learning_rate`，不含 `batch_size`）
- 新 `run_name` 标识这是 vendor-fix 之后的 retest（与 ATL-5B / ATL-6A 历史区分）
- agent 仍不调用 Castform API、不访问 UI、不上传、不训练、不读取 API key
- agent 仅做 result-recording（on-disk verify first, then transcribe to case page / cases.json / report）
- 如新 retest 成功（launch SUCCESS 且 status != failed），更新 `phase` / `status` / `final_status`；如仍失败，停止本地 retry，回到 support 路径并把 vendor 修复信息附在新的 support bundle 顶部

## 已知限制

- 本报告**不**记录 Castform 创始人 Girish 原文截图（用户硬规则）
- 本报告**不**记录用户邮箱（用于联系 Castform）
- 本报告**不**记录 Castform 官方账号的任何 credential
- 任何后续 retest 的真实 Castform API 调用仍由用户在本地 WSL 手动执行（agent 边界不变）
