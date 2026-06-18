# ATL-EVOMAP-6B · Telegram Message Router Failure Bundle — Report

> Status: **telegram router bundle completed (PASS)**  
> Phase: **ATL-EVOMAP-6B**  
> Author: conanxin / OpenClaw  
> Date: 2026-06-19 04:30+ Asia/Shanghai  
> Base: `00caf1d` (Phase 6A)  
> Bundle: `telegram-message-router-failure.bundle.json` (8157 B)  
> Gene: `gene_distilled_telegram-message-router-failure` (repair)  
> Capsule: `capsule_telegram_message_router_failure_phase6b` (4-step trace)  
> Validator: `scripts/validate_evomap_phase6b_telegram_router_bundle.py` — ALL CHECKS PASSED  
> All 7 validators (3C-V2, 4A, 4B, 4C, 5, 6A, 6B) PASS

---

## 1. 目标 (Goal)

Create the **third canonical local-only bundle** for the OpenClaw / Hermes
Local Evolution Kit. Capture the Telegram message router failure shape seen
when:

- the gateway is healthy,
- `sendMessage` times out (proxy missing on that path),
- `sendVoice` has proxy but no delivery confirmation,
- retries are consumed without a terminal delivery event,
- smoke is not confirmed.

The bundle must be:

- **Offline** — never call the Telegram API, never read `.env`, never print credentials / chat IDs.
- **Local-only** — no Hub, no publish, no credits, no `--approve`, no `solidify`.
- **Reusable** — same 3-tool kit as Phase 5/6A, same `atl-evomap-portable-bundle-v0.1` schema, same 16-item hard boundary.
- **Domain-agnostic kit** — proves the kit works for a 2nd `repair`-category bundle and a 3rd problem domain.

---

## 2. Phase 6A 解锁条件 (Phase 6A Unlock Conditions)

Phase 6A (`00caf1d`) delivered:

- `gene_distilled_hermes-systemd-service-recovery` (repair category)
- `capsule_hermes_systemd_service_recovery_phase6a` (4-step execution_trace)
- `hermes-systemd-service-recovery.bundle.json` (8587 B)
- Offline parser `scripts/hermes_systemd_recovery_fixture.py` (stdlib only)
- Validator `scripts/validate_evomap_phase6a_hermes_systemd_bundle.py` (19 checks)
- 6/6 validators (3C-V2, 4A, 4B, 4C, 5, 6A) PASS

This proved the kit's 3 tools work for a 2nd bundle in a new domain
(systemd). Phase 6B extends this to a 3rd bundle in a 3rd domain (Telegram
router), **without** changing the kit.

---

## 3. Telegram router failure model

### 3.1 The failure shape (canonical, deterministic)

```
COMPONENT: hermes-telegram-message-router
SCOPE: local notification delivery path
EXPECTED: gateway reports healthy and message router confirms Telegram delivery
ACTUAL: gateway healthy, but Telegram delivery has no terminal success result

router status
gateway_alive: true
message_router_loaded: true
sendMessage_path: attempted
sendVoice_path: attempted
delivery_terminal_result: missing

proxy configuration observation
expected_proxy: SOCKS5 proxy should be inherited by both sendMessage and sendVoice paths
actual_sendMessage_proxy: missing
actual_sendVoice_proxy: present
proxy_mismatch: true

failure symptoms
sendMessage result: timeout before Telegram response
sendVoice result: proxy path configured but no delivery confirmation
retry result: attempts consumed without terminal delivery event
smoke result: not confirmed
```

### 3.2 The 12 detectable signals (parser-emitted)

1. `gateway_alive`
2. `message_router_loaded`
3. `sendmessage_attempted`
4. `sendvoice_attempted`
5. `delivery_terminal_missing`
6. `sendmessage_timeout`
7. `sendvoice_delivery_unconfirmed`
8. `proxy_mismatch`
9. `sendmessage_proxy_missing`
10. `sendvoice_proxy_present`
11. `retry_consumed_without_terminal`
12. `smoke_not_confirmed`

The parser emits all 12 booleans at the top level (canonical schema for
the bundle) and inside `detected_signals` (for inspector convenience). A
fixture that misses any of them produces `all_signals_present=false` and
the apply tool refuses to write the bundle to a target.

### 3.3 The 6-step recommended check order

