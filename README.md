# Java Project Agents Installer

这个仓库承载的是一个可分发的 skill：`JavaProjectAgentInstaller`。

它不是简单复制模板，而是让 agent 在目标 Java 项目里完成两件事：

1. 安装 `AGENTS.md`、`CLAUDE.md`、`.agents/rules/project-agents.md` 和 `ProjectAgents/` 文档。
2. 对目标项目做一轮首轮 review，尽量自动回填模块、构建体系、框架栈、配置入口、持久化 / 消息机制、测试目录等稳定信息，并把剩余待确认项留在 review 文档里。


## 亮点
- 统一入口：让 Codex、Claude Code、Cursor、OpenCode 等多个 agent 共读同一套项目文档，避免知识分散在不同工具的私有记忆里。
- 可沉淀：把一次性对话里的稳定结论回写成项目文档，后续任务可以直接复用，不必反复解释背景。
- 文档自我进化：文档不是一次性生成后就静止不动，而是可以随着后续任务持续补全、校正和细化。
- 降低误判：通过轻量模式 / 重型模式分层，避免一上来过度阅读，也避免复杂任务只看局部。
- 兼容现有项目：接入时不会粗暴覆盖已有文档，而是尽量合并、保留自定义内容、把冲突留给人工确认。
- 可复制：它不是某个项目的私有知识，而是一套可安装、可 review、可继续演化的接入模板。
- 有风险控制：默认把检索边界、git 使用、平台差异、公共层影响这些高风险点写进规则里，减少 agent 改错地方。

## Skill 目录

- `JavaProjectAgentInstaller/SKILL.md`：skill 触发说明和执行流程
- `JavaProjectAgentInstaller/scripts/install_project_agents.py`：安装 + 兼容处理 + 首轮 review 脚本
- `JavaProjectAgentInstaller/assets/template/`：原始 ProjectAgents 模板资产

## 兼容策略

- 现有 `AGENTS.md` / `CLAUDE.md` 不整体覆盖，只追加受控引导块。
- 现有 `ProjectAgents/*.md` 如果仍有模板占位符，会原地回填。
- 现有 `ProjectAgents/*.md` 如果已经有自定义内容，会保留原文件，并生成 `.incoming.md` 供后续合并。
- 执行安装前，先询问用户的安装偏好，并在用户明确确认后再运行安装流程。
- 每次安装都会生成 `ProjectAgents/references/project-agents-onboarding-review.md`，把自动识别结果和未完成 review 项列出来。
- 安装完成后应提示用户关闭这个 skill，否则在后续依赖语义识别的自动调用场景里可能继续被误触发。
