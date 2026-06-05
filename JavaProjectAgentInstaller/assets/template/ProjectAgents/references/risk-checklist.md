# 风险检查清单

在实际修改前以及写 review 时，都要过这份清单。

## 强制检查项

- 确认改动是否跨模块影响。
- 确认是否同时影响多个 runtime profile、deployable、worker、CLI 入口或 sourceSet 路径。
- 确认链路是否经过 `[ENTRY_MODULE]`、`[CORE_SHARED_MODULE]`、`[API_CONTRACT_MODULE]` 或其它高聚合公共层。
- 确认是否涉及 `[API_CONTRACT_MODULE]`、`[WEB_ENTRY_PATTERN]`、`[MESSAGING_OR_EVENT_PATTERN]`、`[PERSISTENCE_PATTERN]` 的契约、接口、DTO、事件名、序列化结构或服务查找逻辑变化。
- 确认受影响模块是否可能因为 profile、自动配置、feature toggle、代码生成、annotation processor 或构建参数而切到另一套实现。
- 确认是否依赖了 parent BOM、starter、generated-code 模块或其它当前未纳入稳定源码认知的依赖，尤其是 `[SPECIAL_MODULE_OR_DEPENDENCY]`。
- 确认改动是否依赖配置覆盖、环境变量、部署脚本或 Gradle / Maven 行为。
- 确认改动是否符合项目现有 Java 版本、框架栈和第三方开源技术栈约束。

## 技术栈与版本检查

先从根级和目标模块文件确认当前版本基线，再决定实现方式。至少留意：
- Java 语言级别
- Gradle / Maven 版本与插件 DSL
- Spring Boot / Spring Cloud / Micronaut / Quarkus / Jakarta EE
- Jackson / Gson / 序列化库
- Lombok / MapStruct / annotation processor
- JPA / Hibernate / MyBatis / jOOQ / JdbcTemplate
- Reactor / CompletableFuture / 调度框架
- JUnit / Mockito / Testcontainers / ArchUnit
- 打包、镜像或发布插件

不要默认引入或使用只适配更高版本技术栈的写法，例如：
- 仅适用于更高 Java 版本的语言特性、集合 API 或并发 API
- 仅适用于更新 Gradle / Maven 插件 DSL 的配置方式
- 当前项目未使用或版本不兼容的框架注解、starter、自动配置能力
- 与现有序列化、持久化、消息、异步库版本不兼容的调用方式、适配器或扩展

如果需要推断某个实现是否安全，先回到依赖脚本、版本目录、根级 Gradle 配置和目标模块 `build.gradle` / `build.gradle.kts` 里核对版本与现有用法，再决定是否修改。

## Java / Kotlin 安全编码检查

- Java 中访问对象属性前必须检查 null，必要时使用项目既有注解；Kotlin 中优先使用 `?.`、`?:`、`?.let` 等空安全写法，避免 `!!`。
- 外部传入参数、网络 / 数据库 / JSON 返回值、跨模块 DTO 字段都要做空值兜底，不要假设服务方一定返回完整数据。
- 数组、List、Map、JSONArray 等访问前必须确认空值和边界；不要直接用不可信 index 访问集合。
- 集合判空优先沿用项目既有工具和扩展函数，不要重复新增等价工具。
- 遍历集合时避免在遍历过程中直接修改原集合；需要修改时使用副本、迭代器或明确安全的集合 API。
- 使用 Stream、CompletableFuture、Reactor 或 Rx 风格链路时，确认异常传播、线程切换和副作用边界，不要把带副作用的逻辑藏进 `map` / `peek` 之类操作里。
- 涉及 IO、数据库连接、文件句柄时，确认资源关闭策略，优先复用项目已有封装。

## Spring / 框架检查

- 如果项目使用 Spring，检查 `@Transactional`、`@Async`、`@Scheduled`、`@ConfigurationProperties`、`@Conditional*` 的边界和代理生效条件。
- 检查 Bean 生命周期、作用域、自动配置顺序和 profile 条件，避免改动只在本地 profile 生效或只在测试环境可用。
- 调整 controller / client / DTO 时，确认序列化字段名、默认值、校验注解和兼容性。
- 如果项目使用 Micronaut / Quarkus / Jakarta EE 等其它框架，也要检查对应的注入、配置绑定和 native / build-time 特性是否受影响。

## 并发与资源检查

- 线程池、Scheduler、连接池、缓存、全局 client、监听器等长生命周期对象不要无边界增长，也不要把请求态对象泄漏到全局。
- 修改异步逻辑时确认超时、重试、幂等、背压或并发限制，避免把原本串行的逻辑意外改成并行。
- 消息消费者、定时任务、批处理任务要确认重复执行和失败重试时是否安全。
- 使用缓存时优先沿用项目已有缓存策略，不要无边界持有大对象集合。

## 配置与运行差异检查

如果工作区存在多 profile、多入口或多 sourceSet，不要只看：
- `src/main`
- 公共 `build.gradle` / `pom.xml`
- 当前激活的默认运行参数

还要检查：
- `src/test`
- `src/integrationTest`
- `src/testFixtures`
- `src/generated*`
- `application-*.yml` / `application-*.properties`
- Maven / Gradle profile
- 部署脚本、Dockerfile、compose 或环境变量文档

对于配置和契约改动，额外确认：
- 是否存在同名配置键、Bean、SQL、schema 或消息主题分别定义在多个 profile / sourceSet
- 当前运行变体命中的是否其实不是同一份配置或实现
- 修改是否会只影响一个环境，或意外改变另一个环境的覆盖结果

如果目标模块存在额外装配脚本、协议文件或代码生成配置，也要把 `[MODULE_EXTRA_CONTEXT_FILES]` 补成真实文件名并列入检查项。

## 验证建议

选择能覆盖真实风险的最小验证方式：
- 优先查找并复用项目已有的 `test/`、`integrationTest/`、contract test、Testcontainers、ArchUnit、Checkstyle、PMD、SpotBugs、Error Prone 或自定义 Gradle / Maven 校验任务。
- 直接改动源码模块的 compile / test
- 受影响功能入口的最小回归路径
- 共享逻辑在多 profile、多入口间分支选择时的环境敏感验证
- 配置、消息、数据库、代码生成或依赖解析相关的构建验证

如果无法完成验证，要明确说明，并点出剩余风险。

## tools 提醒

如果项目里已有 `tools/`、`scripts/`、`gradle task`、`mvn` wrapper 或团队内部扫描脚本能覆盖大范围检索、代码生成、schema 校验或依赖分析，优先复用，而不是重新写一套。
