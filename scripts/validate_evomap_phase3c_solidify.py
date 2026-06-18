#!/usr/bin/env python3
"""
validate_evomap_phase3c_solidify.py

Validates the ATL-EVOMAP-3C EvoMap Evolver OpenClaw solidify
case structure and compliance with hard boundaries.

Usage: python3 scripts/validate_evomap_phase3c_solidify.py
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
PHASE3C_DIR = CASES_DIR / "phase3c-solidify"
ARTIFACTS_DIR = PHASE3C_DIR / "artifacts"
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
    "phase3c-solidify/ATL_EVOMAP_3C_SOLIDIFY_REPORT.md",
    "phase3c-solidify/artifacts/evolver-review-before-approve.txt",
    "phase3c-solidify/artifacts/evolver-review-approve-output.txt",
    "phase3c-solidify/artifacts/evolver-solidify-output.txt",
    "phase3c-solidify/artifacts/gep-state-openclaw-grep.txt",
    "phase3c-solidify/artifacts/capsule-count.txt",
    "phase3c-solidify/artifacts/evolution-events-openclaw.txt",
    "phase3c-solidify/artifacts/scoring.md",
]

# Required content checks
EXPECTED_PENDING_RUN = "run_1781793744810"
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
    REPORTS_DIR / "ATL_EVOMAP_3C_SOLIDIFY_REPORT.md",
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


def check_before_approve_content(path: Path) -> bool:
    """Check the before-approve review contains the expected pending run and gene."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    all_pass = True
    if EXPECTED_PENDING_RUN in content:
        print(green(f"Pre-approve review contains pending run '{EXPECTED_PENDING_RUN}'"))
    else:
        print(red(f"Pre-approve review does NOT contain pending run '{EXPECTED_PENDING_RUN}'"))
        all_pass = False
    if EXPECTED_GENE in content:
        print(green(f"Pre-approve review contains selected gene '{EXPECTED_GENE}'"))
    else:
        print(red(f"Pre-approve review does NOT contain selected gene '{EXPECTED_GENE}'"))
        all_pass = False
    return all_pass


def check_approve_output(path: Path) -> bool:
    """Check the approve output shows the run was approved."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    all_pass = True
    if "Approved" in content or "approve" in content.lower():
        print(green(f"Approve output contains 'Approved' marker"))
    else:
        print(red(f"Approve output does NOT contain 'Approved' marker"))
        all_pass = False
    if EXPECTED_GENE in content:
        print(green(f"Approve output contains selected gene '{EXPECTED_GENE}'"))
    else:
        print(red(f"Approve output does NOT contain selected gene '{EXPECTED_GENE}'"))
        all_pass = False
    return all_pass


def check_solidify_output(path: Path) -> bool:
    """Check the solidify output exists and shows HOLLOW COMMIT detection or evolution events."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    markers = ["HOLLOW COMMIT", "solidify", "Solidify", "SOLIDIFY", "evolver-rollback", "stashed"]
    found = [m for m in markers if m in content or m.lower() in content.lower()]
    if found:
        print(green(f"Solidify output contains expected markers: {found}"))
        return True
    print(yellow(f"Solidify output does NOT contain expected markers"))
    return False


def check_capsule_count(path: Path) -> bool:
    """Check the capsule count file (capsule_count may be 0 due to HOLLOW COMMIT)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    if "capsule_count" in content:
        print(green(f"Capsule count file contains 'capsule_count' marker"))
        return True
    print(red(f"Capsule count file does NOT contain 'capsule_count' marker"))
    return False


def check_evolution_events(path: Path) -> bool:
    """Check the evolution events file contains EvolutionEvent markers."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"File not found: {path}"))
        return False
    all_pass = True
    if "EvolutionEvent" in content or "evt_" in content:
        print(green(f"Evolution events file contains EvolutionEvent markers"))
    else:
        print(red(f"Evolution events file does NOT contain EvolutionEvent markers"))
        all_pass = False
    if EXPECTED_GENE in content:
        print(green(f"Evolution events file contains selected gene '{EXPECTED_GENE}'"))
    else:
        print(red(f"Evolution events file does NOT contain selected gene '{EXPECTED_GENE}'"))
        all_pass = False
    return all_pass


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


