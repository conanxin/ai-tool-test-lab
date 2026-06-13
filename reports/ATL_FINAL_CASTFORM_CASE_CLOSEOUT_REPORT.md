# ATL-CLOSEOUT — Final Closeout for AI Tool Test Lab Castform Case

## Stage conclusion
PASS_CASE_CLOSED_PENDING_BACKEND_LOGS — Castform case is fully closed at the local documentation level. AI Tool Test Lab is published, the Castform case page is published, the local SDK path is validated, the cloud upload / launch path is validated, the repeated step 0 failure is captured in two real Castform runs, and a paste-ready support request is ready. Agent did not call Castform API, did not visit Castform UI, did not upload, did not train, did not repeat the launch, did not forge metrics, did not delete any historical result. No further cloud attempts planned until Castform backend logs or support feedback are available.

## Current baseline commit
- prior commit: 28ae939 (ATL-6C: repeated step 0 failure recorded + support request prepared)
- this commit: see "Commit hash" below

## Project public URL
- https://conanxin.github.io/ai-tool-test-lab/

## Castform case page URL
- https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/

## Test phase overview

| Phase | Date | Summary |
|-------|------|---------|
| ATL-0 | 2025-06-12 | Local scaffold — project structure, homepage, case page, docs, sample format, validation scripts |
| ATL-1 | 2025-06-12 | GitHub Pages publish prep — styles, docs, README |
| ATL-1P | 2025-06-12 | First publish to GitHub, enable GitHub Pages |
| ATL-2 | 2025-06-12 | Local dataset prep — 42 train + 7 eval desensitized, validate_jsonl PASS |
| ATL-3A | 2025-06-12 | Local scaffold-only — benchmax blocked, reward smoke PASS |
| ATL-3B | 2025-06-12 | Python 3.12 venv/pip fix (without-pip + /tmp/get-pip.py), benchmax install OK |
| ATL-3C | 2026-06-13 | Real local `validate_env` 10/10 PASS (`api_key=None` + `local=True` → zero network) |
| ATL-4A | 2026-06-13 | Account / Credit / Billing human preflight scaffold ready |
| ATL-4B-CONFIG | 2026-06-13 | Cloud smoke dry configuration ready (build_your_own_sdk · Qwen/Qwen3.5-4B · 8/2 preview) |
| ATL-4A-CREDIT-FILL | 2026-06-13 | User manually confirmed free credit $50 visible + usage page visible (first YES) |
| ATL-4C | 2026-06-13 | Guarded cloud smoke preflight ready (dual-gate architecture) |
| ATL-5-SCRIPT-PREP | 2026-06-13 | Live cloud smoke run script ready (gate + local validate_env + upload + launch + result JSON) |
| ATL-5 | 2026-06-13 | User manual run: local validate_env PASS · upload SUCCESS · launch FAILED (batch_size rejected) |
| ATL-5A | 2026-06-13 | Fix launcher_args (remove batch_size, add learning_rate: 1e-5) |
| ATL-5B | 2026-06-13 | Second upload + launch retry script ready |
| ATL-5B-RESULT | 2026-06-13 | User manual run: PASS_CLOUD_SMOKE_LAUNCHED · run_id `c83f971d-...` |
| ATL-5C | 2026-06-13 | UI observation: failed at step 0 · no rollouts |
| ATL-5D | 2026-06-13 | Support-ready failure bundle prepared |
| ATL-6A | 2026-06-13 | Starter-style redeploy script ready (16/4, no-tools, 0.0~1.0, no load_dataset override) |
| ATL-6 | 2026-06-13 | User manual run: PASS_CLOUD_SMOKE_LAUNCHED · run_id `56cb5701-...` |
| ATL-6B | 2026-06-13 | Starter-style redeploy result recorded on case page |
| ATL-6C | 2026-06-13 | UI observation: failed at step 0 again · no rollouts · support request prepared (Starter-style run monitor) |
| ATL-CLOSEOUT | 2026-06-13 | Final case closeout — pause project, support request ready, no further cloud runs |

## Final deliverables

- **Open-source test lab published**: `https://conanxin.github.io/ai-tool-test-lab/` (HTTP/2 200)
- **Castform case page published**: `https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/` (HTTP/2 200)
- **Local SDK path validated**: `benchmax.platform.validation.validate_env` real local 10/10 PASS
- **Cloud upload / launch validated**: two real Castform training runs created (upload SUCCESS · launch SUCCESS at SDK level)
- **Repeated cloud step 0 failure captured**: two independent run_ids both `failed` at step 0, both with no rollouts
- **Support request prepared**: `cases/castform-hermes-phase-closer-v0/CASTFORM_SUPPORT_REQUEST_FINAL.md` (paste-ready, English) and `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md` (detailed)

## Final blockers

- **Repeated step 0 failure before rollouts** — both runs `c83f971d-...` and `56cb5701-...` failed at step 0, no rollouts recorded
- **Backend logs required** — likely category `FAILED_UNKNOWN_WORKER_BOOTSTRAP_OR_PLATFORM`; needs Castform backend worker bootstrap logs for both run_ids

## Preserved evidence

- **Run IDs**:
  - `c83f971d-2b2c-42b8-9774-ca64938c1286` (Run 1 / ATL-5B-RESULT, 8 train / 2 eval)
  - `56cb5701-6b3e-424e-b671-fc2efc932aa8` (Run 2 / ATL-6, 16 train / 4 eval)
- **Result JSON files** (preserved, not modified):
  - `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5_cloud_smoke_result.json` (Run 0 / first attempt: upload SUCCESS, launch FAILED on batch_size)
  - `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry_result.json` (Run 1: PASS_CLOUD_SMOKE_LAUNCHED, c83f971d-...)
  - `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy_result.json` (Run 2: PASS_CLOUD_SMOKE_LAUNCHED, 56cb5701-...)
