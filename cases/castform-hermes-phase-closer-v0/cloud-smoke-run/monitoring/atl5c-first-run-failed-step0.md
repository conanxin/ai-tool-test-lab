# ATL-5C — First Castform Run Failed at Step 0

**Date observed**: 2026-06-13
**Phase**: ATL-5C (first-run monitor)
**Status**: **FAILED_STEP_0_NO_ROLLOUTS**
**Project path**: `/mnt/d/AI/ai-tool-test-lab`

## Run identity (user-observed via Castform UI)

| Field | Value |
|-------|-------|
| `run_id` | `c83f971d-2b2c-42b8-9774-ca64938c1286` |
| documented experiment URL | `https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286` (Not Found in UI) |
| actual UI URL | `https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train` |
| display name | `simple-28de6dd2` |
| status | **failed** |
| step | **0** |
| started | about 39–41 min ago |

## Train / eval / compare observations

| Tab | Observation |
|-----|-------------|
| train tab | **no train data available** |
| train rollout deepdive | **no rollouts recorded yet** |
| eval tab | **no eval data available** |
| eval rollout deepdive | **no rollouts recorded yet** |
| compare tab | **external gpt-5.4 batch eval completed** |
| compare tab | **your model has not generated rollouts yet** |
| compare reward for gpt-5.4 | 10.000 |
| compare inference cost shown | about $0.01/request |

## Config observations

| Field | Visible | Value |
|-------|---------|-------|
| config tab | YES | — |
| model | YES | `Qwen/Qwen3.5-4B` |
| `env_cls_path` | YES | (set by upload step) |
| `env_metadata_path` | YES | (set by upload step) |
| `train_dataset_path` | YES | (set by upload step) |
| `eval_dataset_path` | YES | (set by upload step) |
| LoRA save/load paths | YES | (set by launch step) |
| `lr` | YES | 0.00001 |
| `max_turns` | YES | 1 |
| `n_samples_per_prompt` | YES | 2 |
| `n_samples_per_eval_prompt` | YES | 2 |
| `num_epoch` | YES | 1 |
| rollout / eval max response length | YES | 512 |
| environment code | YES | (rendered) |
| `dataset_preprocess` / `load_dataset` / `list_tools` / `run_tool` / `compute_reward` | YES | (rendered) |

## Settings observations

| Field | Visible |
|-------|---------|
| settings tab | YES |
| download checkpoint button | YES |
| Hugging Face connect button | YES |
| external batch eval section | YES |
| delete training run button | YES |
| explicit worker logs (in screenshots) | NO |

## Failure reason visibility

- **failure reason visible**: **NO**
- **no UI-visible traceback or worker log** has been captured yet
- exact root cause remains unknown

## Interpretation

- ATL-5B launch succeeded and the run exists in the Castform training runs list.
- The documented `/experiments/<run_id>` path returned **Not Found**, but `/train/<run_id>?tab=train` works — the documented path is a stale reference; the live URL is the `/train/<run_id>` form with `?tab=train` selecting the train tab.
- The run **failed before the first model rollout** (step 0, no rollouts recorded on either train or eval side).
- The external GPT-5.4 batch eval *did* complete and produced a reward score (10.000) plus per-request cost ($0.01/request), but our own model never reached the rollout stage.
- We do not have a UI-visible traceback, worker log, or backend error message — only the high-level `failed` status at step 0.
- **Current monitoring status**: `FAILED_STEP_0_NO_ROLLOUTS`
- **Exact root cause**: unknown at this point.

## Next action (in-scope for ATL-5C only)

- **Read-only SDK/API status probe** — not a launch, not an upload, not a UI scrape. The probe script is at `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c_readonly_status_probe.py` and **must be run by the user in their local WSL shell with `CASTFORM_API_KEY`**. Agent does NOT run it.
- The probe introspects `benchmax.platform.client.TrainerClient` for read-only candidate methods (`get_*` / `list_*` / `read_*` / `describe_*` / `status_*` / `fetch_*`) and refuses to call anything that looks destructive (no `delete_*` / `cancel_*` / `update_*` / `create_*` / `upload_*` / `launch_*` / `download_*` / `train_*` / `run_*`).
- If no read-only candidate exists, the probe prints `NO_READ_ONLY_STATUS_METHOD_FOUND` and exits 0.
- All output is sanitized for `cf_*` / `sk-*` / `Bearer ` / `Authorization:` / `Cookie:` patterns.

## Hard boundaries (ATL-5C agent phase)

- agent did **not** call Castform API
- agent did **not** access Castform UI
- agent did **not** upload data
- agent did **not** start training
- agent did **not** re-run `atl5b_second_upload_launch_retry.py`
- agent did **not** read / print / record `CASTFORM_API_KEY`
- agent did **not** create `.env`
- agent did **not** commit `.venv`
- agent did **not** record credit card / cookie / Authorization header / user email / screenshots
- agent did **not** record API key prefix or fragment
- agent did **not** fabricate failure reason
- agent did **not** fabricate metrics
- only the user-observed (sanitized) results are recorded

## Next-step branches

- If the probe surfaces a backend error / traceback → enter **ATL-5D — failure root cause record**
- If the probe prints `NO_READ_ONLY_STATUS_METHOD_FOUND` → enter **ATL-5E — support-ready failure bundle**
