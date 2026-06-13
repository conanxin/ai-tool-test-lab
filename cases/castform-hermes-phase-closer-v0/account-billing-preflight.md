# Castform Account / Credit / Billing Preflight — Castform Hermes Phase Closer v0

**Phase**: ATL-4A → ATL-4B-CONFIG (gated)
**Status**: ATL-4B-CONFIG cloud smoke run dry configuration scaffold ready; launch still BLOCKED_BY_UNCLEAR_CHARGES
**Created**: 2026-06-13
**Baseline**: commit `5f06de9` (ATL-3C)
**ATL-4A baseline**: commit `ff22241`

> 本文件只记录**结构化非敏感字段**。任何 API key、信用卡号、cookie、token 均**不得**写入本文件。
> 完整 checklist 见 `docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md`。

---

## Castform Account Access

- Login status: _待填写_
- Workspace visible: _待填写_
- API key page visible: _待填写_
- API key copied into project: **NO**

## Credit / Billing

- Free credit visible: _待填写_
- Free credit amount: _数字可记录_
- Billing method required: _待填写_
- Auto-charge risk: _待填写_
- Estimated cost visible before launch: _待填写_

## Data / Privacy

- Dataset deletion available: _待填写_
- Run deletion available: _待填写_
- Model / checkpoint ownership statement visible: _待填写_
- Data retention notes: _待填写_

## Cloud Smoke Run Readiness

- Recommended model: _待填写_
- Recommended sample count: _待填写_
- Max budget: _数字可记录_
- Ready status: **BLOCKED_BY_UNCLEAR_CHARGES**（ATL-4A 人工 preflight 尚未确认 credit / billing / auto-charge / cost visibility）

## ATL-4A 人工观察摘要 (Web App UI 可见性)

- Login: PASS（用户可登录）
- Workspace visible: PASS
- API key page visible: PASS
- API key page current state: **No API keys yet**
- Example setup flows visible: **starter task · rag agent · agent traces**（PASS）
- Training template pages visible: **rag agent · agent traces**（PASS）
- Export to VSCode button visible: PASS
- base model `Qwen/Qwen3.5-4B` shown in setup pages: PASS
- Billing / credit / auto-charge / cost estimate: **NOT CHECKED**（未在 UI 中确认）
- Run cancellation / data deletion / model ownership: **NOT CHECKED**（未在 UI 中确认）

## ATL-4B-CONFIG Dry Configuration 摘要 (本阶段交付)

- run name: `hermes-phase-closer-smoke`
- template path: `build_your_own_sdk`
- base model: `Qwen/Qwen3.5-4B`
- train_sample_count: 8
- eval_sample_count: 2
- cloud_launch_allowed: **false**
- current_readiness: **BLOCKED_BY_UNCLEAR_CHARGES**
- 详细见 `cloud-smoke-run/README.md` + `cloud-smoke-run/cloud_smoke_config.json`

---

## 备注

- 本文件由 ATL-4A scaffold 自动生成；**不**包含任何真实 secret。
- 用户人工填写后，将 `Ready status` 同步到 `reports/ATL4A_CASTFORM_ACCOUNT_BILLING_PREFLIGHT_SCAFFOLD_REPORT.md`。
- ATL-4B-CONFIG 已准备 dry configuration 包，但 billing / credit 未确认 → launch 仍 blocked。
- 下一步：用户人工确认 credit / billing / auto-charge / cost visibility → `READY_FOR_CLOUD_SMOKE_RUN` 后才进入 ATL-4C。
- 只有 `READY_FOR_CLOUD_SMOKE_RUN` 后，仓库才会进入 ATL-4C guarded upload preflight。
