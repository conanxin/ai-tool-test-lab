# ATL-2 报告：Castform 本地脱敏样本准备

## 阶段结论

ATL-2 完成。为 Castform — Hermes Phase Closer v0 准备了 42 条训练样本 + 7 条评估样本，全部脱敏，格式验证通过。

## 当前基线

- commit: 2114f4c（ATL-1P 基线）
- 本阶段新增 commit 待提交

## 数据来源

| 来源 | 数量 | 说明 |
|------|------|------|
| 本地报告（脱敏摘要） | 14 | 从 workspace/reports、.openclaw/workspace/reports、ai-tool-test-lab/reports 提取 |
| 合成场景 | 35 | 基于真实项目经验虚构的脱敏摘要 |
| **合计** | **49** | 42 train + 7 eval |

## 样本数量

- **训练集（train）**：42 条 → `cases/castform-hermes-phase-closer-v0/sample-train.jsonl`
- **评估集（eval）**：7 条 → `cases/castform-hermes-phase-closer-v0/sample-eval.jsonl`
- **总计**：49 条（目标 50 条，差 1 条）

## 脱敏规则

- IP 地址 → `<IP_REDACTED>`
- 本地路径 → `<PROJECT_PATH>`
- Token/Key → `<TOKEN_REDACTED>` / `<API_KEY_REDACTED>` / `<SECRET_REDACTED>`
- Authorization Header → `Bearer <TOKEN...D>`
- Bot Token → `<BOT_TOKEN_REDACTED>`
- Commit Hash → `<COMMIT_HASH>`

## 验证结果

| 脚本 | 结果 |
|------|------|
| validate_jsonl.py | PASS（42 train + 7 eval） |
| validate_site.py | PASS |
| check_secrets.py | PASS |

## git status

工作区 clean，待提交。

## 是否 push

本阶段最后执行。

## 明确说明

- **未调用 Castform API**
- **未上传数据**
- **未训练模型**
- **未使用真实 CASTFORM_API_KEY**

## 已知限制

1. 样本总数 49 条，距目标 50 条差 1 条
2. 合成样本比例 71%，可能降低模型泛化能力
3. 缺乏企业级、多语言、跨领域样本
4. ground_truth 未经人工标注验证
5. eval 集仅 7 条，评估统计可信度有限

## 下一步建议

**ATL-3：Castform validate_env**
- 安装 benchmax CLI（仅在真实测试时）
- 运行 castform validate_env 检查数据格式
- 根据反馈调整样本格式
- 准备 ATL-4 cloud smoke run
