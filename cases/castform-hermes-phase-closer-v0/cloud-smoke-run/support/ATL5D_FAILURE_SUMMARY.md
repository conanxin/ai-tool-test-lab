# ATL-5D — Failure Summary

## Current status
FAILED_STEP_0_NO_ROLLOUTS

## Likely category
FAILED_UNKNOWN_WORKER_BOOTSTRAP

## Ruled out
- missing API key — local validate_env passed; key was present in env at launch time
- upload failure — upload_succeeded: true (ATL-5B result)
- unsupported batch_size — launcher_args no longer include batch_size; ATL-5A fix was applied and accepted by Castform
- missing run — run is visible in the Castform UI (display name simple-28de6dd2, two URLs resolve)
- missing UI route — /train/<run_id>?tab=train, ?tab=eval, ?tab=compare, ?tab=config, ?tab=settings all render

## Not yet ruled out
- run_id c83f971d-2b2c-42b8-9774-ca64938c1286: remote env load failure
- run_id c83f971d-2b2c-42b8-9774-ca64938c1286: dataset load failure
- run_id c83f971d-2b2c-42b8-9774-ca64938c1286: dependency setup failure
- run_id c83f971d-2b2c-42b8-9774-ca64938c1286: trainer bootstrap failure
- run_id c83f971d-2b2c-42b8-9774-ca64938c1286: quota / billing / worker internal error

## UI-visible evidence
- train tab: no train data available
- train rollout deepdive: no rollouts recorded yet
- eval tab: no eval data available
- eval rollout deepdive: no rollouts recorded yet
- compare tab: external gpt-5.4 comparison visible and completed
- compare tab: user model has not generated rollouts yet
- no explicit worker logs or traceback visible in screenshots

## Read-only SDK probe result
- CASTFORM_API_KEY present: true
- no candidate read-only TrainerClient methods printed
- no safe read-only call attempts available
- no status/log endpoint discovered through SDK
- probe did not upload, launch, delete, or mutate anything

## Next action
- paste support request into Castform assistant / support
- wait for backend error details
- if the backend returns a root cause, plan ATL-5E root-cause fix
- do not repeat the launch until the root cause is known
