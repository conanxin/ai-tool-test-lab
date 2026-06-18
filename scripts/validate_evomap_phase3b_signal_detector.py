#!/usr/bin/env python3
"""
validate_evomap_phase3b_signal_detector.py

Validates the ATL-EVOMAP-3B EvoMap Evolver OpenClaw signal detector case
structure and compliance with hard boundaries.

Usage: python3 scripts/validate_evomap_phase3b_signal_detector.py
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
PHASE3B_DIR = CASES_DIR / "phase3b-signal-detector"
FIXTURES_DIR = PHASE3B_DIR / "fixtures"
ARTIFACTS_DIR = PHASE3B_DIR / "artifacts"
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
    "phase3b-signal-detector/ATL_EVOMAP_3B_SIGNAL_DETECTOR_REPORT.md",
    "phase3b-signal-detector/fixtures/session-tail-tool-bypass.txt",
    "phase3b-signal-detector/artifacts/detected-signals-fixture.json",
    "phase3b-signal-detector/artifacts/detected-signals-real-session.json",
    "phase3b-signal-detector/artifacts/evolver-run-after-signal-injection-output.txt",
    "phase3b-signal-detector/artifacts/evolver-review-after-signal-injection-output.txt",
    "phase3b-signal-detector/artifacts/manual-memory-graph-injection.jsonl",
    "phase3b-signal-detector/artifacts/selector-match-grep.txt",
    "phase3b-signal-detector/artifacts/scoring.md",
]

# Required signals in fixture output
REQUIRED_FIXTURE_SIGNALS = [
    "tool_bypass:exec-on-grep",
    "repeated_tool_usage:exec",
    "protocol_drift:wrong-tool-for-file-read",
    "session_context:openclaw",
    "repo_context:ai-tool-test-lab",
]

# Hard boundary keywords
REQUIRED_HARD_BOUNDARY_KEYWORDS = [
    "no hub",
    "no credits",
    "no auto-publish",
    "no validator",
    "no --loop",
]

REPORT_FILES = [
    REPORTS_DIR / "ATL_EVOMAP_3B_SIGNAL_DETECTOR_REPORT.md",
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


def check_fixture_signals(signal_json_path: Path) -> bool:
    """Check that fixture detection output contains all 5 required signals."""
    try:
        with open(signal_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(red(f"Could not read signals JSON: {e}"))
        return False
    signal_keys = [s.get("key", "") for s in data.get("signals", [])]
    all_pass = True
    for required in REQUIRED_FIXTURE_SIGNALS:
        if required in signal_keys:
            print(green(f"Fixture emits signal '{required}'"))
        else:
            print(red(f"Fixture does NOT emit signal '{required}'"))
            all_pass = False
    return all_pass


def check_detector_smoke_test() -> bool:
    """Re-run the detector on the fixture to confirm reproducibility."""
    fixture = FIXTURES_DIR / "session-tail-tool-bypass.txt"
    output_tmp = Path("/tmp/phase3b_detector_smoke_test.json")
    if not fixture.exists():
        print(red(f"Fixture missing for smoke test: {fixture}"))
        return False
    detector = SCRIPTS_DIR / "openclaw_signal_detector.py"
    if not detector.exists():
        print(red(f"Detector script missing: {detector}"))
        return False
    try:
        result = subprocess.run(
            ["python3", str(detector), "--input", str(fixture), "--output", str(output_tmp)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(red(f"Detector smoke test failed (exit {result.returncode}): {result.stderr[:200]}"))
            return False
        with open(output_tmp, "r", encoding="utf-8") as f:
            data = json.load(f)
        n = len(data.get("signals", []))
        if n >= 5:
            print(green(f"Detector smoke test PASS ({n} signals emitted)"))
            return True
        print(red(f"Detector smoke test PARTIAL: only {n} signals"))
        return False
    except Exception as e:
        print(red(f"Detector smoke test exception: {e}"))
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
        # Filter out case dir paths
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
    print("ATL-EVOMAP-3B EvoMap Evolver OpenClaw Signal Detector Validator")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Required files exist
    print(blue("1. Checking required Phase 3B files..."))
    for rel in REQUIRED_FILES:
        if not check_file_exists(CASES_DIR / rel, rel):
            all_pass = False
    print()

    # 2. Required files non-empty
    print(blue("2. Checking Phase 3B files non-empty..."))
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

    # 4. data/cases.json valid + has Phase 3B phase
    print(blue("4. Checking data/cases.json valid and has Phase 3B phase..."))
    cases_json = DATA_DIR / "cases.json"
    if not check_json_valid(cases_json, "data/cases.json"):
        all_pass = False
    else:
        if not check_case_phase(cases_json, "evomap-evolver-openclaw-v0", "ATL-EVOMAP-3B"):
            all_pass = False
    print()

    # 5. Case README contains ATL-EVOMAP-3B
    print(blue("5. Checking case README contains ATL-EVOMAP-3B references..."))
    case_readme = CASES_DIR / "README.md"
    if not check_readme_contains(case_readme, ["ATL-EVOMAP-3B", "Phase 3b", "Signal Detector"]):
        all_pass = False
    print()

    # 6. Hard boundary keywords in Phase 3B reports
    print(blue("6. Checking hard boundary keywords in Phase 3B reports..."))
    docs_to_check = [
        (PHASE3B_DIR / "ATL_EVOMAP_3B_SIGNAL_DETECTOR_REPORT.md", "Phase 3B case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3B_SIGNAL_DETECTOR_REPORT.md", "Phase 3B main report"),
        (case_readme, "case README"),
    ]
    for doc_path, label in docs_to_check:
        if doc_path.exists():
            if not check_hard_boundary_keywords(doc_path, label):
                all_pass = False
    print()

    # 7. Secret pattern scan
    print(blue("7. Secret pattern scan on Phase 3B files..."))
    files_to_scan = [
        (PHASE3B_DIR / "ATL_EVOMAP_3B_SIGNAL_DETECTOR_REPORT.md", "Phase 3B case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3B_SIGNAL_DETECTOR_REPORT.md", "Phase 3B main report"),
        (SCRIPTS_DIR / "openclaw_signal_detector.py", "detector script"),
        (FIXTURES_DIR / "session-tail-tool-bypass.txt", "fixture"),
        (case_readme, "case README"),
        (DATA_DIR / "cases.json", "cases.json"),
        (ARTIFACTS_DIR / "detected-signals-fixture.json", "fixture signals JSON"),
        (ARTIFACTS_DIR / "detected-signals-real-session.json", "real session signals JSON"),
        (ARTIFACTS_DIR / "manual-memory-graph-injection.jsonl", "injection jsonl"),
    ]
    for file_path, label in files_to_scan:
        if file_path.exists():
            if not check_secret_patterns(file_path, label):
                all_pass = False
    print()

    # 8. Fixture signals contain all 5 required
    print(blue("8. Checking fixture detection contains 5 required signals..."))
    if not check_fixture_signals(ARTIFACTS_DIR / "detected-signals-fixture.json"):
        all_pass = False
    print()

    # 9. Detector smoke test (re-run)
    print(blue("9. Re-running detector on fixture for reproducibility..."))
    if not check_detector_smoke_test():
        all_pass = False
    print()

    # 10. No root runtime state in git
    print(blue("10. Checking no root .evolver/ or memory/ in git..."))
    if not check_no_root_runtime_in_git():
        all_pass = False
    print()

    # 11. Phase 3B validator location
    print(blue("11. Checking Phase 3B validator script location..."))
    script_path = SCRIPTS_DIR / "validate_evomap_phase3b_signal_detector.py"
    if not check_file_exists(script_path, "validate_evomap_phase3b_signal_detector.py"):
        all_pass = False
    print()

    # 12. No real secret in injection jsonl
    print(blue("12. Re-checking injection jsonl for placeholder-only fields..."))
    inj = ARTIFACTS_DIR / "manual-memory-graph-injection.jsonl"
    if inj.exists():
        with open(inj, "r", encoding="utf-8") as f:
            content = f.read()
        # Must contain target gene id and signals
        must_have = [
            "manual_openclaw_tool_bypass_phase3b",
            "tool_bypass:exec-on-grep",
            "session_context:openclaw",
            "repo_context:ai-tool-test-lab",
            "gene_distilled_openclaw-tool-use-discipline",
        ]
        for s in must_have:
            if s in content:
                print(green(f"Injection jsonl contains '{s}'"))
            else:
                print(red(f"Injection jsonl missing '{s}'"))
                all_pass = False
    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print(green("ALL CHECKS PASSED"))
        print("Case: evomap-evolver-openclaw-v0 (Phase 3B)")
        print("Status: openclaw signal detector partial")
        return 0
    print(red("SOME CHECKS FAILED"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
