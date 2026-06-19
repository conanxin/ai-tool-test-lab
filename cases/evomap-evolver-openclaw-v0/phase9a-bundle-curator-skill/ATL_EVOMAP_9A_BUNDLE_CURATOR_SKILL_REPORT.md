# Phase 9A — Bundle Curator Skill · Report

> Status: **PASS** · stdlib-only · offline-only · human-reviewed
> Phase: **ATL-EVOMAP-9A**
> Base commit: `a56e756` (post-ATL-EVOMAP-8A nightly validation loop asset)
> Kit: OpenClaw / Hermes Local Evolution Kit
> Visibility: `private`
> Generator: `scripts/evomap_curate_bundle.py` v0.1.0
> Generated bundle visibility: `private`

## 1. Goal

Ship a **Bundle Curator Skill** for the OpenClaw / Hermes Local
Evolution Kit — a small, predictable, stdlib-only Python tool that
converts a hand-written *curator spec* JSON into a portable bundle
draft and a README draft, hands the draft to the existing
`evomap_inspect_bundle.py` / `evomap_validate_bundle.py` /
`evomap_apply_bundle.py` tool chain, and stops there. No Hub, no
publish, no credits, no approve, no solidify, no AI API, no network,
no real test runners.

## 2. Phase 8A unlock condition

Phase 8A shipped the nightly validation loop asset that validates
all 6 prior phase validators + 4 canonical bundles + secret scan +
git hygiene + 22 hard-boundary flags. With Phase 8A green at commit
`a56e756`, the kit is in a stable state to receive a new
*generator* tool whose outputs can be validated by the existing
inspect / validate / apply pipeline.

Phase 8A final result:

- 9/9 blocking checks PASS
- 6/6 phase validators ALL CHECKS PASSED
- 4/4 bundle inspect PASS, 4/4 bundle validate PASS
- secret_scan hits = 0, allowed_timestamp_hits = 21 (Unix ms timestamps;
  explained as artifacts of evolver run/review events)
- git_hygiene PASS
- 22/22 hard_boundaries all true

## 3. Curator spec schema

Schema version `atl-evomap-curator-spec-v0.1`. The reference schema
example is at
`templates/curator-spec.schema.example.json`. The runnable sample is
at `specs/sample-safe-bundle.curator-spec.json`.

Required fields:

| Path | Type | Required value |
|--|--|--|
| `schema_version` | string | `"atl-evomap-curator-spec-v0.1"` |
| `bundle.schema_version` | string | `"atl-evomap-portable-bundle-v0.1"` |
| `bundle.source_phase` | string | e.g. `"ATL-EVOMAP-9A"` |
| `bundle.target_gene_id` | string | must equal `gene.id` |
| `bundle.target_capsule_id` | string | must equal `capsule.id` |
| `bundle.visibility` | string | `"private"` |
| `gene.type` | string | `"Gene"` |
| `gene.id` | string | non-empty, matches `bundle.target_gene_id` |
| `gene.category` | string | non-empty (`repair` / `optimize` / etc.) |
| `gene.signals_match` | list[string] | non-empty, no denylisted tokens |
| `gene.strategy` | list[string] | non-empty |
| `gene.summary` | string | non-empty |
| `capsule.schema_version` | string | `"1.6.0"` |
| `capsule.type` | string | `"Capsule"` |
| `capsule.id` | string | matches `bundle.target_capsule_id` |
| `capsule.gene` | string | matches `gene.id` |
| `capsule.status` | string | e.g. `"success"` |
| `capsule.confidence` | number | `0 <= x <= 1` |
| `capsule.visibility` | string | `"private"` |
| `capsule.source` | string | provenance tag |
| `capsule.trigger` | list[string] | non-empty |
| `capsule.execution_trace` | list[object] | **>= 3** steps |
| `safety.hub` | string | `"disabled"` |
| `safety.publish` | string | `"disabled"` |
| `safety.credits` | number | `0` |
| `safety.visibility` | string | `"private"` |

