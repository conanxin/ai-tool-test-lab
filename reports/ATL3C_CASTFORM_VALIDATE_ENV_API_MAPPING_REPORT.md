# ATL-3C — Castform validate_env API Mapping & Real Local validate_env

**阶段结论**：**PASS** — `VALIDATE_ENV_LOCAL_PASS` — benchmax `validate_env` API 真实存在且本地 contract checks 10/10 通过。

## 1. 基线

- 当前基线 commit：`df00361`（ATL-3B）
- Python 3.12 venv/pip：PASS（沿用 ATL-3B 修复）
- benchmax：`0.1.2.dev33`（沿用 ATL-3B 安装）

## 2. benchmax 状态

| 项 | 值 |
|----|----|
| benchmax | `0.1.2.dev33` |
| install path | `.venv-castform-local/lib/python3.12/site-packages/benchmax/` |
| `benchmax.platform.validation` | 真实存在（`validation.py`） |
| `benchmax.platform.validation.validate_env` | 真实存在（函数） |
| `benchmax.envs.base_env.BaseEnv` | 真实存在（ABC） |
| BaseEnv 抽象方法 | `{"compute_reward", "list_tools", "run_tool"}` |

## 3. validate_env import path

```
from benchmax.platform.validation import validate_env
```

## 4. validate_env signature

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

## 5. validate_env docstring 摘要

两层验证合一：

1. **Local contract checks**（`local=True`，默认）— in-process、无网络，mirror trainer 调用：`dataset_preprocess`、`load_dataset`、`list_tools`/`run_tool`、`compute_reward`、simulated rollout、`compute_group_reward`、pickle round-trips。
2. **Remote smoke rollout**（`api_key` 给定时）— 把 env inline bundle，在云端跑 `remote_examples` 个真实 rollout。

调用形式：

```python
validate_env(env_class=Env, env_args={...}, train_dataset=rows)         # local only
validate_env(env_class=Env, env_args={...}, train_dataset=rows,
             api_key=API_KEY, base_url=BASE_URL, llm_base_url=LLM_URL)   # local + remote
```

**警告**：local pass 会用 dummy args 调用 env 的 tools 跑真实 backend；若 tool 有副作用（写 / 删 / 发），用 test backend。

## 6. environment candidate 说明

文件：`cases/castform-hermes-phase-closer-v0/local-validate-env/environment_validate_candidate.py`

`HermesPhaseCloserLocalEnv(BaseEnv)` — 满足 SDK 最小契约：

- `dataset_preprocess(cls, row)` — 接受 ATL-2 `{prompt, ground_truth}` 行 → 返回 `make_example(...)` 的 `Example(dict)` 含 `id`, `prompt_messages`, `task`。
- `load_dataset(cls, "json", data_files=..., split="train")` — 委托 `datasets.load_dataset`，返回 `(Dataset, None)`。
- `__init__(**env_args)` — 无副作用。
- `list_tools()` — 故意返回 `[]`（rule-based grader 无工具），让 validator 跳过 run_tool。
- `run_tool(...)` — 不可达（list_tools=[]），保留为 `NotImplementedError`。
- `compute_reward(...)` — 调用 `reward.score_completion`（已有 rule-based grader），返回 `dict[str, float]`。

无外部工具、无网络、无 API key、无真实项目数据；只读 ATL-2 脱敏 JSONL。

## 7. run_real_validate_env_attempt.py 结果

调用形式（不传 api_key/base_url/llm_*）：

```python
report = validate_env(
    env_class=HermesPhaseCloserLocalEnv,
    env_args={},
    train_dataset=train[:5],
    eval_dataset=eval[:2],
    local=True,
    api_key=None,
    base_url=None,
    llm_api_key=None,
    llm_base_url=None,
    verbose=True,
)
```

**输出（节选）**：

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

## 8. 本地脚本运行结果

| 脚本 | 结果 |
|------|------|
| `scripts/validate_jsonl.py` | PASS（42 train + 7 eval） |
| `scripts/validate_site.py` | PASS |
| `scripts/check_secrets.py` | PASS |
| `scripts/validate_castform_local_scaffold.py` | PASS |
| `scripts/validate_atl3c_sdk_mapping.py` | PASS |
| `cases/.../dataset_loader.py` | PASS（Train: 42 / Eval: 7） |
| `cases/.../run_local_reward_smoke.py` | PASS（5/5） |
| `cases/.../sdk-introspection/inspect_benchmax_validate_env.py` | PASS（无调用，纯 introspection） |
| `cases/.../run_real_validate_env_attempt.py` | **VALIDATE_ENV_LOCAL_PASS**（10/10） |
| `cases/.../run_validate_env_stub.py` | HISTORICAL_ATL3B_STUB_ONLY（明确指向 ATL-3C 脚本） |

## 9. 修改文件列表

