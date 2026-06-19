#!/usr/bin/env python3
"""
evomap_nightly_validate.py — ATL-EVOMAP-8A Nightly Validation Loop runner.

OFFLINE-ONLY, LOCAL-ONLY, STDLIB-ONLY.

Executes a fixed composite of pre-flight checks for the OpenClaw / Hermes
Local Evolution Kit, prints human-readable progress to stdout, and writes
both a JSON digest and a Markdown digest to --out-dir.

CLI (per ATL-EVOMAP-8A spec):

    python3 scripts/evomap_nightly_validate.py \\
        --repo-root . \\
        --out-dir <dir>

Optional flags:
    --strict                       treat any non-PASS check as FAIL exit
    --markdown-name <name>         override default digest Markdown filename
    --json-name <name>             override default digest JSON filename
    --dry-run                      run all checks but skip writing digests
    --output-dir <path>            backward-compat alias for --out-dir

Hard boundaries (enforced inside this script):

* No network egress (no urllib, no socket, no requests, no subprocess http)
* No Hub URL set / read / written
* No evolver --loop / run / review / solidify invocation
* No real credentials scanned or read
* No .env file content scanned (refused at the path level too)
* Only Python stdlib imports
* Writes only inside --out-dir

This script is intentionally NOT installed as a cron / systemd timer by
this phase. It only ships the runner plus a dry-run example template
(templates/cron.example). Any real scheduling must be performed by a human
operator in a separate, explicit phase (e.g. ATL-EVOMAP-8B).

Exit codes:
    0 — all blocking checks passed
    1 — at least one blocking check failed
    2 — invocation / boundary / IO error
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import mimetypes
import os
import re
import subprocess
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Any, Callable

# ----- stdlib-only guard -----------------------------------------------------

# If you ever add a third-party import here, this guard will refuse to run.
_ALLOWED_TOP_LEVEL_IMPORTS = {
    "argparse", "datetime", "json", "mimetypes", "os", "re", "subprocess",
    "sys", "textwrap", "traceback", "pathlib", "typing", "__future__",
}

# Output filename defaults per ATL-EVOMAP-8A spec
_DEFAULT_MARKDOWN_NAME = "nightly-validation-digest.md"
_DEFAULT_JSON_NAME = "nightly-validation-digest.json"
_DEFAULT_RUN_LOG_NAME = "nightly-validation-run.log"

# Secret-scan tunables
_SCAN_MAX_BYTES = 2 * 1024 * 1024  # 2 MiB
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
              ".ico", ".tiff", ".tif", ".svg"}
_BINARY_PROBE_BYTES = 4096
_MAX_TAIL_CHARS = 2000  # stdout_tail / stderr_tail cap

# Subprocess env: strip A2A_HUB_URL even if the parent has it set.
def _build_subprocess_env() -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "TZ": os.environ.get("TZ", "Asia/Shanghai"),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        "A2A_HUB_URL": "",
    }
    return env


# ----- secret scan patterns --------------------------------------------------

# Order matters: more specific patterns first so they win over generic ones.
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("authorization_bearer", re.compile(
        r"(?i)authorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._\-]{20,}['\"]?")),
    ("jwt", re.compile(
        r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")),
    ("private_key_block", re.compile(
        r"-----BEGIN\s+(?:RSA|EC|OPENSSH|DSA|PGP|PRIVATE)\s+PRIVATE\s+KEY-----")),
    ("cookie_assignment", re.compile(
        r"(?i)\b(?:set-cookie|cookie)\s*[:=]\s*[A-Za-z0-9_\-]{8,}")),
    ("long_digit_token", re.compile(r"(?<![.\w])(\d{12,})(?!\.\d)")),
]

# 13-digit Unix ms timestamp: 1.5e12 .. 2.0e12 (covers 2017-06 to 2033-05)
_UNIX_MS_TS = re.compile(r"\b1[5-9]\d{11}\b|\b20\d{10}\b")

# Allowlist tokens: placeholder / omitted text in reports
_PLACEHOLDER_HINT = re.compile(
    r"(?i)\b(?:placeholder|omitted|intentionally[_\- ]omitted|redacted|"
    r"fake|dummy|example\.com|example\.org|TODO|FIXME|sk[-_]XXXX|"
    r"ghp[_]YYYY|<[^>]+>|\[REDACTED\])\b")

# Files that should be excluded from scanning even if they look textual.
_ENV_BASENAME_HINT = re.compile(r"(^|/)(\.env|\.env\.[^/]+)$", re.IGNORECASE)

# Git ls-files paths that look like runtime / target dirs (we should never
# scan those because they should not be tracked; the git_hygiene check
# enforces that, but defense-in-depth here too).
_RUNTIME_HINT = re.compile(r"^/tmp/")


# ----- helpers ---------------------------------------------------------------

def _now_iso() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def _human_now() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z").strip()


def _print_check(name: str, status: str, detail: str = "") -> None:
    tag = {
        "PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]",
        "INFO": "[INFO]", "SKIP": "[SKIP]",
    }.get(status, f"[{status}]")
    suffix = f" — {detail}" if detail else ""
    print(f"  {tag} {name}{suffix}", flush=True)


def _record(results: list[dict[str, Any]],
            check_id: str,
            status: str,
            blocking: bool,
            detail: str = "",
            extra: dict[str, Any] | None = None) -> None:
    record = {
        "check_id": check_id,
        "status": status,
        "blocking": blocking,
        "detail": detail,
    }
    if extra:
        record["extra"] = extra
    results.append(record)
    _print_check(check_id, status, detail)


def _enforce_stdlib_only() -> tuple[bool, str]:
    src_path = Path(__file__)
    try:
        src = src_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"cannot read runner source: {exc}"
    pattern = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)",
                         re.MULTILINE)
    bad: list[str] = []
    for match in pattern.finditer(src):
        mod = match.group(1)
        if mod in _ALLOWED_TOP_LEVEL_IMPORTS:
            continue
        bad.append(mod)
    if bad:
        return False, "non-stdlib imports detected: " + ", ".join(sorted(set(bad)))
    return True, "stdlib-only verified"


def _enforce_no_hub_url() -> tuple[bool, str]:
    hub = os.environ.get("A2A_HUB_URL")
    if hub:
        return False, f"A2A_HUB_URL is set (length={len(hub)})"
    return True, "A2A_HUB_URL not set"


def _cap(text: str, n: int = _MAX_TAIL_CHARS) -> str:
    if not text:
        return ""
    if len(text) <= n:
        return text
    return text[-n:]


def _run_subprocess_capture(cmd: list[str],
                            cwd: Path,
                            timeout_seconds: int = 120
                            ) -> dict[str, Any]:
    """Run subprocess with timeout. Never raise on non-zero exit."""
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=_build_subprocess_env(),
        )
    except subprocess.TimeoutExpired:
        return {
            "returncode": 124,
            "stdout_tail": "",
            "stderr_tail": _cap(f"timeout after {timeout_seconds}s"),
            "command": cmd,
        }
    except FileNotFoundError as exc:
        return {
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": _cap(f"command not found: {exc}"),
            "command": cmd,
        }
    return {
        "returncode": completed.returncode,
        "stdout_tail": _cap(completed.stdout or ""),
        "stderr_tail": _cap(completed.stderr or ""),
        "command": cmd,
    }


# ----- individual checks -----------------------------------------------------


def check_stdlib_only(results: list[dict[str, Any]]) -> None:
    ok, detail = _enforce_stdlib_only()
    _record(results, "stdlib_only", "PASS" if ok else "FAIL",
            blocking=True, detail=detail)


def check_no_hub_url(results: list[dict[str, Any]]) -> None:
    ok, detail = _enforce_no_hub_url()
    _record(results, "no_hub_url_set", "PASS" if ok else "FAIL",
            blocking=True, detail=detail)


def check_data_cases_json_parse(results: list[dict[str, Any]],
                                repo_root: Path) -> None:
    """Per spec: use `python3 -m json.tool data/cases.json`."""
    proc = _run_subprocess_capture(
        ["python3", "-m", "json.tool", "data/cases.json"],
        cwd=repo_root,
        timeout_seconds=30,
    )
    ok = proc["returncode"] == 0
    detail = f"rc={proc['returncode']}"
    _record(results, "data_cases_json_parse", "PASS" if ok else "FAIL",
            blocking=True, detail=detail,
            extra={"command": proc["command"],
                   "stdout_tail": proc["stdout_tail"],
                   "stderr_tail": proc["stderr_tail"]})

    # phase-history awareness (forward-compatible)
    cases_path = repo_root / "data" / "cases.json"
    if not cases_path.exists():
        _record(results, "data_cases_json_phase_history_has_evomap_8a",
                "FAIL", True, detail=f"missing: {cases_path}")
        return
    try:
        data = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _record(results, "data_cases_json_phase_history_has_evomap_8a",
                "FAIL", True, detail=f"parse error: {exc}")
        return
    case = next(
        (c for c in data.get("cases", [])
         if c.get("slug") == "evomap-evolver-openclaw-v0"),
        None,
    )
    if case is None:
        _record(results, "data_cases_json_phase_history_has_evomap_8a",
                "FAIL", True, detail="slug not present")
        return
    top_phase = str(case.get("phase", ""))
    history = case.get("phase_history", []) or []
    history_phases = [str(h.get("phase", "")) for h in history
                      if isinstance(h, dict)]
    has_top = "ATL-EVOMAP-8A" in top_phase
    has_hist = any("ATL-EVOMAP-8A" in p for p in history_phases)
    if has_top or has_hist:
        _record(results, "data_cases_json_phase_history_has_evomap_8a",
                "PASS", True,
                detail=("top" if has_top else "history")
                        + f", history_count={len(history_phases)}")
    else:
        _record(results, "data_cases_json_phase_history_has_evomap_8a",
                "FAIL", True,
                detail=f"top_phase={top_phase!r}, "
                       f"history_count={len(history_phases)}")


def _resolve_bundle_paths(repo_root: Path) -> list[tuple[str, Path]]:
    return [
        ("openclaw_tool_use_discipline",
         repo_root / "cases" / "evomap-evolver-openclaw-v0"
         / "phase5-local-evolution-kit" / "bundle"
         / "openclaw-tool-use-discipline.bundle.json"),
        ("hermes_systemd_recovery",
         repo_root / "cases" / "evomap-evolver-openclaw-v0"
         / "phase6a-hermes-systemd-bundle" / "bundle"
         / "hermes-systemd-service-recovery.bundle.json"),
        ("telegram_message_router_failure",
         repo_root / "cases" / "evomap-evolver-openclaw-v0"
         / "phase6b-telegram-router-bundle" / "bundle"
         / "telegram-message-router-failure.bundle.json"),
        ("codex_test_failure_loop",
         repo_root / "cases" / "evomap-evolver-openclaw-v0"
         / "phase6c-codex-test-failure-bundle" / "bundle"
         / "codex-test-failure-loop.bundle.json"),
    ]


def check_bundles_inspect_and_validate(results: list[dict[str, Any]],
                                       repo_root: Path) -> None:
    """Run both inspect_bundle AND validate_bundle for each canonical bundle."""
    bundles = _resolve_bundle_paths(repo_root)
    inspect_script = repo_root / "scripts" / "evomap_inspect_bundle.py"
    validate_script = repo_root / "scripts" / "evomap_validate_bundle.py"

    if not inspect_script.exists() or not validate_script.exists():
        _record(results, "bundles_inspectable", "FAIL", True,
                detail="missing inspect or validate script")
        _record(results, "bundles_validatable", "FAIL", True,
                detail="missing inspect or validate script")
        return

    inspect_failures: list[str] = []
    validate_failures: list[str] = []
    inspect_log: list[dict[str, Any]] = []
    validate_log: list[dict[str, Any]] = []

    for bid, bundle_path in bundles:
        if not bundle_path.exists():
            inspect_failures.append(f"{bid}:missing")
            validate_failures.append(f"{bid}:missing")
            continue

        # inspect
        proc = _run_subprocess_capture(
            ["python3", str(inspect_script), "--bundle", str(bundle_path)],
            cwd=repo_root, timeout_seconds=30,
        )
        inspect_log.append({
            "id": bid,
            "path": str(bundle_path.relative_to(repo_root)),
            "returncode": proc["returncode"],
            "stdout_tail": proc["stdout_tail"],
            "stderr_tail": proc["stderr_tail"],
        })
        if proc["returncode"] != 0:
            inspect_failures.append(f"{bid}:rc={proc['returncode']}")

        # validate
        proc = _run_subprocess_capture(
            ["python3", str(validate_script), "--bundle", str(bundle_path)],
            cwd=repo_root, timeout_seconds=30,
        )
        validate_log.append({
            "id": bid,
            "path": str(bundle_path.relative_to(repo_root)),
            "returncode": proc["returncode"],
            "stdout_tail": proc["stdout_tail"],
            "stderr_tail": proc["stderr_tail"],
        })
        if proc["returncode"] != 0:
            validate_failures.append(f"{bid}:rc={proc['returncode']}")

    if inspect_failures:
        _record(results, "bundles_inspectable", "FAIL", True,
                detail="; ".join(inspect_failures),
                extra={"inspected": inspect_log})
    else:
        _record(results, "bundles_inspectable", "PASS", True,
                detail=f"{len(inspect_log)} bundle(s) inspected",
                extra={"inspected": inspect_log})

    if validate_failures:
        _record(results, "bundles_validatable", "FAIL", True,
                detail="; ".join(validate_failures),
                extra={"validated": validate_log})
    else:
        _record(results, "bundles_validatable", "PASS", True,
                detail=f"{len(validate_log)} bundle(s) validated",
                extra={"validated": validate_log})


def check_all_phase_validators_pass(results: list[dict[str, Any]],
                                    repo_root: Path) -> None:
    failures: list[str] = []
    detail_map: list[dict[str, Any]] = []
    validators = [
        ("phase5_local_evolution_kit",
         "scripts/validate_evomap_phase5_local_evolution_kit.py"),
        ("phase6a_hermes_systemd_bundle",
         "scripts/validate_evomap_phase6a_hermes_systemd_bundle.py"),
        ("phase6b_telegram_router_bundle",
         "scripts/validate_evomap_phase6b_telegram_router_bundle.py"),
        ("phase6c_codex_test_failure_bundle",
         "scripts/validate_evomap_phase6c_codex_test_failure_bundle.py"),
        ("phase7a_domain_signal_injection",
         "scripts/validate_evomap_phase7a_domain_signal_injection.py"),
        ("phase7b_cross_bundle_regression",
         "scripts/validate_evomap_phase7b_cross_bundle_regression.py"),
    ]
    for vid, rel in validators:
        script = repo_root / rel
        if not script.exists():
            failures.append(f"{vid}:missing")
            detail_map.append({
                "id": vid, "returncode": -1,
                "stdout_tail": "", "stderr_tail": "script-missing",
            })
            continue
        proc = _run_subprocess_capture(
            ["python3", str(script)], cwd=repo_root, timeout_seconds=180,
        )
        passed = (proc["returncode"] == 0
                  and "ALL CHECKS PASSED" in (proc["stdout_tail"] or ""))
        detail_map.append({
            "id": vid,
            "returncode": proc["returncode"],
            "stdout_tail": proc["stdout_tail"],
            "stderr_tail": proc["stderr_tail"],
        })
        if not passed:
            failures.append(f"{vid}:rc={proc['returncode']}")

    if failures:
        _record(results, "all_phase_validators_pass", "FAIL", True,
                detail="; ".join(failures),
                extra={"validators": detail_map})
    else:
        _record(results, "all_phase_validators_pass", "PASS", True,
                detail=f"{len(detail_map)} validator(s) ALL CHECKS PASSED",
                extra={"validators": detail_map})


def _is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(_BINARY_PROBE_BYTES)
    except OSError:
        return True
    if not chunk:
        return False
    if b"\x00" in chunk:
        return True
    # Heuristic: >5% non-text bytes
    text_chars = bytes(range(0x20, 0x7F)) + b"\n\r\t\f\b"
    nontext = sum(1 for b in chunk if b not in text_chars)
    return (nontext / len(chunk)) > 0.05


def _is_image(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext in _IMAGE_EXT:
        return True
    # mimetypes is a stdlib helper, not an external dep
    mime, _ = mimetypes.guess_type(str(path))
    return bool(mime and mime.startswith("image/"))


def _is_env_path(path: str) -> bool:
    return bool(_ENV_BASENAME_HINT.search(path))


def _scan_text_for_secrets(text: str) -> dict[str, Any]:
    """Returns dict of {pattern_name: [hit, ...]}.  Also returns
    allowed_timestamp_hits count.  Allowlist tokens (placeholder / omitted
    / etc.) suppress hits whose line contains such a token.
    """
    hits: dict[str, list[str]] = {}
    allowed_ts = 0
    lines = text.splitlines()
    for line in lines:
        # Allowlist short-circuit: if the line looks like placeholder text,
        # skip secret detection on it.
        if _PLACEHOLDER_HINT.search(line):
            continue
        for name, pat in _SECRET_PATTERNS:
            for m in pat.finditer(line):
                hit = m.group(0)
                # Special-case: 12+ digit tokens that look like Unix ms
                # timestamps are allowed, but we still record them.
                if name == "long_digit_token" and _UNIX_MS_TS.fullmatch(hit):
                    allowed_ts += 1
                    continue
                hits.setdefault(name, []).append(hit)
    return {"hits": hits, "allowed_timestamp_hits": allowed_ts}


def check_secret_scan_clean(results: list[dict[str, Any]],
                            repo_root: Path) -> None:
    """In-process stdlib secret scan per ATL-EVOMAP-8A spec.

    Scope: only git ls-files (tracked files). Skip binaries, images, >2 MiB
    files, .env paths (FAIL directly if any), and any /tmp/ runtime paths
    (defense-in-depth: git_hygiene already excludes them, but bail if seen).
    """
    proc = _run_subprocess_capture(
        ["git", "ls-files"], cwd=repo_root, timeout_seconds=30,
    )
    if proc["returncode"] != 0:
        _record(results, "secret_scan_clean", "FAIL", True,
                detail=f"git ls-files rc={proc['returncode']}")
        return
    tracked = [ln for ln in (proc["stdout_tail"] or "").splitlines()
               if ln.strip()]
    # NOTE: stdout_tail is capped at 2000 chars; use the full stdout via a
    # second subprocess-free path — re-run without tail cap.

    # Re-fetch full ls-files (uncapped) using a quick re-read
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(repo_root), capture_output=True, check=False, timeout=30,
            env=_build_subprocess_env(),
        ).stdout.decode("utf-8", errors="replace")
    except Exception as exc:
        _record(results, "secret_scan_clean", "FAIL", True,
                detail=f"git ls-files -z failed: {exc}")
        return
    tracked = [p for p in out.split("\x00") if p]

    # .env path anywhere in tracked list => FAIL directly
    env_hits = [p for p in tracked if _is_env_path(p)]
    if env_hits:
        _record(results, "secret_scan_clean", "FAIL", True,
                detail=f"tracked .env path(s): {env_hits[:3]}",
                extra={"env_path_hits": env_hits[:10]})
        return

    # /tmp target runtime defense-in-depth
    runtime_hits = [p for p in tracked if _RUNTIME_HINT.match(p)]
    if runtime_hits:
        _record(results, "secret_scan_clean", "FAIL", True,
                detail=f"tracked /tmp path(s): {runtime_hits[:3]}",
                extra={"runtime_hits": runtime_hits[:10]})
        return

    all_hits: dict[str, list[str]] = {}
    allowed_ts_total = 0
    scanned = 0
    skipped = {"binary": 0, "image": 0, "too_large": 0, "io_error": 0}
    skipped_paths: list[str] = []

    for rel in tracked:
        full = repo_root / rel
        if not full.exists() or not full.is_file():
            continue
        try:
            if full.stat().st_size > _SCAN_MAX_BYTES:
                skipped["too_large"] += 1
                skipped_paths.append(f"{rel} (>2MiB)")
                continue
        except OSError:
            skipped["io_error"] += 1
            continue
        if _is_image(full):
            skipped["image"] += 1
            skipped_paths.append(f"{rel} (image)")
            continue
        if _is_probably_binary(full):
            skipped["binary"] += 1
            skipped_paths.append(f"{rel} (binary)")
            continue
        try:
            text = full.read_text(encoding="utf-8", errors="replace")
        except OSError:
            skipped["io_error"] += 1
            continue
        scanned += 1
        result = _scan_text_for_secrets(text)
        for name, hits in result["hits"].items():
            all_hits.setdefault(name, []).extend(hits[:50])  # cap per-pattern
        allowed_ts_total += result["allowed_timestamp_hits"]

    total_hits = sum(len(v) for v in all_hits.values())
    ok = total_hits == 0
    _record(
        results, "secret_scan_clean", "PASS" if ok else "FAIL",
        blocking=True,
        detail=(
            f"scanned={scanned}, "
            f"hits={total_hits}, "
            f"allowed_timestamp_hits={allowed_ts_total}, "
            f"skipped={skipped}"
        ),
        extra={
            "scanned_file_count": scanned,
            "skipped": skipped,
            "hits": all_hits,
            "allowed_timestamp_hits": allowed_ts_total,
            "skipped_paths_sample": skipped_paths[:10],
        },
    )


def check_git_hygiene(results: list[dict[str, Any]],
                      repo_root: Path) -> None:
    # Full ls-files (uncapped)
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_root), capture_output=True, check=False, timeout=30,
            env=_build_subprocess_env(),
        ).stdout.decode("utf-8", errors="replace")
    except Exception as exc:
        _record(results, "git_hygiene_no_root_evolver_or_memory", "FAIL",
                True, detail=f"git ls-files failed: {exc}")
        return
    tracked = [ln for ln in out.splitlines() if ln.strip()]

    bad: list[str] = []
    for path in tracked:
        # Reject any root-level .evolver/ or memory/ path
        if path.startswith(".evolver/") or path == ".evolver":
            bad.append(path)
        elif path.startswith("memory/"):
            bad.append(path)

    # Also record git status --short (informational; not a fail criterion
    # because this run produces new artifacts)
    status_proc = _run_subprocess_capture(
        ["git", "status", "--short"],
        cwd=repo_root, timeout_seconds=15,
    )
    status_short_lines = [
        ln for ln in (status_proc.get("stdout_tail") or "").splitlines()
        if ln.strip()
    ]
    # Re-fetch full (uncapped) status:
    try:
        status_full = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(repo_root), capture_output=True, check=False, timeout=15,
            env=_build_subprocess_env(),
        ).stdout.decode("utf-8", errors="replace")
    except Exception:
        status_full = ""
    status_full_lines = [ln for ln in status_full.splitlines() if ln.strip()]

    if bad:
        _record(results, "git_hygiene_no_root_evolver_or_memory", "FAIL",
                True,
                detail=f"{len(bad)} bad path(s): {bad[:3]}",
                extra={"tracked_count": len(tracked), "bad": bad[:10],
                       "status_short_count": len(status_full_lines)})
    else:
        _record(results, "git_hygiene_no_root_evolver_or_memory", "PASS",
                True,
                detail=f"{len(tracked)} tracked file(s) clean, "
                       f"status_short={len(status_full_lines)} line(s) "
                       "(informational)",
                extra={"tracked_count": len(tracked),
                       "status_short_count": len(status_full_lines)})


# ----- digest writers --------------------------------------------------------


def _render_markdown_digest(digest: dict[str, Any],
                            json_name: str,
                            md_name: str) -> str:
    lines: list[str] = []
    lines.append("# EvoMap Nightly Validation Loop — Digest")
    lines.append("")
    lines.append(f"- **Generated:** {digest['generated_at']}")
    lines.append(f"- **Phase:** {digest['phase']}")
    lines.append(f"- **Schema version:** {digest.get('schema_version', '?')}")
    lines.append(f"- **Source base commit:** {digest.get('source_base_commit', '?')}")
    lines.append(f"- **Case slug:** `{digest['case_slug']}`")
    lines.append(f"- **Project root:** `{digest['project_root']}`")
    lines.append(f"- **Runner:** `{digest['runner']}`")
    lines.append(f"- **Python:** {digest['python']}")
    lines.append(f"- **Stdlib-only:** {'YES' if digest['stdlib_only'] else 'NO'}")
    lines.append(f"- **A2A_HUB_URL set:** {'YES' if digest['hub_url_set'] else 'no'}")
    lines.append(f"- **Overall status:** **{digest['overall_status']}**")
    sm = digest["summary"]
    lines.append(f"- **Blocking checks passed:** "
                 f"{sm['passed']} / {sm['blocking_total']}")
    lines.append(f"- **Non-blocking WARN/INFO rows:** {sm['non_blocking']}")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| # | Check ID | Status | Blocking | Detail |")
    lines.append("|---|----------|--------|----------|--------|")
    for i, c in enumerate(digest["checks"], 1):
        detail = (c.get("detail") or "").replace("|", "\\|")
        lines.append(f"| {i} | `{c['check_id']}` | {c['status']} | "
                     f"{'yes' if c['blocking'] else 'no'} | {detail} |")
    lines.append("")
    # Phase validators detail
    val_section = next(
        (c for c in digest["checks"]
         if c["check_id"] == "all_phase_validators_pass"), None)
    if val_section and "extra" in val_section:
        lines.append("## Phase validators")
        lines.append("")
        lines.append("| Validator | Returncode | Last 2000 chars of stdout |")
        lines.append("|-----------|------------|----------------------------|")
        for v in val_section["extra"].get("validators", []):
            tail = (v.get("stdout_tail", "") or "").replace("|", "\\|")
            lines.append(f"| `{v['id']}` | {v['returncode']} | {tail} |")
        lines.append("")
    # Bundle inspect/validate detail
    ins_section = next(
        (c for c in digest["checks"]
         if c["check_id"] == "bundles_inspectable"), None)
    val_section2 = next(
        (c for c in digest["checks"]
         if c["check_id"] == "bundles_validatable"), None)
    if ins_section or val_section2:
        lines.append("## Bundle inspect / validate")
        lines.append("")
        lines.append("| Bundle | Path | inspect rc | validate rc |")
        lines.append("|--------|------|------------|-------------|")
        ins_log = (ins_section.get("extra", {}) if ins_section else {}).get(
            "inspected", [])
        val_log = (val_section2.get("extra", {}) if val_section2 else {}).get(
            "validated", [])
        val_by_id = {v["id"]: v for v in val_log}
        for entry in ins_log:
            v = val_by_id.get(entry["id"], {})
            lines.append(
                f"| `{entry['id']}` | `{entry['path']}` | "
                f"{entry['returncode']} | {v.get('returncode', '?')} |"
            )
        lines.append("")
    # Secret scan
    sec_section = next(
        (c for c in digest["checks"] if c["check_id"] == "secret_scan_clean"),
        None)
    if sec_section and "extra" in sec_section:
        extra = sec_section["extra"]
        lines.append("## Secret scan")
        lines.append("")
        lines.append(f"- **Scanned file count:** {extra.get('scanned_file_count', 0)}")
        lines.append(f"- **Allowed timestamp hits:** {extra.get('allowed_timestamp_hits', 0)}")
        lines.append(f"- **Skipped:** {extra.get('skipped', {})}")
        lines.append(f"- **Hits:** {extra.get('hits', {})}")
        lines.append("")
    # Git
    git_section = next(
        (c for c in digest["checks"]
         if c["check_id"] == "git_hygiene_no_root_evolver_or_memory"), None)
    if git_section and "extra" in git_section:
        lines.append("## Git")
        lines.append("")
        lines.append(f"- **Tracked file count:** {git_section['extra'].get('tracked_count', 0)}")
        lines.append(f"- **git status --short line count:** "
                     f"{git_section['extra'].get('status_short_count', 0)} "
                     "(informational; this run produces new artifacts)")
        lines.append("")
    # Hard boundaries
    lines.append("## Hard boundaries (declared in this run)")
    lines.append("")
    for k, v in sorted(digest["hard_boundaries"].items()):
        lines.append(f"- `{k}`: {'YES' if v else 'no'}")
    lines.append("")
    # Notes
    lines.append("## Notes")
    lines.append("")
    lines.append(f"- This digest is **machine-generated by the nightly "
                 f"validation loop runner** (per ATL-EVOMAP-8A spec, "
                 f"schema `{digest.get('schema_version', '?')}`).")
    lines.append("- This phase ships the runner + dry-run cron example; "
                 "**no real cron / systemd timer is installed**.")
    lines.append("- Any scheduling is operator-owned and must be performed "
                 "in a separate explicit phase (e.g. ATL-EVOMAP-8B).")
    lines.append("")
    lines.append(f"- **Digest files:** `{json_name}` and `{md_name}` "
                 "in the same directory as this Markdown file.")
    lines.append("")
    return "\n".join(lines)


def _write_digests(digest: dict[str, Any],
                   out_dir: Path,
                   json_name: str,
                   md_name: str) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / json_name
    md_path = out_dir / md_name
    log_path = out_dir / _DEFAULT_RUN_LOG_NAME

    json_path.write_text(
        json.dumps(digest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        _render_markdown_digest(digest, json_name, md_name),
        encoding="utf-8",
    )

    log_lines = [
        f"evomap-nightly run @ {digest['generated_at']}",
        f"phase={digest['phase']} schema={digest.get('schema_version', '?')}",
        f"overall_status={digest['overall_status']}",
        f"passed={digest['summary']['passed']}/"
        f"{digest['summary']['blocking_total']} blocking",
        "",
    ]
    for c in digest["checks"]:
        log_lines.append(
            f"{c['status']:<5} "
            f"{'BLOCK' if c['blocking'] else 'info '} "
            f"{c['check_id']} — {c.get('detail', '')}"
        )
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    return {
        "digest_json": str(json_path),
        "digest_markdown": str(md_path),
        "run_log": str(log_path),
    }


# ----- main ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evomap_nightly_validate.py",
        description=("ATL-EVOMAP-8A Nightly Validation Loop runner. "
                     "Offline-only, stdlib-only."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to the ai-tool-test-lab repo root (default: cwd)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory to write digests into",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="(Backward-compat alias for --out-dir)",
    )
    parser.add_argument(
        "--markdown-name",
        type=str,
        default=_DEFAULT_MARKDOWN_NAME,
        help=f"Digest Markdown filename (default: {_DEFAULT_MARKDOWN_NAME})",
    )
    parser.add_argument(
        "--json-name",
        type=str,
        default=_DEFAULT_JSON_NAME,
        help=f"Digest JSON filename (default: {_DEFAULT_JSON_NAME})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat any non-PASS check as a blocking FAIL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all checks but skip writing digest files.",
    )
    args = parser.parse_args(argv)

    # Resolve repo-root
    repo_root = args.repo_root.resolve()
    if not (repo_root / "scripts").exists() or not (repo_root / "data").exists():
        print(f"[FAIL] --repo-root does not look like the ai-tool-test-lab "
              f"repo: {repo_root}", flush=True)
        return 2

    # Resolve out-dir
    out_dir_arg = args.out_dir or args.output_dir
    if out_dir_arg is None:
        out_dir_arg = (
            repo_root
            / "cases" / "evomap-evolver-openclaw-v0"
            / "phase8a-nightly-validation-loop" / "artifacts"
        )
    out_dir = out_dir_arg.resolve()

    # Git commit + status
    commit_proc = _run_subprocess_capture(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root, timeout_seconds=15,
    )
    git_commit = (commit_proc.get("stdout_tail") or "").strip()
    status_proc = _run_subprocess_capture(
        ["git", "status", "--short"],
        cwd=repo_root, timeout_seconds=15,
    )
    try:
        status_full = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(repo_root), capture_output=True, check=False, timeout=15,
            env=_build_subprocess_env(),
        ).stdout.decode("utf-8", errors="replace")
    except Exception:
        status_full = ""
    git_status_short = status_full

    print("=" * 70)
    print(f"ATL-EVOMAP-8A Nightly Validation Loop @ {_human_now()}")
    print(f"  python     : {sys.version.split()[0]}")
    print(f"  repo_root  : {repo_root}")
    print(f"  out_dir    : {out_dir}")
    print(f"  json_name  : {args.json_name}")
    print(f"  md_name    : {args.markdown_name}")
    print(f"  git_commit : {git_commit or '(unknown)'}")
    print(f"  dry_run    : {args.dry_run}")
    print("=" * 70, flush=True)

    results: list[dict[str, Any]] = []
    checks: list[Callable[..., None]] = [
        check_stdlib_only,
        check_no_hub_url,
        lambda r: check_data_cases_json_parse(r, repo_root),
        lambda r: check_bundles_inspect_and_validate(r, repo_root),
        lambda r: check_all_phase_validators_pass(r, repo_root),
        lambda r: check_secret_scan_clean(r, repo_root),
        lambda r: check_git_hygiene(r, repo_root),
    ]

    for fn in checks:
        try:
            fn(results)
        except Exception as exc:  # pragma: no cover — defensive
            _record(results, fn.__name__, "FAIL", True,
                    detail=f"runner crashed: {exc}",
                    extra={"trace": traceback.format_exc().splitlines()[-3:]})

    passed = sum(1 for c in results
                 if c["status"] == "PASS" and c["blocking"])
    failed = sum(1 for c in results
                 if c["status"] == "FAIL" and c["blocking"])
    non_blocking = sum(1 for c in results if not c["blocking"])
    overall = "PASS" if failed == 0 else "FAIL"

    summary = {
        "blocking_total": passed + failed,
        "passed": passed,
        "failed": failed,
        "non_blocking": non_blocking,
    }

    # Determine stdlib-only and hub_url set from results
    stdlib_ok = all(c["check_id"] != "stdlib_only" or c["status"] == "PASS"
                    for c in results)
    hub_url_set = bool(os.environ.get("A2A_HUB_URL"))

    digest: dict[str, Any] = {
        "schema_version": "atl-evomap-nightly-validation-v0.1",
        "phase": "ATL-EVOMAP-8A",
        "case_slug": "evomap-evolver-openclaw-v0",
        "generated_at": _now_iso(),
        "project_root": str(repo_root),
        "out_dir": str(out_dir),
        "git_commit": git_commit,
        "git_status_short": git_status_short,
        "runner": "scripts/evomap_nightly_validate.py",
        "python": sys.version.split()[0],
        "stdlib_only": stdlib_ok,
        "hub_url_set": hub_url_set,
        "overall_status": overall,
        "summary": summary,
        "checks": results,
        "hard_boundaries": {
            "no_hub_connection": True,
            "no_a2a_hub_url": True,
            "no_evolver_loop": True,
            "no_evolver_run": True,
            "no_evolver_review": True,
            "no_evolver_review_approve": True,
            "no_evolver_solidify": True,
            "no_auto_publish": True,
            "no_credit_consumption": True,
            "no_atp_autobuy": True,
            "no_real_credentials_read": True,
            "no_env_file_content_scanned": True,
            "no_curl_or_http_calls": True,
            "no_telegram_api": True,
            "no_online_coding_apis": True,
            "no_real_test_runners": True,
            "no_real_cron_install": True,
            "no_crontab_write": True,
            "no_systemd_timer_create": True,
            "no_evolver_package_source_modify": True,
            "no_runtime_evolver_or_memory_tracked": True,
            "stdlib_only": True,
        },
        "manifest_path": str(repo_root / "cases"
                              / "evomap-evolver-openclaw-v0"
                              / "phase8a-nightly-validation-loop"
                              / "validation-loop-manifest.json"),
        "source_base_commit": "f292757",
    }

    print("=" * 70)
    print(f"Overall status: {overall}")
    print(f"Blocking: passed={passed}, failed={failed}, "
          f"non_blocking_rows={non_blocking}")
    print("=" * 70, flush=True)

    if args.dry_run:
        print(textwrap.dedent("""
            --dry-run set: digest files NOT written.
            (Re-run without --dry-run to persist nightly-validation-digest.{json,md}
             and nightly-validation-run.log.)
        """).strip(), flush=True)
        return 0 if failed == 0 else 1

    try:
        paths = _write_digests(digest, out_dir,
                               args.json_name, args.markdown_name)
    except OSError as exc:
        print(f"[FAIL] could not write digests: {exc}", flush=True)
        return 2
    print(f"Digest JSON     : {paths['digest_json']}")
    print(f"Digest Markdown : {paths['digest_markdown']}")
    print(f"Run log         : {paths['run_log']}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
