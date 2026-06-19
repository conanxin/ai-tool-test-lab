# ATL-EVOMAP-9B — Curator-to-Nightly Integration

> **Status (committed):** Curator-to-Nightly Integration smoke pass
> **Final status:** `CURATOR_NIGHTLY_INTEGRATION_SMOKE_PASS`
> **Base commit:** `7811e1b`
> **Schema:** `atl-evomap-nightly-validation-v0.1` (manifest extended; backward-compatible)

This phase extends the Phase 8A nightly validation runner with a **non-blocking
canary bundle lane** that ingests curator-generated draft bundles. Canonical
bundles (the 4 blocking ones shipped in 5/6A/6B/6C) keep their blocking
semantics; curator-generated bundles enter a separate lane that does NOT
influence `overall_status`.

---

## 1. What this phase does

1. **Extends the validation manifest** at
   `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/validation-loop-manifest.json`
   with a new top-level field `canary_bundles[]`. Each entry describes one
   curator-generated draft bundle, its source phase, expected status, and
   which checks to run against it (`inspect`, `validate`, `apply_dry_run`).
   The manifest `checks[]` list gains a new entry `canary_bundles_checked`
   (default `blocking: false`).

2. **Extends the nightly runner** at `scripts/evomap_nightly_validate.py`
   with a new `check_canary_bundles` step that:
   - reads `canary_bundles[]` from the manifest,
   - for each entry runs `inspect`, `validate`, and `apply --dry-run`
     (target = `/tmp/atl-evomap-nightly-canary-<id>`),
   - records per-bundle results under `canary_bundle_checks[]`,
   - records an aggregate summary under `canary_summary`,
   - emits a single non-blocking row `canary_bundles_checked`.

3. **Promotes the per-validator array** from
   `check_all_phase_validators_pass.extra.validators[]` to a top-level
   `digest["validators"]` array for easier consumption by downstream tooling
   (e.g. Phase 9B summary extractors).

4. **Adds a `bundle_checks` view** at top-level: `digest.bundle_checks.inspect`
   and `digest.bundle_checks.validate` lists of `{id, path, returncode, status}`.

5. **Updates the Markdown digest** with a dedicated
   `## Canary / Curator-generated bundles` section containing both summary
   bullets and a per-bundle table.

