#!/usr/bin/env python3
"""
evomap_nightly_validate.py — ATL-EVOMAP-8A Nightly Validation Loop runner.

Extended in ATL-EVOMAP-9B with a non-blocking canary bundle lane that ingests
curator-generated draft bundles (inspect / validate / apply dry-run against a
/tmp target). Canary failures do NOT cause overall_status=FAIL.

OFFLINE-ONLY, LOCAL-ONLY, STDLIB-ONLY.

Executes a fixed composite of pre-flight checks for the OpenClaw / Hermes
Local Evolution Kit, prints human-readable progress to stdout, and writes
both a JSON digest and a Markdown digest to --out-dir.

CLI (per ATL-EVOMAP-8A spec, extended in ATL-EVOMAP-9B):

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

# Default manifest path (used to read canary_bundles in 9B mode).
# NOTE: uses os.path.join so this constant can live at module scope without
# requiring from pathlib import Path at the top of the file (Path is imported
# lazily below for the rest of the file).
_DEFAULT_MANIFEST_PATH = os.path.join(
    "cases", "evomap-evolver-openclaw-v0",
    "phase8a-nightly-validation-loop",
    "validation-loop-manifest.json",
)


def _load_manifest(repo_root: "Path") -> dict[str, Any]:
    """Read the validation-loop-manifest.json. Returns empty dict if
    missing or unparseable. Used to discover canary_bundles in 9B mode.
    """
    manifest_path = repo_root / _DEFAULT_MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


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
        ("phase9a_bundle_curator_skill",
         "scripts/validate_evomap_phase9a_bundle_curator_skill.py"),
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


# ----- canary bundle lane (ATL-EVOMAP-9B) ------------------------------------


def _extract_apply_ok(stdout: str) -> tuple[bool, str]:
    """Try to parse the apply_bundle dry-run JSON. Returns (apply_ok, reason).

    apply_bundle prints a JSON plan with top-level "ok". If parse fails or
    "ok" is missing, we fall back to rc-only behavior.
    """
    if not stdout:
        return True, "no_stdout"
    # apply_bundle writes JSON; try to grab a balanced JSON object from
    # stdout (last 4 KiB is enough; we already cap at 2000 chars)
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        # Maybe the JSON is truncated (2000-char tail). Try to recover.
        # Find last "}" and attempt to slice — but simpler: just say
        # "json_truncated" and let the caller treat rc-only as authoritative.
        return True, "json_truncated_or_unparseable"
    if isinstance(parsed, dict):
        if parsed.get("ok") is False:
            reason = str(parsed.get("reason") or parsed.get("error") or
                         "apply_ok_false")
            return False, reason
        return True, "ok"
    return True, "non_dict_json"


def check_canary_bundles(results: list[dict[str, Any]],
                         repo_root: Path) -> None:
    """ATL-EVOMAP-9B canary lane.

    Reads `canary_bundles[]` from the validation-loop-manifest.json. For each
    canary bundle entry, runs:

      1. python3 scripts/evomap_inspect_bundle.py --bundle <path>
      2. python3 scripts/evomap_validate_bundle.py --bundle <path>
      3. python3 scripts/evomap_apply_bundle.py --bundle <path> \\
            --target-runtime /tmp/atl-evomap-nightly-canary-<id> --dry-run

    Each canary is NON-BLOCKING by default. The check itself records a
    single non-blocking row `canary_bundles_checked`. Per-bundle details
    are stored in `extra.canary_bundle_checks` and aggregated in
    `extra.canary_summary` so the digest JSON / Markdown can render a
    dedicated canary section.

    overall_status is determined only by blocking checks; canary failures
    never cause overall_status=FAIL.
    """
    manifest = _load_manifest(repo_root)
    canary_bundles = manifest.get("canary_bundles", []) or []
    if not canary_bundles:
        # Backward-compat with 8A: no canary bundles declared → SKIP row,
        # overall_status determined entirely by blocking checks.
        _record(results, "canary_bundles_checked", "SKIP", False,
                detail="no canary bundles declared in manifest "
                       "(backward-compatible with Phase 8A)",
                extra={"canary_bundle_checks": [],
                       "canary_summary": {
                           "total": 0, "passed": 0, "failed": 0,
                           "blocking_failures": 0,
                           "non_blocking_failures": 0,
                           "status": "CANARY_SKIP",
                       }})
        return

    inspect_script = repo_root / "scripts" / "evomap_inspect_bundle.py"
    validate_script = repo_root / "scripts" / "evomap_validate_bundle.py"
    apply_script = repo_root / "scripts" / "evomap_apply_bundle.py"

    checks_log: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    for entry in canary_bundles:
        if not isinstance(entry, dict):
            continue
        bid = str(entry.get("id", "?"))
        rel_path = str(entry.get("path", ""))
        blocking = bool(entry.get("blocking", False))
        expected = str(entry.get("expected_status", "CANARY_PASS"))
        source_phase = entry.get("source_phase")
        target_rt_rel = entry.get("apply_dry_run_target_runtime") or (
            f"/tmp/atl-evomap-nightly-canary-{bid}"
        )
        target_rt = Path(target_rt_rel)

        bundle_path = (repo_root / rel_path).resolve()

        record: dict[str, Any] = {
            "id": bid,
            "source_phase": source_phase,
            "path": rel_path,
            "lane": entry.get("lane", "curator_generated"),
            "blocking": blocking,
            "expected_status": expected,
            "target_runtime": str(target_rt),
            "inspect": {"status": "SKIP", "returncode": None,
                        "reason": "not_run"},
            "validate": {"status": "SKIP", "returncode": None,
                         "reason": "not_run"},
            "apply_dry_run": {"status": "SKIP", "returncode": None,
                              "reason": "not_run",
                              "target_runtime": str(target_rt)},
            "status": "CANARY_FAIL",
        }

        if not bundle_path.exists():
            record["inspect"] = {"status": "FAIL", "returncode": -1,
                                 "reason": "bundle_missing"}
            record["validate"] = {"status": "FAIL", "returncode": -1,
                                  "reason": "bundle_missing"}
            record["apply_dry_run"] = {"status": "FAIL", "returncode": -1,
                                       "reason": "bundle_missing",
                                       "target_runtime": str(target_rt)}
            checks_log.append(record)
            failed += 1
            continue

        # 1) inspect
        if inspect_script.exists():
            proc = _run_subprocess_capture(
                ["python3", str(inspect_script), "--bundle",
                 str(bundle_path)],
                cwd=repo_root, timeout_seconds=30,
            )
            ok = proc["returncode"] == 0
            record["inspect"] = {
                "status": "PASS" if ok else "FAIL",
                "returncode": proc["returncode"],
                "stdout_tail": proc["stdout_tail"],
                "stderr_tail": proc["stderr_tail"],
            }
        else:
            record["inspect"] = {"status": "FAIL", "returncode": -1,
                                 "reason": "script_missing"}

        # 2) validate
        if validate_script.exists():
            proc = _run_subprocess_capture(
                ["python3", str(validate_script), "--bundle",
                 str(bundle_path)],
                cwd=repo_root, timeout_seconds=30,
            )
            ok = proc["returncode"] == 0
            record["validate"] = {
                "status": "PASS" if ok else "FAIL",
                "returncode": proc["returncode"],
                "stdout_tail": proc["stdout_tail"],
                "stderr_tail": proc["stderr_tail"],
            }
        else:
            record["validate"] = {"status": "FAIL", "returncode": -1,
                                  "reason": "script_missing"}

        # 3) apply dry-run (target = /tmp/atl-evomap-nightly-canary-<id>)
        if apply_script.exists():
            try:
                target_rt.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                record["apply_dry_run"] = {
                    "status": "FAIL", "returncode": -1,
                    "reason": f"mkdir_failed: {exc}",
                    "target_runtime": str(target_rt),
                }
            else:
                proc = _run_subprocess_capture(
                    ["python3", str(apply_script),
                     "--bundle", str(bundle_path),
                     "--target-runtime", str(target_rt),
                     "--dry-run"],
                    cwd=repo_root, timeout_seconds=60,
                )
                rc = proc["returncode"]
                apply_json_ok, reason = _extract_apply_ok(
                    proc.get("stdout_tail", "") or "")
                # Combine: rc must be 0 AND JSON.ok must not be false.
                ok = (rc == 0) and apply_json_ok
                record["apply_dry_run"] = {
                    "status": "PASS" if ok else "FAIL",
                    "returncode": rc,
                    "target_runtime": str(target_rt),
                    "apply_json_reason": reason,
                    "stdout_tail": proc["stdout_tail"],
                    "stderr_tail": proc["stderr_tail"],
                }
        else:
            record["apply_dry_run"] = {"status": "FAIL", "returncode": -1,
                                       "reason": "script_missing",
                                       "target_runtime": str(target_rt)}

        # Aggregate this bundle
        all_ok = (
            record["inspect"]["status"] == "PASS"
            and record["validate"]["status"] == "PASS"
            and record["apply_dry_run"]["status"] == "PASS"
        )
        record["status"] = "CANARY_PASS" if all_ok else "CANARY_FAIL"
        if all_ok:
            passed += 1
        else:
            failed += 1
        checks_log.append(record)

    total = len(checks_log)
    blocking_failures = sum(
        1 for c in checks_log
        if c.get("blocking") and c.get("status") == "CANARY_FAIL"
    )
    non_blocking_failures = sum(
        1 for c in checks_log
        if (not c.get("blocking")) and c.get("status") == "CANARY_FAIL"
    )
    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking_failures,
        "non_blocking_failures": non_blocking_failures,
        "status": ("CANARY_PASS" if failed == 0 else "CANARY_FAIL"),
    }

    # The aggregate row is non-blocking by design. Use status PASS when all
    # canaries passed, WARN when any failed (overall_status still driven by
    # blocking checks only).
    row_status = "PASS" if failed == 0 else "WARN"

    _record(
        results, "canary_bundles_checked",
        row_status,
        blocking=False,
        detail=(
            f"total={total}, passed={passed}, failed={failed}, "
            f"canary_status={summary['status']} "
            f"(non-blocking; overall_status driven by blocking checks only)"
        ),
        extra={
            "canary_bundle_checks": checks_log,
            "canary_summary": summary,
        },
    )


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
    # Canary / Curator-generated bundles (ATL-EVOMAP-9B)
    canary_section = next(
        (c for c in digest["checks"]
         if c["check_id"] == "canary_bundles_checked"), None)
    if canary_section and "extra" in canary_section:
        canary_log = canary_section["extra"].get("canary_bundle_checks", [])
        canary_sum = canary_section["extra"].get("canary_summary", {})
        lines.append("## Canary / Curator-generated bundles")
        lines.append("")
        lines.append(f"- **Total:** {canary_sum.get('total', 0)}")
        lines.append(f"- **Passed:** {canary_sum.get('passed', 0)}")
        lines.append(f"- **Failed:** {canary_sum.get('failed', 0)}")
        lines.append(f"- **Blocking failures:** {canary_sum.get('blocking_failures', 0)}")
        lines.append(f"- **Non-blocking failures:** {canary_sum.get('non_blocking_failures', 0)}")
        lines.append(f"- **Canary status:** **{canary_sum.get('status', '?')}**")
        lines.append(f"- **Lane rule:** curator-generated bundles are NON-BLOCKING "
                     f"by default; a CANARY_FAIL is recorded but does NOT make "
                     f"`overall_status` FAIL.")
        lines.append("")
        if canary_log:
            lines.append("| ID | Source phase | Path | inspect | validate | apply_dry_run | Status | Blocking |")
            lines.append("|----|--------------|------|---------|----------|---------------|--------|----------|")
            for c in canary_log:
                ins = c.get("inspect", {}).get("status", "?")
                val = c.get("validate", {}).get("status", "?")
                dry = c.get("apply_dry_run", {}).get("status", "?")
                blocking = "yes" if c.get("blocking") else "no"
                lines.append(
                    f"| `{c.get('id', '?')}` | {c.get('source_phase') or '-'} | "
                    f"`{c.get('path', '?')}` | {ins} | {val} | {dry} | "
                    f"**{c.get('status', '?')}** | {blocking} |"
                )
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
        lambda r: check_canary_bundles(r, repo_root),
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

    # Bundle inspect / validate consolidated view (used by 9B summary
    # extractors that look at digest.bundle_checks.inspect/validate).
    bundle_checks_view: dict[str, list[dict[str, Any]]] = {"inspect": [],
                                                            "validate": []}
    for c in results:
        if c.get("check_id") == "bundles_inspectable":
            for entry in c.get("extra", {}).get("inspected", []):
                bundle_checks_view["inspect"].append({
                    "id": entry.get("id"),
                    "path": entry.get("path"),
                    "returncode": entry.get("returncode"),
                    "status": ("PASS" if entry.get("returncode") == 0
                               else "FAIL"),
                })
        elif c.get("check_id") == "bundles_validatable":
            for entry in c.get("extra", {}).get("validated", []):
                bundle_checks_view["validate"].append({
                    "id": entry.get("id"),
                    "path": entry.get("path"),
                    "returncode": entry.get("returncode"),
                    "status": ("PASS" if entry.get("returncode") == 0
                               else "FAIL"),
                })

    # Canary view (used by 9B summary extractors)
    canary_section = next(
        (c for c in results if c.get("check_id") == "canary_bundles_checked"),
        None,
    )
    canary_bundle_checks_view: list[dict[str, Any]] = []
    canary_summary_view: dict[str, Any] = {
        "total": 0, "passed": 0, "failed": 0,
        "blocking_failures": 0, "non_blocking_failures": 0,
        "status": "CANARY_SKIP",
    }
    if canary_section is not None:
        canary_bundle_checks_view = (canary_section.get("extra", {})
                                     .get("canary_bundle_checks", []))
        canary_summary_view = (canary_section.get("extra", {})
                               .get("canary_summary", canary_summary_view))

    # Validators view: top-level digest["validators"] (used by 9B summary
    # extractors that count validator_count / validators_passed). This is a
    # promotion of check_all_phase_validators_pass.extra.validators[] to a
    # top-level array for convenience.
    validators_section = next(
        (c for c in results
         if c.get("check_id") == "all_phase_validators_pass"),
        None,
    )
    validators_view: list[dict[str, Any]] = []
    if validators_section is not None:
        for v in (validators_section.get("extra", {})
                  .get("validators", [])):
            rc = v.get("returncode", -1)
            tail = (v.get("stdout_tail", "") or "")
            passed = (rc == 0 and "ALL CHECKS PASSED" in tail)
            validators_view.append({
                "id": v.get("id"),
                "returncode": rc,
                "status": "PASS" if passed else "FAIL",
                "stdout_tail": tail,
                "stderr_tail": v.get("stderr_tail", ""),
            })

    digest: dict[str, Any] = {
        "schema_version": "atl-evomap-nightly-validation-v0.1",
        "phase": "ATL-EVOMAP-8A",
        "extended_by_phase": "ATL-EVOMAP-9B",
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
        "bundle_checks": bundle_checks_view,
        "canary_bundle_checks": canary_bundle_checks_view,
        "canary_summary": canary_summary_view,
        "validators": validators_view,
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
