# ATL-6A — Starter-Style Redeploy Prep Report

## 阶段结论
SCRIPT_READY_NO_CLOUD_CALL

## 当前基线 commit
9c0e234 (ATL-6A, the previous-turn pack)
(本 phase (formal-spec alignment) 提交后会被新的 commit 取代)

## Starter-task analysis summary

The Castform Web App ships with example "Build your own" starter tasks
(visible in the ATL-4A preflight walkthrough). Those starters are
deliberately minimal: no RAG, no agent traces, no external tools, a
small structured dataset, a simple rule-based reward, and a small base
model (`Qwen/Qwen3.5-4B` for our case). The previous ATL-5/5B environment
shipped too much custom code to the cloud trainer (a custom
`load_dataset` override, a `run_tool` that raised `NotImplementedError`,
a 0–10 reward, an 8/2 preview subset). The starter-task philosophy is:
**less custom code in the cloud trainer ⇒ less surface area for the
bootstrap to fail.**

## Problem diagnosis

- **ATL-5B first run** `c83f971d-2b2c-42b8-9774-ca64938c1286` launched
  successfully but **failed at step 0** before producing any train / eval
  / rollout data.
- No UI-visible traceback or worker log was exposed by the Castform Web
  App.
- The SDK has **no read-only status / log method**
  (`NO_READ_ONLY_STATUS_METHOD_FOUND` from ATL-5C read-only probe).
- ATL-5D prepared a support-ready failure bundle
  (`ATL5D_SUPPORT_REQUEST.md`) but the user has not yet received a
  backend root cause.
- The local environment (`environment_validate_candidate.py`) **passes
  validate_env 10/10 locally** — so the contract is sound; the failure
  is in the remote cloud trainer bootstrap, not in the local code.

## Created files

- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/prepare_starter_style_subset.py` — stdlib subset prep (16 train / 4 eval)
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-train.preview.jsonl` — 16 rows
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-eval.preview.jsonl` — 4 rows
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/reward_starter_style.py` — 0.0~1.0 `score_completion` (format / coverage / score)
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/environment_starter_style.py` — `HermesPhaseCloserStarterStyleEnv` (no custom `load_dataset` override, `run_tool=""` no raise)
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/validate_starter_style_env.py` — local validate_env runner
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py` — cloud redeploy script (4 gates + local validate_env + upload + launch + result JSON)
- `cases/castform-hermes-phase-closer-v0/starter-style-redeploy/ATL6_STARTER_STYLE_REDEPLOY_NOTES.md` — rationale doc (why ATL-6 / starter-task lessons / old run / fix points / auth / not-done / manual recipe)
- `scripts/validate_atl6_starter_style_redeploy.py` — stdlib validator (per formal spec)
- `reports/ATL6A_STARTER_STYLE_REDEPLOY_PREP_REPORT.md` — this report

## Modified files

- `cases/castform-hermes-phase-closer-v0/index.html` — header line 65–66 (formal-spec wording) + ATL-6A section block (restructured: current phase / reason / starter-task lessons / changes / execution status / next step / files) + timeline entry + footer
- `data/cases.json` — phase = "ATL-6A starter-style redeploy prepared", status = "starter-style redeploy script ready; manual execution required"
- `README.md` — header (ATL-6A) + ATL-6A block + ATL-6A 验证 block (renamed `validate_atl6a_*.py` → `validate_atl6_*.py`, run_name + auth string aligned with formal spec)

## Dataset size

**16 train / 4 eval preview** (was 8 train / 2 eval in ATL-5B; never
uploads the full 49-row dataset). Subset is produced by
`prepare_starter_style_subset.py` from the existing ATL-2 redacted JSONL
samples.

## Environment changes (vs ATL-5/5B)

- **no custom `load_dataset` override** — closer to `BaseEnv` default
- **`list_tools` returns `[]`** (no tools)
- **`run_tool` returns `""`** and never raises `NotImplementedError`
- **system_prompt** fixed and declares the 7-header structured output
- **class name**: `HermesPhaseCloserStarterStyleEnv` (in
  `cases/.../starter-style-redeploy/environment_starter_style.py`)

## Reward changes (vs ATL-5/5B)

- **normalized to 0.0~1.0**: `score_completion` returns
  `{format, coverage, score}` with each component clamped to `[0.0, 1.0]`
- **defensive secret-pattern detection**: forces `score = 0.0` if a
  Castform API key / Bearer / Cookie / `cf_*` fragment appears in the
  completion
- **no LLM judge, no embedding lookup, no network call** — pure
  stdlib rule-based reward

## launcher_args changes

`batch_size` **removed**. `learning_rate: 1e-5` **added**. The 8 accepted
launcher_args are now exactly:

```json
{
  "model": "Qwen/Qwen3.5-4B",
  "learning_rate": 1e-5,
  "num_epochs": 1,
  "group_size": 2,
  "max_rollout_len": 512,
  "max_turns": 1,
  "lora_rank": 16,
  "lora_alpha": 32
}
```

## run_name

`hermes-phase-closer-starter-style-atl6` (independent of ATL-5
`hermes-phase-closer-smoke` and ATL-5B `hermes-phase-closer-smoke-atl5b`).

## Authorization statement

`I AUTHORIZE ATL-6 STARTER STYLE REDEPLOY` (no hyphen between "ATL-6"
and "STARTER"; "STARTER STYLE" with space, not "STARTER-STYLE").

## Local validate_env result (already exercised by agent)

`VALIDATE_ENV_LOCAL_PASS (local 10/10 checks)` — run via:

```bash
.venv-castform-local/bin/python \
  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/validate_starter_style_env.py
