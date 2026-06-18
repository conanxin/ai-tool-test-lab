# ATL-EVOMAP-5 · Local Evolution Kit · Report

**Case:** evomap-evolver-openclaw-v0
**Phase:** 5 · Local Evolution Kit
**Status:** **PASS** — Bundle, 3 tools, 3 templates, 4-step recipe all delivered and tested. All 16 hard boundaries preserved.

**Baseline commit:** `f7897da` (Phase 4C PASS)
**Target for apply test:** `/tmp/atl-evomap-phase5-apply-target` (NOT in main repo, NOT GitHub-tracked)

---

## 1. Goal

Productize the local-only Gene + Capsule pathway proven in Phases 4A/4B/4C as a **reusable, stdlib-only toolset** for future OpenClaw / Hermes / Codex local evolution assets. This is **not** an exploration of evolver internals; it's a delivery of:

1. A canonical portable bundle (Gene + Capsule + execution_trace)
2. Three Python stdlib tools (inspect, validate, apply)
3. Three templates for new bundles
4. A 4-step usage recipe
5. Self-test artifacts proving all of the above work

---

## 2. Phase 4C Unlocking Condition

Phase 4C proved a portable bundle can be **reused across two independent isolated runtimes** with the same identity preserved. The key signal — `capsule trigger matches signals` in the selector reason — confirmed the evolver in both sessions was using the imported Capsule as a usable prior asset.

That unlocks Phase 5's central question:

> "Can this proven pathway be **productized** as a toolset that anyone can use to create / validate / apply portable bundles, **without** ever touching the EvoMap Hub, **without** publishing, and **without** running `evolver review --approve` or `evolver solidify`?"

If yes: a **durable local evolution kit** exists that can be referenced for future OpenClaw / Hermes / Codex evolution assets, with all hard boundaries enforced at the tool level.

If no: the proven pathway is too fragile to productize, and we should stop here.

---

## 3. Kit Composition

```
phase5-local-evolution-kit/
├── README.md                                          (10.4 KB)
├── bundle/
│   └── openclaw-tool-use-discipline.bundle.json       (5458 bytes — canonical Phase 4C bundle)
├── tools/
│   ├── evomap_inspect_bundle.py                        (2674 bytes)
│   ├── evomap_validate_bundle.py                       (6817 bytes)
│   └── evomap_apply_bundle.py                          (8869 bytes)
├── templates/
│   ├── GENE_TEMPLATE.json
│   ├── CAPSULE_TEMPLATE.json
│   └── MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl
├── artifacts/                                          (test outputs)
│   ├── inspect-bundle-output.json
│   ├── validate-bundle-output.json
│   ├── apply-bundle-dry-run-output.json
│   ├── apply-bundle-yes-output.json
│   ├── apply-target-files.txt
│   └── apply-target-summary.json
└── ATL_EVOMAP_5_LOCAL_EVOLUTION_KIT_REPORT.md         (this file)
```

Plus **three top-level scripts** in `scripts/` (the canonical installation; the `tools/` copies are for self-contained kit distribution).

---

## 4. Bundle Schema

`atl-evomap-portable-bundle-v0.1` — see `bundle/openclaw-tool-use-discipline.bundle.json`.

Key fields:

- `schema_version`: `atl-evomap-portable-bundle-v0.1`
- `source_phase`: `ATL-EVOMAP-4B` (provenance chain)
- `source_session`: `/tmp/atl-evomap-4a-isolated` (original isolated runtime)
- `gene`: full Gene JSON (id, category, signals_match, strategy, constraints, summary)
- `capsule`: full Capsule JSON (id, trigger, gene, status, confidence, execution_trace, source, visibility)
- `execution_trace`: top-level summary from the build fixture (ok=true, exec_count, read_count, etc.)
- `safety`: hub disabled, publish disabled, credits 0, visibility private, no failed events, no pollution signals, approve/solidify not executed
- `import_contract`: 3 required + 3 optional files
- `kit_provenance`: links to Phase 4C validation record (`f7897da`, both sessions PASS, score_ranked path)

