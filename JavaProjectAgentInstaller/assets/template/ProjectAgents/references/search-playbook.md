# 检索手册

先确认项目是单一 git root 还是多个独立 git root。确认后仍按全工作区检索；如果项目确实包含多个 git root，不要把搜索限制在当前 root。所有 `rg` / `rg --files` 搜索都必须加 `--no-ignore`，完全不考虑 `.gitignore`。

对大文件、生成代码、schema、常量汇总文件、依赖清单，不要默认全量读取。先 `rg --no-ignore -n` 搜目标常量、关键字、调用点，再按命中行号读取局部上下文。

## 默认范围

检索范围覆盖：
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
- 打包产物、生成物和缓存目录

## 推荐命令

列出候选文件：

```bash
rg --files --no-ignore . \
  -g '**/*.java' -g '**/*.kt' -g '**/*.groovy' -g '**/*.gradle' -g '**/*.gradle.kts' -g '**/pom.xml' -g '**/*.xml' \
  -g '**/gradle.properties' -g '**/*.toml' -g '**/*.yml' -g '**/*.yaml' -g '**/*.properties' -g '**/*.sql' \
  -g '**/*.proto' -g '**/*.avsc' -g '**/Dockerfile*' \
  -g '!**/build/**' -g '!**/target/**' -g '!**/.git/**' -g '!**/.gradle/**' -g '!**/.mvn/**' -g '!venv/**'
```

检索内容：

```bash
rg --no-ignore -n "PATTERN" . \
  -g '**/*.java' -g '**/*.kt' -g '**/*.groovy' -g '**/*.gradle' -g '**/*.gradle.kts' -g '**/pom.xml' -g '**/*.xml' \
  -g '**/gradle.properties' -g '**/*.toml' -g '**/*.yml' -g '**/*.yaml' -g '**/*.properties' -g '**/*.sql' \
  -g '**/*.proto' -g '**/*.avsc' -g '**/Dockerfile*' \
  -g '!**/build/**' -g '!**/target/**' -g '!**/.git/**' -g '!**/.gradle/**' -g '!**/.mvn/**' -g '!venv/**'
```

命中大文件后读取局部片段：

```bash
sed -n 'START,ENDp' PATH
```

不要对大文件直接做整段展开，例如：
- `sed -n '1,400p' PATH`
- `cat PATH`
- 一次性读取整个 schema、常量表、生成代码文件

## 查询清单

### 类

按这个顺序搜索：
1. 简单类名
2. 全限定名
3. `import`
4. 继承与实现关系
5. 构造调用和工厂调用
6. 反射或字符串引用

### 方法与字段

不要只查直接代码调用，还要检查：
- XML / YAML / properties 配置绑定
- Spring / Jakarta / 框架注解
- `import`
- 反射、字符串 Bean 名称、配置键引用
- build 常量和 profile 引用
- SQL、schema、序列化字段映射
- 如果字段来自大表文件，先查字段名和调用点，再回读字段定义附近上下文

### 配置与入口

必须跨 Java、Kotlin、Groovy、XML、YAML、properties 一起检索，不要假设配置或入口只会在所属模块内使用。

同名配置键、Bean、profile 文件、topic、SQL 或 schema 必须额外检查覆盖关系。它们可能同时定义在 `src/main`、`src/test`、`src/integrationTest`、`application-*.yml`、Maven / Gradle profile 或生成目录中，名字一样但具体值、行为或引用目标不同。分析时要同时给出：
- 配置名或入口对应的全部定义位置
- 当前运行变体实际命中的定义
- 其它关键 profile 是否命中不同定义
- 修改后是否会改变覆盖关系

### 数据与协议

涉及数据库、消息或外部协议时，不要只查 Java 调用点，还要补查：
- `db/migration`、`changelog`、`schema.sql`
- `*.proto`、`*.avsc`、OpenAPI / GraphQL 描述文件
- 消息 topic、consumer group、routing key、event name
- DTO、序列化注解、mapper 或转换器

## 结果分类

输出结果时，尽量分成四类：
- 定义位置
- 直接引用
- 间接影响
- runtime / profile 差异点

## 文档回写提醒

如果在检索过程中发现的是稳定的新结构、新规则或高频误区，不要只在当前回答里口头说明。应把结论回写到：
- `ProjectAgents/ProjectAgents.md`：适合全局规则
- `ProjectAgents/references/*.md`：适合专题化补充
