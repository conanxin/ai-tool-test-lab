# 如何新增一个测试案例

## 步骤

### 1. 运行脚手架脚本

```bash
python scripts/new_case.py
```

按提示输入：
- 案例 ID（如 `some-tool-v1`）
- 案例名称
- 测试类型
- 本地角色
- 云端角色

脚本会自动创建：
- `cases/<case-id>/index.html`
- `cases/<case-id>/test-plan.md`
- `cases/<case-id>/local-readiness.md`
- `cases/<case-id>/reward-rubric.md`（如适用）

### 2. 填写案例内容

参照 `docs/CASE_TEMPLATE.md`，编辑以下文件：
- `cases/<case-id>/index.html` — 案例详情页
- `cases/<case-id>/test-plan.md` — 测试计划
- `cases/<case-id>/local-readiness.md` — 本地环境评估

### 3. 更新案例列表

编辑 `data/cases.json`，新增案例元数据：

```json
{
  "id": "some-tool-v1",
  "title": "Some Tool — Test v1",
  "path": "cases/some-tool-v1/index.html",
  "status": "Local scaffold ready",
  "type": "类别",
  "local_role": "本地负责的内容",
  "cloud_role": "云端负责的内容",
  "phase": "当前阶段"
}
```

### 4. 验证站点完整性

```bash
python scripts/validate_site.py
```

检查项：
- 所有案例页面存在
- data/cases.json 格式正确
- 所有链接可访问
- 无敏感信息泄露

### 5. 生成报告

在 `reports/` 目录创建阶段报告，命名格式：
`<PHASE>_<CASE_ID>_<DESCRIPTION>_REPORT.md`

### 6. 提交（可选）

```bash
git add data/cases.json cases/<case-id>/
git commit -m "add case: <case-id>"
```

## 注意事项

- 案例 ID 使用小写字母、数字和连字符
- 所有样本数据必须脱敏，不含真实项目信息
- 绝不提交 API key、token、密码到仓库
- 测试完成后再更新 `status` 为最终状态
