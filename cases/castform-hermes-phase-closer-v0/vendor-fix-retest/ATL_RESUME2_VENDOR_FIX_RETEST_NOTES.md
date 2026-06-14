# ATL-RESUME-2 Vendor-Fix Retest Notes

## Context

Castform founder Girish confirmed the previous failure (ATL-5B Run 1 + ATL-6 Run 2 both step-0 failed before any rollout) was due to a raw data dict causing incompatibilities with the Castform trainer.

## Vendor Fix Summary

- vendor fix: received
- root cause confirmed: raw data dict trainer incompatibility
- $100 extra credits added to the account
- case status moved from `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` → `VENDOR_FIX_RECEIVED_RETEST_PENDING`

## Retest Goal

Verify whether the step-0 failure is fixed after Castform's vendor-side patch. Specifically: confirm that a fresh, independent training run progresses beyond step 0 and produces real rollout data.

## Expected Signal (Success)

- run progresses beyond step 0
- train data and eval data appear in the run output
- rollouts appear (reward computed on real completions)
- run terminates in `completed` state (not `failed`)

## Expected Signal (Still Broken)

- run still `failed` at step 0 with same shape as ATL-5B / ATL-6
- in that case: stop local retry, append vendor-fix context to a new dual-run support bundle, ask Castform backend for both old run_ids plus the new retest run_id

## Configuration

Reuses the ATL-6 starter-style configuration (validated local):

- 16 train / 4 eval preview subset (`../starter-style-redeploy/starter-{train,eval}.preview.jsonl`)
- Qwen/Qwen3.5-4B
- `HermesPhaseCloserStarterStyleEnv` (no-tools, `list_tools=[]`, `run_tool=""` no raise, 0.0~1.0 reward)
- no custom `load_dataset` override (BaseEnv default)
- `learning_rate: 1e-5` (no `batch_size`)
- `run_name`: `hermes-phase-closer-vendor-fix-retest` (fresh, does not collide with ATL-5B `...-atl5b` or ATL-6 `...-atl6`)
- result file: `atl_resume2_vendor_fix_retest_result.json` (separate from ATL-5 / ATL-5B / ATL-6 result JSON)

## Required Authorization

```
export ATL_USER_AUTHORIZATION="I AUTHORIZE ATL-RESUME-2 CASTFORM RETEST AFTER VENDOR FIX"
export ATL_ALLOW_CASTFORM_UPLOAD="YES"
export ATL_ALLOW_CASTFORM_LAUNCH="YES"
read -s CASTFORM_API_KEY && export CASTFORM_API_KEY
```

Any deviation from the exact authorization string → script writes a sanitized blocked result and exits 1.

## Hard Rules (inherited from ATL-6A + ATL-CLOSEOUT)

- 1 upload_training_run only
- 1 launch_training_run only
- only the 16/4 preview subset (no full 49-row upload)
- no RAG corpus / Agent Traces / tools
- no `.env` creation
- no API key written to disk
- no API key printed (only `present: True|False`; no prefix / fragment)
- no auto-retry on failure
- stop on billing/credit/quota error
- stop on upload success + launch failure (do not retry)
- the agent does NOT run this script; user runs it from local WSL

## Old Runs Preserved (NOT Reused)

- Run 1: `c83f971d-2b2c-42b8-9774-ca64938c1286` (ATL-5B result) — preserved as audit trail
- Run 2: `56cb5701-6b3e-424e-b671-fc2efc932aa8` (ATL-6 result) — preserved as audit trail

Both old run_ids are referenced only in audit-trail comments inside this script and inside the result JSON's `env_fix_points`. They are NEVER referenced as input to a new launch.

## Sensitive Information Exclusion

This file does NOT include:

- API key
- API key prefix or fragment
- Authorization header
- Cookie
- user email
- screenshot
- credit card information

## Next Step

User runs the script from local WSL with explicit authorization. Agent does not run the script, does not call the API, does not upload data, does not start training.
