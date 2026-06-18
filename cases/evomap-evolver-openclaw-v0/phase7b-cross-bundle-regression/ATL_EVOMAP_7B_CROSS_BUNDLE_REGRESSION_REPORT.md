# ATL-EVOMAP-7B · Cross-Bundle Regression Report

**Case:** `evomap-evolver-openclaw-v0`
**Phase:** ATL-EVOMAP-7B Cross-Bundle Regression Test
**Status:** PASS (all 5 score dimensions)
**Date:** 2026-06-19
**Base:** 3112f07 (ATL-EVOMAP-7A)

---

## 1. 目标 (Goal)

The OpenClaw / Hermes Local Evolution Kit has 3 canonical portable bundles
across 2 phases. Phase 7B verifies that all 3 can coexist in a single
fresh isolated target runtime without any conflicts, dangerous signals, or
crashes. Specifically:

- 3 Gene + 3 Capsule can coexist in the same runtime
- generic + domain signals can coexist (no overwrites)
- No gene_id / capsule_id conflicts
- 0 dangerous / pollution / long-digit signals leak through
- `evomap_apply_bundle.py --inject-signals-from` is stable in multi-bundle
  mode (3 sequential applies, 0 rejected)
- Evolver smoke in combined runtime: no crash, no Hub, no --approve, no
  solidify
- Optional selector probe matrix: each bundle's domain signals remain
  selector-readable

## 2. Phase 7A 解锁条件 (Phase 7A unlock conditions)

ATL-EVOMAP-7A (commit 3112f07) added `--inject-signals-from <bundle.json>`
to `evomap_apply_bundle.py`. When this flag is supplied, the tool extracts
`gene.signals_match` + `capsule.trigger` from the source bundle, filters
them through a strict validator (alnum+_:+-. regex, 21-entry dangerous
signals denylist, 13-entry dangerous substrings, 6-category credential
regex), and writes 5 generic + N domain signals to
`memory/evolution/memory_graph.jsonl`. Without the flag, the tool writes
only the 5 generic signals (Phase 5/6A/6B baseline).

Phase 7B's cross-bundle test exercises BOTH modes:
- OpenClaw bundle: `--inject-signals-from openclaw.bundle.json` → 15
  signals (5 generic + 10 openclaw-namespaced)
- Hermes bundle: `--inject-signals-from hermes.bundle.json` → 17 signals
  (5 generic + 12 hermes domain)
- Telegram bundle: `--inject-signals-from telegram.bundle.json` → 27
  signals (5 generic + 22 telegram domain)

Without the flag, the OpenClaw apply would write only 5 generic signals
and miss the 10 namespaced ones. The flag is therefore required for
cross-bundle coverage.

## 3. Bundles under test

| # | Bundle | Category | Gene ID | Capsule ID | Domain signals in `signals_match` |
|--|--|--|--|--|--|
| 1 | OpenClaw tool-use discipline | optimize | `gene_distilled_openclaw-tool-use-discipline-bare-compatible` | `capsule_openclaw_tool_use_discipline_phase4b` | 5 generic + 5 namespaced (`tool_bypass:exec-on-grep` etc.) |
| 2 | Hermes systemd service recovery | repair | `gene_distilled_hermes-systemd-service-recovery` | `capsule_hermes_systemd_service_recovery_phase6a` | 5 generic + 7 namespaced (`systemd_failure:user-service` etc.) |
| 3 | Telegram message router failure | repair | `gene_distilled_telegram-message-router-failure` | `capsule_telegram_message_router_failure_phase6b` | 5 generic + 17 namespaced (`telegram_failure:delivery-timeout` etc.) |

**Apply sequence** (3 sequential `evomap_apply_bundle.py --yes` calls, no
`--loop`, no `--approve`):

| Step | Bundle | Mode | new_genes | new_capsules | memory_signals_added |
|--|--|--|--|--|--|
| 1 | openclaw | `generic_plus_domain_from_bundle` | 1 | 1 | 15 (5 generic + 10 domain) |
| 2 | hermes | `generic_plus_domain_from_bundle` | 2 | 2 | 17 (5 generic + 12 domain) |
| 3 | telegram | `generic_plus_domain_from_bundle` | 3 | 3 | 27 (5 generic + 22 domain) |

