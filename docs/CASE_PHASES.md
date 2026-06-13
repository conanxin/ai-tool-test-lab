# Case Phases — AI Tool Test Lab 阶段命名规则

## 说明

本文档以 Castform Hermes Phase Closer v0 为例，定义 case 阶段的命名规则。
未来其他项目不一定完全使用同样编号，但必须保持同样思想：

- 每一阶段有目标
- 每一阶段有边界
- 每一阶段有报告
- 每一阶段有验证
- 每一阶段有下一步

## Castform 阶段命名表

| 阶段编号 | 阶段名称 | 目标 |
|----------|----------|------|
| ATL-0 | scaffold | 创建项目结构、首页、案例页、文档、验证脚本 |
| ATL-1 | public page readiness | 完善样式、文档、README，适合 GitHub Pages |
| ATL-1P | publish | 创建 GitHub repo，push main，启用 Pages |
| ATL-2 | local dataset / input prep | 生成脱敏 JSONL 样本，train/eval 切分 |
| ATL-3 | local SDK / local validation | 验证 dataset/reward/environment 结构 |
| ATL-4 | account / billing / guarded config | API key 注入规则、cost guard、launch guard |
| ATL-5 | first external run | 第一次受保护的云端 smoke run |
| ATL-5A | fix and retry (launch args) | 修复 launcher_args，准备 ATL-5B retry |
| ATL-5B | second upload + launch retry | 第二次 upload + launch retry |
| ATL-6 | redeploy / second attempt | starter-style 风格的独立 redeploy |
| ATL-6A | starter-style redeploy prep | starter-task 风格的 redeploy 准备 |
| ATL-6B | starter-style redeploy result | 把 ATL-6 的 result 转录到 case page |
| ATL-6C | support request (dual run) | 跨两个 run_id 的支持请求 |
| ATL-CLOSEOUT | final closeout | 最终收口，标记 PAUSED / PASS / FAIL |

## 通用阶段模式

### Discovery → Local Readiness → Public Scaffold

每个 case 都要经历：

1. **Discovery** — 为什么测、能解决什么问题、与现有项目的关系
2. **Local Readiness** — 本地能做 / 不能做 / 是否需要云端 / GPU / 账号
3. **Public Scaffold** — 创建 case 目录、case 页面、test-plan、local-readiness、reports/

### Local Validation → Cloud Preflight → Guarded Cloud Run

任何涉及云端或外部平台的 case 都要经历：

1. **Local Validation** — 本地脚本、dry-run、smoke test
2. **Cloud Preflight** — API key、credit、billing、cost guard、launch guard
3. **Guarded Cloud Run** — 默认 blocked、显式授权、最小样本、一次一个 run

### Monitoring → Failure Analysis → Support Request → Closeout

任何真实外部执行的 case 都要经历：

1. **Monitoring** — run_id / URL / 状态 / 成功失败证据
2. **Failure Analysis** — 已排除 / 未排除 / likely category
3. **Support Request** — 整理为可粘贴给 vendor 的请求
4. **Closeout** — 最终状态、what worked / failed、risks、next action

## 阶段文档强制要求

每个阶段产出：

- 阶段报告：`reports/ATL<N>_<DESCRIPTION>_REPORT.md`
- 阶段验证：相关 `validate_atl<N>_<x>.py` 必须 PASS
- 阶段 commit：每阶段独立 commit（方便审计追溯）
- 阶段 push：可 push / Pages 验证（不强制）

## 阶段间不变量

任何 ATL-N+1 阶段开始前：

- ATL-N 阶段的 report 必须存在
- ATL-N 阶段的 validator 必须 PASS
- ATL-N 阶段的 commit 必须落盘
- data/cases.json 中 case 的 phase / status 字段必须同步更新
- 不删除 ATL-N 历史 result JSON / 报告 / run 信息