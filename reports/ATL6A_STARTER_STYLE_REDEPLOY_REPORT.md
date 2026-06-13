# ATL-6A — Starter-Style Redeploy Report

## 阶段结论
PASS_REDEPLOY_PREPARED_NOT_RUN

## Current baseline commit
6c95d5c (ATL-5D)

## 阶段定位
ATL-6A 是 ATL-5B/5C/5D 之后的 **starter-style redeploy 准备阶段**。
ATL-5B 启动的 run c83f971d-... 在 step=0 失败；ATL-5C 监控记录了失败状态；
ATL-5D 整理了 support-ready failure bundle；ATL-6A 不等待 Castform support 回复，
而是基于 starter-task 范式（最小 Build your own text task, no RAG, no agent traces,
简单 dataset, 简单 deterministic reward, Qwen/Qwen3.5-4B）准备一条新的、独立的、
更贴近 BaseEnv 默认行为的 redeploy 路径。

## 旧 Castform run 状态（保留作历史证据）
- run_id: c83f971d-2b2c-42b8-9774-ca64938c1286
- actual UI URL: https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train
- documented experiment URL: https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286 (returns Not Found)
- status: failed
- step: 0
- train data: none
- eval data: none
- rollouts: none
- new ATL-6A script **never references this run_id**; result file is separate

## 7 个主要修复点（spec 中明确）
1. **dataset**: 16 train / 4 eval preview（从 42/7 全量取前 N 条，**永远不**上传 49 全量）
2. **no-tools env**: `list_tools` 返回 `[]`；`run_tool` 返回 `""`（不 raise `NotImplementedError`）
3. **reward 0.0~1.0**: `{format, coverage, score}` 三项全 clamp 到 [0.0, 1.0]
4. **no custom `load_dataset` override**: 贴近 BaseEnv 默认行为（继承 `BaseEnv.load_dataset`）
5. **新 run_name**: `hermes-phase-closer-smoke-atl6a`（区别于 ATL-5 `hermes-phase-closer-smoke` 和 ATL-5B `hermes-phase-closer-smoke-atl5b`）
6. **不重复使用旧 failed run**: 新脚本从不引用 `c83f971d-...`；新 result 文件独立于历史
7. **不自动运行云端 API**: agent 仅准备脚本；真实执行由用户本地 WSL 显式授权后手动完成