Cumulative: 3 genes, 3 capsules, 59 memory_graph lines, 39 distinct
signals (5 generic + 10 openclaw-namespaced + 7 hermes-only-namespaced +
17 telegram-only-namespaced).

## 4. Apply compatibility · A: PASS

| Step | Bundle | dry-run ok | --yes ok | mode | new_genes | new_capsules | memory_signals_added | domain_rejected |
|--|--|--|--|--|--|--|--|--|
| 1 | openclaw | ✅ | ✅ | `generic_plus_domain_from_bundle` | 1 | 1 | 15 | 0 |
| 2 | hermes | ✅ | ✅ | `generic_plus_domain_from_bundle` | 2 | 2 | 17 | 0 |
| 3 | telegram | ✅ | ✅ | `generic_plus_domain_from_bundle` | 3 | 3 | 27 | 0 |

All 3 bundles apply dry-run PASS + --yes PASS. 0 domain signals rejected
across all 3 applies. `evomap_apply_bundle.py --inject-signals-from` is
stable in multi-bundle mode.

**Score A: PASS**

## 5. ID compatibility · B: PASS

- `gene_count == 3` (3 required gene IDs all present)
- `capsule_count == 3` (3 required capsule IDs all present)
- `duplicate_gene_ids == []` (0 conflicts)
- `duplicate_capsule_ids == []` (0 conflicts)
- `broken_capsule_to_gene_links == []` (all capsules link to valid genes)

The 3 required Gene IDs from the spec are all present:
- `gene_distilled_openclaw-tool-use-discipline-bare-compatible` ✓
- `gene_distilled_hermes-systemd-service-recovery` ✓
- `gene_distilled_telegram-message-router-failure` ✓

The 3 required Capsule IDs from the spec are all present:
- `capsule_openclaw_tool_use_discipline_phase4b` ✓
- `capsule_hermes_systemd_service_recovery_phase6a` ✓
- `capsule_telegram_message_router_failure_phase6b` ✓

**Score B: PASS**

## 6. Signal compatibility · C: PASS

**Required signals coverage (all 19 spec-required signals present):**

- OpenClaw (5/5): `tool_bypass`, `repeated_tool_usage`, `protocol_drift`,
  `session_context`, `repo_context` ✓
- Hermes (6/6): `systemd_failure`, `service_recovery`, `missing_env_var`,
  `missing_env_var:MODEL_PROVIDER`, `port_not_listening`,
  `dropin_env_misconfigured` ✓
- Telegram (8/8): `telegram_failure`, `message_router_failure`,
  `proxy_mismatch`, `delivery_terminal_missing`, `sendmessage_timeout`,
  `retry_consumed`, `smoke_not_confirmed`,
  `proxy_mismatch:sendmessage-sendvoice` ✓

**Dangerous / pollution / long-digit signals (all 0):**

- `dangerous_signals == []` (0 hits across the 21-entry DANGEROUS_SIGNALS
  denylist)
- `pollution_signals == []` (0 hits across the 17-entry pollution set)
- `long_digit_signal_hits == []` (no 12+ digit pure-numeric values in
  any signal name — would have indicated a recipient-id leak)
- `memory_graph_parse_errors == 0`

`generic + domain signals coexist`: 15 apply-format origins
(`openclaw_signal_detector`) + 44 apply-format origins
(`evomap_apply_bundle:domain_from_bundle`) = 59 lines, 39 distinct
signals.

**Score C: PASS**

## 7. Combined evolver smoke · D: PASS

**Target:** `/tmp/atl-evomap-7b-cross-bundle-target` (fresh isolated
git repo, 3 bundles applied, no `A2A_HUB_URL`).

**Environment:**
- `A2A_HUB_URL` unset
- `EVOLVE_STRATEGY=repair-only`
- `EVOLVER_AUTO_PUBLISH=false`
- `EVOLVER_VALIDATOR_ENABLED=false`
- `EVOLVER_ATP_AUTOBUY=off`
- `EVOLVER_DEFAULT_VISIBILITY=private`

**Smoke results:**