## 4. `evomap_curate_bundle.py` tool design

- **CLI**: `--spec` (required), `--out-dir` (required),
  `--bundle-name` (optional), `--dry-run`, `--strict`.
- **AST self-check** on startup: parses the curator's own source and
  fails (exit 2) if any non-stdlib import is present. Defense in depth
  to make sure the curator never silently gains a third-party
  dependency.
- **Single-file read scope**: only `--spec` is read. No recursive
  repository scan, no `.env` read, no runtime read.
- **Spec validation**: schema_version, bundle / gene / capsule /
  safety field requirements, ID consistency invariants,
  execution_trace length, safety hard-required values, denylisted
  signal-name scan, secret-pattern scan.
- **Secret redaction**: matches in the result JSON are returned as
  `<first-4>***REDACTED***` so the curator never echoes a secret-like
  substring back to the caller.
- **Output paths**: every output path is resolved and refused if it
  escapes `--out-dir`. The curator never writes to the repo root,
  `.evolver/`, `memory/`, or any tracked directory by default.
- **Visibility**: hard-coded to `private` in every generated artifact's
  `_provenance` / `kit_provenance` block; the spec cannot override.
- **Provenance**: each output JSON carries a `_provenance` (gene /
  capsule) or `kit_provenance` (bundle) block recording the kit,
  phase, base commit, generator, generator version, generated_at,
  visibility, hub / publish / credits / approve / solidify /
  evolver_run / evolver_review flags (all `false` or `not_executed`),
  network_calls_executed, real_test_runners_executed,
  real_cron_installed, systemd_timer_created, env_file_scanned
  (all `false`).

## 5. BUNDLE_CURATOR.SKILL.md

`cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/BUNDLE_CURATOR.SKILL.md`
is the canonical operator-facing description of the skill. It covers:

- Purpose
- When to use (and not to use)
- Inputs
- Outputs (per `--dry-run` and per generation mode)
- Safety boundaries (hard-enforced always + hard-forbidden never)
- Curator spec schema
- Validation sequence (10 ordered checks)
- Refusal conditions (full enumeration)
- Example commands
- Expected result JSON shape
- What the skill does NOT do (10 items)
- Integration with Phase 8A
- Future extensions (ATL-EVOMAP-9B / 9C / 9D)

## 6. Dry-run result

```json
{
  "ok": true,
  "mode": "dry-run",
  "signals_count": 4,
  "execution_trace_steps": 4,
  "secret_hits": [],
  "rejected_signals": [],
  "safety_summary": {
    "hub": "disabled",
    "publish": "disabled",
    "credits": 0,
    "approve": "not_executed",
    "solidify": "not_executed",
    "evolver_run": "not_executed",
    "evolver_review": "not_executed",
    "real_cron_install": "not_executed",
    "systemd_timer_install": "not_executed",
    "network_calls": "not_executed",
    "real_tests": "not_executed",
    "no_env_file_content_scanned": true,
    "stdlib_only": true,
    "visibility": "private"
  }
}
```

The dry-run did not write any file under `--out-dir`. Saved to
`artifacts/curator-dry-run-output.json`.

## 7. Generate result

`--strict` mode generation produced 4 files under
`generated/`:

| File | Size | Purpose |
|--|--|--|
| `sample-safe-bundle.bundle.json` | 5065 bytes | portable bundle (v0.1) |
| `gene-gene_distilled_sample-safe-bundle.json` | 1394 bytes | standalone gene |
| `capsule-capsule_sample_safe_bundle_phase9a.json` | 1658 bytes | standalone capsule |
| `README.generated.md` | 3366 bytes | operator-facing draft README |

Result JSON: `ok=true`, `mode=generated`, `strict=true`,
`signals_count=4`, `execution_trace_steps=4`, `secret_hits=[]`,
`rejected_signals=[]`. Saved to `artifacts/curator-generate-output.json`.

