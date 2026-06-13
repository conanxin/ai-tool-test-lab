# ATL-5A Launch Args Fix Notes

**Date**: 2026-06-13
**Phase**: ATL-5A
**Status**: UPLOAD_DONE_LAUNCH_FAILED → launch args fixed, uploaded_payload capture added, awaiting ATL-5B authorization

## ATL-5 First Run Result

- **local_validate_env**: PASS (`VALIDATE_ENV_LOCAL_PASS`)
- **upload**: **SUCCEEDED** (dataset uploaded to Castform)
- **launch**: **FAILED**

## Failure Reason

```
launch_training_run raised: JobLaunchError: Unknown launch arg: "batch_size".
Use GET /train/launch-args to see what's accepted.
```

## Castform Accepted Launch Args Schema

**Required payload fields from upload**:
- `env_cls_path`
- `env_metadata_path`
- `train_dataset_path`
- `eval_dataset_path`

**Accepted launcher args**:
- `model`
- `learning_rate`
- `num_epochs`
- `group_size`
- `max_rollout_len`
- `max_turns`
- `lora_rank`
- `lora_alpha`

**Rejected launcher arg**:
- `batch_size` — removed in ATL-5A fix

## Corrected launcher_args

```json
{
  "model": "Qwen/Qwen3.5-4B",
  "learning_rate": 1e-5,
  "num_epochs": 1,
  "group_size": 2,
  "max_rollout_len": 512,
  "max_turns": 1,
  "lora_rank": 16,
  "lora_alpha": 32
}
```

## Upload Metadata Missing

Original `atl5_cloud_smoke_result.json` did **not** contain `uploaded_payload`.

- No `env_cls_path`
- No `env_metadata_path`
- No `train_dataset_path`
- No `eval_dataset_path`

This means a **launch-only retry is blocked** — we cannot re-run `launch_training_run` without the uploaded metadata.

## ATL-5A Script Changes

1. **Removed** `batch_size` from `launcher_args`
2. **Added** `learning_rate: 1e-5` to `launcher_args`
3. **Added** `uploaded_payload` capture after `upload_training_run` succeeds
4. **Sanitized** `uploaded_payload` to only keep path-like metadata fields (no API key, no auth)

## Next Possible Phase

**ATL-5B — Second Upload and Launch Retry**

Requires:
- Re-upload the same 8 train / 2 eval preview subset
- Re-launch with corrected `launcher_args`

## ATL-5B Authorization Requirement

User must explicitly say:

```
I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY
```

Without this exact authorization, `atl5b_second_upload_retry_guard.py` will refuse to proceed.

## Hard Boundaries (ATL-5A)

- No API call in ATL-5A
- No upload in ATL-5A
- No launch retry in ATL-5A
- No fake success
- `dataset_uploaded` stays `true` (first upload succeeded)
- `training_started` stays `false` (first launch failed)