- `cases/castform-hermes-phase-closer-v0/local-validate-env/sdk-introspection/inspect_benchmax_validate_env.py` — 新增（introspection）
- `cases/castform-hermes-phase-closer-v0/local-validate-env/sdk-introspection/ATL3C_VALIDATE_ENV_API_NOTES.md` — 新增（API 映射笔记）
- `cases/castform-hermes-phase-closer-v0/local-validate-env/environment_validate_candidate.py` — 新增（最小 Env）
- `cases/castform-hermes-phase-closer-v0/local-validate-env/run_real_validate_env_attempt.py` — 新增（真实本地 attempt）
- `cases/castform-hermes-phase-closer-v0/local-validate-env/run_validate_env_stub.py` — 重写为历史 stub 标记
- `cases/castform-hermes-phase-closer-v0/index.html` — 添加 ATL-3C 模块、更新 timeline 与证据块
- `data/cases.json` — phase/status/updated_at 更新为 ATL-3C PASS
- `README.md` — 当前状态块更新为 ATL-3C
- `docs/CASTFORM_VALIDATE_ENV_NOTES.md` — 追加 ATL-3C 章节
- `scripts/validate_atl3c_sdk_mapping.py` — 新增（scaffolding + secret + venv-tracked 检查）
- `reports/ATL3C_CASTFORM_VALIDATE_ENV_API_MAPPING_REPORT.md` — 本报告

## 10. git status

报告未自动 commit（由用户确认 "可以提交" 后再执行）。

## 11. 硬性边界遵守情况

| 边界 | 遵守 |
|------|------|
| 不调用 Castform API | ✓（`api_key=None` + `local=True` → `run_remote=False`） |
| 不上传任何数据 | ✓（未调用 `upload_training_run` / `dump_bundle` / `RolloutClient`） |
| 不启动 Castform training run | ✓（未调用 `launch_training_run` / `TrainerClient`） |
| 不使用真实 CASTFORM_API_KEY | ✓（`api_key=None`） |
| 不创建 .env | ✓ |
| 不读取或提交 .env / token / API key / cookie | ✓（`validate_atl3c_sdk_mapping.py` 也已扫描确认） |
| 不运行任何 cloud launch / upload / trainer client | ✓ |
| 不伪造 validate_env 成功 | ✓（脚本以状态枚举输出，且确实跑通 SDK 的 10/10 checks，非伪造） |
| 不提交 .venv-castform-local | ✓（已 .gitignore） |
| 不提交 /tmp/get-pip.py | ✓（仅 /tmp） |
| 只允许本地 SDK introspection | ✓（inspect_benchmax_validate_env.py 仅读模块签名/docstring） |
| 只允许 ATL-2 脱敏样本 | ✓（run_real_validate_env_attempt.py 用 train[:5] / eval[:2]） |
| validate_env 不允许要 API key / 网络 / 远端 | ✓（脚本只走 local 路径） |
| 若无法构造符合 Env contract，输出 BLOCKED_BY_ENV_CONTRACT_MAPPING | ✓（实际：契约 PASS；脚本也具备 BLOCKED_* 分支兜底） |
| 真实本地 validate_env 成功需证明无 API/上传/训练 | ✓（见 §12 证明） |

## 12. 证明：本次 validate_env 没有 API 调用 / 上传 / 训练

1. `api_key=None` ⇒ `validate_env` 源码 `run_remote = (not local) or bool(api_key)` ⇒ `run_remote = False` ⇒ 不构造 `RolloutClient` ⇒ 不调用 `client.RolloutClient.validate_examples` ⇒ 无 HTTP。
2. `local=True` ⇒ 进入 `_run_local_checks` 分支，仅 in-process 调用 env 的 `dataset_preprocess` / `load_dataset` / `list_tools` / `compute_reward` / `__init__`，外加 simulated rollout（无 tool）+ pickle round-trip。
3. 本 Env 的 `list_tools() = []` ⇒ validator 跳过 `run_tool`。
4. 本 Env 的 `compute_reward` 只调用本地 `reward.score_completion`（stdlib-only），不导入 `httpx` / `openai` / `requests`。
5. 脚本打印 `no Castform API call intended` / `no upload intended` / `no training intended`。
6. `pip_dependencies=[]` ⇒ 即使后续触发 bundle，也无额外 pip 安装。

## 13. 已知限制

1. **ATL-2 合成样本比例 71%**（来自 ATL-2 报告）。本地 validate_env 用的是 5 条 train + 2 条 eval 的小切片，sample 偏差不影响 contract check，但若进入 ATL-4+ 真实训练需重新评估数据代表性。
2. **当前模型训练尚未开始**。`VALIDATE_ENV_LOCAL_PASS` 只证明 Env 满足 SDK 契约 + 本地 reward 路径工作，**不代表云端真实训练会成功**。
3. **benchmax 0.1.2.dev33 是 pre-release**：validate_env 真实路径可能在 release 版改名 / 改签名；本结论以 PyPI 0.1.2.dev33 为准。
4. **simulated rollout 是空 tools**：本 Env 故意不暴露工具，simulated rollout 只跑 `compute_reward`。若进入 ATL-4+ 真实训练并希望模型用 tool 调用，需补 `run_tool` 真实实现。

## 14. 下一步建议

- **ATL-4** — Castform account / credit / billing preflight（仅当用户显式提供 API key 后启动；脚本继续只走 preflight，不真实训练）。preflight 内容建议：
  - 使用 `RolloutClient(api_key=KEY)` 仅做一次空 `validate_examples(remote_examples=0)` / 试探性 health endpoint 检查，确认 account 有效、billing 通道连通。
  - 不调用 `upload_training_run`，不调用 `launch_training_run`。
  - 若失败，明确分类 BLOCKED_BY_API_KEY_OR_NETWORK_REQUIREMENT，不伪造成功。

## 15. 阶段结论

**PASS** — `VALIDATE_ENV_LOCAL_PASS`（local 10/10 checks）。

未调用 Castform API，未上传数据，未训练。
