# AI Tool Test Lab

一个记录 AI 工具真实测试过程的开源实验室。

## 定位

本项目是一个静态网站，适合发布到 GitHub Pages。每个 AI 工具 / 平台 / 开源项目只用一个页面记录完整测试过程。

记录维度：
- 测试对象是什么
- 为什么测试
- 本地电脑能做什么
- 云端平台负责什么
- 测试步骤
- 成本 / 限制
- 实际执行记录
- 问题与解决
- 最终结论
- 是否值得继续使用

## 当前状态

- **阶段**：ATL-RESUME-2A — Prepare Castform vendor-fix retest script · retest script prepared · vendor fix recorded · real retest requires explicit user authorization
- **目标**：在 vendor 修复后基于 ATL-6 starter-style 配置准备 retest 脚本；新 run_name 不复用旧 failed run；本阶段只准备脚本和验证器，不调用 Castform API / 不访问 UI / 不上传 / 不训练 / 不读取 API key
- **第一个案例**：[Castform — Hermes Phase Closer v0](cases/castform-hermes-phase-closer-v0/) — vendor fix retest script prepared; awaits user manual execution
- **AI Tool Test Lab published**: `https://conanxin.github.io/ai-tool-test-lab/` (HTTP/2 200)
- **Castform case published**: `https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/` (HTTP/2 200)
- **AI Tool Test Lab 已成功发布；Castform case 已成功发布** — 详见 [cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md](cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md) + [reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md](reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md)
- **ATL-3C 收口**：`benchmax.platform.validation.validate_env` 真实本地调用 **10/10 PASS**（api_key=None + local=True → 零网络、零上传、零训练）
- **ATL-4A 收口**：Account / Credit / Billing 人工 preflight scaffold ready；用户已人工进入 Castform Web App，确认 example setup flows (starter task · rag agent · agent traces) 与 Export to VSCode 按钮可见，base model `Qwen/Qwen3.5-4B` 在 setup pages 中可见
- **ATL-4A-CREDIT-FILL 收口**：
  - Free credit visible: **YES** · $50（首次出现 YES 项）
  - Usage page visible: **YES**
  - Billing page visible: **NO** · auto-charge / credit card / cost visibility: **UNKNOWN**
  - Run controls (cancel / delete run / delete dataset / LoRA download): **UNKNOWN**
  - Data policy (terms / privacy / retention / deletion): **UNKNOWN**
  - User-declared readiness: `READY_FOR_CLOUD_SMOKE_RUN`（声明而非系统确认）
  - Risk-adjusted note: `READY` declared with multiple `UNKNOWN`；guarded preflight required before launch
  - `cloud_launch_allowed` 保持 `false`；`current_readiness` 保持 `BLOCKED_BY_UNCLEAR_CHARGES`
- **ATL-4B-CONFIG 选型**：Build your own / SDK path（不选 RAG Agent / Agent Traces，原因见 [cloud-smoke-run/README.md](cases/castform-hermes-phase-closer-v0/cloud-smoke-run/README.md)）
- **ATL-4B-CONFIG 配置**：
  - run name: `hermes-phase-closer-smoke`
  - base model: `Qwen/Qwen3.5-4B`
  - 8 train / 2 eval preview subset（`smoke-train.preview.jsonl` / `smoke-eval.preview.jsonl`）
  - `cloud_launch_allowed = false`
  - `current_readiness = BLOCKED_BY_UNCLEAR_CHARGES`
  - launch guard 默认拒绝 launch
- **ATL-4C guarded preflight 交付**：
  - dual gate 架构：env var 授权（`CASTFORM_API_KEY` + `ATL_ALLOW_CASTFORM_UPLOAD` + `ATL_ALLOW_CASTFORM_LAUNCH`） + 脚本级 guard（`guarded_upload_preflight.py` / `guarded_launch_preflight.py` 默认拒绝 exit 1） + 配置级 tripwire（`actual_upload_allowed_in_this_phase=false` / `actual_launch_allowed_in_this_phase=false`）
  - `FINAL_LAUNCH_GATE.md` — 7 大 gate 清单（用户显式授权 / API key 运行时注入 / env var 授权 / 配置 lock / smoke run 参数 / risk acknowledgment / pre-launch verification）
  - `API_KEY_RUNTIME_ONLY.md` — `read -s` + `export` 注入规则（不写入 repo / 不创建 `.env` / 不发送到 Telegram）
  - `guarded_upload_preflight.py` / `guarded_launch_preflight.py` — 默认拒绝 upload / launch；即使 env var 已设置仍拒绝（因为 `actual_*_allowed=false`）
  - `validate_atl4c_guarded_preflight.py` PASS（59/59 OK）
