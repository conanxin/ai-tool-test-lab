#!/usr/bin/env python3
"""
run_real_validate_env_attempt.py — ATL-3C

Attempts a real local benchmax.validate_env call against the minimal Env.

Hard rules:
  - Do NOT pass api_key / base_url / llm_api_key / llm_base_url.
  - local=True (the default) means no network, no upload, no training.
  - Use only ATL-2 redacted sample-train/sample-eval slices.

Outputs exactly ONE explicit status line:
  VALIDATE_ENV_LOCAL_PASS
  SKIPPED_WITH_REASON
  BLOCKED_BY_ENV_CONTRACT_MAPPING
  BLOCKED_BY_SDK_API_MISMATCH
  BLOCKED_BY_API_KEY_OR_NETWORK_REQUIREMENT

Also prints the explicit safety lines:
  no Castform API call intended
  no upload intended
  no training intended
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path


HERE = Path(__file__).resolve().parent
CASE_ROOT = HERE.parent


def _load_jsonl_slice(path: Path, n: int) -> list[dict]:
    out: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
            if len(out) >= n:
                break
    return out


def _emit(status: str, **extra: object) -> None:
    print("=== run_real_validate_env_attempt.py (ATL-3C) ===")
    print("no Castform API call intended")
    print("no upload intended")
    print("no training intended")
    print(f"STATUS: {status}")
    for k, v in extra.items():
        print(f"{k}: {v}")


def main() -> int:
    # 1. Load tiny slices from the ATL-2 redacted JSONL samples.
    train_path = CASE_ROOT / "sample-train.jsonl"
    eval_path = CASE_ROOT / "sample-eval.jsonl"
    if not train_path.exists() or not eval_path.exists():
        _emit("BLOCKED_BY_SDK_API_MISMATCH", reason="sample-train.jsonl / sample-eval.jsonl missing")
        return 0

    train_dataset = _load_jsonl_slice(train_path, 5)
    eval_dataset = _load_jsonl_slice(eval_path, 2)

    # 2. Import the validate_env entry point.
    try:
        from benchmax.platform.validation import validate_env
    except Exception as e:
        _emit(
            "BLOCKED_BY_SDK_API_MISMATCH",
            reason=f"cannot import benchmax.platform.validation.validate_env: "
                   f"{type(e).__name__}: {e}",
        )
        return 0

    # 3. Import the local Env candidate.
    try:
        sys.path.insert(0, str(HERE))
        from environment_validate_candidate import HermesPhaseCloserLocalEnv  # noqa: E402
    except Exception as e:
        _emit(
            "BLOCKED_BY_ENV_CONTRACT_MAPPING",
            reason=f"cannot import environment_validate_candidate.HermesPhaseCloserLocalEnv: "
                   f"{type(e).__name__}: {e}",
            traceback=traceback.format_exc().splitlines()[-3:],
        )
        return 0

    # 4. Call validate_env with ONLY local-mode args.
    #    No api_key, no base_url, no llm_* — exactly the documented local path.
    env_args: dict = {}
    env_class = HermesPhaseCloserLocalEnv
    local_modules = None
    pip_dependencies: list[str] = []  # empty: nothing extra needed beyond SDK deps
    api_key = None
    base_url = None
    llm_api_key = None
    llm_base_url = None
    llm_model = None
    verbose = True

    try:
        report = validate_env(
            env_class=env_class,
            env_args=env_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            local_modules=local_modules,
            pip_dependencies=pip_dependencies,
            local=True,
            api_key=api_key,
            base_url=base_url,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_model=llm_model,
            verbose=verbose,
        )
    except TypeError as e:
        # Signature mismatch — benchmax API differs from the documented one.
        _emit(
            "BLOCKED_BY_SDK_API_MISMATCH",
            reason=f"validate_env raised TypeError: {e}",
            hint="the installed benchmax SDK has a different validate_env signature "
                 "than ATL-3C expected; re-run inspect_benchmax_validate_env.py",
        )
        return 0
    except Exception as e:
        msg = str(e)
        # Classify common failure shapes without ever claiming PASS.
        if any(
            tok in msg.lower()
            for tok in ("api_key", "credential", "login", "network", "endpoint", "auth")
        ):
            _emit(
                "BLOCKED_BY_API_KEY_OR_NETWORK_REQUIREMENT",
                reason=f"validate_env raised: {type(e).__name__}: {msg}",
            )
            return 0
        # Otherwise this is most likely an Env contract defect.
        _emit(
            "BLOCKED_BY_ENV_CONTRACT_MAPPING",
            reason=f"validate_env raised: {type(e).__name__}: {msg}",
            traceback=traceback.format_exc().splitlines()[-5:],
        )
        return 0

    # 5. Interpret the ValidationReport.
    try:
        ok = bool(report)  # ValidationReport is bool-castable per its docstring
    except Exception:
        ok = False

    if ok:
        _emit("VALIDATE_ENV_LOCAL_PASS")
        return 0

    _emit(
        "BLOCKED_BY_ENV_CONTRACT_MAPPING",
        reason="validate_env returned a falsy ValidationReport "
               "(one or more local contract checks failed)",
        hint="see the validator's printed summary above for the failing checks",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
