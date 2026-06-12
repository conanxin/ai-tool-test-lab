# ATL-3B — Python 3.12 venv/pip Repair & benchmax Import

**阶段结论：** **PASS** — benchmax import works

## 1. 基线

- 当前基线 commit：`97abd7e`（ATL-3A）
- Python 3.12：可用（Python 3.12.3）
- 项目路径：`/mnt/d/AI/ai-tool-test-lab`

## 2. .gitignore 更新

补充排除 venv：

```
.venv-castform-local/
.venv*/
```

旧的 `.venv/` / `venv/` 保留向后兼容。

## 3. venv 创建结果

- 删除旧 venv：`rm -rf .venv-castform-local`
- **方式 A（`ensurepip`）失败**：
  ```
  The virtual environment was not created successfully because ensurepip is not
  available. On Debian/Ubuntu systems, you need to install the python3.12-venv package.
  ```
- **方式 B（`--without-pip` + `/tmp/get-pip.py`）成功**：

  ```bash
  rm -rf .venv-castform-local
  python3.12 -m venv --without-pip .venv-castform-local
  curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
  .venv-castform-local/bin/python /tmp/get-pip.py
  .venv-castform-local/bin/python -m pip --version    # pip 26.1.2
  ```

- 整个过程未使用 `sudo apt` / `sudo dpkg`。
- `get-pip.py` 仅放在 `/tmp`，未复制进项目目录。

## 4. pip 修复方式

- pip 版本：`26.1.2`（在 `.venv-castform-local/lib/python3.12/site-packages/pip`）
- 来源：`https://bootstrap.pypa.io/get-pip.py`（官方 PyPA bootstrap）
- 已升级至最新（`pip install --upgrade pip` already-satisfied）。

## 5. benchmax 安装结果

- 安装命令：`.venv-castform-local/bin/python -m pip install benchmax`
- 安装结果：**PASS**（耗时约 5 分钟，包含 pandas 10.9MB 等大依赖）
- 已安装版本：

  ```
  benchmax-0.1.2.dev33
  aiohttp-3.14.1 aiosignal-1.4.0 anyio-4.13.0 datasets-5.0.0
  httpcore-1.0.9 httpx-0.28.1 huggingface_hub-1.19.0
  markdown-it-py-4.2.0 multiprocess-0.70.19 openai-2.41.1
  pandas-3.0.3 pydantic-2.13.4 pydantic-core-2.46.4
  python-dateutil-2.9.0.post0 rich-15.0.0 typer-0.25.1
  ```

## 6. benchmax import 结果

```python
import importlib
m = importlib.import_module("benchmax")
# benchmax import PASS
# benchmax module: <module 'benchmax' (namespace) from ['.../site-packages/benchmax']>
# benchmax file: None
# benchmax version: ''
```

- **`import benchmax` PASS** — `benchmax` 是一个 namespace package。
- namespace package 无 `__init__.py`，`__file__` / `__version__` 为空，但 `importlib.import_module("benchmax")` 成功表示入口可达。
- 本阶段 **未执行** 任何 `benchmax.<submodule>` 调用，未触发 cloud validate_env。

## 7. 本地脚本运行结果

| 脚本 | 结果 | 备注 |
|------|------|------|
| `scripts/validate_jsonl.py` | PASS | 42 train + 7 eval |
| `scripts/validate_site.py` | PASS | root / docs / scripts / case page 完整 |
| `scripts/check_secrets.py` | PASS | 已扩展 IGNORE_DIRS 加入 `.venv-castform-local` |
| `scripts/validate_castform_local_scaffold.py` | PASS | environment_stub.py 注释去掉了 forbidden 字符串字面量 |
| `cases/.../dataset_loader.py` | PASS | Train: 42 samples / Eval: 7 samples |
| `cases/.../run_local_reward_smoke.py` | PASS | 5/5（好完成 3 个 10 分 / 差完成 0 分 / 含 sk- 测试串 0 分） |
| `cases/.../run_validate_env_stub.py` | **BENCHMAX_IMPORT_PASS_VALIDATE_ENV_NOT_RUN** | benchmax 可导入，未执行真实 validate_env |

## 8. run_validate_env_stub.py 增强

stub 现在显式三态，避免伪造 cloud success：

