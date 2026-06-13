# Cost Guard — Castform Cloud Smoke Run (ATL-4B-CONFIG)

## Current Status

- **Billing / credit**: NOT CONFIRMED.
- **Auto-charge visibility**: NOT CONFIRMED.
- **Cost estimate for smoke run**: NOT COMPUTED.
- **Launch training run**: FORBIDDEN.
- **Current readiness**: `BLOCKED_BY_UNCLEAR_CHARGES`.

## Hard Rules

1. **No launch** of any Castform training run while billing / credit / auto-charge is unconfirmed.
2. The first real cloud smoke run must use the **minimum** sample counts (8 train / 2 eval) and a **small** base model candidate — this is a platform-link smoke run, not a quality run.
3. The first real cloud smoke run's **only** success criterion is: upload accepted, launch accepted, monitoring visible, status can be polled, model can be fetched. The resulting model is allowed to be bad — quality is explicitly out of scope for this run.
4. If the Castform Web App UI does not show: (a) credit balance, (b) billing history, (c) auto-charge toggle, (d) per-run cost estimate — the run stays blocked.
5. If the user cannot articulate a maximum acceptable spend for the smoke run, the run stays blocked.
6. No agent may flip `cloud_launch_allowed` to `true` on its own. The user must do it.

## What "blocked" looks like in this phase

- `cloud_smoke_config.json` -> `cloud_launch_allowed: false`
- `cloud_smoke_config.json` -> `current_readiness: "BLOCKED_BY_UNCLEAR_CHARGES"`
- `cloud_launch_guard.py` -> prints the blocked banner and exits non-zero when invoked.
- `scripts/validate_atl4b_cloud_smoke_config.py` -> would FAIL if either of the above two fields were flipped, so it acts as a tripwire.

## Unblocking Path (out of scope for ATL-4B-CONFIG)

Real launch is only allowed after, in order:

1. User opens the Castform Web App, navigates to billing/credit, and confirms the values.
2. User records those values in `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md` (or in a Telegram message that the agent then transcribes into the file).
3. User sets an explicit cost ceiling (e.g. "max $X for the first smoke run").
4. Agent updates `cloud_smoke_config.json` -> `current_readiness: "READY_FOR_CLOUD_SMOKE_RUN"`.
5. Agent updates `cloud_smoke_config.json` -> `cloud_launch_allowed: false` (still false — the guard is flipped only at run time by the user, not stored in the config).
6. ATL-4C (guarded upload preflight) runs.
7. ATL-4D (guarded launch preflight) runs.
8. ATL-4E (real smoke run) runs, with the user executing the `export CASTFORM_API_KEY=...` line themselves.

ATL-4B-CONFIG only delivers step 0 — the config and the guards. Steps 1+ are explicitly NOT in this phase.

## What ATL-4B-CONFIG is NOT

- It is NOT a "we are about to launch" signal.
- It is NOT a "billing is sorted" claim.
- It is NOT a real upload.
- It is NOT a real launch.
- It is NOT a fabricated success.

It is a written, validated, pre-flight-ready configuration package that sits behind a hard `BLOCKED` gate until the user is satisfied that money will not be spent accidentally.
