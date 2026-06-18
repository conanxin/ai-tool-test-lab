# OpenClaw Local Evolution Kit

**Version:** v1 (2026-06-19)
**Provenance:** ATL-EVOMAP Phase 4A/4B/4C PASS → Phase 5 productization
**Bundle schema:** `atl-evomap-portable-bundle-v0.1`
**Validation record:** Phase 4C at `f7897da` (Session A & B both PASS, score_ranked path, capsule trigger matches signals)

---

## What this kit is

A self-contained, **local-only** toolset for curating and applying **Gene + Capsule** pairs (proven in isolated Evolver runtimes) to new isolated runtimes — **without** connecting to the EvoMap Hub, **without** publishing, **without** consuming credits, and **without** running `evolver review --approve` or `evolver solidify`.

The kit is the productization of ATL-EVOMAP Phases 4A/4B/4C, which proved that a manually-seeded Capsule referencing a distilled Gene can:

1. **Be selected** by the evolver in a clean env (Phase 4A)
2. **Survive** the `evolver run` + `evolver review` cycle in a clean env (Phase 4B)
3. **Be reused across sessions** with the same identity (Phase 4C)

The kit gives you **three Python stdlib tools** (inspect, validate, apply) plus a canonical bundle, templates, and a 4-step recipe to make new bundles for new Gene/Capsule pairs.

---

## What problem it solves

The evolver's local runtime gets **polluted** by real-environment history:

- `failed_capsules.json` accumulates `consecutive_failure_streak` entries
- `events.jsonl` accumulates `user_feature_request` / protocol_drift / session_context events
- These trigger the evolver's `gene_gep_repair_from_errors` GEP-internal path, which **overrides** the distiller's recommendation

This pollution is what caused Phase 3C-V2 (and many real production runs) to be **BLOCKED** at the GEP-internal selector.

**The kit provides a controlled way to inject a known-good (Gene, Capsule) pair into a clean isolated runtime**, so the evolver in that runtime will select the known-good pair via `score_ranked` (with reason `capsule trigger matches signals`) — a more reliable signal than the polluted `distilled_fallback` or worse `gep_repair_from_errors`.

---

## Kit contents

```
phase5-local-evolution-kit/
├── README.md                                          ← this file
├── bundle/
│   └── openclaw-tool-use-discipline.bundle.json       ← canonical Phase 4C bundle
├── tools/
│   ├── evomap_inspect_bundle.py                        ← stdlib inspector
│   ├── evomap_validate_bundle.py                       ← stdlib validator (with secret scan)
│   └── evomap_apply_bundle.py                          ← stdlib apply (dry-run by default)
├── templates/
│   ├── GENE_TEMPLATE.json
│   ├── CAPSULE_TEMPLATE.json
│   └── MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl
├── artifacts/                                          ← test outputs (see "How to use")
└── ATL_EVOMAP_5_LOCAL_EVOLUTION_KIT_REPORT.md         ← phase 5 report
```

Plus three **top-level scripts** in `scripts/`:

```
scripts/
├── evomap_inspect_bundle.py
├── evomap_validate_bundle.py
└── evomap_apply_bundle.py
```

The `case tools/` copies are for self-contained distribution of the kit as a unit; the `scripts/` copies are the canonical installation.

---

## Bundle schema (`atl-evomap-portable-bundle-v0.1`)

```json
{
  "schema_version": "atl-evomap-portable-bundle-v0.1",
  "source_phase": "ATL-EVOMAP-4B",
  "source_session": "/tmp/atl-evomap-4a-isolated",
  "target_capsule_id": "...",
  "target_gene_id": "...",
  "gene": { ... full Gene JSON ... },
  "capsule": { ... full Capsule JSON (with execution_trace) ... },
  "execution_trace": { ... top-level trace summary ... },
  "safety": {
    "hub": "disabled",
    "publish": "disabled",
    "credits": 0,
    "visibility": "private",
    "no_failed_events": true,
    "no_pollution_signals": true,
    "approve": "not_executed",
    "solidify": "not_executed"
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
    ]
  }
}
```

---

## How to use (4-step recipe)

### 1. Validate the bundle

```bash
python3 scripts/evomap_validate_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json
```

Expected output: `ok: true` and 12/12 checks pass. The validator runs a **secret scan** over the entire bundle and rejects any bundle that contains API keys, tokens, cookies, Authorization headers, private keys, or `.env` content.

### 2. Inspect the bundle

```bash
python3 scripts/evomap_inspect_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json
```

Expected output: a JSON summary with gene id, capsule id, execution trace stages, safety record.

### 3. Apply dry-run

```bash
# Create a clean target first
mkdir -p /tmp/my-clean-runtime && cd /tmp/my-clean-runtime && git init

# Dry-run shows what would be written
python3 scripts/evomap_apply_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json \
  --target-runtime /tmp/my-clean-runtime \
  --dry-run
```

