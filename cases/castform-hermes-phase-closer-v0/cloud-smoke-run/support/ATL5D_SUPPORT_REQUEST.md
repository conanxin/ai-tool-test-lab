# ATL-5D — Castform Support Request

## Summary
A minimal SDK training run launched successfully but failed at step 0 before any rollout was recorded. The run is visible in the Castform UI, the config tab shows full trainer/env/dataset wiring, and no UI-visible error or traceback is exposed. This bundle is the only request we need to send to Castform support / Castie to get the backend worker log for this run.

## Run Identity
- run_id: c83f971d-2b2c-42b8-9774-ca64938c1286
- documented experiment URL: https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286
- actual UI URL: https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train
- display name: simple-28de6dd2
- status: failed
- step: 0
- status tag: FAILED_STEP_0_NO_ROLLOUTS

## What Worked
- local validate_env passed
- upload_training_run succeeded
- launch_training_run succeeded
- base model: Qwen/Qwen3.5-4B
- train samples: 8
- eval samples: 2
- no tools
- corrected launcher_args were accepted
- config tab shows env_cls_path, env_metadata_path, train_dataset_path, eval_dataset_path
- config tab shows environment code and trainer args
- API key was not recorded

## What Failed
- training step never advanced past 0
- train tab: no train data available
- train rollout deepdive: no rollouts recorded yet
- eval tab: no eval data available
- eval rollout deepdive: no rollouts recorded yet
- compare tab: external gpt-5.4 comparison visible and completed
- compare tab: user model has not generated rollouts yet
- no explicit worker logs or traceback visible in screenshots
- no read-only status/log method discovered in the SDK

## Requested Information
- the full backend worker log for run c83f971d-2b2c-42b8-9774-ca64938c1286
- the specific error / exception that caused the run to stop at step 0
- the rollout counter, env-load event, and dataset-load event from the worker bootstrap
- confirmation of whether the failure is in remote env load, dataset load, dependency setup, trainer bootstrap, or quota / billing / internal worker error
- suggested next action (root-cause fix, config change, or quota change) so the next retry can succeed

## Privacy / Scope Notes
- This bundle does not include the Castform API key, the API key prefix, the API key fragment, a credit card, a cookie, an Authorization header, a user email, or a private screenshot.
- The displayed run_id, the two URLs, and the displayed trainer/env/dataset path fields come from the public Castform UI and are not secrets.
- The user has not retried the launch after observing step 0, and is not requesting a quota change as part of this bundle.
