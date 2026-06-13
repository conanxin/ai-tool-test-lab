# AI Tool Test Lab — Case Workflow Standard

## 说明

Castform Hermes Phase Closer v0 是本项目的 canonical example。
以后每个测试项目都必须遵循同样的记录思路：

- 一个测试项目对应一个 case 页面
- 每个 case 必须有独立目录
- 每个关键阶段必须有报告
- 每次执行必须写清：
  - 为什么做
  - 做了什么
  - 本地环境承担什么
  - 云端 / 外部平台承担什么
  - 成功证据
  - 失败证据
  - 风险边界
  - 下一步
- 如果失败，不能只写"失败"，必须记录：
  - 已排除的原因
  - 未排除的原因
  - 需要 support / backend logs / vendor feedback 的地方
- 每个 case 最终必须 closeout

## Standard Case Lifecycle

### 1. Discovery / Background

- 工具是什么
- 为什么测试
- 适合解决什么问题
- 与用户现有项目的关系

### 2. Local Readiness

- 本地电脑能做什么
- 本地电脑不能做什么
- 是否需要云端 / API / GPU / 账号

### 3. Public Case Scaffold

- 创建 case 页面
- 创建 test-plan.md
- 创建 local-readiness.md
- 创建 reports/
- 更新 data/cases.json

### 4. Dataset / Input Preparation

- 样本来源
- 数据脱敏
- 样本数量
- train / eval 切分
- 不上传敏感信息

### 5. Local Validation

- 本地脚本验证
- 本地 dry-run
- 本地 smoke test
- 失败要记录 blocked reason

### 6. Account / Billing / API Preflight

- 是否需要 API key
- 是否有免费额度
- 是否需要绑卡
- 是否会自动扣费
- API key 不进项目、不进报告、不发聊天

### 7. Guarded Cloud / External Run

- 默认 blocked
- 必须显式授权
- 必须有 gate
- 必须最小样本
- 一次只做一个 run
- 不重复 launch

### 8. Monitoring

- 记录 run_id / URL
- 记录状态
- 记录成功 / 失败证据
- 不伪造 metrics

### 9. Failure Analysis

- 记录已排除项
- 记录未排除项
- 创建 support-ready request
- 等 vendor / backend logs

### 10. Closeout

- 最终状态
- what worked
- what failed
- evidence
- risks
- next action
- 是否暂停

## Required Final Status Values

每个 case 在 `data/cases.json` 必须使用以下枚举之一：

- `PASS_COMPLETED`
- `PASS_WITH_LIMITATIONS`
- `PAUSED_PENDING_VENDOR_FEEDBACK`
- `PAUSED_PENDING_BACKEND_LOGS`
- `BLOCKED_BY_ACCOUNT_OR_BILLING`
- `BLOCKED_BY_LOCAL_ENVIRONMENT`
- `FAILED_REPRODUCIBLE`
- `ARCHIVED_NO_FURTHER_ACTION`

## Required Final Artifacts

每个 case 最终必须包含：

- `cases/<case>/index.html` — 案例详情页（只展示结论，不堆全部原始日志）
- `cases/<case>/test-plan.md` — 测试计划
- `cases/<case>/local-readiness.md` — 本地环境评估
- `cases/<case>/CASE_CLOSEOUT.md` — 最终收口文档（强制要求）
- `cases/<case>/support-request.md` 或 `cases/<case>/support/` — failure / vendor feedback 文档
- `reports/FINAL_*_REPORT.md` — 最终阶段报告（强制要求）
- `data/cases.json` 中包含该 case 的所有元数据 + 最终状态

## Workflow 硬性原则

- 不要把 API key 写进项目
- 不要上传敏感数据
- 不要跳过本地验证
- 不要直接大规模云端测试
- 不要失败后无限重试
- 不要没有 closeout 就开启下一个项目
- 不要伪造 metrics / failure reason / root cause
- 不要删除历史 result JSON / 报告 / run 信息