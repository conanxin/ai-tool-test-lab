# ATL-EVOMAP-6C · Codex Test Failure Loop Bundle Report

**Case:** `evomap-evolver-openclaw-v0`
**Phase:** ATL-EVOMAP-6C · Codex Test Failure Loop Bundle
**Status:** `codex test failure bundle completed (CODEX_TEST_FAILURE_BUNDLE_PASS)`
**Date:** 2026-06-19
**Base:** `be84810` (ATL-EVOMAP-7B)

---

## 1. 目标 (Goal)

Add a 4th canonical portable bundle to the OpenClaw / Hermes Local
Evolution Kit, focused on the characteristic failure shape of an AI
coding / Codex-style test loop:

- agent edits code → tests run → tests fail
- the same failing test fails 3+ times in a row
- one fix introduces a new regression (fix one break another)
- failure cluster was never built before editing
- prompt / context is suspected stale
- no final green test evidence was recorded

The bundle must be:
- offline-first (only parses a fixture, no real test execution)
- local-only (no Hub, no publish, no credits, no approve, no solidify)
- cross-validatable (inspect, validate, apply --yes, optional smoke)
- safe-by-design (parser refuses `.env` paths and credential-shaped
  text, never echoes raw unsafe content)

## 2. Phase 7B 解锁条件 (Phase 7B unlock conditions)

ATL-EVOMAP-7B (commit `be84810`) proved that 3 canonical portable
bundles (OpenClaw tool-use discipline, Hermes systemd service
recovery, Telegram message router failure) can coexist in a single
fresh isolated target runtime. Cross-bundle compatibility is proven:

- 3 Gene + 3 Capsule + 39 distinct signals coexist
- 0 dangerous / pollution / long-digit signals
- combined evolver smoke PASS (no Hub, no approve, no solidify)
- 5/5 score dimensions PASS

This unlocks authoring new bundles with confidence that the apply
tool, inspect tool, validate tool, and 7B cross-bundle regression
test will all keep passing.

## 3. Codex test failure loop model

The bundle models 9 bare failure-loop signals + 2 cross-context
generic signals + 9 namespaced variants + 2 namespaced context
variants = 22 total signals in the `signals_match` list. The signal
hierarchy is:

| Level | Signal | Meaning |
|--|--|--|
| bare | `test_failure` | at least one test failed |
| bare | `repeated_test_failure` | 3+ consecutive failures with same signature |
| bare | `failing_assertion` | an assertion expected/actual diff is present |
| bare | `regression_introduced` | a new failure was introduced by a fix |
| bare | `fix_one_break_another` | a previous passing case is now failing |
| bare | `failure_cluster_missing` | failures were not clustered by signature |
| bare | `prompt_context_stale` | prompt / context cache is suspected stale |
| bare | `final_green_test_missing` | no terminal pass was recorded |
| bare | `validation_loop_failure` | validation loop did not reach a green state |
| ns    | `test_failure:pytest` | the test runner is pytest |
| ns    | `repeated_test_failure:3-runs` | the repeated-failure threshold is 3 |
| ns    | `failing_assertion:expected-actual` | the assertion diff is the typical expected/actual shape |
| ns    | `regression_introduced:new-failure` | the regression was a new failure (not a re-failure) |
| ns    | `fix_one_break_another:parser-regression` | a common sub-shape: parser regex change broke existing cases |
| ns    | `failure_cluster_missing:no-signature-cluster` | common sub-shape: no signature cluster was built |
| ns    | `prompt_context_stale:cache-or-context` | common sub-shape: cache or context is stale |
| ns    | `final_green_test_missing:no-terminal-pass` | common sub-shape: no terminal pass event was emitted |
| ns    | `validation_loop_failure:no-green-state` | common sub-shape: validation loop never reached green |
| cross | `session_context:codex` | the agent is in a Codex-style session |
| cross | `repo_context:ai-tool-test-lab` | the repo is the local evolution kit |
| generic | `session_context` | cross-context generic |
| generic | `repo_context` | cross-context generic |

## 4. Offline fixture + parser

**Fixture path:** `fixtures/codex-test-failure-loop-sample.txt`

Plain-text description of a 3-run failure loop with two failing tests,
one repeated signature, and a fix-one-break-another regression. The
fixture includes explicit "safe redaction notes" so that anyone reusing
the fixture understands it is offline, sanitized, and contains no real
private code, real test command execution, or real online coding
service references.

