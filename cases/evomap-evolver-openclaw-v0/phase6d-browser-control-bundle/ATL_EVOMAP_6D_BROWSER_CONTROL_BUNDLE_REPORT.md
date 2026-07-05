# ATL-EVOMAP-6D — Browser-Control Recovery Bundle

> **Final status:** `BROWSER_CONTROL_BUNDLE_PASS`
> **Base commit:** `b34c4a3` (post-ATL-EVOMAP-9B)
> **Bundle schema:** `atl-evomap-portable-bundle-v0.1`
> **Bundle id (target):** `gene_distilled_browser-control-recovery` + `capsule_browser_control_recovery_phase6d`

This report documents the 5th canonical portable bundle in the
OpenClaw / Hermes Local Evolution Kit. It ships offline
browser-control failure modeling, a deterministic fixture, a
stdlib-only parser with safety guards, a portable bundle, and the
nightly canonical blocking lane extension from 4 → 5 bundles — all
without launching a real browser, contacting 127.0.0.1:18791, or
performing any network call.

---

## 1. Goal

Codify OpenClaw / Hermes browser-control recovery discipline as a
**canonical portable bundle** and bind it into the Phase 8A nightly
validation runner alongside the existing 4 canonical bundles. Keep the
Phase 9A canary lane unchanged (non-blocking).

## 2. Phase 9B unlock conditions satisfied

- ATL-EVOMAP-9B `CURATOR_NIGHTLY_INTEGRATION_SMOKE_PASS` (commit
  `b34c4a3`).
- `evomap_nightly_validate.py` runs with 4 canonical + 1 canary and
  9 blocking checks.
- Curator-generated `sample-safe-bundle-phase9a` is exposed via
  `canary_bundles[]` in the nightly manifest and is **non-blocking**.

Phase 6D extends the canonical lane to 5 bundles (browser-control
recovery) while leaving the canary lane and 9 blocking checks
untouched. Two existing validators were updated with
**forward-compatible** changes only (no reduction in artifact /
secret / report checks).

## 3. Browser-control failure model

Covered failure signatures:

| Signal | Description |
|--------|-------------|
| `browser_control_port_unavailable` | browser-control endpoint (127.0.0.1:18791) unreachable |
| `browser_control_auth_missing` | client request had no usable auth token |
| `browser_launch_timeout` | on-demand browser instance did not become ready |
| `browser_instance_not_running` | instance ended in `not_running` |
| `navigation_timeout` | navigation did not complete |
| `screenshot_missing` | no screenshot artifact captured |
| `page_snapshot_missing` | no page snapshot artifact captured |
| `fallback_bypass_attempted` | curl / raw HTTP fallback attempted |
| `fallback_allowed` | forced to `false` when bypass attempted |
| `terminal_page_evidence_missing` | no terminal page evidence captured |
| `final_success_missing` | no final success evidence captured |

The Gene also lists the corresponding colon-form signals
(`browser_control_port_unavailable:18791`,
`browser_control_auth_missing:token-required`,
`browser_launch_timeout:on-demand`, etc.).

## 4. Offline fixture + parser

- **Fixture:**
  `cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/fixtures/browser-control-recovery-sample.txt`
  (2477 bytes, 3 attempts, all 3 distinct failure modes).
- **Parser:**
  `scripts/browser_control_recovery_fixture.py`
  (Python stdlib only, CLI `--input PATH`, no recursion, no env
  reading, no network).
- **Parser output (verified, ok=true):**

```
component: openclaw-browser-control
attempt_count: 3
browser_control_failure: true
browser_control_port_unavailable: true
browser_control_auth_missing: true
browser_launch_timeout: true
browser_instance_not_running: true
navigation_timeout: true
screenshot_missing: true
page_snapshot_missing: true
fallback_bypass_attempted: true
fallback_allowed: false
terminal_page_evidence_missing: true
final_success_missing: true
failure_signatures:
  - browser_control_port_unavailable_18791
  - browser_control_auth_missing
  - browser_launch_timeout
recommended_check_order: 7 entries
safety: all true (no_real_browser_launch, no_port_connection,
                  no_http_request, no_curl_wget, no_env_scan,
                  no_secret_echo, fixture_only)
```

## 5. Parser self-tests (3/3 PASS as designed)

| Input | Expected | Observed |
|-------|----------|----------|
| Authorization header value | `ok=false, reason=unsafe_fixture` | PASS |
| Cookie assignment value | `ok=false, reason=unsafe_fixture` | PASS |
| `.env`-named path | `ok=false, reason=refused_input_path` | PASS |

