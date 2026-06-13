# ATL-6C — Failure Summary

## Current status
FAILED_STEP_0_NO_ROLLOUTS_REPEATED

## Likely category
FAILED_UNKNOWN_WORKER_BOOTSTRAP_OR_PLATFORM

## Ruled out
- missing API key — local validate_env passed; key was present in env at launch time (both runs)
- upload failure — Run 1 upload_succeeded: true (ATL-5B result); Run 2 upload_succeeded: true (ATL-6 result)
- unsupported batch_size — Run 1 launcher_args (post-ATL-5A) and Run 2 launcher_args both exclude batch_size; both launches were accepted by Castform
- fewer than 16 train examples — Run 2 uses 16 train (vs Run 1 8 train); failure persists at 16
- run_tool raising in no-tools env — Run 2 env returns "" without raising NotImplementedError; failure persists with non-raising run_tool
- reward not normalized — Run 2 reward returns float in [0.0, 1.0] (vs Run 1 0~10); failure persists with normalized reward
- env complexity / custom load_dataset override / tools — Run 2 is a no-tools BaseEnv default env
- local validate_env contract — Run 2 VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)
- missing run / missing UI route — both runs visible in Castform UI; both /train/<run_id>?tab=train routes render
- config tab broken — both runs show uploaded env and dataset paths in the config tab

## Not yet ruled out
- remote worker bootstrap failure
- dataset load failure in remote trainer (blob paths visible to worker?)
- env unpickle / import issue in remote trainer (env-cls.pkl / env-metadata.json deserialization)
- trainer backend internal error
- quota / runtime / account-level issue

## UI-visible evidence
### Run 1 (c83f971d-2b2c-42b8-9774-ca64938c1286)
- display name: simple-28de6dd2
- status: failed
- step: 0
- train data: none
- eval data: none
- rollouts: none

### Run 2 (56cb5701-6b3e-424e-b671-fc2efc932aa8)
- actual UI route: /train/56cb5701-6b3e-424e-b671-fc2efc932aa8?tab=train
- display name: simple-c869a30d
- status: failed
- step: 0
- started: about 8 min ago
- train data: no train data available
- train rollouts: no rollouts recorded yet
- eval data: not yet checked
- config tab: uploaded env and dataset paths visible

## Read-only SDK probe result (from ATL-5D, reused for ATL-6C)
- CASTFORM_API_KEY present: true
- no candidate read-only TrainerClient methods printed
- no safe read-only call attempts available
- no status/log endpoint discovered through SDK
- probe did not upload, launch, delete, or mutate anything

## Next action
- paste ATL6C_SUPPORT_REQUEST.md into Castform assistant / Castie support
- request backend worker bootstrap logs for both run_ids
- wait for backend error details
- if the backend returns a root cause, plan ATL-6D root-cause fix
- do not repeat the launch until the root cause is known
