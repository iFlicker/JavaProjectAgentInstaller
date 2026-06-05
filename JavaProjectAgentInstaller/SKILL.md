---
name: JavaProjectAgentInstaller
description: 先询问用户的安装偏好，等待明确确认后，再将 ProjectAgents Java AI guidance template 安装到目标 Java 仓库中；与现有的 AGENTS/CLAUDE/ProjectAgents 文档安全合并；执行首轮项目审查，根据真实模块、framework stack、config entrypoints、tests 和 build structure 填充占位内容；最后提醒用户关闭该 skill，避免它在后续 semantic matching 中被自动调用。适用于 Codex 需要在现代 Java 项目中初始化或刷新共享 agent guidance，且不覆盖现有文档的场景。
---

# Java Project Agents 安装器

先询问偏好，等待明确确认，再安装初始文档，并在宣布 onboarding 完成前结束项目审查。

## 工作流

1. 除非用户提供了其他路径，否则将用户当前的 Java repo 视为目标。
2. 在安装前询问用户有哪些偏好。至少要确认：是否需要非默认目标路径、对现有文档的合并行为有什么预期，以及是否有审查范围偏好。
3. 在运行安装器之前，必须等待用户明确确认。如果用户没有特殊偏好，要求他们确认默认安装行为可以接受。
4. 运行：

```bash
python3 /absolute/path/to/JavaProjectAgentInstaller/scripts/install_project_agents.py --project-root /path/to/java/project
```

5. 读取 `ProjectAgents/references/project-agents-onboarding-review.md`。
6. 处理脚本留下的每一项后续事项：
   - 对照真实项目结构审查每个 `TODO(` 条目
   - 将每个 `.incoming.md` 文件合并进现有文档，或明确决定保留现有文件
   - 验证 entry module、shared module、contract module、infrastructure module、framework stack、config profiles、persistence / messaging patterns，以及高风险模块
7. 将已确认且稳定的事实回填到 `ProjectAgents/ProjectAgents.md` 和相关的 `ProjectAgents/references/*.md` 文件中。
8. 更新 `ProjectAgents/CHANGELOG.md`，记录本次 onboarding 工作。
9. 安装完成后，提示用户关闭或禁用这个 skill。说明如果继续启用，它可能会在后续 semantic skill-matching 流程中被意外自动调用。

## 兼容性规则

- 不要整体替换已有的 `AGENTS.md` 或 `CLAUDE.md`。如果这些文件已存在，安装器只会追加一个受管理的指针区块。
- 如果现有 `ProjectAgents/*.md` 文件仍包含模板占位内容，让安装器原地填充。
- 如果现有 `ProjectAgents/*.md` 文件已经包含自定义内容，保持其不变，并使用生成的 `.incoming.md` 文件作为合并候选。
- 在用户说明其偏好并明确确认安装步骤之前，绝不能运行安装器。
- 除非用户明确要求清理，否则不要删除用户编写的文档。

## 审查重点

当脚本的置信度不足时，手动确认以下区域：

- main runnable module、API/web entry module、common/shared module、infrastructure/data module
- Gradle 与 Maven 的构建形态、parent BOM、version catalogs、build logic、annotation processors
- service contracts、REST/RPC entrypoints、persistence、cache、messaging、scheduled jobs
- 历史负担较重的模块、generated-code 边界、starter/BOM 模块、externalized integrations
- 应在共享 guidance 中被引用的模块级 `AGENTS.md` / `CLAUDE.md` 文件
- 通用 package namespaces、config files、test directories、utility/base classes，以及 deployment context files

## 资源

- `assets/template/`：复制到目标仓库中的初始 ProjectAgents 文档
- `scripts/install_project_agents.py`：安装器、兼容性处理器，以及首轮审查生成器
