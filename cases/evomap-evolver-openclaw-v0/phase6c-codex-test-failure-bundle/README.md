# ATL-EVOMAP-6C · Codex Test Failure Loop Bundle

**Status:** Codex test failure bundle completed (PASS)
**Date:** 2026-06-19
**Base:** `be84810` (Phase 7B · ATL-EVOMAP-7B)
**Target runtime:** `/tmp/atl-evomap-phase6c-codex-target`

## What is this

A canonical portable bundle that captures **Codex-style AI coding test
failure loop** recovery discipline. The bundle models the
characteristic shape of an AI coding loop gone wrong:

- agent edits code
- the same failing test fails 3+ times
- one fix introduces a new regression
- the failure cluster was never built before editing
- prompt / context was probably stale
- no final green test evidence was recorded

The bundle packages a 4-step Capsule that walks the agent through a
disciplined recovery sequence, with 22 domain-specific signals covering
the failure-loop shape so the evolver selector can match on it
directly.

## Offline fixture model

The bundle is **offline-first**. The only test data the bundle ever
touches is a fixture text file that describes a failure loop in plain
text. The parser (`scripts/codex_test_failure_loop_fixture.py`) reads
the fixture and outputs a JSON summary. There is **no real test
execution**, **no real source modification**, and **no online coding
API** involved.

Fixture location:
```
cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/fixtures/codex-test-failure-loop-sample.txt
```

## Parser usage

```bash
python3 scripts/codex_test_failure_loop_fixture.py \
  --input cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/fixtures/codex-test-failure-loop-sample.txt
```

Output (JSON, on stdout):
- `ok: true`
- 14 spec fields describing the failure loop shape
- `failing_tests[]` (deduplicated, in document order)
- `failure_signatures[]` (deduplicated)
- `recommended_check_order[]` (7-step recovery order)
- `safety{}` — all 7 offline-only flags set to true

The parser refuses to run on:
- `--input` paths whose basename contains `.env` or `env.local`
  (unless the basename also contains `fixture` or `sample`)
- text containing OpenAI keys, GitHub PATs, Authorization headers,
  JWTs, `BEGIN PRIVATE KEY` blocks, or 12+ digit pure-numeric values
- parser output never echoes the original unsafe line — only the
  error category

## Gene / Capsule summary

**Gene:** `gene_distilled_codex-test-failure-loop` (category: `repair`)

`signals_match` (22 entries):
- 9 generic bare: `test_failure`, `repeated_test_failure`,
  `failing_assertion`, `regression_introduced`, `fix_one_break_another`,
  `failure_cluster_missing`, `prompt_context_stale`,
  `final_green_test_missing`, `validation_loop_failure`
- 2 generic cross-context: `session_context`, `repo_context`
- 9 namespaced: `test_failure:pytest`, `repeated_test_failure:3-runs`,
  `failing_assertion:expected-actual`, `regression_introduced:new-failure`,
  `fix_one_break_another:parser-regression`,
  `failure_cluster_missing:no-signature-cluster`,
  `prompt_context_stale:cache-or-context`,
  `final_green_test_missing:no-terminal-pass`,
  `validation_loop_failure:no-green-state`
- 2 namespaced context: `session_context:codex`,
  `repo_context:ai-tool-test-lab`

**Capsule:** `capsule_codex_test_failure_loop_phase6c`
- `schema_version: 1.6.0`
- `status: success`, `confidence: 0.85`, `visibility: private`
- `source: manual_capsule_seed_phase6c`
- `trigger[]` (6 entries)
- `blast_radius: {files: 0, lines: 0}`
- `execution_trace` (4 steps: build → validate → validate → canary)

## Bundle inspect / validate / apply

```bash
# inspect
python3 scripts/evomap_inspect_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json

# validate
python3 scripts/evomap_validate_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json

# apply dry-run
python3 scripts/evomap_apply_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json \
  --inject-signals-from cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json \
  --target-runtime /tmp/atl-evomap-phase6c-codex-target --dry-run

# apply --yes
python3 scripts/evomap_apply_bundle.py \
  --bundle cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json \
  --inject-signals-from cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json \
  --target-runtime /tmp/atl-evomap-phase6c-codex-target --yes
```

## `--inject-signals-from` usage

The `--inject-signals-from` flag was added in Phase 7A. With this flag,
the apply tool extracts `gene.signals_match` and `capsule.trigger` from
the source bundle, filters them through the strict dangerous-signal /
credential / long-digit denylist, and writes 5 generic + 22 domain
signals to `memory/evolution/memory_graph.jsonl`. Without the flag,
only the 5 generic signals are written.

## Safety boundaries

This bundle **explicitly does not**:

- call Codex / OpenAI / GitHub Copilot / any online coding API
- run real `pytest` / `npm test` / `pnpm test` / `cargo test` /
  `go test` / `mvn test`
- modify any real source file
- read `.env`
- print credentials or other unsafe text
- connect to the EvoMap Hub
- publish assets / consume credits
- auto-approve or auto-solidify evolver output

The parser and apply tool both check these boundaries. The Capsule's
`execution_trace` step 4 (canary) explicitly lists all 10 safety
checkpoints.

## Typical flow

1. **Parse fixture** (offline, no execution):
   `python3 scripts/codex_test_failure_loop_fixture.py --input <fixture.txt>`
2. **Inspect bundle**:
   `python3 scripts/evomap_inspect_bundle.py --bundle <bundle.json>`
3. **Validate bundle**:
   `python3 scripts/evomap_validate_bundle.py --bundle <bundle.json>`
4. **Apply dry-run** to isolated `/tmp` runtime:
   `--target-runtime /tmp/... --dry-run`
5. **Apply --yes** to isolated `/tmp` runtime:
   `--target-runtime /tmp/... --yes`
6. **Optional evolver run/review smoke** in the target runtime:
   `evolver run` + `evolver review` (no `--approve`, no `solidify`)

## Files in this case

```
phase6c-codex-test-failure-bundle/
├── README.md                                          (this file)
├── ATL_EVOMAP_6C_CODEX_TEST_FAILURE_BUNDLE_REPORT.md  (full report)
├── bundle/
│   └── codex-test-failure-loop.bundle.json
├── fixtures/
│   └── codex-test-failure-loop-sample.txt
├── artifacts/
│   ├── gene-codex-test-failure-loop.json
│   ├── capsule-codex-test-failure-loop.json
│   ├── codex-test-failure-fixture-output.json
│   ├── parser-selftest-openai-key-output.json
│   ├── parser-selftest-github-pat-output.json
│   ├── parser-selftest-env-path-output.json
│   ├── inspect-codex-bundle-output.json
│   ├── validate-codex-bundle-output.json
│   ├── apply-codex-bundle-dry-run-output.json
│   ├── apply-codex-bundle-yes-output.json
│   ├── apply-codex-target-summary.json
│   ├── evolver-run-codex-target-output.txt
│   └── evolver-review-codex-target-output.txt
└── tools/
    ├── codex_test_failure_loop_fixture.py
    ├── evomap_apply_bundle.py
    ├── evomap_inspect_bundle.py
    └── evomap_validate_bundle.py
```

## Validator

```bash
python3 scripts/validate_evomap_phase6c_codex_test_failure_bundle.py
```

Expected: `ALL CHECKS PASSED` / `Status: codex test failure bundle completed (PASS)`.
