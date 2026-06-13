# ATL-6 — Starter-Style Redeploy Notes

## Why we need ATL-6

The ATL-5B run (`run_id c83f971d-2b2c-42b8-9774-ca64938c1286`) launched
successfully but **failed at step 0** before producing any train / eval /
rollout data. There was no UI-visible traceback, the SDK had no read-only
status/log method (`NO_READ_ONLY_STATUS_METHOD_FOUND`), and the support-ready
failure bundle (`ATL5D_SUPPORT_REQUEST.md`) has not yet returned a backend
root cause.

ATL-6 stops waiting for the backend log and pivots to a path that is
**maximally likely to produce a real rollout on the cloud trainer**: the
starter-task path.

## Starter-task lessons (applied)

The Castform Web App ships with example "Build your own" starter tasks. The
relevant lessons are:

- **Simple, no-tools environment.** Starter tasks don't use RAG, agent
  traces, or external tools. The minimal env surface is
  `BaseEnv + dataset_preprocess + list_tools=[] + run_tool="" + compute_reward`.
  Less custom code in the cloud trainer = less surface area for the
  bootstrap to fail.
- **Enough dataset examples.** Starter tasks ship with hundreds of examples
  and produce real rollouts in minutes. The previous 8 train / 2 eval
  preview may be too sparse to trigger the trainer's bootstrap path. ATL-6
  doubles the preview to 16 train / 4 eval.
- **Simple, deterministic reward.** Starter tasks use rule-based rewards
  (no LLM judge, no embedding lookup, no network call). ATL-6 normalises
  the reward to 0.0~1.0 and keeps it offline-only.

## Current old run (preserved as historical evidence, NOT touched)

- `run_id`: `c83f971d-2b2c-42b8-9774-ca64938c1286`
- actual UI URL: `https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train`
- documented experiment URL: `https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286` (returns Not Found)
- status: `failed`
- step: `0`
- train data: none
- eval data: none
- rollouts: none

This run is **never deleted, never re-launched, never re-referenced** by the
ATL-6 redeploy script. It is preserved on the Castform side as historical
evidence.

## Fix points (vs ATL-5 / ATL-5B)

1. **16 train / 4 eval preview subset** (vs 8 train / 2 eval in ATL-5B; never
   uploads the full 49-row dataset). The subset is produced by
   `prepare_starter_style_subset.py` from the existing ATL-2 redacted
   JSONL samples.
2. **`run_tool` returns `""`** and never raises `NotImplementedError`. The
   previous environment raised `NotImplementedError` from `run_tool` even
   though `list_tools` returned `[]` — ATL-6 returns `""` instead so the
   no-tools contract is unambiguously safe.
3. **Reward normalised to 0.0~1.0** via `reward_starter_style.py`. The
   grader returns `{format, coverage, score}` with each component clamped
   to `[0.0, 1.0]`. Secret-pattern detection forces `score = 0.0`
   (defensive).
4. **`batch_size` removed** from `launcher_args`. The accepted args are
   exactly: `model`, `learning_rate`, `num_epochs`, `group_size`,
   `max_rollout_len`, `max_turns`, `lora_rank`, `lora_alpha`.
   `learning_rate: 1e-5` is present.
5. **New run_name**: `hermes-phase-closer-starter-style-atl6` (independent
   of ATL-5 `hermes-phase-closer-smoke` and ATL-5B
   `hermes-phase-closer-smoke-atl5b`).
6. **No custom `load_dataset` override** — closer to `BaseEnv` default
   behaviour (less custom code shipped to the cloud trainer).
7. **Independent result file**: `atl6_starter_style_redeploy_result.json`
   does not overwrite `atl5_cloud_smoke_result.json` or
   `atl5b_second_upload_launch_retry_result.json`.

## Authorization statement

The redeploy script `atl6_starter_style_redeploy.py` requires the user to
set the following environment variables explicitly:

```
CASTFORM_API_KEY=<provided-by-user>
ATL_ALLOW_CASTFORM_UPLOAD=YES
ATL_ALLOW_CASTFORM_LAUNCH=YES
ATL_USER_AUTHORIZATION="I AUTHORIZE ATL-6 STARTER STYLE REDEPLOY"
```

The script will refuse and write a sanitized blocked result if any of these
is missing or mismatched. The script never prints or persists the value
of `CASTFORM_API_KEY`; the gate log only reports `present: True|False`.

## Not done in this phase

- The redeploy script is **not run by the agent** during ATL-6A
  preparation. The agent only writes the script, the env, the reward, the
  validator, and the page/json/README/report updates.
- Real Castform API calls (`upload_training_run`, `launch_training_run`)
  are **executed by the user** in their local WSL shell after confirming
  the gates.
- The old failed run is **not deleted**.
- The new run is **not duplicated** beyond a single upload + single launch
  attempt (no auto-retry).
- A previously launched run is **never re-launched** by this script.

## How to execute (user manual step)

```bash
cd /mnt/d/AI/ai-tool-test-lab
export CASTFORM_API_KEY=<your-key>
export ATL_ALLOW_CASTFORM_UPLOAD=YES
export ATL_ALLOW_CASTFORM_LAUNCH=YES
export ATL_USER_AUTHORIZATION=*** AUTHORIZE ATL-6 STARTER STYLE REDEPLOY"
.venv-castform-local/bin/python \
  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py
```

The script writes its result to
`cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy_result.json`.
