#!/usr/bin/env python3
"""
codex_test_failure_loop_fixture.py — offline parser for Codex / AI coding
test-failure-loop fixture text.

Hard rules (enforced by tool design):
- Python stdlib only (argparse, json, re, sys, pathlib, os).
- Only accepts --input. Does not read .env, does not recurse the repo,
  does not contact any online service.
- Does NOT execute real test commands.
- Does NOT modify any source file.
- Does NOT call OpenAI / Codex / GitHub Copilot / any online coding API.
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
    * 12+ digit pure-numeric value (heuristic for secret-like tokens /
      recipient ids; does not flag short numbers, line numbers, or test
      indices)
  Parser output does NOT echo the original unsafe line — only the
  error category.

Output JSON (stdout) includes:
  ok, component, agent_mode, code_change_attempted, test_command_present,
  tests_failed, repeated_failure_count, same_failure_signature_repeated,
  failing_assertion_detected, regression_introduced,
  fix_one_break_another, failure_cluster_missing,
  prompt_context_stale_suspected, final_green_test_missing,
  terminal_green_test_missing,
  failing_tests[], failure_signatures[],
  recommended_check_order[],
  safety{...}
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ----- 1. Input path refusal (path-based safety) -----

def _refuse_input_path(p: Path) -> str:
    """Return empty string if path is OK, else a refusal reason string."""
    name = p.name.lower()
    basename = name  # already a single component
    # Hard refusal: anything whose basename contains ".env" (as substring,
    # e.g. ".env", ".env.production", "codex.env.local") or "env.local"
    # unless the basename also contains "fixture" or "sample" (escape
    # hatch for legitimate offline fixtures whose path is intentionally
    # labelled).
    if ".env" in basename or "env.local" in basename:
        if "fixture" in basename or "sample" in basename:
            return ""  # escape hatch
        return "refused_input_path"
    # Generic refusal: secret-like filenames
    SECRET_FILENAME_HINTS = ("credential", "credentials", "secret", "secrets", "token", "tokens", "apikey", "api_key")
    for hint in SECRET_FILENAME_HINTS:
        if hint in name and "fixture" not in name and "sample" not in name:
            return f"refused_input_path (basename contains {hint!r})"
    return ""


# ----- 2. Text safety scanners (content-based safety) -----

# These patterns are designed to be precise (no false positives on test
# names, short numbers, line numbers, or file paths).
# They ONLY flag values that are unambiguous credential / token shapes.

# OpenAI / OpenAI-style: sk- + >=16 alnum; or sk_live_<...>
RE_OPENAI = re.compile(r"\b(sk-[A-Za-z0-9]{16,}|sk_live_[A-Za-z0-9]{16,})\b")

# GitHub PAT: ghp_/gho_/ghs_/ghr_/ghu_ + 16+ alnum; or github_pat_xxx_yyy
RE_GH_PAT = re.compile(r"\b(ghp_[A-Za-z0-9]{16,}|gho_[A-Za-z0-9]{16,}|ghs_[A-Za-z0-9]{16,}|ghr_[A-Za-z0-9]{16,}|ghu_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,})\b")

# Authorization header value
RE_AUTH = re.compile(r"(?i)authorization\s*[:=]\s*[A-Za-z0-9_\-\.=+]{16,}")

# JWT: eyJ + base64url(.eyJ...) (3 segments)
RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")

# PEM private key
RE_PEM_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")

# 12+ digit pure-numeric value. We require word boundaries and at least
# 12 digits (not 6 or 11, so test indices like "test_3" or short
# timestamps like "1234567890" are NOT flagged).
# The 12-digit minimum is intentional and matches the spec.
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
    if RE_LONG_DIGIT.search(text):
        return "unsafe_fixture (12+ digit pure-numeric value)"
    return ""


# ----- 3. Fixture parsing (offline, no execution) -----

# Recommended order is fixed by spec.
RECOMMENDED_CHECK_ORDER = [
    "freeze the failing test command before editing again",
    "cluster failures by stable signature before changing code",
    "separate repeated same-signature failure from new regression failure",
    "write down expected vs actual assertion diff",
    "make one minimal fix per cycle",
    "rerun the exact failing test before broad test suites",
    "record the final green test evidence before marking done",
]


def _parse_fixture_text(text: str) -> dict:
    """Parse the offline fixture text. Pure parsing — no execution, no
    inference of private code. Returns a dict of extracted fields."""

    def _yn(token: str) -> bool:
        # token on its own line, value 'true' or 'false'
        m = re.search(rf"(?im)^{re.escape(token)}\s*:\s*(true|false)\s*$", text)
        return (m.group(1).lower() == "true") if m else False

    def _int(token: str) -> int:
        m = re.search(rf"(?im)^{re.escape(token)}\s*:\s*(\d+)\s*$", text)
        return int(m.group(1)) if m else 0

    def _str(token: str) -> str:
        m = re.search(rf"(?im)^{re.escape(token)}\s*:\s*(.+?)\s*$", text)
        return m.group(1).strip() if m else ""

    # Collect all failing tests in document order (dedup, preserve order)
    failing_tests = []
    seen = set()
    for m in re.finditer(r"(?im)^failing_test\s*:\s*(.+?)\s*$", text):
        t = m.group(1).strip()
        if t and t not in seen:
            seen.add(t)
            failing_tests.append(t)

    # Collect all failure signatures in document order
    failure_signatures = []
    seen_s = set()
    for m in re.finditer(r"(?im)^failure_signature\s*:\s*(.+?)\s*$", text):
        s = m.group(1).strip()
        if s and s not in seen_s:
            seen_s.add(s)
            failure_signatures.append(s)

    tests_failed = bool(failing_tests) or _yn("tests_failed") or ("failed" in text.lower() and "result: failed" in text.lower())
    if not tests_failed:
        # If any "result: failed" appears, count it
        tests_failed = bool(re.search(r"(?im)^result\s*:\s*failed\s*$", text))

    code_change_attempted = _yn("code_change_attempted") or bool(re.search(r"(?im)^attempted fix\s*#", text))
    test_command_present = _yn("test_command_present") or bool(re.search(r"(?im)^test_command\s*:", text))

    repeated_failure_count = _int("repeated_failure_count")
    if repeated_failure_count == 0:
        # Count "test run #N" blocks
        repeated_failure_count = len(re.findall(r"(?im)^test run\s*#\d+", text))

    same_signature = _yn("same_failure_signature_repeated")
    if not same_signature and len(failure_signatures) >= 2 and len(set(failure_signatures)) < len(failure_signatures):
        same_signature = True

    fix_one_break_another = (
        _yn("fix_one_break_another")
        or "regression_introduced" in text
        or "regressionfailure" in text.lower()
        or bool(re.search(r"(?im)^result\s*:\s*new_failure_introduced", text))
    )

    regression_introduced = (
        _yn("regression_introduced")
        or bool(re.search(r"(?im)^result\s*:\s*new_failure_introduced", text))
        or "RegressionFailure" in text
    )

    failing_assertion = (
        "AssertionError" in text
        or "assertion_diff" in text
        or _yn("failing_assertion")
    )

    failure_cluster_missing = (
        _yn("failure_cluster_missing")
        or bool(re.search(r"(?im)failure\s+cluster", text))
    )

    prompt_context_stale = (
        _yn("prompt_context_stale_suspected")
        or "stale" in text.lower()
    )

    final_green_test_missing = (
        _yn("final_green_test_missing")
        or "final_green_test: missing" in text
        or "terminal_green_test: missing" in text
    )

    terminal_green_test_missing = (
        _yn("terminal_green_test") or final_green_test_missing
    )

    return {
        "ok": True,
        "component": _str("COMPONENT") or "codex-style-test-runner",
        "agent_mode": _str("agent_mode") or "code_edit",
        "code_change_attempted": code_change_attempted,
        "test_command_present": test_command_present,
        "tests_failed": tests_failed,
        "repeated_failure_count": repeated_failure_count,
        "same_failure_signature_repeated": same_signature,
        "failing_assertion_detected": failing_assertion,
        "regression_introduced": regression_introduced,
        "fix_one_break_another": fix_one_break_another,
        "failure_cluster_missing": failure_cluster_missing,
        "prompt_context_stale_suspected": prompt_context_stale,
        "final_green_test_missing": final_green_test_missing,
        "terminal_green_test_missing": terminal_green_test_missing,
        "failing_tests": failing_tests,
        "failure_signatures": failure_signatures,
        "recommended_check_order": RECOMMENDED_CHECK_ORDER,
        "safety": {
            "no_real_tests_run": True,
            "no_source_mutation": True,
            "no_env_scan": True,
            "no_secrets": True,
            "no_network_call": True,
            "no_online_coding_api": True,
            "fixture_only": True,
        },
    }


# ----- 4. Main -----

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Offline parser for Codex / AI coding test-failure-loop fixture text. "
            "Reads --input, refuses .env paths, refuses unsafe credential-shaped text, "
            "and outputs a JSON summary of the failure loop shape."
        )
    )
    parser.add_argument("--input", required=True, help="Path to the fixture text file")
    parser.add_argument("--strict", action="store_true", help="(no-op) this parser is strict by default")
    args = parser.parse_args()

    p = Path(args.input)

    # Path-level safety check
    path_reason = _refuse_input_path(p)
    if path_reason:
        out = {
            "ok": False,
            "error": path_reason,
            "input_path": str(p),
            "safety": {
                "no_real_tests_run": True,
                "no_source_mutation": True,
                "no_env_scan": True,
                "no_secrets": True,
                "no_network_call": True,
                "no_online_coding_api": True,
                "fixture_only": True,
            },
        }
        print(json.dumps(out, ensure_ascii=False))
        return 2

    # File existence
    if not p.exists():
        out = {
            "ok": False,
            "error": "input_file_not_found",
            "input_path": str(p),
        }
        print(json.dumps(out, ensure_ascii=False))
        return 2

    text = p.read_text(encoding="utf-8", errors="replace")

    # Content-level safety check
    content_reason = _scan_text_safety(text)
    if content_reason:
        out = {
            "ok": False,
            "error": content_reason,
            "input_path": str(p),
            "safety": {
                "no_real_tests_run": True,
                "no_source_mutation": True,
                "no_env_scan": True,
                "no_secrets": True,
                "no_network_call": True,
                "no_online_coding_api": True,
                "fixture_only": True,
            },
        }
        print(json.dumps(out, ensure_ascii=False))
        return 2

    # Parse (offline)
    out = _parse_fixture_text(text)
    out["input_path"] = str(p)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
