# ATL-EVOMAP-8A · Nightly Validation Loop Asset — Case Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** ATL-EVOMAP-8A · Nightly Validation Loop Asset
**Status:** Nightly validation loop asset completed (`NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS`)
**Date:** 2026-06-19
**Result:** PASS · 9/9 blocking checks in real smoke run + 22/22 validator checks

---

## 1. Goal

Ship an **offline-only, local-only, stdlib-only** nightly validation loop
asset that can be later wired into a real cron / systemd timer by a human
operator. This phase ships:

- the runner
- the validation manifest (schema `atl-evomap-nightly-validation-v0.1`)
- a dry-run cron example
- the artifacts produced by a real smoke run
- the case + top-level reports
- a dedicated validator (22 checks)

It deliberately does **NOT**:

- install any real cron / systemd timer
- modify any real OpenClaw / Hermes / systemd / cron config
- connect to EvoMap Hub, set `A2A_HUB_URL`, or invoke any `evolver` subcommand
- read or scan `.env` content
- read real Telegram / OpenAI / Codex credentials or chat ids
- run any real `pytest` / `npm test` / `cargo test` / `go test` / `mvn test`
- consume credits or trigger ATP autobuy
- auto-publish or auto-approve or auto-solidify

## 2. Spec compliance (per the detailed ATL-EVOMAP-8A spec, second message)

| Spec requirement | Implementation |
|--|--|
| Runner: `python3 scripts/evomap_nightly_validate.py --repo-root . --out-dir <dir>` | ✅ both flags present, `--repo-root` defaults to `.` |
| Optional `--strict` | ✅ present |
| Optional `--markdown-name` | ✅ present, default `nightly-validation-digest.md` |
| Optional `--json-name` | ✅ present, default `nightly-validation-digest.json` |
| Python stdlib only | ✅ AST-verified; imports limited to `{__future__, argparse, datetime, json, mimetypes, os, pathlib, re, subprocess, sys, textwrap, traceback, typing}` |
| No network egress | ✅ no `urllib` / `socket` / `requests` usage; subprocess env explicitly blanks `A2A_HUB_URL` |
| No `evolver` invocation | ✅ runner never calls `evolver`; subprocess env blanks `A2A_HUB_URL` defensively |
| No real test runner invocation | ✅ runner never calls `pytest` / `npm` / `cargo` / `go` / `mvn` |
| Records `git rev-parse --short HEAD` | ✅ recorded as `git_commit` in digest |
| Records `git status --short` | ✅ recorded as `git_status_short` in digest |
| Records timestamp | ✅ `generated_at` ISO + `_human_now()` in stdout header |
| Phase validators: 6 scripts, each with stdout_tail / stderr_tail (≤ 2000 chars) | ✅ `_cap(text, 2000)` enforces the limit |
| Cases.json parse via `python3 -m json.tool data/cases.json` | ✅ used as the canonical parse step |
| Bundle inspect (`evomap_inspect_bundle.py --bundle <b>`) | ✅ executed for all 4 canonical bundles |
| Bundle validate (`evomap_validate_bundle.py --bundle <b>`) | ✅ executed for all 4 canonical bundles (NEW vs initial spec) |
| Secret scan: tracked text files only, skip binaries / images / >2 MiB, refuse .env paths, patterns + allowlist, `allowed_timestamp_hits` recorded | ✅ in-process stdlib scanner; skip rules + allowlist + per-pattern hit lists |
| Git hygiene: no root `.evolver/` or `memory/`; `git status --short` recorded but not required clean | ✅ implemented; status informational only |
| JSON digest: `nightly-validation-digest.json` | ✅ default filename |
| Markdown digest: `nightly-validation-digest.md` | ✅ default filename |
| Manifest schema: `atl-evomap-nightly-validation-v0.1` with `validators` + `bundles` + `checks` + `hard_boundaries` | ✅ v0.1 manifest shipped |
| `overall_status`: PASS only if all blocking checks PASS | ✅ |

## 3. Files added / updated

