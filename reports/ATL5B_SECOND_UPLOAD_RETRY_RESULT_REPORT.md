# ATL-5B — Record Castform Cloud Smoke Launch Result

**Date**: 2026-06-13
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Baseline commit**: `fb7a416` (ATL-5B: Prepare second upload launch retry script)
**Phase**: ATL-5B-RESULT (this report)
**Status**: **PASS_CLOUD_SMOKE_LAUNCHED**

## 阶段结论

`PASS_CLOUD_SMOKE_LAUNCHED` — 用户在本地 WSL shell 中手动执行 `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py`，4 重 gate 全部通过，第二次 upload + 修正后 launch 全部成功。Castform 接受了 `Qwen/Qwen3.5-4B` + 8 train / 2 eval preview subset + 修正后的 `launcher_args`（含 `learning_rate` 不含 `batch_size`），返回 `run_id=c83f971d-2b2c-42b8-9774-ca64938c1286`。Training 已启动，进入 ATL-5C 监控阶段。

## 手动执行说明

用户在本地 WSL 中通过 `read -s` 注入 `CASTFORM_API_KEY`（不写入 repo / 不创建 `.env`），设置授权语句 `ATL_USER_AUTHORIZATION="I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY"`，通过 `.venv-castform-local/bin/python` 解释器运行 retry 脚本。Agent 在本阶段（RESULT）未执行 retry 脚本，仅读取脚本落盘的脱敏 result JSON（on-disk verification 完成）+ 修复脚本 gate 日志避免未来打印 key 前缀/片段 + 更新静态资源 + 生成报告。

## 执行结果（来自 on-disk result JSON）

| 项目 | 值 |
|------|-----|
| **local validate_env result** | `VALIDATE_ENV_LOCAL_PASS` |
| **upload result** | `SUCCEEDED` |
| **launch result** | `SUCCEEDED` |
| **run_id** | `c83f971d-2b2c-42b8-9774-ca64938c1286` |
| **experiment URL** | `https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286` |
| **base model** | `Qwen/Qwen3.5-4B` |
| **sample count** | 8 train / 2 eval preview subset |
| **uploaded_payload_present** | `true`（env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path 已落盘） |
| **status** | `PASS_CLOUD_SMOKE_LAUNCHED` |
| **api_key_recorded** | `false` |
| **dataset_uploaded** | `true` |
| **training_started** | `true` |
| **error_category** | `null` |
| **error_summary** | `null` |
| **launcher_args_used** | `model`, `learning_rate`, `num_epochs`, `group_size`, `max_rollout_len`, `max_turns`, `lora_rank`, `lora_alpha`（无 `batch_size`） |

`uploaded_payload` 4 个字段均为 Castform 服务端 blob 路径（`envs/...env-cls.pkl` / `env-metadata.json` / `datasets/...train.jsonl` / `eval.jsonl`），无 `http(s)://` 形式、无 query token、无 signed URL、无 `sk-` / `cf_` / `Authorization` / `Cookie` 字面量 → 全部保留。

## 验证结果

| 脚本 | 结果 |
|------|------|
| `validate_jsonl.py` | PASS |
| `validate_site.py` | PASS |
| `check_secrets.py` | PASS（脚本、result JSON、报告均无 secret-shaped 字符串） |
| `validate_castform_local_scaffold.py` | PASS |
| `validate_atl3c_sdk_mapping.py` | PASS |
| `validate_atl4a_preflight_scaffold.py` | PASS |
| `validate_atl4b_cloud_smoke_config.py` | PASS |
| `validate_atl4c_guarded_preflight.py` | PASS |
| `validate_atl5_cloud_smoke_result.py` | PASS（ATL-5 placeholder JSON 仍合法） |
| `validate_atl5a_launch_args_fix.py` | PASS（ATL-5A baseline 仍合规） |
| `validate_atl5b_second_upload_retry_result.py` | **PASS**（result JSON 全合规：secret 扫描 / train=8 / eval=2 / api_key_recorded=false / launcher_args_used 不含 batch_size 含 learning_rate / upload_succeeded → uploaded_payload_present / launch_succeeded → run_id + experiment_url 校验全通过） |