**Parser path:** `scripts/codex_test_failure_loop_fixture.py`

The parser takes `--input <path>`, refuses to run on:
- path basenames containing `.env` or `env.local` (unless the basename
  also contains `fixture` or `sample`)
- text containing OpenAI API keys, GitHub PATs, Authorization
  headers, JWTs, `BEGIN PRIVATE KEY` blocks, or 12+ digit pure-numeric
  values

When the parser refuses, it returns `ok=false` with an error category
(e.g. `unsafe_fixture (openai-style api key)` or
`refused_input_path`) and **never echoes the original unsafe line**.

On the valid fixture, the parser outputs 14 spec fields describing
the failure loop shape, plus `failing_tests[]`, `failure_signatures[]`,
`recommended_check_order[]` (7 steps), and `safety{}` (7 offline-only
flags).

## 5. Parser self-tests

3 self-tests were executed against the parser:

| Input | Expected | Actual |
|--|--|--|
| OpenAI key (`sk-XXXX...X`) in `/tmp` | `ok=false, error=unsafe_fixture (openai-style api key)`, exit=2 | ✅ PASS |
| GitHub PAT (`ghp_YYYY...Y`) in `/tmp` | `ok=false, error=unsafe_fixture (github personal access token)`, exit=2 | ✅ PASS |
| `.env-codex-test.txt` (basename contains `.env`) | `ok=false, error=refused_input_path`, exit=2 | ✅ PASS |

The 3 unsafe raw inputs were generated in `/tmp` only (never in repo)
using a Python heredoc to concatenate the prefix and the token-shaped
suffix — no unsafe substring appears in any committed artifact.

The 3 self-test output JSONs (`parser-selftest-*.json`) were verified
to contain **0 occurrences** of:
- the 48-char `X` run from the OpenAI key
- the 36-char `Y` run from the GitHub PAT
- any `sk-X` or `ghp_Y` substring
- the original unsafe input

## 6. Gene 设计 (Gene design)

**`gene_distilled_codex-test-failure-loop`** (category: `repair`)

`signals_match`: 22 entries (9 bare + 2 cross-context + 9 namespaced +
2 namespaced-context). See Section 3 for the full table.

`strategy` (6 ordered steps):
1. Freeze the exact failing test command before editing again.
2. Cluster failures by stable signature and assertion diff before
   choosing a fix.
3. Distinguish repeated same-signature failure from new regression
   failure.
4. Make one minimal code change per cycle and preserve existing
   passing cases.
5. Rerun the narrow failing test before broad suites.
6. Do not mark the task complete until final green test evidence is
   recorded.

`constraints`:
- `max_files: 8`
- `forbidden_paths`: `.git`, `node_modules`, `.evolver`, `memory`,
  `.env`, `real_runtime_root`
- `forbidden_actions`: `run_real_tests_from_fixture_parser`,
  `mutate_real_source_from_fixture_parser`, `call_online_coding_api`,
  `print_secret`, `commit_env_file`, `claim_green_without_evidence`,
  `broaden_scope_before_signature_cluster`

## 7. Capsule 设计 (Capsule design)

**`capsule_codex_test_failure_loop_phase6c`**

- `schema_version: 1.6.0`
- `status: success`, `confidence: 0.85`, `visibility: private`
- `source: manual_capsule_seed_phase6c`
- `trigger[]` (6 entries): `test_failure`, `repeated_test_failure`,
  `failing_assertion`, `regression_introduced`, `fix_one_break_another`,
  `final_green_test_missing`
- `blast_radius: {files: 0, lines: 0}`
- `execution_trace` (4 steps):

| Step | Stage | Command | exit_code |
|--|--|--|--|
| 1 | build | `python3 scripts/codex_test_failure_loop_fixture.py --input <fixture>` | 0 |
| 2 | validate | `python3 -m json.tool artifacts/codex-test-failure-fixture-output.json` | 0 |
| 3 | validate | `assert repeated_failure_count == 3 and fix_one_break_another == true and final_green_test_missing == true` | 0 |
| 4 | canary | `safety_check` (all 10 boundaries) | 0 |

Step 4 (canary) records 10 safety checkpoints:
- `no_real_tests_run`, `no_source_mutation`, `no_env_scan`,
  `no_secrets`, `no_network_call`, `no_online_coding_api`,
  `no_hub`, `no_publish`, `no_approve`, `no_solidify`.

## 8. Bundle schema

