# SDD V7_2 Project

本项目由 SDD V7_2 管理。

核心目录：

- `.sdd/`：项目状态、任务、经验、日志、测试报告
- `docs/`：PRD、API 契约、开发计划、原型；GitHub Pages 入口与静态工作台也在此目录
- `AGENTS.md`：项目轻入口；核心规则仍在 Harness 根目录 `harness-core/`

## GitHub Pages 托管

静态站发布自仓库 `docs/`（GitHub 允许的 Pages 目录只有仓库根 `/` 或 `/docs`）。产品文档仍保留在 `docs/`，工作台构建产物放在 `docs/app/`，避免覆盖 PRD。

- 演示地址：https://adamunos392-oss.github.io/aily/
- 工作台：https://adamunos392-oss.github.io/aily/app/
- GitHub Pages 无 FastAPI，托管站使用前端 Mock（`VITE_USE_MOCK=true`）

重新生成静态站：

```bash
cd frontend
npm run build:pages
```

仓库 Settings → Pages 可选：

1. **GitHub Actions**（已配置 `.github/workflows/pages.yml`，推送 `main` 后自动发布 `docs/`）
2. 或 **Deploy from a branch**：`main` / `/docs`
