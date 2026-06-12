# ATL-0 报告：Castform 示例案例本地 Scaffold

## 阶段结论

ATL-0 完成。创建了 ai-tool-test-lab 开源静态网站项目，包含第一个测试案例 Castform — Hermes Phase Closer v0 的完整本地 scaffold。

## 创建的文件

- `index.html` — 首页
- `README.md` / `LICENSE` / `.gitignore`
- `assets/css/style.css` / `assets/js/app.js`
- `data/cases.json`
- `cases/castform-hermes-phase-closer-v0/index.html` — 案例详情页
- `cases/castform-hermes-phase-closer-v0/test-plan.md`
- `cases/castform-hermes-phase-closer-v0/local-readiness.md`
- `cases/castform-hermes-phase-closer-v0/reward-rubric.md`
- `cases/castform-hermes-phase-closer-v0/sample-train.jsonl`（5 条合成样本）
- `cases/castform-hermes-phase-closer-v0/sample-eval.jsonl`（3 条合成样本）
- `cases/castform-hermes-phase-closer-v0/castform-env-stub.py`
- `docs/ARCHITECTURE.md` / `CASE_TEMPLATE.md` / `ADDING_A_NEW_CASE.md` / `CASTFORM_NOTES.md`
- `scripts/validate_site.py` / `check_secrets.py` / `new_case.py`
- `reports/ATL0_CASTFORM_EXAMPLE_SCAFFOLD_REPORT.md`

## 第一个测试案例页面路径

`cases/castform-hermes-phase-closer-v0/index.html`

## 本地验证命令

```bash
cd /mnt/d/AI/ai-tool-test-lab
python3 scripts/validate_site.py
python3 scripts/check_secrets.py
```

## validate_site.py 结果

PASS

## check_secrets.py 结果

PASS

## git status

```
```

（working tree clean，无未提交变更）

## commit hash

`645add6`

## 安全声明

- **未调用 Castform API**
- **未上传任何数据**
- **未启动 Castform training run**
- **未使用真实 CASTFORM_API_KEY**
- **未 push 到 GitHub**
- 所有 JSONL 样本为合成虚构数据，不含真实项目信息

## 下一步建议

Phase 1：准备 30–50 条合成脱敏样本，覆盖成功/失败/部分完成/回滚/阻塞等场景。
