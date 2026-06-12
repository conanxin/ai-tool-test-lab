# ATL-3A: Castform local validate_env scaffold 笔记

## 阶段结论

ATL-3A 已完成本地 scaffold-only 阶段。benchmax 安装因 Python 3.12 venv 缺少 pip 而阻塞，但本地 dataset loader 和 rule-based reward smoke 均已通过验证。

## Python 3.12 状态

- **可用**：Python 3.12.3（系统安装）
- **venv 创建**：成功（使用 `--without-pip` 创建）
- **pip 缺失**：`python3.12-venv` 包未完整安装，`sudo dpkg --configure -a` 超时
- **不继续修复**：遵循 ATL-3A 硬性边界，不运行 sudo apt/dpkg

## benchmax 状态

- **BLOCKED**：venv 缺少 pip，无法安装 benchmax
- **不伪造成功**：run_validate_env_stub.py 明确输出 SKIPPED_WITH_REASON
- **不调用 Castform API**：未设置 CASTFORM_API_KEY，未调用任何云端 API

## 本地 reward smoke 与真实 validate_env 的区别

| 维度 | 本地 reward smoke | 真实 validate_env |
|------|-------------------|-------------------|
| 依赖 | 标准库 only | benchmax / Castform SDK |
| 输入 | 本地 JSONL 样本 | 云端训练配置 |
| 输出 | rule-based score | 模型训练指标 |
| 目标 | 检查评分逻辑 | 验证数据格式和训练环境 |
| 阶段 | ATL-3A | ATL-3B / ATL-4 |

## 为什么 ATL-3A 不设置 API key

- 本阶段只验证本地 scaffold，不涉及云端交互
- API key 只在真实云端 run 前设置（ATL-4）
- 避免在本地文件中留下真实密钥痕迹

## 什么时候才进入 ATL-4

1. ATL-3B 修复 venv/pip 并安装 benchmax（可选，可直接用系统 Python 运行）
2. 确认 Castform 账号状态、credit、billing
3. 决定值得投入后，设置 CASTFORM_API_KEY
4. 运行真实 validate_env 或 cloud smoke run

## 现有数据限制

- 样本总数：49 条（42 train + 7 eval）
- 目标 50 条，差 1 条
- 合成样本比例：71%
- 已在 `dataset-notes.md` 中记录为已知限制

## 下一步

- **ATL-3B**：修复 Python 3.12 venv/pip，安装 benchmax
- **ATL-4**：Castform cloud smoke run preflight / billing-credit check
