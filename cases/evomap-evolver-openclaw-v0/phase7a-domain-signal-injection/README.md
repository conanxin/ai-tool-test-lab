# ATL-EVOMAP-7A · Domain-Specific Signal Injection

**Status:** domain signal injection completed (PASS)
**Date:** 2026-06-19
**Base:** `f72b0c1` (ATL-EVOMAP-6B)

## Goal

Enhance the Phase 5 apply tool (`scripts/evomap_apply_bundle.py`) so it can
inject domain-specific signals extracted from any bundle (Hermes systemd,
Telegram router, future Codex / browser-control bundles) into
`memory/evolution/memory_graph.jsonl`, without breaking the Phase 5/6A/6B
generic baseline.

## New CLI flag

```
--inject-signals-from <bundle.json>
```

- **Without it:** tool behaves exactly as before — 5 generic bare signals only
  (`signal_injection_mode: generic_only`).
- **With it:** tool reads `bundle.gene.signals_match` + `bundle.capsule.trigger`,
  filters them through a strict validator, and writes 5 generic + N domain
  signals (`signal_injection_mode: generic_plus_domain_from_bundle`).

## Why this matters

After Phase 6B the apply tool injected only the 5 generic bare signals. The
Hermes / Telegram domain signals (e.g. `systemd_failure`, `telegram_failure`,
`proxy_mismatch`, `delivery_terminal_missing`) lived only in
`gene.signals_match` and `capsule.trigger` and never reached
`memory_graph.jsonl`. As a result, the evolver selector had nothing better to
match on than `tool_bypass` and the `distilled_fallback` path.

After Phase 7A, those domain signals actually reach the selector — confirmed
by the evolver run output (`signals include telegram_failure,
telegram_failure:delivery-timeout, delivery_terminal_missing:telegram,
sendmessage_timeout:telegram-response`).

## Filter engine

Implemented inside `plan_apply`:

1. **Allowed chars:** `^[A-Za-z0-9_:\-\.]{1,120}$` (namespaced names like
   `missing_env_var:MODEL_PROVIDER` and `proxy_mismatch:sendmessage-sendvoice`
   are allowed).
2. **Dangerous signals denylist (21 entries):** `user_feature_request`,
   `consecutive_failure`, `consecutive_failure_streak`, `high_failure_ratio`,
   `stable_success_plateau`, `evolution_saturation`, `explore_opportunity`,
   `memory_missing`, `hub_search_miss_with_problem`, `hub_search_miss`,
   `hub_unavailable`, `no_hub_url`, `no_hub_match`, `validation_skipped`,
   `approval_skipped`, `publish_skipped`, `credits_zero`, `atp_autobuy_off`,
   `loop_disabled`, `validator_disabled`, `dry_run_default`. Rejected.
3. **Dangerous substrings (13 entries):** `token`, `secret`, `cookie`,
   `authorization`, `auth`, `private_key`, `api_key`, `apikey`, `bearer`,
   `password`, `passwd`, `ssh-rsa`, `ssh-ed25519`. Rejected.
4. **Credential regex (6 patterns, case-insensitive):**
   - Telegram bot token shape: `\d{6,12}:[A-Za-z0-9_-]{20,}`
   - HTTP `Authorization: …`
   - API key prefixes: `sk-…`, `sk_live_…`, `ghp_…`, `github_pat_…`
   - JWT: `eyJ…`
   - `-----BEGIN …PRIVATE KEY-----`
   - 12+ digit pure-digit recipient-like IDs

Domain signal `origin` is set to `evomap_apply_bundle:domain_from_bundle` so
consumers can distinguish them from the legacy `openclaw_signal_detector`
origin.

## Self-test results

| Target bundle | Mode | Generic | Domain | Total | Rejected |
|--|--|--|--|--|--|
| Phase 5 OpenClaw tool-use discipline (no flag) | `generic_only` | 5 | 0 | 5 | 0 |
| Phase 6A Hermes systemd | `generic_plus_domain_from_bundle` | 5 | 12 | 17 | 0 |
| Phase 6B Telegram router | `generic_plus_domain_from_bundle` | 5 | 22 | 27 | 0 |

All required domain signals confirmed present in target `memory_graph.jsonl`:
- **Hermes:** `systemd_failure`, `service_recovery`, `missing_env_var`,
  `missing_env_var:MODEL_PROVIDER`, `port_not_listening`,
  `dropin_env_misconfigured`
