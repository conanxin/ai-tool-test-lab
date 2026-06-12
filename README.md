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

- **阶段**：ATL-4A — Castform account / credit / billing manual preflight (scaffold ready, awaiting human input)
- **目标**：在进入云端 smoke run 之前建立人工 preflight checklist 与占位字段；不调用 API、不上传、不训练
- **第一个案例**：[Castform — Hermes Phase Closer v0](cases/castform-hermes-phase-closer-v0/) — manual preflight scaffold ready
- **ATL-3C 收口**：`benchmax.platform.validation.validate_env` 真实本地调用 **10/10 PASS**（api_key=None + local=True → 零网络、零上传、零训练）
- **ATL-4A 下一阶段**：用户人工登录 Castform，填写 [account-billing-preflight.md](cases/castform-hermes-phase-closer-v0/account-billing-preflight.md) 中的非敏感字段；只有 `READY_FOR_CLOUD_SMOKE_RUN` 后才进入 ATL-4B
- **验证**：
  - validate_jsonl.py PASS
  - validate_site.py PASS
  - check_secrets.py PASS
  - validate_castform_local_scaffold.py PASS
  - validate_atl3c_sdk_mapping.py PASS
  - validate_atl4a_preflight_scaffold.py PASS
  - dataset_loader.py PASS（42 train + 7 eval）
  - run_local_reward_smoke.py PASS（5/5）
  - inspect_benchmax_validate_env.py PASS（introspection，无调用）
  - run_real_validate_env_attempt.py **VALIDATE_ENV_LOCAL_PASS**（local contract checks 10/10）
- **benchmax 状态**：`0.1.2.dev33`，`benchmax.platform.validation.validate_env` 真实存在；`api_key=None` + `local=True` → 完全跳过 `RolloutClient`
- **Python 3.12 venv/pip**：通过 `python3.12 -m venv --without-pip` + `/tmp/get-pip.py` 引导（未使用 sudo apt）
- **未调用 Castform API** / **未上传数据** / **未训练模型**

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
