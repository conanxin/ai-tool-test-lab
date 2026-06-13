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

- **阶段**：ATL-4B-CONFIG — Castform cloud smoke run dry configuration (gated; launch blocked by unclear charges)
- **目标**：为 Castform Hermes Phase Closer v0 准备 cloud smoke run 的 dry configuration 包、脚本占位、成本边界、安全说明、页面记录和报告；本阶段不调用 Castform API、不上传数据、不启动训练、不创建 API key
- **第一个案例**：[Castform — Hermes Phase Closer v0](cases/castform-hermes-phase-closer-v0/) — cloud smoke run dry configuration ready
- **ATL-3C 收口**：`benchmax.platform.validation.validate_env` 真实本地调用 **10/10 PASS**（api_key=None + local=True → 零网络、零上传、零训练）
- **ATL-4A 收口**：Account / Credit / Billing 人工 preflight scaffold ready；用户已人工进入 Castform Web App，确认 example setup flows (starter task · rag agent · agent traces) 与 Export to VSCode 按钮可见，base model `Qwen/Qwen3.5-4B` 在 setup pages 中可见；**billing / credit / auto-charge / cost visibility 仍未在 UI 中确认**
- **ATL-4B-CONFIG 选型**：Build your own / SDK path（不选 RAG Agent / Agent Traces，原因见 [cloud-smoke-run/README.md](cases/castform-hermes-phase-closer-v0/cloud-smoke-run/README.md)）
- **ATL-4B-CONFIG 配置**：
  - run name: `hermes-phase-closer-smoke`
  - base model: `Qwen/Qwen3.5-4B`
  - 8 train / 2 eval preview subset（`smoke-train.preview.jsonl` / `smoke-eval.preview.jsonl`）
  - `cloud_launch_allowed = false`
  - `current_readiness = BLOCKED_BY_UNCLEAR_CHARGES`
  - launch guard 默认拒绝 launch
- **ATL-4B 下一步**：用户人工确认 credit / billing / auto-charge / cost visibility，把 `Ready status` 同步到 [account-billing-preflight.md](cases/castform-hermes-phase-closer-v0/account-billing-preflight.md)；只有 `READY_FOR_CLOUD_SMOKE_RUN` 后才进入 ATL-4C guarded upload preflight
- **验证**：
  - validate_jsonl.py PASS
  - validate_site.py PASS
  - check_secrets.py PASS
  - validate_castform_local_scaffold.py PASS
  - validate_atl3c_sdk_mapping.py PASS
  - validate_atl4a_preflight_scaffold.py PASS
  - validate_atl4b_cloud_smoke_config.py PASS
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
