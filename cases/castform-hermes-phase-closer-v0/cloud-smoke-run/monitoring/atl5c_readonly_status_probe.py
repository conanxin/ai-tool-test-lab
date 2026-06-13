#!/usr/bin/env python3
"""
ATL-5C: atl5c_readonly_status_probe.py

Read-only Castform status probe for the first failed training run.

Usage (USER runs locally in WSL with CASTFORM_API_KEY; agent does NOT run):

    export CASTFORM_API_KEY=...     # runtime only, do NOT write to .env
    .venv-castform-local/bin/python \\
        cases/castform-hermes-phase-closer-v0/cloud-smoke-run/monitoring/atl5c_readonly_status_probe.py \\
        --run-id c83f971d-2b2c-42b8-9774-ca64938c1286

This script:
  - introspects benchmax.platform.client.TrainerClient for candidate
    read-only methods (get_* / list_* / read_* / describe_* / status_* / fetch_*)
  - REFUSES to call any destructive method (no delete_*, cancel_*,
    update_*, create_*, upload_*, launch_*, download_*, train_*, run_*,
    submit_*, post_*, put_*, patch_*, kill_*)
  - does NOT call upload_training_run
  - does NOT call launch_training_run
  - does NOT call delete / cancel / update / create / download
  - prints NO API key value, prefix, or fragment
  - if a candidate method returns data, prints the sanitized result
  - if no candidate method exists, prints NO_READ_ONLY_STATUS_METHOD_FOUND
  - exits 0 either way (the user reads stdout; exit code is for pipeline use)

This is a SCREENING probe. The point is to find any backend-visible
traceback or root-cause hint without firing any mutating API call. If
the probe surfaces a clear failure, branch to ATL-5D (failure root cause
record). If no read-only method exists, branch to ATL-5E (support-ready
failure bundle).

Hard rules:
  - Agent does NOT run this script during ATL-5C.
  - User runs it manually with their own API key.
  - No API key value / prefix / fragment is ever printed to stdout or
    persisted to disk.
  - No call to upload_training_run, launch_training_run, or any
    destructive verb.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import sys
from typing import Iterable

# ----------------------------------------------------------------------
# Read-only / destructive verb whitelists
# ----------------------------------------------------------------------

# Method-name prefixes that strongly suggest a read-only status query.
# These are the prefixes we will TRY to call (if present in the client).
READ_ONLY_PREFIXES = (
    "get_",
    "list_",
    "read_",
    "describe_",
    "status_",
    "fetch_",
    "inspect_",
    "summary_",
)

# Method-name prefixes/keywords that suggest a mutating call.
# If ANY of these appear in a method name, we refuse to call it,
# even if it also looks read-only. This is a safety net.
DESTRUCTIVE_KEYWORDS = (
    "delete",
    "cancel",
    "kill",
    "stop",
    "update",
    "patch",
    "create",
    "submit",
    "post",
    "put",
    "upload",
    "launch",
    "train",
    "download",
    "import",
    "export",
    "run_",
    "rerun",
    "retry",
    "reset",
    "clear",
    "purge",
    "wipe",
    "destroy",
    "approve",
    "reject",
    "transfer",
    "share",
    "publish",
    "deploy",
    "release",
    "merge",
    "fork",
)


def _is_read_only_name(name: str) -> bool:
    """Return True if `name` matches a read-only prefix and does not
    contain any destructive keyword.
    """
    if name.startswith("_"):
        return False
    if not any(name.startswith(p) for p in READ_ONLY_PREFIXES):
        return False
    lower = name.lower()
    for kw in DESTRUCTIVE_KEYWORDS:
        if kw in lower:
            return False
    return True


# ----------------------------------------------------------------------
# Output sanitization
# ----------------------------------------------------------------------

SECRET_PATTERNS = [
    re.compile(r"cf-[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Authorization:\s*[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Cookie:\s*[A-Za-z0-9_\-]{20,}"),
]

# Sentinel to replace any caught secret-shaped substring. We do NOT echo
# a 4-char prefix or any fragment — the whole substring is replaced.
REDACTION = "<SECRET_REDACTED>"


def _scrub(text: str) -> str:
    """Return `text` with every secret-shaped pattern replaced by
    REDACTION. Never echoes a prefix or fragment.
    """
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub(REDACTION, out)
    return out


# ----------------------------------------------------------------------
# TrainerClient introspection
# ----------------------------------------------------------------------

CLIENT_PATH = "benchmax.platform.client.TrainerClient"


def _import_trainer_client():
    """Import the TrainerClient class. Returns (class, error_str).
    error_str is empty on success.
    """
    try:
        from benchmax.platform.client import TrainerClient  # type: ignore
    except Exception as exc:
        return None, f"import failed: {type(exc).__name__}: {exc}"
    return TrainerClient, ""


def _candidate_methods(client_cls) -> list[str]:
    """Return sorted list of method names on `client_cls` that match the
    read-only filter.
    """
    out: list[str] = []
    for name, _member in inspect.getmembers(client_cls, predicate=inspect.isfunction):
        if _is_read_only_name(name):
            out.append(name)
    # Also include methods that are defined directly on the class
    # (inspect.getmembers only returns functions, but TrainerClient may
    # expose its API as regular methods; both work).
    for name in dir(client_cls):
        if name.startswith("_"):
            continue
        attr = getattr(client_cls, name, None)
        if attr is None:
            continue
        if not callable(attr):
            continue
        if _is_read_only_name(name) and name not in out:
            out.append(name)
    return sorted(set(out))


# ----------------------------------------------------------------------
# Probe execution
# ----------------------------------------------------------------------

def _try_call(client_obj, method_name: str, run_id: str) -> tuple[bool, str]:
    """Try to call `client_obj.method_name(run_id=run_id)`. On any
    exception, return (False, sanitized error string). On success, return
    (True, sanitized repr of result).
    """
    method = getattr(client_obj, method_name, None)
    if method is None or not callable(method):
        return False, "method not found on instance"
    try:
        result = method(run_id=run_id)
    except TypeError:
        # Method signature may not accept run_id=...; try positional.
        try:
            result = method(run_id)
        except Exception as exc:
            return False, _scrub(f"{type(exc).__name__}: {exc}")
    except Exception as exc:
        return False, _scrub(f"{type(exc).__name__}: {exc}")
    try:
        rendered = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    except Exception:
        rendered = repr(result)
    return True, _scrub(rendered)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Castform status probe (ATL-5C)."
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Castform run_id (UUID form) to probe",
    )
    args = parser.parse_args(argv)

    run_id = args.run_id.strip()
    if not run_id:
        print("FAIL: --run-id is empty", file=sys.stderr)
        return 1

    # API key presence check (boolean only; never echo any part of the key).
    api_key_present = bool(os.environ.get("CASTFORM_API_KEY", "").strip())
    print(f"CASTFORM_API_KEY present: {api_key_present}")

    # Introspect TrainerClient.
    client_cls, err = _import_trainer_client()
    if err:
        print(f"PROBE_IMPORT_ERROR: {_scrub(err)}")
        return 0
    print(f"PROBE_CLIENT_OK: {CLIENT_PATH}")

    candidates = _candidate_methods(client_cls)
    if not candidates:
        print("NO_READ_ONLY_STATUS_METHOD_FOUND")
        return 0

    print(f"PROBE_CANDIDATES: {candidates}")
    if not api_key_present:
        # Without a key, the SDK can't call any backend endpoint anyway.
        # We still list the candidate method names so the user knows what
        # WOULD be called if they ran the script with their key.
        print("PROBE_SKIPPED_CALLS: CASTFORM_API_KEY not set; candidate list shown above.")
        print("NO_READ_ONLY_STATUS_METHOD_FOUND")
        return 0

    # We have a key and at least one candidate. Try each, sanitized.
    api_key = os.environ["CASTFORM_API_KEY"]  # used only to construct the client
    try:
        client_obj = client_cls(api_key=api_key)
    except Exception as exc:
        print(f"PROBE_CONSTRUCT_ERROR: {_scrub(f'{type(exc).__name__}: {exc}')}")
        return 0

    for name in candidates:
        print(f"--- {name} ---")
        ok, body = _try_call(client_obj, name, run_id)
        if ok:
            print("STATUS: ok")
            print(body)
        else:
            print(f"STATUS: error")
            print(body)

    print("PROBE_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())