# Phase 9A — Bundle Curator Skill (ATL-EVOMAP-9A)

> Status: **DRAFT · stdlib-only · offline-only · human-reviewed**
> Base commit: `a56e756` (post-ATL-EVOMAP-8A nightly validation loop asset)
> Kit: OpenClaw / Hermes Local Evolution Kit
> Visibility: `private`
> Generator: `scripts/evomap_curate_bundle.py` v0.1.0

This directory ships a small, predictable **Bundle Curator Skill** for
the Local Evolution Kit. It is *not* an autonomous agent — it is a
generator that converts a hand-written *curator spec* JSON into a
portable bundle draft, hands the draft to the existing
`evomap_inspect_bundle.py` / `evomap_validate_bundle.py` /
`evomap_apply_bundle.py` tool chain, and stops there. All decisions
about whether to apply a bundle to a real runtime, whether to publish
anything, and whether to approve or solidify remain with the human
operator.

## Why a curator (and not "just write bundles by hand")?

By Phase 8A the kit has 4 canonical portable bundles and a working
apply pipeline. The next natural pain point is *generating* new
portable bundles without:

- manually copying the import-contract stanza every time,
- accidentally emitting a non-private bundle,
- accidentally embedding a secret or a denylisted signal in a bundle
  draft that the apply tool would later refuse anyway,
- writing per-bundle boilerplate that drifts from one bundle to the
  next.

The curator consolidates all of that into a single Python script that
reads one spec file and emits a portable bundle that already
satisfies the canonical schema, the canonical import contract, the
safety contract, and the denylist — and it refuses specs that violate
any of these.

## What ships in this directory

```
phase9a-bundle-curator-skill/
├── README.md                                            ← this file
├── BUNDLE_CURATOR.SKILL.md                              ← canonical skill doc
├── ATL_EVOMAP_9A_BUNDLE_CURATOR_SKILL_REPORT.md         ← full phase report
├── templates/
│   └── curator-spec.schema.example.json                 ← spec schema reference
├── specs/
│   └── sample-safe-bundle.curator-spec.json             ← runnable sample
├── generated/
│   ├── sample-safe-bundle.bundle.json                   ← curator output (bundle)
│   ├── gene-gene_distilled_sample-safe-bundle.json      ← curator output (gene)
│   ├── capsule-capsule_sample_safe_bundle_phase9a.json  ← curator output (capsule)
│   └── README.generated.md                              ← curator output (README)
└── artifacts/
    ├── curator-dry-run-output.json                      ← dry-run result
    ├── curator-generate-output.json                     ← generation result
    ├── inspect-generated-bundle-output.json             ← inspect result
    ├── validate-generated-bundle-output.json            ← validate result
    ├── apply-generated-bundle-dry-run-output.json       ← apply dry-run result
    ├── apply-generated-bundle-yes-output.json           ← apply --yes result
    ├── apply-generated-target-summary.json              ← /tmp target post-apply
    ├── curator-selftest-unsafe-secret-output.json       ← selftest A (denylist hit)
    └── curator-selftest-unsafe-id-output.json           ← selftest B (id mismatch)
```

The curator tool itself lives at
`scripts/evomap_curate_bundle.py` (top-level, alongside the other kit
scripts). The validator for this phase lives at
`scripts/validate_evomap_phase9a_bundle_curator_skill.py`.

## Curator spec schema (TL;DR)

`atl-evomap-curator-spec-v0.1`. Required top-level keys:

| Key | Required value |
|--|--|
| `schema_version` | `"atl-evomap-curator-spec-v0.1"` |
| `bundle.schema_version` | `"atl-evomap-portable-bundle-v0.1"` |
| `bundle.visibility` | `"private"` (hard-required) |
| `gene.type` | `"Gene"` |
| `gene.id` | non-empty, must equal `bundle.target_gene_id` |
| `capsule.id` | non-empty, must equal `bundle.target_capsule_id` |
| `capsule.gene` | must equal `gene.id` |
| `capsule.execution_trace` | list with **>= 3** steps |
| `safety.hub` | `"disabled"` |
| `safety.publish` | `"disabled"` |
| `safety.credits` | `0` |
| `safety.visibility` | `"private"` |

A complete schema example with `_doc_field_requirements` is at
`templates/curator-spec.schema.example.json`. The runnable sample is
at `specs/sample-safe-bundle.curator-spec.json`.

## CLI usage

