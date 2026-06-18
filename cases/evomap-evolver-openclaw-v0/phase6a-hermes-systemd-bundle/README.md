# ATL-EVOMAP-6A · Hermes Systemd Service Recovery Bundle

> Second canonical local-only bundle for the **OpenClaw Local Evolution Kit**
> (Phase 5). Repository: `gene_distilled_hermes-systemd-service-recovery` +
> `capsule_hermes_systemd_service_recovery_phase6a`. Targets **Hermes / OpenClaw
> systemd user-service failure recovery** in a strictly offline, local-only
> pipeline that does not touch real OpenClaw / Hermes / systemd / cron
> configuration.

---

## What this bundle is

A portable EvoMap bundle (`schema_version: atl-evomap-portable-bundle-v0.1`)
that captures a proven offline recipe for recovering a Hermes systemd
user-service when:

- `hermes-gateway.service` is in `Active: failed` / `start-limit-hit`
- `journalctl` shows `code=exited, status=N/INVALIDARGUMENT`
- `systemctl --user show-environment` shows a missing `MODEL_PROVIDER` (or
  similar runtime env)
- The service drop-in `~/.config/systemd/user/hermes-gateway.service.d/env.conf`
  references a `.env` path that no longer exists
- Port `127.0.0.1:18789` is not in `LISTEN`
- The Telegram smoke test was not sent

The bundle's strategy is **offline-first**: an offline parser
(`scripts/hermes_systemd_recovery_fixture.py`) consumes a deterministic
text fixture and emits a JSON summary that names the failure shape. Recovery
**is then executed by a human** on the real host, never by a recipe script.

This is **category = `repair`**, complementing Phase 5's
**`optimize`**-category `openclaw-tool-use-discipline` bundle. Together they
demonstrate that the kit supports multiple intent categories.

---

## What problem it solves

Hermes gateway recovery has a recurring shape:

1. Post-OOM / post-OpenClaw restart, `hermes-gateway.service` fails to come back
2. `journalctl` shows env-loading failures
3. Operators run a fragile ad-hoc check sequence (status → log → env → drop-in → port)
4. The fix is often mechanical, but the *evidence trail* is lost

This bundle pins the **check order** as deterministic text in a recipe
(`recommended_check_order` in the parser output) and pins the **expected
fixture shape** so future failures can be diffed.

It does NOT:

- Touch the real service
- Read `.env`
- Persist any secret, token, cookie, or Authorization header
- Connect to EvoMap Hub
- Auto-publish
- Run `evolver review --approve` or `evolver solidify`

---

## Bundle schema

Same `atl-evomap-portable-bundle-v0.1` schema as Phase 5, with one extra
field:

```json
{
  "schema_version": "atl-evomap-portable-bundle-v0.1",
  "source_phase": "ATL-EVOMAP-6A",
  "source_session": "/tmp/atl-evomap-phase6a-hermes-target",
  "target_capsule_id": "capsule_hermes_systemd_service_recovery_phase6a",
  "target_gene_id": "gene_distilled_hermes-systemd-service-recovery",
  "gene": { ... repair-category Gene ... },
  "capsule": { ... Capsule with 4-step execution_trace ... },
  "execution_trace": [ ... 4 steps ... ],
  "fixture_summary": {
    "input_fixture": "fixtures/hermes-systemd-failure-sample.txt",
    "parser_cmd": "python3 scripts/hermes_systemd_recovery_fixture.py --input <fixture>",
    "expected_missing_env_var": "MODEL_PROVIDER",
    "expected_service": "hermes-gateway.service",
    "expected_port": "127.0.0.1:18789",
    "no_real_systemctl": true,
    "no_real_journalctl": true,
    "no_env_scan": true,
    "no_secrets": true
  },
  "safety": { "hub": "disabled", "publish": "disabled", "credits": 0, ... },
  "import_contract": { ... },
  "kit_provenance": { "phase_5_commit": "c1a6b9a", "phase_6a_phase": "ATL-EVOMAP-6A", ... }
}
```

`fixture_summary` is the only Phase 6A addition; it captures what the
parser **must** detect for the bundle to be considered valid.

---

## Files in this directory

