#!/usr/bin/env python3
"""
Castform 环境 stub — ATL-0 阶段

本文件仅为示意代码，不实际运行 Castform。
在真实测试阶段（Phase 4+）才需要执行。

前置要求：
- Python 3.12+
- 安装 benchmax：pip install benchmax（仅在真实测试时安装）
- 设置 CASTFORM_API_KEY 环境变量（仅在真实测试时设置）

安全提示：
- 不要将 CASTFORM_API_KEY 写入代码或提交到仓库
- 使用 .env 文件或环境变量注入
- 本文件不包含任何真实 API key
"""

import os
import sys


# 占位常量 — 真实测试时从环境变量读取
CASTFORM_API_KEY = os.environ.get("CASTFORM_API_KEY", "")


def validate_env():
    """
    检查运行环境是否满足 Castform 要求。
    ATL-0 阶段仅打印检查项，不实际调用 API。
    """
    checks = {
        "Python 版本": sys.version_info >= (3, 12),
        "CASTFORM_API_KEY 已设置": bool(CASTFORM_API_KEY),
        "benchmax 已安装": False,  # 真实测试时检查
    }

    print("=== Castform 环境检查 ===")
    for name, ok in checks.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")

    if not any(checks.values()):
        print("\nATL-0 阶段：所有检查项均为占位状态，无需修复。")
        print("进入 Phase 4 后再运行真实检查。")

    return checks


def submit_training_run_stub():
    """
    提交训练任务的占位函数。
    ATL-0 阶段不执行任何网络请求。
    """
    print("=== 训练任务提交（stub） ===")
    print("状态：未执行")
    print("原因：ATL-0 阶段禁止调用 Castform API")
    print("如需真实提交，请完成 Phase 1–3 后取消本函数的 stub 标记")
    return None


def evaluate_model_stub():
    """
    模型评估的占位函数。
    ATL-0 阶段不执行任何评估。
    """
    print("=== 模型评估（stub） ===")
    print("状态：未执行")
    print("原因：无训练完成的模型")
    return None


if __name__ == "__main__":
    validate_env()
    print("\n提示：如需进入真实测试阶段，请：")
    print("  1. 确认 Python 3.12+")
    print("  2. pip install benchmax")
    print("  3. export CASTFORM_API_KEY=<CASTFORM_API_KEY>")
    print("  4. 运行真实脚本（非本 stub）")
