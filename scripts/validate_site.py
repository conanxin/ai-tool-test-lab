#!/usr/bin/env python3
"""
validate_site.py — 验证站点完整性

标准库 only，输出 PASS / FAIL。
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

REQUIRED_ROOT = ["index.html", "README.md", "LICENSE", ".gitignore"]
REQUIRED_DOCS = ["ARCHITECTURE.md", "CASE_TEMPLATE.md", "ADDING_A_NEW_CASE.md", "CASTFORM_NOTES.md"]
REQUIRED_SCRIPTS = ["validate_site.py", "check_secrets.py", "new_case.py"]

CASE_REQUIRED_FIELDS = ["title", "status", "category", "slug"]


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


def main():
    print("=== validate_site.py ===")
    results = [check_files(), check_cases_json()]
    if all(results):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
