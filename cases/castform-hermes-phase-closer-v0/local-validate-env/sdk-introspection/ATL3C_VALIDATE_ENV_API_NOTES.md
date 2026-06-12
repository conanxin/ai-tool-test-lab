# ATL-3C — benchmax validate_env API Mapping Notes

**结论**：**VALIDATE_ENV_LOCAL_PASS** — `benchmax.platform.validation.validate_env` 真实存在，本地 contract checks 全部通过 10/10。

## 1. validate_env import path

```
benchmax.platform.validation.validate_env
```

真实存在于 `benchmax 0.1.2.dev33`：

```
site-packages/benchmax/platform/validation.py
```

## 2. validate_env signature

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

- `local=True` 为默认，**只要不传 `api_key` 就不调用 `RolloutClient`** → 纯本地、零网络。
- `api_key=None` + `local=True` → `run_remote = False` → 完全跳过远程 smoke rollout。
- `ValidationReport` 是 bool-castable：`bool(report)` 即整体 PASS/FAIL。

## 3. validate_env docstring 摘要（前 1000 字符）

> Validate an environment before launching a training run.
>
> A single entry point that folds together the two validation layers:
>
> 1. **Local contract checks** (`local=True`, the default) — run in-process
>    with no network, mirroring how the trainer calls env methods
>    (dataset_preprocess, load_dataset, list_tools/run_tool, compute_reward,
>    a simulated rollout, compute_group_reward, pickle round-trips).
> 2. **Remote smoke rollout** (runs when `api_key` is given) — bundles the
>    env inline and runs `remote_examples` real rollouts on the platform …
>
> Pass nothing but the env + dataset for a fast offline check; add
> `api_key` (and, if your script's environment differs from the SDK
> defaults, `base_url`/`llm_base_url`) to also smoke-test against the
> platform::
>
>     validate_env(env_class=Env, env_args={...}, train_dataset=rows)          # local only
>     validate_env(env_class=Env, env_args={...}, train_dataset=rows,           # local + remote
>                  api_key=API_KEY, base_url=BASE_URL, llm_base_url=LLM_URL)
>
> Warning: The local pass calls your env's tools with dummy arguments against
> real backends. If your tools have side effects (writes, deletes, sends),
> use a test backend.

## 4. Env 契约（来自 `benchmax.envs.base_env.BaseEnv`）

`BaseEnv.__abstractmethods__ == frozenset({"compute_reward", "list_tools", "run_tool"})`。

加上 validator 还会显式调用的类方法，Env 必须实现：

| 方法 | 形态 | 期望 |
|------|------|------|
| `dataset_preprocess(cls, row)` | classmethod | 返回 dict 含 `id` (str) + `prompt_messages` (list[{role,content}])；可选 `task`, `init_rollout_args` |
| `load_dataset(cls, "json", data_files=..., split="train")` | classmethod | 返回 `(Dataset, str\|None)`；至少 1 行 |
| `__init__(self, **env_args)` | instance | 无副作用即可 |
| `list_tools(self)` | async | 返回 `list[ToolDefinition]`；空 list 时 run_tool 检查自动跳过 |
| `run_tool(self, rollout_id, tool_name, **args)` | async | 仅在 tools 非空时调用，返回 `str` |
| `compute_reward(self, rollout_id, messages, task, **kwargs)` | async | 返回 `dict[str, float]`（值必须 finite，不能 NaN/Inf） |
| `compute_group_reward(...)` | async（可选） | 默认实现返回 `[{}]`；覆盖时 validator 才检查 |

校验器还会自动：
- 模拟一次 simulated rollout（每个 tool 跑 2 次防 stateful bug）
- pickle round-trip env class
- 自动 bundle `local_modules` 引用到的所有本地 module（environment_validate_candidate + reward 都被自动捕获）

## 5. 真实本地 validate_env 执行结果

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

**10/10 PASS**。

## 6. 是否调用 Castform API / 上传 / 训练

| 项 | 本阶段 |
|----|------|
| Castform API 调用 | **无**（`api_key=None` + `local=True` → `run_remote=False`） |
| 上传训练数据 | **无**（没调用 `upload_training_run` / `dump_bundle` / `RolloutClient`） |
| 启动训练 | **无**（没调用 `launch_training_run` / `TrainerClient`） |
| 网络 | **无**（仅本地进程内调用 `benchmax.platform.validation._run_local_checks`） |

## 7. 下一步

- **ATL-4** — Castform account / credit / billing preflight（需要用户显式提供 API key；仍先 preflight 不真实训练）。

## 8. 已知限制

1. **benchmax 是 dev33 pre-release**（`benchmax-0.1.2.dev33`），validate_env 真实路径可能在 release 版改名 / 改签名；本结论以 PyPI 0.1.2.dev33 为准。
2. **真实 cloud training 仍未发生**。`VALIDATE_ENV_LOCAL_PASS` 只代表环境 contract 与本地 reward 路径可工作，不代表 cloud 训练会成功。
3. **ATL-2 合成样本比例 71%**（来自 ATL-2 报告）。本地 validate_env 用的是 5 条 train + 2 条 eval 的小切片，sample 偏差不影响 contract check，但若进入 ATL-4+ 真实训练需重新评估数据代表性。
4. **simulated rollout 是空 tools**。本 Env 故意不暴露工具（rule-based grader），所以 simulated rollout 只跑 `compute_reward`，没有 tool-call 分支。真实训练若给模型工具调用能力，需补 `run_tool` 真实实现。