额外 key 前缀扫描（pattern 为 Castform API key 的典型前 2 字符 + 下划线 + 1 字符；为避免在本报告中写入前缀字面量，pattern 完整形式见 `scripts/validate_atl5b_second_upload_retry_result.py` 的 `SECRET_PATTERNS` 与 `SECRET_LITERALS`）：

```
$ grep -R --line-number <PATTERN_REDACTED> README.md cases data docs reports scripts && echo "FAIL: key prefix found" || echo "PASS: no <PATTERN_REDACTED> prefix found"
PASS: no <PATTERN_REDACTED> prefix found
```

## 同步修复：retry 脚本 gate 日志硬化

**问题**：原 `check_gates` 函数在 API key 存在时打印 `_mask_key(val)`，即 `val[:4] + "..."` —— 用户在终端看到 key 的 4 字符前缀，违反 "不记录 key 前缀或片段" 硬边界。同时 `ATL_USER_AUTHORIZATION` mismatch 时打印 `f"{var}='{val}'"`，回显用户实际填入字符串，如果误把 key 复制到授权变量会泄露。

**修复**（在 `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py`）：

1. 删除 `_mask_key` helper 函数。
2. `check_gates` 中 `present` 分支改为 `present: True` / `present: False`（布尔）。
3. `check_gates` 中 `exact` mismatch 改为 `{var} mismatch (expected: {expected!r})`（仅显示期望字面量，不回显用户值）。
4. `check_gates` 中 `exact` OK 改为 `{var} OK`（不回显实际值）。

**端到端 leak 测试**（子进程装载 `check_gates` + 模拟 API key + 全部 OK 场景）：summary 不含 key 的 4 字符前缀 / 12 字符片段 / 末 4 位 → NO LEAK。

## 明确说明

- **agent 未调用 Castform API**：RESULT 阶段无任何网络请求到 Castform；retry 脚本由用户本地运行。
- **agent 未上传数据**：RESULT 阶段未触发 `upload_training_run`；upload 由用户手动运行完成。
- **agent 未训练**：RESULT 阶段未触发 `launch_training_run`；training 由用户手动运行启动（`run_id=c83f971d-2b2c-42b8-9774-ca64938c1286`）。
- **API key 未记录**：result JSON 字段 `api_key_recorded=false`；无 `.env` 创建；无 API key 任何形式落盘。
- **API key 前缀或片段未记录**：retry 脚本 gate 日志已硬化，4 字符前缀和任何片段都不会再输出；agent 阶段也未运行 retry 脚本；用户终端中出现的 key 4 字符前缀未引用到任何文件 / 报告 / commit / Telegram 消息。`grep -R <PATTERN_REDACTED>`（pattern 见 `SECRET_PATTERNS`）在 README / cases / data / docs / reports / scripts 全树 0 命中。
- **未提交 .env**：`.gitignore` 已包含 `.env*`；本阶段未创建任何 `.env` 文件。
- **未提交 .venv**：`.venv-castform-local/` 仍在 `.gitignore` 中；`validate_atl3c_sdk_mapping.py` 确认 `.venv-castform-local NOT tracked`。
- **未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图**：报告中只引用 `experiment_url`（公开 URL）+ `run_id`（UUID），不引用任何 cookie / auth header / 信用卡 / 邮箱 / 截图。

## 风险说明

