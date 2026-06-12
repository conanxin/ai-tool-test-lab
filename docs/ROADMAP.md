# 项目路线图

## ATL-0：本地 scaffold ✅ 已完成

- 创建 ai-tool-test-lab 项目结构
- 编写首页、案例页面、文档、脚本
- 创建合成样本（5 条训练 + 3 条评估）
- 编写 reward rubric 和测试计划
- 本地验证通过（validate_site.py PASS，check_secrets.py PASS）
- commit：d069f86

## ATL-1：公开发布准备 🔄 当前

- 完善首页（介绍区、工作流、状态说明）
- 完善 Castform 案例页（摘要、阶段、证据、时间线）
- 新增 GitHub Pages 发布文档
- 新增项目路线图
- 更新 README.md
- 增强样式
- 生成 ATL-1 报告
- commit

## ATL-2：Castform 本地样本准备

- 准备 30–50 条合成脱敏样本
- 覆盖场景：PASS / FAIL / PARTIAL / ROLLBACK / BLOCKED
- 本地验证 JSONL 格式
- 扫描敏感信息
- 更新案例页面状态

## ATL-3：Castform validate_env

- 确认 Python 3.12+ 环境
- 安装 benchmax（仅在真实测试时）
- 设置 CASTFORM_API_KEY（仅在真实测试时）
- 运行本地环境验证
- 更新案例页面状态

## ATL-4：Castform cloud smoke run

- 确认 Castform 账号、credit、billing
- 上传 30 条训练样本
- 启动 1–2 epoch 小规模训练
- 监控训练曲线和 reward 变化
- 更新案例页面状态

## ATL-5：Playground 评估与页面更新

- 在 playground 用 hold-out 样本测试
- 对比基线模型和训练后模型
- 使用 reward rubric 打分
- 更新案例页面评估结果
- 生成 ATL-5 报告

## ATL-6：新增第二个 AI 工具测试案例

- 选择第二个测试工具/平台
- 运行 scripts/new_case.py
- 填写案例页面
- 更新 data/cases.json
- 运行 validate_site.py
- 生成报告
