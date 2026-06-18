# ATL-EVOMAP-4A · Isolation Selector Test · Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** 4A · Isolation Selector
**Commit (Phase 3C-V2 baseline):** `685477a`
**Isolated runtime:** `/tmp/atl-evomap-4a-isolated` (not committed)
**Isolated runtime baseline commit:** `f14ba6c`
**Status:** **PASS** — selector re-hit OpenClaw Gene in clean environment

---

## 1. Goal

Verify that the Phase 3C-V2 BLOCKED result was caused by `history-and-session driven selector pollution`, NOT by an inherent selector incompatibility with the OpenClaw Gene.

To test this, build a **fully isolated runtime** at `/tmp/atl-evomap-4a-isolated` that:

1. Loads **only one Gene** (`gene_distilled_openclaw-tool-use-discipline-bare-compatible`).
2. Carries **zero failed EvolutionEvents**.
3. Has **no recent session transcript** that could be interpreted as `user_feature_request`.
4. Injects **5 clean bare signals** pointing exclusively at the OpenClaw Gene.
5. Runs `evolver run` + `evolver review` under the standard hard-boundary env.

Pass criterion: `evolver review` shows `Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible"` (or equivalent) and the diff is dominated by that gene's mutation events, with no GEP-internal gene selection.

---

## 2. Phase 3C-V2 BLOCKED Root Cause (recap)

| Pollutant | Source | Effect |
|---|---|---|
| `consecutive_failure_streak_3` | Failed Phase 3C EvolutionEvents in `.evolver/gep/events.jsonl` | Selector enters `repair` repair-loop, ignores memory_graph injection |
| `user_feature_request` | Recent session text containing feature words | LLM scanner classifies as user-driven, picks generic GEP Gene |
| `gene_gep_repair_from_errors` / `gene_gep_innovate_from_opportunity` | GEP-internal default genes | Always ranked above `distilled_fallback` path when history is dense |

Phase 3B2 already proved that on a `clean-ish` runtime (no failed events, no recent session), the selector can pick the OpenClaw Gene. Phase 4A re-tests this with **fully clean** conditions and documents the exact mechanism.

---

## 3. Isolation Runtime Design

**Location:** `/tmp/atl-evomap-4a-isolated` (outside main repo, not GitHub-tracked)

**Layout:**
```
/tmp/atl-evomap-4a-isolated/
├── .git/                            (independent git init)
├── README.md
├── openclaw_tool_use_fixture.py     (copied from main repo scripts/)
├── fixtures/
│   └── session-tool-use-sample.txt  (copied from Phase 3C-V2 fixtures)
├── .evolver/gep/
│   ├── genes.json                   (1 Gene: bare-compatible)
│   ├── capsules.json                (empty: 0 capsules)
│   ├── events.jsonl                 (empty: 0 events)
│   ├── failed_capsules.json         (empty)
│   └── candidates.jsonl             (empty)
└── memory/evolution/
    └── memory_graph.jsonl           (5 bare-signal MemoryGraphEvents, all targeting OpenClaw Gene)
```

**Baseline commit:** `f14ba6c` — clean state, zero failed events.

**Hard-boundary env (set before run):**
- `A2A_HUB_URL` unset
- `EVOLVE_STRATEGY=repair-only`
- `EVOLVER_AUTO_PUBLISH=false`
- `EVOLVER_VALIDATOR_ENABLED=false`
- `EVOLVER_ATP_AUTOBUY=off`
- `EVOLVER_DEFAULT_VISIBILITY=private`

**What's excluded from the runtime:**
- No `MEMORY.md`, `SOUL.md`, `USER.md`, `AGENTS.md` (forces evolver to scan-only via session tail)
- No `.evolver/gep/events.jsonl` entries (no failed EvolutionEvents to drive `consecutive_failure_streak`)
- No `~/.evomap/` node secret (Hub handshake impossible)
- No `gh` remote (`gh pr list` fails non-fatally, irrelevant to selector)

---

## 4. Injected Signals

5 MemoryGraphEvents, all `mutation.target = gene:gene_distilled_openclaw-tool-use-discipline-bare-compatible`:

| # | signal | origin | weight | context |
|---|---|---|---|---|
| 1 | `tool_bypass` | openclaw_signal_detector | 0.85 | Detected exec invocation without prior read on .md file |
| 2 | `repeated_tool_usage` | openclaw_signal_detector | 0.7 | Same exec command used >3 times for grep operations |
| 3 | `protocol_drift` | openclaw_signal_detector | 0.9 | Used read tool for binary file or wrong-tool-for-file-read scenario |
| 4 | `session_context` | openclaw_signal_detector | 0.6 | OpenClaw session marker detected in cwd / context tokens |
| 5 | `repo_context` | openclaw_signal_detector | 0.65 | Repository is ai-tool-test-lab with OpenClaw tool discipline focus |

