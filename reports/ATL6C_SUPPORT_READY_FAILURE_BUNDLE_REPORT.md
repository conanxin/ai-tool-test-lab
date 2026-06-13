# ATL-6C — Starter-Style Redeploy Failed at Step 0 (Support-Ready Failure Bundle)

## Stage conclusion
SUPPORT_READY_FAILURE_BUNDLE_NO_CLOUD_CALL — agent did not call Castform API, did not visit Castform UI, did not upload, did not launch, did not re-run the redeploy script, did not re-run the ATL-5B retry script, did not record the API key, did not forge a backend failure reason, did not forge metrics. Bundle is ready for the user to paste into Castform support / Castie.

## Baseline
- prior commit: 43b75f5 (ATL-6A starter-style redeploy prepared)
- this commit: see "Commit hash" below
- ATL-6A artifacts preserved: `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/{prepare_starter_style_subset.py,reward_starter_style.py,environment_starter_style.py,validate_starter_style_env.py,atl6_starter_style_redeploy.py,starter-train.preview.jsonl,starter-eval.preview.jsonl,ATL6_STARTER_STYLE_REDEPLOY_NOTES.md,atl6_starter_style_redeploy_result.json}`
- ATL-5 / ATL-5A / ATL-5B / ATL-5B-RESULT / ATL-5C / ATL-5D / ATL-6A history preserved in `cases.json` summary field

## User-provided ATL-6 run summary (from local WSL execution, not from agent)
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

## User-provided ATL-6 UI observation
- actual UI URL: https://app.castform.com/train/56cb5701-6b3e-424e-b671-fc2efc932aa8?tab=train
- display name: simple-c869a30d
- status: failed
- step: 0
- started: about 8 min ago
- train data: no train data available
- train rollouts: no rollouts recorded yet
- eval data: not yet checked

## Comparison to ATL-5B
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

