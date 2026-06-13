# ATL-5B Second Upload Retry Script Preparation Report

**Date**: 2026-06-13
**Phase**: ATL-5B-SCRIPT-PREP
**Status**: **SCRIPT_READY_NO_CLOUD_CALL**

## 阶段结论

`SCRIPT_READY_NO_CLOUD_CALL` — ATL-5B 第二次 upload + launch retry 脚本已准备。Agent 仅创建脚本、验证器、文档、页面更新和报告；未调用 Castform API，未上传任何数据，未启动训练，未读取或记录 API key。等待用户在本地 WSL shell 中显式授权后手动运行 retry 脚本。

## 当前基线

- commit: `9eab4ec` (ATL-5A: Fix Castform launch args schema, add validator, prepare ATL-5B retry)

## 为什么需要 ATL-5B

ATL-5 首次 cloud smoke run 部分成功：
- `local validate_env` PASS
- `upload_training_run` SUCCEEDED（dataset uploaded）
- `launch_training_run` FAILED (`JobLaunchError: Unknown launch arg: "batch_size"`)

原始 ATL-5 result JSON (`atl5_cloud_smoke_result.json`) **未保存 `uploaded_payload`**（env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path）。没有这些路径，launch-only retry 不可能。因此必须重新 upload + launch。

## 创建文件

- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py` — retry 脚本（4 重 gate · 8/2 preview · 本地 validate_env · 一次 upload · 落盘 uploaded_payload · 一次 launch · 修正后 launcher_args · 写入独立 result 文件 `atl5b_second_upload_launch_retry_result.json`，不覆盖 ATL-5 历史）
- `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/ATL5B_SECOND_UPLOAD_RETRY_NOTES.md` — 为什么需要 ATL-5B / batch_size 移除 / 授权语句 / 硬规则
- `scripts/validate_atl5b_second_upload_retry_result.py` — std-lib 验证器（无 result JSON → `SKIPPED_RESULT_NOT_PRESENT` exit 0；有 result JSON → 检查 secret / train=8 / eval=2 / api_key_recorded=false / launcher_args_used 不含 batch_size 含 learning_rate / 上传成功 → uploaded_payload_present 必须 true / launch 成功 → run_id 非空 + experiment_url 含 app.castform.com）
- `reports/ATL5B_SECOND_UPLOAD_RETRY_SCRIPT_PREP_REPORT.md` — 本报告

## 修改文件

- `cases/castform-hermes-phase-closer-v0/index.html` — 增加 ATL-5B-SCRIPT-PREP 模块
- `data/cases.json` — phase 和 status 更新到 ATL-5B
- `README.md` — 顶部状态切换到 ATL-5B-SCRIPT-PREP

## Corrected launcher_args

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

明确移除 `batch_size`（Castform 拒绝）。`learning_rate` 是 Castform 接受但 ATL-5 遗漏的参数。

## Gate 要求（4 重，全部必须满足）

| Env Var | Check | Expected |
|---------|-------|----------|
| `CASTFORM_API_KEY` | present | 任何非空值（脱敏 mask 输出 4 字符前缀） |
| `ATL_ALLOW_CASTFORM_UPLOAD` | exact | `YES` |
| `ATL_ALLOW_CASTFORM_LAUNCH` | exact | `YES` |
| `ATL_USER_AUTHORIZATION` | exact | `I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY` |

任一 gate 不满足 → 写入脱敏 result JSON，**不**调用 API，**不**上传，**不**训练，exit 1。

## 明确说明

- **agent 未调用 Castform API**：未运行 `atl5b_second_upload_launch_retry.py`；本地 dry-run 只验证 gate 拒绝分支，exit 1。
- **agent 未上传任何数据**：未触发 `upload_training_run`。
- **agent 未训练**：未触发 `launch_training_run`。
- **agent 未读取 API key**：脚本中 `os.environ["CASTFORM_API_KEY"]` 只在 gate 通过后才被读取（gate 通过 = 用户显式授权后），agent 阶段未通过 gate。日志输出用 `_mask_key` 仅显示 4 字符前缀。
- **agent 未记录 API key**：result JSON 字段 `api_key_recorded=false`；无 `.env` 创建；无 secret-shaped 字符串落盘（验证器已扫描）。

## 验证结果

| 脚本 | 结果 |
|------|------|
| `validate_jsonl.py` | PASS |
| `validate_site.py` | PASS |
| `check_secrets.py` | PASS |
| `validate_castform_local_scaffold.py` | PASS |
| `validate_atl3c_sdk_mapping.py` | PASS |
| `validate_atl4a_preflight_scaffold.py` | PASS |
| `validate_atl4b_cloud_smoke_config.py` | PASS |
| `validate_atl4c_guarded_preflight.py` | PASS |
| `validate_atl5_cloud_smoke_result.py` | PASS（ATL-5 placeholder JSON 仍合法） |
| `validate_atl5a_launch_args_fix.py` | PASS（ATL-5A baseline 仍合规） |
| `validate_atl5b_second_upload_retry_result.py` | `SKIPPED_RESULT_NOT_PRESENT`（script-prep 阶段 result JSON 尚未生成，exit 0） |

post-run 模式已用合成 result JSON 端到端测试：合规 → PASS；含 `batch_size` 或 `sk-*` → FAIL（带详细原因）。

## git 状态

- `git status --short`（commit 前）：见 commit 阶段输出
- 预期 commit 列表（per-file `git add`，**不**用 `git add .`）：
  1. `README.md`
  2. `cases/castform-hermes-phase-closer-v0/index.html`
  3. `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/`（含 retry script + notes doc）
  4. `data/cases.json`
  5. `reports/ATL5B_SECOND_UPLOAD_RETRY_SCRIPT_PREP_REPORT.md`
  6. `scripts/validate_atl5b_second_upload_retry_result.py`

## 下一步

用户在本地 WSL shell 中：

```bash
export ATL_USER_AUTHORIZATION=*** AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY"
export ATL_ALLOW_CASTFORM_UPLOAD="YES"
export ATL_ALLOW_CASTFORM_LAUNCH="YES"
read -s CASTFORM_API_KEY && export CASTFORM_API_KEY

cd /mnt/d/AI/ai-tool-test-lab
.venv-castform-local/bin/python cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py
python3 scripts/validate_atl5b_second_upload_retry_result.py
```

运行后，agent 将进入 ATL-5B-RESULT 阶段：读取 `atl5b_second_upload_launch_retry_result.json`，更新页面、cases.json、README 和报告（ATL-5B-RESULT_REPORT.md）。

## 风险评估

- **本阶段 agent 无新风险**：仅创建脚本、验证器、文档、页面和报告。
- **遗留风险**（继承自 ATL-4A-CREDIT-FILL）：billing / auto-charge / cost visibility / run controls / data policy 仍多项 UNKNOWN；用户声明不考虑付费、没有绑卡，若 Castform 要求绑卡则 upload/launch 会失败。
- **ATL-5B 运行风险**：即使 launch 再次失败，`uploaded_payload` 已落盘到独立 result JSON，可作为下一次 retry 的审计依据。
- **retry 脚本本地 dry-run 证据**：执行 `python3 cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py`（无 env vars）→ exit 1，gate 拒绝分支产生脱敏 result JSON（status=`BLOCKED_BY_MISSING_USER_AUTHORIZATION`），未触发任何上传或训练。测试 result JSON 已清理。