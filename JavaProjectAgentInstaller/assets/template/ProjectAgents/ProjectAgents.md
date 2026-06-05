# Project Agents

这套说明会被多个 AI agent app 共同读取和增量维护，例如 Codex、Cursor、Claude Code、Antigravity、OpenCode 等；新增的稳定项目认知、检索规则、结构变化和风险约束，必须优先沉淀到 `ProjectAgents/ProjectAgents.md` 或 `ProjectAgents/references/` 下的专题文件，不要只留在某个 app 私有记忆、临时规则或对话上下文里。

默认先用轻量模式处理高频日常任务，只有在复杂度明显升级时，才切到重型模式。

> 首次落地时，先把全文中的 `[PLACEHOLDER]` 替换成目标项目真实信息；如果某条规则不适用，就删掉，不要保留空壳。

## 项目结构现状

先建立两个总前提：
- 先确认整个工作区是单一 git root，还是多个独立 git root；确认后再按实际仓库形态理解检索边界、变更范围和 git 命令执行位置，不要在未确认前直接假设成多 git 或单 git。
- 当前运行目标通常是 `[PRIMARY_RUNTIME_TARGET]`；如果项目存在多个 deployable、worker、CLI 入口或 profile，修改共享逻辑、公共配置、契约或基础设施时，仍要评估 `[SECONDARY_RUNTIME_TARGET_OR_PROFILE]` 以及其它运行变体的影响。

当前工作区根目录下可见的本地 module，建议至少列出：
- `[ENTRY_MODULE]`
- `[CORE_SHARED_MODULE]`
- `[API_CONTRACT_MODULE]`
- `[INFRASTRUCTURE_MODULE]`
- `[FEATURE_MODULE_EXAMPLE_A]`
- `[FEATURE_MODULE_EXAMPLE_B]`
- `[INTEGRATION_MODULES]`

如果项目确认存在多个独立 git root，再额外列出这些 git root 的目录边界和各自承载的模块范围。

还要按项目实际情况补充这些稳定事实：
- 如果根目录构建体系是 `[ROOT_BUILD_SYSTEM]`，把真正控制依赖版本、插件和公共构建逻辑的文件明确写出来，例如 `[ROOT_BUILD_FILES]`。
- 如果项目存在 parent BOM、starter、聚合模块、generated-code 模块或高隐式耦合依赖，把它们明确写出来，例如 `[SPECIAL_MODULE_OR_DEPENDENCY]`。
- 如果项目不是所有 module 都采用常规 `src/main/java + src/test/java` 布局，明确列出哪些模块存在 `src/integrationTest`、自定义 sourceSet、生成源码目录或脚手架目录。
- 如果项目里关键包名、配置文件、测试目录和部署上下文文件已经比较稳定，也要补成真实值，例如 `[PACKAGE_NAMESPACE_EXAMPLES]`、`[CONFIG_FILE_EXAMPLES]`、`[TEST_DIRECTORY_EXAMPLES]`、`[MODULE_EXTRA_CONTEXT_FILES]`。

## 文档维护约定

当使用过程里发现“这已经是稳定规则，不该只存在本次对话里”时，要立即落文档，并按粒度选择位置：
- 影响整个工作区的总规则、默认流程、结构现状、共性约束：更新 `ProjectAgents/ProjectAgents.md`
- 某个专题的细化说明，例如模块地图、检索手法、风险清单：更新 `ProjectAgents/references/` 下对应文件
- 如果现有专题文件都不适合承载，再新增一个 `references/*.md`，并在 `ProjectAgents.md` 里补入口说明

不要把这类稳定信息只写进某个 app 的专属规则、memory、scratchpad 或线程内总结，否则其它 agent app 无法继承。

需要更细的回写原则和落点示例时，再读 [references/doc-maintenance.md](references/doc-maintenance.md)。
每次对这些文档做稳定性更新后，还要在 [CHANGELOG.md](CHANGELOG.md) 追加一条简短变更记录，写清时间、app、git 提交人和本次改动重点。

