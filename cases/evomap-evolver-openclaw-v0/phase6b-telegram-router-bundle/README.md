# Phase 6B · Telegram Message Router Failure Bundle

> Status: **telegram router bundle completed (PASS)**  
> Phase: **ATL-EVOMAP-6B**  
> Commit: `00caf1d` (Phase 6A base) + new commit (this phase)  
> Validator: `scripts/validate_evomap_phase6b_telegram_router_bundle.py` — ALL CHECKS PASSED  
> All 7 validators (3C-V2, 4A, 4B, 4C, 5, 6A, 6B) PASS

## What this bundle is

The **third canonical local-only bundle** for the OpenClaw / Hermes Local Evolution
Kit. Same schema (`atl-evomap-portable-bundle-v0.1`), same 3 tools, same
16-item hard boundary — but a **different failure domain (Telegram message
router)** and the same `repair` intent category as Phase 6A.

The bundle captures the failure shape seen when a Hermes gateway is healthy
but the Telegram delivery path has no terminal success result. Symptoms
captured by the fixture:

- `gateway_alive: true` but `delivery_terminal_result: missing`
- `proxy_mismatch: true` (sendMessage and sendVoice inherit different proxy
  config)
- `sendMessage result: timeout` (no Telegram response)
- `sendVoice result: no delivery confirmation` (proxy present but no proof)
- `retry result: attempts consumed without terminal delivery event`
- `smoke result: not confirmed`

The bundle distills this into a Gene + Capsule that any local-only evolver
cycle can select, without ever reading `.env`, calling the Telegram API, or
printing credentials or recipient IDs.

## Bundle contents

```
phase6b-telegram-router-bundle/
├── README.md                                       (this file)
├── ATL_EVOMAP_6B_TELEGRAM_ROUTER_BUNDLE_REPORT.md  (full report, 398 lines)
├── fixtures/
│   └── telegram-router-failure-sample.txt          (1402 bytes, 0 secrets)
├── bundle/
│   ├── telegram-message-router-failure.bundle.json (8157 bytes)
│   └── fixture_summary.json                        (parser output snapshot)
├── artifacts/
│   ├── gene-telegram-message-router-failure.json       (2023 bytes)
│   ├── capsule-telegram-message-router-failure.json   (2169 bytes)
│   ├── telegram-router-fixture-output.json             (parser output, 12/12 signals)
│   ├── inspect-telegram-bundle-output.json             (ok=true)
│   ├── validate-telegram-bundle-output.json            (12/12 checks PASS)
│   ├── apply-telegram-bundle-dry-run-output.json       (planned, 0 writes)
│   ├── apply-telegram-bundle-yes-output.json           (6 files written, 0 errors)
│   ├── apply-telegram-target-summary.json              (gene=1 capsule=1 signals=5)
│   ├── evolver-run-telegram-target-output.txt          (Gene selected, no Hub)
│   └── evolver-review-telegram-target-output.txt       (no --approve, no solidify)
└── tools/                                          (Phase 5 3-tool copy)
    ├── evomap_inspect_bundle.py
    ├── evomap_validate_bundle.py
    └── evomap_apply_bundle.py
```

## Offline fixture model

The fixture is a deterministic text file that **describes** the failure shape
without **containing** any of the dangerous data (Telegram bot token, chat ID,
proxy URL with embedded creds, Authorization header, etc.). Hard rules in the
fixture's footer:

- Do not print credentials
- Do not print recipient identifiers
- Do not read .env
- Do not call Telegram API
- Do not run curl or wget
- Do not send real messages
- Do not modify real Hermes/OpenClaw configuration
- Only parse this text

`scripts/telegram_router_recovery_fixture.py` consumes the fixture and emits
a JSON summary. It also performs **safety scans** and refuses fixtures that
contain:

- `.env`-shape basenames (unless the basename contains `fixture`/`sample`)
- Telegram bot token shape (`\d{6,12}:[A-Za-z0-9_-]{20,}`)
- HTTP `Authorization:` header value
- API key tokens (`sk-...`, `sk_live_...`, `ghp_...`, etc.)
- Long pure-digit recipient-like IDs (12+ digits)

If any of these are detected, the parser returns `ok: false` with
`unsafe_fixture: ...` and the bundle becomes non-applyable.

## Parser usage

```bash
# Canonical invocation
python3 scripts/telegram_router_recovery_fixture.py \
  --input cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/fixtures/telegram-router-failure-sample.txt
```

Sample output (12/12 signals detected):

