#!/usr/bin/env python3
"""
ATL-5B: atl5b_second_upload_launch_retry.py

Second upload + launch retry for Castform cloud smoke run.

Difference from ATL-5A guard script:
- Writes to a SEPARATE result file: atl5b_second_upload_launch_retry_result.json
  (does NOT overwrite atl5_cloud_smoke_result.json — that preserves ATL-5 history)
- run_name = "hermes-phase-closer-smoke-atl5b" (distinguishes from ATL-5 first run)
- launcher_args schema already corrected (no batch_size, learning_rate added)

Hard rules:
  - Only 1 second upload_training_run.
  - Only 1 second launch_training_run.
  - Only 8 train / 2 eval preview subset (same as ATL-5).
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
  - Phase field in result JSON = "ATL-5B".

Required environment variables (all four must be set):
  - CASTFORM_API_KEY: must be present (any non-empty value)
  - ATL_ALLOW_CASTFORM_UPLOAD: must equal "YES" exactly
  - ATL_ALLOW_CASTFORM_LAUNCH: must equal "YES" exactly
  - ATL_USER_AUTHORIZATION: must equal exactly
      "I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY"

Any deviation => refuse, write a sanitized blocked result, exit 1.

Agent does NOT run this script during ATL-5B-SCRIPT-PREP.
User runs it manually after confirming all gates.
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

# IMPORTANT: this is a NEW result file. The ATL-5 result file
# (atl5_cloud_smoke_result.json) is left untouched so the first run's
# UPLOAD_DONE_LAUNCH_FAILED status is preserved as historical evidence.
RESULT_PATH = LIVE_ROOT / "atl5b_second_upload_launch_retry_result.json"

REQUIRED_GATES = {
    "CASTFORM_API_KEY": ("present", None),
    "ATL_ALLOW_CASTFORM_UPLOAD": ("exact", "YES"),
    "ATL_ALLOW_CASTFORM_LAUNCH": ("exact", "YES"),
    "ATL_USER_AUTHORIZATION": (
        "exact",
        "I AUTHORIZE ATL-5B SECOND UPLOAD AND LAUNCH RETRY",
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

TRAIN_SAMPLES = 8
EVAL_SAMPLES = 2
BASE_MODEL = "Qwen/Qwen3.5-4B"
RUN_NAME = "hermes-phase-closer-smoke-atl5b"

# Allowed metadata fields saved into the result JSON.
SAFE_UPLOAD_FIELDS = (
    "env_cls_path",
    "env_metadata_path",
    "train_dataset_path",
    "eval_dataset_path",
    "run_name",
    "run_id",
)


def _load_jsonl(path: Path, expected: int) -> list[dict]:
    """Load JSONL file; assert row count and required fields.

    Only the 8-train / 2-eval preview subset is allowed; we hard-fail otherwise.
    """
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
            raise ValueError(
                f"{path.name} row {i}: missing prompt or ground_truth"
            )
    return out


def _mask_key(val: str) -> str:
    """Mask a secret value for safe log output (4 chars + ellipsis or ***)."""
    if len(val) <= 8:
        return "***"
    return val[:4] + "..."


def _sanitize_error_text(text: str) -> str:
    """Sanitize any leaked secret-shaped value from an error message.

    Defensive: in case Castform echoes an Authorization header, bot token, or
    cookie into the raised exception, scrub it before persisting.
    """
    if not text:
        return text
    # Mask any sk-/cf-/Bearer/Authorization/Cookie-shaped substring.
    import re as _re
    scrubbed = text
    for pat in (
        r"sk-[A-Za-z0-9]{20,}",
        r"cf-[A-Za-z0-9]{20,}",
        r"Bearer\s+[A-Za-z0-9_\-]{20,}",
        r"Authorization:\s*[A-Za-z0-9_\-]{20,}",
        r"Cookie:\s*[A-Za-z0-9_\-]{20,}",
    ):
        scrubbed = _re.sub(pat, "<SECRET_REDACTED>", scrubbed)
    return scrubbed


def _write_result(payload: dict) -> None:
    RESULT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _base_payload(local_validate_env_result: str = "NOT_EXECUTED") -> dict:
    """Common skeleton for every result JSON variant."""
    return {
        "phase": "ATL-5B",
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
        "launcher_args_used": LAUNCHER_ARGS,
        "uploaded_payload_present": False,
        "uploaded_payload": None,
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


def check_gates() -> tuple[bool, str, str]:
    """Validate all four environment-variable gates.

    Returns (ok, category, summary). If any gate fails, ok=False and category
    identifies which gate (BLOCKED_BY_*). The summary lists every gate's
    observed vs expected state for audit purposes.
    """
    ok = True
    category: str | None = None
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
    """Run the local validate_env path only — local=True, api_key=None.

    No upload, no launch, no network to Castform. Mirrors ATL-3C's no-network
    proof chain: api_key=None / base_url=None / llm_api_key=None /
    llm_base_url=None.
    """
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
        train_dataset = _load_jsonl(train_path, TRAIN_SAMPLES)
        eval_dataset = _load_jsonl(eval_path, EVAL_SAMPLES)
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
        if any(
            tok in msg
            for tok in ("api_key", "credential", "login", "network", "endpoint", "auth")
        ):
            return False, f"validate_env network/auth error: {type(e).__name__}: {e}"
        return False, f"validate_env error: {type(e).__name__}: {e}"


def _is_billing_error(msg_lower: str) -> bool:
    return any(
        tok in msg_lower
        for tok in ("billing", "credit", "payment", "quota", "insufficient", "balance")
    )


def _build_uploaded_payload(uploaded_obj: object) -> dict:
    """Extract the safe (path-only, no-secret) subset of an uploaded dataclass."""
    try:
        raw = dataclasses.asdict(uploaded_obj)
    except Exception:
        # Fall back to reading __dict__ if not a dataclass.
        raw = dict(getattr(uploaded_obj, "__dict__", {}))
    return {k: v for k, v in raw.items() if k in SAFE_UPLOAD_FIELDS}


def main() -> int:
    print("[INFO] ATL-5B second upload + launch retry starting")
    print("[INFO] This script will call Castform API if all gates pass.")

    # ------------------------------------------------------------------
    # A. Gate check (no API call, no upload, no launch)
    # ------------------------------------------------------------------
    gates_ok, gate_category, gate_summary = check_gates()
    print(f"[INFO] Gate check: {gate_summary}")
    if not gates_ok:
        print(f"[FAIL] Gate blocked: {gate_category}")
        _write_blocked(gate_category, gate_summary)
        return 1

    # ------------------------------------------------------------------
    # B. Dataset check (only the 8-train / 2-eval preview subset)
    # ------------------------------------------------------------------
    try:
        train_path = CLOUD_SMOKE_RUN / "smoke-train.preview.jsonl"
        eval_path = CLOUD_SMOKE_RUN / "smoke-eval.preview.jsonl"
        train_dataset = _load_jsonl(train_path, TRAIN_SAMPLES)
        eval_dataset = _load_jsonl(eval_path, EVAL_SAMPLES)
        print(
            f"[INFO] Dataset check: train={len(train_dataset)} eval={len(eval_dataset)} OK"
        )
    except Exception as e:
        print(f"[FAIL] Dataset check failed: {e}")
        _write_blocked("BLOCKED_BY_DATASET_CHECK", str(e))
        return 1

    # ------------------------------------------------------------------
    # C. Local validate_env (local=True, api_key=None — no network)
    # ------------------------------------------------------------------
    print("[INFO] Running local validate_env...")
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

    # ------------------------------------------------------------------
    # D. Upload (second attempt)
    # ------------------------------------------------------------------
    print("[INFO] Uploading training run to Castform (second attempt)...")
    api_key = os.environ["CASTFORM_API_KEY"]
    upload_attempted = True
    upload_succeeded = False
    upload_error: Exception | None = None
    uploaded_obj: object | None = None
    try:
        from benchmax.platform.training_run import upload_training_run

        sys.path.insert(0, str(LOCAL_VALIDATE))
        from environment_validate_candidate import HermesPhaseCloserLocalEnv

        uploaded_obj = upload_training_run(
            env_class=HermesPhaseCloserLocalEnv,
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
            print(
                f"[FAIL] Upload blocked by billing/credit/quota: "
                f"{type(e).__name__}: {e}"
            )
            payload = _base_payload(local_validate_env_result=local_msg)
            payload["status"] = "BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT"
            payload["upload_attempted"] = True
            payload["upload_succeeded"] = False
            payload["error_category"] = "BLOCKED_BY_CASTFORM_BILLING_OR_CREDIT"
            payload["error_summary"] = _sanitize_error_text(
                f"upload_training_run raised: {type(e).__name__}: {e}"
            )
            _write_result(payload)
            return 1
        print(f"[FAIL] Upload failed: {type(e).__name__}: {e}")

    if not upload_succeeded:
        # upload_error is set here
        err = upload_error
        payload = _base_payload(local_validate_env_result=local_msg)
        payload["status"] = "UPLOAD_FAILED"
        payload["upload_attempted"] = upload_attempted
        payload["upload_succeeded"] = False
        payload["error_category"] = "UPLOAD_FAILED"
        payload["error_summary"] = _sanitize_error_text(
            f"upload_training_run raised: {type(err).__name__}: {err}"
        )
        _write_result(payload)
        return 1

    # ------------------------------------------------------------------
    # E. Save uploaded payload metadata BEFORE launch (critical lesson)
    # ------------------------------------------------------------------
    safe_payload = _build_uploaded_payload(uploaded_obj)
    uploaded_payload_present = bool(safe_payload)

    # ------------------------------------------------------------------
    # F. Launch (second attempt, corrected args — no batch_size)
    # ------------------------------------------------------------------
    print("[INFO] Launching training run on Castform (second attempt)...")
    launch_attempted = True
    launch_succeeded = False
    launch_error: Exception | None = None
    run_id: str | None = None
    experiment_url: str | None = None
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
            print(
                f"[FAIL] Launch blocked by billing/credit/quota: "
                f"{type(e).__name__}: {e}"
            )
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
        # launch_error is set here
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

    # ------------------------------------------------------------------
    # G. Success
    # ------------------------------------------------------------------
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
    print("[INFO] ATL-5B second upload + launch retry complete.")
    print(f"[INFO] run_id: {run_id}")
    print(f"[INFO] experiment_url: {experiment_url}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # last-resort sanitizer
        # Catch any unexpected exception during main() so a partial result JSON
        # is always written, sanitized, before exit.
        summary = f"{type(e).__name__}: {e}"
        try:
            _write_blocked("FAILED_WITH_SANITIZED_ERROR", summary)
        except Exception:
            pass
        traceback.print_exc()
        sys.exit(1)