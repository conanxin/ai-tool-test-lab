# ATL-EVOMAP-6D — Browser-Control Recovery Bundle

> **Status (committed):** Browser-control recovery bundle completed
> **Final status:** `BROWSER_CONTROL_BUNDLE_PASS`
> **Base commit:** `b34c4a3` (post-ATL-EVOMAP-9B curator-to-nightly integration)
> **Bundle schema:** `atl-evomap-portable-bundle-v0.1`

Phase 6D ships the **5th canonical portable bundle** for the EvoMap Local
Evolution Kit. It codifies OpenClaw / Hermes browser-control recovery
discipline, covering port / auth / launch / navigation / screenshot
evidence, plus an anti-curl / anti-raw-HTTP bypass constraint.

After Phase 6D, the nightly canonical blocking lane runs **5 bundles**
plus 1 non-blocking canary bundle (Phase 9A `sample-safe-bundle-phase9a`).

---

## 1. What this phase does

1. **Defines a browser-control failure model** drawn from typical
   OpenClaw / Hermes automation failure modes:
   - `browser_control_port_unavailable` (127.0.0.1:18791 not listening)
   - `browser_control_auth_missing` (token not wired or unreadable)
   - `browser_launch_timeout` (on-demand browser fails to become ready)
   - `browser_instance_not_running` (idle vs failed-launch ambiguity)
   - `navigation_timeout`
   - `screenshot_missing` / `page_snapshot_missing`
   - `fallback_bypass_attempted` (curl / raw HTTP fallbacks)
   - `terminal_page_evidence_missing` / `final_success_missing`

2. **Ships a deterministic offline fixture** (no real browser, no real
   port, no real network) at
   `fixtures/browser-control-recovery-sample.txt`.

3. **Ships a stdlib-only offline parser** at
   `scripts/browser_control_recovery_fixture.py` that:
   - reads only the fixture text via `--input`,
   - refuses `.env` / `env.local` paths (unless basename contains
     `fixture` or `sample`),
   - refuses content with sk-/ghp_/Authorization/cookie/JWT/private-key
     or 12+ digit pure-numeric secrets,
   - never echoes the original unsafe line,
   - never connects to any port,
   - emits a sanitized JSON summary.

4. **Bundles a Gene + Capsule + portable bundle** that fit the existing
   `apply_bundle.py` chain:
   - `artifacts/gene-browser-control-recovery.json`
   - `artifacts/capsule-browser-control-recovery.json` (4 execution_trace
     steps: build / validate / validate / canary)
   - `bundle/browser-control-recovery.bundle.json` (schema
     `atl-evomap-portable-bundle-v0.1`)

5. **Adds the bundle to the nightly canonical blocking lane**:
   - `validation-loop-manifest.json` `bundles[]` now has 5 entries
   - `manifest_version` bumped `0.2.0 → 0.3.0`
   - `extended_by_phase` updated to `ATL-EVOMAP-6D`
   - runner `_resolve_bundle_paths` made manifest-driven with the
     original 4 as backward-compat fallback

6. **Forward-compatible fixes** to two existing validators so that they
   accept the new bundle count without lowering any artifact / secret /
   report check:
   - `validate_evomap_phase8a_nightly_validation_loop.py`: the
     canonical-bundle check now requires the original 4 AND at least one
     Phase 6D+ additional canonical bundle, rather than hardcoded 4.
   - `validate_evomap_phase9b_curator_nightly_integration.py`: digest
     bundle_checks length updated from 4 → 5.

---

## 2. What this phase does NOT do (hard boundaries)

- ❌ Does NOT launch a real browser.
- ❌ Does NOT connect to 127.0.0.1:18791 (browser-control port) or any
  real port.
- ❌ Does NOT perform HTTP requests.
- ❌ Does NOT run `curl` / `wget` / any network tool.
- ❌ Does NOT run `evolver run` / `evolver review` / `--approve` /
  `solidify` / `auto-publish` / consume ATP credits.
- ❌ Does NOT call OpenAI / Codex / GitHub Copilot / any online coding
  API.
