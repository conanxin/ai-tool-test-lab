#!/usr/bin/env python3
"""
evomap_cross_bundle_analyze.py — Cross-bundle regression analyzer.

Reads ONLY the 6 fixed files written by `evomap_apply_bundle.py` + the
Evolver CLI inside a single target runtime. Does NOT recursively scan the
repository, does NOT read .env, does NOT use curl/wget/HTTP. Python stdlib
only.

Inputs (all relative to --target-runtime):
  /.evolver/gep/genes.json
  /.evolver/gep/capsules.json
  /memory/evolution/memory_graph.jsonl
  /.evolver/gep/events.jsonl
  /.evolver/gep/failed_capsules.json
  /.evolver/gep/candidates.jsonl

Outputs (JSON to stdout):
  {
    "ok": true,
    "target_runtime": "...",
    "gene_count": 3,
    "capsule_count": 3,
    "memory_graph_lines": 59,
    "distinct_signal_count": 39,
    "gene_ids": [...],
    "capsule_ids": [...],
    "duplicate_gene_ids": [],
    "duplicate_capsule_ids": [],
    "dangerous_signals": [],
    "pollution_signals": [],
    "required_gene_ids_present": true,
    "required_capsule_ids_present": true,
    "required_openclaw_signals_present": true,
    "required_hermes_signals_present": true,
    "required_telegram_signals_present": true,
    "broken_capsule_to_gene_links": [],
    "summary": {...}
  }
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Required Gene IDs (3 canonical bundles)
REQUIRED_GENE_IDS = [
    "gene_distilled_openclaw-tool-use-discipline-bare-compatible",
    "gene_distilled_hermes-systemd-service-recovery",
    "gene_distilled_telegram-message-router-failure",
]

# Required Capsule IDs (3 canonical bundles)
REQUIRED_CAPSULE_IDS = [
    "capsule_openclaw_tool_use_discipline_phase4b",
    "capsule_hermes_systemd_service_recovery_phase6a",
    "capsule_telegram_message_router_failure_phase6b",
]

# Required OpenClaw signals (must all be present)
REQUIRED_OPENCLAW_SIGNALS = [
    "tool_bypass",
    "repeated_tool_usage",
    "protocol_drift",
    "session_context",
    "repo_context",
]

# Required Hermes signals
REQUIRED_HERMES_SIGNALS = [
    "systemd_failure",
    "service_recovery",
    "missing_env_var",
    "missing_env_var:MODEL_PROVIDER",
    "port_not_listening",
    "dropin_env_misconfigured",
]

# Required Telegram signals
REQUIRED_TELEGRAM_SIGNALS = [
    "telegram_failure",
    "message_router_failure",
    "proxy_mismatch",
    "delivery_terminal_missing",
    "sendmessage_timeout",
    "retry_consumed",
    "smoke_not_confirmed",
    "proxy_mismatch:sendmessage-sendvoice",
]

# Dangerous signals (mirror of apply tool's DANGEROUS_SIGNALS, 21 entries)
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

# Pollution signals (separate category, 12-entry subset that mirrors
# bundle.safety.no_pollution_signals language while sharing the same
# content as the dangerous denylist for the user-visible/heuristic set).
POLLUTION_SIGNALS = {
    "user_feature_request",
    "consecutive_failure",
    "consecutive_failure_streak",
    "high_failure_ratio",
    "stable_success_plateau",
    "evolution_saturation",
    "explore_opportunity",
    "hub_search_miss_with_problem",
    "memory_missing",
    "token",
    "secret",
    "cookie",
    "authorization",
    "private_key",
    "api_key",
    "bearer",
    "password",
}

# Long-digit pure-numeric value pattern (12+ digits) — never allowed in
# a signal name (catches recipient-id-like values leaking through)
CREDENTIAL_PATTERN = re.compile(r"^\d{12,}$")


def _normalize_signal(sig):
    """Normalize a signal value. Memory graph events can have signal as
    either a string ("foo") or a dict ({"key": "...", "signals": [...]}
    evolver format)."""
    if isinstance(sig, str):
        return [sig]
    if isinstance(sig, dict):
        return [str(s) for s in sig.get("signals", []) if isinstance(s, (str, int))]
    return []


def analyze(target_runtime: str) -> dict:
    base = Path(target_runtime)

    # 1. read the 6 fixed files (read-only, paths are constants, no recursion)
    paths = {
        "genes": base / ".evolver" / "gep" / "genes.json",
        "capsules": base / ".evolver" / "gep" / "capsules.json",
        "memory_graph": base / "memory" / "evolution" / "memory_graph.jsonl",
        "events": base / ".evolver" / "gep" / "events.jsonl",
        "failed_capsules": base / ".evolver" / "gep" / "failed_capsules.json",
        "candidates": base / ".evolver" / "gep" / "candidates.jsonl",
    }
    present = {k: p.exists() for k, p in paths.items()}

    # 2. parse genes.json
    gene_ids = []
    if present["genes"]:
        try:
            data = json.loads(paths["genes"].read_text(encoding="utf-8"))
            for g in data.get("genes", []):
                if isinstance(g, dict) and g.get("id"):
                    gene_ids.append(g["id"])
        except Exception as e:
            return {"ok": False, "reason": f"genes.json parse error: {e}"}

    # 3. parse capsules.json
    capsule_ids = []
    capsule_to_gene = {}
    if present["capsules"]:
        try:
            data = json.loads(paths["capsules"].read_text(encoding="utf-8"))
            for c in data.get("capsules", []):
                if isinstance(c, dict) and c.get("id"):
                    cid = c["id"]
                    capsule_ids.append(cid)
                    if c.get("gene_id"):
                        capsule_to_gene[cid] = c["gene_id"]
        except Exception as e:
            return {"ok": False, "reason": f"capsules.json parse error: {e}"}

    # 4. parse memory_graph.jsonl (each line is a JSON object)
    memory_graph_lines = 0
    distinct_signals = set()
    origins = set()
    parse_errors = 0
    raw_signals_list = []
    if present["memory_graph"]:
        try:
            for line in paths["memory_graph"].read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    parse_errors += 1
                    continue
                memory_graph_lines += 1
                origin = obj.get("origin")
                if isinstance(origin, str):
                    origins.add(origin)
                for s in _normalize_signal(obj.get("signal")):
                    distinct_signals.add(s)
                    raw_signals_list.append(s)
        except Exception as e:
            return {"ok": False, "reason": f"memory_graph.jsonl read error: {e}"}

    # 5. detect duplicates
    seen = set()
    duplicate_gene_ids = []
    for g in gene_ids:
        if g in seen:
            duplicate_gene_ids.append(g)
        else:
            seen.add(g)
    seen = set()
    duplicate_capsule_ids = []
    for c in capsule_ids:
        if c in seen:
            duplicate_capsule_ids.append(c)
        else:
            seen.add(c)

    # 6. dangerous / pollution
    dangerous_hits = sorted(s for s in distinct_signals if s in DANGEROUS_SIGNALS)
    pollution_hits = sorted(s for s in distinct_signals if s in POLLUTION_SIGNALS)
    long_digit_hits = sorted(s for s in distinct_signals if CREDENTIAL_PATTERN.match(s))

    # 7. required coverage
    required_gene_ids_present = all(g in gene_ids for g in REQUIRED_GENE_IDS)
    required_capsule_ids_present = all(c in capsule_ids for c in REQUIRED_CAPSULE_IDS)
    openclaw_missing = [s for s in REQUIRED_OPENCLAW_SIGNALS if s not in distinct_signals]
    hermes_missing = [s for s in REQUIRED_HERMES_SIGNALS if s not in distinct_signals]
    telegram_missing = [s for s in REQUIRED_TELEGRAM_SIGNALS if s not in distinct_signals]
    required_openclaw_signals_present = len(openclaw_missing) == 0
    required_hermes_signals_present = len(hermes_missing) == 0
    required_telegram_signals_present = len(telegram_missing) == 0

    # 8. broken capsule → gene links
    gene_id_set = set(gene_ids)
    broken_capsule_to_gene_links = []
    for cid, gid in capsule_to_gene.items():
        if gid not in gene_id_set:
            broken_capsule_to_gene_links.append({"capsule_id": cid, "gene_id": gid})

    return {
        "ok": True,
        "target_runtime": str(base),
        "files_present": present,
        "gene_count": len(gene_ids),
        "capsule_count": len(capsule_ids),
        "memory_graph_lines": memory_graph_lines,
        "distinct_signal_count": len(distinct_signals),
        "memory_graph_origins": sorted(origins),
        "memory_graph_parse_errors": parse_errors,
        "gene_ids": gene_ids,
        "capsule_ids": capsule_ids,
        "duplicate_gene_ids": duplicate_gene_ids,
        "duplicate_capsule_ids": duplicate_capsule_ids,
        "dangerous_signals": dangerous_hits,
        "pollution_signals": pollution_hits,
        "long_digit_signal_hits": long_digit_hits,
        "dangerous_signals_count": len(dangerous_hits),
        "pollution_signals_count": len(pollution_hits),
        "required_gene_ids_present": required_gene_ids_present,
        "required_capsule_ids_present": required_capsule_ids_present,
        "required_openclaw_signals_present": required_openclaw_signals_present,
        "required_hermes_signals_present": required_hermes_signals_present,
        "required_telegram_signals_present": required_telegram_signals_present,
        "openclaw_signals_missing": openclaw_missing,
        "hermes_signals_missing": hermes_missing,
        "telegram_signals_missing": telegram_missing,
        "broken_capsule_to_gene_links": broken_capsule_to_gene_links,
        "summary": {
            "ok": (
                required_gene_ids_present
                and required_capsule_ids_present
                and required_openclaw_signals_present
                and required_hermes_signals_present
                and required_telegram_signals_present
                and len(duplicate_gene_ids) == 0
                and len(duplicate_capsule_ids) == 0
                and len(dangerous_hits) == 0
                and len(pollution_hits) == 0
                and len(long_digit_hits) == 0
                and len(broken_capsule_to_gene_links) == 0
            ),
            "has_openclaw_signal_detector_origin": "openclaw_signal_detector" in origins,
            "has_evomap_apply_bundle_domain_origin": "evomap_apply_bundle:domain_from_bundle" in origins,
            "memory_graph_parse_errors": parse_errors,
            "dangerous_hits_count": len(dangerous_hits),
            "pollution_hits_count": len(pollution_hits),
            "long_digit_hits_count": len(long_digit_hits),
        },
    }


def main():
    p = argparse.ArgumentParser(
        description="Cross-bundle regression analyzer for an EvoMap target runtime."
    )
    p.add_argument(
        "--target-runtime",
        required=True,
        help="Path to the fresh isolated target runtime (must be under /tmp).",
    )
    args = p.parse_args()

    result = analyze(args.target_runtime)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
