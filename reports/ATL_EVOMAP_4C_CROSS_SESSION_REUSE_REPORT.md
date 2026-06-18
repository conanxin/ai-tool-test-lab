# ATL-EVOMAP-4C · Cross-Session Reuse Test · Top-Level Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** 4C · Cross-Session Reuse
**Status:** **PASS**
**Date:** 2026-06-19 (Asia/Shanghai)
**Baseline commit:** `e8451f3` / `0071523` (Phase 4B PASS)
**Session A commit (isolated):** `bf7bae1`
**Session B commit (isolated):** `7450847`

---

## TL;DR

The **local-only Capsule pathway is cross-session-portable**. A portable bundle (Gene + Capsule + execution_trace) was:

1. Created as a single JSON artifact (`portable-openclaw-gene-capsule-bundle.json`)
2. Imported into **two independent isolated runtimes** (different paths, different git histories)
3. Recognized by both runtimes' evolver with **`capsule trigger matches signals`** in the selector reason
4. Survived the `evolver run` + `evolver review` cycle in both sessions with **identical identity** preserved (id, gene, status, confidence, execution_trace, stages)

**Three-step local-only pathway now complete:**
- Phase 4A: distilled Gene **selectable** in clean env ✅
- Phase 4B: Capsule referencing Gene **survives** in clean env ✅
- Phase 4C: Gene + Capsule **reused across sessions** ✅

**Phase 5 (local evolution kit) is GO.**

---

## Key Evidence

### Portable bundle (`portable-openclaw-gene-capsule-bundle.json`, 4841 bytes)

- `schema_version: atl-evomap-portable-bundle-v0.1`
- Contains: `gene` + `capsule` + `execution_trace` + `safety` + `import_contract`
- Required files (3): `genes.json`, `capsules.json`, `memory_graph.jsonl`
- Optional files (3): `events.jsonl`, `failed_capsules.json`, `candidates.jsonl`

### Session A — `/tmp/atl-evomap-4c-session-a` (commit `bf7bae1`)

Selector output:
```
2. Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible".
   Reason: signals match gene.signals_match; capsule trigger matches signals;
           signals: repeated_tool_usage:exec, tool_bypass; drift_intensity: 1.000;
           selection_path: score_ranked
```

Capsule survival:
```
capsule_count 1
found_target True
gene gene_distilled_openclaw-tool-use-discipline-bare-compatible
status success
confidence 0.84
execution_trace_non_empty True
execution_trace_steps 4
execution_trace_stages ['build', 'validate', 'validate', 'canary']
```

### Session B — `/tmp/atl-evomap-4c-session-b` (commit `7450847`)

**Identical** selector output and capsule survival to Session A (verified by `diff -q` on .evolver/ pre-run and by identical survival-check output).

### Cross-session reuse evidence

The selector reason field in **both** sessions contains:

> `capsule trigger matches signals`

This is the evolver's way of saying "I'm using the imported Capsule's trigger array as evidence for selecting this Gene". The same reason appeared in both sessions — confirming the **same Capsule identity is recognized in both**.

### Pollution check

| Source | Session A | Session B |
|---|---|---|
| `events.jsonl` lines | 0 | 0 |
| `failed_capsules.json` entries | 0 | 0 |
| pollution signals in memory_graph | 0 | 0 |
| consecutive_failure_streak | 0 | 0 |
| user_feature_request | 0 | 0 |

### Safety audit

