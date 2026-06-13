# ATL-4C — Guarded Castform Cloud Smoke Preflight Report

**Date**: 2026-06-13
**Phase**: ATL-4C
**Status**: **PASS_WITH_LAUNCH_BLOCKED**
**Project path**: `/mnt/d/AI/ai-tool-test-lab`
**Baseline**: `68fb302` (ATL-4A-CREDIT-FILL) · `b364bb7` (ATL-4B-CONFIG) · `ff22241` (ATL-4A) · `5f06de9` (ATL-3C)

## 阶段结论

`PASS_WITH_LAUNCH_BLOCKED` —— ATL-4C guarded cloud smoke preflight 包已交付：dual gate 架构（env var 授权 + 脚本级 guard + 配置级 tripwire）、`guarded_upload_preflight.py` / `guarded_launch_preflight.py`（默认拒绝 exit 1）、`FINAL_LAUNCH_GATE.md`（7 大 gate 清单）、`API_KEY_RUNTIME_ONLY.md`（read -s + export 注入规则）。`cloud_launch_allowed` 保持 `false`，`current_readiness` 保持 `BLOCKED_BY_UNCLEAR_CHARGES`，`actual_upload_allowed_in_this_phase=false`，`actual_launch_allowed_in_this_phase=false`。

## Guarded Upload / Launch 架构

Castform 真实训练启动分两步：

1. `upload_training_run` — 上传 environment（Python module）和 dataset（JSONL）到 Castform。
2. `TrainerClient.launch_training_run` — 启动 Castform GPU 训练 job。

两步均为危险动作（消耗 credit、启动 GPU 计算、创建云端状态）。ATL-4C 用 **triple gate** 控制：

### Gate 1 — Environment Variable Authorization

用户必须显式设置三个环境变量：

```bash
export CASTFORM_API_KEY="<redacted>"
export ATL_ALLOW_CASTFORM_UPLOAD="YES"
export ATL_ALLOW_CASTFORM_LAUNCH="YES"
```

- `CASTFORM_API_KEY`：真实 API key，仅通过 `read -s` + `export` 运行时注入。
- `ATL_ALLOW_CASTFORM_UPLOAD`：用户显式授权 upload 步骤。
- `ATL_ALLOW_CASTFORM_LAUNCH`：用户显式授权 launch 步骤。

若任一变量缺失或值不匹配，脚本拒绝继续并 exit 1。

### Gate 2 — Script-Level Guard

- `guarded_upload_preflight.py` — 默认拒绝 upload（exit 1），即使 env var 已设置。
- `guarded_launch_preflight.py` — 默认拒绝 launch（exit 1），即使 env var 已设置。
- 两个脚本均检查 `actual_upload_allowed_in_this_phase` / `actual_launch_allowed_in_this_phase`（必须为 `true` 才允许执行真实动作）。

### Gate 3 — Config-Level Tripwire

`guarded_cloud_preflight_config.json` 中：

- `cloud_launch_allowed: false`
- `current_readiness: "BLOCKED_BY_UNCLEAR_CHARGES"`
- `actual_upload_allowed_in_this_phase: false`
- `actual_launch_allowed_in_this_phase: false`

这些字段是机器可读 tripwire，validators 会检查。

## 生成 / 修改文件

- `cases/castform-hermes-phase-closer-v0/guarded-cloud-preflight/guarded_cloud_preflight_config.json` — 机器可读 guarded config
- `cases/castform-hermes-phase-closer-v0/guarded-cloud-preflight/README.md` — 架构与边界说明
- `cases/castform-hermes-phase-closer-v0/guarded-cloud-preflight/API_KEY_RUNTIME_ONLY.md` — API key 运行时注入规则
- `cases/castform-hermes-phase-closer-v0/guarded-cloud-preflight/FINAL_LAUNCH_GATE.md` — ATL-5 最终 launch gate 清单（7 大 gate）
- `cases/castform-hermes-phase-closer-v0/guarded-cloud-preflight/guarded_upload_preflight.py` — 默认拒绝 upload 的 guard 脚本
- `cases/castform-hermes-phase-closer-v0/guarded-cloud-preflight/guarded_launch_preflight.py` — 默认拒绝 launch 的 guard 脚本
- `scripts/validate_atl4c_guarded_preflight.py` — ATL-4C 验证脚本（59 项检查）
- `cases/castform-hermes-phase-closer-v0/index.html` — 更新（加入 ATL-4C 模块 + guard status grid + 时间线 + footer）
- `data/cases.json` — 更新（phase = `ATL-4C guarded cloud smoke preflight`，status = `guarded preflight ready; launch blocked by unclear charges`）
- `README.md` — 更新（顶部当前状态切换到 ATL-4C 收口）
- `reports/ATL4C_GUARDED_PREFLIGHT_REPORT.md` — 本报告

## Guard 状态复核（关键不变量）

| 字段 | 当前值 |
| --- | --- |
| `guarded_cloud_preflight_config.json` → `cloud_launch_allowed` | `false`（未改） |
| `guarded_cloud_preflight_config.json` → `current_readiness` | `BLOCKED_BY_UNCLEAR_CHARGES`（未改） |
| `guarded_cloud_preflight_config.json` → `actual_upload_allowed_in_this_phase` | `false`（未改） |
| `guarded_cloud_preflight_config.json` → `actual_launch_allowed_in_this_phase` | `false`（未改） |
| `cloud_smoke_config.json` → `cloud_launch_allowed` | `false`（未改） |
| `cloud_smoke_config.json` → `current_readiness` | `BLOCKED_BY_UNCLEAR_CHARGES`（未改） |
| `cloud_launch_guard.py` exit code | `1`（默认拒绝 launch） |
| `guarded_upload_preflight.py` exit code | `1`（默认拒绝 upload） |
| `guarded_launch_preflight.py` exit code | `1`（默认拒绝 launch） |

