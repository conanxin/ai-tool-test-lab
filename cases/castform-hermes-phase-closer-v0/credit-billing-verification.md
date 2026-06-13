# Castform Credit / Billing Verification — Castform Hermes Phase Closer v0

**Phase**: ATL-4A-CREDIT-FILL
**Status**: free credit confirmed ($50) · READY declared with unresolved billing/charge unknowns · launch remains blocked
**Date**: 2026-06-13
**Baseline**: commit `b364bb7` (ATL-4B-CONFIG) · commit `ff22241` (ATL-4A) · commit `5f06de9` (ATL-3C)

> 本文件只记录**结构化非敏感字段**。任何 API key、信用卡号、cookie、token、Authorization header、用户邮箱、截图均**不得**写入本文件。
> 完整 checklist 与结论字段见 `docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md`。

---

## Credit

- Free credit visible: **YES**
- Free credit amount: **$50**（数字可记录；非敏感）
- Credit expiration visible: **NO**
- Usage page visible: **YES**

## Billing

- Billing page visible: **NO**
- Billing method required: **UNKNOWN**
- Credit card required before launch: **UNKNOWN**
- Auto-charge risk: **UNKNOWN**
- Spending limit visible: **UNKNOWN**

## Cost Visibility

- Estimated cost visible before launch: **UNKNOWN**
- Model cost visible: **UNKNOWN**
- GPU / runtime cost visible: **UNKNOWN**
- Endpoint cost visible: **UNKNOWN**

## Run Controls

- Cancel training run available: **UNKNOWN**
- Delete training run available: **UNKNOWN**
- Delete uploaded dataset available: **UNKNOWN**
- Download LoRA / checkpoint visible: **UNKNOWN**

## Data Policy

- Terms visible: **UNKNOWN**
- Privacy policy visible: **UNKNOWN**
- Data retention notes: **UNKNOWN**
- Dataset deletion policy visible: **UNKNOWN**

---

## Final Readiness

- **User-declared Final readiness**: `READY_FOR_CLOUD_SMOKE_RUN`
- **Risk note**: `READY` declared while billing / charge visibility / run controls / data policy remain unresolved (多项 `UNKNOWN`).
- **Cloud launch allowed**: **NO** until guarded preflight explicitly updates `cloud_launch_allowed` to `true`.
- **Guard status**: `cloud_launch_allowed` in `cloud_smoke_config.json` remains `false`; `current_readiness` remains `BLOCKED_BY_UNCLEAR_CHARGES` until ATL-4C (or later) explicitly promotes it.
- **Next phase requirement**: ATL-4C guarded cloud smoke preflight only — NOT immediate training launch.

---

## 备注

- 本文件由 ATL-4A-CREDIT-FILL 阶段自动生成；**不**包含任何真实 secret、API key、cookie、信用卡信息、用户邮箱或截图。
- 用户已人工确认 free credit $50 可见 + usage page 可见，是 ATL-4A 阶段首次出现 YES 项。
- billing / auto-charge / cost estimate / cancellation / deletion / data policy 仍为 UNKNOWN —— 这是必须留档的 **explicit risk**。
- 用户声明 `READY_FOR_CLOUD_SMOKE_RUN` 不等于系统已就绪；本仓库的 `cloud_launch_allowed` 必须保持 `false`，由后续 ATL-4C 在更严格的 guard 下显式升级。
- `READY_FOR_CLOUD_SMOKE_RUN` 仅表示 **用户侧决策**：用户接受当前 UNKNOWN 风险并选择推进 guarded preflight；不代表平台已确认计费透明。
