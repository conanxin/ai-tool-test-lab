# 本地环境评估

## 硬件配置

| 组件 | 规格 |
|------|------|
| 操作系统 | Windows 10 + WSL2 Ubuntu 24.04 |
| CPU | Intel i7-6700 4C/8T |
| RAM | 16GB（WSL 可用约 7.7GB） |
| GPU | NVIDIA GTX 1070 8GB |
| 本地推理 | Ollama 0.18.0 |

## 能力评估

### 适合的任务

- 静态项目开发（HTML/CSS/JS）
- JSONL 数据整理和清洗
- Python 脚本编写和验证
- reward rubric 设计和评分逻辑
- 本地 dry-run 和格式检查
- 小模型本地推理（Ollama，如 7B 级别）

### 不适合的任务

- 本地 RL fine-tuning（显存不足，算力不足）
- 35B 及以上模型训练
- 大规模 LoRA 训练
- 多卡分布式训练

## 结论

本地电脑适合承担数据准备、验证、记录和轻量推理工作。所有训练任务必须交给云端平台（Castform 或其他）。

## 建议

- 保持 WSL2 内存分配在 8GB 以内，避免 Windows 主机卡顿
- 使用 Ollama 进行本地基线对比时，选择 7B 或更小模型
- 所有训练相关脚本先以 stub 形式存在，确认云端环境后再执行
