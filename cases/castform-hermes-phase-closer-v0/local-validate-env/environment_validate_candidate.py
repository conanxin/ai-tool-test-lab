#!/usr/bin/env python3
"""
environment_validate_candidate.py — ATL-3C minimal local Env for benchmax.validate_env.

Builds the smallest env_class that satisfies benchmax's contract for the *local-only*
validation path (no API key, no upload, no training, no network):

  - dataset_preprocess(cls, row) -> Example dict with id + prompt_messages
  - load_dataset(cls, name, data_files=..., split=...) -> (Dataset, None)
  - __init__(self, **env_args)               # accepts env_args, no side effects
  - list_tools(self)                          # returns [] (no tools)
  - run_tool(...)                             # would only run if list_tools non-empty
  - compute_reward(self, rollout_id, messages, task, **kwargs) -> dict[str, float]

The reward side delegates to the existing rule-based reward.py (score_completion),
which is exercised by run_local_reward_smoke.py and is fully offline.

No external tools, no network, no API keys, no real project data.
Only the ATL-2 redacted JSONL samples (prompt + ground_truth) are used.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, ClassVar

from datasets import Dataset, load_dataset as _hf_load_dataset

from benchmax.envs.base_env import BaseEnv
from benchmax.envs.example_id import make_example
from benchmax.envs.types import ToolDefinition

# Local rule-based reward (stdlib-only), already covered by run_local_reward_smoke.py.
from reward import score_completion


SYSTEM_PROMPT = (
    "You are Hermes Phase Closer — given an agent phase report, produce a structured\n"
    "JSON closing with 7 fields: 阶段结论, 当前状态, 设计理由, 修改影响, 验证结果, 风险边界, 下一步.\n"
    "Never echo tokens, api_keys, or secrets."
)


# Tools are intentionally empty: this env is a non-tool, rule-based grader.
# Returning [] makes validate_env's run_tool step skip ("no tools defined"), which
# is the safest possible behavior for an offline contract check.


class HermesPhaseCloserLocalEnv(BaseEnv):
    """Minimal local-only Env for validate_env contract checks."""

    # Static class attribute — read by BaseEnv.get_system_prompt(add_tool_defs=False).
    system_prompt: ClassVar[str] = SYSTEM_PROMPT

    # ── 1. dataset_preprocess ───────────────────────────────────────────
    @classmethod
    def dataset_preprocess(cls, row: Any, **kwargs: Any) -> dict[str, Any]:
        # Accept either ATL-2 shape {prompt, ground_truth} or already-prepped rows.
        if not isinstance(row, dict):
            raise TypeError(
                f"{cls.__name__}.dataset_preprocess: row must be a dict, got "
                f"{type(row).__name__}"
            )

        # Build chat-style prompt_messages.
        if "prompt_messages" in row and isinstance(row["prompt_messages"], list):
            prompt_messages = list(row["prompt_messages"])
        elif "messages" in row and isinstance(row["messages"], list):
            prompt_messages = list(row["messages"])
        elif "prompt" in row and isinstance(row["prompt"], str):
            prompt_messages = [{"role": "user", "content": row["prompt"]}]
        else:
            raise ValueError(
                f"{cls.__name__}.dataset_preprocess: row has none of "
                "'prompt_messages', 'messages', 'prompt'. Got keys: "
                f"{sorted(row.keys())}"
            )

        # Task carries the ground_truth to compute_reward (JSON-serializable only).
        task: dict[str, Any] | None = None
        gt_raw = row.get("ground_truth")
        if isinstance(gt_raw, str) and gt_raw.strip():
            try:
                task = {"ground_truth": json.loads(gt_raw)}
            except json.JSONDecodeError:
                # ground_truth is a raw string; keep as-is so reward can still grade headers.
                task = {"ground_truth_raw": gt_raw}
        elif isinstance(gt_raw, dict):
            task = {"ground_truth": gt_raw}
        elif gt_raw is None:
            task = None

        return make_example(
            prompt_messages=prompt_messages,
            task=task,
            system_prompt=cls.system_prompt,
        )

    # ── 2. load_dataset ─────────────────────────────────────────────────
    @classmethod
    def load_dataset(
        cls,
        name: str,
        data_files: str | None = None,
        split: str | None = None,
        **kwargs: Any,
    ) -> tuple[Dataset, str | None]:
        # Delegate to HuggingFace datasets.load_dataset for the "json" case the
        # validator exercises. Returns the (Dataset, revision_or_None) tuple the
        # validator inspects.
        ds = _hf_load_dataset(name, data_files=data_files, split=split, **kwargs)
        return ds, None

    # ── 3. Constructor ──────────────────────────────────────────────────
    def __init__(self, **env_args: Any) -> None:
        # Store env_args verbatim — no side effects, no I/O, no network.
        self.env_args = dict(env_args)

    # ── 4. Tool surface (empty, by design) ──────────────────────────────
    async def list_tools(self) -> list[ToolDefinition]:
        return []

    async def run_tool(
        self,
        rollout_id: str,
        tool_name: str,
        **tool_args: Any,
    ) -> str:
        # Unreachable: list_tools() returns []. Kept for type completeness.
        raise NotImplementedError(
            f"{type(self).__name__} has no tools (list_tools returns [])"
        )

    # ── 5. Reward ───────────────────────────────────────────────────────
    async def compute_reward(
        self,
        rollout_id: str,
        messages: list[dict[str, Any]],
        task: dict[str, Any] | None,
        **kwargs: Any,
    ) -> dict[str, float]:
        # Flatten the transcript into a single completion string for the
        # rule-based grader. Strip role markers so scoring matches the
        # smoke test's expectations (headers must appear in the completion).
        parts: list[str] = []
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                parts.append(content)
        completion = "\n".join(parts).strip()

        # Pull ground_truth (parsed dict, or the raw fallback string).
        gt_for_grade: str = ""
        if isinstance(task, dict):
            gt = task.get("ground_truth")
            if isinstance(gt, dict):
                gt_for_grade = json.dumps(gt, ensure_ascii=False)
            elif isinstance(gt, str):
                gt_for_grade = gt
            else:
                gt_for_grade = task.get("ground_truth_raw", "") or ""

        if not completion:
            return {"score": 0.0}

        result = score_completion(
            prompt="<validate_env_local>",
            completion=completion,
            ground_truth=gt_for_grade,
        )
        # Normalize the 0-10 score into a finite float.
        raw = float(result.get("score", 0.0))
        return {"score": raw}


# Convenience: when run as a module-level entry point, dump a one-line
# description so that a human running `python environment_validate_candidate.py`
# doesn't get a silent no-op.
if __name__ == "__main__":
    print(
        "HermesPhaseCloserLocalEnv — minimal BaseEnv subclass for offline validate_env."
    )
    print("Use run_real_validate_env_attempt.py to actually exercise validate_env.")
