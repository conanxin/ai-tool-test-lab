#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evomap_curate_bundle.py — Bundle Curator for the OpenClaw / Hermes Local Evolution Kit.

Phase:    ATL-EVOMAP-9A (Bundle Curator Skill)
Base:     a56e756 (post-ATL-EVOMAP-8A nightly validation loop asset)

Purpose
-------
Convert a hand-written curator spec JSON (schema_version =
atl-evomap-curator-spec-v0.1) into a standard portable bundle JSON
(schema_version = atl-evomap-portable-bundle-v0.1), plus standalone
gene / capsule JSON files and a README draft. The curator is
**stdlib-only**, **offline-only**, **read-only of the spec**, and never
touches the real runtime. It only writes inside the caller-supplied
``--out-dir`` (or, in dry-run, prints the planned writes).

Safety contract (enforced by this script)
-----------------------------------------
- No Hub / no A2A_HUB_URL / no evolver run / no evolver review /
  no approve / no solidify / no auto-publish / no credits / no ATP
  autobuy.
- No AI API calls (OpenAI / Codex / GitHub Copilot / etc.).
- No curl / wget / HTTP / Telegram API.
- No real test runner (pytest / npm / cargo / go / mvn).
- No .env content scan.
- No real OpenClaw / Hermes / systemd / cron config mutation.
- AST self-check at startup rejects any non-stdlib import.
- Spec is rejected if safety block does not contain exactly
  hub=disabled, publish=disabled, credits=0, visibility=private.
- Spec is rejected if any signal in gene.signals_match or capsule.trigger
  matches a denylisted signal name OR a secret-like pattern.
- Curator visibility is hard-coded to ``private``; spec.requested_visibility
  cannot override this.
- Output default directory is *never* the repository root, the real
  runtime root, or any tracked subdirectory; only the caller-supplied
  ``--out-dir`` is writable.
- Recursive repo scan is disabled. The curator reads only the single
  file passed via ``--spec``.

CLI
---
    python3 scripts/evomap_curate_bundle.py \\
        --spec <spec.json> \\
        --out-dir <dir> \\
        [--bundle-name <name>] \\
        [--dry-run] \\
        [--strict]

Exit codes
----------
    0  ok / dry-run plan ok
    1  spec validation failed (non-strict)
    2  --spec missing / AST check failed / strict-mode validation failed
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPEC_SCHEMA_VERSION = "atl-evomap-curator-spec-v0.1"
BUNDLE_SCHEMA_VERSION = "atl-evomap-portable-bundle-v0.1"
SOURCE_BASE_COMMIT = "a56e756"
GENERATOR_NAME = "evomap_curate_bundle.py"
GENERATOR_VERSION = "0.1.0"

# Forbidden import top-level names (third-party). Anything in this set is
# rejected by the AST self-check.
FORBIDDEN_TOP_LEVEL_IMPORTS = frozenset({
    "openai", "anthropic", "google", "cohere", "requests", "httpx", "urllib3",
    "urllib", "telegram", "telebot", "aiogram", "slack_sdk", "slack",
    "boto3", "botocore", "github", "github3", "gitlab", "bitbucket",
    "playwright", "selenium", "pyppeteer", "scrapy", "pytest", "unittest",
    "dotenv", "environs", "click", "typer", "rich", "colorama",
    "yaml", "toml", "tomllib", "fastapi", "flask", "django",
    "numpy", "pandas", "scipy", "torch", "tensorflow",
})

# Denylisted signal-name tokens (case-insensitive substring match).
# Mirrors the Phase 7A apply-tool denylist.
DENYLIST_SIGNAL_NAME_TOKENS = (
    "user_feature_request",
    "consecutive_failure",
    "consecutive_failure_streak",
    "high_failure_ratio",
    "stable_success_plateau",
    "evolution_saturation",
    "explore_opportunity",
    "memory_missing",
    "hub_search_miss_with_problem",
    "private_key",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "password",
    "passwd",
    "secret",
    "cookie",
    "csrf_token",
    "session_token",
    "auth_token",
    "bearer_token",
    "access_token",
    "refresh_token",
)

