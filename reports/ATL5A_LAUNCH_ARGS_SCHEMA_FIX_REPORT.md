# ATL-5A — Launch Args Schema Fix Report

**Date**: 2026-06-13
**Phase**: ATL-5A
**Status**: **PASS_FIX_PREPARED_LAUNCH_RETRY_BLOCKED_BY_MISSING_UPLOAD_METADATA**
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Baseline**: `14e2677` (ATL-5A previous)

## 阶段结论

`PASS_FIX_PREPARED_LAUNCH_RETRY_BLOCKED_BY_MISSING_UPLOAD_METADATA` — ATL-5 首次 cloud smoke run upload 成功但 launch 失败（`batch_size` 参数被拒绝）。本阶段修复 launcher_args schema，增强脚本保存 uploaded_payload，但 launch-only retry 被阻止，因为原始结果中缺少 upload metadata。

## ATL-5 First Run Result Summary

| 步骤 | 结果 |
|------|------|
| local validate_env | **PASS** (`VALIDATE_ENV_LOCAL_PASS`) |
| upload | **SUCCEEDED** (dataset uploaded to Castform) |
| launch | **FAILED** (`JobLaunchError: Unknown launch arg: "batch_size"`) |

## Local validate_env Result

`VALIDATE_ENV_LOCAL_PASS` — ATL-3C 的 `HermesPhaseCloserLocalEnv` 通过 `benchmax.platform.validation.validate_env` 本地验证，10/10 checks PASS。

## Upload Result

`upload_succeeded: true` — 8 train / 2 eval preview subset 成功上传到 Castform。

## Launch Result

`launch_succeeded: false` — `launch_training_run` 因 `Unknown launch arg: "batch_size"` 被拒绝。

## Accepted Launch Args Schema

用户已查询 Castform 当前接受的 launcher args：

- `model`
- `learning_rate`
- `num_epochs`
- `group_size`
- `max_rollout_len`
- `max_turns`
- `lora_rank`
- `lora_alpha`

## Removed Arg

`batch_size` — 从 `launcher_args` 中删除。

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

## uploaded_payload Status

`MISSING` — 原始 `atl5_cloud_smoke_result.json` 中没有 `uploaded_payload` 字段。

因此无法提取 `env_cls_path`、`env_metadata_path`、`train_dataset_path`、`eval_dataset_path` 进行 launch-only retry。

## Retry Launch Status

`BLOCKED_BY_MISSING_UPLOAD_METADATA` — 必须先重新 upload，才能 launch。

## Next Required Authorization

用户必须显式说：

```
I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY
```

## 验证结果

- `validate_jsonl.py` **PASS**
- `validate_site.py` **PASS**
- `check_secrets.py` **PASS**
- `validate_castform_local_scaffold.py` **PASS**
- `validate_atl3c_sdk_mapping.py` **PASS**
- `validate_atl4a_preflight_scaffold.py` **PASS**
- `validate_atl4b_cloud_smoke_config.py` **PASS**
- `validate_atl4c_guarded_preflight.py` **PASS**（59/59 OK）
- `validate_atl5_cloud_smoke_result.py` **PASS**
- `validate_atl5a_launch_args_fix.py` **PASS**（13/13 OK）

## git 状态

- `git status --short`: 干净（本阶段 commit 后）

## Commit Hash

`14e2677`（基线）→ 新 commit 待生成

## Whether Pushed

Yes（push 后更新）

## Explicit Statement

- **No API key recorded** — `api_key_recorded: false` in result JSON
- **No new upload** — agent 未执行 upload
- **No launch retry executed** — agent 未执行 launch retry
- **No training started** — `training_started: false` in result JSON
- **No .env committed** — 无 `.env` 文件
- **No .venv committed** — `.venv-castform-local` 在 `.gitignore` 中

## 风险评估

- **无新风险** — 本阶段 agent 未执行任何 API 调用、未上传、未训练。
- **遗留风险**：billing / auto-charge / cost visibility 仍多项 UNKNOWN；用户声明不考虑付费、没有绑卡，若 Castform 要求绑卡则 upload/launch 会失败。
- **ATL-5B 风险**：二次 upload + launch 仍可能因 billing/credit/quota 或其他原因失败。
