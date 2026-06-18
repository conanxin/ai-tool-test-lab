#!/usr/bin/env python3
"""
validate_evomap_phase3c_v2_non_hollow_solidify.py

Validates the ATL-EVOMAP-3C-V2 EvoMap Evolver non-hollow solidify
case structure and compliance with hard boundaries.

Usage: python3 scripts/validate_evomap_phase3c_v2_non_hollow_solidify.py
Exit codes: 0 = PASS, 1 = FAIL
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = REPO_ROOT / "scripts"
CASES_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0"
PHASE3CV2_DIR = CASES_DIR / "phase3c-v2-non-hollow-solidify"
ARTIFACTS_DIR = PHASE3CV2_DIR / "artifacts"
FIXTURES_DIR = PHASE3CV2_DIR / "fixtures"
REPORTS_DIR = REPO_ROOT / "reports"
DATA_DIR = REPO_ROOT / "data"

# Secret patterns (forbidden literals)
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"sk_live_[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{36,}",
    r"glpat-[A-Za-z0-9\-]{20,}",
    r"xox[baprs]-[A-Za-z0-9\-]{10,}",
    r"AIza[A-Za-z0-9_-]{35,}",
    r"ya29\.[A-Za-z0-9_-]{100,}",
    r"amzn\.mfa\.[A-Za-z0-9_-]{100,}",
    r"Bearer\s+[A-Za-z0-9_\-\.]{20,}",
    r"Authorization:\s*Bearer",
    r"Authorization:\s*Token",
    r"cookie:\s*[A-Za-z0-9_\-]+",
    r"private_key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}",
    r'"private_key"\s*:\s*"',
    r"-----BEGIN (RSA |EC |DSA |OPENSSH )PRIVATE KEY-----",
]

REQUIRED_FILES = [
    "phase3c-v2-non-hollow-solidify/ATL_EVOMAP_3C_V2_NON_HOLLOW_SOLIDIFY_REPORT.md",
    "phase3c-v2-non-hollow-solidify/fixtures/session-tool-use-sample.txt",
    "phase3c-v2-non-hollow-solidify/artifacts/openclaw-tool-use-fixture-output.json",
    "phase3c-v2-non-hollow-solidify/artifacts/manual-bare-signal-injection-v2.jsonl",
    "phase3c-v2-non-hollow-solidify/artifacts/evolver-run-non-hollow-output.txt",
    "phase3c-v2-non-hollow-solidify/artifacts/evolver-review-before-approve-non-hollow.txt",
    "phase3c-v2-non-hollow-solidify/artifacts/capsule-count-after-non-hollow.txt",
    "phase3c-v2-non-hollow-solidify/artifacts/gep-state-non-hollow-grep.txt",
    "phase3c-v2-non-hollow-solidify/artifacts/scoring.md",
]

# Real code diff files (the "non-hollow" deliverable)
REAL_CODE_FILES = [
    "scripts/openclaw_tool_use_fixture.py",
]

EXPECTED_GENE = "gene_distilled_openclaw-tool-use-discipline-bare-compatible"

# Hard boundary keywords
REQUIRED_HARD_BOUNDARY_KEYWORDS = [
    "no hub",
    "no credits",
    "no auto-publish",
    "no validator",
    "no --loop",
]

REPORT_FILES = [
    REPORTS_DIR / "ATL_EVOMAP_3C_V2_NON_HOLLOW_SOLIDIFY_REPORT.md",
]


def green(msg): return f"\033[92mPASS\033[0m {msg}"
def red(msg): return f"\033[91mFAIL\033[0m {msg}"
def yellow(msg): return f"\033[93mWARN\033[0m {msg}"
def blue(msg): return f"\033[94mINFO\033[0m {msg}"


def check_file_exists(path: Path, label: str) -> bool:
    if path.exists():
        print(green(f"File exists: {label}"))
        return True
    print(red(f"File missing: {label} -> {path}"))
    return False


def check_file_not_empty(path: Path, label: str) -> bool:
    if path.exists() and path.stat().st_size > 0:
        size = path.stat().st_size
        print(green(f"File not empty: {label} ({size} bytes)"))
        return True
    if path.exists() and path.stat().st_size == 0:
        print(red(f"File empty: {label}"))
        return False
    print(red(f"File missing: {label}"))
    return False


def check_json_valid(path: Path, label: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            json.load(f)
        print(green(f"Valid JSON: {label}"))
        return True
    except json.JSONDecodeError as e:
        print(red(f"Invalid JSON: {label} -> {e}"))
        return False
    except FileNotFoundError:
        print(red(f"File missing: {label}"))
        return False


def check_case_phase(path: Path, slug: str, expected_phase_substring: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        for case in data.get("cases", []):
            if case.get("slug") == slug:
                phase = case.get("phase", "")
                if expected_phase_substring.lower() in phase.lower():
                    print(green(f"Case '{slug}' phase contains '{expected_phase_substring}': {phase}"))
                    return True
                print(red(f"Case '{slug}' phase does NOT contain '{expected_phase_substring}': {phase}"))
                return False
        print(red(f"Slug '{slug}' not found in cases.json"))
        return False
    except Exception as e:
        print(red(f"Error reading cases.json: {e}"))
        return False


def check_readme_contains(path: Path, required_strings: list) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
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
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().lower()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    missing = []
    for kw in REQUIRED_HARD_BOUNDARY_KEYWORDS:
        if kw.lower() not in content:
            missing.append(kw)
    if not missing:
        print(green(f"All hard boundary keywords found in {label}"))
        return True
    for kw in missing:
        print(yellow(f"Missing keyword in {label}: {kw}"))
    return False


def check_secret_patterns(path: Path, label: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    violations = []
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            real = [m for m in matches if not re.search(r"(example|placeholder|sk_live_xxx|sk-xxx)", m, re.IGNORECASE)]
            if real:
                violations.append(f"Pattern '{pattern}' matched: {real[:3]}")
    if violations:
        for v in violations:
            print(red(f"Secret violation in {label}: {v}"))
        return False
    print(green(f"No secret patterns found in {label}"))
    return True


def check_fixture_output_json(path: Path) -> bool:
    """Check the fixture output JSON has all required fields."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(red(f"Could not read fixture output: {e}"))
        return False
    required_fields = ["exec_count", "read_count", "edit_count", "exec_ratio", "has_session_context"]
    all_pass = True
    for field in required_fields:
        if field in data:
            print(green(f"Fixture output contains '{field}' (={data[field]})"))
        else:
            print(red(f"Fixture output does NOT contain '{field}'"))
            all_pass = False
    if data.get("ok") is True:
        print(green(f"Fixture output ok=True"))
    else:
        print(red(f"Fixture output ok != True"))
        all_pass = False
    return all_pass


