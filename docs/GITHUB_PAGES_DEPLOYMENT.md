# GitHub Pages 发布指南

## 创建 GitHub 仓库

1. 登录 GitHub，点击右上角 **+** → **New repository**
2. 仓库名：`ai-tool-test-lab`
3. 描述：Open-source test lab for evaluating AI tools, workflows, and agent-driven experiments.
4. 选择 **Public**
5. 不勾选 README、.gitignore、license（本地已有）
6. 点击 **Create repository**

## 推送本地仓库

```bash
cd /path/to/ai-tool-test-lab
git remote add origin https://github.com/conanxin/ai-tool-test-lab.git
git branch -M main
git push -u origin main
```

## 启用 GitHub Pages

1. 进入仓库 **Settings** → **Pages**
2. **Source**：选择 **Deploy from a branch**
3. **Branch**：选择 `main`，文件夹选择 `/ (root)`
4. 点击 **Save**

## 等待部署

- GitHub Pages 通常在 1–2 分钟内完成部署
- 访问地址：`https://conanxin.github.io/ai-tool-test-lab/`

## 验证

- 检查首页是否正常显示
- 检查 Castform 案例页是否正常显示
- 检查所有链接是否可访问

## 注意事项

- 本项目是纯静态 HTML/CSS/JS，不需要 GitHub Actions
- 不需要构建步骤（无 npm、无 webpack、无 bundler）
- 每次 push 到 main 分支后，GitHub Pages 会自动重新部署
- 如果页面样式异常，检查 CSS 路径是否为相对路径（`assets/css/style.css`）

## 更新流程

```bash
git add <修改的文件>
git commit -m "描述更新内容"
git push origin main
```

等待 1–2 分钟后，线上页面自动更新。
