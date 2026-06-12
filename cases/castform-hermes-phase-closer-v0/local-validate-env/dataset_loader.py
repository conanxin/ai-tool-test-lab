#!/usr/bin/env python3
"""
dataset_loader.py — 读取 Castform JSONL 样本
标准库 only。
"""

import json
from pathlib import Path


def load_dataset(train_path: Path, eval_path: Path) -> dict:
    datasets = {"train": [], "eval": []}
    for key, path in [("train", train_path), ("eval", eval_path)]:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError(f"Line {i} in {path.name}: not a dict")
                for field in ("prompt", "ground_truth"):
                    if field not in obj or not isinstance(obj[field], str) or not obj[field].strip():
                        raise ValueError(f"Line {i} in {path.name}: missing/empty '{field}'")
                datasets[key].append(obj)
    return datasets


if __name__ == "__main__":
    base = Path(__file__).parent.parent
    train = base / "sample-train.jsonl"
    eval_ = base / "sample-eval.jsonl"
    ds = load_dataset(train, eval_)
    print(f"Train: {len(ds['train'])} samples")
    print(f"Eval:  {len(ds['eval'])} samples")
