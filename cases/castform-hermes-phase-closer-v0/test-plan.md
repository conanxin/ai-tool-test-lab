# Castform 测试计划

## 目标

评估 Castform 作为 Hermes Agent Phase Closer 的 RL post-training 平台。

## 阶段划分

### Phase 0：本地开源项目 scaffold
- 创建 ai-tool-test-lab 项目结构
- 编写首页、案例页面、文档、脚本
- 创建合成样本和 reward rubric
- 本地验证所有文件格式正确
- 产出：本报告及项目仓库

### Phase 1：准备 30–50 条脱敏样本
- 编写 30 条训练样本（sample-train.jsonl）
- 编写 10 条评估样本（sample-eval.jsonl）
- 覆盖场景：成功、失败、部分完成、回滚、阻塞
- 所有样本为虚构内容，不含真实项目信息
- 产出：完整的 JSONL 数据集

### Phase 2：本地 validate_env
- 运行 validate_site.py 检查项目完整性
- 运行 check_secrets.py 扫描敏感信息
- 本地 dry-run reward rubric 评分逻辑
- 验证 JSONL 格式和字段完整性
- 产出：验证报告

### Phase 3：确认 Castform 账号、credit、billing
- 注册 Castform 账号（如尚未注册）
- 确认 account credit 充足
- 查阅 pricing 页面，估算 smoke run 成本
- 设置 billing alert（如支持）
- 产出：账号状态报告

### Phase 4：小规模云端 smoke run
- 设置 CASTFORM_API_KEY（本地环境变量，不提交到仓库）
- 安装 benchmax（Castform 的 Python SDK）
- 上传 30 条训练样本
- 启动 1–2 epoch 的 smoke run
- 监控训练曲线和 reward 变化
- 产出：训练日志和初步评估

### Phase 5：playground 评估
- 在 Castform playground 用 10 条 hold-out 样本测试
- 对比基线模型（GPT-4o-mini）和训练后模型
- 使用 reward rubric 打分
- 产出：评估报告

### Phase 6：是否接入 Hermes/OpenClaw
- 综合评估：输出质量、成本、稳定性、维护复杂度
- 决定是否将 Castform 训练模型接入 Hermes Agent 工作流
- 如接入：设计 integration plan
- 如放弃：记录原因，转向其他方案
- 产出：最终决策报告

## 风险控制

- 绝不提交 API key 到仓库
- 所有真实训练数据脱敏处理
- smoke run 前设置成本上限
- 保留本地备份，随时可切换回模板方案

## 时间预估

| 阶段 | 预估时间 |
|------|----------|
| Phase 0 | 1–2 小时 |
| Phase 1 | 2–3 小时 |
| Phase 2 | 30 分钟 |
| Phase 3 | 30 分钟 |
| Phase 4 | 1–2 小时（含等待训练） |
| Phase 5 | 1 小时 |
| Phase 6 | 30 分钟 |