The bundle follows the Phase 5 / 6A / 6B / 7A schema:
- `schema_version: atl-evomap-portable-bundle-v0.1`
- `source_phase: ATL-EVOMAP-6C`
- `source_session: /tmp/atl-evomap-phase6c-codex-target`
- `target_gene_id`, `target_capsule_id` (denormalized for
  pre-validation)
- `gene: {...}`, `capsule: {...}` (full embedded objects)
- `execution_trace` (mirrors capsule.execution_trace)
- `fixture_summary` (15 fields summarising the parsed fixture)
- `safety{}` — 9 hard safety flags
- `import_contract` — 3 required files, 3 optional files,
  required-in-genes, required-in-capsules, minimum_execution_trace
- `kit_provenance` — all 5 prior phase commits + 6C phase marker

## 9. inspect / validate 结果

| Check | Result | Detail |
|--|--|--|
| inspect | ✅ PASS | 12 fields returned; execution_trace_steps=4, stages=build/validate/validate/canary |
| validate | ✅ PASS | 12/12 checks PASS, 0 failures, 0 secret hits |

`validate-codex-bundle-output.json` confirms:
- bundle file exists
- bundle is valid JSON
- bundle has schema_version `atl-evomap-portable-bundle-v0.1`
- bundle has `gene`, `capsule`, `execution_trace` fields
- `gene.id == gene_distilled_codex-test-failure-loop`
- `capsule.id == capsule_codex_test_failure_loop_phase6c`
- `capsule.gene` references the same Gene id
- `capsule.execution_trace` is non-empty list (len=4)
- `import_contract.required_files` contains the 3 required paths
- 0 secret patterns found in bundle

## 10. apply dry-run / apply --yes 结果

Both apply calls succeeded with `signal_injection_mode =
generic_plus_domain_from_bundle`:

| Apply | mode | ok | gene | capsule | memory_signals | domain_rejected |
|--|--|--|--|--|--|--|
| dry-run | plan | ✅ | 1 | 1 | 27 (5 generic + 22 domain) | 0 |
| --yes   | applied | ✅ | 1 | 1 | 27 (5 generic + 22 domain) | 0 |

After apply, `/tmp/atl-evomap-phase6c-codex-target` contains:

| File | State |
|--|--|
| `.evolver/gep/genes.json` | 1 gene, `gene_distilled_codex-test-failure-loop` |
| `.evolver/gep/capsules.json` | 1 capsule, `capsule_codex_test_failure_loop_phase6c` |
| `memory/evolution/memory_graph.jsonl` | 27 lines, 25 distinct signals |
| `.evolver/gep/events.jsonl` | empty (reset by apply) |
| `.evolver/gep/failed_capsules.json` | `[]` (reset by apply) |
| `.evolver/gep/candidates.jsonl` | empty (reset by apply) |

All 8 spec-required signals are present in the target:
`test_failure`, `repeated_test_failure`, `failing_assertion`,
`regression_introduced`, `fix_one_break_another`,
`final_green_test_missing`, `test_failure:pytest`,
`repeated_test_failure:3-runs`.

## 11. optional run/review smoke 结果

The isolated target was committed as `apply Codex test failure loop
bundle for ATL-EVOMAP-6C`, then `evolver run` and `evolver review` were
executed with the standard safety env vars
(`A2A_HUB_URL` unset, `EVOLVE_STRATEGY=repair-only`,
`EVOLVER_AUTO_PUBLISH=false`, `EVOLVER_VALIDATOR_ENABLED=false`,
`EVOLVER_ATP_AUTOBUY=off`, `EVOLVER_DEFAULT_VISIBILITY=private`).

| Criterion | Expected | Actual |
|--|--|--|
| No crash | no Traceback / panic / FATAL | 0 occurrences across 786-line run output |
| No Hub | `[SearchFirst] No hub match (reason: no_hub_url)` | found |
| Selected Gene is the bundle's Gene | `gene_distilled_codex-test-failure-loop` | ✅ selected by selector (selectionPath: distilled_fallback, since evolver injected an internal `memory_missing` signal that doesn't match our 22) |
| Review shows pending run | review diff visible | ✅ review output shows full Gene summary + diff in memory_graph.jsonl (+3 evolver events) |
| No `--approve` | review invoked without `--approve` | ✅ |
| No `solidify` | `node index.js solidify` not executed | ✅ |
| No credits / publish / validator | env vars unset | ✅ |