## 8. Inspect / validate result

```bash
python3 scripts/evomap_inspect_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated/sample-safe-bundle.bundle.json
# ok=true, schema_version=atl-evomap-portable-bundle-v0.1,
# gene_id=gene_distilled_sample-safe-bundle,
# capsule_id=capsule_sample_safe_bundle_phase9a

python3 scripts/evomap_validate_bundle.py \
    --bundle cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated/sample-safe-bundle.bundle.json
# ok=true, summary.secret_hits=0, summary.capsule_execution_trace_steps=4,
# summary.capsule_gene_match=true, summary.required_import_files_count=3
```

Both PASS. Saved to
`artifacts/inspect-generated-bundle-output.json` and
`artifacts/validate-generated-bundle-output.json`.

## 9. Apply dry-run result

Isolated target prepared under `/tmp/atl-evomap-9a-curator-target/`
(initialized as a fresh `git init` repo). The apply dry-run reported:

- `ok=true`, `mode=dry-run`
- `plan.signal_injection_mode=generic_plus_domain_from_bundle`
- `plan.generic_signals` (5): `tool_bypass`, `repeated_tool_usage`,
  `protocol_drift`, `session_context`, `repo_context`
- `plan.domain_signals` (4): `sample_failure`, `sample_failure:fixture`,
  `session_context`, `repo_context`
- `plan.domain_signals_rejected=[]`
- `plan.summary.memory_graph_signals_added=9` (5 generic + 4 domain)
- `plan.summary.new_gene_count=1`, `new_capsule_count=1`
- `plan.summary.memory_graph_domain_rejected=0`

The dry-run did not touch the target filesystem. Saved to
`artifacts/apply-generated-bundle-dry-run-output.json`.

## 10. Apply `--yes` result (isolated `/tmp` only)

With explicit `--yes`, the apply tool wrote:

- `/tmp/.../.evolver/gep/genes.json` (1127 bytes)
- `/tmp/.../.evolver/gep/capsules.json` (1466 bytes)
- `/tmp/.../.evolver/gep/events.jsonl` (reset, 0 bytes)
- `/tmp/.../.evolver/gep/failed_capsules.json` (`[]\n`, 3 bytes)
- `/tmp/.../.evolver/gep/candidates.jsonl` (reset, 0 bytes)
- `/tmp/.../memory/evolution/memory_graph.jsonl` (2741 bytes,
  9 lines)

Result: `ok=true`, `mode=applied`, `writes_executed=6`, `errors=[]`.
Saved to `artifacts/apply-generated-bundle-yes-output.json`.

Target post-apply summary (`apply-generated-target-summary.json`):

- `gene_count=1`, `capsule_count=1`
- `memory_graph_lines=9`
- `distinct_signal_count=7`
  (`tool_bypass`, `repeated_tool_usage`, `protocol_drift`,
  `session_context`, `repo_context`, `sample_failure`,
  `sample_failure:fixture`)
- `gene_ids=["gene_distilled_sample-safe-bundle"]`
- `capsule_ids=["capsule_sample_safe_bundle_phase9a"]`

## 11. Unsafe-spec self-tests

Two negative tests were created in `/tmp` (not committed):

### A. `curator-selftest-unsafe-secret-output.json`

Spec at `/tmp/evomap-curator-unsafe-secret.curator-spec.json` with
`api_key:omitted` injected into `gene.signals_match`.

- `ok=false`, `mode=rejected`, exit code `1`
- `rejected_signals=["api_key:omitted"]`
- `errors=["denylisted signal name(s) detected in gene.signals_match or
  capsule.trigger: 'api_key:omitted'"]`
- `secret_hits=[]` (the offending string was caught by the *name*
  denylist, not by the secret-pattern scan — neither path echoes a
  raw secret back)

### B. `curator-selftest-unsafe-id-output.json`

