#!/usr/bin/env python3
"""
run_validate_env_stub.py — historical ATL-3B stub.

This file is kept only as a historical marker for the ATL-3B milestone.
In ATL-3C we have a real local validate_env attempt; defer to that script:

    cases/castform-hermes-phase-closer-v0/local-validate-env/run_real_validate_env_attempt.py

This stub MUST NOT claim a real validate_env has succeeded.
"""

from __future__ import annotations

import importlib
import sys


def _try_import_benchmax():
    try:
        m = importlib.import_module("benchmax")
        return True, m
    except Exception as e:  # pragma: no cover - explicit error reporting
        return False, e


def main() -> int:
    available, mod_or_err = _try_import_benchmax()

    print("=== run_validate_env_stub.py (historical, ATL-3B) ===")
    print("NOTE: ATL-3B reached benchmax import only.")
    print("NOTE: ATL-3C uses run_real_validate_env_attempt.py for the real local attempt.")
    print("no Castform API call intended")
    print("no upload intended")
    print("no training intended")

    if not available:
        print("benchmax: unavailable")
        print(f"benchmax import error: {mod_or_err!r}")
        print("STATUS: SKIPPED_WITH_REASON")
        return 0

    m = mod_or_err
    print("benchmax: available (import only)")
    print(f"benchmax file: {getattr(m, '__file__', '')}")
    print("STATUS: HISTORICAL_ATL3B_STUB_ONLY — defer to run_real_validate_env_attempt.py")
    print("NO_VALIDATE_ENV_LOCAL_PASS_FROM_THIS_STUB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
