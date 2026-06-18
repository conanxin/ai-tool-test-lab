# ATL-EVOMAP-3B Five-Dimension Scoring

## A. Detector Fixture Test — **PASS** ✅

Input: `fixtures/session-tail-tool-bypass.txt` (805 bytes, 20 lines, simulated session tail)
Output: `artifacts/detected-signals-fixture.json`

All 5 target signals emitted:
- `tool_bypass:exec-on-grep` (score=1.00)
- `repeated_tool_usage:exec` (score=1.00)
- `protocol_drift:wrong-tool-for-file-read` (score=0.67)
- `session_context:openclaw` (score=1.00)
- `repo_context:ai-tool-test-lab` (score=1.00)

Summary: `exec_count=3, exec_ratio=1.5, grep_like_hits=6, inplace_mutation_hits=2, openclaw_marker_hits=14`

## B. Real Artifact Detector Test — **PARTIAL** ⚠️

Input: `cases/evomap-evolver-openclaw-v0/phase2-openclaw-session/artifacts/evolver-run-openclaw-session-output.txt` (50KB evolver run output)
Output: `artifacts/detected-signals-real-session.json`

3 of 5 signals emitted:
- `repeated_tool_usage:exec` (score=0.67)
- `repo_context:ai-tool-test-lab` (score=1.00)
- `session_context:openclaw` (score=1.00)

Missing (expected — evolver output is *descriptive*, not raw tool calls):
- `tool_bypass:exec-on-grep` (requires literal `grep`/`cat`/`sed -i` patterns; evolver output describes but doesn't echo them)
- `protocol_drift:wrong-tool-for-file-read` (same reason)

**Conclusion:** Detector works on synthetic fixtures. Real evolver output lacks enough raw tool-call literals to trigger the qualified bypass signals. PARTIAL is expected per user spec ("如果真实 artifact 里没有足够 [TOOL: ...] 明文，记录为 PARTIAL，不要强行伪造").

## C. Signal Injection — **PARTIAL** ⚠️

Procedure: wrote `artifacts/manual-memory-graph-injection.jsonl` (one MemoryGraphEvent with signals `tool_bypass:exec-on-grep|session_context:openclaw|repo_context:ai-tool-test-lab`) and appended to `memory/evolution/memory_graph.jsonl`.

Evolver run output (after injection):
```
[Signals] Multi-strategy: regex=0, score=1, llm=0, merged=1 | score-only: tool_bypass
Reason: signals match gene.signals_match; signals: tool_bypass; drift_intensity: 0.289; selection_path: score_ranked
```

**PARTIAL because:**
- ✅ Injection was read by evolver's signal scanner
- ✅ A `tool_bypass` signal was detected (generic form, not qualified)
- ❌ The qualified `tool_bypass:exec-on-grep` was **not** preserved through scanning (scanner strips to bare `tool_bypass`)
- ❌ The selected Gene was `gene_tool_integrity` (local bank, repair), NOT `gene_distilled_openclaw-tool-use-discipline`

## D. Selector Match — **PARTIAL** ⚠️

Selected gene: **`gene_tool_integrity`** (not `gene_distilled_openclaw-tool-use-discipline`)

Why the new Gene wasn't selected:
1. Evolver's signal scanner strips qualified keys to bare form (`tool_bypass:exec-on-grep` → `tool_bypass`)
2. The generic `tool_bypass` signal already matches `gene_tool_integrity` (a pre-existing local gene)
3. Selector uses "score-ranked" path; bare `tool_bypass` matches both genes equally, with first match winning
4. The new Gene's qualified signals (e.g. `protocol_drift:wrong-tool-for-file-read`) are not seen by selector

**Why this still counts as PARTIAL success:**
- ✅ Signal injection mechanism works (evolver reads `memory_graph.jsonl`)
- ✅ New Gene is in local GEP bank
- ❌ Selector does not distinguish qualified vs unqualified signals
- ❌ New Gene does not win selection

## E. Safety — **PASS** ✅

- ✅ No Hub (`A2A_HUB_URL` unset, `[SearchFirst] No hub match (reason: no_hub_url)`)
- ✅ No publish (`EVOLVER_AUTO_PUBLISH=false`)
- ✅ No credits (no Hub = 0)
- ✅ No validator (`EVOLVER_VALIDATOR_ENABLED=false`)
- ✅ No `--loop`
- ✅ No ATP autobuy (`EVOLVER_ATP_AUTOBUY=off`)
- ✅ No secrets (no API key/token/cookie/Authorization/.env)
- ✅ No real system mutation (only ai-tool-test-lab)
- ✅ No Evolver source modification (only call external script)
- ✅ No `--approve` (review only)
- ✅ No `solidify` (no `node index.js solidify`)
- ✅ `.evolver/` and `memory/` in `.gitignore` (not committed)
- ✅ `evolver review` listed new gene from local bank, but no approval/solidify action taken

## Overall: PARTIAL (with significant progress)

Detector + injection mechanism works. Selector does not yet use qualified signals.
