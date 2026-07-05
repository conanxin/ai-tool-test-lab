#!/usr/bin/env python3
"""
browser_control_recovery_fixture.py — offline parser for browser-control
recovery fixture text (ATL-EVOMAP-6D).

Hard rules (enforced by tool design):
- Python stdlib only (argparse, json, re, sys, pathlib, os).
- Only accepts --input. Does not read .env, does not recurse the repo,
  does not contact any online service.
- Does NOT launch a real browser.
- Does NOT connect to 127.0.0.1:18791 or any browser-control port.
- Does NOT perform HTTP requests.
- Does NOT run curl / wget / any network tool.
- Does NOT modify any source file.
- Does NOT print the original unsafe line — only the error category
  (e.g. "unsafe_fixture" with a generic reason).
- Rejects input paths whose basename contains ".env" or "env.local"
  unless the basename also contains "fixture" or "sample" (escape hatch
  for legitimate offline fixtures whose path is intentionally labelled).
- Refuses to parse if the text contains any of:
    * OpenAI-style API key (sk-...)
    * GitHub PAT (ghp_..., github_pat_...)
    * Authorization header value
    * JWT (eyJ.eyJ.eyJ)
    * -----BEGIN ... PRIVATE KEY-----
    * 12+ digit pure-numeric value (heuristic for secret-like tokens;
      does not flag short numbers, line numbers, or test indices)

Output JSON (stdout) includes:
  ok, component, gateway_status_alive, gateway_port_present,
  browser_control_expected_port_present, browser_control_enabled,
  browser_instance_initial_idle, browser_instance_expected_on_demand,
  attempt_count, browser_control_failure,
  browser_control_port_unavailable, browser_control_auth_missing,
  browser_launch_timeout, browser_instance_not_running,
  navigation_timeout, screenshot_missing, page_snapshot_missing,
  fallback_bypass_attempted, fallback_allowed,
  terminal_page_evidence_missing, final_success_missing,
  failure_signatures[], recommended_check_order[], safety{...}
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. Input-path refusal (path-based safety)
# ---------------------------------------------------------------------------

def _refuse_input_path(p: Path) -> str:
    """Return empty string if path is OK, else a refusal reason string."""
    name = p.name.lower()
    basename = name  # already a single component
    if ".env" in basename or "env.local" in basename:
        if "fixture" in basename or "sample" in basename:
            return ""  # escape hatch
        return "refused_input_path"
    SECRET_FILENAME_HINTS = (
        "credential", "credentials", "secret", "secrets",
        "token", "tokens", "apikey", "api_key",
    )
    for hint in SECRET_FILENAME_HINTS:
        if hint in name and "fixture" not in name and "sample" not in name:
            return f"refused_input_path (basename contains {hint!r})"
    return ""


# ---------------------------------------------------------------------------
# 2. Text safety scanners (content-based safety)
# ---------------------------------------------------------------------------

RE_OPENAI = re.compile(r"\b(sk-[A-Za-z0-9]{16,}|sk_live_[A-Za-z0-9]{16,})\b")
RE_GH_PAT = re.compile(
    r"\b(ghp_[A-Za-z0-9]{16,}|gho_[A-Za-z0-9]{16,}|ghs_[A-Za-z0-9]{16,}"
    r"|ghr_[A-Za-z0-9]{16,}|ghu_[A-Za-z0-9]{16,}"
    r"|github_pat_[A-Za-z0-9_]{16,})\b"
)
RE_AUTH = re.compile(
    r"(?i)authorization\s*[:=]\s*(?:[A-Za-z0-9_\-\.=+]+\s+)?"
    r"[A-Za-z0-9_\-\.=+]{16,}"
)
RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
RE_PEM_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
RE_COOKIE = re.compile(r"(?i)\bcookie\s*[:=]\s*[A-Za-z0-9_\-\.=+]{16,}")
RE_LONG_DIGIT = re.compile(r"(?<![A-Za-z0-9_])\d{12,}(?![A-Za-z0-9_])")


def _scan_text_safety(text: str) -> str:
    """Return empty string if text is safe, else a generic refusal reason.
    The original text is NEVER echoed."""
    if RE_OPENAI.search(text):
        return "unsafe_fixture (openai-style api key)"
    if RE_GH_PAT.search(text):
        return "unsafe_fixture (github personal access token)"
    if RE_AUTH.search(text):
        return "unsafe_fixture (authorization header value)"
    if RE_JWT.search(text):
        return "unsafe_fixture (jwt token)"
    if RE_PEM_KEY.search(text):
        return "unsafe_fixture (private key block)"
    if RE_COOKIE.search(text):
        return "unsafe_fixture (cookie assignment)"
    if RE_LONG_DIGIT.search(text):
        return "unsafe_fixture (12+ digit pure-numeric value)"
    return ""


# ---------------------------------------------------------------------------
# 3. Fixture parsing (offline, no execution)
# ---------------------------------------------------------------------------

RECOMMENDED_CHECK_ORDER = [
    "verify browser-control feature is enabled before retrying",
    "verify browser-control endpoint is listening without printing credentials",
    "verify client-side auth token wiring without reading .env",
    "distinguish normal idle browser state from failed on-demand launch",
    "avoid curl/raw HTTP fallback for browser-control tasks",
    "capture screenshot or page snapshot before declaring success",
    "record terminal page evidence before marking done",
]


def _yn(text: str, token: str) -> bool:
    m = re.search(rf"(?im)^{re.escape(token)}\s*:\s*(true|false)\s*$", text)
    return (m.group(1).lower() == "true") if m else False


def _str(text: str, token: str) -> str:
    m = re.search(rf"(?im)^{re.escape(token)}\s*:\s*(.+?)\s*$", text)
    return m.group(1).strip() if m else ""


def _parse_fixture_text(text: str) -> dict:
    """Parse the offline fixture text. Pure parsing — no execution, no
    inference of private page content. Returns a dict of extracted fields."""

    # Component / scope
    component = _str(text, "COMPONENT") or "openclaw-browser-control"

    # Local context booleans
    gateway_status = _str(text, "gateway_status").lower()
    gateway_status_alive = gateway_status == "alive"
    gateway_port = _str(text, "gateway_port")
    gateway_port_present = bool(gateway_port)
    browser_control_expected_port = _str(text, "browser_control_expected_port")
    browser_control_expected_port_present = bool(
        browser_control_expected_port)
    browser_control_enabled = _yn(text, "browser_control_enabled")
    browser_instance_initial_idle = (
        _str(text, "browser_instance_initial_state").lower() == "idle"
    )
    browser_instance_expected_on_demand = (
        _str(text, "browser_instance_expected_behavior").lower()
        == "on-demand launch"
    )

    # Attempt count (count "attempt #N" blocks)
    attempt_count = len(re.findall(r"(?im)^attempt\s*#\d+", text))

    # Diagnosis flags
    browser_control_failure = _yn(text, "browser_control_failure")
    browser_control_port_unavailable = _yn(text, "browser_control_port_unavailable")
    browser_control_auth_missing = _yn(text, "browser_control_auth_missing")
    browser_launch_timeout = _yn(text, "browser_launch_timeout")
    browser_instance_not_running = _yn(text, "browser_instance_not_running")
    navigation_timeout = _yn(text, "navigation_timeout")
    screenshot_missing = _yn(text, "screenshot_missing")
    fallback_bypass_attempted = _yn(text, "fallback_bypass_attempted")
    terminal_page_evidence_missing = _yn(text, "terminal_page_evidence_missing")
    final_success_missing = _yn(text, "final_success_missing")

    # page_snapshot_missing: infer if "page snapshot missing" appears in
    # text (lowercase substring)
    page_snapshot_missing = bool(
        re.search(r"(?im)page\s+snapshot\s+missing", text))

    # fallback_allowed is False when fallback_bypass_attempted is True
    # (any bypass attempt is unsafe by default).
    fallback_allowed = (not fallback_bypass_attempted)

    # Failure signatures (preserve order, dedup)
    failure_signatures: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"(?im)^failure_signature\s*:\s*(.+?)\s*$", text):
        s = m.group(1).strip()
        if s and s not in seen:
            seen.add(s)
            failure_signatures.append(s)

    return {
        "component": component,
        "gateway_status_alive": gateway_status_alive,
        "gateway_port_present": gateway_port_present,
        "browser_control_expected_port_present": (
            browser_control_expected_port_present
        ),
        "browser_control_enabled": browser_control_enabled,
        "browser_instance_initial_idle": browser_instance_initial_idle,
        "browser_instance_expected_on_demand": (
            browser_instance_expected_on_demand
        ),
        "attempt_count": attempt_count,
        "browser_control_failure": browser_control_failure,
        "browser_control_port_unavailable": browser_control_port_unavailable,
        "browser_control_auth_missing": browser_control_auth_missing,
        "browser_launch_timeout": browser_launch_timeout,
        "browser_instance_not_running": browser_instance_not_running,
        "navigation_timeout": navigation_timeout,
        "screenshot_missing": screenshot_missing,
        "page_snapshot_missing": page_snapshot_missing,
        "fallback_bypass_attempted": fallback_bypass_attempted,
        "fallback_allowed": fallback_allowed,
        "terminal_page_evidence_missing": terminal_page_evidence_missing,
        "final_success_missing": final_success_missing,
        "failure_signatures": failure_signatures,
        "recommended_check_order": list(RECOMMENDED_CHECK_ORDER),
    }


# ---------------------------------------------------------------------------
# 4. Main
# ---------------------------------------------------------------------------

def _build_safety_block() -> dict:
    return {
        "no_real_browser_launch": True,
        "no_port_connection": True,
        "no_http_request": True,
        "no_curl_wget": True,
        "no_env_scan": True,
        "no_secret_echo": True,
        "fixture_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline browser-control recovery fixture parser "
                    "(ATL-EVOMAP-6D, stdlib only, no browser, no network).",
    )
    parser.add_argument("--input", required=True,
                        help="Path to the offline fixture text file.")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()

    # 1. Path refusal
    refusal = _refuse_input_path(input_path)
    if refusal:
        out = {
            "ok": False,
            "reason": refusal,
            "input_basename": input_path.name,
            "safety": _build_safety_block(),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    if not input_path.is_file():
        out = {
            "ok": False,
            "reason": f"input file not found: {input_path}",
            "safety": _build_safety_block(),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    try:
        text = input_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        out = {
            "ok": False,
            "reason": f"cannot read input: {exc}",
            "safety": _build_safety_block(),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    # 2. Text safety
    safety_refusal = _scan_text_safety(text)
    if safety_refusal:
        out = {
            "ok": False,
            "reason": safety_refusal,
            "safety": _build_safety_block(),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    # 3. Parse
    parsed = _parse_fixture_text(text)

    out = {
        "ok": True,
        **parsed,
        "safety": _build_safety_block(),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())