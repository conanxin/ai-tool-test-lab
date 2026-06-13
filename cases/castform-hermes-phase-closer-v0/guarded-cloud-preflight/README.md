# Castform Guarded Cloud Smoke Preflight — ATL-4C

**Phase**: ATL-4C
**Status**: Guarded preflight only — NOT a real cloud smoke run
**Date**: 2026-06-13
**Baseline**: commit `68fb302` (ATL-4A-CREDIT-FILL) · `b364bb7` (ATL-4B-CONFIG) · `ff22241` (ATL-4A) · `5f06de9` (ATL-3C)

## What ATL-4C Is

ATL-4C is a **guarded preflight** phase. It prepares the final guarded scripts and gates that will be used in ATL-5 (real cloud smoke run), but **does not execute any of them** in this phase.

This phase is **not** a real cloud smoke run. It does NOT call the Castform API, does NOT upload any data, does NOT start any training run, does NOT create any API key, and does NOT use a real `CASTFORM_API_KEY`.

## What ATL-4C Is NOT

- It is NOT a real `upload_training_run` call.
- It is NOT a real `launch_training_run` call.
- It is NOT a real `TrainerClient.launch_training_run` call.
- It is NOT a "we are about to launch" signal.
- It is NOT a fabricated success.

## Hard Boundaries (unchanged from ATL-4B-CONFIG)

1. No Castform API call.
2. No data upload.
3. No training run start.
4. No API key creation.
5. No real `CASTFORM_API_KEY` ever written to repo or `.env`.
6. No `.env` file created in this project.
7. No `.env`, token, API key, Telegram bot token, or private cookie read or committed.
8. No user email recorded.
9. No credit card info recorded.
10. No screenshots committed.
11. No `upload_training_run` executed.
12. No `launch_training_run` executed.
13. No `TrainerClient.launch_training_run` executed.
14. No model training.
15. No fabricated cloud smoke run success.
16. `cloud_launch_allowed` stays `false` in this phase.
17. `current_readiness` stays `BLOCKED_BY_UNCLEAR_CHARGES` in this phase.
18. Allowed: guarded scripts, docs, gate definitions, and this report.
19. Allowed: `git commit` and `git push` of the guarded artifacts.

## Guarded Upload / Launch Architecture

Castform real training launch is a two-step process:

1. **upload_training_run**: Uploads the environment (Python module) and dataset (JSONL) to Castform.
2. **TrainerClient.launch_training_run**: Starts the actual training job on Castform's GPU infrastructure.

Both are **dangerous actions** (consume credit, start compute, create cloud state). ATL-4C wraps them in **dual gates**:

### Gate 1: Environment Variable Authorization

Before any upload or launch script can proceed, the user must explicitly set three environment variables in their local shell:

```bash
export CASTFORM_API_KEY="<redacted-at-source>"
export ATL_ALLOW_CASTFORM_UPLOAD="YES"
export ATL_ALLOW_CASTFORM_LAUNCH="YES"
```

- `CASTFORM_API_KEY`: The real API key. Must be injected at runtime only. Never written to a file in this repo.
- `ATL_ALLOW_CASTFORM_UPLOAD`: Explicit user authorization for the upload step.
- `ATL_ALLOW_CASTFORM_LAUNCH`: Explicit user authorization for the launch step.

If any of these three variables is missing or does not match the expected value, the script **must refuse to continue** and exit non-zero.

### Gate 2: Script-Level Guard

Each script (`guarded_upload_preflight.py`, `guarded_launch_preflight.py`) implements its own guard:

- Default behavior: **REFUSE** the action, print the blocked banner, exit 1.
- The script checks the environment variables.
- The script checks `cloud_launch_allowed` in `guarded_cloud_preflight_config.json` (must be `false` in ATL-4C).
- The script checks `current_readiness` in `guarded_cloud_preflight_config.json` (must be `BLOCKED_BY_UNCLEAR_CHARGES` in ATL-4C).
- Even if all environment variables are present, the script still refuses in ATL-4C because `actual_upload_allowed_in_this_phase = false` and `actual_launch_allowed_in_this_phase = false`.

## Why the Dual Gate Design

- **Environment variable gate**: Prevents accidental execution if the user runs the script without thinking. The user must explicitly type `export ATL_ALLOW_CASTFORM_UPLOAD="YES"` — this is a deliberate act of authorization.
- **Script-level gate**: Prevents execution even if the environment variables are set. The script has its own `ALLOWED` flag that is `false` by default. Only ATL-5 (or a future phase) can flip this flag after the user provides an explicit written authorization.
- **Config-level gate**: `guarded_cloud_preflight_config.json` has `cloud_launch_allowed = false` and `current_readiness = BLOCKED_BY_UNCLEAR_CHARGES`. This is a machine-readable tripwire that validators can check.

## API Key Handling (ATL-5 only)

- ATL-4C does **not** need an API key.
- ATL-5 may need an API key, but only if the user explicitly authorizes a real cloud smoke run.
- The API key must be injected via a temporary shell environment variable:
  ```bash
  read -s CASTFORM_API_KEY
  export CASTFORM_API_KEY
  ```
- The `read -s` command prevents the key from appearing in shell history.
- The key must never be written to a file in this repo, never committed, never sent to Telegram, never pasted into markdown.
- See `API_KEY_RUNTIME_ONLY.md` for the full rules.

## Files In This Directory

- `guarded_cloud_preflight_config.json` — machine-readable guarded config (checked by validators).
- `README.md` — this file.
- `API_KEY_RUNTIME_ONLY.md` — API key handling rules for ATL-5.
- `FINAL_LAUNCH_GATE.md` — The final launch gate checklist (must be green before ATL-5).
- `guarded_upload_preflight.py` — Guarded upload script (default = refuse).
- `guarded_launch_preflight.py` — Guarded launch script (default = refuse).
- `guarded_preflight_validator.py` — Validator for the guarded preflight artifacts.

## Current Status

- `cloud_launch_allowed`: `false`
- `current_readiness`: `BLOCKED_BY_UNCLEAR_CHARGES`
- `user_declared_readiness`: `READY_FOR_CLOUD_SMOKE_RUN` (from ATL-4A-CREDIT-FILL)
- `actual_upload_allowed_in_this_phase`: `false`
- `actual_launch_allowed_in_this_phase`: `false`
- Next phase: ATL-5 — Real cloud smoke run (only after user explicitly confirms all gates)

## Risk Note

User declared `READY_FOR_CLOUD_SMOKE_RUN` in ATL-4A-CREDIT-FILL, but billing / charge visibility / run controls / data policy remain partially unknown. ATL-4C does not override this risk — it adds more gates. The risk is still present and must be acknowledged again in ATL-5 before any real launch.
