#!/usr/bin/env python3
"""
environment_stub.py — ATL-3B scaffold only
Do not launch cloud training from this file.
"""

# ATL-3B: benchmax imports cleanly (no real validate_env executed).
# This file is a placeholder for future ATL-3C/ATL-4 integration.
# Do not import benchmax here. Do not call any Castform cloud training
# functions (e.g. the three call sites listed in the safety contract).


def validate_environment_stub() -> dict:
    """
    Placeholder for Castform validate_env.
    Returns a dict indicating the stub status.
    """
    return {
        "status": "STUB",
        "benchmax_available": False,
        "reason": "benchmax blocked: Python 3.12 venv lacks pip",
        "note": "ATL-3A scaffold only. Replace with real validate_env in ATL-3B.",
    }


if __name__ == "__main__":
    result = validate_environment_stub()
    print(f"Status: {result['status']}")
    print(f"benchmax_available: {result['benchmax_available']}")
    print(f"Reason: {result['reason']}")
