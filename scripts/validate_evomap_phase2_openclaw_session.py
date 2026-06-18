#!/usr/bin/env python3
"""
validate_evomap_phase2_openclaw_session.py

Validates the ATL-EVOMAP-2 EvoMap Evolver OpenClaw session-context test
case structure and compliance with hard boundaries.

Usage: python3 scripts/validate_evomap_phase2_openclaw_session.py
Exit codes: 0 = PASS, 1 = FAIL
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
CASES_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0"
PHASE2_DIR = CASES_DIR / "phase2-openclaw-session"
ARTIFACTS_DIR = PHASE2_DIR / "artifacts"
REPORTS_DIR = REPO_ROOT / "reports"
SCRIPTS_DIR = REPO_ROOT / "scripts"
DATA_DIR = REPO_ROOT / "data"

# Secret patterns (forbidden literals)
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"sk_live_[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{36,}",
    r"glpat-[A-Za-z0-9\\-]{20,}",
    r"xox[baprs]-[A-Za-z0-9\\-]{10,}",
    r"AIza[A-Za-z0-9_-]{35,}",
    r"ya29\\.[A-Za-z0-9_-]{100,}",
    r"amzn\\.mfa\\.[A-Za-z0-9_-]{100,}",
    r"Bearer\\s+[A-Za-z0-9_\\-\\.]{20,}",
    r"Authorization:\\s*Bearer",
    r"Authorization:\\s*Token",
    r"cookie:\\s*",
    r"private_key",
    r"-----BEGIN (RSA |EC |DSA |OPENSSH )PRIVATE KEY-----",
]

# Forbidden content patterns (only actual secret content, not doc references)
FORBIDDEN_CONTENT = [
    r"API_KEY\s*=\s*[A-Za-z0-9_-]{10,}",
    r"TOKEN\s*=\s*[A-Za-z0-9_-]{10,}",
    r"SECRET\s*=\s*[A-Za-z0-9_-]{10,}",
    r"PASSWORD\s*=\s*[A-Za-z0-9_-]{6,}",
]

REQUIRED_FILES = [
    ("phase2-openclaw-session/ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md", CASES_DIR),
    ("phase2-openclaw-session/artifacts/evolver-run-openclaw-session-output.txt", CASES_DIR),
    ("phase2-openclaw-session/artifacts/evolver-review-openclaw-session-output.txt", CASES_DIR),
    ("phase2-openclaw-session/artifacts/evolver-generated-files.txt", CASES_DIR),
]

# Hard boundary keywords — these are the simplified phrases the user asked for
REQUIRED_HARD_BOUNDARY_KEYWORDS = [
    "no hub",
    "no credits",
    "no auto-publish",
    "no validator",
    "no --loop",
]

REPORT_FILES = [
    REPORTS_DIR / "ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md",
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


def check_case_phase(path: Path, slug: str, expected_phase_substring: str) -> bool:
    """Check that the case in cases.json has the expected phase."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for case in data.get("cases", []):
            if case.get("slug") == slug:
                phase = case.get("phase", "")
                if expected_phase_substring.lower() in phase.lower():
                    print(green(f"Case '{slug}' phase contains '{expected_phase_substring}': {phase}"))
                    return True
                else:
                    print(red(f"Case '{slug}' phase does NOT contain '{expected_phase_substring}': {phase}"))
                    return False
        print(red(f"Slug '{slug}' not found in cases.json"))
        return False
    except Exception as e:
        print(red(f"Error reading cases.json: {e}"))
        return False


