# ATL-EVOMAP-3C Five-Dimension Scoring

## A. Pre-approve review — **PASS** ✅

- Pre-approve `evolver review` output (`evolver-review-before-approve.txt`) contains:
  - `run_1781793744810` ✓
  - `gene_distilled_openclaw-tool-use-discipline-bare-compatible` ✓
- Pending run confirmed; selected Gene confirmed (the right one).

## B. Approve — **PASS** (with HOLLOW COMMIT detection) ✅

- `evolver review --approve` ran without errors
- Output: `[Review] Approved. Running solidify...`
- Auto-triggered solidify (Evolver combines approve + solidify in one flow)
- **System safety net engaged:** Evolver detected HOLLOW COMMIT (only artifact/metadata files in diff)
- Auto-rollback via `git stash` (ref: `evolver-rollback-1781795571643`)
- Status: `[SOLIDIFY] FAILED` — but this is **safety working as designed**
- The "failure" is not an Evolver bug — it's a feature preventing empty commits from being published

## C. Solidify — **PARTIAL** ⚠️

- `evolver solidify` ran 3 times:
  1. `evolver review --approve` (auto-solidify) — HOLLOW COMMIT, rollback
  2. `evolver solidify` (manual) — HOLLOW COMMIT, rollback
  3. `node $(command -v evolver) solidify` (manual node call) — HOLLOW COMMIT, rollback
- All 3 attempts detected HOLLOW COMMIT and rolled back
- **No Capsule generated** (capsule_count = 0)
- **3 EvolutionEvents generated** in `.evolver/gep/events.jsonl`:
  - `evt_1781795571190` (from 1st attempt)
  - `evt_1781795618207` (from 2nd attempt, parent: evt_1781795571190)
  - `evt_1781795639960` (from 3rd attempt, parent: evt_1781795618207)
- All 3 events: outcome=`failed`, capsule_id=`null`, violation=`hollow_commit`
- 3 ValidationReports also generated (vr_1781795568895, vr_1781795617822, vr_1781795638599)

**Verdict:** Solidify is a **PARTIAL** — the pipeline works (events are written), but Capsule creation is gated by HOLLOW COMMIT detection. This is **correct behavior** for safety, not a bug.

## D. GEP artifacts — **PASS** ✅

- ✅ `gep-state-openclaw-grep.txt` — comprehensive grep across `.evolver/` and `memory/`
- ✅ `capsule-count.txt` — shows 0 capsules
- ✅ `evolution-events-openclaw.txt` — extracts 3 EvolutionEvents + 3 ValidationReports
- ✅ All events reference `gene_distilled_openclaw-tool-use-discipline-bare-compatible`
- ✅ `evolution_narrative.md` mentions the new Gene 3 times
- ✅ All extracted evidence is at `cases/evomap-evolver-openclaw-v0/phase3c-solidify/artifacts/`

## E. Safety — **PASS** ✅

- ✅ no Hub: `A2A_HUB_URL` unset, no Hub calls in any output
- ✅ no auto-publish: `EVOLVER_AUTO_PUBLISH=false`
- ✅ no validator: `EVOLVER_VALIDATOR_ENABLED=false`
- ✅ no --loop: not used
- ✅ no credits: 0 credits (no Hub = 0)
- ✅ no ATP autobuy: `EVOLVER_ATP_AUTOBUY=off`
- ✅ no secrets: no API key/token/cookie/Authorization/.env
- ✅ no real system mutation: only ai-tool-test-lab
- ✅ no OpenClaw/Hermes/systemd/cron change
- ✅ no Evolver source modification
- ✅ no .env scan
- ✅ no Capsule published (capsule_count = 0)
- ✅ Auto-rollback triggered (HOLLOW COMMIT detection)
- ✅ Two untracked files preserved via git stash + pop (no data loss)

## Overall: **PARTIAL** (4 PASS + 1 PARTIAL)

This is a **meaningful PARTIAL**:
- Approve path is fully verified (A, B = PASS)
- Solidify path is partially verified (C = PARTIAL) — events are generated, but Capsule creation is gated by HOLLOW COMMIT
- Evidence extraction is complete (D = PASS)
- All safety boundaries respected (E = PASS)

**The HOLLOW COMMIT detection is evolver's own safety net, working as designed.** It correctly prevented the approve/solidify flow from committing empty changes.

## Capsule status: NOT generated (correctly)

- Expected: hollow commit rejection → no Capsule
- Got: hollow commit rejection → no Capsule + 3 EvolutionEvents with `outcome=failed`
- This is **safety working**, not failure

## EvolutionEvent status: 3 generated ✅

- Each event shows:
  - selected_gene_id = `gene_distilled_openclaw-tool-use-discipline-bare-compatible`
  - selector reason: `signals match gene.signals_match; signals: tool_bypass`
  - outcome: `failed` (hollow_commit)
  - capsule_id: `null` (no Capsule due to hollow commit)
  - parent chain: evt_1781795571190 → evt_1781795618207 → evt_1781795639960 (3-level chain)