```
phase6a-hermes-systemd-bundle/
├── README.md                                            (this file)
├── ATL_EVOMAP_6A_HERMES_SYSTEMD_BUNDLE_REPORT.md        (case-local full report)
├── fixtures/
│   └── hermes-systemd-failure-sample.txt                (1803 B offline text fixture)
├── bundle/
│   └── hermes-systemd-service-recovery.bundle.json      (8587 B portable bundle)
├── artifacts/
│   ├── gene-hermes-systemd-service-recovery.json        (canonical Gene)
│   ├── capsule-hermes-systemd-service-recovery.json     (canonical Capsule)
│   ├── hermes-systemd-fixture-output.json               (parser output)
│   ├── inspect-bundle-output.json                       (inspect tool output)
│   ├── validate-bundle-output.json                      (validate tool output)
│   ├── apply-bundle-dry-run-output.json                 (apply --dry-run output)
│   ├── apply-bundle-yes-output.json                     (apply --yes output)
│   ├── apply-target-summary.json                        (on-disk verify)
│   ├── apply-target-files-manifest.json                 (file manifest)
│   ├── evolver-run-hermes-target-output.txt             (run smoke output)
│   └── evolver-review-hermes-target-output.txt          (review smoke output)
└── tools/
    ├── evomap_inspect_bundle.py                         (kit tool copy)
    ├── evomap_validate_bundle.py                        (kit tool copy)
    └── evomap_apply_bundle.py                           (kit tool copy)
```

---

## inspect / validate / apply usage

The three Phase 5 stdlib tools work on this bundle unchanged:

```bash
# 1. Inspect — read-only summary
python3 scripts/evomap_inspect_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json

# 2. Validate — 12 checks + secret scan
python3 scripts/evomap_validate_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json

# 3. Apply dry-run — print plan, write nothing
python3 scripts/evomap_apply_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json \
    --target-runtime /tmp/atl-evomap-phase6a-hermes-target \
    --dry-run

# 4. Apply --yes — actually write (requires the target to exist)
python3 scripts/evomap_apply_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json \
    --target-runtime /tmp/atl-evomap-phase6a-hermes-target \
    --yes
```

`apply` writes **6 files** to the target runtime's `.evolver/gep/` +
`memory/evolution/` directories and appends **5 clean bare memory signals**
(generic Phase 5 signals — see "Known limitations" below).

---

## Typical 4-step recipe (with optional evolver smoke)

1. **Run the offline parser on the fixture:**
   ```bash
   python3 scripts/hermes_systemd_recovery_fixture.py \
       --input cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/fixtures/hermes-systemd-failure-sample.txt
   ```
   Confirm the JSON summary lists `service_failed=true`,
   `missing_env_var=MODEL_PROVIDER`, `expected_port=127.0.0.1:18789`,
   `port_not_listening=true`, `dropin_env_misconfigured=true`.

2. **Inspect + validate the bundle:**
   ```bash
   python3 scripts/evomap_inspect_bundle.py --bundle <bundle>
   python3 scripts/evomap_validate_bundle.py --bundle <bundle>
   ```
   Validate must return `ok=true`, `failures=[]`, `secret_hits=0`.

3. **Apply dry-run:**
   ```bash
   python3 scripts/evomap_apply_bundle.py \
       --bundle <bundle> --target-runtime /tmp/atl-evomap-phase6a-hermes-target --dry-run
   ```
   Confirm the plan summary: `new_gene_count=1`, `new_capsule_count=1`,
   `memory_graph_signals_added=5`.

4. **Apply --yes:**
   ```bash
   python3 scripts/evomap_apply_bundle.py \
       --bundle <bundle> --target-runtime /tmp/atl-evomap-phase6a-hermes-target --yes
   ```

5. **(Optional) evolver run/review smoke:**
   ```bash
   cd /tmp/atl-evomap-phase6a-hermes-target
   unset A2A_HUB_URL
   export EVOLVE_STRATEGY=repair-only
   export EVOLVER_AUTO_PUBLISH=false
   export EVOLVER_VALIDATOR_ENABLED=false
   export EVOLVER_ATP_AUTOBUY=off
   export EVOLVER_DEFAULT_VISIBILITY=private
   evolver run
   evolver review     # DO NOT --approve, DO NOT solidify
   ```
   Expected: `Selected Gene "gene_distilled_hermes-systemd-service-recovery"`,
   Capsule visible in review, no Hub contact, no crash, no diff.

6. **(Outside this repo, on the real host) Human runs the recovery:**
   ```bash
   systemctl --user status hermes-gateway.service
   journalctl --user -u hermes-gateway.service --since today
   systemctl --user show-environment
   # inspect ~/.config/systemd/user/hermes-gateway.service.d/env.conf
   ss -ltnp | grep 18789
   # Telegram smoke test
   ```

---

## Known limitations (Phase 6A scope)