```
cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/
├── README.md                                       ← case-page README
├── ATL_EVOMAP_8A_NIGHTLY_VALIDATION_LOOP_REPORT.md ← this report
├── validation-loop-manifest.json                   ← v0.1 machine-readable contract
├── templates/
│   └── cron.example                                ← DRY-RUN cron example (NOT installed)
└── artifacts/
    ├── nightly-validation-digest.json              ← spec default filename
    ├── nightly-validation-digest.md                ← spec default filename
    └── nightly-validation-run.log                 ← runner log

scripts/
├── evomap_nightly_validate.py                      ← runner (stdlib only, 9 blocking checks)
└── validate_evomap_phase8a_nightly_validation_loop.py ← validator (22 checks)

reports/
└── ATL_EVOMAP_8A_NIGHTLY_VALIDATION_LOOP_REPORT.md ← top-level mirror of this report
```

Updated: `data/cases.json` (phase → ATL-EVOMAP-8A + `phase_history` entry
+ spec-refinement note), `cases/evomap-evolver-openclaw-v0/README.md`
(Phase 8A section).

## 4. Runner design (CLI per spec)

```
python3 scripts/evomap_nightly_validate.py --repo-root <path> --out-dir <path>
                                              [--strict]
                                              [--markdown-name <name>]
                                              [--json-name <name>]
                                              [--dry-run]
                                              [--output-dir <path>]   # backward-compat alias for --out-dir
```

`--repo-root` defaults to `.`. `--out-dir` defaults to
`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts`
when not specified. `--output-dir` is accepted as a backward-compat alias
for `--out-dir` (so prior invocations like
`python3 scripts/evomap_nightly_validate.py` without explicit
`--out-dir` keep working as before).

## 5. Validation manifest (schema v0.1)

`validation-loop-manifest.json` carries `schema_version =
"atl-evomap-nightly-validation-v0.1"`, `source_base_commit = "f292757"`,
and structured top-level fields:

- `validators[]` — 6 phase validator script paths
- `bundles[]` — 4 canonical portable bundle paths
- `checks[]` — 6 check kinds (`phase_validators`, `data_cases_json_parse`,
  `bundle_inspect`, `bundle_validate`, `secret_scan`, `git_hygiene`)
- `checks_detail` — per-check spec (kind, blocking, command, pass criterion,
  skip rules, allowlist, detection patterns)
- `hard_boundaries` — 16 explicit no-go flags
- `cron_integration` — `installed: false`, `example_only: true`, recommended
  cadence `30 2 * * * Asia/Shanghai`

The Phase 8A validator (checks 10–15) verifies each of these structural
fields.

## 6. Dry-run cron example

`templates/cron.example` is a deliberately not-installed cron snippet. It
contains:

- A header block explaining it is **DRY-RUN** / **EXAMPLE** / **MUST NOT**
  be installed by this phase.
- The recommended cadence: `30 2 * * *` (daily 02:30 Asia/Shanghai).
- A command line using a placeholder path (`/path/to/ai-tool-test-lab`)
  that the future operator must replace.
- A pointer to `/etc/cron.d/evomap-nightly` as the suggested drop-in path
  (operator-owned, NOT managed by this phase).