```json
{
  "ok": true,
  "component": "hermes-telegram-message-router",
  "gateway_alive": true,
  "message_router_loaded": true,
  "sendmessage_attempted": true,
  "sendvoice_attempted": true,
  "delivery_terminal_missing": true,
  "sendmessage_timeout": true,
  "sendvoice_delivery_unconfirmed": true,
  "proxy_mismatch": true,
  "sendmessage_proxy_missing": true,
  "sendvoice_proxy_present": true,
  "retry_consumed_without_terminal": true,
  "smoke_not_confirmed": true,
  "checks_passed": 12,
  "checks_total": 12,
  "all_signals_present": true,
  "recommended_check_order": [
    "confirm gateway health without printing credentials",
    "inspect router path selection for sendMessage and sendVoice",
    "verify proxy inheritance for both delivery paths",
    "check retry outcome for terminal success or failure event",
    "run one redacted dry-run smoke in fixture mode only",
    "record delivery evidence without printing credentials or recipient identifiers"
  ],
  "safety": {
    "no_real_telegram_call": true,
    "no_network_call": true,
    "no_curl_or_wget": true,
    "no_env_scan": true,
    "no_credentials": true,
    "no_recipient_identifier": true,
    "no_real_config_mutation": true
  }
}
```

## Gene summary

- **id:** `gene_distilled_telegram-message-router-failure`
- **category:** `repair`
- **signals_match:** 11 bare + 11 qualified (dual-form) = 22 entries, including
  `telegram_failure`, `message_router_failure`, `proxy_mismatch`,
  `delivery_terminal_missing`, `sendmessage_timeout`, `sendvoice_unconfirmed`,
  `retry_consumed`, `smoke_not_confirmed`, plus `session_context:hermes` and
  `repo_context:ai-tool-test-lab`
- **strategy:** 6 steps (gateway health → split paths → verify proxy →
  treat-no-terminal-as-failure → redacted-only smoke → evidence as
  states/categories, never as creds/IDs)
- **constraints:** `max_files=8`, `forbidden_paths` includes `.env`,
  `forbidden_actions` includes `print_credential`, `print_recipient_identifier`,
  `call_real_telegram_api`, `run_curl_or_wget`, `send_real_message`,
  `commit_env_file`, `mutate_real_router_config_without_user_instruction`

## Capsule summary