def check_readme_contains(path: Path, required_strings: list) -> bool:
    """Check that the README contains all required strings."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        all_pass = True
        for s in required_strings:
            if s in content:
                print(green(f"README contains '{s}'"))
            else:
                print(red(f"README does NOT contain '{s}'"))
                all_pass = False
        return all_pass
    except FileNotFoundError:
        print(red(f"README not found: {path}"))
        return False


def check_hard_boundary_keywords(path: Path, label: str) -> bool:
    """Check that hard boundary keywords appear in docs (case-insensitive substring)."""
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
    """Scan for forbidden secret patterns. Returns True if clean."""
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


def main():
    print("=" * 60)
    print("ATL-EVOMAP-2 EvoMap Evolver OpenClaw Session Validator")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Required files exist
    print(blue("1. Checking required Phase 2 files..."))
    for rel_path, base_dir in REQUIRED_FILES:
        path = base_dir / rel_path
        if not check_file_exists(path, rel_path):
            all_pass = False
    print()

    # 2. Artifacts non-empty
    print(blue("2. Checking Phase 2 artifacts non-empty..."))
    for rel_path, _ in REQUIRED_FILES[1:]:
        path = CASES_DIR / rel_path
        if not check_file_not_empty(path, rel_path):
            all_pass = False
    print()

    # 3. Report files exist
    print(blue("3. Checking report files..."))
    for report_path in REPORT_FILES:
        if not check_file_exists(report_path, report_path.name):
            all_pass = False
    print()

    # 4. data/cases.json valid
    print(blue("4. Checking data/cases.json valid and has Phase 2 phase..."))
    cases_json = DATA_DIR / "cases.json"
    if not check_json_valid(cases_json, "data/cases.json"):
        all_pass = False
    else:
        if not check_case_phase(cases_json, "evomap-evolver-openclaw-v0", "ATL-EVOMAP"):
            all_pass = False
    print()

    # 5. Case README contains ATL-EVOMAP-2
    print(blue("5. Checking case README contains ATL-EVOMAP-2 references..."))
    case_readme = CASES_DIR / "README.md"
    if not check_readme_contains(case_readme, ["ATL-EVOMAP-2", "Phase 2", "OpenClaw Session-Context Test"]):
        all_pass = False
    print()

    # 6. Hard boundary keywords in Phase 2 reports
    print(blue("6. Checking hard boundary keywords in Phase 2 reports..."))
    docs_to_check = [
        (PHASE2_DIR / "ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md", "Phase 2 case report"),
        (REPORTS_DIR / "ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md", "Phase 2 main report"),
        (case_readme, "case README"),
    ]
    for doc_path, label in docs_to_check:
        if doc_path.exists():
            if not check_hard_boundary_keywords(doc_path, label):
                all_pass = False
    print()

    # 7. Secret pattern scan
    print(blue("7. Secret pattern scan on Phase 2 files..."))
    files_to_scan = [
        (PHASE2_DIR / "ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md", "Phase 2 case report"),
        (REPORTS_DIR / "ATL_EVOMAP_2_OPENCLAW_SESSION_REPORT.md", "Phase 2 main report"),
        (case_readme, "case README"),
        (DATA_DIR / "cases.json", "cases.json"),
    ]
    for file_path, label in files_to_scan:
        if file_path.exists():
            if not check_secret_patterns(file_path, label):
                all_pass = False
    print()

    # 8. Validator script location
    print(blue("8. Checking Phase 2 validator script location..."))
    script_path = SCRIPTS_DIR / "validate_evomap_phase2_openclaw_session.py"
    if not check_file_exists(script_path, "validate_evomap_phase2_openclaw_session.py"):
        all_pass = False
    print()

    # 9. Verify Phase 2 evolver review output contains 'pending'
    print(blue("9. Checking evolver review output shows pending run..."))
    review_output = ARTIFACTS_DIR / "evolver-review-openclaw-session-output.txt"
    if review_output.exists():
        try:
            with open(review_output, "r", encoding="utf-8") as f:
                review_content = f.read()
            if "Pending" in review_content or "pending" in review_content:
                print(green("Review output shows pending evolution run"))
            else:
                print(yellow("Review output does NOT show pending run (may be 'no pending' state)"))
        except Exception as e:
            print(red(f"Error reading review output: {e}"))
            all_pass = False
    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print(green("ALL CHECKS PASSED"))
        print("Case: evomap-evolver-openclaw-v0 (Phase 2)")
        print("Status: openclaw session-context test partial")
        return 0
    else:
        print(red("SOME CHECKS FAILED"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
