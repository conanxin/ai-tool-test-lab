#!/usr/bin/env python3
"""
ATL-4C: guarded_launch_preflight.py

Guarded launch preflight for Castform cloud smoke run.

- Default behavior: REFUSE the launch, print the blocked banner, exit 1.
- Requires three environment variables to be set before it would even consider
  proceeding (but still refuses in ATL-4C because
  actual_launch_allowed_in_this_phase = false).
- Does not import or call launch_training_run.
- Does not import or call TrainerClient.
- Does not call any Castform API. No network. No upload. No training.
- Uses Python std-lib only.

The ONLY way to actually launch is for the user to explicitly satisfy ALL
pre-launch gates in FINAL_LAUNCH_GATE.md AND flip
actual_launch_allowed_in_this_phase to true in a future phase (ATL-5).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "guarded_cloud_preflight_config.json"

# These names must remain strings only — never import or call them.
FORBIDDEN_CALLABLES = (
    "upload_training_run",
    "launch_training_run",
    "TrainerClient",
)

REQUIRED_ENV_VARS = {
    "CASTFORM_API_KEY": "real API key (injected via read -s + export)",
    "ATL_ALLOW_CASTFORM_UPLOAD": '"YES"',
    "ATL_ALLOW_CASTFORM_LAUNCH": '"YES"',
}


def banner() -> None:
    print("ATL-4C guarded launch preflight")
    print("actual_launch_allowed_in_this_phase=false")
    print("BLOCKED_BY_UNCLEAR_CHARGES")
    print("no API call")
    print("no upload")
    print("no training")


def check_no_forbidden_symbols() -> None:
    ns = set(globals().keys()) | set(locals().keys())
    for name in FORBIDDEN_CALLABLES:
        if name in ns:
            raise SystemExit(f"[FAIL] forbidden symbol leaked into guard: {name}")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"[FAIL] missing config: {CONFIG_PATH}")
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[FAIL] invalid JSON in config: {exc}")


def check_env_vars() -> tuple[dict[str, str], list[str]]:
    missing: list[str] = []
    env: dict[str, str] = {}
    for var, desc in REQUIRED_ENV_VARS.items():
        val = os.environ.get(var, "").strip()
        if not val:
            missing.append(f"{var} ({desc})")
        else:
            env[var] = val
    return env, missing


def mask_key(val: str) -> str:
    if len(val) <= 8:
        return "***"
    return val[:4] + "..."


def main() -> int:
    check_no_forbidden_symbols()

    print("[INFO] ATL-4C guarded_launch_preflight.py")
    cfg = load_config()

    # Config-level gate
    if cfg.get("actual_launch_allowed_in_this_phase") is not True:
        print("[GUARD] actual_launch_allowed_in_this_phase is false (ATL-4C default)")
    else:
        print("[INFO] actual_launch_allowed_in_this_phase is true")

    if cfg.get("cloud_launch_allowed") is not False:
        print(f"[WARN] cloud_launch_allowed is {cfg.get('cloud_launch_allowed')!r} (expected false in ATL-4C)")
    else:
        print("[OK]   cloud_launch_allowed == false")

    if cfg.get("current_readiness") != "BLOCKED_BY_UNCLEAR_CHARGES":
        print(f"[WARN] current_readiness is {cfg.get('current_readiness')!r} (expected BLOCKED_BY_UNCLEAR_CHARGES in ATL-4C)")
    else:
        print("[OK]   current_readiness == BLOCKED_BY_UNCLEAR_CHARGES")

    # Environment variable gate
    env, missing = check_env_vars()
    if missing:
        print("[GUARD] missing required environment variables:")
        for m in missing:
            print(f"  - {m}")
    else:
        print("[OK]   all required environment variables present")
        key = env.get("CASTFORM_API_KEY", "")
        if key:
            print(f"[INFO] CASTFORM_API_KEY detected: {mask_key(key)}")

    # Final decision: refuse in ATL-4C
    if cfg.get("actual_launch_allowed_in_this_phase") is not True:
        banner()
        print("[GUARD] launch refused (ATL-4C default — actual_launch_allowed_in_this_phase=false)")
        return 1

    # The branch below is intentionally unreachable in ATL-4C.
    # A future phase (ATL-5, after explicit user authorization) may flip
    # actual_launch_allowed_in_this_phase to true.
    print("[FAIL] actual_launch_allowed_in_this_phase=true reached but no launch path is wired in ATL-4C", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