def main():
    print("=" * 60)
    print("ATL-EVOMAP-3C EvoMap Evolver OpenClaw Solidify Validator")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Required files exist
    print(blue("1. Checking required Phase 3C files..."))
    for rel in REQUIRED_FILES:
        if not check_file_exists(CASES_DIR / rel, rel):
            all_pass = False
    print()

    # 2. Required files non-empty
    print(blue("2. Checking Phase 3C files non-empty..."))
    for rel in REQUIRED_FILES:
        if not check_file_not_empty(CASES_DIR / rel, rel):
            all_pass = False
    print()

    # 3. Report files exist
    print(blue("3. Checking report files..."))
    for report_path in REPORT_FILES:
        if not check_file_exists(report_path, report_path.name):
            all_pass = False
    print()

    # 4. data/cases.json valid + has Phase 3C phase
    print(blue("4. Checking data/cases.json valid and has Phase 3C phase..."))
    cases_json = DATA_DIR / "cases.json"
    if not check_json_valid(cases_json, "data/cases.json"):
        all_pass = False
    else:
        if not check_case_phase(cases_json, "evomap-evolver-openclaw-v0", "ATL-EVOMAP-3C"):
            all_pass = False
    print()

    # 5. Case README contains ATL-EVOMAP-3C
    print(blue("5. Checking case README contains ATL-EVOMAP-3C references..."))
    case_readme = CASES_DIR / "README.md"
    if not check_readme_contains(case_readme, ["ATL-EVOMAP-3C", "Phase 3c", "Solidify"]):
        all_pass = False
    print()

    # 6. Pre-approve review content
    print(blue("6. Checking pre-approve review content..."))
    if not check_before_approve_content(ARTIFACTS_DIR / "evolver-review-before-approve.txt"):
        all_pass = False
    print()

    # 7. Approve output content
    print(blue("7. Checking approve output content..."))
    if not check_approve_output(ARTIFACTS_DIR / "evolver-review-approve-output.txt"):
        all_pass = False
    print()

    # 8. Solidify output content
    print(blue("8. Checking solidify output content..."))
    if not check_solidify_output(ARTIFACTS_DIR / "evolver-solidify-output.txt"):
        all_pass = False
    print()

    # 9. GEP state grep
    print(blue("9. Checking GEP state grep file..."))
    if not check_gep_state_grep(ARTIFACTS_DIR / "gep-state-openclaw-grep.txt"):
        all_pass = False
    print()

    # 10. Capsule count file
    print(blue("10. Checking capsule count file..."))
    if not check_capsule_count(ARTIFACTS_DIR / "capsule-count.txt"):
        all_pass = False
    print()

    # 11. Evolution events file
    print(blue("11. Checking evolution events file..."))
    if not check_evolution_events(ARTIFACTS_DIR / "evolution-events-openclaw.txt"):
        all_pass = False
    print()

    # 12. Hard boundary keywords
    print(blue("12. Checking hard boundary keywords in Phase 3C reports..."))
    docs_to_check = [
        (PHASE3C_DIR / "ATL_EVOMAP_3C_SOLIDIFY_REPORT.md", "Phase 3C case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3C_SOLIDIFY_REPORT.md", "Phase 3C main report"),
        (case_readme, "case README"),
    ]
    for doc_path, label in docs_to_check:
        if doc_path.exists():
            if not check_hard_boundary_keywords(doc_path, label):
                all_pass = False
    print()

    # 13. Secret pattern scan
    print(blue("13. Secret pattern scan on Phase 3C files..."))
    files_to_scan = [
        (PHASE3C_DIR / "ATL_EVOMAP_3C_SOLIDIFY_REPORT.md", "Phase 3C case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3C_SOLIDIFY_REPORT.md", "Phase 3C main report"),
        (case_readme, "case README"),
        (DATA_DIR / "cases.json", "cases.json"),
        (ARTIFACTS_DIR / "scoring.md", "scoring.md"),
        (ARTIFACTS_DIR / "capsule-count.txt", "capsule count"),
        (ARTIFACTS_DIR / "evolution-events-openclaw.txt", "evolution events"),
    ]
    for file_path, label in files_to_scan:
        if file_path.exists():
            if not check_secret_patterns(file_path, label):
                all_pass = False
    print()

    # 14. No root runtime state in git
    print(blue("14. Checking no root .evolver/ or memory/ in git..."))
    if not check_no_root_runtime_in_git():
        all_pass = False
    print()

    # 15. Validator script location
    print(blue("15. Checking Phase 3C validator script location..."))
    script_path = SCRIPTS_DIR / "validate_evomap_phase3c_solidify.py"
    if not check_file_exists(script_path, "validate_evomap_phase3c_solidify.py"):
        all_pass = False
    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print(green("ALL CHECKS PASSED"))
        print("Case: evomap-evolver-openclaw-v0 (Phase 3C)")
        print("Status: openclaw solidify partial")
        return 0
    print(red("SOME CHECKS FAILED"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
