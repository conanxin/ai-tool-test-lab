#!/usr/bin/env python3
"""ATL-CLOSEOUT case closeout validator (Python stdlib only).

Verifies the ATL-CLOSEOUT final closeout bundle is ready to ship to Castform support / Castie:
  * CASE_CLOSEOUT.md exists
  * CASTFORM_SUPPORT_REQUEST_FINAL.md exists
  * ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md exists
  * data/cases.json has Castform case status = "paused pending Castform backend logs" and phase = "CASE-CLOSEOUT"
  * both run_id tokens appear in CASE_CLOSEOUT.md and CASTFORM_SUPPORT_REQUEST_FINAL.md
  * PAUSED_PENDING_CASTFORM_BACKEND_LOGS appears in CASE_CLOSEOUT.md and CASTFORM_SUPPORT_REQUEST_FINAL.md
  * files do not contain API keys, sk-* style keys, Authorization headers, cookies, or key-like private tokens

Exits 0 on PASS, 1 on FAIL. Outputs PASS/FAIL line plus detailed reason list.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "castform-hermes-phase-closer-v0"
REPORT_DIR = REPO_ROOT / "reports"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

CASE_CLOSEOUT_FILE = CASE_DIR / "CASE_CLOSEOUT.md"
SUPPORT_REQUEST_FILE = CASE_DIR / "CASTFORM_SUPPORT_REQUEST_FINAL.md"
CLOSEOUT_REPORT_FILE = REPORT_DIR / "ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md"

RUN_ID_RUN1 = "c83f971d-2b2c-42b8-9774-ca64938c1286"
RUN_ID_RUN2 = "56cb5701-6b3e-424e-b671-fc2efc932aa8"
STATUS_TAG = "PAUSED_PENDING_CASTFORM_BACKEND_LOGS"
EXPECTED_CASE_PHASE = "CASE-CLOSEOUT"
EXPECTED_CASE_STATUS = "paused pending Castform backend logs"

SECRET_PATTERNS = (
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
)

SECRET_LITERALS = (
    "cf" + "_" + "J",
)


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


def _check_cases_json() -> list:
    issues = []
    if not CASES_JSON.exists():
        issues.append(f"missing file: {CASES_JSON}")
        return issues
    try:
        raw = CASES_JSON.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"unreadable or invalid json {CASES_JSON}: {exc}")
        return issues
    cases = data.get("cases", [])
    castform = None
    for c in cases:
        if c.get("slug") == "castform-hermes-phase-closer-v0":
            castform = c
            break
    if castform is None:
        issues.append("cases.json: no case with slug castform-hermes-phase-closer-v0")
        return issues
    if castform.get("phase") != EXPECTED_CASE_PHASE:
        issues.append(
            f"cases.json: Castform case phase != {EXPECTED_CASE_PHASE!r} "
            f"(got {castform.get('phase')!r})"
        )
    if castform.get("status") != EXPECTED_CASE_STATUS:
        issues.append(
            f"cases.json: Castform case status != {EXPECTED_CASE_STATUS!r} "
            f"(got {castform.get('status')!r})"
        )
    for pat in SECRET_PATTERNS:
        if pat.search(raw):
            issues.append(
                f"cases.json: secret-shaped match for pattern {pat.pattern!r}"
            )
    return issues


def main() -> int:
    issues = []

    if not CASE_DIR.exists():
        issues.append(f"missing case dir: {CASE_DIR}")
    if not REPORT_DIR.exists():
        issues.append(f"missing report dir: {REPORT_DIR}")

    issues.extend(_check_file(CASE_CLOSEOUT_FILE, [RUN_ID_RUN1, RUN_ID_RUN2, STATUS_TAG]))
    issues.extend(_check_file(SUPPORT_REQUEST_FILE, [RUN_ID_RUN1, RUN_ID_RUN2, STATUS_TAG]))
    issues.extend(_check_file(CLOSEOUT_REPORT_FILE, [STATUS_TAG]))
    issues.extend(_check_cases_json())

    if issues:
        print("FAIL: validate_case_closeout")
        for line in issues:
            print(f"  - {line}")
        return 1

    print("PASS: validate_case_closeout")
    print(f"  - case dir: {CASE_DIR}")
    print(f"  - CASE_CLOSEOUT.md: {CASE_CLOSEOUT_FILE.name}")
    print(f"  - CASTFORM_SUPPORT_REQUEST_FINAL.md: {SUPPORT_REQUEST_FILE.name}")
    print(f"  - ATL_FINAL_CASTFORM_CASE_CLOSEOUT_REPORT.md: {CLOSEOUT_REPORT_FILE.name}")
    print(f"  - data/cases.json Castform case phase: {EXPECTED_CASE_PHASE}")
    print(f"  - data/cases.json Castform case status: {EXPECTED_CASE_STATUS}")
    print(f"  - run_id Run 1 present: {RUN_ID_RUN1}")
    print(f"  - run_id Run 2 present: {RUN_ID_RUN2}")
    print(f"  - status tag present: {STATUS_TAG}")
    print(f"  - secret-pattern scan: clean ({len(SECRET_PATTERNS)} patterns, {len(SECRET_LITERALS)} literals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
