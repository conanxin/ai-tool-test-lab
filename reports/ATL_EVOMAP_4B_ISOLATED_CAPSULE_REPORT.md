# ATL-EVOMAP-4B · Isolated Capsule Test · Top-Level Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** 4B · Isolated Capsule
**Status:** **PASS**
**Date:** 2026-06-19 (Asia/Shanghai)
**Baseline commit:** `bd7133a` (Phase 4A PASS)
**Isolated runtime commits:**
- `f14ba6c` — initial baseline (Phase 4A)
- `8c6853f` — seed capsule (Phase 4B)

---

## TL;DR

In the isolated runtime at `/tmp/atl-evomap-4a-isolated` (reused from Phase 4A), a **manually-seeded Capsule** referencing `gene_distilled_openclaw-tool-use-discipline-bare-compatible` was created with a 4-step `execution_trace` (build + 2 validate + canary). After a subsequent `evolver run` + `evolver review` cycle:

- The Capsule **survived intact** (id, gene, status, confidence, execution_trace all preserved)
- The **selector still hit the OpenClaw Gene** (no GEP-internal pollution)
- **0 pollution events** were emitted
- **All 16 hard boundaries** were preserved (no Hub, no publish, no credits, no --approve, no solidify, no secrets)

The **two-step local-only pathway** is now proven:
1. Phase 4A: distilled Gene can be **selected** in clean env ✅
2. Phase 4B: a Capsule referencing that Gene can be **created and survive** in clean env ✅

**Phase 4C (cross-session reuse) is GO.**

---

## Key Evidence

### Capsule survival check (post-cycle)

```
capsule_count 1
found_target True
gene_id gene_distilled_openclaw-tool-use-discipline-bare-compatible
status success
confidence 0.84
execution_trace_non_empty True
execution_trace_type list
execution_trace_steps 4
  step_1 build    python3 openclaw_tool_use_fixture.py --input ...   exit=0
  step_2 validate python3 -m json.tool /tmp/openclaw_tool_use_...    exit=0
  step_3 validate json_parse_pass                                    exit=0
  step_4 canary   safety_check                                       exit=0
target_survived True
```

### Selector behavior (re-hit OpenClaw Gene)

```
2. Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible".
selection_path: distilled_fallback
selector.alternatives: []
selector.reason: ["signals match gene.signals_match", "signals: memory_missing",
                  "drift_intensity: 1.000", "selection_path: distilled_fallback"]
```

The seeded Capsule did **not destabilize** the selector.

### Pollution check

| Source | Pre-run pollution | Post-run pollution |
|---|---|---|
| `events.jsonl` | 0 events | (still 0) |
| `failed_capsules.json` | 0 | (still 0) |
| `memory_graph.jsonl` (5 events) | 0 pollution signals | (still 0) |
| evolver output (boilerplate only) | n/a | no new pollution events |

### Safety audit

- Hub: not connected (`(no hub match)`)
- Publish: disabled
- Credits: 0
- Validator: disabled
- `evolver review --approve`: NOT executed
- `evolver solidify`: NOT executed
- Secrets: none in any artifact
- Real OpenClaw/Hermes config: not touched
- Evolver package source: not modified
- Runtime .evolver/ + memory/: in /tmp only, NOT committed to main repo

---

## Files

### Case directory: `cases/evomap-evolver-openclaw-v0/phase4b-isolated-capsule/`

- `ATL_EVOMAP_4B_ISOLATED_CAPSULE_REPORT.md` (full report, 13.6 KB)
- `artifacts/capsule-openclaw-tool-use-discipline-phase4b.json` (the seeded Capsule, full)
- `artifacts/capsules-json-after-seed-summary.json` (capsules.json state after seeding)
- `artifacts/execution-trace-openclaw-tool-use.json` (real fixture output as execution_trace evidence)
- `artifacts/evolver-run-isolated-capsule-output.txt` (full run output)
- `artifacts/evolver-review-isolated-capsule-output.txt` (full review output)
- `artifacts/capsule-survival-check.txt` (Python check confirming target_survived=True)
- `artifacts/capsule-grep-after-run.txt` (grep evidence of preserved Capsule fields)
- `artifacts/isolation-capsule-setup-summary.json` (setup summary)

### Top-level: `reports/ATL_EVOMAP_4B_ISOLATED_CAPSULE_REPORT.md` (this file)

### Validator: `scripts/validate_evomap_phase4b_isolated_capsule.py` (TBD)

### Isolated runtime: `/tmp/atl-evomap-4a-isolated` (NOT committed)
- Phase 4A baseline commit: `f14ba6c`
- Phase 4B seed commit: `8c6853f`
- 1 bare-compatible Gene
- 1 Capsule (`capsule_openclaw_tool_use_discipline_phase4b`)
- 5 clean bare signals
- 0 pollution events
- 0 failed events

---

## Comparison: Phase 4A vs Phase 4B

| Aspect | Phase 4A | Phase 4B |
|---|---|---|
| Question | Can selector hit OpenClaw Gene in clean env? | Can a Capsule survive run/review cycle in clean env? |
| Runtime | isolated (1 Gene, 0 events, 0 capsules) | isolated (1 Gene, 0 events, 1 Capsule after seed) |
| Outcome | selector hit OpenClaw Gene | Capsule survived intact; selector still hits OpenClaw Gene |
| Cycles | 1 | 1 (with seed step before) |
| Hard boundaries | 15 | 16 (added: re-create if Phase 4A runtime missing) |

Phase 4A answers "can the Gene be selected?"; Phase 4B answers "can the Capsule survive?". Phase 4C will answer "can the Capsule be reused across sessions?".

---

## Next: Phase 4C

**Status:** GO

**Goals (proposed):**

1. Copy the isolated runtime's `capsules.json` to a second isolated runtime (e.g., `/tmp/atl-evomap-4c-session-b`).
2. In each runtime, run `evolver run` + `evolver review` and verify the **same** Capsule is recognized.
3. Document the minimal import contract (which fields, which schema) for cross-session-portable Capsules.
4. Assess whether the **main repo runtime** can accept a Capsule import without triggering GEP-internal repair loop.

**Hard boundaries:** unchanged.