- **ATL-4C 硬边界**：`cloud_launch_allowed` 保持 `false`；`current_readiness` 保持 `BLOCKED_BY_UNCLEAR_CHARGES`；`actual_upload_allowed_in_this_phase=false`；`actual_launch_allowed_in_this_phase=false`；不调用 Castform API；不上传；不训练；不创建 API key
- **ATL-5-SCRIPT-PREP 交付**：
  - `atl5_cloud_smoke_run.py` — live cloud smoke run 脚本（gate 检查 → 本地 validate_env → upload → launch → 结果 JSON）
  - `atl5_cloud_smoke_result.json` — placeholder（status = SCRIPT_READY_NO_CLOUD_CALL）
  - `validate_atl5_cloud_smoke_result.py` — ATL-5 结果验证器
  - agent 不执行脚本；用户手动运行
- **ATL-5 首次运行结果**（用户手动执行）：
  - local validate_env: **PASS** (`VALIDATE_ENV_LOCAL_PASS`)
  - upload: **SUCCEEDED** (dataset uploaded to Castform)
  - launch: **FAILED** (`JobLaunchError: Unknown launch arg: "batch_size"`)
  - `dataset_uploaded=true`；`training_started=false`
  - **未记录** API key
- **ATL-5A 交付**：
  - 修复 `atl5_cloud_smoke_run.py` launcher_args（删除 `batch_size`，增加 `learning_rate: 1e-5`）
  - 增强脚本保存 `uploaded_payload`（env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path）
  - `ATL5A_LAUNCH_ARGS_FIX_NOTES.md` — 详细修复记录和 Castform 接受参数列表
  - `atl5b_second_upload_retry_guard.py` — ATL-5B 二次 upload + launch 脚本（gate 检查 → 本地 validate_env → upload → launch → 结果 JSON）
  - `validate_atl5a_launch_args_fix.py` — ATL-5A 验证器
  - agent 不执行脚本；用户手动运行 ATL-5B
- **ATL-5A 硬边界**：agent 不调用 Castform API；不上传；不训练；不读取 API key；不运行 `atl5_cloud_smoke_run.py`；不运行 `atl5b_second_upload_retry_guard.py`
- **ATL-5A 下一步**：ATL-5B — 用户手动运行 `.venv-castform-local/bin/python cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_retry_guard.py`，需显式授权：`I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY`
- **ATL-5B-SCRIPT-PREP 交付**：
  - 第二次 upload + launch retry 脚本已准备：`atl5b_second_upload_launch_retry.py`（独立 result 文件 `atl5b_second_upload_launch_retry_result.json`，不覆盖 ATL-5 的 `atl5_cloud_smoke_result.json`；`run_name=hermes-phase-closer-smoke-atl5b`；4 重 gate 含 ATL-5B 授权语句；本地 validate_env → upload → 落盘 `uploaded_payload` → launch with 修正后 args 含 `learning_rate` 不含 `batch_size`）
  - `ATL5B_SECOND_UPLOAD_RETRY_NOTES.md` — 为什么需要 ATL-5B / batch_size 移除 / 授权语句 / 硬规则
  - `validate_atl5b_second_upload_retry_result.py` — std-lib 验证器（无 result → `SKIPPED_RESULT_NOT_PRESENT` exit 0；有 result → PASS/FAIL）
- **ATL-5B-SCRIPT-PREP 硬边界**：agent 未调用 Castform API；agent 未上传；agent 未训练；agent 未读取 API key；agent 未记录 API key；不运行 `atl5b_second_upload_launch_retry.py`；不伪造 run_id / experiment_url
- **ATL-5B-SCRIPT-PREP 下一步**：真实运行需要用户本地 shell 授权；用户在本地 WSL 中：

