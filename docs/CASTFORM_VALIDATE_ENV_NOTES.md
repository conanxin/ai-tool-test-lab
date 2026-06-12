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
