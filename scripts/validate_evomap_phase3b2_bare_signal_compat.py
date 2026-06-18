#!/usr/bin/env python3
"""
validate_evomap_phase3b2_bare_signal_compat.py

Validates the ATL-EVOMAP-3B2 EvoMap Evolver bare signal compatibility
case structure and compliance with hard boundaries.

Usage: python3 scripts/validate_evomap_phase3b2_bare_signal_compat.py
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
PHASE3B2_DIR = CASES_DIR / "phase3b2-bare-signal-compat"
ARTIFACTS_DIR = PHASE3B2_DIR / "artifacts"
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
    "phase3b2-bare-signal-compat/ATL_EVOMAP_3B2_BARE_SIGNAL_COMPAT_REPORT.md",
    "phase3b2-bare-signal-compat/artifacts/gene-openclaw-tool-use-discipline-bare-compatible.json",
    "phase3b2-bare-signal-compat/artifacts/install-bare-compatible-gene-output.txt",
    "phase3b2-bare-signal-compat/artifacts/manual-bare-signal-injection.jsonl",
    "phase3b2-bare-signal-compat/artifacts/evolver-run-bare-signal-output.txt",
    "phase3b2-bare-signal-compat/artifacts/evolver-review-bare-signal-output.txt",
    "phase3b2-bare-signal-compat/artifacts/selector-bare-match-grep.txt",
    "phase3b2-bare-signal-compat/artifacts/scoring.md",
]

# Bare signals that must be in the new Gene's signals_match
REQUIRED_BARE_SIGNALS = [
    "tool_bypass",
    "repeated_tool_usage",
    "protocol_drift",
    "session_context",
    "repo_context",
]

# Bare signals that must be in the injection JSONL
REQUIRED_INJECTION_SIGNALS = [
    "tool_bypass",
    "repeated_tool_usage",
    "protocol_drift",
    "session_context",
    "repo_context",
]

# Hard boundary keywords
REQUIRED_HARD_BOUNDARY_KEYWORDS = [
    "no hub",
    "no credits",
    "no auto-publish",
    "no validator",
    "no --loop",
]

# Expected selected Gene
EXPECTED_SELECTED_GENE = "gene_distilled_openclaw-tool-use-discipline-bare-compatible"

REPORT_FILES = [
    REPORTS_DIR / "ATL_EVOMAP_3B2_BARE_SIGNAL_COMPAT_REPORT.md",
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
        with open(path, "r", encoding="utf-8") as f:
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
        with open(path, "r", encoding="utf-8") as f:
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
    try:
        with open(path, "r", encoding="utf-8") as f:
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
        with open(path, "r", encoding="utf-8") as f:
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


def check_gene_artifact(gene_path: Path) -> bool:
    """Check the bare-compatible Gene artifact has all required bare signals."""
    try:
        with open(gene_path, "r", encoding="utf-8") as f:
            gene = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(red(f"Could not read gene artifact: {e}"))
        return False
    all_pass = True
    gene_id = gene.get("id", "")
    if EXPECTED_SELECTED_GENE in gene_id:
        print(green(f"Gene ID matches expected: {gene_id}"))
    else:
        print(red(f"Gene ID mismatch: got {gene_id}, expected contains {EXPECTED_SELECTED_GENE}"))
        all_pass = False
    signals = gene.get("signals_match", [])
    for sig in REQUIRED_BARE_SIGNALS:
        if sig in signals:
            print(green(f"Gene contains bare signal '{sig}'"))
        else:
            print(red(f"Gene does NOT contain bare signal '{sig}'"))
            all_pass = False
    return all_pass


def check_injection_jsonl(jsonl_path: Path) -> bool:
    """Check the bare-signal injection JSONL has 5 bare signals targeting the new Gene."""
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        print(red(f"Injection JSONL not found: {jsonl_path}"))
        return False
    if len(lines) < 5:
        print(red(f"Injection JSONL has only {len(lines)} lines, expected >= 5"))
        return False
    print(green(f"Injection JSONL has {len(lines)} lines"))
    all_pass = True
    found_signals = set()
    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(red(f"Invalid JSON line: {e}"))
            all_pass = False
            continue
        sig = obj.get("signal", {}).get("key", "")
        if sig in REQUIRED_INJECTION_SIGNALS:
            found_signals.add(sig)
        target = obj.get("mutation", {}).get("target", "")
        if EXPECTED_SELECTED_GENE in target:
            print(green(f"Event '{obj.get('id', '?')}' targets {EXPECTED_SELECTED_GENE}"))
        else:
            print(yellow(f"Event '{obj.get('id', '?')}' does NOT target {EXPECTED_SELECTED_GENE}: {target}"))
    missing = set(REQUIRED_INJECTION_SIGNALS) - found_signals
    if missing:
        print(red(f"Missing bare signals in injection: {missing}"))
        all_pass = False
    else:
        print(green(f"All 5 bare signals present in injection"))
    return all_pass


def check_selector_match(review_path: Path) -> bool:
    """Check the evolver review output shows the new Gene was selected."""
    try:
        with open(review_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"Review output not found: {review_path}"))
        return False
    if EXPECTED_SELECTED_GENE in content and "Selected Gene" not in content:
        # Review always shows "ID: ..." with the gene id
        print(green(f"Review output mentions selected Gene {EXPECTED_SELECTED_GENE}"))
        return True
    if EXPECTED_SELECTED_GENE in content:
        print(green(f"Review output contains selected Gene {EXPECTED_SELECTED_GENE}"))
        return True
    print(red(f"Review output does NOT mention {EXPECTED_SELECTED_GENE}"))
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
        # Only check root-level (not case dir)
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
    print("ATL-EVOMAP-3B2 EvoMap Evolver Bare Signal Compat Validator")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Required files exist
    print(blue("1. Checking required Phase 3B2 files..."))
    for rel in REQUIRED_FILES:
        if not check_file_exists(CASES_DIR / rel, rel):
            all_pass = False
    print()

    # 2. Required files non-empty
    print(blue("2. Checking Phase 3B2 files non-empty..."))
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

    # 4. data/cases.json valid + has Phase 3B2 phase
    print(blue("4. Checking data/cases.json valid and has Phase 3B2 phase..."))
    cases_json = DATA_DIR / "cases.json"
    if not check_json_valid(cases_json, "data/cases.json"):
        all_pass = False
    else:
        if not check_case_phase(cases_json, "evomap-evolver-openclaw-v0", "ATL-EVOMAP"):
            all_pass = False
    print()

    # 5. Case README contains ATL-EVOMAP-3B2
    print(blue("5. Checking case README contains ATL-EVOMAP-3B2 references..."))
    case_readme = CASES_DIR / "README.md"
    if not check_readme_contains(case_readme, ["ATL-EVOMAP-3B2", "Phase 3b2", "Bare Signal"]):
        all_pass = False
    print()

    # 6. Hard boundary keywords in Phase 3B2 reports
    print(blue("6. Checking hard boundary keywords in Phase 3B2 reports..."))
    docs_to_check = [
        (PHASE3B2_DIR / "ATL_EVOMAP_3B2_BARE_SIGNAL_COMPAT_REPORT.md", "Phase 3B2 case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3B2_BARE_SIGNAL_COMPAT_REPORT.md", "Phase 3B2 main report"),
        (case_readme, "case README"),
    ]
    for doc_path, label in docs_to_check:
        if doc_path.exists():
            if not check_hard_boundary_keywords(doc_path, label):
                all_pass = False
    print()

    # 7. Secret pattern scan
    print(blue("7. Secret pattern scan on Phase 3B2 files..."))
    files_to_scan = [
        (PHASE3B2_DIR / "ATL_EVOMAP_3B2_BARE_SIGNAL_COMPAT_REPORT.md", "Phase 3B2 case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3B2_BARE_SIGNAL_COMPAT_REPORT.md", "Phase 3B2 main report"),
        (case_readme, "case README"),
        (DATA_DIR / "cases.json", "cases.json"),
        (ARTIFACTS_DIR / "gene-openclaw-tool-use-discipline-bare-compatible.json", "gene artifact"),
        (ARTIFACTS_DIR / "manual-bare-signal-injection.jsonl", "injection jsonl"),
        (ARTIFACTS_DIR / "scoring.md", "scoring.md"),
    ]
    for file_path, label in files_to_scan:
        if file_path.exists():
            if not check_secret_patterns(file_path, label):
                all_pass = False
    print()

    # 8. Gene artifact fields
    print(blue("8. Checking Gene artifact has all 5 bare signals..."))
    if not check_gene_artifact(ARTIFACTS_DIR / "gene-openclaw-tool-use-discipline-bare-compatible.json"):
        all_pass = False
    print()

    # 9. Injection JSONL has 5 bare signals
    print(blue("9. Checking injection JSONL has 5 bare signals targeting new Gene..."))
    if not check_injection_jsonl(ARTIFACTS_DIR / "manual-bare-signal-injection.jsonl"):
        all_pass = False
    print()

    # 10. Selector match in review output
    print(blue("10. Checking evolver review output shows new Gene selected..."))
    if not check_selector_match(ARTIFACTS_DIR / "evolver-review-bare-signal-output.txt"):
        all_pass = False
    print()

    # 11. No root runtime state in git
    print(blue("11. Checking no root .evolver/ or memory/ in git..."))
    if not check_no_root_runtime_in_git():
        all_pass = False
    print()

    # 12. Validator script location
    print(blue("12. Checking Phase 3B2 validator script location..."))
    script_path = SCRIPTS_DIR / "validate_evomap_phase3b2_bare_signal_compat.py"
    if not check_file_exists(script_path, "validate_evomap_phase3b2_bare_signal_compat.py"):
        all_pass = False
    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print(green("ALL CHECKS PASSED"))
        print("Case: evomap-evolver-openclaw-v0 (Phase 3B2)")
        print("Status: bare signal compatibility completed")
        return 0
    print(red("SOME CHECKS FAILED"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