```python
[
    "confirm gateway health without printing credentials",
    "inspect router path selection for sendMessage and sendVoice",
    "verify proxy inheritance for both delivery paths",
    "check retry outcome for terminal success or failure event",
    "run one redacted dry-run smoke in fixture mode only",
    "record delivery evidence without printing credentials or recipient identifiers",
]
```

### 3.4 Safety conditions the parser enforces

- `no_real_telegram_call`
- `no_network_call`
- `no_curl_or_wget`
- `no_env_scan`
- `no_credentials`
- `no_recipient_identifier`
- `no_real_config_mutation`

These are the 7 booleans in `parser_output.safety`. They are also asserted
in the Capsule's canary step.

---

## 4. Offline fixture + parser

### 4.1 Fixture file

Path: `cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/fixtures/telegram-router-failure-sample.txt`  
Size: 1402 bytes  
Format: plain text, deterministic, no real credentials

The fixture ends with hard rules forbidding the parser/recovery script from:

- printing credentials
- printing recipient identifiers
- reading `.env`
- calling the Telegram API
- running `curl` or `wget`
- sending real messages
- modifying real Hermes/OpenClaw configuration

### 4.2 Parser

Path: `scripts/telegram_router_recovery_fixture.py`  
Size: ~9200 bytes (after 1 edit for `.env` basename fix)  
Dependencies: Python stdlib only (`argparse`, `json`, `re`, `sys`, `pathlib`)

#### Self-test results

| Test | Result |
|---|---|
| Real fixture: 12/12 signals detected | PASS |
| `ok: true`, `all_signals_present: true`, `checks_passed: 12` | PASS |
| `.env` basename → `ok: false`, `error: refused_input_path`, exit 2 | PASS |
| `env.local` basename → `ok: false`, `error: refused_input_path`, exit 2 | PASS |
| Credential-like (`1234567890:AAE...`) → `ok: false`, `error: unsafe_fixture` | PASS |
| Long-digit recipient-like (12+ digit pure-digit) → `ok: false`, `error: unsafe_fixture` | PASS |
| `.env-fixture.txt` (hint in name) → accepted, content-scanned | PASS |
| Stdlib only (no `requests`, `urllib`, `httpx`, `aiohttp`, `yaml`) | PASS |

The `.env` basename check has a fixture-hint escape hatch (basename
containing `fixture` / `sample`) so that test fixtures like
`.env-fixture.txt` can still be scanned for content.

---

## 5. Gene 设计

### 5.1 Signal matrix (dual-form, 22 entries)

Bare form (10): `telegram_failure`, `message_router_failure`, `proxy_mismatch`, `proxy_missing`, `delivery_terminal_missing`, `sendmessage_timeout`, `sendvoice_unconfirmed`, `retry_consumed`, `smoke_not_confirmed`, plus `session_context`, `repo_context`.

Qualified form (11): each bare signal qualified with a colon
context (e.g. `telegram_failure:delivery-timeout`,
`proxy_mismatch:sendmessage-sendvoice`,
`session_context:hermes`, `repo_context:ai-tool-test-lab`).

Total: **22 signals** (Phase 6A used 12; Phase 6B uses 22 to cover more
of the failure shape).

### 5.2 Strategy (6 steps)

1. Confirm gateway health and router load state without printing credentials.
2. Separate `sendMessage` and `sendVoice` delivery paths before changing shared proxy code.
3. Verify that both delivery paths inherit the same proxy configuration.
4. Treat consumed retry without terminal delivery event as a router failure, not as success.
5. Run only redacted fixture-mode smoke checks unless the user explicitly authorizes a real message.
6. Record evidence as delivery states and error categories, never as credentials or recipient identifiers.

### 5.3 Constraints