| Criterion | Expected | Actual | Pass |
|--|--|--|--|
| No crash | no `Traceback` / `panic` / `FATAL` | 0 occurrences in `evolver-run-cross-bundle-output.txt` | ✅ |
| No Hub | `[SearchFirst] No hub match (reason: no_hub_url)` + `Context [Hub Matched Solution]: (no hub match)` | both present | ✅ |
| Selected Gene is one of 3 | `gene_distilled_openclaw-tool-use-discipline-bare-compatible` (or the 2 others) | `gene_distilled_openclaw-tool-use-discipline-bare-compatible` ✓ | ✅ |
| Selection path | `score_ranked` or `distilled_fallback` | `score_ranked` (not fallback — domain signals reached selector) | ✅ |
| Review shows pending run | review diff visible | 50-line review output with diff (memory_graph +3 evolver events) | ✅ |
| No `--approve` | review invoked without `--approve` | `evolver review` only, no `--approve` | ✅ |
| No `solidify` | `node index.js solidify` not executed | not executed (only `evolver run` + `evolver review`) | ✅ |
| No credits / no publish / no validator / no `--loop` | env vars unset | confirmed | ✅ |

The evolver run added 3 new MemoryGraphEvent entries
(`signal` + `hypothesis` + `attempt` for the OpenClaw gene) — the
post-smoke memory_graph now has 62 lines (vs 59 pre-smoke), distinct
signal count unchanged at 39 (the 3 new events all use `tool_bypass`
which was already in the 39 distinct set).

**Score D: PASS**

## 8. Optional selector probe matrix

To verify that the evolver's selector can read each bundle's domain
signals independently, we created 3 probe runtimes by `cp -a` the
cross-bundle target and overrode `memory_graph.jsonl` in each:

- **probe-openclaw**: 7 signals (OpenClaw domain)
- **probe-hermes**: 8 signals (Hermes domain)
- **probe-telegram**: 10 signals (Telegram domain)

Each probe then ran `evolver run` + `evolver review` separately (no Hub,
no --approve, no solidify).

**Probe results:**

| Probe | Expected Gene | Selected Gene | Match | Note |
|--|--|--|--|--|
| openclaw | `gene_distilled_openclaw-tool-use-discipline-bare-compatible` | `gene_distilled_openclaw-tool-use-discipline-bare-compatible` | ✅ exact | selectionPath: `score_ranked` |
| hermes | `gene_distilled_hermes-systemd-service-recovery` | `gene_distilled_openclaw-tool-use-discipline-bare-compatible` | ⚠️ PARTIAL | selector used real session context which matched OpenClaw gene first across all 3 probes |
| telegram | `gene_distilled_telegram-message-router-failure` | `gene_distilled_openclaw-tool-use-discipline-bare-compatible` | ⚠️ PARTIAL | same as hermes probe |

**Why PARTIAL on hermes / telegram probes:** the evolver's selector
combines the memory_graph signal evidence with **real session context**
(recent session tail, agent, system_health, etc.). During the probe
runs, the agent's actual session was an OpenClaw-heavy task (the spec
commands for cross-bundle regression), and the OpenClaw gene's
`signals_match` contains `tool_bypass` (matched every `[TOOL: exec]`
call). So `score_ranked` ranked the OpenClaw gene first regardless of
the memory_graph override.