## 默认模式

默认轻量模式是起手方式，适用于大多数分析、检索、修改和 review 任务。

### 默认规则

1. 先读当前任务直接相关的源码、配置、SQL、测试和调用点，再决定是否扩大范围。
2. 如果目标 module 根目录下存在 module 级 `AGENTS.md`、`CLAUDE.md` 或其它本地 agent 说明，在涉及该 module 代码时一并阅读，并把它当作局部补充说明；项目级 `ProjectAgents.md` 仍是总入口。把目标项目里已确认存在这类说明的模块补成 `[MODULE_WITH_LOCAL_AGENTS_EXAMPLES]`。
3. 默认不把 `build.gradle`、`build.gradle.kts`、`pom.xml`、根级构建脚本当成起手必读项；只有问题明显涉及依赖、打包、插件、运行 profile、代码生成、Bean 装配或部署行为时，再补看。
4. 检索优先使用 `rg --no-ignore` 和 `rg --files --no-ignore`。轻量模式只是减少默认读取的上下文，不缩小文件定位边界。
5. 对大文件、生成代码、常量表、协议模型、SQL 汇总文件禁止默认全量读取。先用 `rg` 精确搜索目标常量、关键字、调用点，再按命中位置读取必要片段。
6. 如果模块存在 `src/main`、`src/test`、`src/integrationTest`、`src/testFixtures`、生成源码目录或自定义 sourceSet，要检查源码和配置是否存在运行环境差异。
7. 不对历史特殊模块、外部 starter / BOM、annotation processor、代码生成产物或脚手架目录做默认预设；只有检索结果明确指向它们时，再补充分析。
8. 使用 `git status`、`git diff`、`git log`、`git blame` 等能力时，先确认项目是单 git 还是多 git；如果是多 git，再确认目标文件属于哪个 git root 并切到对应目录执行，不要用错误 git root 的结果判断业务代码变更。
9. 如果任务涉及官方文档查询，或需要操作数据库、消息队列、Docker、脚手架、代码生成器等外部工具，优先使用团队既有 `tools/`、`scripts/`、wrapper 命令或内部脚本；如果环境没有，就不要假设它存在。
10. 模块 compile / test 只在确有必要时才做，不要把编译当成每次任务的默认步骤；执行期间不要持续刷日志，只在结束后一次性获取成功状态或失败原因。
11. 修改代码时优先贴合项目现有写法、依赖风格和框架版本，不要无依据引入更重或更新的实现方式。
12. 写 Java 或 Kotlin 时优先复用项目已有工具类、基类、测试基座和约定式配置，不要重复造同类 helper。
13. 新增或修改配置时，先搜索同类配置键、profile 和装配方式；把目标项目关键配置入口补成 `[CONFIG_FILE_EXAMPLES]`。
14. 新增 Web / RPC / 消费者 / 定时任务时，先搜索同域已有入口模式和注册方式；把目标项目常见入口风格补成 `[WEB_ENTRY_PATTERN]`、`[MESSAGING_OR_EVENT_PATTERN]`。
15. 新增或调整持久化逻辑时，先检查现有 repository / mapper / DSL / migration 组织方式；把真实模式补成 `[PERSISTENCE_PATTERN]`、`[DB_MIGRATION_PATTERN]`。

### 默认工作流

#### 1. 聚焦目标

先回答这几个问题：
- 要看的核心对象是什么：类、方法、配置键、SQL、接口、消费者、任务，还是某个模块
- 它的定义在哪
- 谁直接调用它
- 改动会先落在哪个模块、package、配置文件或测试目录

如果这些问题还没答清，不要急着扩大全工作区，也不要先跳去读构建文件。

#### 2. 逐层检索

直接做全工作区搜索来定位文件，不要只在当前目录或已打开模块里搜索；如果项目确认存在多个 git root，还要覆盖其它相关 root。搜索必须加 `--no-ignore`，完全不考虑 `.gitignore`；区别只是定位后优先读取目标文件和直接引用链，不默认展开重型构建上下文。

