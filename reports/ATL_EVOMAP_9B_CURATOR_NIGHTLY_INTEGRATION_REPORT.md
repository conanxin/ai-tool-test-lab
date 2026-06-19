# ATL-EVOMAP-9B Curator-to-Nightly Integration — Case Report

**Phase:** ATL-EVOMAP-9B — Curator-to-Nightly Integration
**Base commit:** `7811e1b`
**Status:** ✅ Curator-to-Nightly Integration smoke pass
**Final status:** `CURATOR_NIGHTLY_INTEGRATION_SMOKE_PASS`
**Schema:** `atl-evomap-nightly-validation-v0.1` (manifest extended; backward-compatible)

---

## 1. 目标

把 Phase 9A 的 curator-generated draft bundles 接入 Phase 8A nightly
validation runner,实现:

- canonical bundles = blocking lane(不变)
- curator-generated draft bundles = non-blocking canary lane(新)
- canary 失败不使 overall_status FAIL
- future curator-generated bundles 可以自动加入 nightly digest 做
  inspect / validate / apply dry-run

不安装真实 cron,不运行 evolver,不 approve,不 solidify,不 publish,
不接 Hub。

## 2. Phase 9A 解锁条件

Phase 9A(`7811e1b`)已交付:

- `scripts/evomap_curate_bundle.py` — stdlib-only curator skill with AST
  self-check + spec-time safety enforcement。
- `cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated/sample-safe-bundle.bundle.json`
  — 一个 curator 生成的 draft bundle,自带完整 inspect / validate /
  apply 链路,且已通过 9A 的 self-tests。

Phase 9B 在此基础上扩展 nightly runner,让它自动 ingest 此类 draft bundle
做 inspect + validate + apply dry-run。

## 3. Manifest extension

修改
`cases/evomap-evolver-openclaw-v0/phase8a-nightly-validation-loop/validation-loop-manifest.json`:

- 顶层加 `extended_by_phase: "ATL-EVOMAP-9B"`。
- 顶层加 `canary_bundles[]`,首条 `sample-safe-bundle-phase9a` 指向 9A
  生成的 sample bundle,`lane = "curator_generated"`,
  `blocking = false`,`expected_status = "CANARY_PASS"`,
  `apply_dry_run_target_runtime = "/tmp/atl-evomap-nightly-canary-sample-safe-bundle-phase9a"`。
- `checks[]` 列表追加 `"canary_bundles_checked"`(默认 non-blocking)。
- `checks_detail.canary_bundles_checked` 详细描述三条检查命令和 lane 行为。
- `versioning.manifest_version` 升级 `0.1.0 → 0.2.0`;
  `next_intended_phase` 改写为 `ATL-EVOMAP-9C (optional: curator-driven
  canary apply with operator gate)`。
- `intent` 文本追加 9B 说明。
- `schema_version` **保持** `atl-evomap-nightly-validation-v0.1`
  (backward-compatible)。

## 4. Runner extension

修改 `scripts/evomap_nightly_validate.py`:

1. **新增 `_load_manifest(repo_root)` 辅助函数**:从磁盘读取 manifest JSON,
   用于发现 `canary_bundles`。
2. **新增 `check_canary_bundles(results, repo_root)`**:
   - 读 manifest 的 `canary_bundles[]`;
   - 每个 entry 跑 `inspect → validate → apply --dry-run(target=/tmp/...)`;
   - 失败不写 overall_status 影响;只把 `canary_bundles_checked` 这一行
     标记为 `WARN`,细节进 `extra.canary_bundle_checks` + `extra.canary_summary`。
3. **`all_phase_validators_pass` 列表追加 `phase9a_bundle_curator_skill`**,
   validators 数量从 6 → 7。
4. **顶层 digest 新增字段**:
   - `bundle_checks.inspect[]` / `bundle_checks.validate[]` — 4 canonical
     bundles 各一条 `{id, path, returncode, status}`;
   - `canary_bundle_checks[]` — per-canary inspect/validate/apply_dry_run;
   - `canary_summary` — `{total, passed, failed, blocking_failures,
     non_blocking_failures, status}`;
   - `validators[]` — 把 `check_all_phase_validators_pass.extra.validators[]`
     提到顶层,方便下游 summary extractor 计数;
   - `extended_by_phase: "ATL-EVOMAP-9B"`。
5. **Markdown digest** 新增 `## Canary / Curator-generated bundles` 章节,
   含汇总 + per-bundle 表格(`id, source_phase, path, inspect, validate,
   apply_dry_run, status, blocking`)。
6. **apply dry-run 目标目录** 在 runner 中由
   `target_rt.mkdir(parents=True, exist_ok=True)` 创建于
   `/tmp/atl-evomap-nightly-canary-<id>`(隔离、临时、不动真 runtime)。
7. **apply JSON 解析**:即使 apply rc=0,也解析 stdout 中 JSON 的 `ok` 字段,
   若 `ok=false` 则记录为 FAIL,带 `reason`。