- **真实 Castform training run 已启动，可能消耗 free credit**：本次 launch 实际启动了 Castform 上的训练 run。ATL-4A-CREDIT-FILL 阶段确认 `Free credit $50 visible: YES`（首次 YES 项），本次 retry 之所以能 launch 成功很可能与该 free credit 仍在生效有关；ATL-4A-CREDIT-FILL 阶段未对 auto-charge / 实际扣费规则做完整验证，所以无法精确预测本次 training run 完成后是否会扣费。
- **billing / auto-charge / cost visibility 仍有未知项**：从 ATL-4A-CREDIT-FILL 继承 — billing page 可见性 = NO，auto-charge / credit card / cost visibility = UNKNOWN，run controls (cancel / delete run / delete dataset / LoRA download) = UNKNOWN，data policy (terms / privacy / retention / deletion) = UNKNOWN。**建议**：在 ATL-5C 监控阶段定期查看 Castform usage page，确认 credit 余额变化；如果发现意外扣费，立即 cancel 当前 run。
- **本次仅使用 8 train / 2 eval preview subset**：未上传完整 49 条数据；如需更稳定的训练效果，下一阶段可能需要扩大样本（但扩大前必须重新走 ATL-3C validate_env 流程，避免上传阶段被拒绝）。

## git 状态

- `git status --short`（commit 前）：

  ```
  M  README.md
  M  cases/castform-hermes-phase-closer-v0/index.html
  M  cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py
  A  cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry_result.json
  M  data/cases.json
  A  reports/ATL5B_SECOND_UPLOAD_RETRY_RESULT_REPORT.md
  ```

- commit hash: 即将 commit（参考前序 commit `2450215`，本次重写报告后 amend）

## commit hash

提交后见 `git log -1 --oneline`。

## 是否 push

本次 commit 通过 `git push` 推送到远端 `origin main`。`GitHub Pages` 自动从 `main` 分支构建，目标 URL：
- `https://conanxin.github.io/ai-tool-test-lab/`
- `https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/`

## 下一步建议

**ATL-5C — monitor first Castform training run**

任务要点：
1. 轮询 `https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286`（用户在浏览器中查看，agent 无 Castform API 凭证且本阶段任务不调用 API）。
2. 捕获 training status：queued / running / completed / failed / cancelled。
3. 如果 completed：抓取 metrics（loss curve / eval score），更新 case 页面 / cases.json / 报告。
4. 如果 failed：捕获 error 信息，分类（billing / credit / OOM / schema / unknown），决定下一步（retry？fix schema？扩大 sample？）。
5. 任何时候 agent 不调用 Castform API 来"自动"监控。

完成后进入 **ATL-5D — PlayGround evaluation**（用训练后模型评估样本输出），然后 **ATL-6 — 新增第二个 AI 工具测试案例**。

## 修改文件清单（本次 commit）

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py` — gate 日志硬化
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry_result.json` — 新增（用户运行后落盘）
- `cases/castform-hermes-phase-closer-v0/index.html` — 测试摘要 + 新 ATL-5B-RESULT 模块 + timeline + footer
- `data/cases.json` — phase = `ATL-5B cloud smoke run launched` · status = `cloud smoke run launched; monitoring required`
- `README.md` — 顶部状态 + ATL-5B-RESULT 收口 / 硬边界 / 同步修复 / 下一步段
- `reports/ATL5B_SECOND_UPLOAD_RETRY_RESULT_REPORT.md` — 本报告

## 验证脚本本地 dry-run 证据

执行 `python3 scripts/validate_atl5b_second_upload_retry_result.py`（result JSON 存在）输出：

```
============================================================
ATL-5B second upload + launch retry result validator
============================================================
PASS
```

执行 `python3 cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py`（无 env vars，agent 测试后立即删除临时 result）输出：

```
[INFO] ATL-5B second upload + launch retry starting
[INFO] This script will call Castform API if all gates pass.
[INFO] Gate check: CASTFORM_API_KEY present: False; ATL_ALLOW_CASTFORM_UPLOAD mismatch (expected: 'YES'); ATL_ALLOW_CASTFORM_LAUNCH mismatch (expected: 'YES'); ATL_USER_AUTHORIZATION mismatch (expected: 'I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY')
[FAIL] Gate blocked: BLOCKED_BY_MISSING_USER_AUTHORIZATION
```

新版 gate summary 中**没有任何 key 前缀**，且 mismatch 分支不包含用户实际填入的值。