```bash
export ATL_USER_AUTHORIZATION=*** AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY"
export ATL_ALLOW_CASTFORM_UPLOAD="YES"
export ATL_ALLOW_CASTFORM_LAUNCH="YES"
read -s CASTFORM_API_KEY && export CASTFORM_API_KEY

cd /mnt/d/AI/ai-tool-test-lab
.venv-castform-local/bin/python cases/castform-hermes-phase-closer-v0/cloud-smoke-run/live/atl5b_second_upload_launch_retry.py
python3 scripts/validate_atl5b_second_upload_retry_result.py
```
- **ATL-5B-RESULT 收口**（用户在本地 WSL 手动执行 retry 脚本）：
  - **second upload**: SUCCESS（8 train / 2 eval preview subset 上传 Castform 成功）
  - **launch**: SUCCESS（修正后 `launcher_args` 含 `learning_rate` 不含 `batch_size`，被 Castform 接受）
  - **run_id**: `c83f971d-2b2c-42b8-9774-ca64938c1286`
  - **experiment URL**: <https://app.castform.com/experiments/c83f971d-2b2c-42b8-9774-ca64938c1286>
  - **base model**: `Qwen/Qwen3.5-4B`
  - **sample count**: 8 train / 2 eval
  - **status**: `PASS_CLOUD_SMOKE_LAUNCHED`
  - **API key not recorded**: `api_key_recorded=false`；无 `.env` 创建；无 API key 片段落盘
  - **full dataset not uploaded**: 仅 8/2 preview subset
  - **`uploaded_payload_present`**: `true`（env_cls_path / env_metadata_path / train_dataset_path / eval_dataset_path 已落盘）
  - **`validate_atl5b_second_upload_retry_result.py`**: PASS
- **ATL-5B-RESULT 硬边界**：agent 未调用 Castform API；agent 未重复运行 retry 脚本；agent 未读取 API key；agent 未记录 API key 片段；不伪造 `run_id` / `experiment_url`
- **ATL-5B-RESULT 同步修复**：retry 脚本 `atl5b_second_upload_launch_retry.py` 的 `check_gates` 日志已硬化 — API key 仅显示 `present: True|False`（不再用 `_mask_key` 输出 4 字符前缀）；gate mismatch 仅显示 gate 名 + 期望字面量，不再回显用户填入的授权字符串。`_mask_key` 函数已删除。
- **ATL-5B-RESULT 下一步**：**ATL-5C monitor first Castform training run** — 轮询 experiment URL，捕获 training status（queued / running / completed / failed）+ metrics；运行到终态后更新页面 / cases.json / 报告。
- **ATL-5C 收口**（用户在 Castform UI 观察到 launched run 状态）：
  - **ATL-5B cloud smoke run launched**：run_id `c83f971d-2b2c-42b8-9774-ca64938c1286`
  - **actual UI URL discovered**：`https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train`（documented `/experiments/<run_id>` 路径在 live UI 中返回 Not Found）
  - **run failed at step 0**：status = `failed`, step = `0`, started ≈ 39–41 min ago
  - **no train / eval data**：train tab 与 eval tab 均无数据
  - **no model rollouts**：train rollout deepdive 与 eval rollout deepdive 均无 rollouts
  - **compare external eval works**：external `gpt-5.4` batch eval completed，reward = 10.000，per-request cost ≈ $0.01
  - **failure details not visible**：UI 中无 traceback / worker log；config / settings tab 可见
  - **monitoring status**：`FAILED_STEP_0_NO_ROLLOUTS`
  - **next step**：read-only SDK status probe (用户本地 WSL 跑 `cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c_readonly_status_probe.py`)
- **ATL-5C 交付**：
  - `cases/.../monitoring/atl5c-first-run-failed-step0.md` — 用户观察记录
  - `cases/.../monitoring/atl5c-failure-diagnostics-template.md` — 诊断模板
  - `cases/.../monitoring/atl5c_readonly_status_probe.py` — read-only probe（introspect `TrainerClient` 找 `get_*` / `list_*` / `status_*` / `describe_*`，拒绝 destructive verb；找不到时输出 `NO_READ_ONLY_STATUS_METHOD_FOUND`）
  - `scripts/validate_atl5c_failed_step0_record.py` — 三文件存在 + 必要字段 + 无 secret 字面量校验，PASS
- **ATL-5C 硬边界**：agent 未调用 Castform API；agent 未访问 Castform UI；agent 未上传数据；agent 未启动训练；agent 未重复运行 retry 脚本；API key 未记录；API key 前缀或片段未记录；未提交 `.env`；未提交 `.venv`；未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图；不伪造 failure reason；不伪造 metrics
- **ATL-5C 下一步**：用户本地 WSL 运行 `atl5c_readonly_status_probe.py --run-id c83f971d-...`；若发现 backend error / traceback → 进入 **ATL-5D failure root cause record**；若 probe 输出 `NO_READ_ONLY_STATUS_METHOD_FOUND` → 进入 **ATL-5E support-ready failure bundle**
- **ATL-5D 收口**（read-only SDK probe → `NO_READ_ONLY_STATUS_METHOD_FOUND` → 不存在 root cause record path，只存在 support-ready failure bundle path）：
  - `cases/.../support/ATL5D_SUPPORT_REQUEST.md` — 粘贴给 Castform support / Castie 询问 backend worker log（run_id `c83f971d-2b2c-42b8-9774-ca64938c1286` / what worked / what failed / requested backend log / privacy-scope notes）
  - `cases/.../support/ATL5D_FAILURE_SUMMARY.md` — ruled out: 缺 API key / upload 失败 / batch_size 拒绝 / 缺 run / 缺 UI route；not yet ruled out: remote env load / dataset load / 依赖安装 / trainer bootstrap / quota-billing / worker 内部错误；likely category `FAILED_UNKNOWN_WORKER_BOOTSTRAP`
  - `scripts/validate_atl5d_support_bundle.py` — stdlib 验证器，检查 support 目录、两个 md 文件、run_id token `c83f971d-2b2c-42b8-9774-ca64938c1286`、status tag `FAILED_STEP_0_NO_ROLLOUTS`、16 secret patterns + 1 forbidden literal scan，PASS
