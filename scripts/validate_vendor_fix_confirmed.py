#!/usr/bin/env python3
"""ATL-RESUME-2C vendor fix confirmed validator (Python stdlib only).

Verifies the ATL-RESUME-2C Castform vendor-fix confirmed-by-retest bundle:

  * VENDOR_FIX_CONFIRMED.md exists
  * the new status tag `VENDOR_FIX_CONFIRMED_BY_RETEST` appears
  * the retest run_id `e4abb2dc-cc68-4b52-8ba5-2195c3f12d1d` appears
  * data/cases.json has Castform case final_status == "VENDOR_FIX_CONFIRMED_BY_RETEST"
  * CASE_CLOSEOUT.md still preserves the historical closeout status
    `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` (audit trail invariant)
  * files do not contain API keys, sk-* style keys, Authorization headers,
    cookies, or key-like private tokens (16 secret patterns + 1 forbidden
    literal scan; the forbidden literal is built at runtime via chr-concat
    so the validator source itself does not contain the bare pattern - see
    pitfall #27 in the ai-tool-test-lab SKILL).

Exits 0 on PASS, 1 on FAIL. Outputs PASS/FAIL line plus detailed reason list.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "castform-hermes-phase-closer-v0"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

VENDOR_CONFIRMED_FILE = CASE_DIR / "VENDOR_FIX_CONFIRMED.md"
CASE_CLOSEOUT_FILE = CASE_DIR / "CASE_CLOSEOUT.md"
SUPPORT_REQUEST_FILE = CASE_DIR / "CASTFORM_SUPPORT_REQUEST_FINAL.md"
RESUME2C_REPORT_FILE = REPO_ROOT / "reports" / "ATL_RESUME2C_VENDOR_FIX_CONFIRMED_REPORT.md"

RETEST_RUN_ID = "e4abb2dc-cc68-4b52-8ba5-2195c3f12d1d"

NEW_STATUS_TAG = "VENDOR_FIX_CONFIRMED_BY_RETEST"
HISTORICAL_STATUS_TAGS = (
    "PAUSED_PENDING_CASTFORM_BACKEND_LOGS",
    "VENDOR_FIX_RECEIVED_RETEST_PENDING",
)

EXPECTED_CASE_PHASE = "ATL-RESUME-2C vendor fix confirmed by retest"
EXPECTED_CASE_STATUS = "vendor fix confirmed by retest"
EXPECTED_CASE_FINAL_STATUS = "VENDOR_FIX_CONFIRMED_BY_RETEST"

# 16 secret patterns mirrored from the ATL-CLOSEOUT validator for consistency.
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

# Forbidden-literal scan: built at runtime via chr-concat so the validator source
# itself does not contain the bare key-prefix pattern (per pitfall #27).
SECRET_LITERALS = (
    "cf" + "_" + "J",
)

OLD_FAILED_RUN_IDS = (
    "c83f971d-2b2c-42b8-9774-ca64938c1286",
    "56cb5701-6b3e-424e-b671-fc2efc932aa8",
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
                f"{path.name}: secret-shaped match for pattern {pat.pattern!r}: <REDACTED>"
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
    if castform.get("final_status") != EXPECTED_CASE_FINAL_STATUS:
        issues.append(
            f"cases.json: Castform case final_status != {EXPECTED_CASE_FINAL_STATUS!r} "
            f"(got {castform.get('final_status')!r})"
        )
    if not castform.get("canonical_example", False):
        issues.append("cases.json: Castform case canonical_example must remain True")
    if not castform.get("workflow_reference", False):
        issues.append("cases.json: Castform case workflow_reference must remain True")
    for pat in SECRET_PATTERNS:
        if pat.search(raw):
            issues.append(
                f"cases.json: secret-shaped match for pattern {pat.pattern!r}"
            )
    for literal in SECRET_LITERALS:
        if literal in raw:
            issues.append(
                f"cases.json: contains forbidden secret literal: {literal!r}"
            )
    return issues


def main() -> int:
    issues = []

    if not CASE_DIR.exists():
        issues.append(f"missing case dir: {CASE_DIR}")

    # VENDOR_FIX_CONFIRMED.md: must exist + new status + run_id + historical run_ids preserved
    issues.extend(_check_file(
        VENDOR_CONFIRMED_FILE,
        [
            NEW_STATUS_TAG,
            RETEST_RUN_ID,
            OLD_FAILED_RUN_IDS[0],
            OLD_FAILED_RUN_IDS[1],
        ],
    ))

    # CASE_CLOSEOUT.md: must still preserve historical closeout status tags
    # + new status tag + new run_id
    must_contain_closeout = list(HISTORICAL_STATUS_TAGS) + [
        NEW_STATUS_TAG,
        RETEST_RUN_ID,
    ]
    issues.extend(_check_file(CASE_CLOSEOUT_FILE, must_contain_closeout))

    # CASTFORM_SUPPORT_REQUEST_FINAL.md: both old run_ids still present
    # (this doc is the original ATL-RESUME-1 short support request, intentionally
    # scoped to the historical failed runs; the new retest run_id is NOT expected here)
    issues.extend(_check_file(
        SUPPORT_REQUEST_FILE,
        [OLD_FAILED_RUN_IDS[0], OLD_FAILED_RUN_IDS[1]],
    ))

    # Resume-2C report: must mention new status tag + new run_id
    issues.extend(_check_file(
        RESUME2C_REPORT_FILE,
        [NEW_STATUS_TAG, RETEST_RUN_ID],
    ))

    # cases.json structural + field-level checks
    issues.extend(_check_cases_json())

    if issues:
        print("FAIL: validate_vendor_fix_confirmed")
        for line in issues:
            print(f"  - {line}")
        return 1

    print("PASS: validate_vendor_fix_confirmed")
    print(f"  - VENDOR_FIX_CONFIRMED.md exists and contains all required tokens")
    print(f"  - new status tag present in doc + cases.json: {NEW_STATUS_TAG}")
    print(f"  - retest run_id present: {RETEST_RUN_ID}")
    print(f"  - historical closeout status tags preserved in CASE_CLOSEOUT.md: {', '.join(HISTORICAL_STATUS_TAGS)}")
    print(f"  - both old run_ids preserved as audit trail: {OLD_FAILED_RUN_IDS[0]} + {OLD_FAILED_RUN_IDS[1]}")
    print(f"  - data/cases.json Castform case phase: {EXPECTED_CASE_PHASE}")
    print(f"  - data/cases.json Castform case status: {EXPECTED_CASE_STATUS}")
    print(f"  - data/cases.json Castform case final_status: {EXPECTED_CASE_FINAL_STATUS}")
    print(f"  - canonical_example and workflow_reference preserved")
    print(f"  - secret-pattern scan: clean ({len(SECRET_PATTERNS)} patterns, {len(SECRET_LITERALS)} literals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
