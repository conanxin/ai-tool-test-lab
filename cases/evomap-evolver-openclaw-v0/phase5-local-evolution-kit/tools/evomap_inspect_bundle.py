#!/usr/bin/env python3
"""
evomap_inspect_bundle.py

Inspect a portable bundle and emit a JSON summary.

Stdlib only. Strictly read-only. No network, no Hub, no secrets.
Does NOT recurse into a repo. Only reads the single --bundle path.

Usage:
  python3 scripts/evomap_inspect_bundle.py --bundle <bundle.json>

Output (stdout): JSON summary with ok=true and the bundle's metadata,
or ok=false with a "reason" on error.
"""

import argparse
import json
import sys
from pathlib import Path


def inspect_bundle(bundle_path: Path) -> dict:
    if not bundle_path.is_file():
        return {"ok": False, "reason": f"bundle file not found: {bundle_path}"}
    try:
        bundle = json.loads(bundle_path.read_text())
    except Exception as e:
        return {"ok": False, "reason": f"bundle is not valid JSON: {e}"}

    gene = bundle.get("gene") or {}
    capsule = bundle.get("capsule") or {}
    exec_trace = capsule.get("execution_trace") or []
    if not isinstance(exec_trace, list):
        exec_trace = []

    summary = {
        "ok": True,
        "bundle_path": str(bundle_path),
        "schema_version": bundle.get("schema_version", ""),
        "source_phase": bundle.get("source_phase", ""),
        "source_session": bundle.get("source_session", ""),
        "gene_id": gene.get("id", ""),
        "gene_category": gene.get("category", ""),
        "capsule_id": capsule.get("id", ""),
        "capsule_status": capsule.get("status", ""),
        "capsule_confidence": capsule.get("confidence"),
        "capsule_visibility": capsule.get("visibility", ""),
        "capsule_source": capsule.get("source", ""),
        "execution_trace_steps": len(exec_trace),
        "execution_trace_stages": [t.get("stage", "?") for t in exec_trace if isinstance(t, dict)],
        "top_level_execution_trace_ok": (bundle.get("execution_trace") or {}).get("ok") if isinstance(bundle.get("execution_trace"), dict) else None,
        "import_contract": bundle.get("import_contract", {}),
        "safety": bundle.get("safety", {}),
        "kit_provenance": bundle.get("kit_provenance", {}),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a portable OpenClaw Evolution bundle (stdlib only, read-only)"
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        required=True,
        help="Path to the portable bundle JSON file",
    )
    args = parser.parse_args()

    result = inspect_bundle(args.bundle)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