- **Telegram:** `telegram_failure`, `message_router_failure`, `proxy_mismatch`,
  `delivery_terminal_missing`, `sendmessage_timeout`, `retry_consumed`,
  `smoke_not_confirmed`, `proxy_mismatch:sendmessage-sendvoice`

## Evolver smoke

- **Hermes target:** `Selected Gene "gene_distilled_hermes-systemd-service-recovery"`,
  `[SearchFirst] No hub match (reason: no_hub_url)`, no `--approve`, no
  `solidify`. memory_graph 17 → 20 lines after evolver run cycles.
- **Telegram target:** `Selected Gene "gene_distilled_telegram-message-router-failure"`,
  `[SearchFirst] No hub match (reason: no_hub_url)`, no `--approve`, no
  `solidify`. memory_graph 27 → 30 lines after evolver run cycles. **Domain
  signals visible in evolver run's signal-match output.**

## On-disk target verify

```
default: /tmp/atl-evomap-7a-default-apply-target  → 1 gene, 1 capsule, memory_graph_lines=5
hermes:  /tmp/atl-evomap-7a-hermes-domain-target  → 1 gene, 1 capsule, memory_graph_lines=17 (5+12)
telegram:/tmp/atl-evomap-7a-telegram-domain-target→ 1 gene, 1 capsule, memory_graph_lines=27 (5+22)
```

## Usage

```bash
# Default (Phase 5/6A/6B behavior — 5 generic signals only)
python3 scripts/evomap_apply_bundle.py \
    --bundle <bundle.json> \
    --target-runtime <path> \
    --dry-run

# Phase 7A: also inject domain-specific signals
python3 scripts/evomap_apply_bundle.py \
    --bundle <bundle.json> \
    --inject-signals-from <bundle-or-summary.json> \
    --target-runtime <path> \
    --dry-run
python3 scripts/evomap_apply_bundle.py \
    --bundle <bundle.json> \
    --inject-signals-from <bundle-or-summary.json> \
    --target-runtime <path> \
    --yes
```

## What we explicitly do NOT do

- ❌ Do not call EvoMap Hub (no A2A_HUB_URL).
- ❌ Do not publish bundles or capsules.
- ❌ Do not consume credits.
- ❌ Do not auto-buy ATP.
- ❌ Do not enable validator.
- ❌ Do not run evolver with `--loop`.
- ❌ Do not write credentials, chat ids, API keys, cookies, Authorization
  headers, or private keys to `memory_graph.jsonl`.
- ❌ Do not write dangerous / pollution signals (`consecutive_failure*`,
  `evolution_saturation`, `hub_search_miss*`, etc.) even if they appear in
  the source bundle.
- ❌ Do not modify the Evolver package source.
- ❌ Do not run `evolver review --approve` or `evolver solidify`.
- ❌ Do not commit runtime `.evolver/` or `memory/` originals.

## Files

- **Modified tool:** `scripts/evomap_apply_bundle.py` (now 17.5 KB; CLI gained
  `--inject-signals-from`; plan output gained `signal_injection_mode` +
  `generic_signals` + `domain_signals` + `domain_signals_rejected`)
- **Validator:** `scripts/validate_evomap_phase7a_domain_signal_injection.py`
- **Report (case dir):** `ATL_EVOMAP_7A_DOMAIN_SIGNAL_INJECTION_REPORT.md`
- **Report (top-level):** `reports/ATL_EVOMAP_7A_DOMAIN_SIGNAL_INJECTION_REPORT.md`
- **Artifacts (13):** under `artifacts/`
  - `inspect-*-bundle-output.json` (×2: Hermes, Telegram)
  - `validate-*-bundle-output.json` (×2: Hermes, Telegram)
  - `default-apply-{dry-run,yes,target-summary}-output.json` (×3)
  - `hermes-domain-{dry-run,yes,target-summary}-output.json` (×3)
  - `telegram-domain-{dry-run,yes,target-summary}-output.json` (×3)
  - `domain-signal-extraction-summary.json` (master summary)
  - `evolver-{run,review}-{hermes,telegram}-domain-output.txt` (×4)

## Next steps

1. **Cross-bundle regression test** — apply all 3 bundles to a single fresh
   isolated target, verify no signal/gene/capsule id collision, count distinct
   signals.
2. **`bundle-curator` skill** — auto-generate portable bundles from evolver
   run outputs.
3. **Codex `prompt-cache-discipline` bundle** (optimize).
4. **Browser-control `rate-limit-recovery` bundle** (repair).
