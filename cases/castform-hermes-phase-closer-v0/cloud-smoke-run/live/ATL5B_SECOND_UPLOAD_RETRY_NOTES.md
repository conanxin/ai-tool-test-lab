# ATL-5B Second Upload Retry Notes

**Date**: 2026-06-13
**Phase**: ATL-5B second upload + launch retry script preparation
**Status**: Script ready · execution not run · awaiting user authorization

## Why ATL-5B is needed

ATL-5 first cloud smoke run produced partial success: `upload_training_run` returned successfully, but `launch_training_run` was rejected by Castform with:

```
JobLaunchError: Unknown launch arg: "batch_size".
Use GET /train/launch-args to see what's accepted.
```

This means we cannot just `launch_training_run` again — even if we corrected the args, the ATL-5 result JSON did **not** save `uploaded_payload` (the env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path returned by `upload_training_run`). Without those, a launch-only retry is impossible. We must re-upload the same dataset with corrected launch args.

## ATL-5 result

- **Local validate_env**: PASS (`VALIDATE_ENV_LOCAL_PASS`)
- **Upload**: SUCCEEDED
- **Launch**: FAILED (`Unknown launch arg: "batch_size"`)
- **`dataset_uploaded`**: true
- **`training_started`**: false
- **`uploaded_payload`**: **missing** — cannot retry launch only

## What changed

- `batch_size` removed from `launcher_args`.
- `learning_rate: 1e-5` added to `launcher_args` (Castform accepted args verified 2026-06-13: `model`, `learning_rate`, `num_epochs`, `group_size`, `max_rollout_len`, `max_turns`, `lora_rank`, `lora_alpha`).
- Result JSON now captures `uploaded_payload` after upload so a future launch-only retry becomes possible.

## ATL-5B plan

- Re-upload the **same** 8-train / 2-eval preview subset (`smoke-train.preview.jsonl` / `smoke-eval.preview.jsonl`).
- Re-launch with the corrected `launcher_args` (no `batch_size`, with `learning_rate`).
- Allowed calls: exactly **1** `upload_training_run` and **1** `launch_training_run`.
- No full 49-row upload.
- No repeated launch retries.

## Authorization gate

User must set in their local WSL shell **before** running the retry script:

```bash
export ATL_USER_AUTHORIZATION=*** AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY"
export ATL_ALLOW_CASTFORM_UPLOAD="YES"
export ATL_ALLOW_CASTFORM_LAUNCH="YES"
read -s CASTFORM_API_KEY && export CASTFORM_API_KEY
```

Any deviation from the exact authorization string → `BLOCKED_BY_MISSING_USER_AUTHORIZATION`, exit 1, no API call.

## Hard rules (re-stated)

- **No API key recorded.** `api_key_recorded` is `false` in the result JSON.
- **No API key printed.** Only a 4-character mask (`cf-t...`) appears in the gate summary.
- **No full 49-row upload.** Only the 8/2 preview subset.
- **No repeated launch.** If launch fails, the script exits; it does not auto-retry.
- **No .env file.** API key lives only in the shell environment for the duration of the run.
- **No commit of `.venv-castform-local/`** or any local credentials.

## Files

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py` — retry script (writes to `atl5b_second_upload_launch_retry_result.json`; preserves ATL-5 history).
- `scripts/validate_atl5b_second_upload_retry_result.py` — std-lib validator. Prints `SKIPPED_RESULT_NOT_PRESENT` when no result file (script-prep phase), `PASS` / `FAIL` otherwise.

## Next step

Run from local WSL shell:

```bash
cd /mnt/d/AI/ai-tool-test-lab
.venv-castform-local/bin/python cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py
python3 scripts/validate_atl5b_second_upload_retry_result.py
```