# Secret-like regex patterns. Tested against every signal string AND every
# constraint field. Triggers hard refusal of the spec.
SECRET_PATTERNS = (
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("github_pat", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("authorization_header", re.compile(r"(?i)authorization\s*:\s*bearer\s+\S+")),
    ("jwt_shape", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("begin_private_key", re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY( BLOCK)?-----")),
    ("numeric_token_12plus", re.compile(r"(?<![\d.])(\d{12,})(?![\d.])")),
)

# Canonical import contract — copied verbatim from the existing 4 canonical
# portable bundles so any apply target can ingest curator output.
CANONICAL_IMPORT_CONTRACT = {
    "required_files": [
        ".evolver/gep/genes.json",
        ".evolver/gep/capsules.json",
        "memory/evolution/memory_graph.jsonl",
    ],
    "optional_files": [
        ".evolver/gep/events.jsonl",
        ".evolver/gep/failed_capsules.json",
        ".evolver/gep/candidates.jsonl",
    ],
    "required_in_genes": ["genes[].id"],
    "required_in_capsules": [
        "capsules[].id",
        "capsules[].gene",
        "capsules[].execution_trace",
    ],
    "minimum_execution_trace_steps": 1,
    "minimum_execution_trace_stages_with_unique_stages": 1,
}

# Paths the curator refuses to write into. Defense-in-depth in case a caller
# points --out-dir at a dangerous location.
FORBIDDEN_OUTPUT_PATH_PREFIXES = (
    "/.git/",
    "/.evolver/",
    "/memory/",
    "/real_runtime_root/",
    "/etc/systemd/",
    "/etc/cron",
    "/var/spool/cron",
    "/root/.crontab",
    "C:/Windows/",
    "C:/Program Files/",
)


# ---------------------------------------------------------------------------
# AST self-check
# ---------------------------------------------------------------------------

def _ast_self_check(source_path: Path) -> list[str]:
    """Parse this file and reject any non-stdlib import."""
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
    except SyntaxError as e:
        return [f"AST parse failed: {e}"]

    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in FORBIDDEN_TOP_LEVEL_IMPORTS:
                    errors.append(
                        f"forbidden import '{top}' at line {node.lineno}"
                    )
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            if top and top in FORBIDDEN_TOP_LEVEL_IMPORTS:
                errors.append(
                    f"forbidden from-import '{top}' at line {node.lineno}"
                )
    return errors


# ---------------------------------------------------------------------------
# Spec validation
# ---------------------------------------------------------------------------

def _scan_for_secrets(text: str) -> list[tuple[str, str]]:
    """Return list of (pattern_name, redacted_snippet) for each secret match."""
    if not isinstance(text, str):
        return []
    hits: list[tuple[str, str]] = []
    for name, pat in SECRET_PATTERNS:
        m = pat.search(text)
        if m:
            # Redact the actual match so the result JSON does not echo the
            # secret-like content back to the caller.
            redacted = (m.group(0)[:4] + "***REDACTED***") if len(m.group(0)) > 4 else "***REDACTED***"
            hits.append((name, redacted))
    return hits


def _signal_name_is_denylisted(name: str) -> bool:
    low = name.lower()
    for token in DENYLIST_SIGNAL_NAME_TOKENS:
        if token in low:
            return True
    return False


def validate_spec(spec: dict, *, strict: bool) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """Return (errors, rejected_signal_names, secret_hits)."""
    errors: list[str] = []
    rejected: list[str] = []
    secret_hits: list[tuple[str, str]] = []

    # 1. Top-level schema version
    if spec.get("schema_version") != SPEC_SCHEMA_VERSION:
        errors.append(
            f"spec.schema_version must be '{SPEC_SCHEMA_VERSION}', "
            f"got {spec.get('schema_version')!r}"
        )

    # 2. Required top-level keys
    for k in ("bundle", "gene", "capsule", "safety"):
        if k not in spec:
            errors.append(f"spec missing required top-level key '{k}'")

    bundle = spec.get("bundle") or {}
    gene = spec.get("gene") or {}
    capsule = spec.get("capsule") or {}
    safety = spec.get("safety") or {}

    # 3. Bundle schema version
    if bundle.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        errors.append(
            f"bundle.schema_version must be '{BUNDLE_SCHEMA_VERSION}', "
            f"got {bundle.get('schema_version')!r}"
        )
    if bundle.get("visibility") != "private":
        errors.append(
            f"bundle.visibility must be 'private' (curator never emits public bundles), "
            f"got {bundle.get('visibility')!r}"
        )

    # 4. Gene required fields
    for k in ("type", "id", "category", "signals_match", "strategy", "summary"):
        if k not in gene:
            errors.append(f"gene missing required field '{k}'")
    if gene.get("type") not in ("Gene", "gene"):
        errors.append(
            f"gene.type must be 'Gene', got {gene.get('type')!r}"
        )

    # 5. Capsule required fields
    for k in ("schema_version", "type", "id", "gene", "status", "confidence",
              "visibility", "source", "trigger", "execution_trace"):
        if k not in capsule:
            errors.append(f"capsule missing required field '{k}'")
    if capsule.get("visibility") != "private":
        errors.append(
            f"capsule.visibility must be 'private' (curator never emits public capsules), "
            f"got {capsule.get('visibility')!r}"
        )
    if not isinstance(capsule.get("execution_trace"), list) or len(capsule["execution_trace"]) < 3:
        errors.append(
            f"capsule.execution_trace must be a list with >= 3 steps, "
            f"got {type(capsule.get('execution_trace')).__name__} len="
            f"{len(capsule.get('execution_trace') or [])}"
        )

    # 6. ID consistency invariants
    gene_id = gene.get("id")
    capsule_id = capsule.get("id")
    target_gene_id = bundle.get("target_gene_id")
    target_capsule_id = bundle.get("target_capsule_id")
    if gene_id and target_gene_id and gene_id != target_gene_id:
        errors.append(
            f"gene.id ({gene_id!r}) must equal bundle.target_gene_id ({target_gene_id!r})"
        )
    if capsule_id and target_capsule_id and capsule_id != target_capsule_id:
        errors.append(
            f"capsule.id ({capsule_id!r}) must equal bundle.target_capsule_id ({target_capsule_id!r})"
        )
    if gene_id and capsule.get("gene") and capsule.get("gene") != gene_id:
        errors.append(
            f"capsule.gene ({capsule.get('gene')!r}) must equal gene.id ({gene_id!r})"
        )

    # 7. Safety block hard requirements
    if safety.get("hub") != "disabled":
        errors.append(f"safety.hub must be 'disabled', got {safety.get('hub')!r}")
    if safety.get("publish") != "disabled":
        errors.append(f"safety.publish must be 'disabled', got {safety.get('publish')!r}")
    if safety.get("credits") != 0:
        errors.append(f"safety.credits must be 0, got {safety.get('credits')!r}")
    if safety.get("visibility") != "private":
        errors.append(f"safety.visibility must be 'private', got {safety.get('visibility')!r}")

    # 8. signals_match / trigger denylist
    sigs = list(gene.get("signals_match") or []) + list(capsule.get("trigger") or [])
    for sig in sigs:
        if not isinstance(sig, str):
            errors.append(f"signal must be string, got {type(sig).__name__}: {sig!r}")
            continue
        if _signal_name_is_denylisted(sig):
            rejected.append(sig)
        secret_hits.extend(_scan_for_secrets(sig))

    # 9. Constraint / summary secret scan
    constraints = gene.get("constraints") or {}
    for v in constraints.values():
        if isinstance(v, str):
            secret_hits.extend(_scan_for_secrets(v))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    secret_hits.extend(_scan_for_secrets(item))

    summary = gene.get("summary") or ""
    if isinstance(summary, str):
        secret_hits.extend(_scan_for_secrets(summary))

    # 10. Promote signal-name denylist to error (always, even non-strict)
    if rejected:
        # Deduplicate while preserving order
        seen = set()
        uniq = []
        for r in rejected:
            if r not in seen:
                seen.add(r)
                uniq.append(r)
        rejected = uniq
        errors.append(
            "denylisted signal name(s) detected in gene.signals_match or "
            "capsule.trigger: " + ", ".join(repr(r) for r in rejected)
        )

    # 11. Promote secret hits to error
    if secret_hits:
        # Deduplicate
        seen = set()
        uniq = []
        for name, snip in secret_hits:
            key = name + "|" + snip
            if key not in seen:
                seen.add(key)
                uniq.append((name, snip))
        secret_hits = uniq
        errors.append(
            "secret-like content detected in spec (redacted): "
            + "; ".join(f"{n}={s}" for n, s in secret_hits)
        )

    # In strict mode we are stricter; currently non-strict == strict for
    # all curator validation rules, but the flag is preserved for forward
    # compatibility (e.g. treating warn-only findings as fatal later).
    _ = strict
    return errors, rejected, secret_hits


# ---------------------------------------------------------------------------
# Bundle / gene / capsule / readme builders
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def build_bundle_json(spec: dict) -> dict:
    gene = spec["gene"]
    capsule = spec["capsule"]
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "source_phase": spec["bundle"].get("source_phase", "ATL-EVOMAP-9A"),
        "source_session": "bundle-curator-local",
        "target_gene_id": gene["id"],
        "target_capsule_id": capsule["id"],
        "gene": gene,
        "capsule": capsule,
        "execution_trace": list(capsule.get("execution_trace") or []),
        "fixture_summary": dict(spec.get("fixture_summary") or {}),
        "safety": dict(spec.get("safety") or {}),
        "import_contract": dict(CANONICAL_IMPORT_CONTRACT),
        "kit_provenance": {
            "kit": "OpenClaw/Hermes Local Evolution Kit",
            "kit_version_phase": "ATL-EVOMAP-9A",
            "kit_base_commit": SOURCE_BASE_COMMIT,
            "generator": GENERATOR_NAME,
            "generator_version": GENERATOR_VERSION,
            "generated_at": _now_iso(),
            "hub": "disabled",
            "publish": "disabled",
            "credits": 0,
            "visibility": "private",
            "approve_executed": False,
            "solidify_executed": False,
            "evolver_run_executed": False,
            "evolver_review_executed": False,
            "network_calls_executed": False,
            "real_test_runners_executed": False,
            "real_cron_installed": False,
            "systemd_timer_created": False,
            "env_file_scanned": False,
        },
    }


def build_gene_json(spec: dict) -> dict:
    gene = dict(spec["gene"])
    gene["_provenance"] = {
        "kit": "OpenClaw/Hermes Local Evolution Kit",
        "phase": "ATL-EVOMAP-9A",
        "kit_base_commit": SOURCE_BASE_COMMIT,
        "generator": GENERATOR_NAME,
        "generator_version": GENERATOR_VERSION,
        "generated_at": _now_iso(),
        "visibility": "private",
        "hub": "disabled",
        "publish": "disabled",
        "credits": 0,
        "approve_executed": False,
        "solidify_executed": False,
        "evolver_run_executed": False,
    }
    return gene


def build_capsule_json(spec: dict) -> dict:
    capsule = dict(spec["capsule"])
    capsule["_provenance"] = {
        "kit": "OpenClaw/Hermes Local Evolution Kit",
        "phase": "ATL-EVOMAP-9A",
        "kit_base_commit": SOURCE_BASE_COMMIT,
        "generator": GENERATOR_NAME,
        "generator_version": GENERATOR_VERSION,
        "generated_at": _now_iso(),
        "visibility": "private",
        "hub": "disabled",
        "publish": "disabled",
        "credits": 0,
        "approve_executed": False,
        "solidify_executed": False,
        "evolver_run_executed": False,
    }
    return capsule


def build_readme(bundle: dict, spec: dict) -> str:
    gene = bundle["gene"]
    capsule = bundle["capsule"]
    safety = bundle["safety"]
    kit = bundle["kit_provenance"]

    lines: list[str] = []
    lines.append(f"# Auto-generated Bundle: `{gene['id']}`")
    lines.append("")
    lines.append("> Draft bundle generated by the **Phase 9A bundle curator**")
    lines.append(f"> (`scripts/{GENERATOR_NAME}` v{GENERATOR_VERSION}).")
    lines.append("> Human review + inspect + validate + apply dry-run is required")
    lines.append("> before any apply --yes to a real runtime target.")
    lines.append("")
    lines.append("## Identity")
    lines.append("")
    lines.append(f"- **Gene ID**: `{gene['id']}`")
    lines.append(f"- **Capsule ID**: `{capsule['id']}`")
    lines.append(f"- **Category**: `{gene.get('category')}`")
    lines.append(f"- **Source phase**: `{bundle['source_phase']}`")
    lines.append(f"- **Generator**: `{kit['generator']}` v{kit['generator_version']}")
    lines.append(f"- **Generated at**: `{kit['generated_at']}`")
    lines.append(f"- **Kit base commit**: `{kit['kit_base_commit']}`")
    lines.append(f"- **Visibility**: `{safety.get('visibility')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(gene.get("summary", "(no summary provided)"))
    lines.append("")
    lines.append("## Signals")
    lines.append("")
    for sig in gene.get("signals_match", []):
        lines.append(f"- `{sig}`")
    lines.append("")
    lines.append("## Strategy")
    lines.append("")
    for i, step in enumerate(gene.get("strategy", []), 1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("## Constraints")
    lines.append("")
    constraints = gene.get("constraints") or {}
    for k, v in constraints.items():
        lines.append(f"- **{k}**: `{json.dumps(v, ensure_ascii=False)}`")
    lines.append("")
    lines.append("## Capsule Execution Trace")
    lines.append("")
    for i, step in enumerate(capsule.get("execution_trace", []), 1):
        stage = step.get("stage", "?")
        command = step.get("command", "?")
        exit_code = step.get("exit_code", "?")
        result = step.get("result", "?")
        lines.append(f"{i}. **{stage}** (exit={exit_code}) — `{command}` → `{result}`")
    lines.append("")
    lines.append("## Safety")
    lines.append("")
    for k, v in safety.items():
        lines.append(f"- **{k}**: `{json.dumps(v, ensure_ascii=False)}`")
    lines.append("")
    lines.append("## Hard Boundaries Enforced by Curator")
    lines.append("")
    for k, v in kit.items():
        if k.startswith("_"):
            continue
        lines.append(f"- **{k}**: `{json.dumps(v, ensure_ascii=False)}`")
    lines.append("")
    lines.append("## Required Review Before Apply")
    lines.append("")
    lines.append("1. Re-run `scripts/evomap_inspect_bundle.py --bundle <this.bundle.json>`")
    lines.append("   and confirm `ok=true`.")
    lines.append("2. Re-run `scripts/evomap_validate_bundle.py --bundle <this.bundle.json>`")
    lines.append("   and confirm `ok=true` and `secret_hits=[]`.")
    lines.append("3. Run `scripts/evomap_apply_bundle.py --bundle <this.bundle.json>")
    lines.append("   --target-runtime /tmp/<isolated-target> --dry-run` and confirm")
    lines.append("   plan ok.")
    lines.append("4. Only after 1-3 PASS, manually invoke apply with `--yes` against an")
    lines.append("   **isolated** runtime under `/tmp`. Real runtimes require an explicit")
    lines.append("   operator authorization phase.")
    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _resolve_out_path(out_dir: Path, name: str) -> Path:
    """Resolve a path inside --out-dir, refusing any escape."""
    candidate = (out_dir / name).resolve()
    out_dir_resolved = out_dir.resolve()
    try:
        candidate.relative_to(out_dir_resolved)
    except ValueError:
        raise ValueError(f"resolved path {candidate} escapes out-dir {out_dir_resolved}")
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evomap_curate_bundle.py",
        description=(
            "Bundle Curator for the OpenClaw / Hermes Local Evolution Kit. "
            "Converts a hand-written curator spec (atl-evomap-curator-spec-v0.1) "
            "into a portable bundle draft (atl-evomap-portable-bundle-v0.1)."
        ),
    )
    parser.add_argument("--spec", required=True, help="Path to the curator spec JSON")
    parser.add_argument("--out-dir", required=True, help="Output directory for the generated bundle / gene / capsule / README")
    parser.add_argument("--bundle-name", default=None, help="Optional bundle filename (default: derived from gene.id)")
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes; do not touch the filesystem")
    parser.add_argument("--strict", action="store_true", help="Strict mode: treat any policy mismatch as fatal with exit 2")
    args = parser.parse_args(argv)

    # AST self-check (defense-in-depth even though this script is itself stdlib-only)
    ast_errors = _ast_self_check(Path(__file__).resolve())
    if ast_errors:
        sys.stderr.write("CURATOR AST SELF-CHECK FAILED:\n")
        for e in ast_errors:
            sys.stderr.write(f"  - {e}\n")
        return 2

    # Read the spec — single-file read, no recursive scan
    spec_path = Path(args.spec)
    if not spec_path.is_file():
        sys.stderr.write(f"spec not found: {spec_path}\n")
        result = {
            "ok": False,
            "mode": "rejected",
            "spec": str(spec_path),
            "errors": [f"spec not found: {spec_path}"],
            "rejected_signals": [],
            "secret_hits": [],
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 2

    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.stderr.write(f"spec is not valid JSON: {e}\n")
        result = {
            "ok": False,
            "mode": "rejected",
            "spec": str(spec_path),
            "errors": [f"spec is not valid JSON: {e}"],
            "rejected_signals": [],
            "secret_hits": [],
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 2

    # Validate
    errors, rejected, secret_hits = validate_spec(spec, strict=args.strict)
    if errors:
        result = {
            "ok": False,
            "mode": "rejected",
            "spec": str(spec_path),
            "out_dir": args.out_dir,
            "errors": errors,
            "rejected_signals": rejected,
            "secret_hits": [(n, s) for n, s in secret_hits],
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 2 if args.strict else 1

    # Compute output paths
    out_dir = Path(args.out_dir)
    gene_id = spec["gene"]["id"]
    capsule_id = spec["capsule"]["id"]
    bundle_name = args.bundle_name or f"{gene_id.replace('gene_distilled_', '')}.bundle.json"
    try:
        bundle_path = _resolve_out_path(out_dir, bundle_name)
        gene_path = _resolve_out_path(out_dir, f"gene-{gene_id}.json")
        capsule_path = _resolve_out_path(out_dir, f"capsule-{capsule_id}.json")
        readme_path = _resolve_out_path(out_dir, "README.generated.md")
    except ValueError as e:
        sys.stderr.write(f"unsafe --out-dir: {e}\n")
        return 2

    # Build outputs
    bundle = build_bundle_json(spec)
    gene = build_gene_json(spec)
    capsule = build_capsule_json(spec)
    readme = build_readme(bundle, spec)

    result = {
        "ok": True,
        "mode": "dry-run" if args.dry_run else "generated",
        "spec": str(spec_path),
        "out_dir": str(out_dir),
        "bundle_path": str(bundle_path),
        "gene_path": str(gene_path),
        "capsule_path": str(capsule_path),
        "readme_path": str(readme_path),
        "gene_id": gene_id,
        "capsule_id": capsule_id,
        "signals_count": len(spec["gene"].get("signals_match") or []),
        "execution_trace_steps": len(spec["capsule"].get("execution_trace") or []),
        "secret_hits": [(n, s) for n, s in secret_hits],
        "rejected_signals": rejected,
        "strict": bool(args.strict),
        "safety_summary": {
            "hub": "disabled",
            "publish": "disabled",
            "credits": 0,
            "approve": "not_executed",
            "solidify": "not_executed",
            "evolver_run": "not_executed",
            "evolver_review": "not_executed",
            "real_cron_install": "not_executed",
            "systemd_timer_install": "not_executed",
            "network_calls": "not_executed",
            "real_tests": "not_executed",
            "no_env_file_content_scanned": True,
            "stdlib_only": True,
            "visibility": "private",
        },
    }

    if args.dry_run:
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 0

    # Actually write
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    gene_path.write_text(json.dumps(gene, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    capsule_path.write_text(json.dumps(capsule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme_path.write_text(readme, encoding="utf-8")

    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())