- ❌ Does NOT call Telegram API.
- ❌ Does NOT install cron or create a systemd timer.
- ❌ Does NOT modify real OpenClaw / Hermes / systemd / cron config.
- ❌ Does NOT read `.env` files.
- ❌ Does NOT read real API keys / tokens / cookies / Authorization
  headers / private keys.
- ❌ Does NOT run real `pytest` / `npm test` / `cargo test` /
  `go test` / `mvn test`.
- ❌ Does NOT modify the evolver package source.
- ❌ Does NOT track runtime `.evolver/` or `memory/` paths in git.
- ✅ Python stdlib only.

---

## 3. Failure model covered

| Signal | Description |
|--------|-------------|
| `browser_control_failure` | Top-level umbrella flag |
| `browser_control_port_unavailable` | browser-control endpoint unreachable |
| `browser_control_auth_missing` | client request lacked usable token |
| `browser_launch_timeout` | on-demand browser did not become ready |
| `browser_instance_not_running` | browser instance ended in not_running |
| `navigation_timeout` | navigation did not complete |
| `screenshot_missing` | no screenshot artifact captured |
| `page_snapshot_missing` | no page snapshot artifact captured |
| `fallback_bypass_attempted` | curl / raw HTTP fallback attempted |
| `fallback_allowed` | forced to `false` when bypass attempted |
| `terminal_page_evidence_missing` | no terminal page evidence captured |
| `final_success_missing` | no final success evidence captured |

---

## 4. How to use

### 4.1 Parse the offline fixture

```bash
python3 scripts/browser_control_recovery_fixture.py \
    --input cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/fixtures/browser-control-recovery-sample.txt
```

Expected stdout (abridged):

```json
{
  "ok": true,
  "component": "openclaw-browser-control",
  "browser_control_failure": true,
  "browser_control_port_unavailable": true,
  "browser_control_auth_missing": true,
  "browser_launch_timeout": true,
  "screenshot_missing": true,
  "terminal_page_evidence_missing": true,
  "failure_signatures": [
    "browser_control_port_unavailable_18791",
    "browser_control_auth_missing",
    "browser_launch_timeout"
  ],
  "safety": {
    "no_real_browser_launch": true,
    "no_port_connection": true,
    "no_http_request": true,
    "no_curl_wget": true,
    "no_env_scan": true,
    "no_secret_echo": true,
    "fixture_only": true
  }
}
```

### 4.2 Inspect the bundle

```bash
python3 scripts/evomap_inspect_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json
```

Returns `ok=true` with full bundle metadata.

### 4.3 Validate the bundle

```bash
python3 scripts/evomap_validate_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json
```

Returns `ok=true` with `secret_hits=0`.

### 4.4 Apply dry-run / apply --yes (isolated `/tmp` only)

```bash
# target: an isolated /tmp git repo
rm -rf /tmp/atl-evomap-phase6d-browser-control-target
mkdir -p /tmp/atl-evomap-phase6d-browser-control-target
cd /tmp/atl-evomap-phase6d-browser-control-target && git init -q

cd /mnt/d/AI/ai-tool-test-lab

python3 scripts/evomap_apply_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json \
    --inject-signals-from cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json \
    --target-runtime /tmp/atl-evomap-phase6d-browser-control-target \
    --dry-run

python3 scripts/evomap_apply_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json \
    --inject-signals-from cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json \
    --target-runtime /tmp/atl-evomap-phase6d-browser-control-target \
    --yes
```

Expected target summary (verified):

```
gene_count        : 1
capsule_count     : 1
memory_graph_lines: 29
distinct_signals  : 27
signals include   : browser_control_failure, browser_launch_timeout,
                    screenshot_missing, terminal_page_evidence_missing,
                    browser_control_failure:openclaw,
                    browser_control_port_unavailable:18791, …
```

### 4.5 Run the full nightly validation (5 canonical + 1 canary)

```bash
rm -rf cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/artifacts/nightly-smoke/*
python3 scripts/evomap_nightly_validate.py \
    --repo-root . \
    --out-dir cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/artifacts/nightly-smoke \
    --strict
```