```

Inputs: 5 train rows + 2 eval rows. Contract: `local=True`, `api_key=None`,
no upload, no training, no network.

## Validation results (per formal spec)

- `python3 cases/castform-hermes-phase-closer-v0/starter-style-redeploy/prepare_starter_style_subset.py` → PASS (16 train / 4 eval written)
- `scripts/validate_atl6_starter_style_redeploy.py` → PASS (SKIPPED_RESULT_NOT_PRESENT, exit 0): starter-style-redeploy 目录存在 / 16 train / 4 eval / `run_tool` 不 raise / reward 0.0~1.0 / `launcher_args` 不含 `batch_size` 含 `learning_rate` / result JSON 缺失 → SKIPPED_RESULT_NOT_PRESENT
- 全部 12 个前置 validators 继续 PASS (validate_jsonl / validate_site / check_secrets / validate_castform_local_scaffold / validate_atl3c_sdk_mapping / validate_atl4a_preflight_scaffold / validate_atl4b_cloud_smoke_config / validate_atl4c_guarded_preflight / validate_atl5_cloud_smoke_result / validate_atl5a_launch_args_fix / validate_atl5b_second_upload_retry_result / validate_atl5c_failed_step0_record / validate_atl5d_support_bundle)
- `<redacted-key-prefix-literal>` repo-wide grep → 0 matches (validator 内部用字符串拼接构造 forbidden literal，源码不再含 bare 模式)
- 整个 ATL-5 / ATL-5B / ATL-5C / ATL-5D 历史 result JSON 完整保留：`atl5_cloud_smoke_result.json` + `atl5b_second_upload_launch_retry_result.json` + monitoring/ + support/ 全部未被覆盖

## Git status (before commit)

A  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/ATL6_STARTER_STYLE_REDEPLOY_NOTES.md
A  reports/ATL6A_STARTER_STYLE_REDEPLOY_PREP_REPORT.md (renamed from ATL6A_STARTER_STYLE_REDEPLOY_REPORT.md)
A  scripts/validate_atl6_starter_style_redeploy.py
D  reports/ATL6A_STARTER_STYLE_REDEPLOY_REPORT.md
D  scripts/validate_atl6a_starter_style_redeploy.py
M  README.md
M  cases/castform-hermes-phase-closer-v0/index.html
M  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py
M  data/cases.json

## Hard boundary compliance

- agent **未调用 Castform API**（无 upload、launch、TrainerClient 调用）
- agent **未访问 Castform UI**（无浏览器请求）
- agent **未上传数据**（prepare_starter_style_subset.py 只写本地 JSONL，不触网）
- agent **未启动训练**（atl6_starter_style_redeploy.py 未被运行；只跑过 local validate_env path）
- agent **未读取 API key**（脚本仅检查 `os.environ` 中 `CASTFORM_API_KEY` 是否存在，不读值）
- agent **未记录 API key**（gate log 仅显示 `present: True|False`；validate_atl6_starter_style_redeploy.py 6 secret patterns scan 全 PASS）
- **未提交 `.env`**
- **未提交 `.venv`**
- **未记录** 信用卡 / cookie / Authorization header / 用户邮箱 / 截图
- **未伪造** `run_id` / `experiment_url`（脚本在 launch 前不会填这两个字段，只在 result JSON 写 `null`）
- **未删除** 旧 Castform run
- **未重复运行** ATL-5B retry script
- **不覆盖** ATL-5 / ATL-5B 历史 result JSON

## Next step

用户在本地 WSL 显式授权后手动运行 redeploy 脚本（真实 Castform API 调用由用户执行）：

```bash
cd /mnt/d/AI/ai-tool-test-lab
export CASTFORM_API_KEY=*** CONFIG secrets here ***
export ATL_ALLOW_CASTFORM_UPLOAD=YES
export ATL_ALLOW_CASTFORM_LAUNCH=YES
export ATL_USER_AUTHORIZATION=*** AUTHORIZE ATL-6 STARTER STYLE REDEPLOY"
.venv-castform-local/bin/python \
  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/atl6_starter_style_redeploy.py
```

成功 result 写入 `cases/.../starter-style-redeploy/atl6_starter_style_redeploy_result.json`（独立文件，不覆盖 ATL-5 / ATL-5B 历史）。

## commit hash
(待提交后填入)

## whether pushed
否 (待 push)