The Phase 8A validator (check #16) verifies that the file is **NOT a real
cron drop-in**: a real drop-in would have a non-comment line referencing
`/etc/cron.d/`, `/var/spool/cron/`, or `crontab`; the example has none.

## 7. Smoke run evidence

The runner was executed as a real smoke run after the case was wired up.
The run recorded `9/9 PASS` overall.

### 7.1 Blocking checks (9/9 PASS)

| # | Check ID | Status | Detail |
|--|--|--|--|
| 1 | `stdlib_only` | PASS | stdlib-only verified |
| 2 | `no_hub_url_set` | PASS | A2A_HUB_URL not set |
| 3 | `data_cases_json_parse` | PASS | rc=0 (via `python3 -m json.tool`) |
| 4 | `data_cases_json_phase_history_has_evomap_8a` | PASS | top — `ATL-EVOMAP-8A Nightly Validation Loop Asset`, history_count=17 |
| 5 | `bundles_inspectable` | PASS | 4 bundle(s) inspected |
| 6 | `bundles_validatable` | PASS | 4 bundle(s) validated |
| 7 | `all_phase_validators_pass` | PASS | 6 validator(s) ALL CHECKS PASSED |
| 8 | `secret_scan_clean` | PASS | scanned=301, hits=0, allowed_timestamp_hits=21, skipped={binary: 84, image: 0, too_large: 0, io_error: 0} |
| 9 | `git_hygiene_no_root_evolver_or_memory` | PASS | 385 tracked file(s) clean, status_short=6 line(s) (informational) |

### 7.2 Subprocess phase validators (all rc=0, "ALL CHECKS PASSED" present)

| Validator | Script | Result |
|--|--|--|
| Phase 5 | `scripts/validate_evomap_phase5_local_evolution_kit.py` | ALL CHECKS PASSED |
| Phase 6A | `scripts/validate_evomap_phase6a_hermes_systemd_bundle.py` | ALL CHECKS PASSED |
| Phase 6B | `scripts/validate_evomap_phase6b_telegram_router_bundle.py` | ALL CHECKS PASSED |
| Phase 6C | `scripts/validate_evomap_phase6c_codex_test_failure_bundle.py` | ALL CHECKS PASSED |
| Phase 7A | `scripts/validate_evomap_phase7a_domain_signal_injection.py` | ALL CHECKS PASSED |
| Phase 7B | `scripts/validate_evomap_phase7b_cross_bundle_regression.py` | ALL CHECKS PASSED |

### 7.3 Bundle inspect + validate (all rc=0)

| Bundle | inspect rc | validate rc |
|--|--|--|
| openclaw_tool_use_discipline | 0 | 0 |
| hermes_systemd_recovery | 0 | 0 |
| telegram_message_router_failure | 0 | 0 |
| codex_test_failure_loop | 0 | 0 |

### 7.4 Secret scan details

| Metric | Value |
|--|--|
| Tracked file count | 385 |
| Tracked `.env` paths | 0 (refused-scan rule would FAIL if > 0) |
| Scanned (text, ≤ 2 MiB, not image, not binary) | 301 |
| Skipped binary | 84 |
| Skipped image | 0 |
| Skipped > 2 MiB | 0 |
| Skipped IO error | 0 |
| Total secret hits | 0 |
| Allowed timestamp hits (Unix ms in 1.5e12..2.0e12) | 21 |
| Tracked `/tmp/...` paths | 0 (defense-in-depth check) |

### 7.5 Digest artifacts (per spec'd filenames)

- `artifacts/nightly-validation-digest.json` — machine-readable digest
  (9 checks + summary + 22 hard boundaries + manifest metadata + git
  commit + git status --short).
- `artifacts/nightly-validation-digest.md` — human-readable digest with
  per-check table + per-validator stdout_tail + per-bundle inspect/validate
  + secret scan + git hygiene sections.
- `artifacts/nightly-validation-run.log` — short log suitable for tailing
  in cron output.

## 8. Validator (`validate_evomap_phase8a_nightly_validation_loop.py`)

22 checks. All PASS on the post-update repository.

| # | Check | Type | Result |
|--|--|--|--|
| 1 | `scripts/evomap_nightly_validate.py` exists | file | PASS |
| 2 | runner source is Python stdlib only | AST | PASS |
| 3 | runner declares `--repo-root` | arg | PASS |
| 4 | runner declares `--out-dir` | arg | PASS |
| 5 | runner declares `--markdown-name` + `--json-name` | arg | PASS |
| 6 | runner declares `--output-dir` backward-compat alias | arg | PASS |
| 7 | runner declares 22 hard-boundary flags in digest | text | PASS |
| 8 | `validation-loop-manifest.json` exists | file | PASS |
| 9 | manifest parses as valid JSON | JSON | PASS |
| 10 | manifest `schema_version == 'atl-evomap-nightly-validation-v0.1'` | JSON | PASS |
| 11 | manifest has `source_base_commit` (string, length ≥ 7) | JSON | PASS |
| 12 | manifest `validators[]` contains all 6 prior phase validators | JSON | PASS |
| 13 | manifest `bundles[]` contains all 4 canonical portable bundles | JSON | PASS |
| 14 | manifest `runner.stdlib_only == true` | JSON | PASS |
| 15 | manifest `cron_integration.installed==false` + `cron.example` path | JSON | PASS |
| 16 | `templates/cron.example` is dry-run only, not a real drop-in | text | PASS |
| 17 | `artifacts/nightly-validation-digest.json` exists (spec filename) | file | PASS |
| 18 | digest JSON `overall_status == PASS` | JSON | PASS |
| 19 | digest JSON blocking checks passed == 9/9 | JSON | PASS |
| 20 | `artifacts/nightly-validation-digest.md` exists (spec filename) | file | PASS |
| 21 | `data/cases.json` phase or history contains ATL-EVOMAP-8A | JSON | PASS |
| 22 | 6 prior validators ALL PASS + nightly runner self-host exits 0 | composite | PASS |

## 9. Boundary verification

Verified that the asset does not violate any of the 22 hard boundaries:

- No `urllib` / `socket` / `requests` / HTTP usage in the runner (runner
  only uses `subprocess` to invoke local `python3` and `git ls-files` /
  `git status` / `git rev-parse`, all offline).
- No `A2A_HUB_URL` set during the smoke run; subprocess env explicitly
  blanks `A2A_HUB_URL` defensively.
- No `evolver` subcommand invoked.
- No `.env` file content scanned (the in-process secret scanner refuses
  to even *read* `.env` paths if they appear in tracked files — would FAIL
  with `env_path_hits` if any). Tracked count: 0.
- No real `pytest` / `npm test` / etc. invoked.
- No `crontab` write, no `/etc/cron.d/` file created, no systemd timer
  unit created.
- The runner's own top-level imports are limited to the stdlib set
  declared in `_ALLOWED_TOP_LEVEL_IMPORTS`.

## 10. Re-test on a clean checkout

To re-verify on a fresh clone, an operator would:

```bash
cd /path/to/ai-tool-test-lab
python3 scripts/validate_evomap_phase8a_nightly_validation_loop.py
# expect: 22/22 PASS, ALL CHECKS PASSED

python3 scripts/evomap_nightly_validate.py --repo-root . --dry-run
# expect: 9/9 PASS, exit 0, no files written

python3 scripts/evomap_nightly_validate.py --repo-root .
# expect: 9/9 PASS, exit 0, 3 files written under
#   cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/
#   (nightly-validation-digest.json, nightly-validation-digest.md, nightly-validation-run.log)
```

## 11. Next steps (forward-looking, NOT executed in this phase)

- **ATL-EVOMAP-8B · Operator-led real-cron install** — gated on this
  asset being green for at least N consecutive smoke runs and on explicit
  human authorization. Out of scope for this phase.
- **ATL-EVOMAP-9A · `bundle-curator` skill** — meta-tool that auto-generates
  portable bundles from evolver run outputs. Out of scope.

## 12. Conclusion

ATL-EVOMAP-8A delivers a reusable, future-installable nightly validation
loop asset for the OpenClaw / Hermes Local Evolution Kit. The runner is
**offline-only, local-only, stdlib-only**, supports the full spec'd CLI
(`--repo-root`, `--out-dir`, `--markdown-name`, `--json-name`, `--strict`,
`--dry-run`, plus the `--output-dir` backward-compat alias), and respects
all 22 hard boundaries. It runs 9 blocking checks (including the new
`bundles_validatable` step and the in-process stdlib secret scanner per
the detailed spec). A dry-run cron example is shipped for future operator
use; **no real cron or systemd timer is installed by this phase**. All 6
prior phase validators remain green (no regression); the Phase 8A
validator itself also passes 22/22.

Case status: **NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS**.

## 13. Refresh smoke re-run (2026-06-19 10:30)

The runner was re-executed as a fresh smoke run at 2026-06-19 10:30:18
(GMT+8) into the spec-required `artifacts/nightly-smoke/` subdirectory
(per ATL-EVOMAP-8A spec step 7). Result: 9/9 blocking PASS, all_expected
fields PASS, no regression vs the original smoke run.

| Artifact | Path |
|--|--|
| Digest JSON | `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/nightly-smoke/nightly-validation-digest.json` |
| Digest Markdown | `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/nightly-smoke/nightly-validation-digest.md` |
| Run log | `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/nightly-smoke/nightly-validation-run.log` |
| Smoke summary | `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/nightly-smoke/nightly-smoke-summary.json` |

Smoke summary key fields (`nightly-smoke-summary.json`):

- `overall_status`: `PASS`
- `schema_version`: `atl-evomap-nightly-validation-v0.1`
- `source_base_commit`: `f292757`
- `git_commit`: `f292757`
- `blocking_count`: 9 (passed=9, failed=0)
- `validator_count`: 6 (passed=6)
- `bundle_inspect_count`: 4
- `bundle_validate_count`: 4
- `secret_scan_ok`: true (hits=0, allowed_timestamp_hits=21, scanned=301, skipped_binary=84)
- `git_hygiene_ok`: true (tracked=385, status_short_lines=6)
- `hard_boundaries_ok`: true (22 boundaries, all true)
- `all_expected_met`: true