Expected:

```
overall_status       : PASS
blocking_total       : 9
bundle_inspect_count : 5
bundle_validate_count: 5
canary_total         : 1
canary_status        : CANARY_PASS
secret_scan          : hits=0
git_hygiene          : PASS
hard_boundaries      : all YES
```

---

## 5. Nightly canonical lane update (4 → 5 bundles)

| # | Bundle ID | Source phase | Path |
|---|-----------|-------------|------|
| 1 | `openclaw-tool-use-discipline` | ATL-EVOMAP-5 | `phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json` |
| 2 | `hermes-systemd-service-recovery` | ATL-EVOMAP-6A | `phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json` |
| 3 | `telegram-message-router-failure` | ATL-EVOMAP-6B | `phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json` |
| 4 | `codex-test-failure-loop` | ATL-EVOMAP-6C | `phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json` |
| 5 | **`browser-control-recovery`** | **ATL-EVOMAP-6D** | `phase6d-browser-control-bundle/bundle/browser-control-recovery.bundle.json` |

Canary lane (unchanged from Phase 9B):

| Canary ID | Source phase | Lane | Blocking |
|-----------|--------------|------|----------|
| `sample-safe-bundle-phase9a` | ATL-EVOMAP-9A | curator_generated | no |

---

## 6. Files added or modified

- `cases/evomap-evolver-openclaw-v0/phase6d-browser-control-bundle/` — new directory
  - `fixtures/browser-control-recovery-sample.txt`
  - `bundle/browser-control-recovery.bundle.json`
  - `artifacts/gene-browser-control-recovery.json`
  - `artifacts/capsule-browser-control-recovery.json`
  - `artifacts/browser-control-fixture-output.json`
  - `artifacts/parser-selftest-{auth,cookie,env-path}-output.json`
  - `artifacts/inspect-browser-control-bundle-output.json`
  - `artifacts/validate-browser-control-bundle-output.json`
  - `artifacts/apply-browser-control-bundle-{dry-run,yes}-output.json`
  - `artifacts/apply-browser-control-target-summary.json`
  - `artifacts/nightly-smoke/{nightly-validation-digest.json,nightly-validation-digest.md,nightly-validation-run.log}`
  - `artifacts/nightly-6d-smoke-summary.json`
  - `tools/{browser_control_recovery_fixture.py,evomap_inspect_bundle.py,evomap_validate_bundle.py,evomap_apply_bundle.py}`
  - `README.md`
  - `ATL_EVOMAP_6D_BROWSER_CONTROL_BUNDLE_REPORT.md`

- `scripts/browser_control_recovery_fixture.py` — new parser
- `scripts/validate_evomap_phase6d_browser_control_bundle.py` — new validator
- `scripts/evomap_nightly_validate.py` — forward-compatible: `_resolve_bundle_paths`
  now manifest-driven with the original 4 as a fallback; `extended_by_phase`
  read from manifest
- `scripts/validate_evomap_phase8a_nightly_validation_loop.py` — forward-compatible:
  canonical-bundle check now requires original 4 AND ≥1 additional canonical
- `scripts/validate_evomap_phase9b_curator_nightly_integration.py` —
  forward-compatible: digest bundle_checks length updated 4 → 5
- `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/validation-loop-manifest.json`
  — `bundles[]` extended, `manifest_version 0.2.0 → 0.3.0`,
  `extended_by_phase → ATL-EVOMAP-6D`
- `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/artifacts/nightly-validation-digest.{json,md}`
  — regenerated with 5 canonical bundles
- `data/cases.json` — phase = `ATL-EVOMAP-6D Browser-Control Recovery Bundle`,
  `final_status = BROWSER_CONTROL_BUNDLE_PASS`, `phase_history + 6D entry`
- `reports/ATL_EVOMAP_6D_BROWSER_CONTROL_BUNDLE_REPORT.md` — top-level report
- `README.md` — main case README updated with 6D row