---

## 5. Tool Specs

### `evomap_inspect_bundle.py` (2674 bytes, stdlib only)

- **Usage:** `python3 scripts/evomap_inspect_bundle.py --bundle <bundle.json>`
- **Output:** JSON summary with `ok: true`, gene id, capsule id, execution_trace steps, stages, safety record, kit_provenance
- **Behavior:** Read-only. No network. No recursion into repo. Only reads the single bundle file.
- **Exit code:** 0 if ok, 1 if bundle missing or invalid JSON.

### `evomap_validate_bundle.py` (6817 bytes, stdlib only)

- **Usage:** `python3 scripts/evomap_validate_bundle.py --bundle <bundle.json>`
- **Output:** JSON with `ok: true|false`, list of 12 checks (name, ok, detail), `failures` list, summary block
- **Behavior:** Read-only. Runs secret scan over the entire bundle (recursive over nested JSON values).
- **Checks (12):**
  1. bundle file exists
  2. bundle is valid JSON
  3. bundle has schema_version
  4. bundle has 'gene' field (dict)
  5. bundle has 'capsule' field (dict)
  6. bundle has 'execution_trace' field
  7. gene.id present and non-empty
  8. capsule.id present and non-empty
  9. capsule.gene (or gene_id) == gene.id
  10. capsule.execution_trace is non-empty list
  11. import_contract.required_files contains 3 required paths (`.evolver/gep/genes.json`, `.evolver/gep/capsules.json`, `memory/evolution/memory_graph.jsonl`)
  12. no secret patterns (api_key, slack_token, github_pat, google_api_key, jwt, bearer, telegram_bot, private_key, etc.)
- **Exit code:** 0 if all PASS, 1 if any FAIL.

### `evomap_apply_bundle.py` (8869 bytes, stdlib only)

- **Usage:**
  - `python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path>` (defaults to dry-run)
  - `python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --dry-run` (explicit dry-run)
  - `python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --yes` (real write)
- **Behavior:**
  - Defaults to `--dry-run` if neither `--dry-run` nor `--yes` is given
  - Dry-run: prints planned writes, does NOT touch the filesystem
  - `--yes`: writes 3 required + 3 optional files
  - **Idempotent** on gene/capsule (id-based dedup, never duplicates)
  - **Append-only** on memory_graph (signals accumulate over time)
  - Warns (but allows) if target is not a git repo
  - Refuses to write if target doesn't exist as a directory
- **Writes (6 files):**
  - `<target>/.evolver/gep/genes.json` (overwrite with merged gene list)
  - `<target>/.evolver/gep/capsules.json` (overwrite with merged capsule list)
  - `<target>/memory/evolution/memory_graph.jsonl` (append 5 clean bare signals)
  - `<target>/.evolver/gep/events.jsonl` (reset to empty)
  - `<target>/.evolver/gep/failed_capsules.json` (reset to `[]`)
  - `<target>/.evolver/gep/candidates.jsonl` (reset to empty)
- **Hard boundaries enforced:**
  - Does NOT contact the Hub
  - Does NOT publish
  - Does NOT consume credits
  - Does NOT run `evolver run` / `evolver review`
  - Does NOT execute `evolver review --approve` or `evolver solidify`
  - Does NOT read/write secrets (the bundle was pre-validated)
  - Does NOT scan `.env`
  - Does NOT touch real config outside the target runtime

---

## 6. Dry-Run Test Result

```
$ python3 scripts/evomap_apply_bundle.py --bundle ... --target-runtime /tmp/atl-evomap-phase5-apply-target --dry-run
```

