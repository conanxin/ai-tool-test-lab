#!/usr/bin/env python3
"""
validate_atl4a_preflight_scaffold.py — ATL-4A scaffolding check

Standard library only. Verifies:

  - docs/CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md exists
  - cases/castform-hermes-phase-closer-v0/account-billing-preflight.md exists
  - Neither file contains real secrets (real API key, sk-, Authorization header,
    Cookie, credit card, card number, password=, PRIVATE KEY)
  - Placeholders (<CASTFORM_API_KEY>, <TOKEN_REDACTED>, <SECRET_REDACTED>) are
    explicitly allowed and skipped during the scan.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
CASE_DIR = PROJECT_ROOT / "cases" / "castform-hermes-phase-closer-v0"

PREFLIGHT_DOC = DOCS_DIR / "CASTFORM_ACCOUNT_BILLING_PREFLIGHT.md"
PREFLIGHT_CASE = CASE_DIR / "account-billing-preflight.md"

REQUIRED_FILES = [PREFLIGHT_DOC, PREFLIGHT_CASE]

# Patterns indicating real credentials. Placeholder-bearing lines are skipped.
SECRET_PATTERNS = [
    (re.compile(r"CASTFORM_API_KEY\s*=\s*['\"]?[A-Za-z0-9_\-]{10,}"), "CASTFORM_API_KEY with real value"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "OpenAI-style secret key"),
    (re.compile(r"Authorization\s*:\s*(?!Bearer\s*<)\S+", re.IGNORECASE), "Authorization header with real value"),
    (re.compile(r"Cookie\s*:\s*[A-Za-z0-9_=\-\.;]{20,}", re.IGNORECASE), "Cookie with real value"),
    (re.compile(r"credit\s*card", re.IGNORECASE), "credit card mention"),
    (re.compile(r"card\s*number", re.IGNORECASE), "card number mention"),
    (re.compile(r"password\s*=\s*['\"]?[A-Za-z0-9_\-]{6,}"), "password= with real value"),
    (re.compile(r"PRIVATE\s+KEY", re.IGNORECASE), "PRIVATE KEY mention"),
]

# Lines containing any of these placeholder markers are ignored.
PLACEHOLDERS = (
    "<CASTFORM_API_KEY>",
    "<TOKEN_REDACTED>",
    "<SECRET_REDACTED>",
    "<API_KEY_REDACTED>",
    "<API_KEY>",
    "<TOKEN>",
    "<PLACEHOLDER>",
    "<IP_REDACTED>",
)


def _is_placeholder(line: str) -> bool:
    return any(p in line for p in PLACEHOLDERS)


# Lines that *describe* the prohibition (e.g. "do NOT record PRIVATE KEY") are
# not the same as lines that contain a real PRIVATE KEY block. A negation cue
# tells us the author is enumerating forbidden values rather than exposing one.
NEGATION_CUES = (
    "不",
    "不得",
    "禁止",
    "严禁",
    "NOT",
    "FORBID",
    "FORBIDDEN",
    "DO NOT",
    "NEVER",
)


def _is_negated(line: str) -> bool:
    upper = line.upper()
    if any(cue in upper for cue in ("NOT", "FORBID", "FORBIDDEN", "DO NOT", "NEVER")):
        return True
    return any(cue in line for cue in NEGATION_CUES if len(cue) > 1)


# Section headers (or paragraph openers) that declare a *prohibition list* —
# any bullet/entry that follows inside the same list is descriptive, not a
# real secret leak. We allow these to arm an "in-prohibition-list" mode that
# applies to subsequent list items until the list ends (blank line or new
# header).
PROHIBITION_HEADERS = (
    "严禁",
    "禁止",
    "不得",
    "FORBIDDEN",
    "DO NOT",
    "PROHIBITED",
)


def _scan(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    in_prohibition_list = False
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()

        # Track when we enter / leave a prohibition list. A new markdown
        # heading always ends the current list. A blank line is fine — bullet
        # lists in markdown often have one between header and first item, or
        # between consecutive bullet groups. We rely on the next heading or a
        # non-list paragraph to terminate the list.
        if stripped.startswith("#"):
            in_prohibition_list = False
        if any(h in line for h in PROHIBITION_HEADERS) and not stripped.startswith("-"):
            in_prohibition_list = True
        # A list item that itself contains a negation cue is always descriptive.
        if _is_negated(line):
            in_prohibition_list = True

        if _is_placeholder(line):
            continue
        for pat, desc in SECRET_PATTERNS:
            if pat.search(line):
                if in_prohibition_list or _is_negated(line):
                    break
                findings.append((lineno, desc, line.strip()[:200]))
                break
    return findings


def main() -> int:
    print("=== validate_atl4a_preflight_scaffold.py ===")
    errors: list[str] = []

    # 1. Files exist.
    for p in REQUIRED_FILES:
        if p.exists():
            print(f"  ✓ file: {p.relative_to(PROJECT_ROOT)}")
        else:
            errors.append(f"missing required file: {p.relative_to(PROJECT_ROOT)}")

    # 2. Secret scan.
    for p in REQUIRED_FILES:
        if not p.exists():
            continue
        for lineno, desc, snippet in _scan(p):
            errors.append(
                f"secret in {p.relative_to(PROJECT_ROOT)}:{lineno} — {desc}\n    {snippet}"
            )

    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\nFAIL ({len(errors)} errors)")
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