6. **Forwards-compatible fix to Phase 9A:** the
   `validate_evomap_phase9a_bundle_curator_skill.py` script previously listed
   `phase8a_nightly_validation_loop.py` in `PRIOR_VALIDATORS`. With Phase 9B
   adding the 9A curator-skill validator into the nightly runner's
   `all_phase_validators_pass` list, this would create
   runner → 9A → 8A → runner → 9A → ... infinite recursion. Phase 9B removes
   the 8A reference from `PRIOR_VALIDATORS` per the Step-1 forward-compatible
   rule (no artifact / secret / report check is lowered; 8A's own self-host
   test still runs in 8A's validator and via the 8A nightly chain).

---

## 2. Canonical bundle lane vs curator canary lane

| Lane | Examples | Default `blocking` | Failed check status | Affects `overall_status`? |
|------|----------|--------------------|----------------------|---------------------------|
| **Canonical (blocking)** | 4 bundles from Phases 5 / 6A / 6B / 6C | `true` | `FAIL` | YES |
| **Curator-generated canary (non-blocking)** | sample-safe-bundle from Phase 9A | `false` | `CANARY_FAIL` / `WARN` | NO |

- The 4 canonical bundles (`openclaw-tool-use-discipline`,
  `hermes-systemd-service-recovery`, `telegram-message-router-failure`,
  `codex-test-failure-loop`) are validated by the existing `bundles_inspectable`
  and `bundles_validatable` blocking checks. If any of those fails,
  `overall_status` becomes `FAIL`.
- The curator-generated canary bundle
  (`cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated/sample-safe-bundle.bundle.json`)
  is validated by the new `canary_bundles_checked` non-blocking check. If it
  fails, `canary_summary.status` becomes `CANARY_FAIL` and the row status
  becomes `WARN`, but `overall_status` stays driven solely by the 9 blocking
  checks.

---

## 3. Why canary lane is non-blocking

Curator-generated bundles are *drafts* — produced by the Phase 9A curator
skill. They are intentionally not part of the canonical kit. Waking up a
nightly pipeline to a failed curator run is informative, but it should never
flip the kit's overall health. The canary lane therefore:

- runs only `inspect` / `validate` / `apply --dry-run`,
- never invokes the evolver package, never calls `--yes`, never publishes,
- uses an isolated `/tmp` target directory that is created fresh on each run
  (so apply dry-run has a writable directory to plan against, but no real
  runtime is mutated),
- fails are surfaced as `CANARY_FAIL` in the digest and as `WARN` on the row,
  but `overall_status` is computed only over `blocking=true` checks.

---

## 4. How to add a new curator-generated canary bundle

1. The curator skill (Phase 9A) produces a bundle JSON in
   `cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated/`
   (or in any case-scoped location you choose).
2. Append a new entry to `canary_bundles[]` in the validation-loop-manifest:

   ```json
   {
     "id": "my-new-canary-bundle",
     "source_phase": "ATL-EVOMAP-9A",
     "path": "cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated/my-new-canary-bundle.bundle.json",
     "lane": "curator_generated",
     "blocking": false,
     "checks": ["inspect", "validate", "apply_dry_run"],
     "expected_status": "CANARY_PASS",
     "apply_dry_run_target_runtime": "/tmp/atl-evomap-nightly-canary-my-new-canary-bundle",
     "notes": "Optional human-readable note."
   }
   ```

3. Run the nightly smoke again. The new entry will be picked up automatically
   by `check_canary_bundles`. No runner code changes are required.

---

## 5. What the runner does per canary bundle

For each entry in `canary_bundles[]`, the runner executes:

```bash
# 1. inspect (read-only, stdlib-only)
python3 scripts/evomap_inspect_bundle.py --bundle <bundle-path>

# 2. validate (read-only, stdlib-only, secret scan)
python3 scripts/evomap_validate_bundle.py --bundle <bundle-path>

# 3. apply dry-run (planner only; no real mutation; target = /tmp/...)
python3 scripts/evomap_apply_bundle.py \
    --bundle <bundle-path> \
    --target-runtime /tmp/atl-evomap-nightly-canary-<id> \
    --dry-run
```

The runner ensures the `--target-runtime` directory exists (creates it with
`mkdir(parents=True, exist_ok=True)` under `/tmp`, isolated from any real
runtime). It then parses the apply JSON output: if `ok` is `false`, the dry-run
is recorded as FAIL even if the returncode is 0.

Each of the three checks produces a `PASS` / `FAIL` / `SKIP` record. The
bundle-level status is `CANARY_PASS` only if all three are `PASS`; otherwise
`CANARY_FAIL`.

---

## 6. What the digest contains

After a smoke run, `nightly-validation-digest.json` contains:

- `overall_status` — PASS / FAIL driven **only** by blocking checks.
- `summary.blocking_total` = 9 (unchanged from Phase 8A).
- `summary.passed` + `summary.failed` — blocking-only counts.
- `summary.non_blocking` = number of non-blocking rows (now 1: canary).
- `bundle_checks.inspect[]` / `bundle_checks.validate[]` — 4 canonical
  bundles each, with `id / path / returncode / status`.
- `canary_bundle_checks[]` — per-canary records with `inspect / validate /
  apply_dry_run` sub-statuses.
- `canary_summary` — `{total, passed, failed, blocking_failures,
  non_blocking_failures, status}`.
- `validators[]` — top-level array of per-validator results from the
  runner's `all_phase_validators_pass` step (7 entries including 9A).
- `hard_boundaries` — all `true` (no Hub / publish / credits / approve /
  solidify / real cron / systemd timer / network / env / evolve).

`nightly-validation-digest.md` additionally renders a
`## Canary / Curator-generated bundles` section with summary bullets and a
table of per-bundle statuses.

---

## 7. How to run manually

From the repo root:

```bash
# Dry-run (no digest files written; useful for quick smoke)
python3 scripts/evomap_nightly_validate.py \
    --repo-root . \
    --out-dir cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-smoke \
    --dry-run

# Full smoke (writes nightly-validation-digest.{json,md,log})
python3 scripts/evomap_nightly_validate.py \
    --repo-root . \
    --out-dir cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-smoke

# Verify with the Phase 9B validator (separate run; checks the digest)
python3 scripts/validate_evomap_phase9b_curator_nightly_integration.py
```

---

## 8. What this phase does NOT do (hard boundaries)

- ❌ Does NOT install a real cron job.
- ❌ Does NOT create a systemd timer.
- ❌ Does NOT run `evolver` (no `--loop`, no `run`, no `review`, no
  `--approve`, no `solidify`).
- ❌ Does NOT connect to EvoMap Hub. `A2A_HUB_URL` is not set and is forced
  empty in subprocess envs.
- ❌ Does NOT publish any assets.
- ❌ Does NOT consume ATP credits or run autobuy.
- ❌ Does NOT call OpenAI / Codex / GitHub Copilot / any AI API.
- ❌ Does NOT call Telegram API.
- ❌ Does NOT issue any `curl` / `wget` / HTTP request.
- ❌ Does NOT run real `pytest` / `npm test` / `cargo test` / `go test` /
  `mvn test`.
- ❌ Does NOT read `.env` files (any tracked `.env` path would fail
  `secret_scan_clean` immediately).
- ❌ Does NOT read real API keys / tokens / cookies / Authorization headers /
  private keys.
- ❌ Does NOT mutate the real OpenClaw / Hermes / systemd / cron config.
- ❌ Does NOT install `python` third-party packages; everything is stdlib-only.
- ❌ Does NOT auto-apply canary bundles to real runtime — only
  `evomap_apply_bundle.py --dry-run` is invoked, and the target is
  `/tmp/atl-evomap-nightly-canary-<id>` (isolated, ephemeral).

---

## 9. Next steps (out of scope for this phase)

- **Phase 9C (proposed):** curator-driven canary **apply** with an explicit
  operator gate (e.g. only when `apply_dry_run` PASS AND human-issued
  token AND `blocking=false` lane). Still no auto-publish.
- **Phase 8B (separate, operator-led):** real cron install of
  `scripts/evomap_nightly_validate.py` at `/etc/cron.d/evomap-nightly` or
  equivalent. This phase ships only the example template at
  `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/templates/cron.example`
  (still NOT installed).
- **browser-control bundle (proposed):** add a 5th canonical bundle for
  browser-control failures (requires separate OpenClaw evolution kit phase).

---

## 10. Files added or modified by this phase

- `cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/validation-loop-manifest.json`
  — added `canary_bundles[]`, `extended_by_phase`, `manifest_version 0.2.0`,
  new `checks_detail.canary_bundles_checked`, updated `purpose`/`intent`/`checks`.
- `scripts/evomap_nightly_validate.py` — added `_load_manifest`,
  `check_canary_bundles`, `_extract_apply_ok`; added `check_canary_bundles`
  to `checks[]`; added 9A to `all_phase_validators_pass`; promoted
  `validators` to top-level digest; added top-level `bundle_checks`,
  `canary_bundle_checks`, `canary_summary`; updated Markdown renderer with
  `## Canary / Curator-generated bundles` section.
- `scripts/validate_evomap_phase9a_bundle_curator_skill.py` —
  forward-compatible fix: removed 8A from `PRIOR_VALIDATORS` to break
  nightly runner → 9A → 8A → runner recursion (with explanatory comment);
  no artifact / secret / report check lowered.
- `data/cases.json` — added `phase = "ATL-EVOMAP-9B ..."`,
  `status = "curator nightly integration smoke pass"`,
  `final_status = "CURATOR_NIGHTLY_INTEGRATION_SMOKE_PASS"`, and a 9B
  `phase_history` entry.
- `cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/`
  — new directory containing this README, the case report, and the
  `artifacts/nightly-smoke/` digest outputs.
- `reports/ATL_EVOMAP_9B_CURATOR_NIGHTLY_INTEGRATION_REPORT.md` — top-level
  report (same content, repo-rooted).
- `scripts/validate_evomap_phase9b_curator_nightly_integration.py` —
  validator for this phase.
- `README.md` — main case README updated with 9B row.

---

## 11. Smoke result (this commit)

```
overall_status       : PASS
blocking_total       : 9
blocking_passed      : 9
blocking_failed      : 0
validator_count      : 7
validators_passed    : 7
bundle_inspect_count : 4
bundle_validate_count: 4
canary_total         : 1
canary_passed        : 1
canary_failed        : 0
canary_status        : CANARY_PASS
canary_blocking      : false
secret_scan_ok       : true
git_hygiene_ok       : true
hard_boundaries_ok   : true
```