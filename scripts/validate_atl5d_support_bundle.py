#!/usr/bin/env python3
"""ATL-5D support bundle validator (Python stdlib only).

Verifies the ATL-5D support bundle is ready to ship to Castform support / Castie:
  * support directory exists
  * ATL5D_SUPPORT_REQUEST.md exists
  * ATL5D_FAILURE_SUMMARY.md exists
  * run_id is referenced in both files
  * FAILED_STEP_0_NO_ROLLOUTS is referenced in both files
  * files do not contain API keys, sk-* style keys, Authorization headers, cookies, or key-like private tokens

Exits 0 on PASS, 1 on FAIL. Outputs PASS/FAIL line plus detailed reason list.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_DIR = (
    REPO_ROOT
    / "cases"
    / "castform-hermes-phase-closer-v0"
    / "cloud-smoke-run"
    / "support"
)
REQUEST_FILE = SUPPORT_DIR / "ATL5D_SUPPORT_REQUEST.md"
SUMMARY_FILE = SUPPORT_DIR / "ATL5D_FAILURE_SUMMARY.md"

RUN_ID = "c83f971d-2b2c-42b8-9774-ca64938c1286"
STATUS_TAG = "FAILED_STEP_0_NO_ROLLOUTS"

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{8,}"),
    re.compile(r"sk_test_[A-Za-z0-9]{8,}"),
    re.compile(r"CFK-[A-Za-z0-9]{8,}"),
    re.compile(r"castform_[A-Za-z0-9]{8,}"),
    re.compile(r"CASTFORM_API_KEY\s*=\s*[A-Za-z0-9]{8,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}", re.IGNORECASE),
    re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{8,}", re.IGNORECASE),
    re.compile(r"Cookie\s*:\s*[A-Za-z0-9=._;-]{8,}", re.IGNORECASE),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"gho_[A-Za-z0-9]{16,}"),
    re.compile(r"ghu_[A-Za-z0-9]{16,}"),
    re.compile(r"ghs_[A-Za-z0-9]{16,}"),
    re.compile(r"ghr_[A-Za-z0-9]{16,}"),
]

SECRET_LITERALS = [
    "cf" + "_" + "J",
]


def _check_file(path: Path, must_contain: list) -> list:
    issues = []
    if not path.exists():
        issues.append(f"missing file: {path}")
        return issues
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"unreadable file {path}: {exc}")
        return issues
    for needle in must_contain:
        if needle not in text:
            issues.append(f"{path.name}: missing required token: {needle!r}")
    for pat in SECRET_PATTERNS:
        match = pat.search(text)
        if match:
            issues.append(
                f"{path.name}: secret-shaped match for pattern {pat.pattern!r}: "
                f"<REDACTED_SECRET_LITERAL>"
            )
    for literal in SECRET_LITERALS:
        if literal in text:
            issues.append(
                f"{path.name}: contains forbidden secret literal: {literal!r}"
            )
    return issues


def main() -> int:
    issues = []

    if not SUPPORT_DIR.exists():
        issues.append(f"missing support directory: {SUPPORT_DIR}")
    if not SUPPORT_DIR.is_dir():
        issues.append(f"support path is not a directory: {SUPPORT_DIR}")

    issues.extend(_check_file(REQUEST_FILE, [RUN_ID, STATUS_TAG]))
    issues.extend(_check_file(SUMMARY_FILE, [RUN_ID, STATUS_TAG]))

    if issues:
        print("FAIL: validate_atl5d_support_bundle")
        for line in issues:
            print(f"  - {line}")
        return 1

    print("PASS: validate_atl5d_support_bundle")
    print(f"  - support dir: {SUPPORT_DIR}")
    print(f"  - request file: {REQUEST_FILE.name}")
    print(f"  - summary file: {SUMMARY_FILE.name}")
    print(f"  - run_id token present in both: {RUN_ID}")
    print(f"  - status tag present in both: {STATUS_TAG}")
    print(f"  - secret-pattern scan: clean ({len(SECRET_PATTERNS)} patterns, {len(SECRET_LITERALS)} literals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
