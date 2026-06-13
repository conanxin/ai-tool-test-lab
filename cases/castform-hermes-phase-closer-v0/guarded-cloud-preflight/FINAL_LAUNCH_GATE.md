# Final Launch Gate — ATL-5 Real Cloud Smoke Run

**Phase**: ATL-5 (future, not ATL-4C)
**Status**: Gate definition only — ATL-4C does NOT satisfy these gates

This file defines the **minimum checklist** that must be green before any real Castform cloud smoke run is allowed. ATL-4C prepares these gates but does **not** satisfy them.

---

## Mandatory Gates (ALL must be green)

### 1. User Explicit Authorization

- [ ] User has sent a message (Telegram or equivalent) containing the exact phrase:
  **"I AUTHORIZE ATL-5 CLOUD SMOKE RUN"**
- [ ] User has confirmed they understand this will consume Castform credit ($50 free credit currently visible).
- [ ] User has confirmed they understand the risk of partial billing / charge visibility unknowns.

### 2. API Key Runtime Injection

- [ ] `CASTFORM_API_KEY` is set in the current shell environment only.
- [ ] The key was injected via `read -s CASTFORM_API_KEY` + `export CASTFORM_API_KEY` (not written to a file in this repo).
- [ ] The key is not empty and does not contain whitespace.
- [ ] The key is not committed to git, not in `.env`, not in any markdown file.

### 3. Environment Variable Authorization

- [ ] `ATL_ALLOW_CASTFORM_UPLOAD` is set to `"YES"` in the current shell.
- [ ] `ATL_ALLOW_CASTFORM_LAUNCH` is set to `"YES"` in the current shell.
- [ ] Both variables were set by the user explicitly (not by any script or automation).

### 4. Configuration Lock

- [ ] `guarded_cloud_preflight_config.json` has been updated by the user (not by the agent) to:
  - `cloud_launch_allowed: true`
  - `current_readiness: "READY_FOR_CLOUD_SMOKE_RUN"`
  - `actual_upload_allowed_in_this_phase: true`
  - `actual_launch_allowed_in_this_phase: true`
- [ ] The config update was committed by the user (not by the agent) with a message containing "ATL-5".

### 5. Smoke Run Parameters

- [ ] Run name: `hermes-phase-closer-smoke`
- [ ] Base model: `Qwen/Qwen3.5-4B`
- [ ] Train samples: 8 (from `smoke-train.preview.jsonl`)
- [ ] Eval samples: 2 (from `smoke-eval.preview.jsonl`)
- [ ] Selected path: `build_your_own_sdk`
- [ ] Tools: none
- [ ] External network tools: none
- [ ] Max turns: 1 (minimal)

### 6. Risk Acknowledgment

- [ ] User confirms they still accept that billing / auto-charge / cost estimate / run controls / data policy are partially unknown.
- [ ] User confirms they understand `upload_training_run` will upload the environment and dataset to Castform's cloud storage.
- [ ] User confirms they understand `launch_training_run` will start a Castform training job that consumes GPU time and credit.
- [ ] User confirms they know how to cancel the run if something goes wrong (or accepts the risk of not knowing).
- [ ] User confirms they know how to delete the uploaded dataset if needed (or accepts the risk of not knowing).

### 7. Pre-Launch Verification

- [ ] `validate_jsonl.py` PASS
- [ ] `validate_site.py` PASS
- [ ] `check_secrets.py` PASS
- [ ] `validate_castform_local_scaffold.py` PASS
- [ ] `validate_atl3c_sdk_mapping.py` PASS
- [ ] `validate_atl4a_preflight_scaffold.py` PASS
- [ ] `validate_atl4b_cloud_smoke_config.py` PASS
- [ ] `validate_atl4c_guarded_preflight.py` PASS
- [ ] `guarded_upload_preflight.py` dry-run PASS (with env vars set but `actual_upload_allowed_in_this_phase: false` — it should still refuse)
- [ ] `guarded_launch_preflight.py` dry-run PASS (with env vars set but `actual_launch_allowed_in_this_phase: false` — it should still refuse)

---

## What Happens If Any Gate Is Red

If ANY of the above gates is not green, the launch is **blocked**. The `guarded_upload_preflight.py` and `guarded_launch_preflight.py` scripts will:

1. Print the blocked banner.
2. List which gates are red.
3. Exit non-zero.
4. Not call any Castform API.

## What ATL-4C Does With This File

ATL-4C creates this file as a **definition** but does **not** check any boxes. The checkboxes are for the user to fill in ATL-5. ATL-4C's job is to make sure the gates are well-defined, well-documented, and enforced by code.

## Current Status (ATL-4C)

- All gates: **NOT CHECKED** (by design)
- `cloud_launch_allowed`: `false`
- `current_readiness`: `BLOCKED_BY_UNCLEAR_CHARGES`
- Next phase: ATL-5 — only if user explicitly authorizes and satisfies all gates