- `SKIPPED_WITH_REASON` — benchmax 不可导入（pip/venv 异常）
- `BENCHMAX_IMPORT_PASS_VALIDATE_ENV_NOT_RUN` — benchmax 可导入，未执行真实 validate_env（**本阶段目标**）
- `VALIDATE_ENV_LOCAL_PASS` — 只有真正本地 validate_env 且无 API key / 无上传 / 无训练时才允许

明确输出 `NO_CASTFORM_API_CALL` / `NO_UPLOAD` / `NO_TRAINING` / `NO_VALIDATE_ENV_LOCAL_PASS`。

## 9. 修改文件列表

- `.gitignore` — 补充 `.venv-castform-local/` 与 `.venv*/`
- `scripts/check_secrets.py` — IGNORE_DIRS 加入 `.venv-castform-local` 与 `.venv*`
- `cases/castform-hermes-phase-closer-v0/local-validate-env/run_validate_env_stub.py` — 重写为三态 stub
- `cases/castform-hermes-phase-closer-v0/local-validate-env/run_local_reward_smoke.py` — secret_completion 用占位符 + sk- 合成 token 形式（check_secrets 友好）
- `cases/castform-hermes-phase-closer-v0/local-validate-env/environment_stub.py` — 注释去掉 forbidden 字面量
- `cases/castform-hermes-phase-closer-v0/index.html` — 添加 ATL-3B 模块，更新 timeline 与证据块
- `data/cases.json` — phase/status/updated_at 更新
- `README.md` — 当前状态块更新为 ATL-3B
- `docs/CASTFORM_VALIDATE_ENV_NOTES.md` — 新增 ATL-3B 修复路径与三态说明
- `reports/ATL3B_PYTHON_VENV_BENCHMAX_REPAIR_REPORT.md` — 本报告

## 10. git / push

- 提交前：`git status --short` 仅有 `.venv-castform-local/`（被 .gitignore 排除）
- 本报告未自动 commit — 由用户确认 "可以提交" 后再执行。

## 11. 硬性边界遵守情况

| 边界 | 遵守 |
|------|------|
| 不调用 Castform API | ✓ |
| 不上传任何数据 | ✓ |
| 不启动 Castform training run | ✓ |
| 不使用真实 CASTFORM_API_KEY | ✓ |
| 不创建 .env | ✓ |
| 不读取或提交 .env / token / API key / cookie | ✓ |
| 不运行 upload_training_run / launch_training_run / TrainerClient | ✓ |
| 不伪造 validate_env 成功 | ✓（明确 `BENCHMAX_IMPORT_PASS_VALIDATE_ENV_NOT_RUN`） |
| 不提交 .venv-castform-local | ✓（已 .gitignore） |
| 不提交 /tmp/get-pip.py | ✓（只放 /tmp） |
| 优先不使用 sudo apt / sudo dpkg | ✓（方式 A 失败后用 `--without-pip` + `/tmp/get-pip.py`） |
| 可以安装 benchmax 到本地 venv | ✓ |
| 可以提交文档 / 脚本 / 报告 | ✓ |

## 12. 已知限制

1. benchmax 为 namespace package，本阶段未执行其子模块，未触发 cloud 侧请求。
2. `__version__` 为空，需要版本判定时建议 `pip show benchmax`。
3. 本地未跑 cloud-side smoke run，无网络侧 cost / latency 反馈。
4. Castform 真实 `validate_env` 是否能纯本地运行（不调用 cloud）需 ATL-3C 验证。

## 13. 下一步建议

- **ATL-3C** — 映射官方 `validate_env` API，尝试真正本地 validate_env：
  1. 通过 PyPI / GitHub README 找 `benchmax` 子模块入口
  2. 检查官方是否提供 "validate env without uploading" 模式
  3. 若官方仅云端路径，本地只能"伪 validate_env"（不计入 `VALIDATE_ENV_LOCAL_PASS`）
- **ATL-4** — Castform account / credit / billing preflight（仅当用户显式提供 API key 后启动，且仍先做 preflight 而非真实训练）
- **ATL-5** — Playground 评估（依赖 ATL-3C 或 ATL-4 完成）

## 14. 阶段结论

**PASS** — benchmax import works。

未调用 Castform API，未上传数据，未训练。
