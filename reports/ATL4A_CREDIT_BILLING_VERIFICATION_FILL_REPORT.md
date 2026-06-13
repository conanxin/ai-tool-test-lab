# ATL-4A-CREDIT-FILL — Castform Credit / Billing Result Recording Report

**Date**: 2026-06-13
**Phase**: ATL-4A-CREDIT-FILL
**Status**: **PASS_WITH_LAUNCH_BLOCKED**
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Baseline (current)**: `79880c9` (ATL-4B-CONFIG hash fixup) · `b364bb7` (ATL-4B-CONFIG) · `ff22241` (ATL-4A) · `5f06de9` (ATL-3C)

## 阶段结论

`PASS_WITH_LAUNCH_BLOCKED` —— 用户人工 credit / billing / cost / run controls / data policy 检查结果已留档；用户声明 `READY_FOR_CLOUD_SMOKE_RUN`；但 `cloud_launch_allowed` 保持 `false`，`current_readiness` 保持 `BLOCKED_BY_UNCLEAR_CHARGES`，**guarded preflight required before launch**。

## 用户人工检查结果（已记录到 `credit-billing-verification.md`）

### Credit

- Free credit visible: **YES**
- Free credit amount: **$50**（数字可记录；非敏感）
- Credit expiration visible: **NO**
- Usage page visible: **YES**

### Billing

- Billing page visible: **NO**
- Billing method required: **UNKNOWN**
- Credit card required before launch: **UNKNOWN**
- Auto-charge risk: **UNKNOWN**
- Spending limit visible: **UNKNOWN**

### Cost Visibility

- Estimated cost visible before launch: **UNKNOWN**
- Model cost visible: **UNKNOWN**
- GPU / runtime cost visible: **UNKNOWN**
- Endpoint cost visible: **UNKNOWN**

### Run Controls

- Cancel training run available: **UNKNOWN**
- Delete training run available: **UNKNOWN**
- Delete uploaded dataset available: **UNKNOWN**
- Download LoRA / checkpoint visible: **UNKNOWN**

### Data Policy

- Terms visible: **UNKNOWN**
- Privacy policy visible: **UNKNOWN**
- Data retention notes: **UNKNOWN**
- Dataset deletion policy visible: **UNKNOWN**

## User-declared Final readiness

- Final readiness: **`READY_FOR_CLOUD_SMOKE_RUN`**（声明）
- Risk note: **`READY` declared while billing / charge visibility / run controls / data policy remain unresolved (多项 `UNKNOWN`)**.
- Cloud launch allowed: **NO** until guarded preflight explicitly updates `cloud_launch_allowed` to `true`.
- Guard status: `cloud_launch_allowed` 在 `cloud_smoke_config.json` 中保持 `false`；`current_readiness` 保持 `BLOCKED_BY_UNCLEAR_CHARGES` 直到 ATL-4C（或后续）显式升级。

## 生成 / 修改文件

- `cases/castform-hermes-phase-closer-v0/credit-billing-verification.md` — 新建（用户人工检查完整结果 + 风险说明）
- `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md` — 更新（加入 ATL-4A-CREDIT-FILL 摘要 + Risk-adjusted note）
- `cases/castform-hermes-phase-closer-v0/index.html` — 更新（加入 ATL-4A-CREDIT-FILL 模块 + guard status grid + 时间线 + footer）
- `data/cases.json` — 更新（phase = `ATL-4A-CREDIT credit billing result recorded`，status = `free credit confirmed; ready declared with guarded preflight required`）
- `README.md` — 更新（顶部当前状态切换到 ATL-4A-CREDIT-FILL 收口）
- `reports/ATL4A_CREDIT_FILL_REPORT.md` — 本报告

## Guard 状态复核（关键不变量）

| 字段 | 当前值 |
| --- | --- |
| `cloud_smoke_config.json` → `cloud_launch_allowed` | `false`（未改） |
| `cloud_smoke_config.json` → `current_readiness` | `BLOCKED_BY_UNCLEAR_CHARGES`（未改） |
| `cloud_smoke_config.json` → `phase` | `ATL-4B-CONFIG`（未改；本阶段不重写 config） |
| `cloud_launch_guard.py` exit code | `1`（默认拒绝 launch） |
| `cloud_launch_guard.py` banner | 完整（dry configuration only / cloud_launch_allowed=false / BLOCKED_BY_UNCLEAR_CHARGES / no API call / no upload / no training） |

## 验证结果