- **ATL-5D 硬边界**：agent 未调用 Castform API；agent 未访问 Castform UI；agent 未上传数据；agent 未启动训练；agent 未重复运行 retry 脚本；API key 未记录；API key 前缀或片段未记录；未提交 `.env`；未提交 `.venv`；未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图；不伪造 failure reason；不伪造 metrics
- **ATL-5D 下一步**：用户把 `ATL5D_SUPPORT_REQUEST.md` 内容粘贴给 Castform support / Castie 询问 backend log；若得到 backend error 根因 → 进入 **ATL-5E root-cause fix plan**
- **ATL-5 timeline 摘要**：
  - **ATL-5B launched successfully**：local validate_env PASS · upload SUCCESS · launch SUCCESS · run_id `c83f971d-2b2c-42b8-9774-ca64938c1286` · 8 train / 2 eval · `api_key_recorded=false`
  - **ATL-5C observed failed at step 0**：用户在 Castform UI 观察到 `failed` / `step=0` / no train data / no eval data / no rollouts；read-only SDK probe 确认无 status/log 方法（`NO_READ_ONLY_STATUS_METHOD_FOUND`）
  - **ATL-5D prepared support-ready failure bundle**：run_id / what worked / what failed / requested backend log 整理为可粘贴的支持请求，等待 Castform support 返回 backend log
  - **no repeated launch** · **no new upload**：ATL-5C 后未重复 launch、ATL-5D 后未重复 launch、两次之间未新增 upload；`api_key_recorded` 始终为 `false`
- **ATL-5D 验证（追加）**：
  - validate_atl5d_support_bundle.py PASS（support dir + 两个 md + run_id token + status tag + 16 patterns + 1 literal scan 全部通过）
- **ATL-6A 收口**（starter-style redeploy 准备完成；agent 不调用 Castform API；不重复使用旧 failed run）：
  - `cases/.../starter-style-redeploy/prepare_starter_style_subset.py` — stdlib 子集脚本，16 train / 4 eval preview（从 42/7 全量取前 N 条）
  - `cases/.../starter-style-redeploy/starter-train.preview.jsonl` (16 rows) + `starter-eval.preview.jsonl` (4 rows) — 实际生成的子集
  - `cases/.../starter-style-redeploy/reward_starter_style.py` — 0.0~1.0 `score_completion` 返回 `{format, coverage, score}`；secret-pattern 检测强制 score=0
  - `cases/.../starter-style-redeploy/environment_starter_style.py` — `HermesPhaseCloserStarterStyleEnv`：`BaseEnv` 子类；no-tools（`list_tools=[]` / `run_tool=""` 不 raise）；no custom `load_dataset` override；system_prompt 固定 7 字段结构
  - `cases/.../starter-style-redeploy/validate_starter_style_env.py` — 本地 validate runner（`local=True` / `api_key=None`）；已实测 `VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)` with 5 train + 2 eval rows
  - `cases/.../starter-style-redeploy/atl6_starter_style_redeploy.py` — 云端 redeploy 脚本（4 重 gate 含 `I AUTHORIZE ATL-6 STARTER STYLE REDEPLOY` 授权语句；run_name `hermes-phase-closer-starter-style-atl6`；独立 result 文件 `atl6_starter_style_redeploy_result.json`；launcher_args 同 ATL-5B 修正后版本；不引用旧 run_id `c83f971d-...`；不覆盖 ATL-5 / ATL-5B 历史）
  - `cases/.../starter-style-redeploy/ATL6_STARTER_STYLE_REDEPLOY_NOTES.md` — why ATL-6, starter-task lessons, old run context, fix points, authorization statement, "not done" boundaries, manual execution recipe
  - `scripts/validate_atl6_starter_style_redeploy.py` — stdlib 验证器（per formal spec）：starter-style-redeploy 目录 / 16 train / 4 eval / `run_tool` 不 raise / reward 0.0~1.0 / `launcher_args` 不含 `batch_size` 含 `learning_rate` / result JSON secret-pattern scan + train/eval samples + launch_succeeded 时 run_id + experiment_url 含 app.castform.com / result 缺失时输出 SKIPPED_RESULT_NOT_PRESENT 但 PASS，**PASS**
