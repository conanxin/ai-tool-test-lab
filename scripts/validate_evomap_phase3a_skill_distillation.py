#!/usr/bin/env python3
"""
validate_evomap_phase3a_skill_distillation.py

Validates the ATL-EVOMAP-3A EvoMap Evolver OpenClaw-specific skill
distillation case structure and compliance with hard boundaries.

Usage: python3 scripts/validate_evomap_phase3a_skill_distillation.py
Exit codes: 0 = PASS, 1 = FAIL
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
CASES_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0"
PHASE3A_DIR = CASES_DIR / "phase3-skill-distillation"
SKILLS_DIR = PHASE3A_DIR / "skills"
INPUTS_DIR = PHASE3A_DIR / "inputs"
ARTIFACTS_DIR = PHASE3A_DIR / "artifacts"
REPORTS_DIR = REPO_ROOT / "reports"
SCRIPTS_DIR = REPO_ROOT / "scripts"
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
    # private_key only when it's a real value (key=private_key or "private_key": or BEGIN block)
    r"private_key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}",
    r'"private_key"\s*:\s*"',
    r"-----BEGIN (RSA |EC |DSA |OPENSSH )PRIVATE KEY-----",
]

FORBIDDEN_CONTENT = [
    r"API_KEY\s*=\s*[A-Za-z0-9_-]{10,}",
    r"TOKEN\s*=\s*[A-Za-z0-9_-]{10,}",
    r"SECRET\s*=\s*[A-Za-z0-9_-]{10,}",
    r"PASSWORD\s*=\s*[A-Za-z0-9_-]{6,}",
]

REQUIRED_FILES = [
    "phase3-skill-distillation/ATL_EVOMAP_3A_SKILL_DISTILLATION_REPORT.md",
    "phase3-skill-distillation/skills/openclaw-tool-use-discipline.SKILL.md",
    "phase3-skill-distillation/inputs/skill-as-llm-response.md",
    "phase3-skill-distillation/artifacts/distilled-gene-openclaw-tool-use-discipline.json",
    "phase3-skill-distillation/artifacts/manual-distill-request.json",
    "phase3-skill-distillation/artifacts/evolver-top-help.txt",
    "phase3-skill-distillation/artifacts/evolver-distill-noargs-output.txt",
    "phase3-skill-distillation/artifacts/evolver-distill-direct-call-output.txt",
    "phase3-skill-distillation/artifacts/evolver-distill-manual-request-output.txt",
    "phase3-skill-distillation/artifacts/evolver-run-after-distill-output.txt",
    "phase3-skill-distillation/artifacts/evolver-review-after-distill-output.txt",
]

# Hard boundary keywords
REQUIRED_HARD_BOUNDARY_KEYWORDS = [
    "no hub",
    "no credits",
    "no auto-publish",
    "no validator",
    "no --loop",
]

# Required OpenClaw-specific signals in the Skill
REQUIRED_SIGNALS = [
    "tool_bypass:exec-on-grep",
    "session_context:openclaw",
    "repo_context:ai-tool-test-lab",
]

# Required Gene ID
EXPECTED_GENE_ID = "gene_distilled_openclaw-tool-use-discipline"

REPORT_FILES = [
    REPORTS_DIR / "ATL_EVOMAP_3A_SKILL_DISTILLATION_REPORT.md",
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
        print(red(f"File empty: {label} (0 bytes)"))
        return False
    else:
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
                else:
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


def check_skill_contains_signals(skill_path: Path) -> bool:
    """Check that the SKILL.md contains all required OpenClaw-specific signals."""
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(red(f"Skill file not found: {skill_path}"))
        return False

    all_pass = True
    for signal in REQUIRED_SIGNALS:
        if signal in content:
            print(green(f"Skill contains signal '{signal}'"))
        else:
            print(red(f"Skill does NOT contain signal '{signal}'"))
            all_pass = False
    return all_pass


def check_gene_in_local_store() -> bool:
    """Check that the distilled gene exists in the local GEP store."""
    genes_path = REPO_ROOT / ".evolver" / "gep" / "genes.json"
    if not genes_path.exists():
        print(yellow(f"Local GEP store not found (run-time state, may be ignored): {genes_path}"))
        return True  # Not a hard fail

    try:
        with open(genes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for g in data.get("genes", []):
            if g.get("id") == EXPECTED_GENE_ID:
                print(green(f"Distilled gene '{EXPECTED_GENE_ID}' found in local GEP store"))
                # Verify signals
                signals = g.get("signals_match", [])
                for required in REQUIRED_SIGNALS:
                    if required in signals:
                        print(green(f"Gene has signal '{required}'"))
                    else:
                        print(yellow(f"Gene missing signal '{required}'"))
                return True
        print(red(f"Distilled gene '{EXPECTED_GENE_ID}' NOT found in local GEP store"))
        return False
    except Exception as e:
        print(red(f"Error reading GEP store: {e}"))
        return False


def check_distilled_gene_artifact(artifact_path: Path) -> bool:
    """Check that the distilled-gene artifact contains expected fields."""
    try:
        with open(artifact_path, "r", encoding="utf-8") as f:
            gene = json.load(f)
    except FileNotFoundError:
        print(red(f"Gene artifact not found: {artifact_path}"))
        return False
    except json.JSONDecodeError as e:
        print(red(f"Gene artifact invalid JSON: {e}"))
        return False

    all_pass = True
    expected_fields = ["id", "type", "signals_match", "strategy", "constraints"]
    for field in expected_fields:
        if field in gene:
            print(green(f"Gene has field '{field}'"))
        else:
            print(red(f"Gene missing field '{field}'"))
            all_pass = False

    if gene.get("id") == EXPECTED_GENE_ID:
        print(green(f"Gene ID matches expected: {EXPECTED_GENE_ID}"))
    else:
        print(red(f"Gene ID mismatch: got {gene.get('id')}, expected {EXPECTED_GENE_ID}"))
        all_pass = False

    forbidden_paths = gene.get("constraints", {}).get("forbidden_paths", [])
    required_forbidden = [".git", "node_modules"]
    for fp in required_forbidden:
        if fp in forbidden_paths:
            print(green(f"Gene constraints include forbidden path '{fp}'"))
        else:
            print(yellow(f"Gene constraints missing forbidden path '{fp}'"))

    return all_pass


def main():
    print("=" * 60)
    print("ATL-EVOMAP-3A EvoMap Evolver OpenClaw Skill Distillation Validator")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Required files exist
    print(blue("1. Checking required Phase 3a files..."))
    for rel_path in REQUIRED_FILES:
        path = CASES_DIR / rel_path
        if not check_file_exists(path, rel_path):
            all_pass = False
    print()

    # 2. Required files non-empty
    print(blue("2. Checking Phase 3a files non-empty..."))
    for rel_path in REQUIRED_FILES:
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
    print(blue("4. Checking data/cases.json valid and has Phase 3a phase..."))
    cases_json = DATA_DIR / "cases.json"
    if not check_json_valid(cases_json, "data/cases.json"):
        all_pass = False
    else:
        if not check_case_phase(cases_json, "evomap-evolver-openclaw-v0", "ATL-EVOMAP"):
            all_pass = False
    print()

    # 5. Case README contains ATL-EVOMAP-3A
    print(blue("5. Checking case README contains ATL-EVOMAP-3A references..."))
    case_readme = CASES_DIR / "README.md"
    if not check_readme_contains(case_readme, ["ATL-EVOMAP-3A", "Phase 3a", "OpenClaw-Specific Skill Distillation"]):
        all_pass = False
    print()

    # 6. Hard boundary keywords in Phase 3a reports
    print(blue("6. Checking hard boundary keywords in Phase 3a reports..."))
    docs_to_check = [
        (PHASE3A_DIR / "ATL_EVOMAP_3A_SKILL_DISTILLATION_REPORT.md", "Phase 3a case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3A_SKILL_DISTILLATION_REPORT.md", "Phase 3a main report"),
        (case_readme, "case README"),
    ]
    for doc_path, label in docs_to_check:
        if doc_path.exists():
            if not check_hard_boundary_keywords(doc_path, label):
                all_pass = False
    print()

    # 7. Secret pattern scan
    print(blue("7. Secret pattern scan on Phase 3a files..."))
    files_to_scan = [
        (PHASE3A_DIR / "ATL_EVOMAP_3A_SKILL_DISTILLATION_REPORT.md", "Phase 3a case report"),
        (REPORTS_DIR / "ATL_EVOMAP_3A_SKILL_DISTILLATION_REPORT.md", "Phase 3a main report"),
        (SKILLS_DIR / "openclaw-tool-use-discipline.SKILL.md", "Skill file"),
        (case_readme, "case README"),
        (DATA_DIR / "cases.json", "cases.json"),
        (ARTIFACTS_DIR / "distilled-gene-openclaw-tool-use-discipline.json", "distilled gene JSON"),
    ]
    for file_path, label in files_to_scan:
        if file_path.exists():
            if not check_secret_patterns(file_path, label):
                all_pass = False
    print()

    # 8. Skill contains OpenClaw-specific signals
    print(blue("8. Checking Skill contains OpenClaw-specific signals..."))
    skill_path = SKILLS_DIR / "openclaw-tool-use-discipline.SKILL.md"
    if not check_skill_contains_signals(skill_path):
        all_pass = False
    print()

    # 9. Distilled gene artifact fields
    print(blue("9. Checking distilled gene artifact fields..."))
    gene_artifact = ARTIFACTS_DIR / "distilled-gene-openclaw-tool-use-discipline.json"
    if not check_distilled_gene_artifact(gene_artifact):
        all_pass = False
    print()

    # 10. Gene in local GEP store
    print(blue("10. Checking distilled gene in local GEP store..."))
    if not check_gene_in_local_store():
        all_pass = False
    print()

    # 11. Distill output contains success message
    print(blue("11. Checking distill output contains success message..."))
    distill_output = ARTIFACTS_DIR / "evolver-distill-manual-request-output.txt"
    if distill_output.exists():
        try:
            with open(distill_output, "r", encoding="utf-8") as f:
                content = f.read()
            if EXPECTED_GENE_ID in content and "Distillation complete" in content:
                print(green("Distill output contains success: 'Distillation complete' + Gene ID"))
            else:
                print(red("Distill output does NOT contain expected success message"))
                all_pass = False
        except Exception as e:
            print(red(f"Error reading distill output: {e}"))
            all_pass = False
    print()

    # 12. Validator script location
    print(blue("12. Checking Phase 3a validator script location..."))
    script_path = SCRIPTS_DIR / "validate_evomap_phase3a_skill_distillation.py"
    if not check_file_exists(script_path, "validate_evomap_phase3a_skill_distillation.py"):
        all_pass = False
    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print(green("ALL CHECKS PASSED"))
        print("Case: evomap-evolver-openclaw-v0 (Phase 3a)")
        print("Status: openclaw skill distillation completed")
        return 0
    else:
        print(red("SOME CHECKS FAILED"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