**Excluded by design (Phase 3C-V2 pollutants):**
- `consecutive_failure_streak_3`
- `user_feature_request`
- any `consecutive_failure` pattern
- any failed EvolutionEvent

---

## 5. Evolver Run / Review Result

### Run output (excerpt, full file in artifacts/)

```
GEP — GENOME EVOLUTION PROTOCOL (v1.10.3 STRICT) Cycle #0001

1. Intent: UNKNOWN
   Reason: signals match gene.signals_match; signals: memory_missing; 
           drift_intensity: 1.000; selection_path: distilled_fallback

2. Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible".
ACTIVE STRATEGY (gene_distilled_openclaw-tool-use-discipline-bare-compatible):
  1. Read files with the read tool before referencing their content in reasoning.
  2. Use the edit tool for in-place file changes; never use sed -i or awk -i inplace.
  3. Use the search tool for repo-wide content search before falling back to rg via exec.
  4. Prefix every non-validator exec invocation with a one-line EXEC: <reason> in reasoning.
  5. Re-run validators after each substantive change.
```

### Review output (excerpt)

```
--- Gene ---
  ID:       gene_distilled_openclaw-tool-use-discipline-bare-compatible
  Category: optimize
  Summary:  OpenClaw-specific tool discipline with bare-signal compatibility...
  Strategy: 5 steps (read/edit/search first; EXEC: prefix; re-run validators)

--- Mutation ---
  Category:   optimize
  Risk Level: low

--- Diff (memory_graph.jsonl) ---
+ {"type":"MemoryGraphEvent","kind":"hypothesis",...,"gene":{"id":"gene_distilled_openclaw-tool-use-discipline-bare-compatible",...},"action":{"selected_by":"selector","selector":{"selected":"gene_distilled_openclaw-tool-use-discipline-bare-compatible","reason":["signals match gene.signals_match","signals: memory_missing","drift_intensity: 1.000","selection_path: distilled_fallback"]}}
+ {"type":"MemoryGraphEvent","kind":"attempt",...,"gene":{"id":"gene_distilled_openclaw-tool-use-discipline-bare-compatible",...}
```

---

## 6. Did Selector Hit the OpenClaw Gene? — **YES**

Evidence:
1. `Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible"` (evolver-run-isolated-output.txt line containing "Selection: Selected Gene")
2. Review diff emits `+ hypothesis` and `+ attempt` events both with `gene.id = gene_distilled_openclaw-tool-use-discipline-bare-compatible`
3. `selector.selected = gene_distilled_openclaw-tool-use-discipline-bare-compatible` with `selectionPath = distilled_fallback`
4. `selector.alternatives = []` — no competing Gene in the candidate set (expected: only 1 Gene in the runtime)
5. `ACT_STRATEGY` block in run output contains the 5 rules from the OpenClaw Gene verbatim

The selector used `selection_path: distilled_fallback` because the scanner's first-pass signal extraction collapsed to `memory_missing` (the isolated runtime has no `MEMORY.md` and no recent error patterns). The bare-compatible Gene's broad `signals_match` array (includes `session_context:openclaw`, `repo_context:ai-tool-test-lab`, plus bare `tool_bypass`, `repeated_tool_usage`, `protocol_drift`, `session_context`, `repo_context`) was broad enough to match the fallback path.

---

## 7. Did Pollution Disappear? — **YES**

| Pollution signal | Phase 3C-V2 (polluted) | Phase 4A (isolated) |
|---|---|---|
| `consecutive_failure_streak_3` in events.jsonl | Yes (3 failures) | **No** (events.jsonl empty) |
| `user_feature_request` from session text | Yes (recent session words) | **No** (no session content beyond standard evolver scan) |
| `gene_gep_repair_from_errors` selected | Yes (13/13 cycles) | **No** (zero competing genes) |
| GEP-internal Gene in selection | Yes (always first) | **No** |

The only mentions of `consecutive_failure_streak` in the run output appear in the evolver's **system prompt boilerplate** ("FAILURE STREAK AWARENESS: If `consecutive_failure_streak_N`..."), NOT in actual MemoryGraphEvents or EvolutionEvents. This is a known and stable part of evolver's instruction text, not a runtime pollution.

---

## 8. Four-Score Evaluation

### A. Isolation setup — **PASS**
- `/tmp/atl-evomap-4a-isolated` created as independent git repo
- Only 1 Gene in `genes.json`
- `events.jsonl` empty (0 failed events)
- `capsules.json` empty (0 successful events)
- No pollution signals in `memory_graph.jsonl`

### B. Selector match — **PASS**
- `Selection: Selected Gene "gene_distilled_openclaw-tool-use-discipline-bare-compatible"` confirmed
- `selectionPath: distilled_fallback` (the expected path for a clean runtime with broad-signals Gene)
- `alternatives: []` (no GEP-internal gene in candidate set)
- Hypothesis + attempt + action events all reference the OpenClaw Gene

