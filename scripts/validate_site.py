#!/usr/bin/env python3
"""
validate_site.py — 验证站点完整性

标准库 only，输出 PASS / FAIL。

ATL-STD-1 扩展：
- 检查 data/cases.json 中至少有一个 canonical_example = true 的 case
- 检查 Castform case canonical_example = true
- 检查 docs/CASE_WORKFLOW_STANDARD.md 存在
- 检查 docs/CASE_PHASES.md 存在
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

REQUIRED_ROOT = ["index.html", "README.md", "LICENSE", ".gitignore"]
REQUIRED_DOCS = [
    "ARCHITECTURE.md",
    "CASE_TEMPLATE.md",
    "ADDING_A_NEW_CASE.md",
    "CASTFORM_NOTES.md",
    "CASE_WORKFLOW_STANDARD.md",
    "CASE_PHASES.md",
]
REQUIRED_SCRIPTS = ["validate_site.py", "check_secrets.py", "new_case.py"]

CASE_REQUIRED_FIELDS = ["title", "status", "category", "slug"]

CANONICAL_CASE_SLUG = "castform-hermes-phase-closer-v0"


def fail(msg):
    print(f"FAIL: {msg}")
    return False


def ok(msg):
    print(f"  OK: {msg}")
    return True


def check_files():
    r = True
    for f in REQUIRED_ROOT:
        if not (PROJECT_ROOT / f).exists():
            r = fail(f"root file missing: {f}") and r
        else:
            ok(f"root file: {f}")
    for f in REQUIRED_DOCS:
        p = PROJECT_ROOT / "docs" / f
        if not p.exists():
            r = fail(f"doc missing: docs/{f}") and r
        else:
            ok(f"doc: docs/{f}")
    for f in REQUIRED_SCRIPTS:
        p = PROJECT_ROOT / "scripts" / f
        if not p.exists():
            r = fail(f"script missing: scripts/{f}") and r
        else:
            ok(f"script: scripts/{f}")
    return r


def check_cases_json():
    p = PROJECT_ROOT / "data" / "cases.json"
    if not p.exists():
        return fail("data/cases.json missing")
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return fail(f"cases.json invalid JSON: {e}")

    cases = data.get("cases")
    if not isinstance(cases, list):
        return fail("cases.json missing 'cases' list")

    r = True
    for case in cases:
        for key in CASE_REQUIRED_FIELDS:
            if key not in case:
                r = fail(f"case missing field '{key}': {case}") and r
        slug = case.get("slug")
        if slug:
            case_index = PROJECT_ROOT / "cases" / slug / "index.html"
            if not case_index.exists():
                r = fail(f"case page missing: cases/{slug}/index.html") and r
            else:
                ok(f"case page: cases/{slug}/index.html")
    return r


def check_canonical_example():
    """ATL-STD-1 扩展：检查至少有一个 canonical_example=true 的 case。"""
    p = PROJECT_ROOT / "data" / "cases.json"
    if not p.exists():
        return fail("data/cases.json missing (canonical_example check)")
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return fail(f"cases.json invalid JSON: {e}")

    cases = data.get("cases", [])
    if not cases:
        return fail("cases.json has empty cases list")

    r = True
    canonical_cases = [c for c in cases if c.get("canonical_example") is True]
    if not canonical_cases:
        r = fail("no case has canonical_example = true") and r
    else:
        ok(f"canonical_example count: {len(canonical_cases)}")

    castform = next((c for c in cases if c.get("slug") == CANONICAL_CASE_SLUG), None)
    if castform is None:
        r = fail(f"canonical case missing: {CANONICAL_CASE_SLUG}") and r
    elif castform.get("canonical_example") is not True:
        r = fail(f"Castform case canonical_example != true") and r
    else:
        ok(f"Castform case canonical_example = true")

    if castform and castform.get("workflow_reference") is not True:
        r = fail("Castform case workflow_reference != true") and r
    elif castform:
        ok("Castform case workflow_reference = true")

    return r


def main():
    print("=== validate_site.py ===")
    results = [
        check_files(),
        check_cases_json(),
        check_canonical_example(),
    ]
    if all(results):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())