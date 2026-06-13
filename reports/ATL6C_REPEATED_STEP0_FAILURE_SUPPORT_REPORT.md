# ATL-6C — Repeated Step 0 Failure Support Request

## Stage conclusion
PASS_SUPPORT_REQUEST_READY — support request, failure summary, stdlib validator, case page (ATL-6B + ATL-6C sections), README, cases.json, and report are all in place. Agent did not call Castform API, did not visit Castform UI, did not upload, did not train, did not repeat the launch, did not forge metrics. Bundle is ready for the user to paste into Castform Castie/support.

## Current baseline commit
- 43b75f5 (ATL-6A starter-style redeploy prepared)
- this commit: see "Commit hash" below
- ATL-6A artifacts preserved: `cases/.../starter-style-redeploy/{prepare_starter_style_subset.py,reward_starter_style.py,environment_starter_style.py,validate_starter_style_env.py,atl6_starter_style_redeploy.py,starter-train.preview.jsonl,starter-eval.preview.jsonl,ATL6_STARTER_STYLE_REDEPLOY_NOTES.md,atl6_starter_style_redeploy_result.json}`

## ATL-6 launch result (from user-executed redeploy script, recorded in `atl6_starter_style_redeploy_result.json`)
- phase: ATL-6
- status: PASS_CLOUD_SMOKE_LAUNCHED
- local_validate_env_result: VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)
- upload_attempted: true / upload_succeeded: true
- launch_attempted: true / launch_succeeded: true
- run_id: 56cb5701-6b3e-424e-b671-fc2efc932aa8
- experiment_url: https://app.castform.com/experiments/56cb5701-6b3e-424e-b671-fc2efc932aa8
- base_model: Qwen/Qwen3.5-4B
- train_samples: 16 / eval_samples: 4
- api_key_recorded: false
- dataset_uploaded: true / training_started: true
- uploaded_payload_present: true (env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path — blob paths only, no signed URLs, no tokens, no credentials)
- launcher_args: model, learning_rate, num_epochs, group_size, max_rollout_len, max_turns, lora_rank, lora_alpha (no batch_size)
- error_category: null / error_summary: null (script returned clean; UI observed the failure, not the script)

## ATL-6 UI observation (from user-reported Castform UI)
- actual UI URL: https://app.castform.com/train/56cb5701-6b3e-424e-b671-fc2efc932aa8?tab=train
- display name: simple-c869a30d
- status: failed
- step: 0
- started: about 8 min ago
- train data: no train data available
- train rollouts: no rollouts recorded yet
- eval data: not yet checked
- config tab: uploaded env and dataset paths visible

## Comparison with ATL-5B (Run 1)
| Field | Run 1 (ATL-5B-RESULT) | Run 2 (ATL-6) |
|-------|----------------------|---------------|
| run_id | c83f971d-2b2c-42b8-9774-ca64938c1286 | 56cb5701-6b3e-424e-b671-fc2efc932aa8 |
| env class | HermesPhaseCloserLocalEnv | HermesPhaseCloserStarterStyleEnv |
| base model | Qwen/Qwen3.5-4B | Qwen/Qwen3.5-4B |
| train / eval | 8 / 2 | 16 / 4 |
| tools | list_tools=[] (still raised NotImplementedError) | list_tools=[] (returns "" no raise) |
| reward range | 0.0~10.0 | 0.0~1.0 |
| batch_size | not used (ATL-5A fix applied) | not used |
| load_dataset override | no | no (BaseEnv default) |
| launcher_args | 8 keys (no batch_size) | 8 keys (no batch_size) |
| local validate_env | VALIDATE_ENV_LOCAL_PASS (10/10) | VALIDATE_ENV_LOCAL_PASS (10/10) |
| upload | SUCCEEDED | SUCCEEDED |
| launch | SUCCEEDED | SUCCEEDED |
| UI status | failed | failed |
| UI step | 0 | 0 |
| UI train data | none | none |
| UI rollouts | none | none |
| display name | simple-28de6dd2 | simple-c869a30d |
| actual UI route | /train/<run_id>?tab=train | /train/<run_id>?tab=train |
| config tab | uploaded env + dataset paths visible | uploaded env + dataset paths visible |

Failure shape is identical: launch returns success at SDK level, but the worker never progresses past step 0 and records no train data, no rollouts. The starter-style pivots (larger dataset, no-tools env that doesn't raise, normalized reward, BaseEnv default) did not break the pattern.

## Ruled out (per formal spec, across both runs)
- missing API key
- upload failure
- unsupported `batch_size`
- fewer than 16 train examples
- `run_tool` raising in no-tools env
- reward not normalized

Additional ruled-out items (this report, beyond formal spec):
- env complexity / custom `load_dataset` override / tools — Run 2 is a no-tools BaseEnv default env
- local `validate_env` contract — Run 2 VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)
- missing run / missing UI route — both runs visible in Castform UI; both `/train/<run_id>?tab=train` routes render
- config tab broken — both runs show uploaded env and dataset paths

## Not yet ruled out (per formal spec)
- remote worker bootstrap failure
- dataset load failure in remote trainer
- env unpickle / import issue in remote trainer
- trainer backend internal error
- quota / runtime / account-level issue

Likely category: **FAILED_UNKNOWN_WORKER_BOOTSTRAP_OR_PLATFORM** (Castform backend, not agent-side config)

## Support request path
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md`
- structure: "What Worked" / "What Failed" / "Request" / "Sensitive Information Exclusion" / Run 1 (ATL-5B) / Run 2 (ATL-6) / Configuration (Run 2) / Local Validation (Run 2) / Upload Artifacts (Run 2) / What was ruled out / What we need from Castform / What we can provide back to Castform / Local environment context / Status

## Failure summary path
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_FAILURE_SUMMARY.md`
- structure: current status / likely category / ruled out (6 per spec) / not yet ruled out (5 per spec) / UI-visible evidence (both runs) / read-only SDK probe (reused from ATL-5D) / next action