- `max_files: 8` (offline fixture doesn't touch real files; cap is the
  evolver's per-cycle blast radius)
- `forbidden_paths: [.git, node_modules, .evolver, memory, .env, real_runtime_root]`
- `forbidden_actions: [print_credential, print_recipient_identifier, call_real_telegram_api, run_curl_or_wget, send_real_message, commit_env_file, mutate_real_router_config_without_user_instruction]`

### 5.4 Summary

> Hermes Telegram message router recovery discipline for proxy mismatch, sendMessage timeout, sendVoice delivery uncertainty, and missing terminal delivery state.

---

## 6. Capsule 设计

### 6.1 Capsule metadata

- `id: capsule_telegram_message_router_failure_phase6b`
- `gene: gene_distilled_telegram-message-router-failure`
- `status: success`
- `confidence: 0.84`
- `visibility: private`
- `source: manual_capsule_seed_phase6b`
- `created_at: 2026-06-19T04:35:00Z`
- `blast_radius: {files: 0, lines: 0}` (offline fixture, no real files touched)

### 6.2 Trigger (6 signals)

`["telegram_failure", "message_router_failure", "proxy_mismatch", "delivery_terminal_missing", "sendmessage_timeout", "smoke_not_confirmed"]`

### 6.3 Execution trace (4 steps, build + 2 validate + canary)

| # | stage | command | exit | result |
|---|---|---|---|---|
| 1 | build | `python3 scripts/telegram_router_recovery_fixture.py --input <fixture>` | 0 | `fixture_parsed_with_12_of_12_signals` |
| 2 | validate | `python3 -m json.tool <fixture-output>` | 0 | `json_parse_pass` |
| 3 | validate | `assert delivery_terminal_missing and proxy_mismatch and sendmessage_timeout` | 0 | `fixture_detected_expected_router_failure_shape` |
| 4 | canary | `safety_check` | 0 | 10/10 booleans all true |

The canary 10 booleans:

```
no_real_telegram_call, no_network_call, no_curl_or_wget, no_env_scan,
no_credentials, no_recipient_identifier, no_hub, no_publish,
no_approve, no_solidify
```

---

## 7. Bundle schema

```json
{
  "schema_version": "atl-evomap-portable-bundle-v0.1",
  "source_phase": "ATL-EVOMAP-6B",
  "source_session": "/tmp/atl-evomap-phase6b-telegram-target",
  "target_gene_id": "gene_distilled_telegram-message-router-failure",
  "target_capsule_id": "capsule_telegram_message_router_failure_phase6b",
  "gene": <full Gene JSON>,
  "capsule": <full Capsule JSON>,
  "execution_trace": <capsule.execution_trace>,
  "fixture_summary": {
    "input_fixture": "...",
    "parser_cmd": "...",
    "parser_module": "scripts/telegram_router_recovery_fixture.py",
    "expected_component": "hermes-telegram-message-router",
    "expected_gateway_alive": true,
    "expected_delivery_terminal_missing": true,
    "expected_proxy_mismatch": true,
    "expected_sendmessage_timeout": true,
    "expected_sendvoice_unconfirmed": true,
    "expected_smoke_not_confirmed": true,
    "no_real_telegram_call": true,
    "no_network_call": true,
    "no_env_scan": true,
    "no_credentials": true,
    "no_recipient_identifier": true,
    "checks_passed": 12,
    "checks_total": 12,
    "all_signals_present": true
  },
  "safety": {
    "hub": "disabled",
    "publish": "disabled",
    "credits": 0,
    "visibility": "private",
    "no_failed_events": true,
    "no_pollution_signals": true,
    "no_real_telegram_call": true,
    "no_real_config_mutation": true,
    "no_credentials": true,
    "no_recipient_identifier": true
  },
  "import_contract": {
    "required_files": [
      ".evolver/gep/genes.json",
      ".evolver/gep/capsules.json",
      "memory/evolution/memory_graph.jsonl"
    ],
    "optional_files": [
      ".evolver/gep/events.jsonl",
      ".evolver/gep/failed_capsules.json",
      ".evolver/gep/candidates.jsonl"
    ],
    "required_in_genes": ["genes[].id"],
    "required_in_capsules": ["capsules[].id", "capsules[].gene", "capsules[].execution_trace"],
    "minimum_execution_trace_steps": 1,
    "minimum_execution_trace_stages": ["build", "validate", "canary"]
  },
  "kit_provenance": {
    "phase_5_commit": "c1a6b9a",
    "phase_6a_commit": "00caf1d",
    "phase_6b_phase": "ATL-EVOMAP-6B"
  }
}
```

Size: 8157 bytes (Phase 5 was 5458; Phase 6A was 8587; Phase 6B is 8157).
Larger than Phase 5 because of the dual-form 22-signal Gene. Smaller than
Phase 6A because the 4-step execution_trace is more compact than the
schema layout in Phase 6A's capsule.

---

## 8. inspect / validate 结果

### 8.1 inspect

```
ok: true
schema_version: atl-evomap-portable-bundle-v0.1
source_phase: ATL-EVOMAP-6B
gene_id: gene_distilled_telegram-message-router-failure
gene_category: repair
capsule_id: capsule_telegram_message_router_failure_phase6b
capsule_status: success
capsule_confidence: 0.84
capsule_visibility: private
execution_trace_steps: 4
execution_trace_stages: [build, validate, validate, canary]
```

### 8.2 validate

12/12 checks PASS:

| # | check | ok |
|---|---|---|
| 1 | bundle file exists | ✓ |
| 2 | bundle is valid JSON | ✓ |
| 3 | bundle has schema_version | ✓ |
| 4 | bundle has 'gene' field | ✓ |
| 5 | bundle has 'capsule' field | ✓ |
| 6 | bundle has 'execution_trace' field | ✓ |
| 7 | gene.id present and non-empty | ✓ |
| 8 | capsule.id present and non-empty | ✓ |
| 9 | capsule.gene == gene.id | ✓ |
| 10 | capsule.execution_trace is non-empty list | ✓ |
| 11 | import_contract.required_files contains 3 required paths | ✓ |
| 12 | no secret patterns in bundle | ✓ |

`failures: []`, `summary.secret_hits: 0`.

---

## 9. apply dry-run / apply --yes 结果

### 9.1 dry-run

```
ok: true
mode: dry-run
plan.summary: {
  existing_gene_count: 0,
  existing_capsule_count: 0,
  new_gene_count: 1,
  new_capsule_count: 1,
  memory_graph_signals_added: 5
}
writes: 6 planned (2 overwrite + 1 append + 3 reset)
```

Filesystem untouched.

### 9.2 --yes

```
ok: true
mode: applied
plan_summary: same as dry-run
log.writes_executed: 6
log.errors: []
```

Target after apply:

```
gene_count: 1 (gene_distilled_telegram-message-router-failure)
capsule_count: 1 (capsule_telegram_message_router_failure_phase6b)
memory_graph_lines: 5 (tool_bypass, repeated_tool_usage, protocol_drift, session_context, repo_context)
```

### 9.3 Memory graph signals (apply-emitted, 5 generic)

The Phase 5 apply tool emits 5 generic bare signals by design:
`tool_bypass`, `repeated_tool_usage`, `protocol_drift`, `session_context`,
`repo_context`. These are **not** Telegram-specific (e.g. no
`telegram_failure`, no `proxy_mismatch`). This is the same limitation
Phase 6A documented — the Gene is selected in the evolver cycle via
`selection_path: distilled_fallback` (clean env, no failed events),
which does not strictly need domain-specific signals.

A future phase should extend `evomap_apply_bundle.py` with
`--inject-signals-from <bundle>` to write domain-specific signals. This
is a Phase 7+ extension.

---

## 10. optional run/review smoke 结果

In `/tmp/atl-evomap-phase6b-telegram-target` (git init commit `b6985af`),
with `A2A_HUB_URL` unset and the standard 4 evolver safety env vars set:

### 10.1 evolver run

```
[ATP-AutoDeliver] Started (pollMs=60000)
Scanning session logs...
[Signals] Multi-strategy: regex=1, score=1, llm=0, merged=2 | score-only: tool_bypass
[QuestionGenerator] Generated 1 proactive question(s).
[SearchFirst] No hub match (reason: no_hub_url). Proceeding with local evolution.
[OpenPR] gh pr list failed (non-fatal): Command failed: gh pr list --state=open --json number,title,headRefName,files --limit 50
no git remotes found

GEP — GENOME EVOLUTION PROTOCOL (v1.10.3 STRICT) Cycle #0001

Selection: Selected Gene "gene_distilled_telegram-message-router-failure"
selection_path: distilled_fallback
signals: tool_bypass

ACTIVE STRATEGY (gene_distilled_telegram-message-router-failure):
  1. Start by confirming gateway health and router load state without printing credentials.
  2. Separate sendMessage and sendVoice delivery paths before changing shared proxy code.
  3. Verify that both delivery paths inherit the same proxy configuration.
  4. Treat consumed retry without terminal delivery event as a router failure, not as success.
  5. Run only redacted fixture-mode smoke checks unless the user explicitly authorizes a real message.
  6. Record evidence as delivery states and error categories, never as credentials or recipient identifiers.

Hub Matched Solution: (no hub match)
```

✅ Gene selected
✅ No hub
✅ No crash

### 10.2 evolver review

```
[Review] Pending evolution run: run_1781814867297

--- Gene ---
  ID:       gene_distilled_telegram-message-router-failure
  Category: repair
  Summary:  Hermes Telegram message router recovery discipline for proxy mismatch, sendMessage timeout, sendVoice delivery uncertainty, and missing terminal delivery state.

--- Mutation ---
  Category:   innovate
  Risk Level: medium

--- Diff ---
  (no changes detected)

To approve and solidify:  node index.js review --approve
To reject and rollback:   node index.js review --reject
```

✅ Capsule visible
✅ No `--approve` (we did not run it)
✅ No `solidify` (we did not run it)

### 10.3 post-smoke target state

```
gene_count: 1
capsule_count: 1
memory_graph_lines: 8 (5 from apply + 3 from evolver run cycle)
```

The evolver run added 3 more memory graph events (one per cycle).

---

## 11. 安全边界 (Hard Boundaries — 16 preserved)

1. ✅ No Hub (`A2A_HUB_URL` unset, `[SearchFirst] No hub match`)
2. ✅ No `A2A_HUB_URL` env var
3. ✅ No `--loop` (smoke is one-shot)
4. ✅ No validator (`EVOLVER_VALIDATOR_ENABLED=false`)
5. ✅ No auto-publish (`EVOLVER_AUTO_PUBLISH=false`)
6. ✅ No credits consumed (0)
7. ✅ No ATP autobuy (`EVOLVER_ATP_AUTOBUY=off`)
8. ✅ No Telegram credentials (parser refuses token-shape, bundle's
   `safety.no_credentials=true` and canary asserts it)
9. ✅ No recipient IDs (parser refuses 12+ digit pure-digit, bundle's
   `safety.no_recipient_identifier=true` and canary asserts it)
10. ✅ No `.env` read (parser refuses `.env`-shape basename, bundle's
    `safety.no_env_scan=true`)
11. ✅ No curl / wget (parser never imports `urllib`/`requests`/`httpx`/`aiohttp`)
12. ✅ No real Telegram API call (bundle's `safety.no_real_telegram_call=true`)
13. ✅ No real OpenClaw/Hermes/systemd/cron config mutation (smoke is in
    isolated `/tmp` target, bundle's `safety.no_real_config_mutation=true`)
14. ✅ No Evolver package source modification
15. ✅ No `evolver review --approve` (smoke is read-only)
16. ✅ No `evolver solidify` (smoke does not run `node index.js solidify`)
17. ✅ No runtime `.evolver/` or `memory/` originals committed (git only
    sees `phase6b-telegram-router-bundle/...` + `scripts/...` + `README.md` +
    `data/cases.json` + `reports/...`)

---

## 12. 最终结论 (Final Conclusion)

**Status: PASS**

Phase 6B adds the **third canonical local-only bundle** for the OpenClaw /
Hermes Local Evolution Kit. The bundle is:

- Offline (parser does not call Telegram API, does not read .env, does not
  print credentials or chat IDs)
- Reusable (same kit, same 3 tools, same schema as Phase 5/6A)
- Validated (7/7 validators PASS, 12/12 bundle checks, 19/19 Phase 6B
  validator checks, 12/12 parser signals, 10/10 capsule canary booleans)
- Reusable across sessions (target `/tmp/atl-evomap-phase6b-telegram-target`
  shows 1 gene + 1 capsule + 8 memory graph lines after the smoke cycle)

The kit now supports **2 intent categories** (optimize, repair) and
**3 problem domains** (tool discipline, systemd recovery, Telegram routing).

---

## 13. 下一步建议 (Next Steps)

1. **`evomap_apply_bundle.py` extension: `--inject-signals-from <bundle>`** —
   Inject domain-specific signals (e.g. `telegram_failure`,
   `proxy_mismatch`, `delivery_terminal_missing`) from the bundle's
   `signals_match` into `memory_graph.jsonl`. Closes the "5 generic
   signals" gap noted in Phase 5/6A/6B.
2. **Codex `optimize` bundle** — prompt-cache discipline, follows the
   same pattern.
3. **Browser-control `repair` bundle** — Playwright rate-limit recovery,
   uses the same kit.
4. **`bundle-curator` skill** — auto-generate a portable bundle from
   `evolver run` outputs (gene.json, capsule.json, execution_trace.json,
   fixture.txt).
5. **Cross-bundle regression test** — apply all 3 bundles to a single
   fresh isolated target, verify no signal / gene / capsule collisions.

---

*Bundle complete. 7/7 validators green. Kit proven for 2 categories + 3 domains. Ready for Phase 7+ extensions.*
