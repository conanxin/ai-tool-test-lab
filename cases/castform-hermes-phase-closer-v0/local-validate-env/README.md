# ATL-3A Local Scaffold-Only

## 说明

- **阶段**：ATL-3A local scaffold-only
- **Python 3.12**：可用（Python 3.12.3）
- **benchmax**：BLOCKED，因为 venv 缺少 pip（python3.12-venv 包未完整安装）
- **本阶段**：不调用 Castform API，不上传数据，不训练
- **目标**：只验证 dataset loader 和 rule-based reward 结构

## 文件说明

| 文件 | 用途 |
|------|------|
| `dataset_loader.py` | 读取 sample-train.jsonl / sample-eval.jsonl，校验格式 |
| `reward.py` | rule-based reward 评分 |
| `environment_stub.py` | ATL-3A scaffold only，不导入 benchmax，不调用云端 |
| `run_local_reward_smoke.py` | 本地 reward smoke 测试 |
| `run_validate_env_stub.py` | validate_env stub，benchmax 不可用时输出 SKIPPED_WITH_REASON |

## 运行方式

```bash
python3.12 dataset_loader.py
python3.12 run_local_reward_smoke.py
python3.12 run_validate_env_stub.py
```

## 阻塞说明

benchmax 安装需要 pip，但当前 Python 3.12 venv 缺少 pip。`sudo dpkg --configure -a` 超时，无法修复。因此 ATL-3A 只做本地 scaffold，不安装 benchmax。

## 下一步

- ATL-3B：修复 Python 3.12 venv/pip 后安装 benchmax
- ATL-4：前置 Castform account/credit/billing preflight