Output:
```json
{
  "ok": true,
  "mode": "dry-run",
  "plan": {
    "target": "/tmp/atl-evomap-phase5-apply-target",
    "is_git_repo": true,
    "gene_id": "gene_distilled_openclaw-tool-use-discipline-bare-compatible",
    "capsule_id": "capsule_openclaw_tool_use_discipline_phase4b",
    "writes": { ... 6 planned writes ... },
    "summary": {
      "existing_gene_count": 0,
      "existing_capsule_count": 0,
      "new_gene_count": 1,
      "new_capsule_count": 1,
      "memory_graph_signals_added": 5
    }
  }
}
```

**Verified:** After dry-run, `find /tmp/atl-evomap-phase5-apply-target -type f -not -path "*/.git/*"` returned **empty** — no files written. Dry-run is **truly non-destructive**.

---

## 7. Apply --yes Test Result

```
$ python3 scripts/evomap_apply_bundle.py --bundle ... --target-runtime /tmp/atl-evomap-phase5-apply-target --yes
```

Output:
```json
{
  "ok": true,
  "mode": "applied",
  "plan_summary": {
    "existing_gene_count": 0,
    "existing_capsule_count": 0,
    "new_gene_count": 1,
    "new_capsule_count": 1,
    "memory_graph_signals_added": 5
  },
  "log": {
    "writes_executed": [ ... 6 successful writes ... ],
    "errors": []
  }
}
```

### Target after apply --yes

```
/tmp/atl-evomap-phase5-apply-target/
├── .evolver/gep/
│   ├── genes.json              ← 1 gene
│   ├── capsules.json           ← 1 capsule
│   ├── events.jsonl            ← empty
│   ├── failed_capsules.json    ← []
│   └── candidates.jsonl        ← empty
└── memory/evolution/
    └── memory_graph.jsonl      ← 5 clean bare signals
```

### Target summary (apply-target-summary.json)

```json
{
  "gene_count": 1,
  "capsule_count": 1,
  "memory_graph_lines": 5,
  "gene_ids": ["gene_distilled_openclaw-tool-use-discipline-bare-compatible"],
  "capsule_ids": ["capsule_openclaw_tool_use_discipline_phase4b"],
  "memory_graph_signals": [
    "tool_bypass", "repeated_tool_usage", "protocol_drift", "session_context", "repo_context"
  ]
}
```

### Idempotency check (re-apply dry-run)

Re-running dry-run on the now-populated target:
- `existing_genes: 1`, `new_genes: 1` (no duplication)
- `existing_capsules: 1`, `new_capsules: 1` (no duplication)
- `signals_added: 5` (would append 5 more, total 10 if applied)

**Gene and capsule are deduped by id; memory_graph signals are append-only by design.**

---

## 8. Templates

### `templates/GENE_TEMPLATE.json`

```json
{
  "type": "Gene",
  "id": "gene_distilled_<name>-bare-compatible",
  "category": "optimize",
  "signals_match": ["...", "...", "..."],
  "strategy": ["...", "...", "..."],
  "constraints": ["...", "..."],
  "summary": "..."
}
```

### `templates/CAPSULE_TEMPLATE.json`

```json
{
  "schema_version": "1.6.0",
  "type": "Capsule",
  "id": "capsule_<name>_phase<N>",
  "trigger": ["...", "...", "..."],
  "gene": "gene_distilled_<name>-bare-compatible",
  "summary": "...",
  "confidence": 0.8,
  "blast_radius": {"files": 0, "lines": 0},
  "status": "success",
  "outcome": {"status": "success", "score": 0.8},
  "execution_trace": [
    {"step": 1, "stage": "build", "cmd": "...", "exit": 0},
    {"step": 2, "stage": "validate", "cmd": "python3 -m json.tool ...", "exit": 0},
    {"step": 3, "stage": "validate", "cmd": "json_parse_pass", "exit": 0, "validation": "json_parse_pass"},
    {"step": 4, "stage": "canary", "cmd": "safety_check", "exit": 0, "checks": {"no_hub": true, "no_secret": true, "no_env_scan": true, "no_publish": true, "no_approve": true, "no_solidify": true}}
  ],
  "source": "manual_capsule_seed_phase<N>",
  "visibility": "private",
  "created_at": "<ISO-8601>"
}
```