- **ATL-6A 硬边界**：agent 未调用 Castform API；agent 未访问 Castform UI；agent 未上传数据；agent 未启动训练；agent 未运行 `atl6_starter_style_redeploy.py`；API key 未记录；API key 前缀或片段未记录；未提交 `.env`；未提交 `.venv`；未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图；不伪造 `run_id` / `experiment_url`；不覆盖 ATL-5 / ATL-5B 历史 result；不引用旧 failed run `c83f971d-...`
- **ATL-6A 下一步**：用户在本地 WSL 显式授权 `I AUTHORIZE ATL-6 STARTER STYLE REDEPLOY`（连同 `CASTFORM_API_KEY` + `ATL_ALLOW_CASTFORM_UPLOAD=YES` + `ATL_ALLOW_CASTFORM_LAUNCH=YES`）后手动运行：
  ```
  .venv-castform-local/bin/python \
    cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py
  ```
  真实 Castform API 调用由用户执行；agent 仅监督 `run_id` / `experiment_url` / `training_started` 状态
- **ATL-6A 验证（追加）**：
  - `validate_atl6_starter_style_redeploy.py` PASS（per formal spec：starter-style-redeploy 目录 / 16 train / 4 eval / `run_tool` 不 raise / reward 0.0~1.0 / `launcher_args` 不含 `batch_size` 含 `learning_rate` / result JSON secret-pattern scan + train/eval samples + launch_succeeded 时 run_id + experiment_url 含 app.castform.com / result 缺失时输出 SKIPPED_RESULT_NOT_PRESENT 但 PASS，9 检查全部通过）
- **ATL-6 收口**（用户本地 WSL 手动运行 starter-style redeploy → `PASS_CLOUD_SMOKE_LAUNCHED`）：
  - run_id `56cb5701-6b3e-424e-b671-fc2efc932aa8` · experiment_url `https://app.castform.com/experiments/56cb5701-6b3e-424e-b671-fc2efc932aa8` · base model `Qwen/Qwen3.5-4B` · 16 train / 4 eval · launcher_args 8 项含 `learning_rate` 不含 `batch_size` · `api_key_recorded=false` · `uploaded_payload_present=true` · `training_started=true` · `dataset_uploaded=true` · `error_category=null`
  - `local_validate_env_result = VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)` —— 上传前本地 contract 真实跑通（`.venv-castform-local/bin/python validate_starter_style_env.py`）
  - 写入 `cases/.../starter-style-redeploy/atl6_starter_style_redeploy_result.json` —— 独立 result 文件，不覆盖 ATL-5 / ATL-5B 历史
  - `validate_atl6_starter_style_redeploy.py` PASS（result JSON 出现后从 SKIPPED 模式切到 normal 模式）
- **ATL-6B 收口**（Starter-style redeploy 结果记录到案例页）：
  - 本地 `validate_env` PASS · upload SUCCESS · launch SUCCESS · run_id `56cb5701-6b3e-424e-b671-fc2efc932aa8` · base model `Qwen/Qwen3.5-4B` · 16 train / 4 eval · result status `PASS_CLOUD_SMOKE_LAUNCHED`
- **ATL-6C 收口**（用户在 Castform UI 观察到 starter-style redeploy 启动后仍 `failed` / `step=0` / no train data / no rollouts / display name `simple-c869a30d`；失败 shape 与 ATL-5B 一致；repeated failure YES）：
  - `cases/.../starter-style-redeploy/support/ATL6C_SUPPORT_REQUEST.md` — paste-ready 请求（What Worked / What Failed / Request / Sensitive Information Exclusion / Run 1 + Run 2 / configuration / local validation / upload artifacts / ruled out / what we need from Castform / what we can provide back / local env context / status）
  - `cases/.../starter-style-redeploy/support/ATL6C_FAILURE_SUMMARY.md` — current status / likely category / ruled out 6 项 / not yet ruled out 5 项 / UI 可见证据（两个 run 各自列出）/ read-only SDK probe 复用 / next action
  - `scripts/validate_atl6c_support_request.py` — stdlib 验证器（per formal spec）：两个 md 文件存在 / 两个 run_id token (`c83f971d-...` + `56cb5701-...`) 都在 / 状态标签 `FAILED_STEP_0_NO_ROLLOUTS_REPEATED` 都在 / 16 secret patterns + 1 forbidden literal scan，**PASS**
