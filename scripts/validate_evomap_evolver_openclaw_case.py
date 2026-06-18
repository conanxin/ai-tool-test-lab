#!/usr/bin/env python3
"""
validate_evomap_evolver_openclaw_case.py

Validates the ATL-EVOMAP-1 EvoMap Evolver OpenClaw case structure
and compliance with hard boundaries.

Usage: python3 scripts/validate_evomap_evolver_openclaw_case.py
Exit codes: 0 = PASS, 1 = FAIL, 2 = SKIPPED (optional file absent with documented reason)
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
CASES_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0"
FIXTURES_DIR = CASES_DIR / "fixtures" / "local-evolver-smoke"
ARTIFACTS_DIR = CASES_DIR / "artifacts"
REPORTS_DIR = REPO_ROOT / "reports"
SCRIPTS_DIR = REPO_ROOT / "scripts"
DATA_DIR = REPO_ROOT / "data"

# Secret patterns (forbidden literals)
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",           # OpenAI API key
    r"sk_live_[A-Za-z0-9]{20,}",       # Stripe live key
    r"ghp_[A-Za-z0-9]{36,}",           # GitHub personal token
    r"glpat-[A-Za-z0-9\\-]{20,}",      # GitLab token
    r"xox[baprs]-[A-Za-z0-9\\-]{10,}", # Slack token
    r"AIza[A-Za-z0-9_-]{35,}",         # Google API key
    r"ya29\\.[A-Za-z0-9_-]{100,}",    # Google OAuth
    r"amzn\\.mfa\\.[A-Za-z0-9_-]{100,}", # Amazon MFA
    r"Bearer\\s+[A-Za-z0-9_\\-\\.]{20,}", # Generic Bearer token
    r"Authorization:\\s*Bearer",
    r"Authorization:\\s*Token",
    r"cookie:\\s*",
    r"private_key",
    r"-----BEGIN (RSA |EC |DSA |OPENSSH )PRIVATE KEY-----",
]

# Forbidden file/content patterns
FORBIDDEN_CONTENT = [
    # Removed \.env\b — docs legitimately discuss .env as forbidden path
    r"API_KEY\s*=\s*[A-Za-z0-9_-]{10,}",     # API_KEY=actual_value (not just mention)
    r"TOKEN\s*=\s*[A-Za-z0-9_-]{10,}",       # TOKEN=actual_value
    r"SECRET\s*=\s*[A-Za-z0-9_-]{10,}",    # SECRET=actual_value
    r"PASSWORD\s*=\s*[A-Za-z0-9_-]{6,}",   # PASSWORD=actual_value
]

REQUIRED_FILES = [
    ("README.md", CASES_DIR),
    ("CASE_REPORT.md", CASES_DIR),
    ("artifacts/evolver-review-output.txt", CASES_DIR),
    ("artifacts/evolver-run-output.txt", CASES_DIR),
    ("fixtures/local-evolver-smoke/calc.js", CASES_DIR),
    ("fixtures/local-evolver-smoke/test.js", CASES_DIR),
    ("fixtures/local-evolver-smoke/memory/npm-test-failure.log", CASES_DIR),
    ("fixtures/local-evolver-smoke/memory/proxy-failure.log", CASES_DIR),
    ("fixtures/local-evolver-smoke/memory/systemd-failure.log", CASES_DIR),
    ("fixtures/local-evolver-smoke/memory/cron-failure.log", CASES_DIR),
]

REQUIRED_HARD_BOUNDARY_KEYWORDS = [
    "EVOLVER_AUTO_PUBLISH=false",
    "EVOLVER_VALIDATOR_ENABLED=false",
    "EVOLVER_ATP_AUTOBUY=off",
    "no hub connection",
    "no credits consumed",
    "no_hub_url",
]

REPORT_FILES = [
    REPORTS_DIR / "ATL_EVOMAP_EVOLVER_OPENCLAW_V0_REPORT.md",
]


def green(msg): return f"\033[92mPASS\033[0m {msg}"
def red(msg): return f"\033[91mFAIL\033[0m {msg}"
def yellow(msg): return f"\033[93mWARN\033[0m {msg}"
def blue(msg): return f"\033[94mINFO\033[0m {msg}"


def check_file_exists(path: Path, label: str) -> bool:
    if path.exists():
        print(green(f"File exists: {label}"))
        return True
    else:
        print(red(f"File missing: {label} -> {path}"))
        return False


def check_file_not_empty(path: Path, label: str) -> bool:
    if path.exists() and path.stat().st_size > 0:
        size = path.stat().st_size
        print(green(f"File not empty: {label} ({size} bytes)"))
        return True
    elif path.exists() and path.stat().st_size == 0:
        print(red(f"File empty: {label} -> {path} (0 bytes)"))
        return False
    else:
        print(red(f"File missing: {label} -> {path}"))
        return False


def check_json_valid(path: Path, label: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
        print(green(f"Valid JSON: {label}"))
        return True
    except json.JSONDecodeError as e:
        print(red(f"Invalid JSON: {label} -> {e}"))
        return False
    except FileNotFoundError:
        print(red(f"File missing: {label} -> {path}"))
        return False


def check_case_in_cases_json(path: Path, slug: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        slugs = [c.get("slug") for c in data.get("cases", [])]
        if slug in slugs:
            print(green(f"Slug '{slug}' found in cases.json"))
            return True
        else:
            print(red(f"Slug '{slug}' NOT found in cases.json. Found: {slugs}"))
            return False
    except Exception as e:
        print(red(f"Error reading cases.json: {e}"))
        return False


def check_readme_mentions_case(readme_path: Path, slug: str) -> bool:
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        if slug in content:
            print(green(f"README mentions case slug: {slug}"))
            return True
        else:
            print(red(f"README does NOT mention case slug: {slug}"))
            return False
    except FileNotFoundError:
        print(red(f"README not found: {readme_path}"))
        return False


def check_hard_boundary_keywords(path: Path, label: str) -> bool:
    """Check that hard boundary keywords appear in docs (case-insensitive)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        missing = []
        for kw in REQUIRED_HARD_BOUNDARY_KEYWORDS:
            if kw.lower() not in content:
                missing.append(kw)
        if not missing:
            print(green(f"All hard boundary keywords found in {label}"))
            return True
        else:
            for kw in missing:
                print(yellow(f"Missing keyword in {label}: {kw}"))
            return False
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False


