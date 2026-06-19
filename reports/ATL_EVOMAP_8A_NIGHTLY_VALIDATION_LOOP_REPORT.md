# ATL-EVOMAP-8A · Nightly Validation Loop Asset — Top-level Report

**Mirror of the case-level report.** See
[`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/ATL_EVOMAP_8A_NIGHTLY_VALIDATION_LOOP_REPORT.md`](../cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/ATL_EVOMAP_8A_NIGHTLY_VALIDATION_LOOP_REPORT.md)
for the full version.

## Summary

| Item | Value |
|--|--|
| Case | `evomap-evolver-openclaw-v0` |
| Phase | ATL-EVOMAP-8A · Nightly Validation Loop Asset |
| Status | Nightly validation loop asset completed (`NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS`) |
| Result | PASS — 9/9 blocking checks in real smoke run + 22/22 validator checks |
| Date | 2026-06-19 |
| Manifest schema | `atl-evomap-nightly-validation-v0.1` |
| Source base commit | `f292757` |

## What shipped

- **`scripts/evomap_nightly_validate.py`** — stdlib-only runner.
  - CLI per spec: `--repo-root <path> --out-dir <path>`
  - Optional: `--strict`, `--markdown-name <name>`, `--json-name <name>`,
    `--dry-run`
  - Backward-compat alias: `--output-dir <path>` → `--out-dir <path>`
  - 9 blocking checks (per the detailed spec):
    1. `stdlib_only`
    2. `no_hub_url_set`
    3. `data_cases_json_parse` (via `python3 -m json.tool`)
    4. `data_cases_json_phase_history_has_evomap_8a`
    5. `bundles_inspectable` (via `evomap_inspect_bundle.py`)
    6. `bundles_validatable` (via `evomap_validate_bundle.py`)
    7. `all_phase_validators_pass` (6 phase validators, stdout_tail capped at 2000 chars)
    8. `secret_scan_clean` (in-process stdlib scan: tracked text files only,
       skip binary / image / >2 MiB, refuse `.env` paths, allowlist Unix ms
       timestamps as `allowed_timestamp_hits`, allowlist placeholder text)
    9. `git_hygiene_no_root_evolver_or_memory` (recorded `git rev-parse` +
       `git status --short`)
  - JSON + Markdown digest + run log output, with spec'd default filenames
    (`nightly-validation-digest.json`, `nightly-validation-digest.md`,
    `nightly-validation-run.log`).
  - Explicit `A2A_HUB_URL=""` on every subprocess (defensive even if
    parent has it set).
- **`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/validation-loop-manifest.json`**
  — machine-readable contract, schema `atl-evomap-nightly-validation-v0.1`.
  Top-level structured fields: `validators[]`, `bundles[]`, `checks[]`,
  `checks_detail`, `hard_boundaries`, `cron_integration`.
- **`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/templates/cron.example`**
  — DRY-RUN cron example. NOT installed.
- **`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/`**
  — digest JSON + Markdown + run log from the real smoke run (spec'd
    filenames).
- **`scripts/validate_evomap_phase8a_nightly_validation_loop.py`** —
  validator (22 checks: file presence + AST stdlib guard + CLI flag
  presence + manifest schema v0.1 + digest shape + cases.json + main
  README + backward-compat composite of all 6 prior validators + runner
  self-host).
- **Reports** — case-level
  (`ATL_EVOMAP_8A_NIGHTLY_VALIDATION_LOOP_REPORT.md`) + this top-level
  mirror.
- **Updated `data/cases.json`** — phase → ATL-EVOMAP-8A, new
  `phase_history` entry.
- **Updated `cases/evomap-evolver-openclaw-v0/README.md`** — added the
  Phase 8A section and updated next-steps.

## Smoke run result

```
Overall status: PASS
Blocking: passed=9, failed=0, non_blocking_rows=0
```

| # | Check | Result |
|--|--|--|
| 1 | stdlib_only | PASS |
| 2 | no_hub_url_set | PASS |
| 3 | data_cases_json_parse | PASS (rc=0 via `python3 -m json.tool`) |
| 4 | data_cases_json_phase_history_has_evomap_8a | PASS |
| 5 | bundles_inspectable | PASS (4 bundles) |
| 6 | bundles_validatable | PASS (4 bundles) |
| 7 | all_phase_validators_pass | PASS (6 validators) |
| 8 | secret_scan_clean | PASS (scanned=301, hits=0, allowed_ts=21) |
| 9 | git_hygiene_no_root_evolver_or_memory | PASS (385 tracked) |

## Validator result

`scripts/validate_evomap_phase8a_nightly_validation_loop.py` — 22/22 PASS.

## Hard boundaries (22)

No Hub / no `A2A_HUB_URL` / no `evolver --loop` / no `evolver run` / no
`evolver review` / no `evolver review --approve` / no `evolver solidify` /
no auto-publish / no credit consumption / no ATP autobuy / no real
credentials read / no `.env` content scan / no `curl` / no Telegram API /
no online coding API / no real test runner / no real cron install / no
`crontab` write / no systemd timer create / no evolver source modify / no
runtime `.evolver/` or `memory/` tracked / stdlib-only.

## Next steps (NOT executed in this phase)

- **ATL-EVOMAP-8B · Operator-led real-cron install** — gated on Phase 8A
  being green for at least N consecutive smoke runs and on explicit human
  authorization.
- **ATL-EVOMAP-9A · `bundle-curator` skill** — meta-tool that auto-generates
  portable bundles from evolver run outputs.

## Regression check

All 6 prior phase validators (5 / 6A / 6B / 6C / 7A / 7B) still return
`ALL CHECKS PASSED` after this phase. No regression.

## Refresh smoke re-run (2026-06-19 10:30)

A fresh smoke run was executed into the spec-required
`artifacts/nightly-smoke/` subdirectory (per ATL-EVOMAP-8A spec step 7).
Result: **9/9 blocking PASS, 6/6 validators PASS, 4/4 bundle inspect,
4/4 bundle validate, secret_scan clean (hits=0, allowed_ts=21), git
hygiene clean, hard_boundaries clean**. See
`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/nightly-smoke/nightly-smoke-summary.json`
for the structured summary (`all_expected_met: true`). No real cron
installed, no systemd timer created, no Hub / publish / credits / approve
/ solidify.