- **ATL-6C 硬边界**：agent 未调用 Castform API；agent 未访问 Castform UI；agent 未上传数据；agent 未启动训练；agent 未重复运行 `atl6_starter_style_redeploy.py`；agent 未重复运行 `atl5b_second_upload_launch_retry.py`；API key 未记录；API key 前缀或片段未记录；未提交 `.env`；未提交 `.venv`；未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图；不伪造 `run_id`；不伪造 `experiment_url`；不伪造 backend failure reason；不伪造 metrics；不删除旧 run `56cb5701-...` / `c83f971d-...`；不重复 launch
- **ATL-6C 下一步**：用户把 `ATL6C_SUPPORT_REQUEST.md` 内容粘贴到 Castform Castie/support；如果 Castform 返回 backend error，进入 **ATL-6D root cause fix**（可能分支：改 env packaging / 改 dataset upload 路径 / 改 launcher_args / 申请 starter-task 已知好配置做 binary search）
- **ATL-6C 验证（追加）**：
  - `validate_atl6c_support_request.py` PASS（两个 md + 两个 run_id token + 状态标签 + 16 secret patterns + 1 forbidden literal scan 全部通过）
- **ATL-CLOSEOUT 收口**（最终收口，<code>PAUSED_PENDING_CASTFORM_BACKEND_LOGS</code>；不再继续 cloud runs）：
  - `cases/.../CASE_CLOSEOUT.md` — final case closeout doc (final status / what tested / local successes / cloud successes / cloud failure / ruled out / not yet ruled out / final decision / optional future action / sensitive info exclusion)
  - `cases/.../CASTFORM_SUPPORT_REQUEST_FINAL.md` — paste-ready 英文简短支持请求 (Run 1 + Run 2 / what worked / what failed / request / sensitive information exclusion)
  - `reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md` — 完整收口报告 (阶段结论 / current baseline commit / 项目公开 URL / Castform 案例页 URL / 测试阶段总览 / 最终成果 / 最终阻塞 / 保留证据 / 安全说明 / 下一步建议)
  - `scripts/validate_case_closeout.py` — stdlib 验证器（per formal spec：3 closeout doc 文件存在 / 两个 run_id token 都在 / 状态标签 <code>PAUSED_PENDING_CASTFORM_BACKEND_LOGS</code> / <code>data/cases.json</code> Castform case status = paused pending Castform backend logs / 16 secret patterns + 1 forbidden literal scan），**PASS**
- **ATL-CLOSEOUT 硬边界**：agent 未调用 Castform API；agent 未访问 Castform UI；agent 未上传数据；agent 未启动训练 run；agent 未重复运行 ATL-5B 脚本；agent 未重复运行 ATL-6 redeploy 脚本；API key 未记录；API key 前缀或片段未记录；未提交 `.env`；未提交 `.venv`；未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图；不伪造根因；不伪造 metrics；不删除历史 result JSON；不删除旧 run 信息
- **ATL-CLOSEOUT 下一步建议**：pause project；optionally send `CASTFORM_SUPPORT_REQUEST_FINAL.md`（或 `ATL6C_SUPPORT_REQUEST.md`）到 Castform Castie/support；do not run more cloud tests until Castform backend logs are available
- **ATL-CLOSEOUT 验证（追加）**：
  - `validate_case_closeout.py` PASS（3 closeout doc + 两个 run_id token + 状态标签 + data/cases.json Castform case status 校验 + 16 secret patterns + 1 forbidden literal scan 全部通过）
- **ATL-RESUME-1 收口**（记录 Castform vendor fix response；case 可 resume retest）：
  - `cases/.../VENDOR_FIX_RESPONSE.md` — Castform vendor fix response 完整记录（status / summary / vendor-confirmed root cause / credit update / impact on previous conclusion / next step / sensitive information exclusion）
  - `cases/.../CASE_CLOSEOUT.md` — append-only 追加 "Vendor Fix Update" 段；历史 PAUSED_PENDING_CASTFORM_BACKEND_LOGS 结论保留
  - `cases/.../CASTFORM_SUPPORT_REQUEST_FINAL.md` — 顶部新增 "Follow-up" 段；原始 support request 保留
  - `cases/.../index.html` — 新增 "Vendor fix received" 模块 + 更新 footer
  - `data/cases.json` — Castform case phase=VENDOR-FIX-RECEIVED · status=vendor fix received; retest pending · final_status=VENDOR_FIX_RECEIVED_RETEST_PENDING · canonical_example / workflow_reference 保留 · updated_at=2026-06-14
  - `scripts/validate_vendor_fix_response.py` — stdlib 验证器（VENDOR_FIX_RESPONSE.md 存在 / 必填 token / 100 美元 credits / data/cases.json Castform final_status=VENDOR_FIX_RECEIVED_RETEST_PENDING / secret patterns + 1 forbidden literal scan），**PASS**
  - `reports/ATL_RESUME1_CASTFORM_VENDOR_FIX_RESPONSE_REPORT.md` — 阶段报告
