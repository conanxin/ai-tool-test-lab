# Castform Account / Credit / Billing Preflight — Castform Hermes Phase Closer v0

**Phase**: ATL-4A
**Status**: manual preflight scaffold (待用户人工填写)
**Created**: 2026-06-13
**Baseline**: commit `5f06de9` (ATL-3C)

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
- Ready status: _从下列结论中选一个_ READY_FOR_CLOUD_SMOKE_RUN / BLOCKED_BY_NO_CREDIT / BLOCKED_BY_BILLING_REQUIRED / BLOCKED_BY_UNCLEAR_CHARGES / BLOCKED_BY_ACCOUNT_ACCESS / BLOCKED_BY_DATA_POLICY_UNCLEAR

---

## 备注

- 本文件由 ATL-4A scaffold 自动生成；**不**包含任何真实 secret。
- 用户人工填写后，将 `Ready status` 同步到 `reports/ATL4A_CASTFORM_ACCOUNT_BILLING_PREFLIGHT_SCAFFOLD_REPORT.md`。
- 只有 `READY_FOR_CLOUD_SMOKE_RUN` 后，仓库才会进入 ATL-4B。
