# Case Template — Castform Style

新增测试案例时，按以下结构填写。
本模板以 Castform Hermes Phase Closer v0 为 canonical example。

## Case Status

- **phase**: 当前阶段（如 ATL-0 / ATL-3 / ATL-CLOSEOUT）
- **status**: 当前状态（如 Local scaffold ready / PASS / PAUSED）
- **final status**: 最终状态枚举（见下文"Required Final Status Values"）
- **updated_at**: 最后更新日期

## Why This Tool

- 这个工具 / 平台 / 开源项目是什么？
- 为什么测试它？
- 适合解决什么问题？

## What We Want To Test

- 准备测试哪些核心能力？
- 输入是什么？期望输出是什么？
- 边界条件是什么？

## Local Role

- 本地电脑能做什么？
- 本地电脑不能做什么？
- 本地需要承担什么？

## Cloud / External Role

- 云端 / 外部平台承担什么？
- 是否需要 GPU？
- 是否需要账号 / API key？

## Account / Billing Notes

- 是否需要 API key？
- 是否有免费额度？
- 是否需要绑卡？
- 是否会自动扣费？
- API key 不进项目、不进报告、不发聊天

## Data / Input Plan

- 样本来源
- 数据脱敏
- 样本数量
- train / eval 切分
- 不上传敏感信息

## Local Validation

- 本地脚本验证
- 本地 dry-run
- 本地 smoke test
- 失败要记录 blocked reason

## External Run / Cloud Run

- 是否执行了云端 smoke run？
- run_id / experiment_url
- run_name
- base model
- 样本数量
- result status

## Monitoring

- 轮询方式
- run_id / URL
- 状态（queued / running / completed / failed）
- step
- 成功 / 失败证据
- 不伪造 metrics

## Failure Analysis

- 已排除的原因
- 未排除的原因
- likely category
- 需要 vendor / backend logs / support 的地方

## Closeout

- 最终状态
- what worked
- what failed
- evidence
- risks
- next action
- 是否暂停

## Evidence

- run_id 列表
- 实验 URL 列表
- 成功截图 / 失败截图（如适用）
- on-disk result JSON 路径
- log 文件路径

## Reports

- 每个阶段的 report 路径
- reports/FINAL_*_REPORT.md 路径（强制要求）
- 阶段报告清单

## Support Request

- support-request.md 路径
- 支持请求包含的 run_id
- vendor / Castie 联系方式
- sensitive information exclusion 声明

## Sensitive Information Exclusion

明确列出本 case 不包含的内容：

- API key
- API key 前缀 / 片段
- 信用卡号 / CVV / 有效期
- cookie
- Authorization header
- 用户邮箱
- 截图含敏感信息

## Required Final Status Values

- PASS_COMPLETED
- PASS_WITH_LIMITATIONS
- PAUSED_PENDING_VENDOR_FEEDBACK
- PAUSED_PENDING_BACKEND_LOGS
- BLOCKED_BY_ACCOUNT_OR_BILLING
- BLOCKED_BY_LOCAL_ENVIRONMENT
- FAILED_REPRODUCIBLE
- ARCHIVED_NO_FURTHER_ACTION

## 强制要求

- 每个 case 必须最终有 `CASE_CLOSEOUT.md`
- 每个 case 必须最终有 `reports/FINAL_*_REPORT.md`
- 每个 case 如果失败，必须有 support request 或 failure summary
- 每个 case 页面要只展示结论，不堆全部原始日志
- 每个 case 的 `data/cases.json` 必须包含 canonical_example / workflow_reference / final_status 字段（如果有）

## 示例

参见 `cases/castform-hermes-phase-closer-v0/`。