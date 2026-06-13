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

- **阶段**：ATL-5B — Second upload + launch retry script prepared (agent 只准备脚本；用户手动运行)
- **目标**：准备 ATL-5B retry 脚本（独立 result 文件，不覆盖 ATL-5 历史）、验证器、文档和报告；agent 不调用 Castform API、不上传数据、不启动训练、不读取 API key
- **第一个案例**：[Castform — Hermes Phase Closer v0](cases/castform-hermes-phase-closer-v0/) — second upload retry script ready; manual execution required
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