Note on selection path: evolver's selector used `distilled_fallback`
because evolver's own session-context-based signal detector injected
`memory_missing` (an internal evolver signal, not one from our apply
bundle's 22), and `memory_missing` matched our gene's
`signals_match` via the generic `session_context` / `repo_context`
signals. The important point is that **the bundle's Gene survived** and
is the selected one, regardless of which selector branch was used.

## 12. 安全边界 (Safety boundaries)

All 22 spec-listed hard boundaries are preserved:

1. No Hub (no `A2A_HUB_URL`)
2. No `--loop` (no `evolver run --loop`)
3. No validator (`EVOLVER_VALIDATOR_ENABLED=false`)
4. No auto-publish (`EVOLVER_AUTO_PUBLISH=false`)
5. No credits (`EVOLVER_ATP_AUTOBUY=off`)
6. No real OpenAI / Codex / Copilot API key
7. No `.env` scan (parser checks `.env` basenames and refuses)
8. No real `pytest` / `npm test` / `pnpm test` / `cargo test` /
   `go test` / `mvn test`
9. No real project code modification
10. No `curl` / `wget` / HTTP (Python stdlib only)
11. No online coding API call
12. No real OpenClaw / Hermes / systemd / cron config mutation
13. No Evolver source modification
14. No `evolver review --approve`
15. No `evolver solidify`
16. No commit of runtime `.evolver/` or `memory/` originals
17. No real Telegram API / cookie / PAT / Authorization header
18. Python stdlib only for new tools
19. Target runtime strictly under `/tmp`
20. Only commit: tools / bundle / fixture / artifacts / reports /
    validator / README / data updates
21. Human-readable omitted text for any fake secret (never real
    key/token value)
22. Parser self-test unsafe inputs only in `/tmp`, never in repo

The parser additionally enforces (as part of the bundle's safety
contract):
- input path refusal (basename `.env` / `env.local` check)
- content refusal (credential / JWT / PEM / long-digit detection)
- output sanitization (never echoes the original unsafe line)

## 13. 最终结论 (Final conclusion)

**Status: PASS**

ATL-EVOMAP-6C successfully adds a 4th canonical portable bundle to
the OpenClaw / Hermes Local Evolution Kit. The bundle:

- models the Codex-style AI coding test failure loop shape with 22
  domain signals
- has a 6-step Gene strategy and a 4-step Capsule execution_trace
- parses a fixture offline (no real tests, no real source
  modification, no online coding API)
- refuses `.env` paths and credential-shaped text without echoing
  the original unsafe line
- inspects and validates cleanly (12/12 validate checks PASS, 0
  secret hits)
- applies cleanly to an isolated `/tmp` runtime (1 gene, 1 capsule,
  27 memory_graph lines, 25 distinct signals, 0 errors)
- runs an evolver smoke that selects the bundle's Gene, refuses Hub,
  refuses `--approve`, refuses `solidify`

All 5 prior phase validators (Phase 5 / 6A / 6B / 7A / 7B) still
**ALL CHECKS PASSED** — no regression in default mode. The new
Phase 6C validator (23 checks) passes.

## 14. 下一步建议 (Next steps)

Per the spec, with 6C PASS'd the kit now has 4 canonical portable
bundles covering:

- OpenClaw tool-use discipline (optimize)
- Hermes systemd service recovery (repair)
- Telegram message router failure (repair)
- Codex test failure loop (repair)

The next step candidates are:

| Option | Value | Trade-off |
|--|--|--|
| **ATL-EVOMAP-7A · Browser-Control `rate-limit-recovery` Bundle** | Covers browser automation rate-limit / cooldown cycles | Same 3+1 bundle pattern; complements 6C nicely (Codex = local test loop, browser-control = external API loop) |
| **ATL-EVOMAP-8A · `bundle-curator` skill** | Auto-generate portable bundles from evolver run outputs; semi-automates new bundle creation | Meta-tool that makes all future bundles easier |
| **Automated nightly validation loop asset** | Cron-driven run of the 5+1 validators + 6C parser; produces a daily PASS/FAIL digest | Direct match to user's stated "夜间自动验证循环" goal; uses the kit's existing tools + spec'd fixtures |

**Recommendation:** Start with the automated nightly validation loop
asset, since 6C is the last manual-bundle piece needed and the kit
now has enough canonical coverage to be reliably auto-validated. The
7A browser-control bundle and 8A bundle-curator skill can be the
post-validation-loop additions.