```bash
# 1. Dry-run validation (no files written)
python3 scripts/evomap_curate_bundle.py \
    --spec cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/specs/sample-safe-bundle.curator-spec.json \
    --out-dir cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated \
    --bundle-name sample-safe-bundle.bundle.json \
    --dry-run

# 2. Generate bundle + gene + capsule + README draft
python3 scripts/evomap_curate_bundle.py \
    --spec cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/specs/sample-safe-bundle.curator-spec.json \
    --out-dir cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated \
    --bundle-name sample-safe-bundle.bundle.json \
    --strict

# 3. Run the existing tool chain on the generated bundle
python3 scripts/evomap_inspect_bundle.py  --bundle <bundle_path>
python3 scripts/evomap_validate_bundle.py --bundle <bundle_path>

# 4. Apply dry-run to an isolated /tmp target
rm -rf /tmp/<isolated-target> && mkdir -p /tmp/<isolated-target> && cd /tmp/<isolated-target> && git init
python3 scripts/evomap_apply_bundle.py \
    --bundle <bundle_path> \
    --inject-signals-from <bundle_path> \
    --target-runtime /tmp/<isolated-target> \
    --dry-run

# 5. (Optional, operator-led) apply --yes to /tmp only
python3 scripts/evomap_apply_bundle.py \
    --bundle <bundle_path> \
    --inject-signals-from <bundle_path> \
    --target-runtime /tmp/<isolated-target> \
    --yes
```

## 9 blocking checks (covered by Phase 8A nightly runner)

The curator is part of the Local Evolution Kit, so the Phase 8A
nightly validation loop already covers its outputs through the
existing 9 blocking checks:

1. `stdlib_only`
2. `no_hub_url_set`
3. `data_cases_json_parse`
4. `data_cases_json_phase_history_has_evomap_8a` — extended in 9A to
   also include `…evomap_9a`.
5. `bundles_inspectable` — covers curator-generated bundle once the
   kit manifest is extended to include it (out of scope for 9A).
6. `bundles_validatable` — same as above.
7. `all_phase_validators_pass` — runs all 7 phase validators (5 / 6A
   / 6B / 6C / 7A / 7B / 8A). Phase 9A adds its own validator but
   does not yet wire it into the nightly runner (intentional — that
   integration is ATL-EVOMAP-9B).
8. `secret_scan_clean` — runs over the whole tracked repo. Curator
   output is shipped under `cases/.../phase9a-.../generated/` so it is
   scanned like every other tracked file.
9. `git_hygiene_no_root_evolver_or_memory` — applies to all phases.

## 6 phase validators + the 9A validator

The kit currently ships 8 validators:

| Validator | Phase |
|--|--|
| `validate_evomap_phase5_local_evolution_kit.py` | Phase 5 |
| `validate_evomap_phase6a_hermes_systemd_bundle.py` | Phase 6A |
| `validate_evomap_phase6b_telegram_router_bundle.py` | Phase 6B |
| `validate_evomap_phase6c_codex_test_failure_bundle.py` | Phase 6C |
| `validate_evomap_phase7a_domain_signal_injection.py` | Phase 7A |
| `validate_evomap_phase7b_cross_bundle_regression.py` | Phase 7B |
| `validate_evomap_phase8a_nightly_validation_loop.py` | Phase 8A |
| `validate_evomap_phase9a_bundle_curator_skill.py` | **Phase 9A** |

All eight must pass for the kit to be considered green. The 9A
validator checks file presence, the curator CLI shape (via
`argparse` AST inspection), spec/schema existence + JSON parse,
dry-run/generate artifact shape, inspect / validate / apply dry-run /
apply --yes outputs, target summary counts, two unsafe-spec
self-tests, and a regression check that all 7 prior validators still
PASS.

## 4 canonical bundles

The kit currently ships 4 canonical portable bundles:

| Bundle | Phase | Category |
|--|--|--|
| `openclaw-tool-use-discipline.bundle.json` | Phase 5 | `optimize` |
| `hermes-systemd-service-recovery.bundle.json` | Phase 6A | `repair` |
| `telegram-message-router-failure.bundle.json` | Phase 6B | `repair` |
| `codex-test-failure-loop.bundle.json` | Phase 6C | `repair` |

The Phase 9A curator-generated sample bundle is shipped at
`generated/sample-safe-bundle.bundle.json`. It is *not* a canonical
bundle (it is a curator smoke artifact). Promoting it to a canonical
bundle position is an explicit operator-led step (out of scope for 9A).

## Secret scan rules

The curator's spec-time secret scan is **stricter** than the
nightly-runner's repo-wide secret scan, because the curator runs *before*
files are written. The curator refuses (exit 1) on:

