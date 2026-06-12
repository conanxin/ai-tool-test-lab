# Dataset Notes — Castform Hermes Phase Closer v0

## 数据来源概览

| 来源 | 数量 | 说明 |
|------|------|------|
| 本地报告（脱敏摘要） | 14 | 从 workspace/reports、.openclaw/workspace/reports、ai-tool-test-lab/reports 提取 |
| 合成场景 | 35 | 基于真实项目经验虚构的脱敏摘要 |
| **合计** | **49** | 42 train + 7 eval |

## 样本数量

- **训练集（train）**：42 条
- **评估集（eval）**：7 条
- **总计**：49 条

## Train/Eval 切分

- 比例：约 86% / 14%（目标 80/20，但样本总数不足 50 条）
- 切分方式：随机 shuffle 后按顺序切分
- 所有样本均经过脱敏处理

## 脱敏规则

1. **IP 地址**：替换为 `<IP_REDACTED>`
2. **本地路径**：替换为 `<PROJECT_PATH>`
3. **Token/Key**：
   - `sk-...` → `<TOKEN_REDACTED>`
   - `gho_...` / `ghp_...` → `<TOKEN_REDACTED>`
   - `api_key=...` → `api_key=<API_KEY_REDACTED>`
   - `token=...` → `token=<TOKEN_REDACTED>`
   - `secret=...` → `secret=<SECRET_REDACTED>`
   - `password=...` → `password=<PASSWORD_REDACTED>`
4. **Authorization Header**：替换为 `Bearer <TOKEN...D>`
5. **Bot Token**：替换为 `<BOT_TOKEN_REDACTED>`
6. **Commit Hash**：替换为 `<COMMIT_HASH>`

## 不包含哪些内容

- 真实 API key、token、secret
- 真实私有路径（如 `/home/conanxin/...`）
- 真实 IP 地址
- 真实项目日志原文
- 真实 Authorization header
- 真实 Telegram bot token
- 真实 cookie
- 完整原始报告（仅提取摘要）

## 已知限制

1. **样本数量不足**：目标 50 条（40 train + 10 eval），实际 49 条（42 train + 7 eval）。原因：本地可用报告数量有限，且部分报告内容敏感无法脱敏使用。
2. **合成样本比例高**：35/49（71%）为合成样本，基于真实项目经验但非真实报告原文。
3. **缺乏多样性**：主要来自个人项目（Hermes、OpenClaw、Control Tower 等），缺乏企业级、多语言、跨领域样本。
4. **ground_truth 结构统一**：所有样本使用相同的 7 标题结构，可能限制模型泛化能力。
5. **未经过人工标注验证**：ground_truth 由脚本自动生成，未经人工校对。

## 下一阶段：ATL-3 validate_env

1. 使用本数据集运行 Castform `validate_env` 命令
2. 检查数据集格式是否符合 Castform 要求
3. 根据 validate_env 反馈调整样本格式
4. 如需增加样本，继续从本地报告提取或生成合成样本
5. 确认无误后进入 ATL-4：cloud smoke run