def check_review_output(path: Path) -> bool:
    """Check the review output. Per hard boundary, expected to be BLOCKED but file should exist."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    # The review output exists (since we ran evolver review)
    if "Pending evolution run" in content or "review" in content.lower():
        print(green(f"Review output contains expected markers"))
        return True
    print(red(f"Review output does NOT contain expected markers"))
    return False


def check_capsule_count(path: Path) -> bool:
    """Check the capsule count file (may be 0 due to BLOCKED)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    if "capsule_count" in content:
        print(green(f"Capsule count file contains 'capsule_count' marker"))
        return True
    print(red(f"Capsule count file does NOT contain 'capsule_count' marker"))
    return False


def check_gep_state_grep(path: Path) -> bool:
    """Check the GEP state grep file contains evidence."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    if EXPECTED_GENE in content:
        print(green(f"GEP state grep contains gene '{EXPECTED_GENE}'"))
        return True
    print(red(f"GEP state grep does NOT contain gene '{EXPECTED_GENE}'"))
    return False


def check_no_root_runtime_in_git() -> bool:
    """Verify that .evolver/ and memory/ at repo root are not in git tracking."""
    try:
        result = subprocess.run(
            ["git", "ls-files", ".evolver/", "memory/"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            print(yellow(f"git ls-files returned {result.returncode}"))
            return True
        files = [f for f in result.stdout.strip().split("\n") if f]
        relevant = [f for f in files if f.startswith(".evolver/") or (f.startswith("memory/") and not f.startswith("memory/distill_request"))]
        if relevant:
            print(red(f"Root runtime files in git: {relevant[:5]}"))
            return False
        print(green("No root .evolver/ or memory/ tracked by git"))
        return True
    except Exception as e:
        print(yellow(f"Could not run git ls-files: {e}"))
        return True


def check_real_code_files() -> bool:
    """Check the real code files exist and are non-trivial."""
    all_pass = True
    for rel_path in REAL_CODE_FILES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            print(red(f"Real code file missing: {rel_path}"))
            all_pass = False
            continue
        size = path.stat().st_size
        if size < 500:
            print(yellow(f"Real code file {rel_path} is small ({size} bytes)"))
        else:
            print(green(f"Real code file exists: {rel_path} ({size} bytes)"))
    return all_pass


def main():
    print("=" * 60)
    print("ATL-EVOMAP-3C-V2 EvoMap Evolver Non-Hollow Solidify Validator")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Required files exist
    print(blue("1. Checking required Phase 3C-V2 files..."))
    for rel in REQUIRED_FILES:
        if not check_file_exists(CASES_DIR / rel, rel):
            all_pass = False
    print()

    # 2. Required files non-empty
    print(blue("2. Checking Phase 3C-V2 files non-empty..."))
    for rel in REQUIRED_FILES:
        if not check_file_not_empty(CASES_DIR / rel, rel):
            all_pass = False
    print()

    # 3. Real code diff files
    print(blue("3. Checking real code diff files..."))
    if not check_real_code_files():
        all_pass = False
    print()

    # 4. Report files exist
    print(blue("4. Checking report files..."))
    for report_path in REPORT_FILES:
        if not check_file_exists(report_path, report_path.name):
            all_pass = False
    print()

    # 5. data/cases.json valid + has Phase 3C-V2 phase
    print(blue("5. Checking data/cases.json valid and has Phase 3C-V2 phase..."))
    cases_json = DATA_DIR / "cases.json"
    if not check_json_valid(cases_json, "data/cases.json"):
        all_pass = False
    else:
        if not check_case_phase(cases_json, "evomap-evolver-openclaw-v0", "ATL-EVOMAP-3C-V2"):
            all_pass = False
    print()

    # 6. Case README contains ATL-EVOMAP-3C-V2
    print(blue("6. Checking case README contains ATL-EVOMAP-3C-V2 references..."))
    case_readme = CASES_DIR / "README.md"
    if not check_readme_contains(case_readme, ["ATL-EVOMAP-3C-V2", "Phase 3c-v2", "Non-Hollow"]):
        all_pass = False
    print()

    # 7. Fixture output JSON valid + has required fields
    print(blue("7. Checking fixture output JSON..."))
    if not check_fixture_output_json(ARTIFACTS_DIR / "openclaw-tool-use-fixture-output.json"):
        all_pass = False
    print()

    # 8. Review output exists
    print(blue("8. Checking evolver review output..."))
    if not check_review_output(ARTIFACTS_DIR / "evolver-review-before-approve-non-hollow.txt"):
        all_pass = False
    print()

    # 9. Capsule count file
    print(blue("9. Checking capsule count file..."))
    if not check_capsule_count(ARTIFACTS_DIR / "capsule-count-after-non-hollow.txt"):
        all_pass = False
    print()

    # 10. GEP state grep
    print(blue("10. Checking GEP state grep file..."))
    if not check_gep_state_grep(ARTIFACTS_DIR / "gep-state-non-hollow-grep.txt"):
        all_pass = False
    print()

    # 11. Hard boundary keywords
    print(blue("11. Checking hard boundary keywords in Phase 3C-V2 reports..."))
    docs_to_check = [
        (PHASE3CV2_DIR / "ATL_EVOMAP_3C_V2_NON_HOLLOW_SOLIDIFY_REPORT.md", "Phase 3C-V2 case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3C_V2_NON_HOLLOW_SOLIDIFY_REPORT.md", "Phase 3C-V2 main report"),
        (case_readme, "case README"),
    ]
    for doc_path, label in docs_to_check:
        if doc_path.exists():
            if not check_hard_boundary_keywords(doc_path, label):
                all_pass = False
    print()

    # 12. Secret pattern scan
    print(blue("12. Secret pattern scan on Phase 3C-V2 files..."))
    files_to_scan = [
        (PHASE3CV2_DIR / "ATL_EVOMAP_3C_V2_NON_HOLLOW_SOLIDIFY_REPORT.md", "Phase 3C-V2 case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3C_V2_NON_HOLLOW_SOLIDIFY_REPORT.md", "Phase 3C-V2 main report"),
        (case_readme, "case README"),
        (DATA_DIR / "cases.json", "cases.json"),
        (REPO_ROOT / "scripts" / "openclaw_tool_use_fixture.py", "real code script"),
        (FIXTURES_DIR / "session-tool-use-sample.txt", "fixture"),
        (ARTIFACTS_DIR / "openclaw-tool-use-fixture-output.json", "fixture output JSON"),
        (ARTIFACTS_DIR / "manual-bare-signal-injection-v2.jsonl", "injection jsonl"),
        (ARTIFACTS_DIR / "scoring.md", "scoring.md"),
        (ARTIFACTS_DIR / "capsule-count-after-non-hollow.txt", "capsule count"),
        (ARTIFACTS_DIR / "gep-state-non-hollow-grep.txt", "gep state grep"),
    ]
    for file_path, label in files_to_scan:
        if file_path.exists():
            if not check_secret_patterns(file_path, label):
                all_pass = False
    print()

    # 13. No root runtime state in git
    print(blue("13. Checking no root .evolver/ or memory/ in git..."))
    if not check_no_root_runtime_in_git():
        all_pass = False
    print()

    # 14. Validator script location
    print(blue("14. Checking Phase 3C-V2 validator script location..."))
    script_path = SCRIPTS_DIR / "validate_evomap_phase3c_v2_non_hollow_solidify.py"
    if not check_file_exists(script_path, "validate_evomap_phase3c_v2_non_hollow_solidify.py"):
        all_pass = False
    print()

    # 15. BLOCKED status documented
    print(blue("15. Checking BLOCKED status is documented in report..."))
    blocked_report = PHASE3CV2_DIR / "ATL_EVOMAP_3C_V2_NON_HOLLOW_SOLIDIFY_REPORT.md"
    if blocked_report.exists():
        try:
            with open(blocked_report, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if "BLOCKED" in content and "硬边界" in content:
                print(green(f"BLOCKED status and 硬边界 referenced in case report"))
            else:
                print(yellow(f"BLOCKED or 硬边界 not found in report"))
        except Exception as e:
            print(yellow(f"Could not check BLOCKED status: {e}"))
    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print(green("ALL CHECKS PASSED"))
        print("Case: evomap-evolver-openclaw-v0 (Phase 3C-V2)")
        print("Status: non-hollow solidify blocked")
        return 0
    print(red("SOME CHECKS FAILED"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
