# ATL-4A — Castform Account / Credit / Billing Manual Preflight Scaffold Report

**Phase**: ATL-4A
**Date**: 2026-06-13
**Author**: Hermes (with human authorization)
**Status**: **PASS** — manual preflight scaffold created; awaiting human input

## 1. 阶段结论

| 项 | 状态 |
|----|------|
| Stage decision | **PASS** |
| Current baseline commit | `5f06de9` (ATL-3C) |
| New commit hash | see `git log --oneline -1` after commit |
| Castform API calls | **None** |
| Data uploaded | **None** |
| Model training | **None** |
| Real API keys recorded | **None** |
| Credit card info recorded | **None** |
| Cookies / tokens recorded | **None** |
| Private screenshots | **None** |

## 2. 创建文件列表

- `docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md` — 完整 checklist 模板（人工检查项、禁止记录内容、结论字段表、阶段衔接说明）
- `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md` — 案例级占位字段（仅非敏感字段，含 Ready status 选项）
- `scripts/validate_atl4a_preflight_scaffold.py` — 标库实现：检查文件存在 + 反 secret 扫描（识别 `CASTFORM_API_KEY=真实值` / `sk-...` / `Authorization: ...` / `Cookie: ...` / `credit card` / `card number` / `password=...` / `PRIVATE KEY`）；占位符 `<CASTFORM_API_KEY>` / `<TOKEN_REDACTED>` / `<SECRET_REDACTED>` 等被显式豁免；prohibition list 内的描述性文字被识别为政策文本而非 secret 泄露

## 3. 更新文件列表

- `cases/castform-hermes-phase-closer-v0/index.html` — 新增 ATL-4A 区段（声明未使用 API key / 未调用 / 未上传 / 未训练；列出 7 项待确认事项；明确 READY → ATL-4B / BLOCKED → 停 ATL-4A）；时间线插入 ATL-4A 条目；"测试摘要"和"下一步"指针更新
- `data/cases.json` — `phase` → `ATL-4A account and billing preflight`；`status` → `manual preflight scaffold ready`；`local_role` 追加 preflight 角色
- `README.md` — 当前状态区更新为 ATL-4A，补充下一阶段指引与新 validator
- `docs/CASTFORM_VALIDATE_ENV_NOTES.md` — 文末追加 ATL-3C 收口与 ATL-4A 衔接段
- `reports/ATL4A_CASTFORM_ACCOUNT_BILLING_PREFLIGHT_SCAFFOLD_REPORT.md` — 本报告

## 4. preflight checklist 内容摘要

完整内容见 `docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md`。本节给出摘要。

### 账号可访问性（4 项）

- 登录 Castform
- 看到 workspace / dashboard
- 找到 API key 页面
- 记录 API key 页面 URL（不记录 key 本身）

### Credit / Billing（6 项）

- 能看到 free credit 余额
- free credit 金额（数字可记录）
- 是否需要绑卡
- 是否存在「超出 credit 自动扣费」开关
- 能否在启动前看到预计费用
- 能否设置 budget cap / 单次 run 上限

### 风险控制（7 项）

- 取消已启动的 run
- 删除已上传的 dataset
- 删除 training run / checkpoint
- 下载 LoRA adapter
- 提供 OpenAI-compatible endpoint
- endpoint 是否产生额外费用
- 明确 Terms / Privacy / Data retention 文档

### 数据治理（4 项）

- 数据是否被平台用于训练其基础模型
- 数据保留期限
- 数据是否跨境传输
- 能否关闭「数据用于改进产品」

### 结论字段（6 选项）

- `READY_FOR_CLOUD_SMOKE_RUN` → ATL-4B
- `BLOCKED_BY_NO_CREDIT` → 等充值
- `BLOCKED_BY_BILLING_REQUIRED` → 用户决定是否绑卡
- `BLOCKED_BY_UNCLEAR_CHARGES` → 询问平台
- `BLOCKED_BY_ACCOUNT_ACCESS` → 排查账号
- `BLOCKED_BY_DATA_POLICY_UNCLEAR` → 询问平台

### 禁止记录内容（硬红线）

- 真实 API key / `sk-...` / `CASTFORM_API_KEY=真...`
- 完整或部分信用卡号、CVV、有效期
- Cookie、Authorization header、session token
- 邮箱/Castform 账号密码
- 含上述任一项的截图
- PRIVATE KEY / SSH key / .env 内容

