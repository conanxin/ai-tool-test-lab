#!/usr/bin/env python3
"""
evomap_validate_bundle.py

Validate a portable bundle against the OpenClaw Local Evolution Kit contract.

Stdlib only. Strictly read-only. No network, no Hub, no secrets.
Does NOT recurse into a repo. Only reads the single --bundle path.

Usage:
  python3 scripts/evomap_validate_bundle.py --bundle <bundle.json>

Validates:
  - bundle JSON parseable
  - has schema_version
  - has 'gene' and 'capsule' and 'execution_trace'
  - gene.id present
  - capsule.id present
  - capsule.gene (or gene_id) == gene.id
  - capsule.execution_trace non-empty list
  - import_contract.required_files contains the 3 required files
  - no secret patterns anywhere in the bundle

Output (stdout): JSON with ok=true|false, list of check results.
Exit code: 0 if all PASS, 1 if any FAIL.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Secret patterns (consistent with Phase 3C-V2 / 4A / 4B / 4C validators)
SECRET_PATTERNS = [
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9]{16,}")),
    ("api_key", re.compile(r"\bsk_live_[A-Za-z0-9]{16,}")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{16,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{16,}")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{16,}")),
    ("google_oauth", re.compile(r"\bya29\.[0-9A-Za-z_-]{16,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("bearer", re.compile(r"Bearer\s+[A-Za-z0-9_\-\.=]{16,}")),
    ("telegram_bot", re.compile(r"\bbot[0-9]{6,}:[A-Za-z0-9_-]{20,}")),
    ("telegram_token", re.compile(r"\b[0-9]{8,}:[A-Za-z0-9_-]{20,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Required import contract files
REQUIRED_IMPORT_FILES = {
    ".evolver/gep/genes.json",
    ".evolver/gep/capsules.json",
    "memory/evolution/memory_graph.jsonl",
}


def _flatten_strings(obj, prefix=""):
    """Yield (path, string) for every string value in a nested JSON-like object."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            yield from _flatten_strings(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{prefix}[{i}]"
            yield from _flatten_strings(v, p)
    elif isinstance(obj, str):
        yield prefix, obj


def validate_bundle(bundle_path: Path) -> dict:
    checks = []
    failures = []

    def add(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            failures.append(name)

    # 1. file exists
    add("bundle file exists", bundle_path.is_file(), str(bundle_path))
    if not bundle_path.is_file():
        return {"ok": False, "checks": checks, "failures": failures}

    # 2. JSON parseable
    try:
        bundle = json.loads(bundle_path.read_text())
        add("bundle is valid JSON", True)
    except Exception as e:
        add("bundle is valid JSON", False, str(e))
        return {"ok": False, "checks": checks, "failures": failures}

    # 3. has schema_version
    sv = bundle.get("schema_version", "")
    add("bundle has schema_version", bool(sv), str(sv))

    # 4. has gene
    gene = bundle.get("gene")
    add("bundle has 'gene' field", isinstance(gene, dict), type(gene).__name__)
    if not isinstance(gene, dict):
        return {"ok": False, "checks": checks, "failures": failures}

    # 5. has capsule
    capsule = bundle.get("capsule")
    add("bundle has 'capsule' field", isinstance(capsule, dict), type(capsule).__name__)
    if not isinstance(capsule, dict):
        return {"ok": False, "checks": checks, "failures": failures}

    # 6. has execution_trace
    has_exec_trace = "execution_trace" in bundle
    add("bundle has 'execution_trace' field", has_exec_trace)

    # 7. gene.id present
    gene_id = gene.get("id", "")
    add("gene.id present and non-empty", bool(gene_id), str(gene_id))

    # 8. capsule.id present
    capsule_id = capsule.get("id", "")
    add("capsule.id present and non-empty", bool(capsule_id), str(capsule_id))

    # 9. capsule.gene (or gene_id) == gene.id
    capsule_gene_ref = capsule.get("gene") or capsule.get("gene_id") or ""
    add(
        "capsule.gene (or gene_id) == gene.id",
        bool(capsule_gene_ref) and capsule_gene_ref == gene_id,
        f"capsule_gene_ref={capsule_gene_ref!r}, gene_id={gene_id!r}",
    )

    # 10. capsule.execution_trace non-empty list
    cap_trace = capsule.get("execution_trace")
    add(
        "capsule.execution_trace is non-empty list",
        isinstance(cap_trace, list) and len(cap_trace) > 0,
        f"type={type(cap_trace).__name__}, len={len(cap_trace) if isinstance(cap_trace, list) else 0}",
    )

    # 11. import_contract.required_files contains the 3 required files
    import_contract = bundle.get("import_contract", {})
    required = set(import_contract.get("required_files", [])) if isinstance(import_contract, dict) else set()
    missing = REQUIRED_IMPORT_FILES - required
    add(
        "import_contract.required_files contains 3 required paths",
        not missing,
        f"missing={sorted(missing)}" if missing else "all present",
    )

    # 12. no secret patterns anywhere in the bundle
    secret_hits = []
    for path_str, value in _flatten_strings(bundle):
        for label, pat in SECRET_PATTERNS:
            if pat.search(value):
                secret_hits.append({"path": path_str, "pattern": label, "snippet": value[:60]})
    add(
        "no secret patterns in bundle",
        not secret_hits,
        f"hits={secret_hits[:3]}" if secret_hits else "clean",
    )

    return {
        "ok": not failures,
        "checks": checks,
        "failures": failures,
        "summary": {
            "schema_version": sv,
            "gene_id": gene_id,
            "capsule_id": capsule_id,
            "capsule_gene_match": capsule_gene_ref == gene_id,
            "capsule_execution_trace_steps": len(cap_trace) if isinstance(cap_trace, list) else 0,
            "required_import_files_count": len(required & REQUIRED_IMPORT_FILES),
            "secret_hits": len(secret_hits),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a portable OpenClaw Evolution bundle (stdlib only, read-only, secret scan)"
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        required=True,
        help="Path to the portable bundle JSON file",
    )
    args = parser.parse_args()

    result = validate_bundle(args.bundle)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