## 验证结果

- `validate_jsonl.py` **PASS**（42 train / 7 eval）
- `validate_site.py` **PASS**
- `check_secrets.py` **PASS**（未发现 secret-shaped 字符串）
- `validate_castform_local_scaffold.py` **PASS**
- `validate_atl3c_sdk_mapping.py` **PASS**
- `validate_atl4a_preflight_scaffold.py` **PASS**
- `validate_atl4b_cloud_smoke_config.py` **PASS**（49/49 OK）
- `validate_atl4c_guarded_preflight.py` **PASS**（59/59 OK；upload guard exit 1 + banner 6/6；launch guard exit 1 + banner 6/6；secret 扫描 clean；forbidden-call 扫描 clean）
- `prepare_cloud_smoke_subset.py` 仍 PASS（8+2 preview）
- `cloud_launch_guard.py` 仍 PASS（exit 1，banner 完整）
- `guarded_upload_preflight.py` PASS（exit 1，banner 完整，env var 缺失报告正确）
- `guarded_launch_preflight.py` PASS（exit 1，banner 完整，env var 缺失报告正确）

## 明确边界声明

- **未调用 Castform API**（无网络调用）
- **未上传任何数据**（`smoke-*.preview.jsonl` 仍为 preview-only，未触发 upload）
- **未启动 Castform training run**（`actual_launch_allowed_in_this_phase=false`，guard exit 1）
- **未创建 API key**（本仓库无 `CASTFORM_API_KEY`，无 `.env`）
- **未使用真实 CASTFORM_API_KEY**（无环境变量注入）
- **未创建 .env**（`.gitignore` 仍生效，仓库内无 `.env`）
- **未记录信用卡信息 / cookie / Authorization header / 用户邮箱 / 截图**
- **未运行 `upload_training_run` / `launch_training_run` / `TrainerClient.launch_training_run`**
- **未训练模型**
- **`cloud_launch_allowed` 未改为 `true`**
- **`current_readiness` 未改为 `READY`**

## 已知限制

1. **billing / auto-charge / cost estimate / run controls / data policy 仍多项 UNKNOWN** —— 从 ATL-4A-CREDIT-FILL 继承，未改变。
2. **未进行任何真实 launch / upload / API call** —— 全部基于 guarded 脚本默认拒绝 + 配置级 tripwire。
3. **preview subset 仍为 ATL-2 redacted JSONL 的前 N 行**：train 8 行 + eval 2 行；不构成最终训练数据。
4. **ATL-2 合成样本比例 71%** 不变。
5. **ATL-5 需要用户显式 flip config**：`actual_upload_allowed_in_this_phase`、`actual_launch_allowed_in_this_phase`、`cloud_launch_allowed` 必须由用户在 ATL-5 手动改为 `true`，agent 不得在 ATL-4C 自动 flip。

## git 状态

- `git status --short`: 干净（本阶段 commit 后）
- 预期 commit 列表：
  1. `guarded-cloud-preflight/` 目录（6 个新文件）
  2. `scripts/validate_atl4c_guarded_preflight.py`（新）
  3. `cases/castform-hermes-phase-closer-v0/index.html`（修改）
  4. `data/cases.json`（修改）
  5. `README.md`（修改）
  6. `reports/ATL4C_GUARDED_PREFLIGHT_REPORT.md`（新）

## 下一步建议

- **ATL-5 — Real cloud smoke run**（gated）：
  - 用户显式满足 `FINAL_LAUNCH_GATE.md` 全部 7 大 gate：
    1. 用户显式授权（"I AUTHORIZE ATL-5 CLOUD SMOKE RUN"）
    2. API key 运行时注入（`read -s` + `export`）
    3. 环境变量授权（`ATL_ALLOW_CASTFORM_UPLOAD="YES"` + `ATL_ALLOW_CASTFORM_LAUNCH="YES"`）
    4. 配置 lock（用户手动将 `cloud_launch_allowed` / `actual_upload_allowed_in_this_phase` / `actual_launch_allowed_in_this_phase` 改为 `true`）
    5. Smoke run 参数确认（run name / base model / 8 train / 2 eval / build_your_own_sdk）
    6. Risk acknowledgment（接受 billing / auto-charge 未完全明确的风险）
    7. Pre-launch verification（全部验证脚本 PASS）
  - 用户手动注入 `CASTFORM_API_KEY` 后，运行 `guarded_upload_preflight.py`（此时 `actual_upload_allowed_in_this_phase=true`）。
  - 上传成功后，运行 `guarded_launch_preflight.py`（此时 `actual_launch_allowed_in_this_phase=true`）。
  - 监控 training run 状态，记录日志和指标。
- 或在 ATL-5 之前**回填更多 UNKNOWN 字段**，让 launch 决策有更多事实依据。

## 风险评估

- **关键风险**：用户单方声明 `READY` + 多项 `UNKNOWN` 的 billing / cost / data policy 风险。ATL-4C 不消除这些风险，而是通过 triple gate 增加执行阻力。
- **缓解措施**：
  - `cloud_launch_allowed=false`（配置级 tripwire）
  - `actual_upload_allowed_in_this_phase=false` / `actual_launch_allowed_in_this_phase=false`（脚本级 guard）
  - `CASTFORM_API_KEY` + `ATL_ALLOW_CASTFORM_UPLOAD` + `ATL_ALLOW_CASTFORM_LAUNCH` 三重环境变量授权
  - `FINAL_LAUNCH_GATE.md` 7 大 gate 清单（用户必须逐项确认）
- **状态**：**launch 仍然 blocked**；本阶段不引入任何 new risk。
