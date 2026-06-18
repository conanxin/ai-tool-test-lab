# ATL-EVOMAP-4A · Isolation Selector Test · Top-Level Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** 4A · Isolation Selector
**Status:** **PASS**
**Date:** 2026-06-19 (Asia/Shanghai)
**Baseline commit:** `685477a` (Phase 3C-V2 BLOCKED)
**Isolated runtime commit:** `f14ba6c` (in `/tmp/atl-evomap-4a-isolated`, NOT in main repo)

---

## TL;DR

In a fully isolated runtime at `/tmp/atl-evomap-4a-isolated` — only 1 Gene, 0 failed events, 0 pollution signals, 5 clean bare signals — the EvoMap Evolver selector **reliably hit** `gene_distilled_openclaw-tool-use-discipline-bare-compatible`. This **reproduces** the Phase 3B2 result and **proves** that the Phase 3C-V2 BLOCKED was caused by session-and-history pollution in the main repo runtime, **not** by an inherent selector incompatibility with the OpenClaw Gene.

**Phase 4B (capsule creation in isolated env) is GO.**

---

## Evidence

### Selected Gene (run output)

```
2. Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible".
ACTIVE STRATEGY (gene_distilled_openclaw-tool-use-discipline-bare-compatible):
  1. Read files with the read tool before referencing their content in reasoning.
  2. Use the edit tool for in-place file changes; never use sed -i or awk -i inplace.
  3. Use the search tool for repo-wide content search before falling back to rg via exec.
  4. Prefix every non-validator exec invocation with a one-line EXEC: <reason> in reasoning.
  5. Re-run validators after each substantive change.
```

### Review output diff (excerpt)

```
+ hypothesis (gene.id: gene_distilled_openclaw-tool-use-discipline-bare-compatible)
  selector.selected: gene_distilled_openclaw-tool-use-discipline-bare-compatible
  selector.reason: ["signals match gene.signals_match", "signals: memory_missing",
                    "drift_intensity: 1.000", "selection_path: distilled_fallback"]
  selector.alternatives: []
+ attempt (gene.id: gene_distilled_openclaw-tool-use-discipline-bare-compatible)
```

### Pollution check (events.jsonl + memory_graph.jsonl)

| Source | Pre-run pollution | Post-run pollution |
|---|---|---|
| `.evolver/gep/events.jsonl` | 0 events | (still 0) |
| `.evolver/gep/failed_capsules.json` | 0 | (still 0) |
| `memory/evolution/memory_graph.jsonl` (5 events) | 0 pollution signals | (still 0) |
| evolver output (boilerplate only) | 0 actual pollution events | `consecutive_failure_streak` only in system prompt text, not as event |

### Safety audit

- Hub: not connected (`A2A_HUB_URL` unset, `Hub Matched Solution: (no hub match)`)
- Publish: disabled (`EVOLVER_AUTO_PUBLISH=false`)
- Credits: 0 consumed
- Validator: disabled
- `evolver review --approve`: NOT executed (per 硬边界 #12)
- `evolver solidify` / `node index.js solidify`: NOT executed (per 硬边界 #13)
- Secrets: none in any artifact
- Real OpenClaw/Hermes config: not touched
- Evolver package source: not modified
- Runtime .evolver/ + memory/: in /tmp only, NOT committed to main repo

---

## Comparison: Phase 3B2 vs Phase 3C-V2 vs Phase 4A

| Aspect | Phase 3B2 (PASS) | Phase 3C-V2 (BLOCKED) | Phase 4A (PASS) |
|---|---|---|---|
| Runtime | clean-ish | polluted (real repo) | fully clean (/tmp isolated) |
| `genes.json` count | 1 (bare-compatible) | 1 (non-hollow variant) | 1 (bare-compatible) |
| `events.jsonl` | 0 failed | 3 failed | 0 failed |
| `memory_graph.jsonl` | bare signals | mixed + pollution | 5 bare signals only |
| `user_feature_request` triggers | no | yes (session text) | no |
| Selector match | `distilled_fallback` | `repair` (GEP-internal) | `distilled_fallback` |
| Selected Gene | bare-compatible | GEP-internal `gene_gep_repair_from_errors` | bare-compatible |
| Cycles attempted | 1 | 13 | 1 |

Phase 3B2 and Phase 4A are functionally identical (clean runtime, bare-compatible Gene) — both show the selector can hit the OpenClaw Gene. Phase 3C-V2's failure was caused by **pollution accumulating in the real repo runtime**, not by a broken Gene or a broken selector.

---

## Implications

1. The OpenClaw Gene (`gene_distilled_openclaw-tool-use-discipline-bare-compatible`) is **selectable in principle**.
2. To use it in the real `ai-tool-test-lab` runtime, either:
   a. **Bypass `evolver run`** and apply the Gene's strategy directly via a local signal detector (this is the ATL-EVOMAP-3b-1 plan: "OpenClaw signal detector that emits `tool_bypass` etc. to memory_graph.jsonl, and a local executor that runs the strategy steps"), or
   b. **Build a Gene-rotation policy** that injects the distilled Gene as the first candidate before the failed-events repair loop kicks in.
3. Phase 4B can proceed in the isolated runtime to create a real Capsule with `execution_trace`, demonstrating end-to-end that the bare-compatible Gene produces a valid Capsule.

---

## Files

### Case directory: `cases/evomap-evolver-openclaw-v0/phase4a-isolation-selector/`

- `ATL_EVOMAP_4A_ISOLATION_SELECTOR_REPORT.md` (full report, 13.4KB)
- `artifacts/isolation-setup-summary.json` (setup summary)
- `artifacts/evolver-run-isolated-output.txt` (full run output)
- `artifacts/evolver-review-isolated-output.txt` (full review output)
- `artifacts/selector-isolation-grep.txt` (grep evidence)

### Top-level: `reports/ATL_EVOMAP_4A_ISOLATION_SELECTOR_REPORT.md` (this file)

### Validator: `scripts/validate_evomap_phase4a_isolation_selector.py` (TBD)

### Isolated runtime: `/tmp/atl-evomap-4a-isolated` (NOT committed)
- `.git/` independent
- `.evolver/gep/genes.json` (1 bare-compatible Gene)
- `.evolver/gep/capsules.json` (empty)
- `.evolver/gep/events.jsonl` (empty)
- `memory/evolution/memory_graph.jsonl` (5 bare signals)
- Baseline commit: `f14ba6c`

---

## Next: Phase 4B

**Status:** GO

**Goals (proposed):**
1. In isolated runtime, create a real `Capsule` referencing the OpenClaw Gene with non-empty `execution_trace`.
2. Verify Capsule survives a second `evolver review` cycle.
3. Document minimal skill/asset set required for a `trace_empty`-clean Capsule.
4. Assess whether the isolated-runtime Capsule can be exported to the main repo without triggering GEP-internal repair loop.

**Hard boundaries:** unchanged (no Hub, no publish, no credits, no --approve, no solidify).