- **Reports**: `reports/ATL5D_SUPPORT_READY_FAILURE_BUNDLE_REPORT.md`, `reports/ATL6C_REPEATED_STEP0_FAILURE_SUPPORT_REPORT.md`, `reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md` (this file)
- **Case page**: `cases/castform-hermes-phase-closer-v0/index.html` (timeline, ATL-5B / ATL-6B / ATL-6C / final closeout section, footer)
- **Case closeout doc**: `cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md`
- **Support request (paste-ready)**: `cases/castform-hermes-phase-closer-v0/CASTFORM_SUPPORT_REQUEST_FINAL.md` + `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md`
- **Validation scripts**: 14 stdlib validators in `scripts/` (validate_jsonl / validate_site / check_secrets / validate_castform_local_scaffold / validate_atl3c_sdk_mapping / validate_atl4a_preflight_scaffold / validate_atl4b_cloud_smoke_config / validate_atl4c_guarded_preflight / validate_atl5_cloud_smoke_result / validate_atl5a_launch_args_fix / validate_atl5b_second_upload_retry_result / validate_atl6_starter_style_redeploy / validate_atl6c_support_request / **validate_case_closeout**)

## Security notes (12/12)

- API key not recorded — only `os.environ` presence check in scripts; no key value ever touched
- API key prefix or fragment not recorded — `cf` + `_` + `J` pattern stays as concat literal in validators only
- Did not commit `.env` — no `.env` file in working tree
- Did not commit `.venv` — `.gitignore` blocks `.venv-castform-local/`
- Did not record credit card data — none in any file
- Did not record cookies — none in any file
- Did not record Authorization headers — none in any file
- Did not record user email — none in any file
- Did not record screenshots — none in any file
- Did not forge root cause — likely category is analytical; no backend log claims
- Did not forge metrics — no rollout / reward / cost numbers invented
- Result JSON `uploaded_payload` blocks contain only blob paths (`envs/...` / `datasets/...`) — no signed URLs, no tokens, no credentials

## Hard-boundary audit (18/18)

| # | Boundary | Status |
|---|----------|--------|
| 1 | Did not call Castform API | OK — only stdlib validators ran (zero network) |
| 2 | Did not visit Castform UI | OK — no `browser_navigate` to `app.castform.com` |
| 3 | Did not upload data | OK — no `upload_training_run` invocation |
| 4 | Did not start training run | OK — no `launch_training_run` invocation |
| 5 | Did not re-run ATL-5B script | OK — file left intact on disk |
| 6 | Did not re-run ATL-6 redeploy script | OK — file left intact on disk |
| 7 | Did not read / print / record `CASTFORM_API_KEY` | OK — only `os.environ` presence checks |
| 8 | Did not create `.env` | OK — no `.env` file in working tree |
| 9 | Did not commit `.venv` | OK — `.gitignore` blocks `.venv-castform-local/` |
| 10 | Did not record credit card / cookie / Authorization header / user email / screenshot | OK — none in any new file |
| 11 | Did not record API key prefix or fragment | OK — concat literal stays in validators only |
| 12 | Did not forge root cause | OK — likely category is analytical; no backend log claims |
| 13 | Did not forge metrics | OK — no rollout / reward / cost numbers invented |
| 14 | Did not delete historical result JSON | OK — 3 result JSONs preserved |
| 15 | Did not delete old run information | OK — `c83f971d-...` and `56cb5701-...` both referenced in closeout docs and case page |
| 16 | Only did local project closeout | OK — no remote calls |
| 17 | Updated page, README, docs, cases.json, reports, validators | OK — see "Created files" + "Modified files" below |
| 18 | Committed and pushed (allowed) | OK — see "Commit hash" + "Push" below |

## Created files (this phase)
| Path | Purpose |
|------|---------|
| `cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md` | Final case closeout doc (status / what tested / successes / failure / ruled out / not yet ruled out / decision / future action / sensitive info exclusion) |
| `cases/castform-hermes-phase-closer-v0/CASTFORM_SUPPORT_REQUEST_FINAL.md` | Paste-ready English support request (short version) for Castform / Castie |
| `reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md` | This report |
| `scripts/validate_case_closeout.py` | stdlib validator — 3 doc files exist / both run_id tokens / `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` / `data/cases.json` Castform case status / 16 secret patterns + 1 forbidden literal scan |

## Modified files (this phase)
| Path | Change |
|------|--------|
| `cases/castform-hermes-phase-closer-v0/index.html` | Added final closeout section · updated page header (lines 65-66) · updated footer |
| `data/cases.json` | `phase` → `CASE-CLOSEOUT` · `status` → `paused pending Castform backend logs` · `updated_at` = 2026-06-13 |
| `README.md` | Updated `## 当前状态` to reflect final closeout |
| `docs/ROADMAP.md` | Added closeout notes: Castform case closed for now · next case: choose another AI tool / platform · Castform can resume only after support / backend logs |

## Commit hash
- see commit message `ATL-CLOSEOUT: Close Castform case pending backend logs` (created by the next step, not yet at report-write time)

## Whether pushed
- see "push" status below — executed after commit

## Next step recommendation
- **Pause project** — no further cloud attempts for now
- **Optionally send** `cases/castform-hermes-phase-closer-v0/CASTFORM_SUPPORT_REQUEST_FINAL.md` (or `ATL6C_SUPPORT_REQUEST.md`) to Castform / Castie
- **Do not run more cloud tests** until Castform backend logs or support feedback are available
- **Future case selection**: choose another AI tool / platform when ready