8. **CLI 行为完全向后兼容**:`--repo-root` / `--out-dir` / `--markdown-name` /
   `--json-name` / `--strict` / `--dry-run` / `--output-dir`(别名)都保留。
9. **stdlib-only guard 不变**:runner 仍然只用 stdlib。

## 5. Forward-compatible fix (Phase 9A → 8A 解环)

加 9A 到 `all_phase_validators_pass` 后会出现循环:

```
nightly runner
  → 9A validator
    → 8A validator
      → nightly runner (self-host)
        → 9A validator
          → 8A validator
            → ...
```

Phase 9B 按 Step 1 的 forward-compatible 修复规则修改了
`scripts/validate_evomap_phase9a_bundle_curator_skill.py`:**从
`PRIOR_VALIDATORS` 列表中移除 `phase8a_nightly_validation_loop.py`**,
并在源码中加注释解释循环成因与设计取舍。

- 不降低任何 artifact / secret scan / report check。
- 8A 自身的 self-host 检查仍在 8A validator 内运行,且 nightly chain
  仍可触发(只是不再从 9A 内部递归触发)。
- 9A validator 在此修改后仍 ALL CHECKS PASSED(已验证)。
- 8A validator 在此修改后仍 ALL CHECKS PASSED(已验证,见 § 8 回归)。

## 6. Canonical blocking lane

| Bundle | Path | inspect | validate |
|--------|------|---------|----------|
| `openclaw_tool_use_discipline` | `cases/.../phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json` | PASS | PASS |
| `hermes_systemd_recovery` | `cases/.../phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json` | PASS | PASS |
| `telegram_message_router_failure` | `cases/.../phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json` | PASS | PASS |
| `codex_test_failure_loop` | `cases/.../phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json` | PASS | PASS |

4/4 inspect PASS + 4/4 validate PASS,均 blocking。

## 7. Curator-generated canary lane

| Canary ID | Source | inspect | validate | apply_dry_run | Status | Blocking |
|-----------|--------|---------|----------|---------------|--------|----------|
| `sample-safe-bundle-phase9a` | ATL-EVOMAP-9A | PASS | PASS | PASS | **CANARY_PASS** | no |

- 1/1 canary PASS。
- target runtime = `/tmp/atl-evomap-nightly-canary-sample-safe-bundle-phase9a`
  (由 runner 自动 mkdir;apply dry-run 不写任何真实 runtime)。
- canary_blocking = false → 即使 CANARY_FAIL,overall_status 仍由 9 个
  blocking check 决定。

## 8. Nightly smoke result

执行:

```bash
rm -rf cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-smoke
python3 scripts/evomap_nightly_validate.py \
    --repo-root . \
    --out-dir cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-smoke
```

输出:

```
overall_status       : PASS
blocking_total       : 9
blocking_passed      : 9
blocking_failed      : 0
validator_count      : 7
validators_passed    : 7
validators_failed    : 0
bundle_inspect_count : 4
bundle_validate_count: 4
canary_total         : 1
canary_passed        : 1
canary_failed        : 0
canary_status        : CANARY_PASS
canary_blocking_failures       : 0
canary_non_blocking_failures   : 0
canary_first_id                : sample-safe-bundle-phase9a
canary_first_status            : CANARY_PASS
canary_first_blocking          : false
canary_first_inspect           : PASS
canary_first_validate          : PASS
canary_first_apply_dry_run     : PASS
secret_scan_ok                 : true
git_hygiene_ok                 : true
hard_boundaries_ok             : true
schema_version                 : atl-evomap-nightly-validation-v0.1
extended_by_phase              : ATL-EVOMAP-9B
git_commit                     : 7811e1b
summary                        : {"blocking_total":9,"passed":9,"failed":0,"non_blocking":1}
```

生成文件:

- `cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-smoke/nightly-validation-digest.json`
- `cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-smoke/nightly-validation-digest.md`
- `cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-smoke/nightly-validation-run.log`
- `cases/evomap-evolver-openclaw-v0/phase9b-curator-nightly-integration/artifacts/nightly-9b-smoke-summary.json`
  (由本报告附加脚本生成,固化 smoke 结果摘要)

## 9. Digest schema changes

新增顶层字段:

```jsonc
{
  "extended_by_phase": "ATL-EVOMAP-9B",
  "bundle_checks": {
    "inspect":   [ { "id": "...", "path": "...", "returncode": 0, "status": "PASS" }, ... ],
    "validate":  [ { "id": "...", "path": "...", "returncode": 0, "status": "PASS" }, ... ]
  },
  "canary_bundle_checks": [
    {
      "id": "sample-safe-bundle-phase9a",
      "source_phase": "ATL-EVOMAP-9A",
      "path": "cases/.../phase9a-bundle-curator-skill/generated/sample-safe-bundle.bundle.json",
      "lane": "curator_generated",
      "blocking": false,
      "expected_status": "CANARY_PASS",
      "target_runtime": "/tmp/atl-evomap-nightly-canary-sample-safe-bundle-phase9a",
      "inspect":   { "status": "PASS", "returncode": 0 },
      "validate":  { "status": "PASS", "returncode": 0 },
      "apply_dry_run": { "status": "PASS", "returncode": 0, "apply_json_reason": "ok", "target_runtime": "..." },
      "status": "CANARY_PASS"
    }
  ],
  "canary_summary": {
    "total": 1, "passed": 1, "failed": 0,
    "blocking_failures": 0, "non_blocking_failures": 0,
    "status": "CANARY_PASS"
  },
  "validators": [
    { "id": "phase5_local_evolution_kit",      "returncode": 0, "status": "PASS", "stdout_tail": "...", "stderr_tail": "" },
    { "id": "phase6a_hermes_systemd_bundle",   "returncode": 0, "status": "PASS", "stdout_tail": "...", "stderr_tail": "" },
    { "id": "phase6b_telegram_router_bundle",  "returncode": 0, "status": "PASS", "stdout_tail": "...", "stderr_tail": "" },
    { "id": "phase6c_codex_test_failure_bundle","returncode": 0, "status": "PASS", "stdout_tail": "...", "stderr_tail": "" },
    { "id": "phase7a_domain_signal_injection", "returncode": 0, "status": "PASS", "stdout_tail": "...", "stderr_tail": "" },
    { "id": "phase7b_cross_bundle_regression", "returncode": 0, "status": "PASS", "stdout_tail": "...", "stderr_tail": "" },
    { "id": "phase9a_bundle_curator_skill",    "returncode": 0, "status": "PASS", "stdout_tail": "...", "stderr_tail": "" }
  ],
  "checks": [
    /* 9 blocking + 1 non-blocking canary row, unchanged schema for each */
  ]
}
```

`checks[]` 不变(每条仍是 `{check_id, status, blocking, detail, extra}`)。
9 个 blocking check `check_id` 保持 8A 不变,新增第 10 条
`canary_bundles_checked`(`blocking=false`)。

## 10. Safety boundaries

| Boundary | State |
|----------|-------|
| Hub connection | **NO** — A2A_HUB_URL 未设置,subprocess env 强制空 |
| Hub URL config | **NO** — 未写入任何 hub URL 配置 |
| evolver run | **NO** — 未调用 `evolver run` |
| evolver review | **NO** — 未调用 `evolver review` |
| evolver review --approve | **NO** |
| evolver solidify | **NO** |
| auto-publish | **NO** |
| credit consumption | **NO** — credits=0 |
| ATP autobuy | **NO** — atp_autobuy=off |
| real cron install | **NO** — 未写入任何 crontab |
| systemd timer create | **NO** |
| network calls | **NO** — 无 curl/wget/HTTP |
| Telegram API | **NO** |
| online coding APIs (OpenAI/Codex/Copilot) | **NO** |
| real test runners (pytest/npm/cargo/go/mvn) | **NO** |
| real credentials read | **NO** — 无 API key/token/cookie/Authorization/private key |
| .env file content scan | **NO** — secret_scan 命中 `.env` 路径立即 FAIL |
| evolver package source modified | **NO** |
| runtime .evolver/ or memory/ tracked | **NO** — git_hygiene check 保证 |
| stdlib-only | **YES** |

`secret_scan_clean`:scanned=333 files, hits=0, allowed_timestamp_hits=21,
binary-skipped=85(防御性跳过)。

`git_hygiene`:418 tracked files clean, 0 个 root-level `.evolver/` /
`memory/` 路径;`git status --short` 仅显示本 phase 新增/修改的产物。

## 11. Final conclusion

✅ **Phase 9B Curator-to-Nightly Integration smoke PASS**。

- 4 canonical bundles 全部 inspect + validate PASS(阻塞检查);
- 1 curator-generated canary bundle inspect + validate + apply_dry_run 全 PASS;
- canary 失败时不使 overall_status FAIL(默认 non-blocking);
- 7 phase validators(5, 6A, 6B, 6C, 7A, 7B, 9A)ALL CHECKS PASSED;
- 9 blocking checks 全 PASS,overall_status=PASS;
- secret_scan=0 hits;
- git_hygiene clean;
- 所有 hard boundaries 保持;
- 未安装任何 cron / systemd timer;
- 未连接 Hub、未消耗 credits、未 approve / solidify、未 publish;
- 未运行 evolver run / review;
- 未读 .env、未读真实凭据;
- Python stdlib only;
- Dry-run target 仅为 `/tmp/atl-evomap-nightly-canary-*`(隔离)。

适合继续 Phase 9C(curator-driven canary apply + operator gate)或
Phase 8B(operator-led real cron install)。

## 12. Next steps

1. **Phase 9C (proposed)** — curator-driven canary apply,需要 operator
   gate(独立 cron / 人工批准),仍不允许 auto-publish / Hub / credits。
2. **Phase 8B (separate, operator-led)** — 真实 cron install。本 phase
   只 ship `templates/cron.example`,**未安装**。
3. **browser-control bundle (proposed)** — 加第 5 个 canonical bundle,
   覆盖 browser-control 失败模式。
4. **second curator-generated canary** — 真实跑 9A curator 生成多个 draft
   bundle,确认 canary lane 能并发处理多个 entry。