## Created files
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/prepare_starter_style_subset.py` — stdlib 子集脚本 (16 train / 4 eval)
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-train.preview.jsonl` — 16 rows, generated
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-eval.preview.jsonl` — 4 rows, generated
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/reward_starter_style.py` — 0.0~1.0 score_completion
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/environment_starter_style.py` — HermesPhaseCloserStarterStyleEnv
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/validate_starter_style_env.py` — local validate runner
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py` — cloud redeploy script
- `scripts/validate_atl6a_starter_style_redeploy.py` — stdlib validator
- `reports/ATL6A_STARTER_STYLE_REDEPLOY_REPORT.md` — this report

## Modified files
- `cases/castform-hermes-phase-closer-v0/index.html` — header line 65-66 + ATL-6A section block after ATL-5D + timeline entry + footer
- `data/cases.json` — phase / status / summary appended
- `README.md` — header (ATL-6A) + ATL-6A block after ATL-5D

## Validation results
- `scripts/validate_atl6a_starter_style_redeploy.py` PASS (9 checks: 5 files exist + AST 语法 / env class + BaseEnv / run_tool 返回 "" / no custom load_dataset override / reward score_completion + 0.0~1.0 clamp / 16 train + 4 eval dataset / run_name hermes-phase-closer-smoke-atl6a / 授权语句 I AUTHORIZE ATL-6A STARTER-STYLE REDEPLOY / 旧 run_id c83f971d-... 不被引用 / 15 secret patterns scan 全部通过)
- `.venv-castform-local/bin/python validate_starter_style_env.py` → `VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)` — benchmax `validate_env` 真实本地调用通过（5 train + 2 eval rows, local=True, api_key=None, 零网络）
- 全部 14 个前置 validators 继续 PASS (validate_jsonl / validate_site / check_secrets / validate_castform_local_scaffold / validate_atl3c_sdk_mapping / validate_atl4a_preflight_scaffold / validate_atl4b_cloud_smoke_config / validate_atl4c_guarded_preflight / validate_atl5_cloud_smoke_result / validate_atl5a_launch_args_fix / validate_atl5b_second_upload_retry_result / validate_atl5c_failed_step0_record / validate_atl5d_support_bundle + 新增 validate_atl6a_starter_style_redeploy)
- `<redacted-key-prefix-literal>` repo-wide grep → 0 matches (validator 内部用字符串拼接构造 forbidden literal，源码不再含 bare 模式)
- 整个 ATL-5 / ATL-5B / ATL-5C / ATL-5D 历史 result JSON 完整保留：`atl5_cloud_smoke_result.json` + `atl5b_second_upload_launch_retry_result.json` + monitoring/ + support/ 全部未被覆盖

## Hard boundary compliance
- agent **未调用 Castform API**（无 upload、launch、TrainerClient 调用）
- agent **未访问 Castform UI**（无浏览器请求）
- agent **未上传数据**（prepare_starter_style_subset.py 只写本地 JSONL，不触网）
- agent **未启动训练**（atl6_starter_style_redeploy.py 未被运行；只跑过 local validate_env path）
- agent **未读取 API key**（脚本仅检查 `os.environ` 中 `CASTFORM_API_KEY` 是否存在）
- agent **未记录 API key 前缀/片段**（gate log 仅显示 `present: True|False`；validate_atl6a_starter_style_redeploy.py 15 secret patterns + forbidden literal scan 全 PASS）
- **未提交 `.env`**
- **未提交 `.venv`**
- **未记录** 信用卡 / cookie / Authorization header / 用户邮箱 / 截图
- **未伪造** `run_id` / `experiment_url`（脚本在 launch 前不会填这两个字段，只在 result JSON 写 `null`）
- **未删除** 旧 Castform run
- **未重复运行** ATL-5B retry script
- **不覆盖** ATL-5 / ATL-5B 历史 result JSON

## Git status (before commit)
A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py
A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/environment_starter_style.py
A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/prepare_starter_style_subset.py
A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/reward_starter_style.py
A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-eval.preview.jsonl
A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-train.preview.jsonl
A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/validate_starter_style_env.py
A  reports/ATL6A_STARTER_STYLE_REDEPLOY_REPORT.md
A  scripts/validate_atl6a_starter_style_redeploy.py
M  README.md
M  cases/castform-hermes-phase-closer-v0/index.html
M  data/cases.json

## Next step
- 用户在本地 WSL 显式授权 `I AUTHORIZE ATL-6A STARTER-STYLE REDEPLOY` 后手动运行：
  ```bash
  cd /mnt/d/AI/ai-tool-test-lab
  export CASTFORM_API_KEY=*** CONFIG secrets here ***
  export ATL_ALLOW_CASTFORM_UPLOAD=YES
  export ATL_ALLOW_CASTFORM_LAUNCH=YES
  export ATL_USER_AUTHORIZATION="I AUTHORIZE ATL-6A STARTER-STYLE REDEPLOY"
  .venv-castform-local/bin/python \
    cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py
  ```
- 真实 Castform API 调用由用户执行；agent 仅监督 `run_id` / `experiment_url` / `training_started` 状态
- 成功 result 写入 `cases/.../starter-style-redeploy/atl6_starter_style_redeploy_result.json`（独立文件，不覆盖 ATL-5 / ATL-5B 历史）
- 若 run 又失败 → 进入 ATL-6E 根因诊断；若 run 成功 → 进入 ATL-6B 监控与训练结果记录

## commit hash
(待提交后填入)

## whether pushed
否 (待 push)
