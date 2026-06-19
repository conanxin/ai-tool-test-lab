# ATL-EVOMAP-8A · Nightly Validation Loop Asset

This folder ships the **nightly validation loop asset** for the OpenClaw /
Hermes Local Evolution Kit.

It contains **only the asset + dry-run example + artifacts + report +
validator**. It does **NOT** install a real cron / systemd timer. Any real
scheduling must be performed by a human operator in a separate, explicit
phase (e.g. ATL-EVOMAP-8B).

## Contents

```
phase8a-nightly-validation-loop/
├── README.md                                       ← this file
├── ATL_EVOMAP_8A_NIGHTLY_VALIDATION_LOOP_REPORT.md ← full case report
├── validation-loop-manifest.json                   ← machine-readable contract (schema v0.1)
├── templates/
│   └── cron.example                                ← DRY-RUN cron example (NOT installed)
└── artifacts/
    ├── nightly-validation-digest.json              ← written by runner smoke run
    ├── nightly-validation-digest.md                ← written by runner smoke run
    ├── nightly-validation-run.log                 ← written by runner smoke run
    └── nightly-smoke/
        ├── nightly-validation-digest.json          ← refresh smoke re-run (2026-06-19 10:30)
        ├── nightly-validation-digest.md            ← refresh smoke re-run
        ├── nightly-validation-run.log             ← refresh smoke re-run
        └── nightly-smoke-summary.json              ← structured summary (all_expected_met=true)
```

## What the runner does

`scripts/evomap_nightly_validate.py` is a Python **stdlib-only** script that
executes 9 blocking checks in sequence and writes a JSON + Markdown digest
plus a short run log to `--out-dir`.

| # | Check ID | What it verifies |
|--|--|--|
| 1 | `stdlib_only` | Runner source imports only Python stdlib (AST scan). |
| 2 | `no_hub_url_set` | `A2A_HUB_URL` is not set in the runner's process environment. |
| 3 | `data_cases_json_parse` | `python3 -m json.tool data/cases.json` returns rc=0. |
| 4 | `data_cases_json_phase_history_has_evomap_8a` | `data/cases.json` top phase or `phase_history` records `ATL-EVOMAP-8A`. |
| 5 | `bundles_inspectable` | All 4 canonical portable bundles (OpenClaw / Hermes / Telegram / Codex) exist and `scripts/evomap_inspect_bundle.py --bundle ...` returns rc=0 for each. |
| 6 | `bundles_validatable` | All 4 canonical portable bundles exist and `scripts/evomap_validate_bundle.py --bundle ...` returns rc=0 for each. |
| 7 | `all_phase_validators_pass` | All 6 prior phase validators (5 / 6A / 6B / 6C / 7A / 7B) return rc=0 with the literal marker `ALL CHECKS PASSED` in their stdout (capped at 2000 chars). |
| 8 | `secret_scan_clean` | In-process stdlib secret scan over tracked text files: 0 hits, 0 tracked `.env` paths, 0 tracked `/tmp/...` paths. Allowed timestamp hits are recorded. |
| 9 | `git_hygiene_no_root_evolver_or_memory` | `git ls-files` does not list any root-level `.evolver/` or `memory/` paths. `git status --short` is recorded but not required clean (this run produces new artifacts). |

All 9 checks are blocking. The runner exits **0** on full PASS, **1** if
any blocking check fails, and **2** on invocation / IO errors (e.g.
unwritable output dir, `--repo-root` does not look like the repo).

## How to run (per ATL-EVOMAP-8A spec)

### Real run (writes digests)

```bash
cd /path/to/ai-tool-test-lab
python3 scripts/evomap_nightly_validate.py --repo-root . --out-dir <dir>
```

### Dry run (checks run, no digests persisted)

```bash
python3 scripts/evomap_nightly_validate.py --repo-root . --out-dir <dir> --dry-run
```

### Override output filenames

```bash
python3 scripts/evomap_nightly_validate.py \
    --repo-root . --out-dir /tmp/my-digests \
    --json-name my-digest.json \
    --markdown-name my-digest.md
```

### Backward-compat (older invocation without explicit flags)

```bash
# Equivalent to --repo-root . --out-dir <case-artifacts-dir>
python3 scripts/evomap_nightly_validate.py
# --output-dir <path> still works as an alias for --out-dir
```

## Hard boundaries (enforced)

This asset is intentionally local-only. The runner enforces the following
22 hard boundaries, all of which are also declared in the digest JSON and
the validation manifest:

- No Hub connection / no `A2A_HUB_URL` set / no `evolver --loop` / no
  `evolver run` / no `evolver review` / no `evolver review --approve` /
  no `evolver solidify` / no auto-publish / no credit consumption / no ATP
  autobuy.
- No real credentials read (no `.env` content scan; tracked `.env` paths
  cause an immediate FAIL; only public text pattern scan via the in-process
  stdlib scanner).
- No `curl` / `wget` / HTTP / Telegram / OpenAI / Codex / Copilot / any
  online coding API calls.
- No real `pytest` / `npm test` / `pnpm test` / `cargo test` / `go test` /
  `mvn test` invocations.
- No real cron install / no `crontab` write / no systemd timer create.
- No `evolver` package source modification / no committed runtime
  `.evolver/` or `memory/` originals at repo root.
- Python stdlib only.

## Future installation (NOT done by this phase)

When a human operator decides to install real scheduling, they would:

1. Read this README + the case report
   (`ATL_EVOMAP_8A_NIGHTLY_VALIDATION_LOOP_REPORT.md`).
2. Confirm the runner has been green for at least N consecutive dry runs.
3. Customize `templates/cron.example` for the real machine:
   - Replace `/path/to/ai-tool-test-lab` with the real path.
   - Adjust the cadence (`30 2 * * *` is a recommended default).
   - Choose a real log path (`/var/log/evomap-nightly.log` or similar).
4. Copy the customized line into `/etc/cron.d/evomap-nightly` (or any
   other operator-preferred scheduler).
5. Verify the first scheduled run by inspecting the resulting
   `nightly-validation-digest.{json,md}` and `nightly-validation-run.log`.

This asset deliberately does NOT take any of the above steps. Doing so
would require operator authorization and would be tracked under a future
phase (e.g. ATL-EVOMAP-8B).