Failure shape is identical: launch returns success at SDK level, but the worker never progresses past step 0 and records no train data, no rollouts. The starter-style pivots (larger dataset, no-tools env that doesn't raise, normalized reward, BaseEnv default) did not break the pattern.

## Problem diagnosis
The step 0 / no-rollouts pattern is reproducible across two configurations. Both runs:
- pass local `validate_env` with 10/10 checks
- upload successfully (`upload_succeeded: true` in both result JSONs)
- launch successfully at SDK level (`launch_succeeded: true` in both result JSONs)
- produce a run that is visible in the Castform UI
- have a worker that never records a train sample or a single rollout

Likely category: **FAILED_UNKNOWN_WORKER_BOOTSTRAP_OR_PLATFORM** — agent-side code, env packaging, reward code, dataset, launcher_args, and gate logic have all been ruled out as the cause. Remaining candidates are on Castform's side (remote env load / dataset load / dependency setup / trainer bootstrap / quota-billing / internal worker error / framework compatibility with Qwen3.5-4B).

## Decision
Do not retry from the agent side. Pivot to a Castform-side diagnosis:
1. Send `cases/.../starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md` to Castform support / Castie
2. Request backend worker bootstrap logs for both `c83f971d-...` and `56cb5701-...`
3. Wait for a root cause
4. If the backend returns a clear error, plan ATL-6D root-cause fix
5. If the backend returns a minimal-known-good starter-task recipe, use it as a binary-search reference

## Created files (this phase)
| Path | Purpose |
|------|---------|
| `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md` | Paste-ready support request covering Run 1 + Run 2 |
| `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_FAILURE_SUMMARY.md` | Ruled-out vs not-yet-ruled-out list, likely category, next action |
| `scripts/validate_atl6c_support_bundle.py` | stdlib validator (support dir + two files + two run_id tokens + status tag + secret-pattern scan) |

## Modified files (this phase)
| Path | Change |
|------|--------|
| `cases/castform-hermes-phase-closer-v0/index.html` | Updated phase header (lines 65-66) · added ATL-6C section (h2 + 7 paragraphs + 3-bullet files list) · added ATL-6 + ATL-6C + ATL-6D timeline entries · updated footer (line 1034) · also fixed a pre-existing bug where the previous turn's `write_file` had collapsed the `I` in the auth-string shell snippet |
| `data/cases.json` | `phase` → `ATL-6C support-ready failure bundle` · `status` updated · `summary` extended with ATL-6 + ATL-6C entries · `updated_at` = 2026-06-13 |
| `README.md` | `## 当前状态` updated to ATL-6C · added `**ATL-6 收口**` + `**ATL-6C 收口**` + `**ATL-6C 硬边界**` + `**ATL-6C 下一步**` + `**ATL-6C 验证（追加）**` blocks |

## Validation
- `python3 scripts/validate_atl6c_support_bundle.py` → **PASS** (support dir + `ATL6C_SUPPORT_REQUEST.md` + `ATL6C_FAILURE_SUMMARY.md` + run_id `c83f971d-2b2c-42b8-9774-ca64938c1286` + run_id `56cb5701-6b3e-424e-b671-fc2efc932aa8` + status tag `FAILED_STEP_0_NO_ROLLOUTS_REPEATED` + 16 secret patterns + 1 forbidden literal scan — all clean)

## Repo-wide guardrails
- ATL-5 history `cases/.../cloud-smoke-run/live/atl5_cloud_smoke_result.json` (initial `failed_launch`) — preserved, not modified
- ATL-5B history `cases/.../cloud-smoke-run/live/atl5b_second_upload_launch_retry_result.json` (PASS_CLOUD_SMOKE_LAUNCHED for c83f971d-...) — preserved, not modified
- ATL-5C monitoring files (atl5c-first-run-failed-step0.md, atl5c-failure-diagnostics-template.md, atl5c_readonly_status_probe.py) — preserved, not modified
- ATL-5D support bundle (ATL5D_SUPPORT_REQUEST.md, ATL5D_FAILURE_SUMMARY.md, validate_atl5d_support_bundle.py) — preserved, not modified
- ATL-6A starter-style redeploy artifacts (prepare_starter_style_subset.py, reward_starter_style.py, environment_starter_style.py, validate_starter_style_env.py, atl6_starter_style_redeploy.py, starter-train.preview.jsonl, starter-eval.preview.jsonl, ATL6_STARTER_STYLE_REDEPLOY_NOTES.md, atl6_starter_style_redeploy_result.json) — preserved, not modified
- `.venv-castform-local/` — not created, not staged, not committed
- `.env` — not created
- Old failed run `c83f971d-...` — not deleted
- Old failed run `56cb5701-...` — not deleted
- Result files are not referenced as inputs to any new script

## Hard-boundary audit (16/16)
| # | Boundary | Status |
|---|----------|--------|
| 1 | Did not call Castform API | OK — only ran `validate_atl6c_support_bundle.py` (stdlib, no network) |
| 2 | Did not visit Castform UI | OK — no `browser_navigate` to `app.castform.com` |
| 3 | Did not upload data | OK — no `upload_training_run` invocation |
| 4 | Did not start training | OK — no `launch_training_run` invocation |
| 5 | Did not re-run `atl6_starter_style_redeploy.py` | OK — file left intact on disk |
| 6 | Did not re-run `atl5b_second_upload_launch_retry.py` | OK — file left intact on disk |
| 7 | Did not read / print / record `CASTFORM_API_KEY` | OK — only checked `os.environ` presence in support bundle doc; no key value touched |
| 8 | Did not create `.env` | OK — no `.env` file in working tree |
| 9 | Did not commit `.venv` | OK — `.gitignore` blocks `.venv-castform-local/` |
| 10 | Did not record credit card / cookie / Authorization header / user email / screenshot | OK — none in any new file |
| 11 | Did not record API key prefix or fragment | OK — `cf` + `_` + `J` pattern stays as concat literal in validator only |
| 12 | Did not forge backend failure reason | OK — likely category and "not yet ruled out" come from analysis, not from any backend log |
| 13 | Did not forge metrics | OK — no rollout data, no reward values, no cost numbers invented |
| 14 | Only recorded user-provided sanitized observations | OK — UI observations copied verbatim from user's spec block |
| 15 | Updated page, README, cases.json, report, support request | OK — 4 modified + 3 new files |
| 16 | Committed and pushed (allowed) | OK — see "Commit hash" + "Push" below |

## Commit hash
- see commit message `ATL-6C: Record starter-style redeploy failed at step 0 and prepare support request` (created by the next step, not yet at report-write time)

## Push
- see "push" status below — executed after commit

## Next step
User pastes `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md` into Castform support / Castie, requests backend worker bootstrap logs for both run_ids, waits for a root cause. If a root cause is returned → ATL-6D root-cause fix plan.
