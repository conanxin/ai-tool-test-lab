#!/usr/bin/env python3
"""
new_case.py — 新增测试案例脚手架

用法：
    python3 scripts/new_case.py "Project Name"

自动创建：
    cases/<slug>/index.html
    cases/<slug>/test-plan.md
    cases/<slug>/local-readiness.md
    cases/<slug>/CASE_CLOSEOUT.md       (placeholder)
    cases/<slug>/support-request.md    (placeholder)

然后提示用户手动更新 data/cases.json。

Canonical example:
    Use Castform Hermes Phase Closer v0 as the canonical workflow example.
    See docs/CASE_WORKFLOW_STANDARD.md for full lifecycle.
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

    print("Use Castform Hermes Phase Closer v0 as the canonical workflow example.")
    print("See docs/CASE_WORKFLOW_STANDARD.md for the full lifecycle.")
    print()

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
    <h2>Case Status</h2>
    <p>phase: ATL-0</p>
    <p>status: Local scaffold ready</p>
    <p>final status: （待填）</p>
    <p>updated_at: （待填）</p>
  </div>

  <div class="section">
    <h2>Why This Tool</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>What We Want To Test</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Local Role</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Cloud / External Role</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Account / Billing Notes</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Data / Input Plan</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Local Validation</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>External Run / Cloud Run</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Monitoring</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Failure Analysis</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Closeout</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Evidence</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Reports</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Support Request</h2>
    <p>（待填写）</p>
  </div>

  <div class="section">
    <h2>Sensitive Information Exclusion</h2>
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

## 参考

- 参见 `docs/CASE_WORKFLOW_STANDARD.md`（10 阶段 lifecycle）
- 参见 `docs/CASE_PHASES.md`（阶段命名规则）
- 参见 `cases/castform-hermes-phase-closer-v0/`（canonical example）
""")

    local_readiness = case_dir / "local-readiness.md"
    with open(local_readiness, "w", encoding="utf-8") as f:
        f.write(f"""# {name} — 本地环境评估

## 操作系统

（待填写）

## 硬件

（待填写）

## 已有依赖

（待填写）

## 本地能做什么

（待填写）

## 本地不能做什么

（待填写）

## 是否需要云端 / API / GPU / 账号

（待填写）

## 风险评估

（待填写）
""")

    case_closeout = case_dir / "CASE_CLOSEOUT.md"
    with open(case_closeout, "w", encoding="utf-8") as f:
        f.write(f"""# {name} — Final Case Closeout

## Final Status

（PASS_COMPLETED / PASS_WITH_LIMITATIONS / PAUSED_PENDING_VENDOR_FEEDBACK / PAUSED_PENDING_BACKEND_LOGS / BLOCKED_BY_ACCOUNT_OR_BILLING / BLOCKED_BY_LOCAL_ENVIRONMENT / FAILED_REPRODUCIBLE / ARCHIVED_NO_FURTHER_ACTION 之一）

## What Tested

（待填写）

## Local Successes

（待填写）

## Cloud / External Successes

（待填写）

## Cloud / External Failure

（待填写）

## Ruled Out

（待填写）

## Not Yet Ruled Out

（待填写）

## Final Decision

（待填写）

## Optional Future Action

（待填写）

## Sensitive Information Exclusion

API key / API key 前缀 / 信用卡 / cookie / Authorization header / 用户邮箱 / 截图含敏感信息 — 均未记录在仓库中。
""")

    support_request = case_dir / "support-request.md"
    with open(support_request, "w", encoding="utf-8") as f:
        f.write(f"""# {name} — Support Request

## What Worked

（待填写）

## What Failed

（待填写）

## Request

（待填写）

## Sensitive Information Exclusion

API key / API key 前缀 / 信用卡 / cookie / Authorization header / 用户邮箱 / 截图含敏感信息 — 均未包含在本请求中。
""")

    print(f"Created: cases/{slug}/index.html")
    print(f"Created: cases/{slug}/test-plan.md")
    print(f"Created: cases/{slug}/local-readiness.md")
    print(f"Created: cases/{slug}/CASE_CLOSEOUT.md (placeholder)")
    print(f"Created: cases/{slug}/support-request.md (placeholder)")
    print()
    print("Next step: manually update data/cases.json with:")
    print(f'  {{"slug": "{slug}", "title": "{name}", "status": "Local scaffold ready", "category": "（填写类别）", "canonical_example": false, "workflow_reference": false, "final_status": null}}')
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/new_case.py \"Project Name\"", file=sys.stderr)
        return 1
    name = sys.argv[1]
    return create_case(name)


if __name__ == "__main__":
    sys.exit(main())