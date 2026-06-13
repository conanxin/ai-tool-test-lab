# ATL-5A — Upload Succeeded, Launch Failed, Args Fixed Report

**Date**: 2026-06-13
**Phase**: ATL-5A
**Status**: **UPLOAD_SUCCEEDED_LAUNCH_FAILED_ARGS_FIXED**
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Baseline**: `03dc55b` (ATL-5-SCRIPT-PREP)

## 阶段结论

`UPLOAD_SUCCEEDED_LAUNCH_FAILED_ARGS_FIXED` — ATL-5 首次 cloud smoke run 部分成功：upload 成功，但 launch 因 `batch_size` 参数被拒绝。本阶段修复 launcher_args，增强脚本保存 uploaded_payload，准备 ATL-5B retry。

## ATL-5 首次运行结果

| 步骤 | 结果 |
|------|------|
| local validate_env | **PASS** (`VALIDATE_ENV_LOCAL_PASS`) |
| upload | **SUCCEEDED** (dataset uploaded to Castform) |
| launch | **FAILED** (`JobLaunchError: Unknown launch arg: "batch_size"`) |

## 失败原因

Castform 不接受 `batch_size` 作为 launcher arg。用户已查询 Castform 当前 accepted launch args：

- **Accepted**: `model`, `learning_rate`, `num_epochs`, `group_size`, `max_rollout_len`, `max_turns`, `lora_rank`, `lora_alpha`
- **Rejected**: `batch_size`

## 修复内容

### 1. launcher_args 修正

删除 `batch_size`，增加 `learning_rate: 1e-5`。

修复后：
```json
{
  "model": "Qwen/Qwen3.5-4B",
  "learning_rate": 1e-5,
  "num_epochs": 1,
  "group_size": 2,
  "max_rollout_len": 512,
  "max_turns": 1,
  "lora_rank": 16,
  "lora_alpha": 32
}
```

### 2. uploaded_payload 保存增强

`atl5_cloud_smoke_run.py` 现在在 upload 成功后保存 `dataclasses.asdict(uploaded)` 的 sanitized 子集到 result JSON：
- `env_cls_path`
- `env_metadata_path`
- `train_dataset_path`
- `eval_dataset_path`
- `run_name`
- `run_id`

不包含 API key、Authorization header、cookie 等敏感信息。

## 创建文件

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/ATL5A_LAUNCH_ARGS_FIX_NOTES.md` — 详细修复记录
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_retry_guard.py` — ATL-5B 二次 upload + launch 脚本

## 修改文件

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5_cloud_smoke_run.py` — 修复 launcher_args，增加 uploaded_payload 保存
- `cases/castform-hermes-phase-closer-v0/index.html` — 增加 ATL-5A 模块，更新 ATL-5 运行结果
- `data/cases.json` — phase = `ATL-5A upload succeeded launch failed args fixed`，status = `upload succeeded, launch failed, args fixed, ATL-5B retry ready`
- `README.md` — 顶部状态切换到 ATL-5A，增加 ATL-5 运行结果和 ATL-5A 交付说明

## 验证结果

- `validate_jsonl.py` **PASS**
- `validate_site.py` **PASS**
- `check_secrets.py` **PASS**
- `validate_castform_local_scaffold.py` **PASS**
- `validate_atl3c_sdk_mapping.py` **PASS**
- `validate_atl4a_preflight_scaffold.py` **PASS**
- `validate_atl4b_cloud_smoke_config.py` **PASS**（修改后仍通过，不扫描 live/ 子目录）
- `validate_atl4c_guarded_preflight.py` **PASS**（59/59 OK）
- `validate_atl5_cloud_smoke_result.py` **PASS**（placeholder JSON 合法，无 secret，train=8，eval=2）

## 明确边界声明

- **未调用 Castform API**（agent 未执行 atl5_cloud_smoke_run.py 或 atl5b_second_upload_retry_guard.py）
- **未上传任何数据**
- **未启动 Castform training run**
- **未读取 API key**
- **未记录 API key**
- **未创建 .env**
- **未提交 .venv-castform-local**
- **未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图**
- **未运行 atl5_cloud_smoke_run.py**（agent 阶段不执行）
- **未运行 atl5b_second_upload_retry_guard.py**（agent 阶段不执行）
- **未伪造 launch 成功**
- **dataset_uploaded 保持 true**（第一次 upload 成功）
- **training_started 保持 false**（第一次 launch 失败）

## 已知限制

1. **upload metadata 缺失** — 第一次运行结果 JSON 中没有 `uploaded_payload`。因此不能只做 launch retry，必须重新 upload + launch。
2. **billing / auto-charge / cost estimate / run controls / data policy 仍多项 UNKNOWN** — 从 ATL-4A-CREDIT-FILL 继承。
3. **用户声明不考虑付费、没有绑卡** — 如果 Castform 要求绑卡或付费，upload/launch 会失败。
4. **preview subset 仍为 8 train / 2 eval** — 未扩大数据集。

## git 状态

- `git status --short`: 干净（本阶段 commit 后）
- 预期 commit 列表：
  1. `atl5_cloud_smoke_run.py` 修改（launcher_args 修复 + uploaded_payload 保存）
  2. `ATL5A_LAUNCH_ARGS_FIX_NOTES.md` 新增
  3. `atl5b_second_upload_retry_guard.py` 新增
  4. `index.html` 修改
  5. `data/cases.json` 修改
  6. `README.md` 修改
  7. `ATL5A_UPLOAD_SUCCEEDED_LAUNCH_FAILED_ARGS_FIXED_REPORT.md` 新增

## 下一步

ATL-5B — 用户手动运行：

```bash
cd /mnt/d/AI/ai-tool-test-lab
.venv-castform-local/bin/python cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_retry_guard.py
```

需显式授权：`I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY`

运行后，agent 将进入 ATL-5B-RESULT 阶段：读取 `atl5_cloud_smoke_result.json`，更新页面、cases.json、README 和报告。

## 风险评估

- **无新风险** — 本阶段 agent 未执行任何 API 调用、未上传、未训练。
- **遗留风险**：billing / auto-charge / cost visibility 仍多项 UNKNOWN；用户声明不考虑付费、没有绑卡，若 Castform 要求绑卡则 upload/launch 会失败。
- **ATL-5B 风险**：二次 upload + launch 仍可能因 billing/credit/quota 或其他原因失败。
