# 重型模式

只有当主文档里定义的触发条件明确命中时，才进入这里；否则默认仍按轻量模式处理。

## 重型规则

1. 先确认项目是单一 git root 还是多个独立 git root。确认后，仍以整个业务工作区作为检索边界；如果项目确实存在多个独立 git root，再把它们当成同一个业务工作区的一部分分析。
2. 先读根级关键文件：`settings.gradle`、`settings.gradle.kts`、`build.gradle`、`build.gradle.kts`、`gradle.properties`、`gradle/libs.versions.toml`、`pom.xml`，以及项目实际存在的 `[ROOT_BUILD_FILES]`；如果工程使用 `buildSrc/`、`build-logic/`、`.mvn/`、parent BOM 或其它公共构建逻辑目录，也一并列入根级上下文。
3. 再读目标模块的 `build.gradle`、`build.gradle.kts`、`pom.xml`、关键配置文件和测试目录；如果模块存在自定义 sourceSet、integration test、生成源码目录或 profile 配置，必须同时检查对应上下文。
4. 如果目标模块还带额外装配、部署、协议或代码生成文件，也要把它们一并列入必读项，例如 `[MODULE_EXTRA_CONTEXT_FILES]`。
5. 把 annotation processor、OpenAPI / protobuf / jOOQ 之类生成配置、版本映射和运行 profile 视为功能上下文的一部分。本地看得到的源码路径，可能只是生成结果或局部实现，不一定代表真实运行入口。
6. 如果项目里有 parent BOM、starter、聚合模块、发布用平台模块或高耦合共享依赖，把它们视为外部依赖上下文的一部分；除非任务明确要求深入本地目录，否则不要把它当成稳定可改的普通业务模块。
7. 使用 `git status`、`git diff`、`git log`、`git blame` 等对比或历史能力时，先确认项目是单 git 还是多 git；如果是多 git，再按目标文件所属 module 或 git root 执行，不要用错误 git root 的结果替代真实上下文。
8. 大文件、生成代码、schema、依赖清单在重型模式下也不自动全量通读；即使进入重型模式，也先检索目标符号、字段、配置段，再局部读取命中片段。
9. 修改代码时要服从项目现有 Java 版本、框架栈和第三方依赖版本约束，不要默认按最新写法、最新 API 或最新插件 DSL 实现。
10. 命中特殊模块时，先看它的 sourceSet、自定义源码目录、生成脚本或发布脚本，不要预设它采用常规 `src/main/java` 目录结构。

## 重型工作流

### 1. 建立上下文

先读根级文件，理解：
- `settings.gradle` / `settings.gradle.kts` 里的模块注册、`pluginManagement`、`dependencyResolutionManagement`、included build
- `pom.xml`、parent BOM、`dependencyManagement`、`.mvn/`、wrapper、版本目录或共享配置里的依赖约束和构建参数
- `libs.versions.toml`、`buildSrc/`、`build-logic/`、starter、convention plugin 或团队自定义依赖映射
- `gradle.properties`、profile 配置、环境变量说明和装配脚本里的环境差异

同时识别项目当前技术栈和版本基线，例如 Java 语言级别、Gradle / Maven、Spring Boot / Micronaut / Quarkus、Jackson、Lombok、JPA / MyBatis / jOOQ、JUnit / Testcontainers、Reactor / CompletableFuture。写方案、改代码、补调用方式时，都要优先兼容现有版本，而不是套用默认的新范式。

然后只读取当前任务真正相关的目标模块文件。只有在全工作区检索表明依赖方或调用方确实相关时，再扩展到更多模块。

### 2. 全局检索

默认优先使用 `rg --no-ignore` 和 `rg --files --no-ignore`。检索范围覆盖：
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

默认至少排除：
- `**/build/**`
- `**/target/**`
- `**/.git/**`
- `**/.gradle/**`
- `**/.mvn/**`
- `venv/**`
- 其它明显的生成物、缓存或打包产物目录

需要检索模式、查询顺序和结果分层时，再读 [search-playbook.md](search-playbook.md)。

### 3. 深查运行差异

不要只停留在 `src/main`。需要检查：
- `src/main`
- `src/test`
- `src/integrationTest`
- `src/testFixtures`
- `src/generated*`
- `application*.yml` / `application*.properties`
- Maven / Gradle profile 与装配差异
- Dockerfile、compose、部署脚本或运行参数文件

如果目标项目有多个 deployable、worker、profile、region 或环境差异，先以当前构建参数判断默认运行目标；但在修改共享逻辑、自动配置、消息链路或持久化逻辑前，必须同时评估其它变体的影响。

同名配置键、Bean 定义、SQL、schema 或自动配置类也要按覆盖关系来分析。不要只因为文件名或类名一致就判定行为一致，必须结合实际 profile、装配顺序和运行入口判断。

### 4. 高风险改动检查

在提出改动方案、落地修改或写 review 之前，先过 [risk-checklist.md](risk-checklist.md) 里的强制检查项，尤其关注：
- 跨模块影响
- 共享公共层或核心入口层
- API / DTO / 消息 / schema / 配置契约变化
- 代码生成、profile、starter 或 parent BOM 带来的差异
- 现有技术栈和版本兼容性
