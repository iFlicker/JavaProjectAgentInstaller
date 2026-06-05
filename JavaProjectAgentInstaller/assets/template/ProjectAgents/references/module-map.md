# 模块地图

用这份地图辅助判断模块职责和风险，不要把它当成全工作区检索的替代品。

> 把下面的示例模块名替换成目标项目真实结构；不适用的层级直接删掉。

## 分层

- `[ENTRY_MODULE]`：主服务、CLI、worker 或运行装配入口；聚合度高，通常负责 Bean 装配、启动配置和外部暴露入口。
- `[API_CONTRACT_MODULE]`：如果项目确实存在独立的 API、DTO、client、SPI 或 contract 层，就把它写在这里；如果没有，就删掉这一层，不要为了套模板强行抽象。
- `[CORE_SHARED_MODULE]`：共享业务逻辑、通用能力、领域模型或公共工具。
- `[INFRASTRUCTURE_MODULE]`：数据库、缓存、消息、搜索、外部 SDK 等基础设施接入。
- `[INTEGRATION_MODULES]`：对外部系统的 client、gateway、adapter 或桥接层。
- `[FEATURE_MODULE_EXAMPLES]`：按业务域拆分的上层业务模块。

## 典型模块职责

### 核心应用

- `[ENTRY_MODULE]`：主运行入口、装配层和对外暴露入口。
- `[API_CONTRACT_MODULE]`：公共 API、DTO、对外 client 或服务契约。

### 业务模块

- `[FEATURE_MODULE_EXAMPLE_A]`：业务域 A。
- `[FEATURE_MODULE_EXAMPLE_B]`：业务域 B。
- `[FEATURE_MODULE_EXAMPLE_C]`：业务域 C。

### 组件与基础能力

- `[CORE_SHARED_MODULE]`：共享业务逻辑聚合层，很多通用逻辑、常量、工具和跨域能力会落在这里。
- `[INFRASTRUCTURE_MODULE]`：数据库、缓存、消息、对象存储、搜索或外部平台接入。
- `[INTEGRATION_MODULES]`：对外部系统的适配、桥接和 client 层。
- `[SPECIAL_MODULE_OR_DEPENDENCY]`：parent BOM、starter、历史共享库、generated-code 模块或高影响面模块。

### 服务与契约

- `[API_CONTRACT_MODULE]`：服务接口、DTO、client、SPI 或 facade 层；如果项目没有这一层，就删掉这里的描述。
- `[WEB_ENTRY_PATTERN]`：如果项目存在统一的 Web / RPC 入口风格，就把真实方案写清楚。
- `[MESSAGING_OR_EVENT_PATTERN]`：如果项目存在统一的消息或事件机制，就把真实方案写清楚。
- `[PERSISTENCE_PATTERN]`：如果项目存在统一的持久化组织方式，就把真实方案写清楚。

## 模块间通信

- 先确认项目真实的跨模块通信方式，再写规则。有些项目通过 service 接口、Facade、shared contract、事件、client 模块通信，也有些项目允许 feature/domain/data 直接依赖。
- 把目标项目现有的 Web / RPC 入口、消息机制、持久化约定补到这里，例如 `[WEB_ENTRY_PATTERN]`、`[MESSAGING_OR_EVENT_PATTERN]`、`[PERSISTENCE_PATTERN]`。
- 调整跨模块接口、DTO、事件名、topic、序列化结构或服务查找逻辑时，要同时检查定义方、实现方、调用方和运行 profile 差异。

## 依赖规则

- 不要默认套用“业务模块不能直接依赖”这类规则。先把项目真实的依赖方向写清楚：哪些依赖被禁止，哪些通过服务层走，哪些允许按 feature/domain/data 分层直连。
- 业务模块、shared module、infra module、client / adapter 模块之间的允许依赖方向，也按项目真实规则补充，不要保留空泛描述。
- 修改 Gradle / Maven 依赖前先判断是否真的进入重型模式，避免在普通业务问题中过早展开构建上下文。

## 高关注区域

- `[ENTRY_MODULE]`：聚合度最高、最敏感的运行核心模块
- `[CORE_SHARED_MODULE]`：共享能力集中，改动容易波及多个业务域
- `[API_CONTRACT_MODULE]`：契约层，改动容易形成跨模块破坏
- `[SPECIAL_MODULE_OR_DEPENDENCY]`：parent BOM、starter、generated-code 模块或高耦合模块

## 实用阅读顺序

1. 默认先定位目标类、资源、页面或路由所在模块。
2. 再读目标模块内的直接调用链、配置和测试。
3. 如果影响跨越运行入口、服务契约或装配边界，再检查：
- `[ENTRY_MODULE]`
- `[CORE_SHARED_MODULE]`
- `[API_CONTRACT_MODULE]`
- `[WEB_ENTRY_PATTERN]`
- `[MESSAGING_OR_EVENT_PATTERN]`
- `[PERSISTENCE_PATTERN]`
- 实际存在的自动配置、profile 和生成代码链路

## 技术栈提醒

模块分析不要脱离根工程版本基线。很多模块是独立版本化、可发布的，但实现时仍受根级依赖映射、Java 编译配置和项目现有主流技术栈约束。
