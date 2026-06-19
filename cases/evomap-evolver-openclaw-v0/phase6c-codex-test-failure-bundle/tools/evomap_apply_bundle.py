#!/usr/bin/env python3
"""
evomap_apply_bundle.py

Apply a portable bundle to a target runtime.

Stdlib only. NO network. NO Hub. NO evolver calls. NO publish. NO --approve.
NO solidify. NO secrets. The tool ONLY writes 3 required + 3 optional files
plus bare + (optional) domain memory signals.

Default mode is --dry-run. Real writes require explicit --yes.

Usage:
  # Default (Phase 5/6A/6B behavior): inject 5 generic bare signals only.
  python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --dry-run
  python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --yes

  # Phase 7A: also inject domain-specific signals (extracted from a bundle
  # JSON's gene.signals_match and capsule.trigger). Filtering is enforced
  # (alnum+`_:+-.`, length 1-120, no dangerous / pollution signals, no
  # credential-like patterns, no 12+ digit recipient-like IDs).
  python3 scripts/evomap_apply_bundle.py \
      --bundle <bundle.json> \
      --inject-signals-from <bundle-or-summary.json> \
      --target-runtime <path> --dry-run
  python3 scripts/evomap_apply_bundle.py \
      --bundle <bundle.json> \
      --inject-signals-from <bundle-or-summary.json> \
      --target-runtime <path> --yes

Behavior:
  - Without --yes, defaults to --dry-run (refuses to write).
  - --dry-run: prints the planned writes, does NOT touch the filesystem.
  - --yes: writes the planned files to the target runtime.
  - Target must exist as a directory (will be checked). If not a git repo, warns but allows.
  - Existing genes.json / capsules.json: same id is overwritten/replaced (id-based dedup).
  - memory_graph.jsonl: clean bare + (optional) domain signals APPENDED to
    existing file (or created). Domain signals are only added when
    --inject-signals-from is supplied and contains extractable signals.
  - Optional files: events.jsonl / failed_capsules.json / candidates.jsonl reset to empty.

Hard boundaries (enforced):
  - No A2A_HUB_URL touched.
  - No real config mutation outside the target runtime's .evolver/ + memory/evolution/.
  - No secrets written (the bundle was pre-validated by evomap_validate_bundle.py).
  - No evolver run/review invoked.
  - No --approve / --solidify / publish.
  - No 12+ digit recipient-like IDs, no Telegram credential-like patterns,
    no Authorization headers, no API key prefixes, no private keys are ever
    written to memory_graph.jsonl.
  - No ux/pollution signals (consecutive_failure*, evolution_saturation,
    explore_opportunity, memory_missing, hub_search_miss_*, user_feature_request)
    are injected, even if present in the source bundle.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# 5 clean bare signals to inject (Phase 5 baseline; identical to Phases 4A/4B/4C).
# origin = "openclaw_signal_detector" (Phase 5 lineage) / preserved for backward
# compatibility with existing parsers and Phase 5/6A/6B validators.
CLEAN_BARE_SIGNALS = [
    ("tool_bypass", 0.85, "Detected exec invocation without prior read on .md file"),
    ("repeated_tool_usage", 0.7, "Same read+edit+search pattern repeated 3x"),
    ("protocol_drift", 0.9, "Detected sed -i usage forbidden by OpenClaw protocol"),
    ("session_context", 0.6, "Session has multiple file ops requiring tool discipline"),
    ("repo_context", 0.65, "Repo is ai-tool-test-lab, evomap-evolver-openclaw-v0 case"),
]


# Dangerous / pollution signals that must NEVER be written into
# memory_graph.jsonl by this tool, even if they appear in the source bundle.
# These come from evolver's own internal score_ranked / saturation logic and
# are not domain signals; including them would re-create the very pollution
# Phase 5/6A/6B worked to keep out.
DANGEROUS_SIGNALS = {
    "user_feature_request",
    "consecutive_failure",
    "consecutive_failure_streak",
    "high_failure_ratio",
    "stable_success_plateau",
    "evolution_saturation",
    "explore_opportunity",
    "memory_missing",
    "hub_search_miss_with_problem",
    "hub_search_miss",
    "hub_unavailable",
    "no_hub_url",
    "no_hub_match",
    "validation_skipped",
    "approval_skipped",
    "publish_skipped",
    "credits_zero",
    "atp_autobuy_off",
    "loop_disabled",
    "validator_disabled",
    "dry_run_default",
}

# Words that look like dangerous or credential-related strings; if a signal
# name contains one of these substrings, reject it.
DANGEROUS_SUBSTRINGS = (
    "token", "secret", "cookie", "authorization", "auth", "private_key",
    "api_key", "apikey", "bearer", "password", "passwd", "ssh-rsa", "ssh-ed25519",
)

# Credential-like patterns (defense in depth: even if a signal somehow passes
# the dangerous-substring check, these regexes will catch it).
# Use the (?i) inline flag at the START of the pattern (Python 3.12+ requires
# global flags at position 0). For the "authorization" subpattern we use the
# IGNORECASE flag at compile time.
CREDENTIAL_PATTERN = re.compile(
    r"(?i)"
    r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b"
    r"|authorization\s*[:=]\s*[A-Za-z0-9_\-\.=]{16,}"
    r"|\b(sk-[A-Za-z0-9]{16,}|sk_live_[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,})\b"
    r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|\b\d{12,}\b"
)

# Allowed characters in a signal name: alphanumeric, underscore, colon, dot,
# hyphen. Colon allows namespaced names like "missing_env_var:MODEL_PROVIDER"
# or "proxy_mismatch:sendmessage-sendvoice".
ALLOWED_SIGNAL_CHARS = re.compile(r"^[A-Za-z0-9_:\-\.]{1,120}$")


def _validate_signal_name(s: str) -> tuple[bool, str]:
    """Return (is_valid, reason_if_invalid)."""
    if not isinstance(s, str):
        return False, "not a string"
    if s in DANGEROUS_SIGNALS:
        return False, f"dangerous_signal:{s}"
    if not ALLOWED_SIGNAL_CHARS.match(s):
        return False, "invalid_chars_or_length"
    low = s.lower()
    for bad in DANGEROUS_SUBSTRINGS:
        if bad in low:
            return False, f"contains_dangerous_substring:{bad}"
    if CREDENTIAL_PATTERN.search(s):
        return False, "credential_like_pattern"
    return True, "ok"


def _make_bare_memory_events(target_gene_id: str, ts_base: float = 1718700001.0) -> list[str]:
    """Phase 5 baseline: 5 clean bare signals with the legacy origin name."""
    return [
        json.dumps({
            "type": "MemoryGraphEvent",
            "ts": ts_base + i,
            "signal": sig,
            "origin": "openclaw_signal_detector",
            "weight": weight,
            "context": ctx,
            "mutation": {
                "target": f"gene:{target_gene_id}",
                "action": "select",
            },
        }, ensure_ascii=False)
        for i, (sig, weight, ctx) in enumerate(CLEAN_BARE_SIGNALS)
    ]


def _make_domain_memory_events(
    signals: list[str],
    target_gene_id: str,
    ts_base: float,
) -> tuple[list[str], list[dict]]:
    """Build MemoryGraphEvent lines for domain signals.

    Returns (lines, rejected_records). Each rejected record is a dict with
    keys: signal, reason.
    """
    lines = []
    rejected = []
    ts = ts_base
    for sig in signals:
        ok, reason = _validate_signal_name(sig)
        if not ok:
            rejected.append({"signal": sig, "reason": reason})
            continue
        lines.append(json.dumps({
            "type": "MemoryGraphEvent",
            "ts": ts,
            "signal": sig,
            "origin": "evomap_apply_bundle:domain_from_bundle",
            "weight": 0.8,
            "context": f"domain-specific signal injected from bundle (gene={target_gene_id})",
            "mutation": {
                "target": f"gene:{target_gene_id}",
                "action": "select",
            },
        }, ensure_ascii=False))
        ts += 1
    return lines, rejected


def _extract_signals_from_bundle(bundle: dict) -> list[str]:
    """Extract candidate domain signal names from a portable bundle.

    Looks at:
      - bundle["gene"]["signals_match"]
      - bundle["capsule"]["trigger"]
    Preserves order, de-duplicates.
    """
    raw = []
    gene = bundle.get("gene") or {}
    capsule = bundle.get("capsule") or {}
    if isinstance(gene.get("signals_match"), list):
        raw.extend(x for x in gene["signals_match"] if isinstance(x, str))
    if isinstance(capsule.get("trigger"), list):
        raw.extend(x for x in capsule["trigger"] if isinstance(x, str))
    seen = set()
    out = []
    for s in raw:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _dedup_by_id(items: list, id_field: str = "id") -> list:
    """Replace items with same id, keep last occurrence."""
    seen = {}
    for it in items:
        if isinstance(it, dict) and id_field in it:
            seen[it[id_field]] = it
    return list(seen.values())


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def plan_apply(
    bundle: dict,
    target: Path,
    domain_signals: list[str] | None = None,
) -> dict:
    """Compute planned writes. No filesystem mutation.

    `domain_signals` is the list of candidate domain signal names (already
    extracted from --inject-signals-from) that we will filter and append.
    """
    gene = bundle.get("gene") or {}
    capsule = bundle.get("capsule") or {}
    target_gene_id = gene.get("id", "")

    gene_id = target_gene_id or "<unknown>"
    cap_id = (capsule.get("id") or "<unknown>")

    # existing gene/capsule in target if present
    existing_genes = []
    existing_capsules = []
    target_genes_path = target / ".evolver" / "gep" / "genes.json"
    target_capsules_path = target / ".evolver" / "gep" / "capsules.json"
    if target_genes_path.is_file():
        try:
            existing_genes = json.loads(target_genes_path.read_text()).get("genes", [])
        except Exception:
            existing_genes = []
    if target_capsules_path.is_file():
        try:
            existing_capsules = json.loads(target_capsules_path.read_text()).get("capsules", [])
        except Exception:
            existing_capsules = []

    new_genes_list = _dedup_by_id([*existing_genes, gene]) if gene else existing_genes
    new_capsules_list = _dedup_by_id([*existing_capsules, capsule]) if capsule else existing_capsules

    # Build memory_graph.jsonl lines: bare + (optional) domain.
    bare_events = _make_bare_memory_events(gene_id)
    bare_signal_names = [s for s, _, _ in CLEAN_BARE_SIGNALS]

    domain_lines = []
    domain_rejected = []
    domain_kept = []
    if domain_signals is not None:
        domain_lines, domain_rejected = _make_domain_memory_events(
            domain_signals, gene_id, ts_base=1718700200.0
        )
        domain_kept = [
            json.loads(l)["signal"] for l in domain_lines
        ]

    signal_injection_mode = (
        "generic_plus_domain_from_bundle"
        if domain_signals is not None
        else "generic_only"
    )

    all_lines = [*bare_events, *domain_lines]

    plan = {
        "target": str(target),
        "is_git_repo": _is_git_repo(target),
        "gene_id": gene_id,
        "capsule_id": cap_id,
        "signal_injection_mode": signal_injection_mode,
        "generic_signals": bare_signal_names,
        "domain_signals": domain_kept,
        "domain_signals_rejected": domain_rejected,
        "writes": {
            str(target_genes_path): {
                "action": "overwrite",
                "schema_version": "1.6.0",
                "genes": new_genes_list,
            },
            str(target_capsules_path): {
                "action": "overwrite",
                "schema_version": "1.6.0",
                "capsules": new_capsules_list,
            },
            str(target / "memory" / "evolution" / "memory_graph.jsonl"): {
                "action": "append",
                "lines": all_lines,
            },
            str(target / ".evolver" / "gep" / "events.jsonl"): {
                "action": "reset",
                "content": "",
            },
            str(target / ".evolver" / "gep" / "failed_capsules.json"): {
                "action": "reset",
                "content": "[]\n",
            },
            str(target / ".evolver" / "gep" / "candidates.jsonl"): {
                "action": "reset",
                "content": "",
            },
        },
        "summary": {
            "existing_gene_count": len(existing_genes),
            "existing_capsule_count": len(existing_capsules),
            "new_gene_count": len(new_genes_list),
            "new_capsule_count": len(new_capsules_list),
            "memory_graph_signals_added": len(all_lines),
            "memory_graph_generic_signals": len(bare_signal_names),
            "memory_graph_domain_signals": len(domain_kept),
            "memory_graph_domain_rejected": len(domain_rejected),
        },
    }
    return plan


def execute_plan(plan: dict) -> dict:
    """Execute the planned writes. Returns a log of what was actually written."""
    log = {"writes_executed": [], "errors": []}
    for path_str, info in plan["writes"].items():
        p = Path(path_str)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            if info["action"] == "overwrite":
                payload = {
                    "schema_version": info.get("schema_version", "1.6.0"),
                    "genes" if "genes" in info else "capsules": (
                        info["genes"] if "genes" in info else info["capsules"]
                    ),
                }
                p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
            elif info["action"] == "append":
                with p.open("a") as f:
                    for line in info["lines"]:
                        f.write(line + "\n")
            elif info["action"] == "reset":
                p.write_text(info["content"])
            log["writes_executed"].append({"path": str(p), "action": info["action"]})
        except Exception as e:
            log["errors"].append({"path": str(p), "error": str(e)})
    return log


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply a portable OpenClaw Evolution bundle to a target runtime (stdlib only, no evolver, no Hub, no publish)"
    )
    parser.add_argument("--bundle", type=Path, required=True, help="Path to the portable bundle JSON file")
    parser.add_argument("--target-runtime", type=Path, required=True, help="Path to the target isolated runtime directory")
    parser.add_argument(
        "--inject-signals-from",
        type=Path,
        default=None,
        help=(
            "Optional path to a bundle JSON whose gene.signals_match and "
            "capsule.trigger are extracted and injected (after filtering) as "
            "domain-specific memory signals. Without this flag, only the 5 "
            "Phase 5 generic bare signals are written (backward-compatible)."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without touching the filesystem")
    parser.add_argument("--yes", action="store_true", help="Actually write the planned files (required for non-dry-run)")
    args = parser.parse_args()

    # Default: dry-run if neither --dry-run nor --yes is given
    if not args.dry_run and not args.yes:
        args.dry_run = True

    if not args.bundle.is_file():
        print(json.dumps({"ok": False, "reason": f"bundle file not found: {args.bundle}"}, indent=2))
        return 1

    try:
        bundle = json.loads(args.bundle.read_text())
    except Exception as e:
        print(json.dumps({"ok": False, "reason": f"bundle is not valid JSON: {e}"}, indent=2))
        return 1

    if not args.target_runtime.is_dir():
        print(json.dumps({"ok": False, "reason": f"target runtime is not a directory: {args.target_runtime}"}, indent=2))
        return 1

    # If --inject-signals-from is supplied, load the source JSON (may equal
    # --bundle) and extract candidate domain signals. Filtering happens inside
    # plan_apply().
    domain_signals: list[str] | None = None
    if args.inject_signals_from is not None:
        if not args.inject_signals_from.is_file():
            print(json.dumps({
                "ok": False,
                "reason": f"--inject-signals-from file not found: {args.inject_signals_from}",
            }, indent=2))
            return 1
        try:
            source = json.loads(args.inject_signals_from.read_text())
        except Exception as e:
            print(json.dumps({
                "ok": False,
                "reason": f"--inject-signals-from is not valid JSON: {e}",
            }, indent=2))
            return 1
        domain_signals = _extract_signals_from_bundle(source)

    plan = plan_apply(bundle, args.target_runtime, domain_signals=domain_signals)

    if args.dry_run:
        print(json.dumps({"ok": True, "mode": "dry-run", "plan": plan}, indent=2, ensure_ascii=False))
        return 0

    # Real write
    if not args.yes:
        print(json.dumps({"ok": False, "reason": "real write requires --yes"}, indent=2))
        return 1

    log = execute_plan(plan)
    print(json.dumps({
        "ok": not log["errors"],
        "mode": "applied",
        "plan_summary": plan["summary"],
        "signal_injection_mode": plan["signal_injection_mode"],
        "generic_signals": plan["generic_signals"],
        "domain_signals": plan["domain_signals"],
        "domain_signals_rejected": plan["domain_signals_rejected"],
        "log": log,
    }, indent=2, ensure_ascii=False))
    return 0 if not log["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
