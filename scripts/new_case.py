#!/usr/bin/env python3
"""
new_case.py — 新增测试案例脚手架

用法：
    python3 scripts/new_case.py "Project Name"

自动创建：
    cases/<slug>/index.html
    cases/<slug>/test-plan.md

然后提示用户手动更新 data/cases.json。
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CASES_DIR = PROJECT_ROOT / "cases"


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def create_case(name):
    slug = slugify(name)
    if not slug:
        print("FAIL: cannot create slug from empty name", file=sys.stderr)
        return 1

    case_dir = CASES_DIR / slug
    if case_dir.exists():
        print(f"FAIL: case directory already exists: {case_dir}", file=sys.stderr)
        return 1

    case_dir.mkdir(parents=True)

    index_html = case_dir / "index.html"
    with open(index_html, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} | AI Tool Test Lab</title>
<link rel="stylesheet" href="../../assets/css/style.css">
<style>
  .case-page {{ max-width: 800px; margin: 0 auto; }}
  .back {{ display: inline-block; margin-bottom: 1rem; color: var(--accent); text-decoration: none; font-size: 0.9rem; }}
  .section {{ margin: 2rem 0; }}
  .section h2 {{ font-size: 1.2rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; margin-bottom: 1rem; }}
  .section p {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 0.6rem; }}
</style>
</head>
<body>
<div class="case-page">
  <a href="../../index.html" class="back">&larr; 返回首页</a>
  <h1>{name}</h1>
  <p style="color:var(--muted)">状态: Local scaffold ready</p>

  <div class="section">
    <h2>项目概览</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>测试目的</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>本地环境</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>安装过程</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>核心功能测试</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>成本与限制</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>问题记录</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>结论</h2>
    <p>（待填写）</p>
  </div>
</div>
</body>
</html>
""")

    test_plan = case_dir / "test-plan.md"
    with open(test_plan, "w", encoding="utf-8") as f:
        f.write(f"""# {name} — 测试计划

## 目标

（待填写）

## 阶段划分

### Phase 0：本地 scaffold
- （待填写）

### Phase 1：数据准备
- （待填写）

### Phase 2：本地验证
- （待填写）

### Phase 3：云端测试
- （待填写）

## 风险控制

- （待填写）
""")

    print(f"Created: cases/{slug}/index.html")
    print(f"Created: cases/{slug}/test-plan.md")
    print()
    print("Next step: manually update data/cases.json with:")
    print(f'  {{"slug": "{slug}", "title": "{name}", "status": "Local scaffold ready", "category": "（填写类别）"}}')
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/new_case.py \"Project Name\"", file=sys.stderr)
        return 1
    name = sys.argv[1]
    return create_case(name)


if __name__ == "__main__":
    sys.exit(main())