### `templates/MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl`

5 lines, one per clean bare signal (tool_bypass, repeated_tool_usage, protocol_drift, session_context, repo_context), each with `mutation.target: gene:<gene_id>` and `mutation.action: select`.

---

## 9. Safety Boundaries (Audit Table)

| Boundary | Required | Actual | Status |
|---|---|---|---|
| Hub connection | NO | tool does not contact Hub | ✅ |
| A2A_HUB_URL set | NO | tool does not set it | ✅ |
| --loop | NO | tool does not use --loop | ✅ |
| validator enabled | NO | tool does not enable validator | ✅ |
| auto-publish | NO | tool does not publish | ✅ |
| credits consumed | 0 | 0 | ✅ |
| ATP autobuy | NO | tool does not autobuy | ✅ |
| secrets read/write | NO | validator scans and rejects; apply only writes pre-validated bundles | ✅ |
| .env scan | NO | tool does not read .env | ✅ |
| real OpenClaw/Hermes config mutation | NO | only writes target's .evolver/ + memory/evolution/ | ✅ |
| Evolver package source mutation | NO | tool does not touch /usr/lib/node_modules/evolver/ | ✅ |
| `evolver review --approve` | NO | tool does not invoke this | ✅ |
| `evolver solidify` | NO | tool does not invoke this | ✅ |
| commit isolated runtime .evolver/ + memory/ | NO | target is in /tmp, not in main repo | ✅ |
| commit secrets | NO | validator scans; no bundle secrets | ✅ |
| stdlib only | YES | argparse + json + re + sys + pathlib | ✅ |

---

## 10. Final Conclusion

**ATL-EVOMAP-5 · PASS.**

The OpenClaw Local Evolution Kit is **complete and proven**:

1. **Canonical bundle** delivered (`atl-evomap-portable-bundle-v0.1`, 5458 bytes, sourced from Phase 4C PASS)
2. **3 stdlib-only tools** delivered (inspect / validate / apply), all tested on the canonical bundle
3. **3 templates** delivered (Gene / Capsule / MemoryGraph signals)
4. **4-step recipe** documented (validate → inspect → dry-run → apply --yes)
5. **Self-tests passed**:
   - inspect: ok=true (1 gene, 1 capsule, 4-step execution_trace)
   - validate: ok=true (12/12 checks)
   - apply --dry-run: 6 writes planned, 0 files written
   - apply --yes: 6 writes executed, 0 errors
6. **Idempotency verified**: re-apply dedups gene/capsule by id, appends memory signals
7. **All 16 hard boundaries preserved** (no Hub, no publish, no credits, no --approve, no solidify, no real config mutation, no secrets, no source modification, no isolated runtime committed, stdlib only)

The **local-only Gene + Capsule pathway is now productized** as a durable toolset. It can be referenced for future OpenClaw / Hermes / Codex local evolution assets.

---

## 11. Next Steps (Recommendations)

1. **Create additional bundles** for other proven (Gene, Capsule) pairs following the templates:
   - Hermes-specific tool discipline bundle
   - Codex-specific tool discipline bundle
   - OpenClaw protocol-dedup bundle
2. **Add a `bundle-curator` skill** that:
   - Reads an evolver run output (Gene + Capsule) from a known-good isolated env
   - Auto-fills the templates
   - Runs validate + inspect
   - Stores the bundle in `phase5-local-evolution-kit/bundle/`
3. **Extend apply tool** with:
   - `--bundle-list` flag to apply multiple bundles in one call
   - `--from` flag to copy bundle from one runtime to another (vs always from disk)
   - `--prune-events` flag to also clear events.jsonl (currently done by reset)
4. **Add a `bundle-diff` tool** to compare two bundles and show what would change
5. **Add a `bundle-test` tool** that runs `evolver run` + `evolver review` in the target after apply and verifies the selector hit the right gene (this would be the **fully automated** version of the manual step in the current recipe)

All future work should maintain the same 16 hard boundaries.
