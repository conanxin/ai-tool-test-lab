#!/usr/bin/env python3
"""
run_validate_env_stub.py — validate_env stub (ATL-3B).

Three explicit, non-deceptive states:

  SKIPPED_WITH_REASON               — benchmax unavailable
  BENCHMAX_IMPORT_PASS_VALIDATE_ENV_NOT_RUN  — benchmax imports, but no real validate_env was executed
  VALIDATE_ENV_LOCAL_PASS           — only if a true local validate_env runs without API key / upload / training

This stage (ATL-3B) targets the second state only. It MUST NOT fabricate cloud
or validate_env success.
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

    if not available:
        print("benchmax: unavailable")
        print(f"benchmax import error: {mod_or_err!r}")
        print()
        print("STATUS: SKIPPED_WITH_REASON")
        print("REASON: benchmax unavailable — Python 3.12 venv pip still missing or install incomplete")
        print("NO_CASTFORM_API_CALL")
        print("NO_UPLOAD")
        print("NO_TRAINING")
        print("NO_VALIDATE_ENV_LOCAL_PASS")
        return 0

    m = mod_or_err
    print("benchmax: available")
    print(f"benchmax module: {m}")
    print(f"benchmax file: {getattr(m, '__file__', '')}")
    print(f"benchmax version: {getattr(m, '__version__', '')}")
    print()
    print("STATUS: BENCHMAX_IMPORT_PASS_VALIDATE_ENV_NOT_RUN")
    print("REASON: benchmax imports cleanly, but this stub did NOT execute a real validate_env")
    print("        (no API call, no upload, no training, no API key required).")
    print("        A true local validate_env will be attempted in ATL-3C by mapping the official API.")
    print("NO_CASTFORM_API_CALL")
    print("NO_UPLOAD")
    print("NO_TRAINING")
    print("NO_VALIDATE_ENV_LOCAL_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
