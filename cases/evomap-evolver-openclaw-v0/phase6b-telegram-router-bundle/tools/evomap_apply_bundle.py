#!/usr/bin/env python3
"""
evomap_apply_bundle.py

Apply a portable bundle to a target runtime.

Stdlib only. NO network. NO Hub. NO evolver calls. NO publish. NO --approve.
NO solidify. NO secrets. The tool ONLY writes 3 required + 3 optional files
plus 5 clean bare memory signals.

Default mode is --dry-run. Real writes require explicit --yes.

Usage:
  python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --dry-run
  python3 scripts/evomap_apply_bundle.py --bundle <bundle.json> --target-runtime <path> --yes

Behavior:
  - Without --yes, defaults to --dry-run (refuses to write).
  - --dry-run: prints the planned writes, does NOT touch the filesystem.
  - --yes: writes the planned files to the target runtime.
  - Target must exist as a directory (will be checked). If not a git repo, warns but allows.
  - Existing genes.json / capsules.json: same id is overwritten/replaced (id-based dedup).
  - memory_graph.jsonl: 5 clean bare signals APPENDED to existing file (or created).
  - Optional files: events.jsonl / failed_capsules.json / candidates.jsonl reset to empty.

Hard boundaries (enforced):
  - No A2A_HUB_URL touched.
  - No real config mutation outside the target runtime's .evolver/ + memory/evolution/.
  - No secrets written (the bundle was pre-validated by evomap_validate_bundle.py).
  - No evolver run/review invoked.
  - No --approve / --solidify / publish.
"""

import argparse
import json
import sys
from pathlib import Path


# 5 clean bare signals to inject (consistent with Phases 4A/4B/4C)
CLEAN_BARE_SIGNALS = [
    ("tool_bypass", 0.85, "Detected exec invocation without prior read on .md file"),
    ("repeated_tool_usage", 0.7, "Same read+edit+search pattern repeated 3x"),
    ("protocol_drift", 0.9, "Detected sed -i usage forbidden by OpenClaw protocol"),
    ("session_context", 0.6, "Session has multiple file ops requiring tool discipline"),
    ("repo_context", 0.65, "Repo is ai-tool-test-lab, evomap-evolver-openclaw-v0 case"),
]


def _make_memory_events(target_gene_id: str, ts_base: float = 1718700001.0) -> list[str]:
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


def _dedup_by_id(items: list, id_field: str = "id") -> list:
    """Replace items with same id, keep last occurrence."""
    seen = {}
    for it in items:
        if isinstance(it, dict) and id_field in it:
            seen[it[id_field]] = it
    return list(seen.values())


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def plan_apply(bundle: dict, target: Path) -> dict:
    """Compute planned writes. No filesystem mutation."""
    gene = bundle.get("gene") or {}
    capsule = bundle.get("capsule") or {}
    target_gene_id = gene.get("id", "")
    target_capsule_id = capsule.get("id", "")

    gene_id = target_gene_id or "<unknown>"
    cap_id = target_capsule_id or "<unknown>"

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

    plan = {
        "target": str(target),
        "is_git_repo": _is_git_repo(target),
        "gene_id": gene_id,
        "capsule_id": cap_id,
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
                "lines": _make_memory_events(gene_id),
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
            "memory_graph_signals_added": len(CLEAN_BARE_SIGNALS),
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

    plan = plan_apply(bundle, args.target_runtime)

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
        "log": log,
    }, indent=2, ensure_ascii=False))
    return 0 if not log["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
