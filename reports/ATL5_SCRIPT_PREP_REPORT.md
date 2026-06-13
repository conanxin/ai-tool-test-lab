# ATL-5-SCRIPT-PREP — Live Script Preparation Report

**Date**: 2026-06-13
**Phase**: ATL-5-SCRIPT-PREP
**Status**: **SCRIPT_READY_NO_CLOUD_CALL**
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Baseline**: `0652bb1` (ATL-4C) · `68fb302` (ATL-4A-CREDIT-FILL) · `b364bb7` (ATL-4B-CONFIG)

## 阶段结论

`SCRIPT_READY_NO_CLOUD_CALL` —— ATL-5 live cloud smoke run 脚本已准备，但 agent 未执行。用户将在本地 WSL shell 中手动运行。

## 创建文件

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5_cloud_smoke_run.py` — ATL-5 live cloud smoke run 脚本
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5_cloud_smoke_result.json` — placeholder（status = SCRIPT_READY_NO_CLOUD_CALL）
- `scripts/validate_atl5_cloud_smoke_result.py` — ATL-5 结果验证器
- `scripts/validate_atl4b_cloud_smoke_config.py` — 修改（限制扫描范围，不扫描 ATL-5 live/ 子目录）

## 修改文件

- `cases/castform-hermes-phase-closer-v0/index.html` — 增加 ATL-5-SCRIPT-PREP 模块
- `data/cases.json` — phase = `ATL-5-SCRIPT-PREP live script ready`，status = `live script ready; cloud smoke run pending user execution`
- `README.md` — 顶部状态切换到 ATL-5-SCRIPT-PREP

## 脚本架构（atl5_cloud_smoke_run.py）

```
Gate 检查
  → 数据集检查（8 train / 2 eval）
  → 本地 validate_env（ATL-3C HermesPhaseCloserLocalEnv，local=True，api_key=None）
  → upload_training_run（env + dataset → Castform）
  → TrainerClient.launch_training_run（Qwen/Qwen3.5-4B · 1 epoch · batch_size=2 · group_size=2 · max_turns=1 · lora_rank=16）
  → 结果 JSON（不含 secret）
```

### Gate 检查

- `CASTFORM_API_KEY` present
- `ATL_ALLOW_CASTFORM_UPLOAD` == "YES"
- `ATL_ALLOW_CASTFORM_LAUNCH` == "YES"
- `ATL_USER_AUTHORIZATION` == "I AUTHORIZE ATL-5 CLOUD SMOKE RUN"

### 异常分类

- billing/credit/quota → `BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT`
- upload 成功但 launch 失败 → `UPLOAD_DONE_LAUNCH_FAILED`
- 其他 upload 失败 → `UPLOAD_FAILED`
- 其他 launch 失败 → `LAUNCH_FAILED`

### 结果 JSON 字段

- `phase`: "ATL-5"
- `status`: "PASS_CLOUD_SMOKE_LAUNCHED" / "UPLOAD_DONE_LAUNCH_FAILED" / "BLOCKED_BY_*" / "FAILED_*"
- `local_validate_env_result`: "VALIDATE_ENV_LOCAL_PASS" / "..."
- `upload_attempted`: true/false
- `upload_succeeded`: true/false
- `launch_attempted`: true/false
- `launch_succeeded`: true/false
- `run_id`: "..." or null
- `experiment_url`: "https://app.castform.com/experiments/{run_id}" or null
- `base_model`: "Qwen/Qwen3.5-4B"
- `train_samples`: 8
- `eval_samples`: 2
- `api_key_recorded`: false（永远 false）
- `dataset_uploaded`: true/false
- `training_started`: true/false
- `error_category`: "..." or null
- `error_summary`: "..." or null

## 验证结果

- `validate_jsonl.py` **PASS**（42 train / 7 eval）
- `validate_site.py` **PASS**
- `check_secrets.py` **PASS**
- `validate_castform_local_scaffold.py` **PASS**
- `validate_atl3c_sdk_mapping.py` **PASS**
- `validate_atl4a_preflight_scaffold.py` **PASS**
- `validate_atl4b_cloud_smoke_config.py` **PASS**（修改后仍通过，不扫描 live/ 子目录）
- `validate_atl4c_guarded_preflight.py` **PASS**（59/59 OK）
- `validate_atl5_cloud_smoke_result.py` **PASS**（placeholder JSON 合法，无 secret，train=8，eval=2）

## 明确边界声明

- **未调用 Castform API**（agent 未执行 atl5_cloud_smoke_run.py）
- **未上传任何数据**
- **未启动 Castform training run**
- **未读取 API key**（agent 不知道 CASTFORM_API_KEY 的值）
- **未记录 API key**（无 .env，无文件写入）
- **未创建 .env**
- **未提交 .venv-castform-local**
- **未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图**
- **未运行 atl5_cloud_smoke_run.py**（agent 阶段不执行）
- **未伪造 ATL-5 run result**（placeholder JSON 明确标记 SCRIPT_READY_NO_CLOUD_CALL）

## 已知限制

1. **脚本未执行** —— 所有 cloud 行为均为理论设计，未经实际验证。
2. **billing / auto-charge / cost estimate / run controls / data policy 仍多项 UNKNOWN** —— 从 ATL-4A-CREDIT-FILL 继承。
3. **用户声明不考虑付费、没有绑卡** —— 如果 Castform 要求绑卡或付费，upload/launch 会失败。
4. **preview subset 仍为 ATL-2 redacted JSONL 的前 N 行** —— 8 train / 2 eval。
5. **ATL-4B validator 扫描范围已限制** —— 不扫描 live/ 子目录，避免误报 ATL-5 脚本中的官方 SDK 调用。

## git 状态

- `git status --short`: 干净（本阶段 commit 后）
- 预期 commit 列表：
  1. `cloud-smoke-run/live/` 目录（2 个新文件）
  2. `scripts/validate_atl5_cloud_smoke_result.py`（新）
  3. `scripts/validate_atl4b_cloud_smoke_config.py`（修改）
  4. `cases/castform-hermes-phase-closer-v0/index.html`（修改）
  5. `data/cases.json`（修改）
  6. `README.md`（修改）
  7. `reports/ATL5_SCRIPT_PREP_REPORT.md`（新）

## 下一步

用户在本地 WSL shell 中运行：

```bash
cd /mnt/d/AI/ai-tool-test-lab
.venv-castform-local/bin/python cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5_cloud_smoke_run.py
```

运行后，agent 将进入 ATL-5-RESULT 阶段：读取 `atl5_cloud_smoke_result.json`，更新页面、cases.json、README 和报告。

## 风险评估

- **无新风险** —— 本阶段 agent 未执行任何 API 调用、未上传、未训练。
- **遗留风险**：billing / auto-charge / cost visibility / run controls / data policy 仍多项 UNKNOWN。
- **用户声明不考虑付费、没有绑卡** —— 如果 Castform 要求绑卡，upload/launch 将失败。