Spec at `/tmp/evomap-curator-unsafe-id.curator-spec.json` with
`capsule.gene` rewritten to `gene_distilled_DIFFERENT-id`.

- `ok=false`, `mode=rejected`, exit code `1`
- `rejected_signals=[]`
- `errors=["capsule.gene ('gene_distilled_DIFFERENT-id') must equal
  gene.id ('gene_distilled_sample-safe-bundle')"]`

In both cases the curator wrote **nothing** under `--out-dir`. The
unsafe specs themselves live only in `/tmp` and were never committed
to the repository.

## 12. Safety boundaries — actual state

| Boundary | State |
|--|--|
| Connected to EvoMap Hub | **NO** |
| Set `A2A_HUB_URL` | **NO** |
| Ran `evolver --loop` / `evolver run` / `evolver review` / `evolver review --approve` / `evolver solidify` | **NO** |
| Auto-published any artifact | **NO** |
| Consumed credits | **NO** |
| ATP autobuy | **NO** |
| Called OpenAI / Codex / GitHub Copilot / any AI API | **NO** |
| Called Telegram API | **NO** |
| Called `curl` / `wget` / `httpx` / `requests` / `urllib` | **NO** |
| Ran real test runners (`pytest`, `npm test`, `cargo test`, `go test`, `mvn test`) | **NO** |
| Read `.env` content | **NO** |
| Read/wrote real API keys, tokens, cookies, Authorization headers, private keys | **NO** |
| Modified real OpenClaw / Hermes / systemd / cron configuration | **NO** |
| Installed cron / created systemd timer | **NO** |
| Modified Evolver package source | **NO** |
| Tracked `runtime/.evolver/` or `runtime/memory/` in git | **NO** |
| Used a third-party Python library | **NO** (AST self-check enforces) |

22 hard-boundary flags all `true` in the curator's `safety_summary`
block (see generated bundle's `kit_provenance`).

## 13. Final conclusion

Phase 9A delivers a **Bundle Curator Skill** that:

- is stdlib-only (AST self-check enforces),
- reads only the operator-supplied `--spec` file (no recursive scan,
  no `.env`, no runtime read),
- refuses specs that violate the safety contract (denylisted signal
  names + secret patterns + ID invariants + execution_trace length +
  visibility / hub / publish / credits rules),
- produces a portable bundle draft that already passes
  `evomap_inspect_bundle.py` and `evomap_validate_bundle.py`,
- is safe to apply dry-run + apply `--yes` to an **isolated** `/tmp`
  target (target was a fresh `git init` repo),
- ships two negative self-tests (denylist hit + ID mismatch) that both
  exit `1` with `ok=false`,
- ships a 22-check validator
  (`scripts/validate_evomap_phase9a_bundle_curator_skill.py`) that
  verifies all the above plus regression of all 7 prior phase
  validators.

Status: **BUNDLE_CURATOR_SKILL_PASS**.

## 14. Next steps (NOT executed in this phase)

- **ATL-EVOMAP-9B** · Curator-to-nightly integration: extend the
  Phase 8A nightly runner manifest to include curator-generated
  bundles in the 4-bundle inspect / validate cycle. Out of scope
  here.
- **ATL-EVOMAP-9C** · Domain-specific curator specs: ship curated
  specs for browser-control, Codex-only, Hermes-only domains. Out
  of scope.
- **ATL-EVOMAP-9D** · Curator-driven apply-to-canary: a guarded
  workflow that, on operator approval, applies curator-generated
  bundles to a canary runtime and reports back. Out of scope.
- **ATL-EVOMAP-8B** · Operator-led real-cron install for the
  Phase 8A nightly runner. Out of scope.
- **browser-control bundle** · a new canonical portable bundle in
  the same shape as the 4 existing ones, suitable for the kit's
  browser-automation path. Out of scope.

All of the above are documented as future possibilities; they are
**not** part of Phase 9A deliverables and require their own operator
authorization phases.