如果命中的是大文件、生成模型、schema、常量汇总文件，不要直接整段展开。优先先搜关键字，再按命中行号读取局部上下文。

默认检索范围：
- `**/*.java`
- `**/*.kt`
- `**/*.groovy`
- `**/*.gradle`
- `**/*.gradle.kts`
- `**/pom.xml`
- `**/*.xml`
- `**/gradle.properties`
- `**/*.toml`
- `**/*.yml`
- `**/*.yaml`
- `**/*.properties`
- `**/*.sql`
- `**/*.proto`
- `**/*.avsc`
- `**/Dockerfile*`

默认排除：
- `**/build/**`
- `**/target/**`
- `**/.git/**`
- `**/.gradle/**`
- `**/.mvn/**`
- `venv/**`
- 其它明显生成物或缓存目录

推荐顺序：
1. 定义位置
2. 直接引用
3. 相关配置、测试、SQL 或 schema 引用
4. 依赖模块或上游入口
5. 必要时再看更大范围的间接影响

需要检索模式、查询顺序和结果分层时，再读 [references/search-playbook.md](references/search-playbook.md)。

#### 3. 检查运行差异

当模块含有 profile、测试目录、生成源码目录或部署差异目录时，重点检查：
- `src/main`
- `src/test`
- `src/integrationTest`
- `src/testFixtures`
- `src/generated*`
- `application*.yml` / `application*.properties`
- `pom.xml` profile 或 Gradle task / sourceSet 差异

如果当前改动只落在公共逻辑，也要快速确认是否会被 profile、starter、自动配置、外部集成或生成代码覆盖掉。

#### 4. 谨慎修改或评审

在真正动手前，至少确认：
- 是否会影响多个模块
- 是否存在 profile、测试目录、sourceSet 或生成代码差异
- 是否改到了公共契约、DTO、序列化结构、配置键或对外接口
- 是否需要最小回归验证

如果有明显未知项，要直接说明，不要假装已经覆盖。

## 进入重型模式的条件

只有当任务明确命中以下情况之一时，才进入重型模式：
- 需要系统理解整个聚合工作区，而不是只分析目标模块和直接调用链
- 明确涉及根级 Gradle / Maven、模块注册、依赖映射、打包或复杂构建链路
- 明确涉及 profile、自动配置、annotation processor、生成代码或更深的 sourceSet 差异
- 明确涉及 parent BOM、starter、外部集成、数据库迁移、消息系统或历史特殊模块规则
- 改动跨越多个关键模块、服务契约、共享基础层或部署入口，默认风险偏高

进入重型模式后，不要继续按主文档里的轻量节奏推进，改为按 [references/heavy-mode.md](references/heavy-mode.md) 的完整规则处理。

## 模块认知

需要模块职责、分层、模块间通信或风险预期时，再读 [references/module-map.md](references/module-map.md)。以下区域通常要特别关注，落地时替换成真实模块名：
- `[ENTRY_MODULE]`：入口最多、装配最复杂或最接近实际运行单元的核心模块
- `[CORE_SHARED_MODULE]`：共享业务逻辑和通用能力聚合层
- `[API_CONTRACT_MODULE]`：对外契约、DTO、client 或 SPI 聚合层
- `[INFRASTRUCTURE_MODULE]`：数据访问、持久化、缓存或基础设施模块
- `[SPECIAL_MODULE_OR_DEPENDENCY]`：parent BOM、starter、generated-code 模块或高隐式耦合模块

## 默认输出结构

当用户要求分析某个类、模块、bug 或改动时，默认覆盖：
1. 目标对象和职责
2. 定义位置
3. 直接引用位置；如果已进入重型模式，再补全工作区引用位置
4. 相关模块或调用链
5. runtime / profile / sourceSet 差异点（如果有）
6. 改动风险点
7. 建议验证方式
8. 仍不确定的假设或未知项