- OpenAI API key shape (`sk-…`).
- GitHub PAT shape (`ghp_/ghs_/gho_/ghu_/ghr_`).
- `Authorization: Bearer …` header value.
- JWT shape (`eyJ….eyJ….…`).
- `BEGIN PRIVATE KEY` block (with or without algorithm prefix).
- 12+ digit pure-numeric token (not part of a path / version).
- Denylisted signal-name tokens (case-insensitive substring match):
  `user_feature_request`, `consecutive_failure*`, `high_failure_ratio`,
  `stable_success_plateau`, `evolution_saturation`,
  `explore_opportunity`, `memory_missing`,
  `hub_search_miss_with_problem`, `*token`, `*secret*`, `*cookie*`,
  `authorization`, `bearer`, `password`, `passwd`, `private_key`,
  `api_key`, `csrf_token`, `session_token`, `auth_token`,
  `bearer_token`, `access_token`, `refresh_token`.

Detected matches are **redacted** (`<first-4>***REDACTED***`) in the
result JSON before being echoed back to the caller. The curator never
returns the raw secret-like substring.

The nightly-runner secret scan (Phase 8A) is unchanged and applies
to all generated files once they are committed.

## Git hygiene rules

The curator's output is committed under
`cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated/`,
which is *not* a root `.evolver/` or root `memory/` directory. The
Phase 8A nightly-runner `git_hygiene_no_root_evolver_or_memory`
check still passes for Phase 9A (verified by the Phase 9A validator's
own git-hygiene regression check).

The curator itself does not touch git at all (no `git add`, no
`git commit`, no `git push`). Commit + push is the operator's
responsibility.

## What this skill does NOT do

- It does **not** call any AI API to design gene strategy text.
  Strategy is operator-supplied; the curator only reformats it.
- It does **not** auto-read real runtime state.
- It does **not** read `.env` files. (AST denylist +
  `--spec` single-file read scope combine to enforce this.)
- It does **not** connect to any Hub.
- It does **not** publish anything.
- It does **not** approve or solidify.
- It does **not** install cron or create systemd timers.
- It does **not** run real test suites (`pytest`, `npm test`,
  `cargo test`, `go test`, `mvn test`).
- It does **not** modify evolver source.
- It does **not** track `runtime/.evolver/` or `runtime/memory/` in
  git.

## Refusal conditions

The curator returns `ok=false` and **does not write any file** when
**any** of:

- AST self-check fails (curator source contains a non-stdlib import).
- `--spec` is missing or unparseable JSON.
- Top-level `schema_version` is not `atl-evomap-curator-spec-v0.1`.
- Bundle / gene / capsule / safety blocks are missing required fields.
- ID consistency invariants fail (`gene.id` ≠ `bundle.target_gene_id`
  etc.).
- `bundle.visibility` or `capsule.visibility` is not `"private"`.
- `capsule.execution_trace` has fewer than 3 steps.
- `safety.hub / safety.publish / safety.credits / safety.visibility`
  do not match the hard-required values.
- Any signal name contains a denylisted token.
- Any signal / constraint / strategy / summary string contains a
  secret-like pattern.
- Resolved output path escapes `--out-dir`.

Exit codes: `0` for ok / dry-run plan ok; `1` for spec-validation
refusal (non-strict); `2` for missing-file / AST / strict-mode
refusal.

## Relationship to Phase 8A nightly validation loop

The Phase 8A nightly runner validates the **kit itself** (its 6
prior phase validators + secret scan + git hygiene). The Phase 9A
curator sits **next to** the kit and is **also validated** by the
Phase 8A nightly runner's git-hygiene + secret-scan passes plus a
new Phase 9A-specific validator.

Wiring the curator-generated bundle into the nightly runner's
4-bundle inspect / validate cycle is **out of scope** for 9A and is
left as **ATL-EVOMAP-9B** (curator-to-nightly integration).

## Future use for new domains

When the kit is later extended to ship a browser-control bundle,
Codex-only bundle, Hermes-only bundle, or any other new portable
bundle, the intended workflow is:

1. Hand-write a curator spec (or derive one from existing fixtures)
   that fits the safety contract.
2. Run `evomap_curate_bundle.py --dry-run` to validate the spec.
3. Run `evomap_curate_bundle.py` to generate the bundle draft.
4. Run `evomap_inspect_bundle.py` + `evomap_validate_bundle.py`.
5. Run `evomap_apply_bundle.py --dry-run` against an isolated `/tmp`
   target.
6. Operator reviews the diffs. If acceptable, manually invokes
   `evomap_apply_bundle.py --yes` against the isolated target only.
7. Promote the bundle to a canonical position (separate operator
   step, out of scope for 9A).
8. Extend the Phase 8A nightly runner manifest to include the new
   bundle in the 4-bundle inspect / validate cycle (ATL-EVOMAP-9B).

This keeps the bundle-curation workflow **predictable**, **auditable**,
**offline**, and **operator-gated** end-to-end.