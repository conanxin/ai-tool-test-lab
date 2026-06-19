# EvoMap Nightly Validation Loop — Digest

- **Generated:** 2026-06-19T10:35:00
- **Phase:** ATL-EVOMAP-8A
- **Schema version:** atl-evomap-nightly-validation-v0.1
- **Source base commit:** f292757
- **Case slug:** `evomap-evolver-openclaw-v0`
- **Project root:** `/mnt/d/AI/ai-tool-test-lab`
- **Runner:** `scripts/evomap_nightly_validate.py`
- **Python:** 3.12.3
- **Stdlib-only:** YES
- **A2A_HUB_URL set:** no
- **Overall status:** **PASS**
- **Blocking checks passed:** 9 / 9
- **Non-blocking WARN/INFO rows:** 0

## Checks

| # | Check ID | Status | Blocking | Detail |
|---|----------|--------|----------|--------|
| 1 | `stdlib_only` | PASS | yes | stdlib-only verified |
| 2 | `no_hub_url_set` | PASS | yes | A2A_HUB_URL not set |
| 3 | `data_cases_json_parse` | PASS | yes | rc=0 |
| 4 | `data_cases_json_phase_history_has_evomap_8a` | PASS | yes | top, history_count=18 |
| 5 | `bundles_inspectable` | PASS | yes | 4 bundle(s) inspected |
| 6 | `bundles_validatable` | PASS | yes | 4 bundle(s) validated |
| 7 | `all_phase_validators_pass` | PASS | yes | 6 validator(s) ALL CHECKS PASSED |
| 8 | `secret_scan_clean` | PASS | yes | scanned=301, hits=0, allowed_timestamp_hits=21, skipped={'binary': 84, 'image': 0, 'too_large': 0, 'io_error': 0} |
| 9 | `git_hygiene_no_root_evolver_or_memory` | PASS | yes | 385 tracked file(s) clean, status_short=6 line(s) (informational) |

## Phase validators

