#!/usr/bin/env python3
"""
ATL-5: atl5_cloud_smoke_run.py

Live cloud smoke run for Castform Hermes Phase Closer v0.

- Must be run inside .venv-castform-local with CASTFORM_API_KEY exported.
- Agent does NOT run this script during ATL-5-SCRIPT-PREP.
- User runs it manually after confirming all gates.

Hard rules:
  - Only 1 upload_training_run.
  - Only 1 launch_training_run.
  - Only 8 train / 2 eval preview subset.
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
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE_ROOT = HERE
CLOUD_SMOKE_RUN = HERE.parent
CASE_ROOT = CLOUD_SMOKE_RUN.parent
LOCAL_VALIDATE = CASE_ROOT / "local-validate-env"

RESULT_PATH = LIVE_ROOT / "atl5_cloud_smoke_result.json"

REQUIRED_GATES = {
    "CASTFORM_API_KEY": ("present", None),
    "ATL_ALLOW_CASTFORM_UPLOAD": ("exact", "YES"),
    "ATL_ALLOW_CASTFORM_LAUNCH": ("exact", "YES"),
    "ATL_USER_AUTHORIZATION": ("exact", "I AUTHORIZE ATL-5 CLOUD SMOKE RUN"),
}


def _load_jsonl(path: Path, expected: int) -> list[dict]:
    out: list[dict] = []
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
            raise ValueError(f"{path.name} row {i}: missing prompt or ground_truth")
    return out


def _mask_key(val: str) -> str:
    if len(val) <= 8:
        return "***"
    return val[:4] + "..."


def _write_result(payload: dict) -> None:
    RESULT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _fail(category: str, summary: str, **extra: object) -> dict:
    payload = {
        "phase": "ATL-5",
        "status": category,
        "local_validate_env_result": extra.get("local_validate_env_result", "NOT_EXECUTED"),
        "upload_attempted": False,
        "upload_succeeded": False,
        "launch_attempted": False,
        "launch_succeeded": False,
        "run_id": None,
        "experiment_url": None,
        "base_model": "Qwen/Qwen3.5-4B",
        "train_samples": 8,
        "eval_samples": 2,
        "api_key_recorded": False,
        "dataset_uploaded": False,
        "training_started": False,
        "error_category": category,
        "error_summary": summary,
    }
    _write_result(payload)
    return payload


def check_gates() -> tuple[bool, str, str]:
    ok = True
    category = None
    summary_parts: list[str] = []
    for var, (check, expected) in REQUIRED_GATES.items():
        val = os.environ.get(var, "").strip()
        if check == "present":
            if not val:
                ok = False
                category = "BLOCKED_BY_MISSING_RUNTIME_API_KEY"
                summary_parts.append(f"{var} missing")
            else:
                summary_parts.append(f"{var} present: {_mask_key(val)}")
        elif check == "exact":
            if val != expected:
                ok = False
                if var == "ATL_ALLOW_CASTFORM_UPLOAD":
                    category = "BLOCKED_BY_UPLOAD_GATE"
                elif var == "ATL_ALLOW_CASTFORM_LAUNCH":
                    category = "BLOCKED_BY_LAUNCH_GATE"
                elif var == "ATL_USER_AUTHORIZATION":
                    category = "BLOCKED_BY_MISSING_USER_AUTHORIZATION"
                summary_parts.append(f"{var}='{val}' (expected '{expected}')")
            else:
                summary_parts.append(f"{var}='{val}' OK")
    return ok, category or "UNKNOWN", "; ".join(summary_parts)


def run_local_validate_env() -> tuple[bool, str]:
    sys.path.insert(0, str(LOCAL_VALIDATE))
    try:
        from environment_validate_candidate import HermesPhaseCloserLocalEnv
    except Exception as e:
        return False, f"import HermesPhaseCloserLocalEnv failed: {type(e).__name__}: {e}"

    try:
        from benchmax.platform.validation import validate_env
    except Exception as e:
        return False, f"import validate_env failed: {type(e).__name__}: {e}"

    train_path = CLOUD_SMOKE_RUN / "smoke-train.preview.jsonl"
    eval_path = CLOUD_SMOKE_RUN / "smoke-eval.preview.jsonl"
    try:
        train_dataset = _load_jsonl(train_path, 8)
        eval_dataset = _load_jsonl(eval_path, 2)
    except Exception as e:
        return False, f"dataset load failed: {type(e).__name__}: {e}"

    try:
        report = validate_env(
            env_class=HermesPhaseCloserLocalEnv,
            env_args={},
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            local_modules=None,
            pip_dependencies=[],
            local=True,
            api_key=None,
            base_url=None,
            llm_api_key=None,
            llm_base_url=None,
            llm_model=None,
            verbose=True,
        )
        ok = bool(report)
        return ok, "VALIDATE_ENV_LOCAL_PASS" if ok else "VALIDATE_ENV_LOCAL_FAIL"
    except Exception as e:
        msg = str(e).lower()
        if any(tok in msg for tok in ("api_key", "credential", "login", "network", "endpoint", "auth")):
            return False, f"validate_env network/auth error: {type(e).__name__}: {e}"
        return False, f"validate_env error: {type(e).__name__}: {e}"


def main() -> int:
    print("[INFO] ATL-5 cloud smoke run starting")
    print("[INFO] This script will call Castform API if all gates pass.")

    # A. Gate check
    gates_ok, gate_category, gate_summary = check_gates()
    print(f"[INFO] Gate check: {gate_summary}")
    if not gates_ok:
        print(f"[FAIL] Gate blocked: {gate_category}")
        _fail(gate_category, gate_summary)
        return 1

    # B. Dataset check
    try:
        train_path = CLOUD_SMOKE_RUN / "smoke-train.preview.jsonl"
        eval_path = CLOUD_SMOKE_RUN / "smoke-eval.preview.jsonl"
        train_dataset = _load_jsonl(train_path, 8)
        eval_dataset = _load_jsonl(eval_path, 2)
    except Exception as e:
        print(f"[FAIL] Dataset check failed: {e}")
        _fail("BLOCKED_BY_DATASET_CHECK", str(e))
        return 1

    # C. Local validate_env
    print("[INFO] Running local validate_env...")
    local_ok, local_msg = run_local_validate_env()
    print(f"[INFO] Local validate_env: {local_msg}")
    if not local_ok:
        print("[FAIL] Local validate_env did not pass. Stopping before upload.")
        _fail("BLOCKED_BY_LOCAL_VALIDATE_ENV", local_msg, local_validate_env_result=local_msg)
        return 1

    # D. Upload
    print("[INFO] Uploading training run to Castform...")
    api_key = os.environ["CASTFORM_API_KEY"]
    upload_ok = False
    upload_error = None
    uploaded = None
    try:
        from benchmax.platform.training_run import upload_training_run
        sys.path.insert(0, str(LOCAL_VALIDATE))
        from environment_validate_candidate import HermesPhaseCloserLocalEnv
        uploaded = upload_training_run(
            env_class=HermesPhaseCloserLocalEnv,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            run_name="hermes-phase-closer-smoke",
            api_key=api_key,
            constructor_args={},
            local_modules=None,
            pip_dependencies=[],
        )
        upload_ok = True
        print("[INFO] Upload succeeded.")
    except Exception as e:
        upload_error = e
        msg = str(e).lower()
        if any(tok in msg for tok in ("billing", "credit", "payment", "quota", "insufficient", "balance")):
            print(f"[FAIL] Upload blocked by billing/credit/quota: {type(e).__name__}: {e}")
            _fail(
                "BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT",
                f"upload_training_run raised: {type(e).__name__}: {e}",
                local_validate_env_result=local_msg,
            )
            return 1
        print(f"[FAIL] Upload failed: {type(e).__name__}: {e}")

    if not upload_ok:
        _fail(
            "UPLOAD_FAILED",
            f"upload_training_run raised: {type(upload_error).__name__}: {upload_error}",
            local_validate_env_result=local_msg,
        )
        return 1

    # E. Launch
    print("[INFO] Launching training run on Castform...")
    launch_ok = False
    launch_error = None
    run_id = None
    experiment_url = None
    try:
        from benchmax.platform.client import TrainerClient
        trainer = TrainerClient(api_key=api_key)
        run_id = trainer.launch_training_run(
            training_run_type="simple",
            **dataclasses.asdict(uploaded),
            launcher_args={
                "model": "Qwen/Qwen3.5-4B",
                "num_epochs": 1,
                "batch_size": 2,
                "group_size": 2,
                "max_rollout_len": 512,
                "max_turns": 1,
                "lora_rank": 16,
                "lora_alpha": 32,
            },
        )
        launch_ok = True
        experiment_url = f"https://app.castform.com/experiments/{run_id}"
        print(f"[INFO] Launch succeeded. run_id={run_id}")
    except Exception as e:
        launch_error = e
        msg = str(e).lower()
        if any(tok in msg for tok in ("billing", "credit", "payment", "quota", "insufficient", "balance")):
            print(f"[FAIL] Launch blocked by billing/credit/quota: {type(e).__name__}: {e}")
            payload = {
                "phase": "ATL-5",
                "status": "UPLOAD_DONE_LAUNCH_BLOCKED_BY_BILLING",
                "local_validate_env_result": local_msg,
                "upload_attempted": True,
                "upload_succeeded": True,
                "launch_attempted": True,
                "launch_succeeded": False,
                "run_id": None,
                "experiment_url": None,
                "base_model": "Qwen/Qwen3.5-4B",
                "train_samples": 8,
                "eval_samples": 2,
                "api_key_recorded": False,
                "dataset_uploaded": True,
                "training_started": False,
                "error_category": "BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT",
                "error_summary": f"launch_training_run raised: {type(e).__name__}: {e}",
            }
            _write_result(payload)
            return 1
        print(f"[FAIL] Launch failed: {type(e).__name__}: {e}")

    if not launch_ok:
        payload = {
            "phase": "ATL-5",
            "status": "UPLOAD_DONE_LAUNCH_FAILED",
            "local_validate_env_result": local_msg,
            "upload_attempted": True,
            "upload_succeeded": True,
            "launch_attempted": True,
            "launch_succeeded": False,
            "run_id": None,
            "experiment_url": None,
            "base_model": "Qwen/Qwen3.5-4B",
            "train_samples": 8,
            "eval_samples": 2,
            "api_key_recorded": False,
            "dataset_uploaded": True,
            "training_started": False,
            "error_category": "LAUNCH_FAILED",
            "error_summary": f"launch_training_run raised: {type(launch_error).__name__}: {launch_error}",
        }
        _write_result(payload)
        return 1

    # F. Success
    payload = {
        "phase": "ATL-5",
        "status": "PASS_CLOUD_SMOKE_LAUNCHED",
        "local_validate_env_result": local_msg,
        "upload_attempted": True,
        "upload_succeeded": True,
        "launch_attempted": True,
        "launch_succeeded": True,
        "run_id": run_id,
        "experiment_url": experiment_url,
        "base_model": "Qwen/Qwen3.5-4B",
        "train_samples": 8,
        "eval_samples": 2,
        "api_key_recorded": False,
        "dataset_uploaded": True,
        "training_started": True,
        "error_category": None,
        "error_summary": None,
    }
    _write_result(payload)
    print("[INFO] ATL-5 cloud smoke run complete.")
    print(f"[INFO] run_id: {run_id}")
    print(f"[INFO] experiment_url: {experiment_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
