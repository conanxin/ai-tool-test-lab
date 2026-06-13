#!/usr/bin/env python3
"""
ATL-4B-CONFIG: cloud_launch_guard.py

Hard guard against accidentally launching a Castform training run.

- Default behavior: REFUSE the launch, print the blocked banner, exit 1.
- Will refuse the launch even if CASTFORM_API_KEY happens to be set in
  the environment (defense in depth — presence of a key is not consent).
- Does not import upload_training_run, launch_training_run, or TrainerClient.
- Does not call any Castform API. No network. No upload. No training.
- Uses Python std-lib only.

The ONLY way to actually launch is for the user to explicitly flip
ALLOWED = True in a future phase (ATL-4D or later), AND to have the
pre-launch gates in README.md green.
"""

from __future__ import annotations

import os
import sys

# Hard guard: never import the real Castform training entry points.
# If the SDK is on PYTHONPATH later, these names must NOT resolve here.
try:
    import castform  # type: ignore  # noqa: F401
    _CASTFORM_SDK_PRESENT = True
except Exception:
    _CASTFORM_SDK_PRESENT = False

# These names must remain strings only — never import or call them.
FORBIDDEN_CALLABLES = (
    "upload_training_run",
    "launch_training_run",
    "TrainerClient",
)

ALLOWED = False  # ATL-4B-CONFIG default — DO NOT FLIP


def banner() -> None:
    print("ATL-4B-CONFIG dry configuration only")
    print("cloud_launch_allowed=false")
    print("BLOCKED_BY_UNCLEAR_CHARGES")
    print("no API call")
    print("no upload")
    print("no training")


def check_no_forbidden_symbols() -> None:
    """Belt-and-braces: make sure this file's own namespace is clean."""
    ns = set(globals().keys()) | set(locals().keys())
    for name in FORBIDDEN_CALLABLES:
        if name in ns:
            raise SystemExit(f"[FAIL] forbidden symbol leaked into guard: {name}")


def main() -> int:
    check_no_forbidden_symbols()

    print("[INFO] ATL-4B-CONFIG cloud_launch_guard.py")
    if _CASTFORM_SDK_PRESENT:
        print("[INFO] castform SDK detected on PYTHONPATH — guard still refuses to use it")

    if not ALLOWED:
        banner()
        key_present = "CASTFORM_API_KEY" in os.environ
        if key_present:
            print("[INFO] CASTFORM_API_KEY is set in the environment; guard still refuses launch")
        print("[GUARD] launch refused (ATL-4B-CONFIG default)")
        return 1

    # The branch below is intentionally unreachable in ATL-4B-CONFIG.
    # A future phase (ATL-4D, after explicit user authorization) may flip
    # ALLOWED = True and replace this body with the real launch call.
    print("[FAIL] ALLOWED=True reached but no launch path is wired in ATL-4B-CONFIG", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
