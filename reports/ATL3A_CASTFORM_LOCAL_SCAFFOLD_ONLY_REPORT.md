# ATL-3A: Castform Local Scaffold-Only Report

## 阶段结论

PARTIAL_PASS — 本地 scaffold 文件完整，dataset loader 和 reward smoke 均通过验证。benchmax 因 venv pip 缺失而阻塞，validate_env 未真实运行，已明确标记为 SKIPPED_WITH_REASON。

## 当前基线

- **commit**：53e13c0（ATL-2 基线）
- **项目路径**：/mnt/d/AI/ai-tool-test-lab
- **GitHub Pages**：https://conanxin.github.io/ai-tool-test-lab/
- **Castform 案例页**：https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/

## Python 3.12 状态

- **版本**：Python 3.12.3
- **venv 创建**：成功（使用 `--without-pip`）
- **pip 缺失**：python3.12-venv 包未完整安装，sudo dpkg --configure -a 超时
- **策略**：不继续修复，不运行 sudo apt/dpkg（遵循 ATL-3A 硬性边界）

## benchmax 状态

- **BLOCKED**：venv 缺少 pip，无法安装 benchmax
- **不伪造成功**：run_validate_env_stub.py 输出 SKIPPED_WITH_REASON
- **不调用 Castform API**：未设置 CASTFORM_API_KEY

## 本地验证结果

| 脚本 | 结果 | 说明 |
|------|------|------|
| validate_jsonl.py | PASS | 42 train + 7 eval |
| validate_site.py | PASS | 站点结构完整 |
| check_secrets.py | PASS | 无敏感信息泄露 |
| validate_castform_local_scaffold.py | PASS | 6 个 scaffold 文件存在 |
| dataset_loader.py | PASS | 42 train + 7 eval |
| run_local_reward_smoke.py | PASS | 5/5 测试通过 |
| run_validate_env_stub.py | SKIPPED_WITH_REASON | benchmax unavailable |

## 修改文件列表

- cases/castform-hermes-phase-closer-v0/local-validate-env/README.md（新增）
- cases/castform-hermes-phase-closer-v0/local-validate-env/dataset_loader.py（新增）
- cases/castform-hermes-phase-closer-v0/local-validate-env/reward.py（新增）
- cases/castform-hermes-phase-closer-v0/local-validate-env/environment_stub.py（新增）
- cases/castform-hermes-phase-closer-v0/local-validate-env/run_local_reward_smoke.py（新增）
- cases/castform-hermes-phase-closer-v0/local-validate-env/run_validate_env_stub.py（新增）
- scripts/validate_castform_local_scaffold.py（新增）
- cases/castform-hermes-phase-closer-v0/index.html（更新 ATL-3A 模块）
- data/cases.json（更新 phase 和 status）
- README.md（更新当前状态）
- docs/CASTFORM_VALIDATE_ENV_NOTES.md（新增）
- reports/ATL3A_CASTFORM_LOCAL_SCAFFOLD_ONLY_REPORT.md（本报告）

## 安全声明

- **未调用 Castform API**
- **未上传数据**
- **未训练模型**
- **未创建 .env**
- **未提交真实 API key**

## 已知限制

1. benchmax 未安装（venv pip 缺失）
2. validate_env 未真实运行（仅 stub）
3. ATL-2 数据合成比例 71%（已记录在 dataset-notes.md）
4. 样本总数 49 条，距目标 50 条差 1 条

## 下一步建议

- **ATL-3B**：修复 Python 3.12 venv/pip，安装 benchmax
- **ATL-4**：Castform cloud smoke run preflight，先检查账号、credit、billing，再决定是否运行真实云端训练
