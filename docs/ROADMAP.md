# 项目路线图

## Castform Case (ATL-0 → ATL-CLOSEOUT) — 2025-06-12 → 2026-06-13

- **ATL-0**：本地 scaffold ✅ 已完成 — 创建 ai-tool-test-lab 项目结构 / 编写首页、案例页面、文档、脚本 / 创建合成样本 / 编写 reward rubric / 本地验证通过 / commit: d069f86
- **ATL-1**：公开发布准备 ✅ 已完成 — 完善首页 / 完善 Castform 案例页 / 新增 GitHub Pages 发布文档 / 新增项目路线图 / 更新 README / 增强样式 / commit
- **ATL-1P**：首次发布 ✅ 已完成 — 发布到 GitHub，启用 GitHub Pages
- **ATL-2**：Castform 本地样本准备 ✅ 已完成 — 42 train + 7 eval 合成脱敏样本 / 覆盖 PASS / FAIL / PARTIAL / ROLLBACK / BLOCKED / validate_jsonl PASS / 敏感信息扫描
- **ATL-3A/3B/3C**：Castform validate_env ✅ 已完成 — benchmax install + import / 真实本地 validate_env 10/10 PASS (api_key=None + local=True → 零网络)
- **ATL-4A/4B/4A-CREDIT-FILL/4C**：Account / Credit / Billing / Config / Guard ✅ 已完成 — 人工 preflight scaffold / cloud smoke dry configuration / credit $50 visible + usage page visible / guarded cloud smoke preflight (dual-gate 架构)
- **ATL-5-SCRIPT-PREP / ATL-5 / ATL-5A / ATL-5B**：Cloud smoke run ✅ 已完成 — 脚本准备 / 首次 launch FAILED (batch_size) / 修复 launcher_args (删除 batch_size, 增加 learning_rate: 1e-5) / 第二次 launch SUCCESS (run_id c83f971d-2b2c-42b8-9774-ca64938c1286)
- **ATL-5C / ATL-5D**：UI 观察 + support bundle ✅ 已完成 — UI observed failed at step 0 / support-ready failure bundle 准备
- **ATL-6A / ATL-6 / ATL-6B / ATL-6C**：Starter-style redeploy ✅ 已完成 — 16/4 dataset / no-tools env / 0.0~1.0 reward / 第二次 launch SUCCESS (run_id 56cb5701-6b3e-424e-b671-fc2efc932aa8) / UI 仍 failed at step 0 / support request prepared
- **ATL-CLOSEOUT**：✅ 已完成 (2026-06-13) — final closeout · `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` · no further cloud runs planned · support request ready · 详见 [cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md](../cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md) + [reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md](../reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md)

## Castform case closed for now

- 当前状态: `PAUSED_PENDING_CASTFORM_BACKEND_LOGS`
- 不再继续 cloud attempts（不再 upload / launch / 重复 retry）
- Optionally send `cases/castform-hermes-phase-closer-v0/CASTFORM_SUPPORT_REQUEST_FINAL.md` 到 Castform Castie/support，询问 backend worker bootstrap log (覆盖两个 run_id)
- **Castform can resume only after support / backend logs**（得到根因后进入 ATL-6D root cause fix / ATL-7 阶段）

## Next possible case

- **Next**: choose another AI tool / platform when ready
- 运行 `scripts/new_case.py` 创建第二个案例页面
- 填写案例页面 / 更新 `data/cases.json` / 运行 `validate_site.py` / 生成报告

## Final deliverables status

- ✅ Open-source test lab published: `https://conanxin.github.io/ai-tool-test-lab/`
- ✅ Castform case page published: `https://conanxin.github.io/ai-tool-test-lab/cases/castform-hermes-phase-closer-v0/`
- ✅ Local SDK path validated: `benchmax.platform.validation.validate_env` real local 10/10 PASS
- ✅ Cloud upload / launch validated: 2 real Castform training runs created (SDK level)
- ✅ Repeated cloud step 0 failure captured: 2 independent run_ids both `failed` at step 0
- ✅ Support request prepared: paste-ready 英文简短版本 + 详细版本

## Final blockers

- Repeated step 0 failure before rollouts (both runs)
- Backend logs required (likely category `FAILED_UNKNOWN_WORKER_BOOTSTRAP_OR_PLATFORM`)

## Security notes (final)

- API key 未记录（前缀/片段均未记录）
- 未提交 .env
- 未提交 .venv
- 未记录信用卡 / cookie / Authorization header / 用户邮箱 / 截图
- 不伪造根因
- 不伪造 metrics
- 不删除历史 result JSON
- 不删除旧 run 信息
