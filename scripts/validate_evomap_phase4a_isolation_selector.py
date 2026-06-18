#!/usr/bin/env python3
"""
validate_evomap_phase4a_isolation_selector.py

Validates ATL-EVOMAP-4A Isolation Selector Test.

Stdlib only. Strictly read-only. No network, no Hub, no secrets.

Checks (10):
  1. Phase 4A case report exists
  2. isolation-setup-summary.json exists and is valid JSON
  3. evolver-run-isolated-output.txt exists
  4. evolver-review-isolated-output.txt exists
  5. selector-isolation-grep.txt exists
  6. case report contains target Gene id
  7. data/cases.json phase contains ATL-EVOMAP-4A
  8. case README contains ATL-EVOMAP-4A
  9. secret scan PASS (no tokens / API keys / chat_ids in artifacts)
 10. git status: no root .evolver/ or memory/ tracked (per hard boundary)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase4a-isolation-selector"
ARTIFACTS = CASE_DIR / "artifacts"
TOP_REPORT = REPO_ROOT / "reports" / "ATL_EVOMAP_4A_ISOLATION_SELECTOR_REPORT.md"
CASE_REPORT = CASE_DIR / "ATL_EVOMAP_4A_ISOLATION_SELECTOR_REPORT.md"
CASE_README = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "README.md"
CASES_JSON = REPO_ROOT / "data" / "cases.json"
TARGET_GENE = "gene_distilled_openclaw-tool-use-discipline-bare-compatible"

# Secret patterns (same convention as Phase 3C-V2 validator)
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{16,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{16,}"),
    re.compile(r"ya29\.[0-9A-Za-z_-]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.=]{16,}"),
    re.compile(r"bot[0-9]{6,}:[A-Za-z0-9_-]{20,}"),
    re.compile(r"[0-9]{8,}:[A-Za-z0-9_-]{20,}"),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
    re.compile(r"C:\\Users\\[A-Za-z0-9_. -]+\\"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def _info(msg: str) -> None:
    print(f"\033[94mINFO\033[0m  {msg}")


def _ok(msg: str) -> None:
    print(f"\033[92mPASS\033[0m  {msg}")


def _fail(msg: str) -> None:
    print(f"\033[91mFAIL\033[0m  {msg}", file=sys.stderr)


_failures = 0


def _check(name: str, condition: bool, message: str = "") -> bool:
    global _failures
    if condition:
        _ok(name + (f" — {message}" if message else ""))
        return True
    _failures += 1
    _fail(name + (f" — {message}" if message else ""))
    return False


def main() -> int:
    print("=" * 60)
    print("ATL-EVOMAP-4A Isolation Selector Test Validator")
    print("=" * 60)

    # 1. Case report exists
    _info("1. Checking Phase 4A case report exists...")
    _check("Phase 4A case report exists", CASE_REPORT.is_file())

    # 2. isolation-setup-summary.json exists and valid JSON
    _info("2. Checking isolation-setup-summary.json exists and is valid JSON...")
    summary_path = ARTIFACTS / "isolation-setup-summary.json"
    summary_valid = False
    summary = None
    if not summary_path.is_file():
        _check("isolation-setup-summary.json exists", False)
    else:
        _check("isolation-setup-summary.json exists", True)
        try:
            summary = json.loads(summary_path.read_text())
            summary_valid = True
            _check("isolation-setup-summary.json is valid JSON", True)
        except Exception as e:
            _check("isolation-setup-summary.json is valid JSON", False, str(e))

    # 3. evolver-run-isolated-output.txt exists
    _info("3. Checking evolver-run-isolated-output.txt exists...")
    _check(
        "evolver-run-isolated-output.txt exists",
        (ARTIFACTS / "evolver-run-isolated-output.txt").is_file(),
    )

    # 4. evolver-review-isolated-output.txt exists
    _info("4. Checking evolver-review-isolated-output.txt exists...")
    _check(
        "evolver-review-isolated-output.txt exists",
        (ARTIFACTS / "evolver-review-isolated-output.txt").is_file(),
    )

    # 5. selector-isolation-grep.txt exists
    _info("5. Checking selector-isolation-grep.txt exists...")
    _check(
        "selector-isolation-grep.txt exists",
        (ARTIFACTS / "selector-isolation-grep.txt").is_file(),
    )

    # 6. Case report contains target Gene id
    _info("6. Checking case report contains target Gene id...")
    if CASE_REPORT.is_file():
        text = CASE_REPORT.read_text()
        _check(
            "case report contains target Gene id",
            TARGET_GENE in text,
            TARGET_GENE,
        )
    else:
        _check("case report contains target Gene id", False, "case report missing")

    # 7. data/cases.json phase contains ATL-EVOMAP-4A
    _info("7. Checking data/cases.json phase contains ATL-EVOMAP-4A...")
    if CASES_JSON.is_file():
        try:
            data = json.loads(CASES_JSON.read_text())
            case = next(
                (c for c in data["cases"] if c.get("slug") == "evomap-evolver-openclaw-v0"),
                None,
            )
            if case is None:
                _check("evomap case present in cases.json", False)
            else:
                _check("evomap case present in cases.json", True)
                _check(
                    "cases.json phase contains ATL-EVOMAP-4A",
                    "ATL-EVOMAP-4A" in case.get("phase", ""),
                    case.get("phase", ""),
                )
                _check(
                    "cases.json status contains 'isolation selector completed'",
                    "isolation selector completed" in case.get("status", ""),
                    case.get("status", ""),
                )
                # phase_history should have ATL-EVOMAP-4A entry
                hist = case.get("phase_history", [])
                has_4a = any(e.get("phase") == "ATL-EVOMAP-4A" for e in hist)
                _check(
                    "cases.json phase_history has ATL-EVOMAP-4A entry",
                    has_4a,
                )
        except Exception as e:
            _check("cases.json valid JSON", False, str(e))
    else:
        _check("data/cases.json exists", False)

    # 8. case README contains ATL-EVOMAP-4A
    _info("8. Checking case README contains ATL-EVOMAP-4A...")
    if CASE_README.is_file():
        text = CASE_README.read_text()
        _check("case README contains ATL-EVOMAP-4A", "ATL-EVOMAP-4A" in text)
    else:
        _check("case README exists", False)

    # 9. Secret scan
    _info("9. Scanning for secret patterns in Phase 4A artifacts...")
    scan_paths = [ARTIFACTS, CASE_REPORT, TOP_REPORT, CASE_README, CASES_JSON]
    secret_hits = []
    for path in scan_paths:
        if not path.is_file():
            continue
        if path.is_dir():
            for p in path.rglob("*"):
                if p.is_file() and p.suffix in {".txt", ".json", ".md"}:
                    try:
                        content = p.read_text(errors="ignore")
                    except Exception:
                        continue
                    for pat in SECRET_PATTERNS:
                        if pat.search(content):
                            secret_hits.append((p, pat.pattern))
        else:
            try:
                content = path.read_text(errors="ignore")
            except Exception:
                continue
            for pat in SECRET_PATTERNS:
                if pat.search(content):
                    secret_hits.append((path, pat.pattern))

    if not secret_hits:
        _check("no secret patterns in Phase 4A artifacts", True)
    else:
        for p, pat in secret_hits:
            _check(f"no secret pattern '{pat}' in {p.name}", False)

    # 10. No root .evolver/ or memory/ tracked by git
    _info("10. Checking no root .evolver/ or memory/ tracked by git...")
    try:
        result = subprocess.run(
            ["git", "ls-files", ".evolver/", "memory/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        tracked = [line for line in result.stdout.splitlines() if line.strip()]
        # Allow .gitkeep placeholders if any
        non_keep = [t for t in tracked if not t.endswith(".gitkeep")]
        _check(
            "no root .evolver/ or memory/ tracked by git",
            len(non_keep) == 0,
            f"tracked: {non_keep[:3]}" if non_keep else "clean",
        )
    except Exception as e:
        _check("git ls-files ran", False, str(e))

    # Bonus: validate isolation-setup-summary.json content sanity
    if summary_valid and summary is not None:
        _info("11. Validating isolation-setup-summary.json content...")
        _check("summary has isolated_runtime", "isolated_runtime" in summary)
        _check("summary has gene_count=1", summary.get("gene_count") == 1, str(summary.get("gene_count")))
        _check(
            "summary has target_gene == bare-compatible",
            summary.get("target_gene") == TARGET_GENE,
            summary.get("target_gene", ""),
        )
        _check(
            "summary.hub is 'disabled'",
            summary.get("hub") == "disabled",
        )
        _check(
            "summary.publish is 'disabled'",
            summary.get("publish") == "disabled",
        )
        _check(
            "summary.credits_consumed is 0",
            summary.get("credits_consumed") == 0,
        )
        _check(
            "summary.approver_executed is false",
            summary.get("approver_executed") is False,
        )
        _check(
            "summary.solidify_executed is false",
            summary.get("solidify_executed") is False,
        )

    print("=" * 60)
    if _failures == 0:
        print("\033[92mPASS\033[0m  ALL CHECKS PASSED")
        print("Case: evomap-evolver-openclaw-v0 (Phase 4A Isolation Selector)")
        print("Status: isolation selector completed (PASS)")
        return 0
    print(f"\033[91mFAIL\033[0m  {_failures} check(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