All three selftest artifacts in
`cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/artifacts/parser-selftest-*-output.json`
contain only sanitized metadata; no original unsafe string is
echoed. Inputs are created in `/tmp` via Python at runtime and
are never committed.

## 6. Gene design

`gene_distilled_browser-control-recovery` (category `repair`):

- 26 `signals_match` (13 base + 13 colon-form).
- 7 strategy entries (e.g. "Separate gateway health from
  browser-control readiness before retrying.").
- Constraints: `max_files=8`,
  `forbidden_paths=[.git, node_modules, .evolver, memory, .env,
  real_runtime_root]`, `forbidden_actions` block real launches,
  port connections, http calls, env reads, token echoing, curl
  bypasses, and claiming success without page evidence.

## 7. Capsule design

`capsule_browser_control_recovery_phase6d`:

- `schema_version=1.6.0`, `status=success`, `confidence=0.84`,
  `visibility=private`, `source=manual_capsule_seed_phase6d`.
- `blast_radius = {files:0, lines:0}`.
- `execution_trace` has 4 steps:
  1. `build` (parse fixture)
  2. `validate` (JSON parse)
  3. `validate` (assert expected browser-control failure shape)
  4. `canary` (safety check covering
     `no_hub/no_publish/no_approve/no_solidify` + the full
     no-browser/no-port/no-http/no-curl/no-env/no-secret list).

## 8. Bundle schema

`cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json`
(10869 bytes):

- `schema_version=atl-evomap-portable-bundle-v0.1`
- `source_phase=ATL-EVOMAP-6D`,
  `source_session=/tmp/atl-evomap-phase6d-browser-control-target`
- `target_gene_id=gene_distilled_browser-control-recovery`
- `target_capsule_id=capsule_browser_control_recovery_phase6d`
- embeds the full `gene`, `capsule`, `execution_trace`,
  `fixture_summary`, `safety`, `import_contract`, and
  `kit_provenance` (with `phase_9b_commit=b34c4a3`).
- `safety.hub=disabled`, `publish=disabled`, `credits=0`,
  `visibility=private`,
  `no_failed_events/no_pollution_signals/no_real_browser_launch/no_port_connection/no_http_request/no_curl_wget/no_env_scan/no_secrets`
  all `true`.

## 9. inspect / validate result

- `inspect` output: `ok=true`, full bundle metadata surfaced.
- `validate` output: `ok=true`, `secret_hits=0`, no token / key /
  auth / cookie leakage detected.

## 10. apply dry-run / apply --yes result

`target=/tmp/atl-evomap-phase6d-browser-control-target` (isolated
`/tmp` git init, not part of the project repo):

- dry-run: `ok=true`, plan lists 1 new gene + 1 new capsule, 29
  memory_graph_signals (5 generic + 24 domain, 2 domain signals
  rejected for containing the dangerous substrings `auth` /
  `token` — the safety mechanism is operating correctly).
- --yes: `ok=true`, writes executed for
  `.evolver/gep/genes.json`,
  `.evolver/gep/capsules.json`,
  `memory/evolution/memory_graph.jsonl`,
  `.evolver/gep/events.jsonl`,
  `.evolver/gep/failed_capsules.json`,
  `.evolver/gep/candidates.jsonl`.
- target summary (verified):
  - `gene_count=1`
  - `capsule_count=1`
  - `memory_graph_lines=29`
  - `distinct_signals=27`
  - signals include all required ones
    (`browser_control_failure`, `browser_control_port_unavailable`,
    `browser_control_auth_missing`, `browser_launch_timeout`,
    `screenshot_missing`, `terminal_page_evidence_missing`,
    `browser_control_failure:openclaw`,
    `browser_control_port_unavailable:18791`, …).

## 11. Nightly canonical lane update (4 → 5 bundles)

`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/validation-loop-manifest.json`:

- `bundles[]` extended with the 6D bundle.
- `versioning.manifest_version`: `0.2.0 → 0.3.0`.
- `versioning.compatible_runner_min`: `0.3.0`.
- `versioning.next_intended_phase`: `Phase 6E (proposed: more
  domain curator specs / canary apply gate / operator-led real
  cron install)`.
- `extended_by_phase`: `ATL-EVOMAP-6D`.
- `phase`: `ATL-EVOMAP-6D (Browser-Control Recovery Bundle added
  as 5th canonical bundle; Phase 9B canary lane unchanged)`.
- `checks_detail.bundle_count_expected`: `5`.

`scripts/evomap_nightly_validate.py`:

- `_resolve_bundle_paths` is now **manifest-driven**; the original
  4 paths remain as a backward-compat fallback.
- `extended_by_phase` is read from the manifest.
- CLI flags unchanged (`--repo-root`, `--out-dir`,
  `--markdown-name`, `--json-name`, `--strict`, `--dry-run`,
  `--output-dir`).
- stdlib-only constraint preserved.

Forward-compatible validator updates:

- `validate_evomap_phase8a_nightly_validation_loop.py`:
  canonical-bundle check now requires the **original 4** AND **at
  least one Phase 6D+ additional canonical bundle**, instead of
  hardcoded 4.
- `validate_evomap_phase9b_curator_nightly_integration.py`:
  digest `bundle_checks.inspect / validate` length updated
  `4 → 5`.

No existing artifact, secret-scan, or report check was lowered.

## 12. Nightly smoke result (5 canonical + 1 canary)

`cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/artifacts/nightly-smoke/`:

```
overall_status       : PASS
schema_version       : atl-evomap-nightly-validation-v0.1
extended_by_phase    : ATL-EVOMAP-6D
blocking_total       : 9
blocking_passed      : 9
blocking_failed      : 0
validator_count      : 7
validators_passed    : 7
bundle_inspect_count : 5
bundle_validate_count: 5
canary_total         : 1
canary_passed        : 1
canary_failed        : 0
canary_status        : CANARY_PASS
canary_blocking_failures : 0
canary_non_blocking_failures : 0
secret_scan          : hits=0
git_hygiene          : PASS
hard_boundaries      : all YES (22 fields)
```

Canonical lane (5 blocking bundles, all inspect + validate PASS):

| # | Bundle |
|---|--------|
| 1 | `openclaw-tool-use-discipline` |
| 2 | `hermes-systemd-service-recovery` |
| 3 | `telegram-message-router-failure` |
| 4 | `codex-test-failure-loop` |
| 5 | **`browser-control-recovery`** |

Canary lane (unchanged, 1/1 PASS):

| Bundle | inspect | validate | apply_dry_run | Blocking |
|--------|---------|----------|---------------|----------|
| `sample-safe-bundle-phase9a` | PASS | PASS | PASS | no |

## 13. Safety boundaries

All 26 hard boundaries from the task spec are respected:

- No EvoMap Hub connection, no `A2A_HUB_URL`.
- No `evolver run` / `review` / `--approve` / `solidify`.
- No `auto-publish`, no credit consumption, no ATP autobuy.
- No OpenAI / Codex / GitHub Copilot / Telegram API.
- No `curl` / `wget` / HTTP requests.
- No real browser launch, no contact with 127.0.0.1:18791.
- No real test runners (`pytest`, `npm test`, `cargo test`,
  `go test`, `mvn test`).
- No `.env` reads, no real key/token/cookie/Authorization/private
  key reads or writes.
- No real OpenClaw / Hermes / systemd / cron config changes.
- No cron install, no systemd timer creation.
- No evolver package source modification.
- No runtime `.evolver/` or `memory/` committed to git.
- All new tools Python stdlib only.

## 14. Final conclusion

`ATL-EVOMAP-6D` is **PASS**. The 5th canonical bundle
(`browser-control-recovery`) is shipped, integrated into the
nightly blocking lane (5/5 inspect + 5/5 validate), with the Phase
9A canary lane preserved (1/1, non-blocking). All 9 blocking
checks and 7 phase validators pass; secret scan is clean, git
hygiene is clean, and all 22 hard-boundary fields are
`YES`/`disabled`/`0`/`true` as appropriate.

## 15. Next steps

- **Phase 6E (proposed):** more domain curator specs (e.g.
  Codex-tools, MCP-tools) following the 6D pattern.
- **Phase 9C (proposed):** curator-driven canary apply + operator
  gate; still no auto-publish, no Hub, no credits.
- **Phase 8B (operator-led, NOT in this phase):** real cron
  install; this phase only ships the manifest
  (`templates/cron.example`) and never installs.

---

*Document generated by ATL-EVOMAP-6D execution. See also:
- `cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/README.md`
- `reports/ATL_EVOMAP_6D_BROWSER_CONTROL_BUNDLE_REPORT.md`*
