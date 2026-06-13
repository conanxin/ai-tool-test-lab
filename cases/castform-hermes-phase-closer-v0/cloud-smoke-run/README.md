# Castform Cloud Smoke Run — Dry Configuration (ATL-4B-CONFIG)

## Phase Identity

- **Phase**: ATL-4B-CONFIG
- **Status**: Dry configuration only
- **Launch allowed**: false
- **Current readiness**: `BLOCKED_BY_UNCLEAR_CHARGES`

This phase is **dry configuration only**. It does NOT call the Castform API, does NOT upload any data, does NOT start any training run, does NOT create any API key, and does NOT use a real `CASTFORM_API_KEY`. The artifacts in this directory are scaffolding for a future real smoke run that will only be allowed after the user explicitly confirms credit / billing / auto-charge / cost visibility (ATL-4A-CREDIT or explicit `READY_FOR_CLOUD_SMOKE_RUN` declaration).

## Selected Path: Build your own / SDK

Hermes Phase Closer v0's first cloud smoke run uses the **Build your own / SDK** training path instead of the Castform template paths for RAG Agent or Agent Traces.

### Why not RAG Agent

- The current project does NOT have a production document corpus with citation requirements.
- RAG Agent assumes retrieval + grounded citation; the local artifacts here are prompt + ground_truth JSONL, not a retrieval benchmark.
- Using RAG Agent would force the project to either invent a corpus or abuse a template that does not match the actual workload.
- Cost: RAG Agent template adds retrieval-side compute on top of SFT/RL — wasted spend for a smoke run.

### Why not Agent Traces

- Agent Traces is built for production agent trace providers (real traffic log uploads).
- The local dataset is synthetic, fixture-style, and was constructed for environment + reward validation, not as a real agent traffic capture.
- Misusing Agent Traces as a smoke run target would conflate "platform can ingest traces" with "training is sane" — those are different signals.
- Cost: Agent Traces templates assume large trace volumes; smoke runs should not commit to that cost ceiling.

### Why Build your own / SDK is the right smoke target

- The project already has prompt / ground_truth JSONL (ATL-2).
- The project already has a local environment candidate (`environment_validate_candidate.py`, ATL-3C).
- The project already has a rule-based reward (`reward.py`).
- The project has already passed real local `validate_env` (10/10 contract checks, ATL-3C).
- Build your own / SDK exposes the minimum viable surface area to prove: upload → launch → monitor → fetch model.
- The first cloud smoke run's only objective is to **prove the platform link works**, not to train a useful model.

## Recommended Smoke Run Configuration

| Field | Value |
| --- | --- |
| Run name | `hermes-phase-closer-smoke` |
| Template path | `build_your_own_sdk` |
| Base model | `Qwen/Qwen3.5-4B` |
| Train sample count (first cloud smoke) | 8 |
| Eval sample count (first cloud smoke) | 2 |
| Dataset source | existing local redacted ATL-2 JSONL |
| Environment source | existing ATL-3C `environment_validate_candidate.py` |
| Reward source | existing `reward.py` |
| Tools | none |
| External network tools | none |
| Max turns | 1 (minimal) |
| Objective | prove upload + launch + monitoring can start, not train a useful model |

The base model `Qwen/Qwen3.5-4B` is a placeholder pending user confirmation; it is the candidate the user has visible in the Castform setup flow today.

## Hard Boundaries

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
13. No `TrainerClient` invoked.
14. No model training.
15. No fabricated cloud smoke run success.
16. Allowed: dry-run config files, docs, script placeholders, and this report.
17. Allowed: `git commit` and `git push` of the dry artifacts.

## Pre-Launch Gates (must be green before any real launch)

Real launch is only permitted after ALL of the following are confirmed by the user in writing (Telegram message or explicit file update):

- [ ] Credit balance visible in Castform Web App.
- [ ] Billing / auto-charge / invoice path visible in Castform Web App.
- [ ] Cost estimate for the 8/2 smoke run is known and within user-approved budget.
- [ ] User has confirmed `READY_FOR_CLOUD_SMOKE_RUN` (or ATL-4A-CREDIT has passed).
- [ ] User has explicitly authorized a one-shot shell `export CASTFORM_API_KEY="<redacted-at-source>"` for the guarded launch.
- [ ] `cloud_launch_guard.py` has been temporarily switched from `BLOCKED` to `ALLOWED` by the user (not by the agent).

Until every gate is green, `cloud_launch_allowed` stays `false` and `current_readiness` stays `BLOCKED_BY_UNCLEAR_CHARGES`.

## Files In This Directory

- `cloud_smoke_config.json` — machine-readable dry config (checked by the validator).
- `README.md` — this file.
- `API_KEY_HANDLING.md` — API key handling rules.
- `COST_GUARD.md` — billing / cost guard rules.
- `prepare_cloud_smoke_subset.py` — local preview subset extractor (std-lib only).
- `cloud_launch_guard.py` — explicit launch guard (default = refuse).
- `smoke-train.preview.jsonl` — first 8 train rows (preview only, NOT for upload yet).
- `smoke-eval.preview.jsonl` — first 2 eval rows (preview only, NOT for upload yet).

The `.preview` suffix is a deliberate marker: these files are **not** the final upload artifacts and must not be passed to any Castform upload endpoint.