- **ATL-RESUME-1 硬边界**：agent 未调用 Castform API；agent 未访问 Castform UI；agent 未上传数据；agent 未启动训练；agent 未运行 ATL-5 / ATL-6 / redeploy 脚本；agent 未读取 API key 任何片段；未创建 .env；未提交 .venv；未记录用户邮箱；未记录截图；未记录 API key / 信用卡 / cookie / Authorization header；不改写历史事实（两个旧 run 仍记录为 step 0 failed）；不伪造 retest 成功
- **Castform case 当前状态**：
  - Vendor fix received
  - Root cause confirmed by Castform: raw data dict trainer incompatibility
  - $100 extra credits added
  - Retest pending
- **ATL-RESUME-1 下一步建议**：ATL-RESUME-2 — 基于 vendor 修复后重新跑 starter-style Castform retest（仍走用户本地 WSL 手动授权，不让 agent 自动 launch）
- **ATL-RESUME-2A 收口**（准备 vendor-fix retest 脚本；agent 不运行）：
  - `cases/.../vendor-fix-retest/atl_resume2_vendor_fix_retest.py` — retest 脚本（gate check → 本地 validate_env → upload → launch → 独立 result JSON `atl_resume2_vendor_fix_retest_result.json`；run_name `hermes-phase-closer-vendor-fix-retest`；复用 ATL-6 starter-style env / reward / 16 train / 4 eval；no batch_size / learning_rate included / no custom load_dataset override；旧 run_id 不引用作为输入；授权语句 `I AUTHORIZE ATL-RESUME-2 CASTFORM RETEST AFTER VENDOR FIX`）
  - `cases/.../vendor-fix-retest/ATL_RESUME2_VENDOR_FIX_RETEST_NOTES.md` — retest notes（vendor fix context / expected signal / authorization / hard rules）
  - `cases/.../index.html` — 新增 "ATL-RESUME-2A — Vendor-Fix Retest Prepared" 模块 + 更新 footer
  - `data/cases.json` — Castform case phase=`ATL-RESUME-2A vendor-fix retest prepared` · status=`vendor fix recorded; retest script ready` · final_status=`VENDOR_FIX_RECEIVED_RETEST_PENDING`（保留作为审计） · canonical_example / workflow_reference 保留 · updated_at=2026-06-14
  - `scripts/validate_atl_resume2_vendor_fix_retest.py` — stdlib 验证器（retest dir 存在 / 脚本 compile / no batch_size + learning_rate / auth 字符串 / run_name / 旧 run_id 不引用；result JSON 缺失 → `SKIPPED_RESULT_NOT_PRESENT` exit 0；有 result → 16 secret patterns + 1 forbidden literal scan + train_samples==16 + eval_samples==4 + api_key_recorded==false + launch_succeeded invariants），**PASS**（SKIPPED 模式）
  - `reports/ATL_RESUME2A_VENDOR_FIX_RETEST_PREP_REPORT.md` — 阶段报告
- **ATL-RESUME-2A 硬边界**：agent 未调用 Castform API；agent 未访问 Castform UI；agent 未上传数据；agent 未启动训练；agent 未运行 ATL-5B / ATL-6 / 新 retest 脚本；agent 未读取 API key 任何片段；未创建 .env；未提交 .venv；未记录用户邮箱 / 截图 / API key / cookie / Authorization header / 信用卡；不改写历史事实（两个旧 run 仍记录为 step 0 failed）；新 retest 不引用旧 run_id 作为输入；不伪造 retest 成功
- **ATL-RESUME-2A 状态**：
  - vendor fix recorded
  - retest script prepared
  - true retest requires explicit user authorization
  - no API call / no upload / no training by agent
