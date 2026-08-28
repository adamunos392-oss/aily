---
name: git-workflow
description: SDD V7_2 Git 工作流：项目 Git 仓库初始化、origin 配置（含 repo_url 记录补配）、提交、推送门禁。触发：仓库配置检查、提交代码、用户验收后推送。
---

完整定义见 `harness-core/skills/git-workflow/SKILL.md`（唯一真相源）：初始化、提交、推送的门禁与降级路径一律以该文件为准。主要由开发循环推送门禁调用；主对话说"提交 / 推送 / 配仓库"亦可进入。本文件只提供本平台加载入口。
