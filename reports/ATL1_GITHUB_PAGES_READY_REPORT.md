# ATL-1 报告：GitHub Pages 发布准备

## 阶段结论

ATL-1 完成。AI Tool Test Lab 已完善公开展示质量，适合推送到 GitHub 并启用 GitHub Pages。

## 修改文件列表

| 文件 | 变更 |
|------|------|
| `index.html` | 增加项目介绍区、工作流说明（Discover→Plan→Local Test→Cloud Test→Evaluate→Publish）、案例状态说明 |
| `assets/css/style.css` | 增强样式：workflow 步骤、状态 badge、卡片悬停、移动端适配 |
| `assets/js/app.js` | 增加 phase badge 和 summary 字段渲染 |
| `data/cases.json` | 增加 summary、updated_at 字段 |
| `cases/castform-hermes-phase-closer-v0/index.html` | 增加测试摘要、当前阶段、本地角色、云端角色、为什么不在本地训练、测试时间线、下一阶段计划、当前证据 |
| `docs/GITHUB_PAGES_DEPLOYMENT.md` | 新增：创建仓库、推送、启用 Pages、验证、更新流程 |
| `docs/ROADMAP.md` | 新增：ATL-0 到 ATL-6 完整路线图 |
| `README.md` | 更新：当前状态、本地运行、GitHub Pages 发布链接、路线图链接 |

## 首页更新摘要

- 项目介绍：AI Tool Test Lab 是一个记录 AI 工具、平台、开源项目真实测试过程的开源实验室
- 工作流：6 步骤可视化（Discover → Plan → Local Test → Cloud Test → Evaluate → Publish）
- 状态说明：5 种状态 badge（Local scaffold ready / Local validation / Cloud smoke run / Evaluated / Archived）
- 案例卡片增强：phase badge + summary 摘要

## Castform 案例页更新摘要

- 测试摘要：对象、目标、阶段、状态
- 当前阶段：ATL-0 完成内容
- 本地角色：数据整理、reward 脚手架、dry-run、页面维护
- 云端角色：GPU 训练、playground 评估、batch 生成
- 为什么不在本地训练：GTX 1070 8GB / 7.7GB RAM / i7-6700 4C/8T
- 测试时间线：ATL-0 到 ATL-6
- 下一阶段：ATL-2 准备 30–50 条样本
- 当前证据：commit d069f86、validate PASS、check_secrets PASS、未调用 API

## 新增文档

- `docs/GITHUB_PAGES_DEPLOYMENT.md` — 从创建仓库到启用 Pages 的完整指南
- `docs/ROADMAP.md` — ATL-0 到 ATL-6 的路线图

## 验证结果

- `validate_site.py`：PASS
- `check_secrets.py`：PASS

## git status

working tree clean

## commit hash

待 commit

## 安全声明

- 未调用 Castform API
- 未上传数据
- 未训练模型
- 未 push 到 GitHub
- 无 token / IP / .env 泄露

## 下一步建议

ATL-2：准备 30–50 条合成脱敏样本，覆盖 PASS / FAIL / PARTIAL / ROLLBACK / BLOCKED 场景。
