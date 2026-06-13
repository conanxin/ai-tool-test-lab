# ATL-6C — Failure Summary

## Current status
FAILED_STEP_0_NO_ROLLOUTS_REPEATED

## Likely category
FAILED_UNKNOWN_WORKER_BOOTSTRAP_OR_PLATFORM

## Ruled out (between Run 1 and Run 2)
- batch_size launch arg — Run 2 launcher_args do not include batch_size; ATL-5A fix was applied and accepted by Castform
- train dataset too small — Run 2 uses 16 train (vs Run 1 8 train)
- run_tool raise NotImplementedError — Run 2 env returns "" without raising
- reward scale mismatched — Run 2 reward returns float in [0.0, 1.0]
- env complexity — Run 2 is a no-tools starter-style env aligned with Castform's starter task pattern
- env custom load_dataset override — Run 2 uses BaseEnv default
- local validate_env contract — Run 2 VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)
- API key presence — key was present in env at launch time
- upload failure — Run 2 upload_succeeded: true
- missing run — both runs visible in Castform UI
- missing UI route — /train/<run_id>?tab=train renders for both runs

## Not yet ruled out
- run_id c83f971d-2b2c-42b8-9774-ca64938c1286 (Run 1): remote env load failure
- run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2): remote env load failure
- run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2): dataset load failure
- run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2): dependency setup failure
- run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2): trainer bootstrap failure
- run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2): quota / billing / worker internal error
- run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2): env-cls.pkl / env-metadata.json deserialization issue
- run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2): framework compatibility with Qwen/Qwen3.5-4B

## UI-visible evidence
### Run 1 (c83f971d...)
- display name: simple-28de6dd2
- status: failed
- step: 0
- train data: none
- eval data: none
- rollouts: none

### Run 2 (56cb5701...)
- actual UI route: /train/56cb5701-6b3e-424e-b671-fc2efc932aa8?tab=train
- display name: simple-c869a30d
- status: failed
- step: 0
- started: about 8 min ago
- train data: no train data available
- train rollouts: no rollouts recorded yet
- eval data: not yet checked
- no explicit worker logs or traceback visible in screenshots

## Read-only SDK probe result (from ATL-5D, reused for ATL-6C)
- CASTFORM_API_KEY present: true
- no candidate read-only TrainerClient methods printed
- no safe read-only call attempts available
- no status/log endpoint discovered through SDK
- probe did not upload, launch, delete, or mutate anything

## Decision
- Diagnose via Castform backend support, not via further agent-side retry
- No further Castform API / UI access in this phase
- Do not repeat the launch until the root cause is known
