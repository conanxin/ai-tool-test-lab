# ATL-6C — Castform Support Request

## Summary
Two minimal SDK training runs launched successfully but failed at step 0 before any rollout was recorded. The second run used a starter-style environment aligned with Castform's starter task pattern.

## Run 1 (ATL-5B retry)
- run_id: c83f971d-2b2c-42b8-9774-ca64938c1286
- actual UI route: /train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train
- status: failed
- step: 0
- train data: none
- eval data: none
- rollouts: none

## Run 2 (ATL-6 starter-style redeploy)
- run_id: 56cb5701-6b3e-424e-b671-fc2efc932aa8
- actual UI route: /train/56cb5701-6b3e-424e-b671-fc2efc932aa8?tab=train
- display name: simple-c869a30d
- status: failed
- step: 0
- train data: none
- eval data: not yet checked
- rollouts: none

## Configuration (Run 2)
- base_model: Qwen/Qwen3.5-4B
- train_samples: 16
- eval_samples: 4
- launcher_args (only accepted args):
  - model: Qwen/Qwen3.5-4B
  - learning_rate: 1e-5
  - num_epochs: 1
  - group_size: 2
  - max_rollout_len: 512
  - max_turns: 1
  - lora_rank: 16
  - lora_alpha: 32
- batch_size: not used (removed after ATL-5A launcher_args fix)
- env: HermesPhaseCloserStarterStyleEnv (no custom load_dataset override; BaseEnv default; list_tools=[]; run_tool returns "" without raising; reward normalized 0.0~1.0)
- env_cls_path: cases.castform-hermes-phase-closer-v0.starter-style-redeploy.environment_starter_style:HermesPhaseCloserStarterStyleEnv
- run_name: hermes-phase-closer-starter-style-atl6

## Local Validation (Run 2)
- local_validate_env_result: VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)
- validate_env invoked with: local=True, api_key=None
- no network egress
- contract check: 5 train + 2 eval rows, env_cls_path resolvable, run_tool returns "", reward returns float in [0.0, 1.0]

## Upload Artifacts (Run 2, recorded locally, not requested from Castform)
- env_cls_path: envs/hermes-phase-closer-starter-style-atl6/ab31b4b4b99d38be/env-cls.pkl
- env_metadata_path: envs/hermes-phase-closer-starter-style-atl6/ab31b4b4b99d38be/env-metadata.json
- train_dataset_path: datasets/hermes-phase-closer-starter-style-atl6/c9433eb4/train.jsonl
- eval_dataset_path: datasets/hermes-phase-closer-starter-style-atl6/c9433eb4/eval.jsonl

(Paths are blob storage paths as returned by `upload_training_run`. No signed URLs, tokens, or credentials are stored in the local result JSON.)

## What was ruled out (between Run 1 and Run 2)
- batch_size launch arg rejected by platform — Run 2 does not use batch_size
- train dataset too small (8 train in Run 1) — Run 2 uses 16 train
- run_tool raise NotImplementedError — Run 2 env returns "" instead
- reward scale mismatched (0~10) — Run 2 reward returns float in [0.0, 1.0]
- env complexity (custom load_dataset override, tools, multi-step) — Run 2 is a no-tools starter-style env, BaseEnv default

Despite these changes, Run 2 still failed at step 0 with no rollouts, matching the failure shape of Run 1.

## What we need from Castform
1. Backend worker bootstrap logs for run_id c83f971d-2b2c-42b8-9774-ca64938c1286 (Run 1) — anything that explains why the worker did not record any train data or rollout.
2. Backend worker bootstrap logs for run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8 (Run 2) — same as above.
3. Confirmation of:
   - Whether the env_cls_path was successfully loaded by the worker.
   - Whether the env_metadata_path JSON was parsed (env_name, framework, env_clique_id, dataset reference).
   - Whether the train_dataset_path / eval_dataset_path blobs were actually visible to the worker.
   - Whether there were any platform-side validation errors (e.g. env-cls.pkl deserialization, env-metadata schema, framework compatibility with Qwen3.5-4B).
   - Whether the failure occurred before worker startup, during worker startup, or immediately after the first rollout attempt.
4. Any minimal-known-good starter task recipe (env code, reward code, dataset format, launcher_args) that we can use as a binary-search reference.

## What we can provide back to Castform
- Local result JSON for Run 2: cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy_result.json (no credentials, no tokens, no Authorization headers, no API key prefix)
- Local env code: cases/castform-hermes-phase-closer-v0/starter-style-redeploy/environment_starter_style.py
- Local reward code: cases/castform-hermes-phase-closer-v0/starter-style-redeploy/reward_starter_style.py
- Local dataset samples: starter-train.preview.jsonl (16 rows) / starter-eval.preview.jsonl (4 rows)
- All validation scripts and their PASS output

## Local environment context
- Castform SDK is invoked via Python 3 in a project-local virtualenv (.venv-castform-local, not committed).
- The redeploy script checks 4 gates before any Castform call: API key presence, ATL_ALLOW_CASTFORM_UPLOAD=YES, ATL_ALLOW_CASTFORM_LAUNCH=YES, ATL_USER_AUTHORIZATION match.
- All `upload_training_run` and `launch_training_run` invocations are wrapped in try/except and write a sanitized result JSON on any error.

## Status
- Phase: ATL-6C
- Local state: FAILED_STEP_0_NO_ROLLOUTS_REPEATED
- Likely category: FAILED_UNKNOWN_WORKER_BOOTSTRAP_OR_PLATFORM
- Next action: send this support request to Castform; no further agent-side action until backend logs are returned.
