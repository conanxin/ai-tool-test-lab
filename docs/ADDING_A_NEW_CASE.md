# 如何新增一个测试案例

## 参考 Canonical Example

**Castform Hermes Phase Closer v0** 是本项目的 canonical example。
新增任何 case 之前，必须先阅读：

- `cases/castform-hermes-phase-closer-v0/` — 完整 case 目录
- `cases/castform-hermes-phase-closer-v0/CASE_CLOSEOUT.md` — 最终收口文档
- `cases/castform-hermes-phase-closer-v0/index.html` — 案例详情页（结论式呈现）
- `reports/ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md` — 最终阶段报告
- `docs/CASE_WORKFLOW_STANDARD.md` — case workflow 标准
- `docs/CASE_PHASES.md` — 阶段命名规则

## 步骤

### 1. 运行脚手架脚本

```bash
python3 scripts/new_case.py "Project Name"
```

脚手架脚本会自动创建：

- `cases/<slug>/index.html` — 案例详情页（Castform-style）
- `cases/<slug>/test-plan.md` — 测试计划
- `cases/<slug>/local-readiness.md` — 本地环境评估
- `cases/<slug>/CASE_CLOSEOUT.md` — 最终收口文档 placeholder
- `cases/<slug>/support-request.md` — 支持请求 placeholder

脚本会提示使用 Castform 作为 canonical example。

### 2. 填写案例内容

参照 `docs/CASE_TEMPLATE.md`，按 16 节 Castform-style 结构填写：

- Case Status
- Why This Tool
- What We Want To Test
- Local Role
- Cloud / External Role
- Account / Billing Notes
- Data / Input Plan
- Local Validation
- External Run / Cloud Run
- Monitoring
- Failure Analysis
- Closeout
- Evidence
- Reports
- Support Request
- Sensitive Information Exclusion

### 3. 创建阶段报告

每个阶段完成后，在 `reports/` 目录创建报告，命名格式：

```text
ATL<N>_<DESCRIPTION>_REPORT.md
```

### 4. 更新案例列表

编辑 `data/cases.json`，新增案例元数据：

```json
{
  "slug": "some-tool-v1",
  "title": "Some Tool — Test v1",
  "phase": "ATL-0",
  "status": "Local scaffold ready",
  "category": "（填写类别）",
  "local_role": "本地负责的内容",
  "cloud_role": "云端负责的内容",
  "summary": "（简短描述）",
  "updated_at": "2026-06-13",
  "canonical_example": false,
  "workflow_reference": false,
  "final_status": null
}
```

### 5. 验证

每个阶段完成后必须运行 validators：

```bash
python3 scripts/validate_jsonl.py
python3 scripts/validate_site.py
python3 scripts/check_secrets.py
python3 scripts/validate_case_closeout.py
```

如适用，运行其他 ATL-N 验证器。

### 6. 提交

每阶段独立 commit（不与下一阶段合并）：

```bash
git add cases/<case>/
git add data/cases.json
git add reports/ATL<N>_<DESCRIPTION>_REPORT.md
git commit -m "ATL-<N>: <description>"
```

### 7. Push + Pages 验证（可选）

```bash
git push
```

等待 60-90 秒 CDN 缓存后验证：

```bash
curl -I https://conanxin.github.io/ai-tool-test-lab/
curl -I https://conanxin.github.io/ai-tool-test-lab/cases/<case>/
```

### 8. 最终 closeout

case 测试完成后，必须写：

- `cases/<case>/CASE_CLOSEOUT.md` — 最终收口文档
- `reports/FINAL_<CASE>_CLOSEOUT_REPORT.md` — 最终阶段报告
- 更新 `data/cases.json` 中的 `final_status` 字段

## 强制原则

- **不要把 API key 写进项目**
- **不要上传敏感数据**
- **不要跳过本地验证**
- **不要直接大规模云端测试**
- **不要失败后无限重试**
- **不要没有 closeout 就开启下一个项目**
- **不要伪造 metrics / failure reason / root cause**
- **不要删除历史 result JSON / 报告 / run 信息**

## 注意事项

- 案例 ID 使用小写字母、数字和连字符
- 所有样本数据必须脱敏，不含真实项目信息
- 绝不提交 API key、token、密码到仓库
- 测试完成后再更新 `status` 为最终状态
- 最终状态必须使用 `final_status` 字段（PASS_COMPLETED / PAUSED_PENDING_BACKEND_LOGS 等）