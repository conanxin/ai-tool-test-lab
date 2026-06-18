#!/usr/bin/env python3
"""
hermes_systemd_recovery_fixture.py

Offline parser for Hermes systemd user-service failure fixtures.

Hard constraints (enforced by tool design, not just careful usage):
  - Python stdlib only (argparse, json, re, sys, pathlib)
  - Accepts ONLY --input <path>; nothing else
  - NEVER reads .env files
  - NEVER recursively scans the repo
  - NEVER executes systemctl / journalctl / ss / curl / python imports from text
  - NEVER prints or persists API key / token / cookie / Authorization content
  - NEVER modifies OpenClaw / Hermes / systemd / cron configuration
  - ONLY parses the supplied fixture text and emits a deterministic JSON summary

The parser is intentionally lossy: it only recognizes text shapes that match
the offline Hermes systemd failure model. Anything unrecognized is logged as
`unrecognized_signals` for downstream review (but never raises).

Usage:
  python3 scripts/hermes_systemd_recovery_fixture.py \
      --input cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/fixtures/hermes-systemd-failure-sample.txt
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Recommended, deterministic, ordered check sequence for this failure model.
# This is what the Gene strategy will reference, but the parser only emits it.
RECOMMENDED_CHECK_ORDER = [
    "systemctl --user status hermes-gateway.service",
    "journalctl --user -u hermes-gateway.service --since today",
    "systemctl --user show-environment",
    "check service drop-in Environment lines",
    "check expected port 127.0.0.1:18789",
    "run Telegram smoke test",
]


def _parse(text: str) -> dict:
    """Pure-function parser. No I/O beyond the caller-supplied string."""
    out = {
        "ok": True,
        "service": None,
        "service_failed": False,
        "missing_env_var": None,
        "expected_port": None,
        "port_not_listening": False,
        "telegram_smoke_missing": False,
        "main_process_status": None,
        "restart_counter_at": None,
        "restart_limit_hit": False,
        "dropin_env_lines_present": False,
        "dropin_points_to_missing_env": False,
        "unrecognized_signals": [],
        "recommended_check_order": list(RECOMMENDED_CHECK_ORDER),
        "safety": {
            "no_real_systemctl": True,
            "no_real_journalctl": True,
            "no_env_scan": True,
            "no_secrets": True,
            "no_network_call": True,
            "no_repo_scan": True,
        },
    }

    # Service identity
    m = re.search(r"^Service:\s*(\S+)", text, re.MULTILINE)
    if m:
        out["service"] = m.group(1).strip()

    # Failed status
    if re.search(r"Active:\s*failed", text):
        out["service_failed"] = True
    if re.search(r"code=exited,?\s*status=\d+/[A-Z]+", text):
        mm = re.search(r"code=exited,?\s*status=(\d+/[A-Z]+)", text)
        if mm:
            out["main_process_status"] = mm.group(1)

    # Restart limit hit
    if re.search(r"start-limit-hit", text, re.IGNORECASE):
        out["restart_limit_hit"] = True
    mm = re.search(r"restart counter is at\s*(\d+)", text)
    if mm:
        try:
            out["restart_counter_at"] = int(mm.group(1))
        except ValueError:
            out["restart_counter_at"] = None

    # Missing env var — priority order:
    #   1. vars reported as "is unset" (direct)
    #   2. vars reported as "missing" with no surrounding path-like context
    #   3. vars "referenced" + the env-file path is missing (note in dropin flag instead)
    env_var = None
    unset_iter = list(re.finditer(
        r"[ \t]*([A-Z][A-Z0-9_]{2,})\s+is unset",
        text, re.IGNORECASE,
    ))
    if unset_iter:
        env_var = unset_iter[0].group(1).strip()
    else:
        # Fallback: any bare "missing <ENV>" token (not preceded by a path)
        for mm in re.finditer(r"(?:^|\s)missing\s+([A-Z][A-Z0-9_]{2,})", text, re.MULTILINE):
            candidate = mm.group(1).strip()
            # Heuristic: skip if the surrounding text mentions a file path
            ctx = text[max(0, mm.start() - 60):mm.end() + 60]
            if "/" in ctx.split(candidate)[-1]:
                continue
            env_var = candidate
            break
    out["missing_env_var"] = env_var

    # Drop-in env lines
    if re.search(r"hermes-gateway\.service\.d/env\.conf", text):
        out["dropin_env_lines_present"] = True
    if re.search(r"drop-in.*?missing", text, re.IGNORECASE | re.DOTALL) or \
       re.search(r"Environment=.*?missing\s+/home", text, re.IGNORECASE | re.DOTALL):
        out["dropin_points_to_missing_env"] = True

    # Expected port
    mm = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})", text)
    if mm:
        out["expected_port"] = f"{mm.group(1)}:{mm.group(2)}"
    if re.search(r"Port\s+\d+\s+is not listening", text, re.IGNORECASE) or \
       re.search(r"LISTEN line for .* is missing", text):
        out["port_not_listening"] = True

    # Telegram smoke
    if re.search(r"Telegram smoke test .* was not sent", text, re.IGNORECASE) or \
       re.search(r"Telegram smoke .* missing", text, re.IGNORECASE):
        out["telegram_smoke_missing"] = True

    # Recognize anything weird so reviewers can spot drift
    known_markers = (
        "Active:",
        "code=exited",
        "start-limit-hit",
        "restart counter is at",
        "is unset",
        "missing",
        "drop-in",
        "Environment=",
        "LISTEN",
        "not listening",
        "Telegram smoke",
    )
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(mk in s for mk in known_markers):
            continue
        # token-ish lines we don't know about
        if re.match(r"^[A-Za-z][A-Za-z0-9 _:\-/.,()=]{6,}$", s) and \
           not re.match(r"^[A-Z][a-z]+:", s):  # skip section headings
            out["unrecognized_signals"].append(s[:160])

    # Dedupe unrecognized signals (cap at 50)
    seen = set()
    deduped = []
    for s in out["unrecognized_signals"]:
        if s in seen:
            continue
        seen.add(s)
        deduped.append(s)
        if len(deduped) >= 50:
            break
    out["unrecognized_signals"] = deduped

    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline parser for Hermes systemd failure fixtures (stdlib only, no systemctl, no env scan, no secrets)."
    )
    parser.add_argument("--input", type=Path, required=True,
                        help="Path to a fixture .txt file (NOT a .env, NOT a directory).")
    args = parser.parse_args()

    if not args.input.is_file():
        print(json.dumps({
            "ok": False,
            "reason": f"input is not a regular file: {args.input}",
            "safety": {"no_real_systemctl": True, "no_real_journalctl": True,
                       "no_env_scan": True, "no_secrets": True, "no_network_call": True,
                       "no_repo_scan": True},
        }, indent=2, ensure_ascii=False))
        return 1

    # Hard refusal: refuse .env or anything that looks like a secret-bearing path
    name_lower = args.input.name.lower()
    if name_lower == ".env" or name_lower.endswith(".env") or "/.env/" in str(args.input):
        print(json.dumps({
            "ok": False,
            "reason": "refusing to parse .env-shaped path",
            "safety": {"no_real_systemctl": True, "no_real_journalctl": True,
                       "no_env_scan": True, "no_secrets": True, "no_network_call": True,
                       "no_repo_scan": True},
        }, indent=2, ensure_ascii=False))
        return 1

    try:
        text = args.input.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = args.input.read_text(encoding="utf-8", errors="replace")

    parsed = _parse(text)
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())