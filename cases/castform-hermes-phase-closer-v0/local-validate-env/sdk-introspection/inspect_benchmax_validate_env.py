#!/usr/bin/env python3
"""
inspect_benchmax_validate_env.py — ATL-3C SDK introspection

Standard library only. Imports benchmax and inspects the local-only validate_env
entry point WITHOUT calling it, WITHOUT setting any API key, and WITHOUT making
any network call.

Outputs a structured summary that gets recorded in ATL3C_VALIDATE_ENV_API_NOTES.md.
"""

from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path


def main() -> int:
    out: list[str] = []
    out.append("=== benchmax validate_env introspection (ATL-3C) ===")
    out.append("no Castform API call intended")
    out.append("no upload intended")
    out.append("no training intended")

    # 1. Import the benchmax root namespace
    try:
        benchmax = importlib.import_module("benchmax")
        out.append(f"benchmax import: PASS")
        out.append(f"benchmax module: {benchmax!r}")
        out.append(f"benchmax __file__: {getattr(benchmax, '__file__', None)}")
    except Exception as e:
        out.append(f"benchmax import: FAIL — {type(e).__name__}: {e}")
        print("\n".join(out))
        return 1

    # 2. Try the documented entry path: benchmax.platform.validation
    mod_path = "benchmax.platform.validation"
    try:
        mod = importlib.import_module(mod_path)
        out.append(f"module import: PASS — {mod_path}")
        out.append(f"module file: {getattr(mod, '__file__', None)}")
    except Exception as e:
        out.append(f"module import: FAIL — {mod_path} — {type(e).__name__}: {e}")
        print("\n".join(out))
        return 1

    # 3. Probe for validate_env attribute
    fn = getattr(mod, "validate_env", None)
    if fn is None:
        out.append("validate_env attribute: MISSING")
        print("\n".join(out))
        return 1
    out.append(f"validate_env attribute: PRESENT — {fn!r}")

    # 4. Signature
    try:
        sig = inspect.signature(fn)
        out.append(f"validate_env signature: {sig}")
    except (TypeError, ValueError) as e:
        out.append(f"validate_env signature: <unavailable> ({e})")

    # 5. Docstring (first 1000 chars)
    doc = inspect.getdoc(fn) or ""
    out.append("validate_env docstring (first 1000 chars):")
    out.append("---DOCSTRING-START---")
    out.append(doc[:1000])
    out.append("---DOCSTRING-END---")

    # 6. Probe related helpers (purely passive introspection)
    helpers = []
    for name in (
        "_run_local_checks",
        "assert_group_reward_contract",
        "overrides_compute_group_reward",
    ):
        h = getattr(mod, name, None)
        helpers.append(f"  {name}: {'PRESENT' if h else 'MISSING'}")
    out.append("related helpers:")
    out.extend(helpers)

    # 7. Sanity-check: BaseEnv exists (required for env_class contract)
    try:
        be_mod = importlib.import_module("benchmax.envs.base_env")
        be_cls = getattr(be_mod, "BaseEnv", None)
        out.append(f"benchmax.envs.base_env.BaseEnv: {'PRESENT' if be_cls else 'MISSING'}")
        if be_cls is not None:
            abstract = getattr(be_cls, "__abstractmethods__", frozenset())
            out.append(f"BaseEnv abstract methods: {sorted(abstract)}")
    except Exception as e:
        out.append(f"benchmax.envs.base_env: FAIL — {type(e).__name__}: {e}")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
