#!/usr/bin/env python3
"""
validate_atl3c_sdk_mapping.py — ATL-3C scaffolding check

Standard library only. Verifies:

  - ATL-3C scaffolding files exist
  - No real CASTFORM_API_KEY=... in those files
  - No obvious real token / secret / sk-... in those files
  - .venv-castform-local is NOT tracked by git
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SDK_DIR = (
    PROJECT_ROOT
    / "cases"
    / "castform-hermes-phase-closer-v0"
    / "local-validate-env"
    / "sdk-introspection"
)
LOCAL_ENV = PROJECT_ROOT / "cases" / "castform-hermes-phase-closer-v0" / "local-validate-env"

REQUIRED_FILES = [
    SDK_DIR / "inspect_benchmax_validate_env.py",
    SDK_DIR / "ATL3C_VALIDATE_ENV_API_NOTES.md",
    LOCAL_ENV / "environment_validate_candidate.py",
    LOCAL_ENV / "run_real_validate_env_attempt.py",
]

# Looser placeholder-aware secret patterns: require an actual non-placeholder value.
SECRET_PATTERNS = [
    (re.compile(r"CASTFORM_API_KEY\s*=\s*['\"]?[A-Za-z0-9_\-]{10,}"), "CASTFORM_API_KEY with real value"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI-style secret key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "GitHub personal access token"),
    (re.compile(r"\d{9,}:[A-Za-z0-9_\-]{20,}"), "Telegram bot token"),
]

# Lines containing any of these placeholder markers are ignored.
PLACEHOLDERS = (
    "<CASTFORM_API_KEY>",
    "<TOKEN_REDACTED>",
    "<API_KEY_REDACTED>",
    "<API_KEY>",
    "<TOKEN>",
    "<PLACEHOLDER>",
)


def _is_placeholder(line: str) -> bool:
    return any(p in line for p in PLACEHOLDERS)


def _scan(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for lineno, line in enumerate(text.splitlines(), 1):
        if _is_placeholder(line):
            continue
        for pat, desc in SECRET_PATTERNS:
            if pat.search(line):
                findings.append((lineno, desc, line.strip()[:200]))
                break
    return findings


def main() -> int:
    print("=== validate_atl3c_sdk_mapping.py ===")
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

    # 3. venv not tracked.
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=str(PROJECT_ROOT),
            stderr=subprocess.STDOUT,
        ).decode("utf-8", errors="ignore")
        tracked = [name for name in out.split("\x00") if name]
        bad = [
            t
            for t in tracked
            if ".venv-castform-local" in t
            or t.startswith(".venv/")
            or "/.venv/" in t
        ]
        if bad:
            errors.append(f"venv tracked by git: {bad}")
            print(f"  ✗ venv tracked: {bad}")
        else:
            print("  ✓ .venv-castform-local NOT tracked")
    except subprocess.CalledProcessError as e:
        errors.append(f"git ls-files failed: {e}")

    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\nFAIL ({len(errors)} errors)")
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
