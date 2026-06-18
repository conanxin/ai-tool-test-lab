#!/usr/bin/env python3
"""
telegram_router_recovery_fixture.py — offline fixture parser for the
ATL-EVOMAP-6B Telegram Message Router Failure Bundle.

Reads a single text fixture (--input <path>) and emits a JSON summary that
captures the failure shape WITHOUT making any real network call, reading
.env files, executing curl/wget, or printing credentials / chat IDs.

Hard rules (enforced by tool design):
- Python stdlib only (argparse / json / re / sys / pathlib)
- Refuses --input whose basename matches .env pattern
- Refuses fixtures containing Telegram credential-like or recipient-like patterns
- No HTTP / no curl / no wget / no subprocess execution
- No .env read, no .evolver read, no real OpenClaw/Hermes config mutation
- Always emits structured JSON to stdout; non-zero exit only on hard refusal
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Patterns that, if present in the fixture text, indicate a leak risk.
# The parser refuses such fixtures (ok=false, exit 2) so reviewers must
# remove the offending text from the fixture before re-running.
CREDENTIAL_LIKE_PATTERNS = [
    # Telegram bot token: 7-10 digits + colon + 35 chars (the canonical shape)
    # Also catches "1234567890:AAH..." style strings pasted into the fixture.
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b"),
    # HTTP Authorization: header value
    re.compile(r"(?i)authorization\s*[:=]\s*[A-Za-z0-9_\-\.=]{16,}"),
    # API key style tokens
    re.compile(r"\b(sk-[A-Za-z0-9]{16,}|sk_live_[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,})\b"),
]

# Long pure-digit recipient-like IDs (10+ digits, no separators) — chat_id
# is normally 9-10 digits, but real production IDs can be 12+; threshold 12
# avoids false-positives on ports, line numbers, timestamps, ports.
RECIPIENT_LIKE_PATTERN = re.compile(r"\b\d{12,}\b")

# Allowed fixtures have an "intentionally omitted" sentinel; if the fixture
# accidentally leaks a real value, the credential-like patterns will catch it.
SAFE_REDACTION_SENTINEL = re.compile(r"intentionally omitted", re.IGNORECASE)

# .env-shape basenames the parser refuses (case-insensitive).
# We catch: exact ".env", ".env.*", "*env*" with no fixture-friendly extension,
# and any basename starting with "env" / ".env".
ENV_BASENAMES = re.compile(
    r"^\.env(\.|$)|^\.env$|env\.[A-Za-z0-9_]+$",
    re.IGNORECASE,
)
ALLOWED_BASENAME_HINTS = re.compile(
    r"fixture|sample|fixture-", re.IGNORECASE
)


def _bool(text, true_value=r"\btrue\b"):
    """Return True iff regex of true_value matches anywhere in text (case-insensitive)."""
    return re.search(true_value, text, re.IGNORECASE) is not None


def _neg_bool(text, false_value):
    """Return True iff 'value: missing' / 'value: false' / 'value: absent' is present."""
    return re.search(false_value, text, re.IGNORECASE) is not None


def _check_basename(path: Path) -> tuple[bool, str]:
    """Refuse .env-shape basenames UNLESS basename contains fixture/sample hint.

    The acceptance rule: if the basename looks like a fixture (contains
    'fixture', 'sample', or 'fixture-'), we accept it even if it would
    otherwise match an .env pattern. This protects the parser's own test
    fixtures (e.g. '.env-fixture.txt') from being rejected for the
    basename alone. The credential scan still runs on the content.
    """
    name = path.name
    if ENV_BASENAMES.search(name) and not ALLOWED_BASENAME_HINTS.search(name):
        return False, f"refusing .env-shape basename: {name}"
    return True, ""


def _scan_for_secrets(text: str) -> tuple[bool, str]:
    """Refuse fixtures containing credential-like or recipient-like patterns."""
    for pat in CREDENTIAL_LIKE_PATTERNS:
        m = pat.search(text)
        if m:
            return False, f"unsafe_fixture: credential-like pattern detected ({pat.pattern})"
    m = RECIPIENT_LIKE_PATTERN.search(text)
    if m:
        return False, f"unsafe_fixture: long-digit recipient-like id detected ({m.group()[:6]}...)"
    return True, ""


def _detect(text: str) -> dict:
    """Detect the Telegram router failure shape from the fixture text."""
    has = re.compile(r":\s*(true|present|missing|absent|false|timeout|unconfirmed|consumed|not confirmed)", re.IGNORECASE)

    def line_has(keyword: str, expected: str) -> bool:
        # Look for a line containing `keyword` (case-insensitive) and the expected token.
        for line in text.splitlines():
            if keyword.lower() in line.lower() and expected.lower() in line.lower():
                return True
        return False

    gateway_alive = line_has("gateway_alive", "true")
    router_loaded = line_has("message_router_loaded", "true")
    sendmessage_attempted = line_has("sendMessage_path", "attempted")
    sendvoice_attempted = line_has("sendVoice_path", "attempted")
    delivery_terminal_missing = line_has("delivery_terminal_result", "missing")

    sendmessage_timeout = (
        re.search(r"sendMessage result.*timeout", text, re.IGNORECASE) is not None
        or line_has("sendMessage result", "timeout")
    )
    sendvoice_unconfirmed = (
        re.search(r"sendVoice result.*(no|without).*delivery confirmation", text, re.IGNORECASE) is not None
        or line_has("sendVoice result", "no delivery confirmation")
        or line_has("sendVoice result", "without")
    )

    sendmessage_proxy_missing = line_has("actual_sendMessage_proxy", "missing")
    sendvoice_proxy_present = line_has("actual_sendVoice_proxy", "present")
    proxy_mismatch = (
        sendmessage_proxy_missing and sendvoice_proxy_present
    ) or line_has("proxy_mismatch", "true")

    retry_consumed = (
        re.search(r"retry result.*attempts consumed", text, re.IGNORECASE) is not None
        or line_has("retry result", "attempts consumed")
    )

    smoke_not_confirmed = (
        re.search(r"smoke result.*not confirmed", text, re.IGNORECASE) is not None
        or line_has("smoke result", "not confirmed")
    )

    return {
        "gateway_alive": gateway_alive,
        "message_router_loaded": router_loaded,
        "sendmessage_attempted": sendmessage_attempted,
        "sendvoice_attempted": sendvoice_attempted,
        "delivery_terminal_missing": delivery_terminal_missing,
        "sendmessage_timeout": sendmessage_timeout,
        "sendvoice_delivery_unconfirmed": sendvoice_unconfirmed,
        "proxy_mismatch": proxy_mismatch,
        "sendmessage_proxy_missing": sendmessage_proxy_missing,
        "sendvoice_proxy_present": sendvoice_proxy_present,
        "retry_consumed_without_terminal": retry_consumed,
        "smoke_not_confirmed": smoke_not_confirmed,
    }


def _recommended_check_order() -> list[str]:
    return [
        "confirm gateway health without printing credentials",
        "inspect router path selection for sendMessage and sendVoice",
        "verify proxy inheritance for both delivery paths",
        "check retry outcome for terminal success or failure event",
        "run one redacted dry-run smoke in fixture mode only",
        "record delivery evidence without printing credentials or recipient identifiers",
    ]


def _safety() -> dict:
    return {
        "no_real_telegram_call": True,
        "no_network_call": True,
        "no_curl_or_wget": True,
        "no_env_scan": True,
        "no_credentials": True,
        "no_recipient_identifier": True,
        "no_real_config_mutation": True,
    }


def parse_fixture(input_path: Path) -> dict:
    """Parse a Telegram router failure fixture and return the JSON summary."""
    ok, reason = _check_basename(input_path)
    if not ok:
        return {
            "ok": False,
            "error": "refused_input_path",
            "reason": reason,
        }

    if not input_path.exists():
        return {
            "ok": False,
            "error": "input_not_found",
            "input": str(input_path),
        }

    text = input_path.read_text(encoding="utf-8", errors="replace")

    safe, scan_reason = _scan_for_secrets(text)
    if not safe:
        return {
            "ok": False,
            "error": scan_reason,
            "input": str(input_path),
        }

    detected = _detect(text)
    checks_passed = sum(1 for v in detected.values() if v)
    checks_total = len(detected)

    summary = {
        "ok": True,
        "component": "hermes-telegram-message-router",
        "input": str(input_path),
        "input_size_bytes": input_path.stat().st_size,
        "redaction_safe": SAFE_REDACTION_SENTINEL.search(text) is not None,
        "detected_signals": detected,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "all_signals_present": checks_passed == checks_total,
        "recommended_check_order": _recommended_check_order(),
        "safety": _safety(),
    }
    # Flatten detected_signals to top level for the canonical schema
    for k, v in detected.items():
        summary[k] = v
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Offline Telegram router failure fixture parser (ATL-EVOMAP-6B)."
    )
    parser.add_argument("--input", required=True, help="Path to the failure fixture text file.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    result = parse_fixture(input_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Exit codes: 0 = parsed (ok=true or unsafe_fixture which is also a valid
    # result for review purposes), 1 = invalid usage, 2 = refused input path.
    if result.get("ok") is False and result.get("error") == "refused_input_path":
        return 2
    if result.get("ok") is False and result.get("error") == "input_not_found":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
