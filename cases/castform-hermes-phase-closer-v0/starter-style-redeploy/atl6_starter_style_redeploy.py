#!/usr/bin/env python3
"""
ATL-6A: atl6_starter_style_redeploy.py

Starter-style Castform redeploy script. Mirrors the ATL-5B retry script
structure (4-gate + local validate_env + upload + launch + result JSON) but
embeds the ATL-6A fix points:

  1. dataset = starter-train.preview.jsonl (16) + starter-eval.preview.jsonl (4)
     (NOT the ATL-5 8/2 smoke subset, NOT the full 49-row dataset)
  2. environment = HermesPhaseCloserStarterStyleEnv
     - no-tools (list_tools -> [], run_tool -> "" no raise)
     - 0.0~1.0 reward (format / coverage / score)
     - no custom load_dataset override
  3. run_name = "hermes-phase-closer-smoke-atl6a"
     (does NOT overwrite ATL-5 / ATL-5B run records)
  4. result file = atl6_starter_style_redeploy_result.json
     (separate from atl5_cloud_smoke_result.json +
      atl5b_second_upload_launch_retry_result.json)
  5. old failed run c83f971d-... is NEVER referenced; new run is independent

Hard rules:
  - Only 1 upload_training_run.
  - Only 1 launch_training_run.
  - Only 16 train / 4 eval preview subset.
  - Only Qwen/Qwen3.5-4B.
  - No full 49-row upload.
  - No RAG corpus.
  - No Agent Traces.
  - No .env creation.
  - No API key written to disk.
  - No API key printed.
  - No auto-retry.
  - Stop on billing/credit/quota error.
  - Stop on upload success + launch failure (do not retry).
  - Phase field in result JSON = "ATL-6A".

Required environment variables (all four must be set):
  - CASTFORM_API_KEY: must be present (any non-empty value)
  - ATL_ALLOW_CASTFORM_UPLOAD: must equal "YES" exactly
  - ATL_ALLOW_CASTFORM_LAUNCH: must equal "YES" exactly
  - ATL_USER_AUTHORIZATION: must equal exactly
      "I AUTHORIZE ATL-6A STARTER-STYLE REDEPLOY"

Any deviation => refuse, write a sanitized blocked result, exit 1.

Agent does NOT run this script during ATL-6A-SCRIPT-PREP.
User runs it manually after confirming all gates.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASE_ROOT = HERE.parent
REDEPLOY_ROOT = HERE

# Result file: separate from ATL-5 / ATL-5B result files.
RESULT_PATH = REDEPLOY_ROOT / "atl6_starter_style_redeploy_result.json"

# Dataset files: written by prepare_starter_style_subset.py, not the
# cloud-smoke-run/ 8/2 subset.
TRAIN_FILE = REDEPLOY_ROOT / "starter-train.preview.jsonl"
EVAL_FILE = REDEPLOY_ROOT / "starter-eval.preview.jsonl"

# Environment class file (relative path string the trainer will use to load).
ENV_CLS_PATH = (
    "cases.castform-hermes-phase-closer-v0.starter-style-redeploy."
    "environment_starter_style:HermesPhaseCloserStarterStyleEnv"
)
ENV_METADATA_PATH = str(REDEPLOY_ROOT / "environment_starter_style.py")

REQUIRED_GATES = {
    "CASTFORM_API_KEY": ("present", None),
    "ATL_ALLOW_CASTFORM_UPLOAD": ("exact", "YES"),
    "ATL_ALLOW_CASTFORM_LAUNCH": ("exact", "YES"),
    "ATL_USER_AUTHORIZATION": (
        "exact",
        "I AUTHORIZE ATL-6A STARTER-STYLE REDEPLOY",
    ),
}

LAUNCHER_ARGS = {
    "model": "Qwen/Qwen3.5-4B",
    "learning_rate": 1e-5,
    "num_epochs": 1,
    "group_size": 2,
    "max_rollout_len": 512,
    "max_turns": 1,
    "lora_rank": 16,
    "lora_alpha": 32,
}

TRAIN_SAMPLES = 16
EVAL_SAMPLES = 4
BASE_MODEL = "Qwen/Qwen3.5-4B"
RUN_NAME = "hermes-phase-closer-smoke-atl6a"

SAFE_UPLOAD_FIELDS = (
    "env_cls_path",
    "env_metadata_path",
    "train_dataset_path",
    "eval_dataset_path",
    "run_name",
    "run_id",
)


def _load_jsonl(path: Path, expected: int) -> list:
    out: list = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    if len(out) != expected:
        raise ValueError(f"{path.name}: expected {expected} rows, got {len(out)}")
    for i, row in enumerate(out):
        if "prompt" not in row or "ground_truth" not in row:
            raise ValueError(
                f"{path.name} row {i}: missing prompt or ground_truth"
            )
    return out


def _sanitize_error_text(text: str) -> str:
    if not text:
        return text
    scrubbed = text
    for pat in (
        r"sk-[A-Za-z0-9]{20,}",
        r"cf-[A-Za-z0-9]{20,}",
        r"cf_[A-Za-z0-9]{20,}",
        r"Bearer\s+[A-Za-z0-9_\-]{20,}",
        r"Authorization:\s*[A-Za-z0-9_\-]{20,}",
        r"Cookie:\s*[A-Za-z0-9_\-]{20,}",
    ):
        scrubbed = re.sub(pat, "<SECRET_REDACTED>", scrubbed)
    return scrubbed


def _write_result(payload: dict) -> None:
    RESULT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _base_payload(local_validate_env_result: str = "NOT_EXECUTED") -> dict:
    return {
        "phase": "ATL-6A",
        "local_validate_env_result": local_validate_env_result,
        "upload_attempted": False,
        "upload_succeeded": False,
        "launch_attempted": False,
        "launch_succeeded": False,
        "run_id": None,
        "experiment_url": None,
        "base_model": BASE_MODEL,
        "train_samples": TRAIN_SAMPLES,
        "eval_samples": EVAL_SAMPLES,
        "api_key_recorded": False,
        "dataset_uploaded": False,
        "training_started": False,
        "launcher_args_used": dict(LAUNCHER_ARGS),
        "uploaded_payload_present": False,
        "uploaded_payload": None,
        "env_cls_path": ENV_CLS_PATH,
        "env_metadata_path": ENV_METADATA_PATH,
        "env_name": "HermesPhaseCloserStarterStyleEnv",
        "env_fix_points": [
            "16 train / 4 eval preview subset (vs ATL-5 8/2)",
            "no-tools env (list_tools=[] / run_tool='' no raise)",
            "0.0~1.0 reward (format / coverage / score)",
            "no custom load_dataset override (BaseEnv default)",
            "new run_name hermes-phase-closer-smoke-atl6a (does not overwrite ATL-5 / ATL-5B run records)",
            "old failed run c83f971d-... not referenced",
        ],
        "old_failed_run_referenced": False,
        "error_category": None,
        "error_summary": None,
    }


def _write_blocked(category: str, summary: str, **extra: object) -> dict:
    payload = _base_payload(
        local_validate_env_result=extra.get("local_validate_env_result", "NOT_EXECUTED")
    )
    payload["status"] = category
    payload["error_category"] = category
    payload["error_summary"] = _sanitize_error_text(summary)
    _write_result(payload)
    return payload


def check_gates() -> tuple:
    ok = True
    category = "UNKNOWN"
    summary_parts = []
    for var, (check, expected) in REQUIRED_GATES.items():
        val = os.environ.get(var, "").strip()
        if check == "present":
            if not val:
                ok = False
                category = "BLOCKED_BY_MISSING_RUNTIME_API_KEY"
                summary_parts.append(f"{var} present: False")
            else:
                summary_parts.append(f"{var} present: True")
        elif check == "exact":
            if val != expected:
                ok = False
                if var == "ATL_ALLOW_CASTFORM_UPLOAD":
                    category = "BLOCKED_BY_UPLOAD_GATE"
                elif var == "ATL_ALLOW_CASTFORM_LAUNCH":
                    category = "BLOCKED_BY_LAUNCH_GATE"
                elif var == "ATL_USER_AUTHORIZATION":
                    category = "BLOCKED_BY_MISSING_USER_AUTHORIZATION"
                summary_parts.append(f"{var} mismatch (expected: {expected!r})")
            else:
                summary_parts.append(f"{var} OK")
    return ok, category, "; ".join(summary_parts)


def run_local_validate_env() -> tuple:
    """Local-only contract check via benchmax.validate_env, no API key."""
    sys.path.insert(0, str(REDEPLOY_ROOT))
    try:
        from environment_starter_style import HermesPhaseCloserStarterStyleEnv
    except Exception as e:
        return False, f"import failed: {type(e).__name__}: {e}"

    try:
        from benchmax.platform.validation import validate_env
    except Exception as e:
        return False, f"import validate_env failed: {type(e).__name__}: {e}"

    try:
        train_dataset = _load_jsonl(TRAIN_FILE, TRAIN_SAMPLES)
        eval_dataset = _load_jsonl(EVAL_FILE, EVAL_SAMPLES)
    except Exception as e:
        return False, f"dataset load failed: {type(e).__name__}: {e}"

    try:
        report = validate_env(
            env_class=HermesPhaseCloserStarterStyleEnv,
            env_args={},
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            local=True,
            api_key=None,
            base_url=None,
            llm_api_key=None,
            llm_base_url=None,
            llm_model=None,
            verbose=True,
        )
    except Exception as e:
        return False, f"validate_env error: {type(e).__name__}: {e}"

    passed = getattr(report, "local_passed", 0)
    failed = getattr(report, "local_failed", 1)
    if failed == 0 and passed > 0:
        return True, f"VALIDATE_ENV_LOCAL_PASS (local {passed}/{passed + failed} checks)"
    return False, f"VALIDATE_ENV_LOCAL_FAIL (local_passed={passed}, local_failed={failed})"


def _is_billing_error(msg_lower: str) -> bool:
    return any(
        tok in msg_lower
        for tok in ("billing", "credit", "payment", "quota", "insufficient", "balance")
    )


def _build_uploaded_payload(uploaded_obj: object) -> dict:
    try:
        raw = dataclasses.asdict(uploaded_obj)
    except Exception:
        raw = dict(getattr(uploaded_obj, "__dict__", {}))
    return {k: v for k, v in raw.items() if k in SAFE_UPLOAD_FIELDS}


def main() -> int:
    print("[INFO] ATL-6A starter-style redeploy starting")
    print("[INFO] This script will call Castform API if all gates pass.")

    # A. Gate check
    gates_ok, gate_category, gate_summary = check_gates()
    print(f"[INFO] Gate check: {gate_summary}")
    if not gates_ok:
        print(f"[FAIL] Gate blocked: {gate_category}")
        _write_blocked(gate_category, gate_summary)
        return 1

    # B. Dataset check (16 train / 4 eval, not 8/2, not 49/7)
    try:
        train_dataset = _load_jsonl(TRAIN_FILE, TRAIN_SAMPLES)
        eval_dataset = _load_jsonl(EVAL_FILE, EVAL_SAMPLES)
        print(
            f"[INFO] Dataset check: train={len(train_dataset)} eval={len(eval_dataset)} OK"
        )
    except Exception as e:
        print(f"[FAIL] Dataset check failed: {e}")
        _write_blocked("BLOCKED_BY_DATASET_CHECK", str(e))
        return 1

    # C. Local validate_env
    print("[INFO] Running local validate_env (starter-style env, 5+2 rows)...")
    local_ok, local_msg = run_local_validate_env()
    print(f"[INFO] Local validate_env: {local_msg}")
    if not local_ok:
        print("[FAIL] Local validate_env did not pass. Stopping before upload.")
        _write_blocked(
            "VALIDATE_ENV_FAILED",
            local_msg,
            local_validate_env_result=local_msg,
        )
        return 1

    # D. Upload
    print("[INFO] Uploading training run to Castform (ATL-6A)...")
    api_key = os.environ["CASTFORM_API_KEY"]
    upload_attempted = True
    upload_succeeded = False
    upload_error = None
    uploaded_obj = None
    try:
        from benchmax.platform.training_run import upload_training_run

        sys.path.insert(0, str(REDEPLOY_ROOT))
        from environment_starter_style import HermesPhaseCloserStarterStyleEnv

        uploaded_obj = upload_training_run(
            env_class=HermesPhaseCloserStarterStyleEnv,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            run_name=RUN_NAME,
            api_key=api_key,
            constructor_args={},
            local_modules=None,
            pip_dependencies=[],
        )
        upload_succeeded = True
        print("[INFO] Upload succeeded.")
    except Exception as e:
        upload_error = e
        msg_lower = str(e).lower()
        if _is_billing_error(msg_lower):
            payload = _base_payload(local_validate_env_result=local_msg)
            payload["status"] = "BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT"
            payload["upload_attempted"] = True
            payload["error_category"] = "BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT"
            payload["error_summary"] = _sanitize_error_text(
                f"upload_training_run raised: {type(e).__name__}: {e}"
            )
            _write_result(payload)
            return 1
        print(f"[FAIL] Upload failed: {type(e).__name__}: {e}")

    if not upload_succeeded:
        err = upload_error
        payload = _base_payload(local_validate_env_result=local_msg)
        payload["status"] = "UPLOAD_FAILED"
        payload["upload_attempted"] = upload_attempted
        payload["error_category"] = "UPLOAD_FAILED"
        payload["error_summary"] = _sanitize_error_text(
            f"upload_training_run raised: {type(err).__name__}: {err}"
        )
        _write_result(payload)
        return 1

    # E. Save uploaded payload metadata BEFORE launch
    safe_payload = _build_uploaded_payload(uploaded_obj)
    uploaded_payload_present = bool(safe_payload)

    # F. Launch
    print("[INFO] Launching training run on Castform (ATL-6A)...")
    launch_attempted = True
    launch_succeeded = False
    launch_error = None
    run_id = None
    experiment_url = None
    try:
        from benchmax.platform.client import TrainerClient

        trainer = TrainerClient(api_key=api_key)
        run_id = trainer.launch_training_run(
            training_run_type="simple",
            **safe_payload,
            launcher_args=LAUNCHER_ARGS,
        )
        launch_succeeded = True
        experiment_url = f"https://app.castform.com/experiments/{run_id}"
        print(f"[INFO] Launch succeeded. run_id={run_id}")
    except Exception as e:
        launch_error = e
        msg_lower = str(e).lower()
        if _is_billing_error(msg_lower):
            payload = _base_payload(local_validate_env_result=local_msg)
            payload["status"] = "UPLOAD_DONE_LAUNCH_BLOCKED_BY_BILLING"
            payload["upload_attempted"] = True
            payload["upload_succeeded"] = True
            payload["launch_attempted"] = True
            payload["launch_succeeded"] = False
            payload["dataset_uploaded"] = True
            payload["uploaded_payload_present"] = uploaded_payload_present
            payload["uploaded_payload"] = safe_payload
            payload["error_category"] = "BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT"
            payload["error_summary"] = _sanitize_error_text(
                f"launch_training_run raised: {type(e).__name__}: {e}"
            )
            _write_result(payload)
            return 1
        print(f"[FAIL] Launch failed: {type(e).__name__}: {e}")

    if not launch_succeeded:
        err = launch_error
        payload = _base_payload(local_validate_env_result=local_msg)
        payload["status"] = "UPLOAD_DONE_LAUNCH_FAILED"
        payload["upload_attempted"] = True
        payload["upload_succeeded"] = True
        payload["launch_attempted"] = launch_attempted
        payload["launch_succeeded"] = False
        payload["dataset_uploaded"] = True
        payload["uploaded_payload_present"] = uploaded_payload_present
        payload["uploaded_payload"] = safe_payload
        payload["error_category"] = "LAUNCH_FAILED"
        payload["error_summary"] = _sanitize_error_text(
            f"launch_training_run raised: {type(err).__name__}: {err}"
        )
        _write_result(payload)
        return 1

    # G. Success
    payload = _base_payload(local_validate_env_result=local_msg)
    payload["status"] = "PASS_CLOUD_SMOKE_LAUNCHED"
    payload["upload_attempted"] = True
    payload["upload_succeeded"] = True
    payload["launch_attempted"] = True
    payload["launch_succeeded"] = True
    payload["run_id"] = run_id
    payload["experiment_url"] = experiment_url
    payload["dataset_uploaded"] = True
    payload["training_started"] = True
    payload["uploaded_payload_present"] = uploaded_payload_present
    payload["uploaded_payload"] = safe_payload
    payload["error_category"] = None
    payload["error_summary"] = None
    _write_result(payload)
    print("[INFO] ATL-6A starter-style redeploy complete.")
    print(f"[INFO] run_id: {run_id}")
    print(f"[INFO] experiment_url: {experiment_url}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        try:
            payload = _base_payload()
            payload["status"] = "FAILED_WITH_SANITIZED_ERROR"
            payload["error_category"] = "FAILED_WITH_SANITIZED_ERROR"
            payload["error_summary"] = _sanitize_error_text(
                f"top-level: {type(e).__name__}: {e}"
            )
            _write_result(payload)
        finally:
            print(f"[FAIL] top-level: {type(e).__name__}: {e}")
            sys.exit(1)
