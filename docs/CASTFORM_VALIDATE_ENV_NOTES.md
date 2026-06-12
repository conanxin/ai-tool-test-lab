# Castform validate_env — 本地验证笔记

本文件记录 ATL-3B 关于 `validate_env` 与 `benchmax` 的本地观察，
以及为什么本阶段不运行真实 cloud validate_env。

## ATL-3B 结论

| 项 | 状态 | 备注 |
|----|------|------|
| Python 3.12 venv | PASS | `python3.12 -m venv --without-pip` |
| pip 修复 | PASS | `/tmp/get-pip.py` 引导（未使用 sudo apt） |
| benchmax 安装 | PASS | benchmax 0.1.2.dev33，命名空间包 |
| benchmax import | PASS | `import benchmax` 通过 |
| 真实 validate_env | **未运行** | 本阶段仅 import，未执行 cloud validate_env |

## pip 修复路径

### 失败路径 A：`python3.12 -m venv` + `ensurepip`

WSL 上 Debian 默认不安装 `python3.12-venv`，`ensurepip` 不可用。
错误信息原文：

> The virtual environment was not created successfully because ensurepip is not
> available. On Debian/Ubuntu systems, you need to install the python3.12-venv package.

**结论**：避免 `sudo apt install python3.12-venv`（硬性边界要求）。

### 成功路径 B：`--without-pip` + `/tmp/get-pip.py`

```bash
rm -rf .venv-castform-local
python3.12 -m venv --without-pip .venv-castform-local
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv-castform-local/bin/python /tmp/get-pip.py
.venv-castform-local/bin/python -m pip --version     # pip 26.1.2
.venv-castform-local/bin/python -m pip install benchmax
```

- `get-pip.py` 仅放在 `/tmp`，不复制进项目目录，不 commit。
- 整个过程无 `sudo apt` / `sudo dpkg`。

## benchmax 包形态

`benchmax 0.1.2.dev33` 是一个 **namespace package**：

```python
import benchmax
# <module 'benchmax' (namespace) from ['.../site-packages/benchmax']>
# benchmax file: None
# benchmax version: ''
```

namespace package 不带 `__init__.py`，`__file__` 为 `None`，`__version__` 为空。
`importlib.import_module("benchmax")` 成功即表示入口可达。

## run_validate_env_stub.py 三态

为防止伪造 cloud success，stub 现在显式区分：

| 状态 | 含义 |
|------|------|
| `SKIPPED_WITH_REASON` | benchmax 不可导入（pip/venv 异常） |
| `BENCHMAX_IMPORT_PASS_VALIDATE_ENV_NOT_RUN` | benchmax 可导入，但 stub 未执行真实 validate_env（本阶段目标状态） |
| `VALIDATE_ENV_LOCAL_PASS` | 只有真正本地 validate_env 且无需 API key / 无上传 / 无训练时才允许 |

本阶段 ATL-3B 输出 `BENCHMAX_IMPORT_PASS_VALIDATE_ENV_NOT_RUN`。

## 为什么本阶段仍不运行 cloud training

- 没有 `CASTFORM_API_KEY`（硬性边界：不读取/不使用/不创建）。
- 没有 account / credit / billing 验证（属于 ATL-4）。
- 不调用 `upload_training_run` / `launch_training_run` / `TrainerClient`（硬性边界）。
- 仅本地 import benchmax ≠ 运行 validate_env ≠ 训练。

## 下一步 ATL-3C 计划（建议）

在 ATL-3C 中尝试映射官方 `validate_env` API：
1. 通过 PyPI 主页 / GitHub README 找 `benchmax` 的真实入口模块（可能不在根命名空间下）。
2. 检查官方是否提供 "validate env without uploading" 的纯本地模式。
3. 若官方仅提供云端路径，本地只能做"伪 validate_env"（导入 + 字段检查），不算 `VALIDATE_ENV_LOCAL_PASS`。

若 ATL-3C 仍无法真正本地 validate_env → 进入 ATL-4 做 Castform account / credit / billing preflight。

## 已知限制

1. namespace package 的 `__version__` 为空，未来若需要版本判定需读 `pyproject.toml` / `pip show benchmax`。
2. 当前未执行 `benchmax.<some_submodule>`（可能真正入口在 `benchmax.cli` / `benchmax.api` 等子模块），需在 ATL-3C 探索。
3. 本地未跑 cloud-side smoke run，无网络侧 cost / latency 反馈。

---

## ATL-3C 追加（SDK API mapping & real local validate_env）

### benchmax.validate_env import path

```
benchmax.platform.validation.validate_env
```

