# Castform 专项笔记

## 平台定位

Castform 是一个模型微调平台，支持 RL（强化学习）后训练。用户上传数据、定义 reward 函数，平台负责 GPU 训练和模型评估。

## 关键概念

- **benchmax**：Castform 的 Python SDK，用于提交训练任务、查询状态、下载模型
- **reward function**：用户定义的评分函数，平台用 RL 优化模型以最大化 reward
- **smoke run**：小规模快速训练，用于验证配置正确性
- **playground**：在线模型测试环境，可输入 prompt 查看输出

## 已知限制（截至 ATL-0）

- 需要有效的 CASTFORM_API_KEY
- 训练按 token 和 GPU 时间计费
- 本地无法运行训练，必须上传数据到云端
- 数据格式要求：JSONL，每行包含 `prompt` 和 `ground_truth`

## 安全提醒

- CASTFORM_API_KEY 绝不写入代码或提交到仓库
- 使用环境变量或 .env 文件（.env 已加入 .gitignore）
- 所有训练数据脱敏处理

## 相关链接

- 案例页面：`cases/castform-hermes-phase-closer-v0/`
- 测试计划：`cases/castform-hermes-phase-closer-v0/test-plan.md`
- 环境 stub：`cases/castform-hermes-phase-closer-v0/castform-env-stub.py`