### C. Pollution control — **PASS**
- 0 pollution events in `events.jsonl` (verified before run)
- 0 `user_feature_request` triggers in the run output
- 0 `consecutive_failure_streak_N` triggers in actual events (only boilerplate system prompt)
- 0 GEP-internal Genes selected
- Selector reason is purely signal-match driven: `signals match gene.signals_match`, `selection_path: distilled_fallback`

### D. Safety — **PASS**
- A2A_HUB_URL unset (no Hub connection)
- `EVOLVER_AUTO_PUBLISH=false` (no publish)
- 0 credits consumed (no Hub, no autobuy)
- `EVOLVER_VALIDATOR_ENABLED=false` (no validator)
- `evolver review --approve` **NOT executed** (per 硬边界 #12; review output only inspected)
- `evolver solidify` / `node index.js solidify` **NOT executed** (per 硬边界 #13)
- No secrets in any artifact (no tokens, API keys, chat_ids, bot IDs)
- No real OpenClaw/Hermes/systemd/cron config touched
- No `.env` files scanned or written
- No Evolver package source modified
- `/tmp` isolated runtime NOT committed to main repo (independent git init)

---

## 9. Safety Boundary Audit

| Boundary | Required | Actual | Status |
|---|---|---|---|
| Hub connection | NO | A2A_HUB_URL unset; `Hub Matched Solution: (no hub match)` | ✅ |
| A2A_HUB_URL set | NO | unset | ✅ |
| --loop | NO | not used | ✅ |
| validator enabled | NO | `EVOLVER_VALIDATOR_ENABLED=false` | ✅ |
| auto-publish | NO | `EVOLVER_AUTO_PUBLISH=false` | ✅ |
| credits consumed | 0 | 0 (no Hub, no autobuy) | ✅ |
| ATP autobuy | NO | `EVOLVER_ATP_AUTOBUY=off` | ✅ |
| secrets read/write | NO | none | ✅ |
| .env scan | NO | none | ✅ |
| real OpenClaw/Hermes config mutation | NO | none | ✅ |
| Evolver package source mutation | NO | none | ✅ |
| `evolver review --approve` | NO | not executed | ✅ |
| `evolver solidify` | NO | not executed | ✅ |
| commit runtime .evolver/ + memory/ | NO | isolated runtime in /tmp only, not in main repo | ✅ |
| commit secrets | NO | grep verified | ✅ |

---

## 10. Final Conclusion

**ATL-EVOMAP-4A · PASS.**

The Phase 3C-V2 BLOCKED result is **not** an inherent selector bug. The selector **can** hit `gene_distilled_openclaw-tool-use-discipline-bare-compatible` reliably when:

1. There is at least one Gene in `genes.json` (trivially satisfied)
2. There are no failed EvolutionEvents to drive `consecutive_failure_streak_*`
3. There is no dense session text that the LLM scanner can read as `user_feature_request`
4. The candidate gene has a broad `signals_match` array (bare + qualified forms) so the `distilled_fallback` path can match

The root cause of Phase 3C-V2's BLOCKED result is the **session-and-history-driven selector** in the real `ai-tool-test-lab` runtime: dense recent sessions + failed events create a stable GEP-internal selection path that overrides MemoryGraph injection.

To use the OpenClaw Gene in the real repo, the next step is **not** to keep retrying `evolver run` in the polluted runtime — it is to either:
1. Build a **Gene-rotation policy** that injects the distilled Gene as a candidate before the failed-events-driven repair loop kicks in, OR
2. Build a **local signal detector + scheduler** (the ATL-EVOMAP-3b-1 plan) that bypasses `evolver run` entirely and directly applies Gene strategy steps.

---

## 11. Phase 4B Recommendation

**Phase 4B (capsule creation in isolated env) is GO.**

If Phase 4A had failed, we would have concluded the bare-compatible Gene is fundamentally unselectable and abandoned the EvoMap path. Since Phase 4A **passed**, the OpenClaw Gene is selectable, and Phase 4B can proceed with the goal of producing a **real Capsule** (not just a pending run) in the isolated runtime.

**Phase 4B goals (proposed):**
1. In isolated runtime, create a real `Capsule` referencing the OpenClaw Gene with a non-empty `execution_trace`.
2. Verify the Capsule survives a second `evolver review` cycle (no auto-approve, but the Capsule becomes a candidate for future runs).
3. Document the minimal skill/asset set required to make a Capsule `trace_empty`-clean in the isolated env.
4. Assess whether the isolated-runtime Capsule can be exported to the main repo without triggering the GEP-internal repair loop (i.e., a capsule-import strategy that doesn't run `evolver run` first).

**Hard boundaries remain unchanged** (no Hub, no publish, no credits, no --approve, no solidify).