- `validate_jsonl.py` **PASS**（42 train / 7 eval）
- `validate_site.py` **PASS**
- `check_secrets.py` **PASS**（未发现 secret-shaped 字符串）
- `validate_castform_local_scaffold.py` **PASS**
- `validate_atl3c_sdk_mapping.py` **PASS**
- `validate_atl4a_preflight_scaffold.py` **PASS**
- `validate_atl4b_cloud_smoke_config.py` **PASS**（49/49 OK；guard 行为复核 exit 1 + banner 6/6 完整）
- `prepare_cloud_smoke_subset.py` 仍 PASS（8+2 preview）
- `cloud_launch_guard.py` 仍 PASS（exit 1，banner 完整）

## 重要判断

1. **用户声明 ≠ 系统就绪**：用户填了 `READY_FOR_CLOUD_SMOKE_RUN`，但 billing / auto-charge / cost estimate / cancellation / deletion / data policy 仍多项 `UNKNOWN`。本阶段在 `account-billing-preflight.md` 与 `credit-billing-verification.md` 同时留档「声明 READY」与「多项 UNKNOWN」两件事，避免把单方声明误读为系统已就绪。
2. **`cloud_launch_allowed` 必须保持 `false`**：本阶段硬边界第 16 条明确禁止把 `cloud_launch_allowed` 改为 `true`；真正允许 launch 必须在 ATL-4C（guarded cloud smoke preflight）或后续阶段，由更严格的 guard 显式升级。
3. **下一阶段不是 launch**：是 **ATL-4C guarded cloud smoke preflight**——只做"在更严格 guard 下准备 preflight"，仍然 **not** immediate launch。

## 明确边界声明

- **未调用 Castform API**（无网络调用）
- **未上传任何数据**（`smoke-*.preview.jsonl` 仍为 preview-only，本阶段未触发 upload）
- **未启动 Castform training run**（`cloud_launch_allowed=false`，guard exit 1）
- **未创建 API key**（本仓库无 `CASTFORM_API_KEY`，无 `.env`）
- **未使用真实 CASTFORM_API_KEY**（无环境变量注入）
- **未创建 .env**（`.gitignore` 仍生效，仓库内无 `.env`）
- **未记录信用卡信息 / cookie / Authorization header / 用户邮箱 / 截图**（`credit-billing-verification.md` 与 `account-billing-preflight.md` 均不记录上述字段）
- **未运行 `upload_training_run` / `launch_training_run` / `TrainerClient`**
- **未训练模型**

## 已知限制

1. **billing / auto-charge / cost estimate / run controls / data policy 仍多项 UNKNOWN** —— 这是显式留档的 risk，**不会**被用户的 `READY` 声明自动覆盖。
2. **未进行任何真实 launch / upload / API call** —— 全部基于"用户人工 UI 可见性" + "本地脚本行为复核"。
3. **preview subset 仍为 ATL-2 redacted JSONL 的前 N 行**：train 8 行 + eval 2 行；不构成最终训练数据。
4. **ATL-2 合成样本比例 71%** 不变（与 ATL-3C / ATL-4A / ATL-4B-CONFIG 一致）。

## git 状态

- `git status --short`: 干净（本阶段 commit 后）
- 预期 commit 列表：
  1. `cases/castform-hermes-phase-closer-v0/credit-billing-verification.md` (new)
  2. `cases/castform-hermes-phase-closer-v0/account-billing-preflight.md` (modified)
  3. `cases/castform-hermes-phase-closer-v0/index.html` (modified)
  4. `data/cases.json` (modified)
  5. `README.md` (modified)
  6. `reports/ATL4A_CREDIT_FILL_REPORT.md` (new)

## 下一步建议

- **ATL-4C — Guarded cloud smoke preflight**（gated）：
  - 在更严格 guard 下准备"上传 + launch"的 preflight（仍不真实 launch）。
  - 显式升级 `cloud_launch_allowed` 必须由用户在 ATL-4C 内部通过 guarded 决策点完成。
  - 若用户在 ATL-4C 仍要求 launch，系统必须再次确认 billing / cost visibility 已可见（哪怕是 `UNKNOWN` 也必须用户再次确认）。
- 或在 ATL-4C 之前**回填更多 UNKNOWN 字段**（cost estimate / cancellation / data policy 等），让 guarded preflight 有更多事实依据。

## 风险评估

- **关键风险**：用户单方声明 `READY` 容易被误读为"系统已确认就绪"——本阶段已通过 `risk note` 显式留档 `READY` + `UNKNOWN` 共存的事实，并在 guard 状态中重申 `cloud_launch_allowed=false`。
- **缓解措施**：`cloud_launch_guard.py` 仍是默认拒绝 launch 的 exit 1；任何对 `cloud_launch_allowed` 的修改都必须经由 ATL-4C 的 guarded decision point 显式触发。
- **状态**：**launch 仍然 blocked**；本阶段不引入任何 new risk。