## 5. validator 执行结果

| 验证器 | 结果 |
|--------|------|
| `python3 scripts/validate_atl4a_preflight_scaffold.py` | **PASS** |
| `python3 scripts/validate_jsonl.py` | (见运行输出) |
| `python3 scripts/validate_site.py` | (见运行输出) |
| `python3 scripts/check_secrets.py` | (见运行输出) |
| `python3 scripts/validate_castform_local_scaffold.py` | (见运行输出) |
| `python3 scripts/validate_atl3c_sdk_mapping.py` | (见运行输出) |

`validate_atl4a_preflight_scaffold.py` 已确认通过；其余 validator 由 commit 前统一跑批验证。

## 6. git status（commit 前）

预期变更：

```
 M README.md
 M cases/castform-hermes-phase-closer-v0/index.html
 A cases/castform-hermes-phase-closer-v0/account-billing-preflight.md
 M data/cases.json
 A docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md
 M docs/CASTFORM_VALIDATE_ENV_NOTES.md
 A reports/ATL4A_CASTFORM_ACCOUNT_BILLING_PREFLIGHT_SCAFFOLD_REPORT.md
 A scripts/validate_atl4a_preflight_scaffold.py
```

## 7. commit

- 计划消息：`ATL-4A: Add Castform account billing preflight scaffold`
- 计划 commit hash：见 `git log --oneline -1` after commit
- 工作区状态：commit 后 `git status --short` 应输出空

## 8. 是否 push

是。Push 完成后：

- 验证 `https://conanxin.github.io/ai-tool-test-lab/` → HTTP/2 200
- 验证 `https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/` → HTTP/2 200
- 验证 case 页内容含 ATL-4A 段

## 9. 明确安全声明

| 项 | 本阶段 |
|----|--------|
| 调用 Castform API | **未调用** |
| 上传数据 | **未上传** |
| 训练模型 | **未训练** |
| 创建 `.env` | **未创建** |
| 使用真实 `CASTFORM_API_KEY` | **未使用** |
| 调用 `upload_training_run` | **未调用** |
| 调用 `launch_training_run` | **未调用** |
| 调用 `TrainerClient` | **未调用** |
| 记录信用卡信息 | **未记录** |
| 记录 API key / token / cookie | **未记录** |
| 记录账号隐私信息 | **未记录** |
| 提交未脱敏截图 | **未提交** |

## 10. 已知限制

1. **尚未人工确认 Castform 账号和 credit**。`account-billing-preflight.md` 中除明确非敏感字段外，所有 `_待填写_` 仍为空。
2. **尚未提供 API key**。仓库内不存在任何 `CASTFORM_API_KEY=...` 真值；占位符 `<CASTFORM_API_KEY>` 仅作为说明用。
3. **尚未进行 cloud smoke run**。`validate_env` 仅在本地以 `api_key=None + local=True` 调用，未触发 `RolloutClient`、未上传、未训练。
4. **`validate_atl4a_preflight_scaffold.py` 存在误判可能**。当前实现对"禁止记录清单"内的描述性文字（如"PRIVATE KEY"出现在 `严禁...` 段中）做了 negation-cue 豁免；如未来书写风格变化需同步调整。
5. **ATL-2 合成样本比例 71%**（沿用 ATL-3C 限制）。本阶段未涉及样本，但若进入 ATL-4B 真实训练需重新评估。

## 11. 下一步建议

1. 用户人工登录 Castform，填写 `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md` 中的非敏感字段（Login / Workspace / Free credit amount / Billing method / Data deletion / Run cancellation / Cost visibility / Recommended model / Recommended sample count / Max budget）。
2. 从 `READY_FOR_CLOUD_SMOKE_RUN` / `BLOCKED_BY_*` 中选择 1 个填入 `Ready status`。
3. 若 `READY`：进入 ATL-4B（cloud smoke run dry configuration — 仍不带真 key，dry config 完成后由用户显式确认 key 才进入 ATL-4C）。
4. 若 `BLOCKED_BY_*`：在仓库 issues / 报告里记录 blocked reason，**不**进入云端；可在 `account-billing-preflight.md` 中追加笔记。
5. 在任何情况下，本仓库**不会**自动引入真实 `CASTFORM_API_KEY`；任何 `api_key` / `Authorization` 注入都需要用户在 Hermes 单独明确授权。
