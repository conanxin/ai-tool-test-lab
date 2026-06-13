# ATL-STD-1 报告：Standardize future case workflow from Castform example

## 阶段结论

**PASS_CASE_WORKFLOW_STANDARDIZED**

## 当前基线

- baseline commit: `951c4c5`（ATL-CLOSEOUT: Close Castform case pending backend logs）

## 目标

基于第一个完整案例 Castform Hermes Phase Closer v0，总结并固化 AI Tool Test Lab 的标准测试流程。要求以后所有 AI 工具 / 平台 / 开源项目测试，都必须参考 Castform 第一个案例的结构、阶段记录、页面呈现、报告归档、验证脚本、失败收口和最终 closeout 方式。

## 新增文档

| 文档 | 路径 | 用途 |
|------|------|------|
| Case Workflow Standard | `docs/CASE_WORKFLOW_STANDARD.md` | 10 阶段 lifecycle + 强制原则 + Required Final Status Values |
| Case Phases | `docs/CASE_PHASES.md` | 阶段命名规则（ATL-0 ~ ATL-CLOSEOUT） |

## 更新文件

| 文件 | 改动 |
|------|------|
| `docs/CASE_TEMPLATE.md` | 升级为 Castform-style 模板（16 节固定结构） |
| `docs/ADDING_A_NEW_CASE.md` | 增加 Castform canonical example 说明 + 强制原则 + 8 步流程 |
| `README.md` | 新增 "Case workflow standard" section + 相关文档链接 |
| `index.html` | 新增 "Case workflow standard" 模块 |
| `cases/castform-hermes-phase-closer-v0/index.html` | 在 Final Closeout 段顶部增加 canonical example note |
| `data/cases.json` | Castform case 增加 `canonical_example=true` / `workflow_reference=true` / `final_status=PAUSED_PENDING_CASTFORM_BACKEND_LOGS` |
| `scripts/new_case.py` | 升级：自动创建 5 个文件（index.html / test-plan.md / local-readiness.md / CASE_CLOSEOUT.md / support-request.md）+ 提示 Castform canonical example + 提示使用 docs/CASE_WORKFLOW_STANDARD.md |
| `scripts/validate_site.py` | 扩展：检查 canonical_example=true + Castform canonical_example=true + Castform workflow_reference=true + docs/CASE_WORKFLOW_STANDARD.md 存在 + docs/CASE_PHASES.md 存在 |

## Castform canonical example 说明

Castform Hermes Phase Closer v0 现在正式被标记为本项目的 canonical example：

- `data/cases.json` 中 `canonical_example = true`
- `data/cases.json` 中 `workflow_reference = true`
- `data/cases.json` 中 `final_status = PAUSED_PENDING_CASTFORM_BACKEND_LOGS`
- 案例页 Final Closeout 段顶部新增 "Canonical example note" 提示框
- 首页新增 "Case workflow standard" 模块明确指向 Castform
- README 新增 "Case workflow standard" section 列出 Castform 作为 canonical example

未来任何 AI 工具 / 平台 / 开源项目测试都将参照本案例的 16 节模板 + 10 阶段 lifecycle + ATL-N 阶段命名。

## 未来 case workflow 标准

1. 一个测试项目对应一个 case 页面（只展示结论，不堆原始日志）
2. 每个 case 必须有独立目录（cases/<slug>/）
3. 每个关键阶段必须有报告（命名格式：ATL-N_*_REPORT.md）
4. 每次执行必须写清：为什么做、做了什么、本地承担什么、云端承担什么、成功证据、失败证据、风险边界、下一步
5. 失败不能只写"失败"，必须记录：已排除的原因、未排除的原因、需要 support / backend logs / vendor feedback 的地方
6. 每个 case 最终必须 closeout（CASE_CLOSEOUT.md + reports/FINAL_*_REPORT.md + data/cases.json final_status 字段）

## 验证结果

| 脚本 | 结果 |
|------|------|
| validate_jsonl.py | PASS |
| validate_site.py | PASS（含 ATL-STD-1 canonical_example 扩展检查） |
| check_secrets.py | PASS |
| validate_case_closeout.py | PASS |
| validate_castform_local_scaffold.py | PASS |
| validate_atl3c_sdk_mapping.py | PASS |
| validate_atl4a_preflight_scaffold.py | PASS |
| validate_atl4b_cloud_smoke_config.py | PASS |
| validate_atl4c_guarded_preflight.py | PASS |
| validate_atl5_cloud_smoke_result.py | PASS |
| validate_atl5a_launch_args_fix.py | PASS |
| validate_atl5b_second_upload_retry_result.py | PASS |
| validate_atl5c_failed_step0_record.py | PASS |
| validate_atl5d_support_bundle.py | PASS |
| validate_atl6_starter_style_redeploy.py | PASS |
| validate_atl6c_support_request.py | PASS |

敏感信息 grep 检查（按用户给定命令扫描所有项目文件，排除 .venv）：

执行用户 spec 第 14 步规定的 repo-wide grep 命令（grep pattern 字面以避免误读，禁止任何前缀/片段出现在 commit 内容中）：

```text
# command pattern: forbidden key prefix (literal key-shape pattern)
# 执行结果: zero hits → no real key prefix leaked across repo
```

## git status

```text
M README.md
M docs/CASE_TEMPLATE.md
M docs/ADDING_A_NEW_CASE.md
M index.html
M cases/castform-hermes-phase-closer-v0/index.html
M data/cases.json
M scripts/new_case.py
M scripts/validate_site.py
?? docs/CASE_WORKFLOW_STANDARD.md
?? docs/CASE_PHASES.md
?? reports/ATL_STD1_CASE_WORKFLOW_STANDARD_REPORT.md
```

## commit hash

- baseline commit: `951c4c5`
- ATL-STD-1 commit: `8404f8b`

## 是否 push

- push status: SUCCESS（`951c4c5..8404f8b main -> main`）
- Pages URL: <https://conanxin.github.io/ai-tool-test-lab/> · HTTP/2 200
- Castform 案例页 URL: <https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/> · HTTP/2 200
- 首页 "Case workflow standard" 段已上线（1 hit）
- 案例页 "Canonical example note" 段已上线（1 hit）

## 明确说明

- 未调用 Castform API
- 未上传数据
- 未训练
- 未访问 Castform UI
- 未读取 API key
- 未记录敏感信息（API key / 信用卡 / cookie / Authorization header / 用户邮箱 / 截图均未记录）
- 未删除 Castform 历史 result JSON（3 个 result JSON 全部保留）
- 未删除 Castform 历史报告
- 未改写 Castform 案例结论
- 未提交 .venv
- 未创建 .env

## 下一步建议

选择 AI Tool Test Lab 第二个测试案例。可以从以下候选中选择：

- 其他 RL post-training 平台（如 OpenPipe / Steerable / etc.）
- LLM inference 平台（如 Groq / Together / etc.）
- 本地 LLM 微调框架（如 unsloth / axolotl / llama-factory）
- Agent 评估框架（如 inspect / agent-eval / etc.）

无论选择哪个，必须遵循 Castform canonical example 的 10 阶段 lifecycle + 16 节模板。