Dry-run **does not write anything**. Use it to verify the plan before committing.

### 4. Apply with explicit consent

```bash
python3 scripts/evomap_apply_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json \
  --target-runtime /tmp/my-clean-runtime \
  --yes
```

The `--yes` flag is required to actually write. Without it, the tool defaults to dry-run.

### 5. Manually run evolver in the clean target

```bash
cd /tmp/my-clean-runtime

unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private

evolver run
evolver review
```

The expected selector output is:

```
2. Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible".
   Reason: ... capsule trigger matches signals ...; selection_path: score_ranked
```

The presence of `capsule trigger matches signals` confirms the imported Capsule is being recognized as a usable prior asset.

---

## Hard boundaries (enforced)

| Boundary | Status |
|---|---|
| No EvoMap Hub connection | A2A_HUB_URL never set; tool does not contact Hub |
| No publishing | EVOLVER_AUTO_PUBLISH=false; tool does not publish |
| No credits | Tool does not call Hub; 0 credits consumed |
| No ATP autobuy | EVOLVER_ATP_AUTOBUY=off; tool does not autobuy |
| No `evolver review --approve` | Tool does not invoke this |
| No `evolver solidify` / `node index.js solidify` | Tool does not invoke this |
| No real config mutation outside target | Only writes target's .evolver/ + memory/evolution/ |
| No secrets in bundle | Validator scans for and rejects secret patterns |
| No `.env` scan | Tool does not read .env |
| No Evolver package source modification | Tool does not touch /usr/lib/node_modules/evolver/ or similar |
| stdlib only | All 3 tools use only Python stdlib (argparse, json, re, sys, pathlib) |

---

## What this kit does NOT do (and won't ever do)

- ❌ Does **not** connect to the EvoMap Hub
- ❌ Does **not** publish assets to the Hub
- ❌ Does **not** consume credits
- ❌ Does **not** execute `evolver review --approve` or `evolver solidify`
- ❌ Does **not** modify the real main repo's `.evolver/` or `memory/` (apply is for isolated targets only)
- ❌ Does **not** read or write secrets, API keys, tokens, cookies, Authorization headers
- ❌ Does **not** scan `.env` files
- ❌ Does **not** modify Evolver package source code
- ❌ Does **not** run `evolver run` / `evolver review` on its own (that's a manual step after apply)

---

## Idempotency

The apply tool is **idempotent on gene/capsule** (id-based dedup: re-applying with the same bundle replaces by id, never duplicates) and **append-only on memory_graph** (signals accumulate over time). To re-validate a target after re-apply, run inspect + validate.

---

## Extending to new bundles

To create a new bundle (for a new Gene + Capsule pair), use the templates in `templates/`:

1. Fill in `GENE_TEMPLATE.json` with the new gene's id, signals, strategy
2. Fill in `CAPSULE_TEMPLATE.json` with the new capsule's id, gene reference, 4-step execution_trace
3. Fill in `MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl` with 5 clean bare signals pointing at the new gene
4. Bundle them into a single JSON following the `import_contract` schema
5. Run `evomap_validate_bundle.py` to check the bundle
6. Run `evomap_inspect_bundle.py` to see the summary
7. Run `evomap_apply_bundle.py --dry-run` then `--yes` to apply

---

## Provenance (which phase proved what)

- **Phase 4A (`bd7133a`):** Distilled Gene can be **selected** in clean isolated env (selection_path=distilled_fallback, alternatives=[])
- **Phase 4B (`e8451f3`):** A Capsule referencing the Gene can be **created and survive** an evolver cycle in clean env (capsule_count preserved, all fields preserved, execution_trace preserved)
- **Phase 4C (`f7897da`):** The same Gene + Capsule can be **imported into a second session** and recognized identically (selection_path=score_ranked, capsule trigger matches signals in both)
- **Phase 5 (this commit):** Productize the proven path as a 3-tool kit + canonical bundle + templates

---

## Files in this kit

| Path | Purpose |
|---|---|
| `bundle/openclaw-tool-use-discipline.bundle.json` | Canonical Phase 4C bundle (Gene + Capsule + execution_trace + safety + import_contract) |
| `tools/evomap_inspect_bundle.py` | Read-only inspector (returns JSON summary) |
| `tools/evomap_validate_bundle.py` | Read-only validator (12 checks including secret scan) |
| `tools/evomap_apply_bundle.py` | Apply tool (defaults to --dry-run, requires --yes for real write) |
| `templates/GENE_TEMPLATE.json` | Gene field template |
| `templates/CAPSULE_TEMPLATE.json` | Capsule field template |
| `templates/MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl` | 5 clean bare signals template |
| `artifacts/` | Test outputs (inspect / validate / apply dry-run / apply --yes / target summary) |
| `ATL_EVOMAP_5_LOCAL_EVOLUTION_KIT_REPORT.md` | Full phase 5 report |