| Validator | Returncode | Last 2000 chars of stdout |
|-----------|------------|----------------------------|
| `phase5_local_evolution_kit` | 0 | 0m  templates/GENE_TEMPLATE.json exists
[92mPASS[0m  templates/CAPSULE_TEMPLATE.json exists
[92mPASS[0m  templates/MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl exists
[94mINFO[0m  9. Checking inspect-bundle-output.json exists and ok=true...
[92mPASS[0m  inspect-bundle-output.json ok=true
[94mINFO[0m  10. Checking validate-bundle-output.json exists and ok=true...
[92mPASS[0m  validate-bundle-output.json ok=true
[92mPASS[0m  validate-bundle-output.json has 12+ checks — 12/12 pass
[94mINFO[0m  11. Checking apply-bundle-dry-run-output.json exists...
[92mPASS[0m  apply-dry-run mode='dry-run'
[94mINFO[0m  12. Checking apply-bundle-yes-output.json exists...
[92mPASS[0m  apply-yes mode='applied'
[92mPASS[0m  apply-yes ok=true
[94mINFO[0m  13. Checking apply-target-summary.json has valid counts...
[92mPASS[0m  summary.gene_count >= 1 — 1
[92mPASS[0m  summary.capsule_count >= 1 — 1
[92mPASS[0m  summary.memory_graph_lines >= 5 — 5
[94mINFO[0m  14. Checking data/cases.json phase contains ATL-EVOMAP-5...
[92mPASS[0m  evomap case present in cases.json
[92mPASS[0m  cases.json phase references ATL-EVOMAP-5 (current or phase_history) — ATL-EVOMAP-8A Nightly Validation Loop Asset
[92mPASS[0m  cases.json status references 'local evolution kit completed' (current or via history) — nightly validation loop asset completed
[92mPASS[0m  cases.json phase_history has ATL-EVOMAP-5 entry
[94mINFO[0m  15. Checking case README contains ATL-EVOMAP-5...
[92mPASS[0m  case README contains ATL-EVOMAP-5
[94mINFO[0m  16. Scanning for secret patterns in Phase 5 artifacts...
[92mPASS[0m  no secret patterns in Phase 5 artifacts
[94mINFO[0m  17. Checking no root .evolver/ or memory/ tracked by git...
[92mPASS[0m  no root .evolver/ or memory/ tracked by git — clean
============================================================
[92mPASS[0m  ALL CHECKS PASSED
Case: evomap-evolver-openclaw-v0 (Phase 5 Local Evolution Kit)
Status: local evolution kit completed (PASS)
 |
| `phase6a_hermes_systemd_bundle` | 0 | unts...
[92mPASS[0m  summary.gene_count >= 1 — 1
[92mPASS[0m  summary.capsule_count >= 1 — 1
[92mPASS[0m  summary.memory_graph_lines >= 5 — 5
[92mPASS[0m  summary.gene_ids contains Hermes gene
[92mPASS[0m  summary.capsule_ids contains Hermes capsule
[94mINFO[0m  15. Checking case tools/ has 3 script copies...
[92mPASS[0m  case tools/evomap_inspect_bundle.py exists
[92mPASS[0m  case tools/evomap_validate_bundle.py exists
[92mPASS[0m  case tools/evomap_apply_bundle.py exists
[94mINFO[0m  16. Checking data/cases.json phase + phase_history for ATL-EVOMAP-6A...
[92mPASS[0m  evomap case present in cases.json
[92mPASS[0m  cases.json phase contains ATL-EVOMAP-6A (top-level or phase_history) — ATL-EVOMAP-8A Nightly Validation Loop Asset
[92mPASS[0m  cases.json status contains 'hermes systemd bundle completed' (or phase_history has 6A) — nightly validation loop asset completed
[92mPASS[0m  cases.json final_status contains HERMES_SYSTEMD_BUNDLE_PASS (or phase_history has 6A) — NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS
[92mPASS[0m  cases.json phase_history has ATL-EVOMAP-6A entry
[92mPASS[0m  phase_history ATL-EVOMAP-6A result == PASS
[92mPASS[0m  phase_history ATL-EVOMAP-6A has gene_id
[92mPASS[0m  phase_history ATL-EVOMAP-6A has capsule_id
[92mPASS[0m  phase_history ATL-EVOMAP-6A has evolver_smoke
[94mINFO[0m  17. Checking case README contains ATL-EVOMAP-6A...
[92mPASS[0m  case README contains ATL-EVOMAP-6A
[92mPASS[0m  case README contains '6A' row in phase table
[94mINFO[0m  18. Scanning for secret patterns in Phase 6A artifacts...
[92mPASS[0m  no secret patterns in Phase 6A artifacts
[94mINFO[0m  19. Checking no root .evolver/ or memory/ tracked by git...
[92mPASS[0m  no root .evolver/ or memory/ tracked by git — clean
============================================================
[92mPASS[0m  ALL CHECKS PASSED
Case: evomap-evolver-openclaw-v0 (Phase 6A Hermes Systemd Bundle)
Status: hermes systemd bundle completed (PASS)
 |
| `phase6b_telegram_router_bundle` | 0 | 92mPASS[0m] 6. gene artifact contains expected gene id
          got id='gene_distilled_telegram-message-router-failure'
  [[92mPASS[0m] 7. capsule artifact contains expected capsule id
          got id='capsule_telegram_message_router_failure_phase6b'
  [[92mPASS[0m] 8. capsule execution_trace non-empty with >= 4 steps
          len=4
  [[92mPASS[0m] 9. bundle JSON valid with gene + capsule + schema_version
          schema='atl-evomap-portable-bundle-v0.1'
  [[92mPASS[0m] 10. inspect-bundle output ok == true
          ok=True
  [[92mPASS[0m] 11. validate-bundle output ok == true
          ok=True, failures=0
  [[92mPASS[0m] 12. apply dry-run output present and mode == dry-run
          mode='dry-run', ok=True
  [[92mPASS[0m] 13. apply --yes output present and mode == applied
          mode='applied', ok=True
  [[92mPASS[0m] 14. apply target summary: gene_count >= 1 and capsule_count >= 1
          gene_count=1, capsule_count=1
  [[92mPASS[0m] 15. case report exists
          cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/ATL_EVOMAP_6B_TELEGRAM_ROUTER_BUNDLE_REPORT.md
  [[92mPASS[0m] 15. top-level report exists
          reports/ATL_EVOMAP_6B_TELEGRAM_ROUTER_BUNDLE_REPORT.md
  [[92mPASS[0m] 16. case README exists
          cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/README.md
  [[92mPASS[0m] 17. data/cases.json contains ATL-EVOMAP-6B in phase or phase_history
          top_phase='ATL-EVOMAP-8A Nightly Validation Loop Asset', history_count=18
  [[92mPASS[0m] 18. main case README references ATL-EVOMAP-6B
          main README len=65607
  [[92mPASS[0m] 19. secret scan: no Telegram credential / recipient id / API key / Authorization / private key in committed files
          scanned=16 files, hits=0

[92mPASS[0m  ALL CHECKS PASSED
Case: evomap-evolver-openclaw-v0 (Phase 6B Telegram Message Router Failure Bundle)
Status: nightly validation loop asset completed (NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS)
 |
| `phase6c_codex_test_failure_bundle` | 0 | ists and contains 'capsule_codex_test_failure_loop_phase6c'
          id=capsule_codex_test_failure_loop_phase6c, type=Capsule
  [[92mPASS[0m] 14. capsule.execution_trace is non-empty list with >= 4 steps
          type=list, len=4
  [[92mPASS[0m] 15. bundle/codex-test-failure-loop.bundle.json exists and JSON is valid
          schema_version=atl-evomap-portable-bundle-v0.1
  [[92mPASS[0m] 16. inspect-codex-bundle-output.json exists and ok=true
          ok=True
  [[92mPASS[0m] 17. validate-codex-bundle-output.json exists and ok=true
          ok=True, failures=[]
  [[92mPASS[0m] 18. apply-codex-bundle-dry-run-output.json exists and ok=true & mode=generic_plus_domain_from_bundle
          ok=True, mode=generic_plus_domain_from_bundle
  [[92mPASS[0m] 19. apply-codex-bundle-yes-output.json exists and ok=true & mode=generic_plus_domain_from_bundle & gene=1 & capsule=1 & 27 memory signals
          ok=True, mode=generic_plus_domain_from_bundle, gene=1, cap=1, mem=27
  [[92mPASS[0m] 20. apply-codex-target-summary.json: gene_count >= 1, capsule_count >= 1
          gene_count=1, capsule_count=1
  [[92mPASS[0m] 21. apply-codex-target-summary.json signals contain test_failure, repeated_test_failure, failing_assertion, fix_one_break_another, final_green_test_missing
          all 5 required signals present in 25 distinct signals
  [[92mPASS[0m] 22. evolver-run-codex-target-output.txt contains 'No hub match' or 'no_hub_url' (combined smoke no-Hub confirmation)
          found in evolver run output
  [[92mPASS[0m] 23. data/cases.json + main case README + secret scan + git status + 5 prior validators (composite)
          data/cases.json_6c=True, main_README_6c=True, secret_scan=23 files, 0 hits, git_root_evolver_or_memory_tracked=False, 5_prior_validators=PASS

[92mPASS[0m  ALL CHECKS PASSED
Case: evomap-evolver-openclaw-v0 (Phase 6C Codex Test Failure Loop Bundle)
Status: nightly validation loop asset completed (NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS)
 |
| `phase7a_domain_signal_injection` | 0 | ain_from_bundle
          ok=True, mode=generic_plus_domain_from_bundle
  [[92mPASS[0m] 9. hermes-domain --yes: ok & mode=generic_plus_domain_from_bundle
          ok=True, mode=generic_plus_domain_from_bundle
  [[92mPASS[0m] 10. hermes target summary contains systemd_failure / missing_env_var / port_not_listening
          all 3 present in 17 signals
  [[92mPASS[0m] 11. telegram-domain dry-run: ok & mode=generic_plus_domain_from_bundle
          ok=True, mode=generic_plus_domain_from_bundle
  [[92mPASS[0m] 12. telegram-domain --yes: ok & mode=generic_plus_domain_from_bundle
          ok=True, mode=generic_plus_domain_from_bundle
  [[92mPASS[0m] 13. telegram target summary contains telegram_failure / proxy_mismatch / delivery_terminal_missing / sendmessage_timeout
          all 4 present in 27 signals
  [[92mPASS[0m] 14. domain-signal-extraction-summary: hermes+telegram injected, default preserved, no hub/approve/solidify
          default=True hermes=True telegram=True hub=disabled
  [[92mPASS[0m] 15. data/cases.json contains ATL-EVOMAP-7A in phase or phase_history
          top_phase='ATL-EVOMAP-8A Nightly Validation Loop Asset', history_count=18
  [[92mPASS[0m] 16. main case README references ATL-EVOMAP-7A
          main README len=65607
  [[92mPASS[0m] 17. secret scan: no Telegram credential / recipient id / API key / Authorization / private key in committed files
          scanned=24 files, hits=0
  [[92mPASS[0m] 18. git status: no root .evolver/ or memory/ tracked
          clean
  [[92mPASS[0m] 19. Phase 5 validator ALL CHECKS PASSED (backward-compat)
          returncode=0, output_tail=Status: local evolution kit completed (PASS)
  [[92mPASS[0m] 20. Phase 6A + 6B validators ALL CHECKS PASSED (backward-compat)
          6A_rc=0, 6B_rc=0

[92mPASS[0m  ALL CHECKS PASSED
Case: evomap-evolver-openclaw-v0 (Phase 7A Domain-Specific Signal Injection)
Status: nightly validation loop asset completed (NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS)
 |
| `phase7b_cross_bundle_regression` | 0 | icate_gene_ids=[]
  [[92mPASS[0m] 13. duplicate_capsule_ids == []
          duplicate_capsule_ids=[]
  [[92mPASS[0m] 14. required_openclaw_signals_present == true
          missing=[]
  [[92mPASS[0m] 15. required_hermes_signals_present == true
          missing=[]
  [[92mPASS[0m] 16. required_telegram_signals_present == true
          missing=[]
  [[92mPASS[0m] 17. dangerous_signals == []
          dangerous_signals=[]
  [[92mPASS[0m] 18. pollution_signals == []
          pollution_signals=[]
  [[92mPASS[0m] 19. cross-bundle-regression-summary.json exists with status & scoring & probes
          status=PASS
  [[92mPASS[0m] 20. evolver-run-cross-bundle-output.txt exists
          cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/evolver-run-cross-bundle-output.txt
  [[92mPASS[0m] 21. evolver-review-cross-bundle-output.txt exists
          cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/evolver-review-cross-bundle-output.txt
  [[92mPASS[0m] 22. combined smoke output contains 'No hub match' or 'no_hub_url' (no Hub confirmation)
          found in evolver-run output
  [[92mPASS[0m] 23. data/cases.json phase contains 'ATL-EVOMAP-7B' (top or history)
          top_phase='ATL-EVOMAP-8A Nightly Validation Loop Asset', history_count=18
  [[92mPASS[0m] 24. main case README references ATL-EVOMAP-7B
          main README len=65607
  [[92mPASS[0m] 25. secret scan: no Telegram credential / recipient id / API key / cookie / Authorization / private key in committed files
          scanned=26 files, hits=0
  [[92mPASS[0m] 26. git status: no root .evolver/ or memory/ tracked
          clean
  [[92mPASS[0m] 27. prior validators (5, 6A, 6B, 7A) ALL CHECKS PASSED (backward-compat)
          4/4 prior validators PASS

[92mPASS[0m  ALL CHECKS PASSED
Case: evomap-evolver-openclaw-v0 (Phase 7B Cross-Bundle Regression)
Status: nightly validation loop asset completed (NIGHTLY_VALIDATION_LOOP_ASSET_SMOKE_PASS)
 |

## Bundle inspect / validate

| Bundle | Path | inspect rc | validate rc |
|--------|------|------------|-------------|
| `openclaw_tool_use_discipline` | `cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json` | 0 | 0 |
| `hermes_systemd_recovery` | `cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json` | 0 | 0 |
| `telegram_message_router_failure` | `cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json` | 0 | 0 |
| `codex_test_failure_loop` | `cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json` | 0 | 0 |

## Secret scan

- **Scanned file count:** 301
- **Allowed timestamp hits:** 21
- **Skipped:** {'binary': 84, 'image': 0, 'too_large': 0, 'io_error': 0}
- **Hits:** {}

## Git

- **Tracked file count:** 385
- **git status --short line count:** 6 (informational; this run produces new artifacts)

## Hard boundaries (declared in this run)

- `no_a2a_hub_url`: YES
- `no_atp_autobuy`: YES
- `no_auto_publish`: YES
- `no_credit_consumption`: YES
- `no_crontab_write`: YES
- `no_curl_or_http_calls`: YES
- `no_env_file_content_scanned`: YES
- `no_evolver_loop`: YES
- `no_evolver_package_source_modify`: YES
- `no_evolver_review`: YES
- `no_evolver_review_approve`: YES
- `no_evolver_run`: YES
- `no_evolver_solidify`: YES
- `no_hub_connection`: YES
- `no_online_coding_apis`: YES
- `no_real_credentials_read`: YES
- `no_real_cron_install`: YES
- `no_real_test_runners`: YES
- `no_runtime_evolver_or_memory_tracked`: YES
- `no_systemd_timer_create`: YES
- `no_telegram_api`: YES
- `stdlib_only`: YES

## Notes

- This digest is **machine-generated by the nightly validation loop runner** (per ATL-EVOMAP-8A spec, schema `atl-evomap-nightly-validation-v0.1`).
- This phase ships the runner + dry-run cron example; **no real cron / systemd timer is installed**.
- Any scheduling is operator-owned and must be performed in a separate explicit phase (e.g. ATL-EVOMAP-8B).

- **Digest files:** `nightly-validation-digest.json` and `nightly-validation-digest.md` in the same directory as this Markdown file.
