#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

BASE = Path("cases/boneyard-skeleton-screen-v0")
REPORTS = Path("reports")
REQUIRED_CASE_FILES = [
    "index.html", "test-plan.md", "local-readiness.md", "CASE_CLOSEOUT.md",
    "smoke-result.json",
    "smoke-app/package.json", "smoke-app/index.html", "smoke-app/vite.config.ts",
    "smoke-app/tsconfig.json", "smoke-app/src/main.tsx", "smoke-app/src/App.tsx",
    "smoke-app/src/App.css"
]
REQUIRED_REPORTS = [
    "ATL_BONEYARD_1_NPM_REGISTRY_DIAGNOSTIC_REPORT.md",
    "ATL_BONEYARD_1_LOCAL_SMOKE_REPORT.md",
    "FINAL_BONEYARD_SKELETON_SCREEN_V0_REPORT.md"
]

def main():
    issues = []
    for f in REQUIRED_CASE_FILES:
        if not (BASE / f).exists():
            issues.append(f"Missing case file: {f}")
    for r in REQUIRED_REPORTS:
        if not (REPORTS / r).exists():
            issues.append(f"Missing report: {r}")

    smoke = BASE / "smoke-result.json"
    if smoke.exists():
        try:
            data = json.loads(smoke.read_text())
            keys = ["case_slug", "phase", "final_status", "official_registry_resolution",
                    "boneyard_build", "generated_bones_json", "generated_registry",
                    "npm_build", "error_excerpt"]
            for k in keys:
                if k not in data:
                    issues.append(f"Missing key in smoke-result.json: {k}")
            if data.get("final_status") != "BLOCKED_BY_LOCAL_ENVIRONMENT":
                issues.append("final_status must be BLOCKED_BY_LOCAL_ENVIRONMENT")
            if data.get("official_registry_resolution") != "FAIL":
                issues.append("official_registry_resolution must be FAIL")
            if not data.get("error_excerpt"):
                issues.append("error_excerpt must be non-empty")
        except Exception as e:
            issues.append(f"smoke-result.json parse error: {e}")
    else:
        issues.append("smoke-result.json missing")

    cases_json = Path("data/cases.json")
    if cases_json.exists():
        try:
            c = json.loads(cases_json.read_text())
            cases_list = c.get("cases", c) if isinstance(c, dict) else c
            if not any(isinstance(x, dict) and x.get("slug") == "boneyard-skeleton-screen-v0" for x in cases_list):
                issues.append("data/cases.json missing boneyard-skeleton-screen-v0")
        except Exception as e:
            issues.append(f"data/cases.json parse error: {e}")

    index = Path("index.html")
    if index.exists():
        if "boneyard-skeleton-screen-v0" not in index.read_text():
            issues.append("index.html missing link to boneyard-skeleton-screen-v0")
    else:
        issues.append("index.html missing")

    if issues:
        print("STATUS: FAIL")
        for i in issues:
            print("  -", i)
        sys.exit(1)
    else:
        print("STATUS: PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()
