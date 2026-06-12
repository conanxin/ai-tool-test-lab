# 架构说明

## 设计原则

1. **静态优先**：纯 HTML/CSS/JS，无构建工具，适合 GitHub Pages
2. **单页记录**：每个测试案例一个独立页面，完整记录全过程
3. **数据驱动**：首页通过 JSON 加载案例列表，便于扩展
4. **安全边界**：所有敏感信息（API key、token）绝不提交到仓库

## 目录结构

```
ai-tool-test-lab/
  index.html              # 首页，加载 data/cases.json
  assets/
    css/style.css         # 全局样式
    js/app.js             # 首页案例列表渲染
  data/
    cases.json            # 案例元数据
  cases/
    <case-id>/
      index.html          # 案例详情页
      test-plan.md        # 测试计划
      local-readiness.md  # 本地环境评估
      reward-rubric.md    # 评分标准
      sample-*.jsonl      # 样本数据
      *.py                # 脚本/stub
  docs/
    ARCHITECTURE.md       # 本文档
    CASE_TEMPLATE.md      # 新增案例模板
    ADDING_A_NEW_CASE.md  # 新增案例指南
    CASTFORM_NOTES.md     # Castform 专项笔记
  scripts/
    validate_site.py      # 站点完整性验证
    check_secrets.py      # 敏感信息扫描
    new_case.py           # 新增案例脚手架
  reports/
    *.md                  # 阶段报告
```

## 扩展方式

新增案例时：
1. 运行 `python scripts/new_case.py`
2. 按 `docs/CASE_TEMPLATE.md` 填写内容
3. 更新 `data/cases.json`
4. 运行 `python scripts/validate_site.py`

## 部署

直接推送到 GitHub，启用 GitHub Pages（从 main 分支根目录部署）。