- Hub: not connected (both sessions, A2A_HUB_URL unset)
- Publish: disabled (both sessions, EVOLVER_AUTO_PUBLISH=false)
- Credits: 0 (both sessions, no Hub, no autobuy)
- Validator: disabled
- `evolver review --approve`: NOT executed (per 硬边界 #12)
- `evolver solidify` / `node index.js solidify`: NOT executed (per 硬边界 #13)
- No secrets in any artifact
- No real OpenClaw/Hermes/systemd/cron config touched
- No Evolver package source modified
- Both isolated runtimes in /tmp, NOT committed to main repo

---

## Five-Score Summary

| Dimension | Status | Notes |
|---|---|---|
| A. Portable bundle | PASS | All 3 core assets present, valid JSON, schema defined |
| B. Session A | PASS | Selector hit OpenClaw Gene (score_ranked), Capsule survived |
| C. Session B | PASS | Selector hit OpenClaw Gene (score_ranked), Capsule survived |
| D. Cross-session portability | PASS | Same capsule id in A/B; identical survival; same reason |
| E. Safety | PASS | All 16 hard boundaries preserved (no Hub/publish/credits/--approve/solidify) |

---

## Comparison: Phase 4A → 4B → 4C

| Aspect | Phase 4A | Phase 4B | Phase 4C |
|---|---|---|---|
| Question | Can selector hit OpenClaw Gene in clean env? | Can Capsule survive run/review in clean env? | Can Gene + Capsule be reused across sessions? |
| Runtimes | 1 (isolated) | 1 (isolated) | 2 (isolated, independent git) |
| Selection path | distilled_fallback | distilled_fallback | **score_ranked** |
| "capsule trigger matches signals" | n/a | not observed | **observed in both** |
| Capsule survives | n/a | ✅ (1 session) | ✅ (2 sessions) |
| Hard boundaries | 15 | 16 | 16 |

Phase 4C **unlocks richer selection behavior**: `score_ranked` with `capsule trigger matches signals` — a more reliable signal than the bare `distilled_fallback` because the evolver now has both Gene and Capsule evidence to work with.

---

## Files

### Case directory: `cases/evomap-evolver-openclaw-v0/phase4c-cross-session-reuse/`

- `ATL_EVOMAP_4C_CROSS_SESSION_REUSE_REPORT.md` (full report, 16.3 KB)
- `artifacts/portable-openclaw-gene-capsule-bundle.json` (portable bundle, 4841 bytes)
- `artifacts/cross-session-setup-summary.json` (setup summary)
- `artifacts/evolver-run-session-a-output.txt`
- `artifacts/evolver-review-session-a-output.txt`
- `artifacts/evolver-run-session-b-output.txt`
- `artifacts/evolver-review-session-b-output.txt`
- `artifacts/capsule-survival-session-a.txt`
- `artifacts/capsule-survival-session-b.txt`
- `artifacts/cross-session-reuse-grep.txt` (grep evidence)

### Top-level: `reports/ATL_EVOMAP_4C_CROSS_SESSION_REUSE_REPORT.md` (this file)

### Validator: `scripts/validate_evomap_phase4c_cross_session_reuse.py` (TBD)

### Isolated runtimes: `/tmp/atl-evomap-4c-session-{a,b}` (NOT committed)
- Each: independent `git init`
- Each: 1 bare-compatible Gene + 1 Capsule
- Each: 5 clean bare signals
- Each: 0 pollution events
- Session A commit: `bf7bae1`
- Session B commit: `7450847`

---

## Next: Phase 5

**Status:** GO

**Goals (proposed):**

1. **Curate a portable bundle repository** — collect proven (Gene, Capsule) pairs verified in isolated env
2. **Document a `apply-bundle.sh` tool** — copies a bundle to a target runtime's `.evolver/gep/` and `memory/evolution/` without running `evolver run` in the polluted main runtime
3. **Test the import path on a clean main-runtime snapshot** — verify that importing a bundle does NOT trigger GEP-internal repair loop
4. **Document the safety contract** — what makes a bundle "safe to apply" (no secrets, no failed events, no pollution signals)

**Hard boundaries:**
- No Hub, no publish, no credits
- No `evolver review --approve` in real runtime
- No `evolver solidify` in real runtime
- Bundles only contain Gene + Capsule + execution_trace + 5 clean bare signals
- Apply via `cp` + `git add` in a controlled branch, NOT via `evolver run`

**Phase 5 success criteria:**
- A bundle imported into a clean main-runtime snapshot survives `evolver run` + `evolver review` without triggering GEP-internal repair
- The imported Capsule is recognized as `capsule trigger matches signals` in the selector reason
- The imported Capsule can be referenced as a "prior asset" in a subsequent cycle