- **Apply tool injects 5 generic bare signals** (`tool_bypass`,
  `repeated_tool_usage`, `protocol_drift`, `session_context`,
  `repo_context`), **NOT** Hermes-specific signals like
  `systemd_failure` / `service_recovery` / `missing_env_var`. These
  signals are sufficient to keep the bundle alive in the target runtime's
  memory graph, but a future phase should extend `evomap_apply_bundle.py`
  with an `--inject-signals-from <bundle>` flag to write Hermes-specific
  signals.
- **Bundle requires git init in target runtime.** Evolver refuses to run in
  non-git directories. The apply tool itself doesn't require git, but the
  optional smoke step does. Workaround documented in the 4-step recipe.
- **`dropin_env_misconfigured` is derived** (heuristic match on
  `drop-in.*missing` and `Environment=.*missing\s+/home`). Real-world drop-in
  formats vary; the parser keeps the unrecognized lines in
  `unrecognized_signals` for human review rather than failing.

---

## Hard boundaries (16)

All 16 boundaries preserved by **tool design**, not just by careful usage:

- **No Hub:** apply tool does NOT contact Hub; fixture parser does NOT
  import from evolver package; no `A2A_HUB_URL` is set in any bundle /
  capsule / execution_trace.
- **No publish:** apply tool does NOT call `evolver review --approve` or
  `evolver solidify`; no `EVOLVER_AUTO_PUBLISH=true`.
- **No credits:** `safety.credits=0` in bundle; no `EVOLVER_ATP_AUTOBUY`.
- **No validator:** `EVOLVER_VALIDATOR_ENABLED=false`; bundle safety
  block sets `validator_enabled=false`.
- **No `--loop`:** no `evolver --loop` invocation in any artifact or
  recipe step.
- **No approve:** `safety.approve="not_executed"`; recipe step explicitly
  says "DO NOT --approve".
- **No solidify:** `safety.solidify="not_executed"`; recipe step
  explicitly says "DO NOT solidify".
- **No real system mutation:** fixture parser does NOT execute
  systemctl / journalctl / ss / curl; only parses text. `fixture_summary.no_real_systemctl=true`,
  `no_real_journalctl=true`, `no_env_scan=true`, `no_secrets=true`.
- **No secret persistence:** validate tool's secret scan must return 0
  hits; fixture parser refuses any path matching `.env`; capsule
  `execution_trace` step 4 has `no_secrets=true` canary check.
- **No env scan:** fixture parser does NOT recursively walk the repo
  for `.env`; only consumes the single `--input` path.
- **No real OpenClaw / Hermes / systemd / cron config mutation:** apply
  tool writes ONLY to `<target>/.evolver/gep/` and
  `<target>/memory/evolution/`; never touches real config files.
- **No Evolver source modification:** no edits to
  `~/.local/lib/node_modules/@evomap/evolver/`.
- **No runtime `.evolver/` / `memory/` originals committed:** target
  runtime is `/tmp/...`, never committed; only the **bundle JSON** +
  **artifacts** + **case directory contents** are committed.
- **Only kit files / bundle artifact / tools / templates / reports /
  validators committed:** the commit whitelist in Phase 5 / 6A validator
  enforces this.
- **Stdlib only:** `scripts/hermes_systemd_recovery_fixture.py` uses only
  `argparse / json / re / sys / pathlib`.

---

## Bundle survival evidence

After `apply --yes` + `evolver run` + `evolver review` (no `--approve`,
no solidify) in `/tmp/atl-evomap-phase6a-hermes-target`:

```
genes:       ['gene_distilled_hermes-systemd-service-recovery']
capsules:    ['capsule_hermes_systemd_service_recovery_phase6a']
memory_graph lines: 8  (5 from apply + 3 from evolver run cycles)
```

The bundle **survives the evolver cycle** with the same Gene + Capsule
intact. Selection path confirmed via `evolver review` output:
`Selected Gene "gene_distilled_hermes-systemd-service-recovery"`.

---

## Relationship to Phase 5 (kit) and other planned bundles

| Phase | Bundle | Category | Intent |
|---|---|---|---|
| 5 | `openclaw-tool-use-discipline` | `optimize` | Tool discipline in OpenClaw sessions |
| **6A** | **`hermes-systemd-service-recovery`** | **`repair`** | **Hermes gateway user-service recovery** |
| 6B (planned) | `telegram-message-router` | `repair` | Telegram bot message routing failures |
| 6C (planned) | `codex-prompt-cache-discipline` | `optimize` | Codex prompt cache invalidation discipline |
| 6D (planned) | `browser-control-rate-limit` | `repair` | Playwright / OpenClaw browser-control rate-limit handling |

All bundles share the same `atl-evomap-portable-bundle-v0.1` schema, the
same apply tool, and the same 16 hard boundaries.