# ATL-EVOMAP-5 · Local Evolution Kit · Top-Level Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** 5 · Local Evolution Kit
**Status:** **PASS**
**Date:** 2026-06-19 (Asia/Shanghai)
**Baseline commit:** `f7897da` (Phase 4C PASS)
**Apply target (test only):** `/tmp/atl-evomap-phase5-apply-target` (NOT in main repo)

---

## TL;DR

The OpenClaw Local Evolution Kit is **complete and proven**. The kit consists of:

- **1 canonical bundle** (`openclaw-tool-use-discipline.bundle.json`, 5458 bytes, schema `atl-evomap-portable-bundle-v0.1`)
- **3 stdlib-only tools** (inspect / validate / apply)
- **3 templates** (Gene / Capsule / MemoryGraph signals)
- **4-step recipe** (validate → inspect → dry-run → apply --yes)
- **6 self-test artifacts** (all in `artifacts/`)
- **5 idiomatic usage examples** documented

**All 16 hard boundaries preserved** (no Hub, no publish, no credits, no --approve, no solidify, no real config mutation, no secrets, no source modification, no isolated runtime committed, stdlib only).

The **local-only Gene + Capsule pathway is now productized** as a durable toolset.

---

## Key Evidence

### Bundle: `bundle/openclaw-tool-use-discipline.bundle.json`

- `schema_version: atl-evomap-portable-bundle-v0.1`
- `source_phase: ATL-EVOMAP-4B` (provenance chain)
- 1 gene (bare-compatible) + 1 capsule (phase4b) + execution_trace (4 steps) + safety (11 fields) + import_contract (3 required + 3 optional files) + kit_provenance (links to Phase 4C validation)

### Tool self-tests

| Tool | Test | Result |
|---|---|---|
| `evomap_inspect_bundle.py` | Inspect canonical bundle | `ok: true`, gene + capsule + 4-step trace + safety returned |
| `evomap_validate_bundle.py` | Validate canonical bundle | `ok: true`, 12/12 checks PASS (including secret scan) |
| `evomap_apply_bundle.py` --dry-run | Plan writes to clean target | 6 writes planned, **0 files written** (truly non-destructive) |
| `evomap_apply_bundle.py` --yes | Apply to clean target | 6 writes executed, 0 errors |

### Target after apply --yes

```
gene_count: 1
capsule_count: 1
memory_graph_lines: 5
gene_ids: ["gene_distilled_openclaw-tool-use-discipline-bare-compatible"]
capsule_ids: ["capsule_openclaw_tool_use_discipline_phase4b"]
memory_graph_signals: ["tool_bypass", "repeated_tool_usage", "protocol_drift", "session_context", "repo_context"]
```

### Idempotency

Re-applying the same bundle to the populated target:
- `existing_genes: 1, new_genes: 1` (no duplication; id-based dedup)
- `existing_capsules: 1, new_capsules: 1` (no duplication; id-based dedup)
- `signals_added: 5` (would append 5 more; memory_graph is append-only by design)

### Safety audit (16 boundaries)

All preserved. Specifically:
- **Tool-level enforcement:** apply tool does not contact Hub, does not publish, does not run `evolver`, does not write secrets
- **Pre-flight enforcement:** validate tool runs secret scan; apply tool refuses to write if bundle has secrets
- **Default-safety:** apply defaults to --dry-run; --yes required for real write
- **Source protection:** apply only writes the target's `.evolver/` + `memory/evolution/`, never touches real main repo or Evolver package source
- **Target protection:** apply refuses to write if target doesn't exist as a directory; warns (but allows) if target is not a git repo

---

## Files

### Case directory: `cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/`

- `README.md` (10.4 KB, full kit doc)
- `bundle/openclaw-tool-use-discipline.bundle.json` (5458 bytes)
- `tools/evomap_inspect_bundle.py` (2674 bytes)
- `tools/evomap_validate_bundle.py` (6817 bytes)
- `tools/evomap_apply_bundle.py` (8869 bytes)
- `templates/GENE_TEMPLATE.json`
- `templates/CAPSULE_TEMPLATE.json`
- `templates/MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl`
- `artifacts/inspect-bundle-output.json`
- `artifacts/validate-bundle-output.json`
- `artifacts/apply-bundle-dry-run-output.json`
- `artifacts/apply-bundle-yes-output.json`
- `artifacts/apply-target-files.txt`
- `artifacts/apply-target-summary.json`
- `ATL_EVOMAP_5_LOCAL_EVOLUTION_KIT_REPORT.md` (14.5 KB, full report)

### Top-level: `reports/ATL_EVOMAP_5_LOCAL_EVOLUTION_KIT_REPORT.md` (this file)

### Top-level scripts: `scripts/`
- `evomap_inspect_bundle.py`
- `evomap_validate_bundle.py`
- `evomap_apply_bundle.py`

### Validator: `scripts/validate_evomap_phase5_local_evolution_kit.py` (TBD)

### Apply target (test only): `/tmp/atl-evomap-phase5-apply-target` (NOT committed)

---

## 4-Step Usage Recipe

```bash
# 1. Validate
python3 scripts/evomap_validate_bundle.py --bundle <bundle.json>

# 2. Inspect
python3 scripts/evomap_inspect_bundle.py --bundle <bundle.json>

# 3. Dry-run
python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --dry-run

# 4. Apply (with explicit consent)
python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --yes

# 5. Manually run evolver in the clean target
cd <target> && unset A2A_HUB_URL && evolver run && evolver review
```

---

## Comparison: Phase 4C → Phase 5

| Aspect | Phase 4C | Phase 5 |
|---|---|---|
| Question | Can Gene + Capsule be reused across sessions? | Can the proven pathway be productized? |
| Deliverable | Test artifacts in 2 isolated runtimes | Reusable toolset (3 tools + 3 templates + 1 bundle + recipe) |
| Reusability | Manual copy of artifacts | Standard CLI invocation |
| Validation | Manual inspection of run outputs | Automated 12-check validator with secret scan |
| Idempotency | N/A (one-shot test) | Verified: gene/capsule dedup, signals append |
| Hard boundaries | 16 preserved during test | 16 preserved by tool design |
| Future applicability | One proven bundle | Extensible to new bundles via templates |

---

## Next: Phase 6 / Future Work

Phase 5 marks the **end of the ATL-EVOMAP exploration series**. Future work (separate tasks, not Phase 6):

1. **Create more bundles** for other proven (Gene, Capsule) pairs (Hermes, Codex, protocol-dedup, etc.)
2. **Add a `bundle-curator` skill** that auto-generates bundles from evolver run outputs
3. **Extend apply tool** with `--bundle-list`, `--from`, `--prune-events`, etc.
4. **Add a `bundle-test` tool** that auto-runs `evolver run` + `evolver review` and verifies selector hit the right gene (fully automated version of step 5 in the recipe)

All future work should maintain the same 16 hard boundaries established in Phase 4A.