- **ATL-RESUME-2A 下一步建议**：ATL-RESUME-2B — 用户本地 WSL 显式授权后手动运行 `atl_resume2_vendor_fix_retest.py`，agent 仅做 on-disk result verify + transcribe 到 case page / cases.json / 报告（不调用 API、不访问 UI、不上传、不启动训练）
- **验证**：
  - validate_jsonl.py PASS
  - validate_site.py PASS
  - check_secrets.py PASS
  - validate_castform_local_scaffold.py PASS
  - validate_atl3c_sdk_mapping.py PASS
  - validate_atl4a_preflight_scaffold.py PASS
  - validate_atl4b_cloud_smoke_config.py PASS
  - validate_atl4c_guarded_preflight.py PASS（59/59 OK；upload guard exit 1 + banner 6/6；launch guard exit 1 + banner 6/6）
  - validate_atl5_cloud_smoke_result.py PASS（placeholder JSON 合法，无 secret，train=8，eval=2）
  - validate_atl5a_launch_args_fix.py PASS（13/13 OK：status/upload/launch/error_summary/batch_size/learning_rate/secret 扫描全部通过）
  - dataset_loader.py PASS（42 train + 7 eval）
  - run_local_reward_smoke.py PASS（5/5）
  - inspect_benchmax_validate_env.py PASS（introspection，无调用）
  - run_real_validate_env_attempt.py **VALIDATE_ENV_LOCAL_PASS**（local contract checks 10/10）
  - prepare_cloud_smoke_subset.py PASS（8 train + 2 eval preview）
  - cloud_launch_guard.py PASS（exit 1，默认拒绝 launch）
- **benchmax 状态**：`0.1.2.dev33`，`benchmax.platform.validation.validate_env` 真实存在；`api_key=None` + `local=True` → 完全跳过 `RolloutClient`
- **Python 3.12 venv/pip**：通过 `python3.12 -m venv --without-pip` + `/tmp/get-pip.py` 引导（未使用 sudo apt）
- **ATL-4B-CONFIG 阶段：未调用 Castform API** / **未上传数据** / **未训练模型** / **未创建 API key** / **未使用真实 CASTFORM_API_KEY** / **未创建 .env** / **未记录 API key / 信用卡 / cookie / 用户邮箱 / 截图**

## 本地运行

```bash
# 进入项目目录
cd ai-tool-test-lab

# 本地预览
python -m http.server 8080

# 验证站点完整性
python scripts/validate_site.py

# 检查敏感信息泄露
python scripts/check_secrets.py
```

## Case workflow standard

Castform Hermes Phase Closer v0 is the canonical example.

Future cases should follow the same one-case-one-page structure.

Every case should move through discovery, local readiness, scaffold, local validation, guarded external run, monitoring, failure analysis, and closeout.

The goal is not only to test tools, but to preserve reasoning, evidence, risk boundaries, and final state.

### 相关文档与案例

- [docs/CASE_WORKFLOW_STANDARD.md](docs/CASE_WORKFLOW_STANDARD.md) — Case workflow 标准（10 阶段 lifecycle + 强制原则）
- [docs/CASE_PHASES.md](docs/CASE_PHASES.md) — 阶段命名规则（ATL-0 ~ ATL-CLOSEOUT）
- [docs/CASE_TEMPLATE.md](docs/CASE_TEMPLATE.md) — Castform-style case 模板（16 节固定结构）
- [docs/ADDING_A_NEW_CASE.md](docs/ADDING_A_NEW_CASE.md) — 新增 case 标准步骤
- [cases/castform-hermes-phase-closer-v0/index.html](cases/castform-hermes-phase-closer-v0/index.html) — Castform 案例页
- [cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md](cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md) — Castform 最终 closeout 文档

## 新增案例

参见 [docs/ADDING_A_NEW_CASE.md](docs/ADDING_A_NEW_CASE.md)。

## GitHub Pages 发布

参见 [docs/GITHUB_PAGES_DEPLOYMENT.md](docs/GITHUB_PAGES_DEPLOYMENT.md)。

## 项目路线图

参见 [docs/ROADMAP.md](docs/ROADMAP.md)。

## 项目结构

```
ai-tool-test-lab/
  README.md
  LICENSE
  .gitignore
  index.html              # 首页
  assets/
    css/style.css
    js/app.js
  data/cases.json         # 案例元数据
  cases/                  # 各案例页面
  docs/                   # 文档与模板
  scripts/                # 验证与工具脚本
  reports/                # 阶段报告
```

## 声明

本项目所有测试记录均为真实测试过程，但 **第一阶段（ATL-0）为本地 scaffold 阶段**，不调用任何外部 API，不上传数据，不启动云端训练。详见各案例页面的状态说明。

## License

MIT