def check_secret_patterns(path: Path, label: str) -> bool:
    """Scan for forbidden secret patterns. Returns True if clean (no secrets found)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False

    violations = []
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Filter out false positives (example/sk- in code comments)
            real_matches = [m for m in matches if not re.search(r"(example|placeholder|sk_live_xxx|sk-xxx)", m, re.IGNORECASE)]
            if real_matches:
                violations.append(f"Pattern '{pattern}' matched: {real_matches[:3]}")

    for pattern in FORBIDDEN_CONTENT:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(f"Forbidden content pattern: '{pattern}'")

    if violations:
        for v in violations:
            print(red(f"Secret violation in {label}: {v}"))
        return False
    else:
        print(green(f"No secret patterns found in {label}"))
        return True


def check_artifacts_output(path: Path, label: str) -> bool:
    """Check artifacts output is present and non-empty."""
    if not check_file_not_empty(path, label):
        # Special case: if evolver installation failed and this is documented, allow FAIL to become WARNING
        return False
    return True


def main():
    print("=" * 60)
    print("ATL-EVOMAP-1 EvoMap Evolver Case Validator")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Required files exist
    print(blue("1. Checking required files..."))
    for rel_path, base_dir in REQUIRED_FILES:
        path = base_dir / rel_path
        if not check_file_exists(path, rel_path):
            all_pass = False
    print()

    # 2. Artifacts present and non-empty
    print(blue("2. Checking artifacts..."))
    for artifact_name in ["artifacts/evolver-review-output.txt", "artifacts/evolver-run-output.txt"]:
        path = CASES_DIR / artifact_name
        if not check_file_not_empty(path, artifact_name):
            all_pass = False
    print()

    # 3. Report files exist
    print(blue("3. Checking report files..."))
    for report_path in REPORT_FILES:
        if not check_file_exists(report_path, report_path.name):
            all_pass = False
    print()

    # 4. data/cases.json valid and has slug
    print(blue("4. Checking data/cases.json..."))
    cases_json = DATA_DIR / "cases.json"
    if not check_json_valid(cases_json, "data/cases.json"):
        all_pass = False
    else:
        if not check_case_in_cases_json(cases_json, "evomap-evolver-openclaw-v0"):
            all_pass = False
    print()

    # 5. README mentions the case
    print(blue("5. Checking README mentions case..."))
    readme_path = REPO_ROOT / "README.md"
    if not check_readme_mentions_case(readme_path, "evomap-evolver-openclaw-v0"):
        all_pass = False
    print()

    # 6. Hard boundary keywords in documentation
    print(blue("6. Checking hard boundary keywords in docs..."))
    docs_to_check = [
        (CASES_DIR / "README.md", "cases README.md"),
        (CASES_DIR / "CASE_REPORT.md", "CASE_REPORT.md"),
        (REPORTS_DIR / "ATL_EVOMAP_EVOLVER_OPENCLAW_V0_REPORT.md", "main report"),
    ]
    for doc_path, label in docs_to_check:
        if doc_path.exists():
            if not check_hard_boundary_keywords(doc_path, label):
                all_pass = False
    print()

    # 7. Secret pattern scan on key files
    print(blue("7. Secret pattern scan..."))
    files_to_scan = [
        (CASES_DIR / "README.md", "cases README.md"),
        (CASES_DIR / "CASE_REPORT.md", "CASE_REPORT.md"),
        (REPORTS_DIR / "ATL_EVOMAP_EVOLVER_OPENCLAW_V0_REPORT.md", "main report"),
        (DATA_DIR / "cases.json", "cases.json"),
    ]
    for file_path, label in files_to_scan:
        if file_path.exists():
            if not check_secret_patterns(file_path, label):
                all_pass = False
    print()

    # 8. Validation script itself is in scripts/
    print(blue("8. Checking validation script location..."))
    script_path = SCRIPTS_DIR / "validate_evomap_evolver_openclaw_case.py"
    if not check_file_exists(script_path, "validate_evomap_evolver_openclaw_case.py"):
        all_pass = False
    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print(green("ALL CHECKS PASSED"))
        print("Case: evomap-evolver-openclaw-v0")
        print("Status: local offline smoke completed")
        return 0
    else:
        print(red("SOME CHECKS FAILED"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
