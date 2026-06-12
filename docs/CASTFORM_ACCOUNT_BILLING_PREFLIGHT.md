# Castform Account / Credit / Billing Preflight

**Phase**: ATL-4A
**Status**: manual preflight scaffold ready (awaiting human input)
**Baseline**: commit `5f06de9` (ATL-3C)

## 目标

在进入 cloud smoke run (ATL-4B) 之前，由**人**对 Castform 账号、credit、billing 和数据风险进行一次性人工确认。本文件只提供 checklist 与结论字段模板；不调用任何 Castform API，不上传数据，不训练模型。

## 人工检查项

按顺序逐项打勾或记录观察值；不记录任何敏感凭证。

### 账号可访问性

- [ ] 能登录 Castform
- [ ] 登录后能看到 workspace / dashboard
- [ ] 能找到 API key 页面
- [ ] 知道 API key 页面 URL（不记录 key 本身）

### Credit / Billing

- [ ] 能看到 free credit 余额
- [ ] 当前 free credit 金额（数字可记录）
- [ ] 知道是否需要绑定信用卡
- [ ] 知道是否存在「超出 credit 自动扣费」开关
- [ ] 知道是否能在启动 training run 前看到预计费用
- [ ] 知道是否能设置 budget cap / 单次 run 上限

### 风险控制

- [ ] 知道如何取消已启动的 run
- [ ] 知道如何删除已上传的 dataset
- [ ] 知道如何删除 training run / checkpoint
- [ ] 知道是否支持下载 LoRA adapter
- [ ] 知道是否提供 OpenAI-compatible endpoint
- [ ] 知道 endpoint 调用是否会产生额外费用
- [ ] 知道是否有明确的 Terms / Privacy / Data retention 文档

### 数据治理

- [ ] 数据是否会被 Castform 用于训练其基础模型
- [ ] 数据保留期限是多少天
- [ ] 数据是否跨境传输
- [ ] 是否能关闭数据用于改进产品的选项

## 禁止记录内容

执行本 preflight 时，**严禁**把以下任何内容写入本仓库任何文件：

- 真实 API key / `sk-...` / `CASTFORM_API_KEY=真实值`
- 完整或部分信用卡号、CVV、有效期
- Cookie、Authorization header、session token
- 个人邮箱密码、Casform 账号密码
- 包含上述任何一项的截图（除非已手动脱敏到无法还原）
- PRIVATE KEY / SSH key / .env 内容

允许的占位符：`<CASTFORM_API_KEY>`、`<TOKEN_REDACTED>`、`<SECRET_REDACTED>`、`<IP_REDACTED>`。

## 结论字段

人工 preflight 完成后，从以下选项中**只选一个**填入 `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md` 的 `Ready status` 字段：

| 结论 | 含义 | 下一阶段 |
| --- | --- | --- |
| `READY_FOR_CLOUD_SMOKE_RUN` | 全部检查项通过，已知成本可控 | 进入 ATL-4B cloud smoke run dry configuration |
| `BLOCKED_BY_NO_CREDIT` | free credit 不足或未发放 | 等待充值 / 申请 credit |
| `BLOCKED_BY_BILLING_REQUIRED` | 平台要求绑定信用卡 | 由用户决定是否绑定 |
| `BLOCKED_BY_UNCLEAR_CHARGES` | 预计费用或自动扣费规则不透明 | 进一步询问平台 |
| `BLOCKED_BY_ACCOUNT_ACCESS` | 登录 / workspace / API key 页面无法访问 | 排查账号问题 |
| `BLOCKED_BY_DATA_POLICY_UNCLEAR` | 数据保留 / 训练使用条款不清晰 | 进一步询问平台 |

## 与本地阶段的衔接

- ATL-3C 已在本地完成 `validate_env` 真实调用，10/10 contract checks PASS。
- 本地阶段 (`local=True`) **不消耗 credit、不调用云端、不上传数据**。
- 本 preflight 是进入云端的最后一道闸门。结论 `READY` 之前，**不会**在仓库内引入真实 `CASTFORM_API_KEY`、不会调用 `upload_training_run`、不会调用 `launch_training_run`、不会触发 `TrainerClient`。