真实存在于 `benchmax 0.1.2.dev33` 的 `site-packages/benchmax/platform/validation.py`。

### validate_env signature

```
validate_env(
    env_class: type,
    env_args: dict[str, Any],
    train_dataset: list[dict[str, Any]],
    eval_dataset: list[dict[str, Any]] | None = None,
    *,
    local_modules: list[ModuleType] | None = None,
    pip_dependencies: list[str] | None = None,
    local: bool = True,
    api_key: str | None = None,
    base_url: str | None = None,
    llm_base_url: str | None = None,
    llm_api_key: str | None = None,
    remote_examples: int = 2,
    group_reward_samples: int = 2,
    llm_model: str | None = None,
    max_turns: int = 4,
    verbose: bool = True,
) -> ValidationReport
```

**关键事实**：`local=True` 是默认值，且只有 `api_key is not None` 或 `local=False` 时才会触发远程 smoke rollout。因此**只要不传 `api_key`，validate_env 就不调用 Castform API，不上传数据，不启动训练**。

### validate_env docstring 摘要

- Local contract checks：in-process、无网络，mirror trainer 调用流程（dataset_preprocess、load_dataset、list_tools/run_tool、compute_reward、模拟 rollout、compute_group_reward、pickle round-trips）。
- Remote smoke rollout：仅当传入 `api_key` 时运行，使用 `RolloutClient.validate_examples` 在云端跑 `remote_examples` 个真实 rollout。

### Env contract（来自 BaseEnv）

`BaseEnv.__abstractmethods__ == {"compute_reward", "list_tools", "run_tool"}`。

Env 必须实现：

| 方法 | 形态 | 期望 |
|------|------|------|
| `dataset_preprocess(cls, row)` | classmethod | 返回 dict 含 `id` + `prompt_messages` (list[{role,content}])；可选 `task`, `init_rollout_args` |
| `load_dataset(cls, "json", data_files=..., split="train")` | classmethod | 返回 `(Dataset, str\|None)`；至少 1 行 |
| `__init__(self, **env_args)` | instance | 无副作用 |
| `list_tools(self)` | async | list[ToolDefinition]；空 list 时跳过 run_tool |
| `run_tool(self, rollout_id, tool_name, **args)` | async | 仅 tools 非空时调用，返回 str |
| `compute_reward(self, rollout_id, messages, task, **kwargs)` | async | dict[str, float]；值必须 finite |

### 真实本地 validate_env 执行结果

```
Environment Validation
  ✓ dataset_preprocess returns Example with id + prompt_messages
  ✓ prompt_messages is a 2-message chat list
  ✓ load_dataset accepts ("json", data_files=..., split="train") — 5 rows
  ✓ list_tools returns 0 tool(s)
  - run_tool: skipped (no tools defined)
  ✓ compute_reward returns dict[str, float]: {'score': 10.0}
  ✓ simulated rollout OK (no tools, reward={'score': 10.0})
  - compute_group_reward: skipped (not overridden — per-rollout rewards only)
  ✓ pickle round-trip OK (75 bytes, 0 tools)
  ✓ auto-bundled local module(s): environment_validate_candidate, reward
  ✓ env_args pickle round-trip OK (5 bytes)
  ✓ system_prompt: 189 chars

validate_env passed: local 10/10 checks
STATUS: VALIDATE_ENV_LOCAL_PASS
```

### 是否调用 Castform API / 上传 / 训练

| 项 | 本阶段 |
|----|------|
| Castform API 调用 | **无** |
| 上传 | **无** |
| 训练 | **无** |

### 已知限制（ATL-3C 增量）

1. **benchmax 是 dev33 pre-release**（`0.1.2.dev33`），validate_env 真实路径可能在 release 改名/改签名；本结论以 0.1.2.dev33 为准。
2. **真实 cloud training 仍未发生**。`VALIDATE_ENV_LOCAL_PASS` 只代表环境 contract + 本地 reward 路径可工作，不代表云端训练会成功。
3. **ATL-2 合成样本比例 71%**。本地 validate_env 仅用 5+2 条切片，contract check 不受样本偏差影响，但若进入 ATL-4+ 真实训练需重新评估数据代表性。
4. **simulated rollout 是空 tools**。本 Env 故意不暴露工具（rule-based grader），simulated rollout 只跑 `compute_reward`。真实训练若给模型工具调用能力，需补 `run_tool` 真实实现。

### 下一步

- **ATL-4** — Castform account / credit / billing preflight（需要用户显式提供 API key；仍先 preflight 不真实训练）。