## Created files (this phase)
| Path | Purpose |
|------|---------|
| `cases/.../starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md` | Paste-ready support request (What Worked / What Failed / Request / Sensitive Information Exclusion / Run 1 + Run 2 / configuration / upload artifacts / ruled out / what we need / what we can provide / local env context / status) |
| `cases/.../starter-style-redeploy/support/ATL6C_FAILURE_SUMMARY.md` | Ruled out 6 / not yet ruled out 5 / UI evidence (both runs) / SDK probe reuse / next action |
| `scripts/validate_atl6c_support_request.py` | stdlib validator (per formal spec) — both md files exist / both run_id tokens / status tag / 16 secret patterns + 1 forbidden literal scan |

## Modified files (this phase)
| Path | Change |
|------|--------|
| `cases/.../index.html` | Updated page header (lines 65-66) · **added new ATL-6B section** (Starter-style redeploy result) · rewrote ATL-6C section (Starter-style run monitor wording, What Worked / What Failed / Ruled out 6 / Not yet ruled out 5) · updated timeline entry · updated footer |
| `data/cases.json` | `phase` → `ATL-6C starter-style run failed before rollouts` · `status` → `repeated step 0 failure; support request prepared` · `updated_at` = 2026-06-13 |
| `README.md` | `## 当前状态` updated to ATL-6C · added `**ATL-6B 收口**` block · updated `**ATL-6C 收口**` and `**ATL-6C 硬边界**` and `**ATL-6C 下一步**` and `**ATL-6C 验证（追加）**` to reference `validate_atl6c_support_request.py` |
| `scripts/validate_atl6c_support_bundle.py` → `scripts/validate_atl6c_support_request.py` | Renamed via `git mv` (the file content was already aligned with formal spec; only the banner name and filename changed) |
| `reports/ATL6C_SUPPORT_READY_FAILURE_BUNDLE_REPORT.md` → `reports/ATL6C_REPEATED_STEP0_FAILURE_SUPPORT_REPORT.md` | Renamed via `git mv` (this report replaces it) |

## Validation results
- `python3 scripts/validate_atl6c_support_request.py` → **PASS** (per formal spec: support dir / `ATL6C_SUPPORT_REQUEST.md` / `ATL6C_FAILURE_SUMMARY.md` / run_id `c83f971d-2b2c-42b8-9774-ca64938c1286` / run_id `56cb5701-6b3e-424e-b671-fc2efc932aa8` / status tag `FAILED_STEP_0_NO_ROLLOUTS_REPEATED` / 16 secret patterns + 1 forbidden literal scan — all clean)
- `<redacted-key-prefix-literal>` repo-wide grep → 0 matches in `README.md`, `cases/`, `data/`, `docs/`, `reports/`, `scripts/`
- All 12 prior validators + new `validate_atl6c_support_request.py` PASS (13/13)

## Repo-wide guardrails preserved
- ATL-5 history `cases/.../cloud-smoke-run/live/atl5_cloud_smoke_result.json` — preserved
- ATL-5B history `cases/.../cloud-smoke-run/live/atl5b_second_upload_launch_retry_result.json` — preserved
- ATL-5C monitoring files — preserved
- ATL-5D support bundle (ATL5D_SUPPORT_REQUEST.md, ATL5D_FAILURE_SUMMARY.md, validate_atl5d_support_bundle.py) — preserved
- ATL-6A starter-style redeploy artifacts — preserved
- `atl6_starter_style_redeploy_result.json` — preserved (recorded from user-executed redeploy)
- `.venv-castform-local/` — not created, not staged, not committed
- `.env` — not created
- Old failed run `c83f971d-...` — not deleted
- Old failed run `56cb5701-...` — not deleted
- Result files are not referenced as inputs to any new script

## Hard-boundary audit (11/11)
| # | Boundary | Status |
|---|----------|--------|
| 1 | agent did not call Castform API | OK — only ran stdlib validators (zero network) |
| 2 | agent did not visit Castform UI | OK — no `browser_navigate` to `app.castform.com` |
| 3 | agent did not upload data | OK — no `upload_training_run` invocation |
| 4 | agent did not train | OK — no `launch_training_run` invocation |
| 5 | agent did not repeat launch | OK — did not run `atl6_starter_style_redeploy.py` again, did not run `atl5b_second_upload_launch_retry.py` again |
| 6 | API key not recorded | OK — only `os.environ` presence check in support doc; no key value touched |
| 7 | API key prefix or fragment not recorded | OK — `cf` + `_` + `J` pattern stays as concat literal in validator only |
| 8 | did not commit `.env` | OK — no `.env` file in working tree |
| 9 | did not commit `.venv` | OK — `.gitignore` blocks `.venv-castform-local/` |
| 10 | did not record credit card / cookie / Authorization header / user email / screenshot | OK — none in any new file |
| 11 | did not forge backend failure reason / did not forge metrics | OK — likely category and "not yet ruled out" come from analysis, not from any backend log; no rollout / reward / cost numbers invented |

## Commit hash
- see commit message `ATL-6C: Record repeated step 0 failure and support request` (created by the next step, not yet at report-write time)

## Whether pushed
- see "push" status below — executed after commit

## Next step
User pastes `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md` content into Castform Castie/support. If Castform returns a backend error → enter **ATL-6D root cause fix** (可能分支：改 env packaging / 改 dataset upload 路径 / 改 launcher_args / 申请 starter-task 已知好配置做 binary search). No further agent-side action until backend logs are returned.