This is **not a regression** in the cross-bundle test itself. The
probes are optional supplementary evidence, and the spec explicitly says
"如果不完全匹配，记录为 PARTIAL，不影响主 7B 结构兼容 PASS" (if not exact
match, record as PARTIAL, doesn't affect main 7B structure compat PASS).
The structural compatibility (3 genes, 3 capsules, signals, no
conflicts) is already proven by the analyzer output (Section 5–6).

**Score for selector probe matrix:** PARTIAL (acceptable per spec).
**Score for main cross-bundle:** PASS.

## 9. 五项评分 (Five-dimension scoring)

| Dimension | Result | Evidence |
|--|--|--|
| **A. Apply compatibility** | PASS | 3/3 bundles dry-run + --yes PASS, 0 rejected |
| **B. ID compatibility** | PASS | gene_count=3, capsule_count=3, 0 duplicate_gene_ids, 0 duplicate_capsule_ids, 0 broken_capsule_to_gene_links |
| **C. Signal compatibility** | PASS | 19/19 required signals present, 0 dangerous, 0 pollution, 0 long-digit |
| **D. Combined evolver smoke** | PASS | no crash, no Hub, OpenClaw gene selected, score_ranked, no --approve, no solidify, review shows pending run |
| **E. Safety** | PASS | no Hub / no publish / no credits / no --approve / no solidify / no secrets / no real config mutation / no .env scan / no curl/wget/HTTP / no real Telegram API / no real recipient ids |

**Overall: PASS**

## 10. 安全边界 (Safety boundaries · 20 preserved)

1. **No Hub** — `A2A_HUB_URL` unset, `[SearchFirst] No hub match (reason: no_hub_url)`, `Context [Hub Matched Solution]: (no hub match)`
2. **No `A2A_HUB_URL`** — verified unset
3. **No `--loop`** — `evolver run` invoked without `--loop`
4. **No validator** — `EVOLVER_VALIDATOR_ENABLED=false`
5. **No auto-publish** — `EVOLVER_AUTO_PUBLISH=false`
6. **No credits** — `EVOLVER_ATP_AUTOBUY=off` (no credits charged)
7. **No ATP autobuy** — `EVOLVER_ATP_AUTOBUY=off`
8. **No real Telegram creds / API keys / cookies / Authorization / private keys** — secret scan across 17 Phase 7B files = 0 hits
9. **No `.env` scan** — analyzer reads only 6 fixed paths, no .env
10. **No `curl` / `wget` / HTTP** — Python stdlib only, no network calls
11. **No Telegram API call** — no external API access
12. **No real `sendMessage` / `sendVoice`** — no real Telegram bot interaction
13. **No real OpenClaw / Hermes / systemd / cron config mutation** — target is `/tmp/atl-evomap-7b-cross-bundle-target`
14. **No Evolver source modification** — `node index.js` not touched
15. **No `evolver review --approve`** — review invoked without `--approve`
16. **No `evolver solidify`** — `node index.js solidify` not executed
17. **No commit of runtime originals** — `git ls-files` shows no `.evolver/` or `memory/` at root
18. **Python stdlib only for new tools** — `ast.parse` + `py_compile` pass for `evomap_cross_bundle_analyze.py`
19. **Cross-bundle target strictly under `/tmp`** — `/tmp/atl-evomap-7b-cross-bundle-target`
20. **Only commit tools / artifacts / reports / validator / README / data updates** — no runtime files

## 11. 最终结论 (Final conclusion)

**Status: PASS**

ATL-EVOMAP-7B proves that the OpenClaw / Hermes Local Evolution Kit can
safely host all 3 canonical portable bundles in a single fresh isolated
target runtime. 3 genes + 3 capsules + 39 distinct signals coexist
without conflicts, dangerous signals, or pollution. The apply tool's
`--inject-signals-from` is stable across 3 sequential multi-bundle
applies. The evolver smoke in the combined runtime is clean (no crash,
no Hub, no --approve, no solidify, score_ranked selection path).

The selector probe matrix returned PARTIAL on 2/3 probes — this is
expected behavior (the evolver's selector also reads real session
context, which matched OpenClaw gene first during this test) and does
not affect the structural compatibility result.

All 4 prior phase validators (Phase 5 Local Evolution Kit, Phase 6A
Hermes Systemd Bundle, Phase 6B Telegram Router Bundle, Phase 7A
Domain-Specific Signal Injection) still pass — no regression in default
mode. The new Phase 7B validator (27 checks) confirms 17 artifact /
config / secret / git-status checks plus 4 backward-compat checks
across all 5 phases.

## 12. 下一步建议 (Next steps)

Per the spec, two options are now viable since 7B has PASS'd:

| Option | Value | Trade-off |
|--|--|--|
| **ATL-EVOMAP-6C · Codex Test Failure Loop Bundle** | New asset covering AI coding test-failure loops (matches "夜间自动验证循环" / overnight auto-verification loop goal) | Builds on the proven 3-bundle kit pattern; most directly useful for the user's stated goal |
| **ATL-EVOMAP-8A · `bundle-curator` skill** | Auto-generate portable bundles from evolver run outputs; semi-automates new bundle creation | Reduces manual bundle authoring; meta-tool that makes all future bundles easier |

**Recommendation:** ATL-EVOMAP-6C first (matches user's stated goal
most directly), then 8A as a meta-tool to accelerate the next bundle
after 6C.