- **id:** `capsule_telegram_message_router_failure_phase6b`
- **schema_version:** `1.6.0`
- **status:** `success`, **confidence:** `0.84`, **visibility:** `private`
- **source:** `manual_capsule_seed_phase6b`
- **blast_radius:** `{files: 0, lines: 0}` (offline fixture doesn't touch real files)
- **execution_trace:** 4 steps
  1. **build** — `python3 scripts/telegram_router_recovery_fixture.py --input <fixture>` → `fixture_parsed_with_12_of_12_signals`
  2. **validate** — `python3 -m json.tool <fixture-output>` → `json_parse_pass`
  3. **validate** — `assert delivery_terminal_missing and proxy_mismatch and sendmessage_timeout` → `fixture_detected_expected_router_failure_shape`
  4. **canary** — `safety_check` → 10/10 safety booleans all true
     (`no_real_telegram_call`, `no_network_call`, `no_curl_or_wget`, `no_env_scan`,
     `no_credentials`, `no_recipient_identifier`, `no_hub`, `no_publish`,
     `no_approve`, `no_solidify`)

## Bundle usage (inspect / validate / apply)

The same 3 tools from Phase 5 work unchanged:

```bash
# 1. Inspect (read-only, returns JSON summary)
python3 scripts/evomap_inspect_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json

# 2. Validate (12 checks + secret scan)
python3 scripts/evomap_validate_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json

# 3. Apply dry-run (planned writes, 0 files written)
python3 scripts/evomap_apply_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json \
  --target-runtime /tmp/atl-evomap-phase6b-telegram-target \
  --dry-run

# 4. Apply --yes (real write to isolated target)
python3 scripts/evomap_apply_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json \
  --target-runtime /tmp/atl-evomap-phase6b-telegram-target \
  --yes

# 5. Optional: evolver run + review smoke (NOT --approve, NOT solidify)
cd /tmp/atl-evomap-phase6b-telegram-target
unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private
evolver run
evolver review
```

## Safety boundaries (preserved by tool design)

1. **No Hub:** `A2A_HUB_URL` unset; `Hub Matched Solution: (no hub match)`
2. **No publish:** `EVOLVER_AUTO_PUBLISH=false`
3. **No validator:** `EVOLVER_VALIDATOR_ENABLED=false`
4. **No `--loop`:** not used
5. **No credits:** 0 consumed
6. **No ATP autobuy:** `EVOLVER_ATP_AUTOBUY=off`
7. **No Telegram credentials:** parser refuses token-shape strings; bundle's
   `safety.no_credentials=true` is asserted in the canary step
8. **No recipient IDs:** parser refuses 12+ digit pure-digit strings; bundle's
   `safety.no_recipient_identifier=true` is asserted in the canary step
9. **No .env read:** parser refuses `.env`-shape basenames; `safety.no_env_scan=true`
10. **No real Telegram API call:** parser does no HTTP, no socket; bundle's
    `safety.no_real_telegram_call=true` is asserted
11. **No curl / wget:** parser never imports `urllib`, `requests`, `httpx`,
    `aiohttp`; `safety.no_curl_or_wget=true`
12. **No real OpenClaw/Hermes/systemd/cron config mutation:** bundle's
    `safety.no_real_config_mutation=true`; evolver run is in `/tmp` isolated target
13. **No Evolver source modification:** `skills/evolver/` not touched
14. **No `evolver review --approve`:** smoke only runs `evolver review` (no flag)
15. **No `evolver solidify`:** smoke does not run `node index.js solidify`
16. **No runtime `.evolver/` or `memory/` originals committed:** git only sees
    `phase6b-telegram-router-bundle/{bundle,fixtures,artifacts,tools}/` +
    `scripts/telegram_router_recovery_fixture.py` + `scripts/validate_*.py` +
    `README.md` + `data/cases.json` + `reports/...`

## Typical 5-step flow

```
1. parse fixture          python3 scripts/telegram_router_recovery_fixture.py --input <fixture>
2. inspect bundle         python3 scripts/evomap_inspect_bundle.py --bundle <bundle.json>
3. validate bundle        python3 scripts/evomap_validate_bundle.py --bundle <bundle.json>
4. apply dry-run          python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <isolated> --dry-run
5. apply --yes            python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <isolated> --yes
6. (optional) smoke       cd <isolated> && unset A2A_HUB_URL && evolver run && evolver review
```

## What this bundle does NOT do

- ❌ Does **not** call the Telegram API
- ❌ Does **not** send any real message (text or voice)
- ❌ Does **not** read `.env`
- ❌ Does **not** print credentials or recipient identifiers
- ❌ Does **not** use `curl` or `wget`
- ❌ Does **not** modify any real OpenClaw / Hermes / systemd / cron config
- ❌ Does **not** connect to the EvoMap Hub
- ❌ Does **not** publish any asset
- ❌ Does **not** consume credits
- ❌ Does **not** run `evolver review --approve`
- ❌ Does **not** run `evolver solidify`

## Verified target state (`/tmp/atl-evomap-phase6b-telegram-target`)

After `apply --yes` + optional `evolver run+review` smoke:

```
gene_count: 1  (gene_distilled_telegram-message-router-failure)
capsule_count: 1  (capsule_telegram_message_router_failure_phase6b)
memory_graph_lines: 8  (5 from apply + 3 from evolver run cycle)
selection_path: distilled_fallback (clean env, no failed events)
hub_match: false
publish: false
approve: false
solidify: false
```

## Known limitations (Phase 6B scope)

1. **Apply tool injects 5 generic bare signals** (`tool_bypass`,
   `repeated_tool_usage`, `protocol_drift`, `session_context`,
   `repo_context`) — NOT Telegram-specific signals like
   `telegram_failure / proxy_mismatch / delivery_terminal_missing`. These 5
   are sufficient for `evolver run` to select the Gene (selection path =
   `distilled_fallback` in this clean target), but a future phase should
   extend `evomap_apply_bundle.py` with `--inject-signals-from <bundle>` to
   write domain-specific signals.
2. **Bundle requires git init in target runtime** (Evolver refuses non-git
   directories). Workaround: `cd /tmp/atl-evomap-phase6b-telegram-target && git init` before `evolver run`.
3. **Smoke step is best-effort** — the `evolver run` cycle may attempt to
   emit Mutation/PersonalityState/EvolutionEvent/Gene/Capsule objects as
   raw JSON. We do **not** approve or solidify them.

## Lessons (durable)

1. **Two-path proxy mismatch is the most common Telegram delivery failure.**
   When `sendMessage` and `sendVoice` share a router but different proxy
   config, the gateway health is fine but the **terminal delivery event is
   missing**. The bundle's `delivery_terminal_missing=true` +
   `proxy_mismatch=true` is the canonical signal pair.
2. **Treating "retry consumed without terminal" as a router failure (not
   success)** is the key discipline. A retry that consumed all attempts but
   did not produce a terminal delivery event is **not** a successful
   delivery — it's a router that gave up.
3. **Redaction must be schema-enforced, not just textually avoided.** The
   parser's refusal of `.env`-shape basenames + Telegram token-shape + long
   pure-digit IDs makes the bundle re-pasteable into new fixtures without
   reviewer worry.
4. **Same kit, new domain.** Phase 6A proved the kit for `repair` (Hermes
   systemd). Phase 6B proves the kit for `repair` (Telegram router). The
   3-tool, 1-schema, 16-boundary pattern is domain-agnostic.

## Cross-cutting takeaway

The OpenClaw / Hermes Local Evolution Kit now supports:
- **2 intent categories** (optimize, repair)
- **3 problem domains** (tool discipline, systemd recovery, Telegram routing)
- **7 validated phases** (3C-V2, 4A, 4B, 4C, 5, 6A, 6B)

Future bundles (Codex, browser-control, /etc.) can use the same kit without
modification. The next natural extensions are:
- `--inject-signals-from <bundle>` in `evomap_apply_bundle.py`
- A `bundle-curator` skill that auto-generates portable bundles from
  `evolver run` outputs
- A Codex `optimize` bundle (prompt-cache discipline)
- A browser-control `repair` bundle (Playwright rate-limit recovery)
