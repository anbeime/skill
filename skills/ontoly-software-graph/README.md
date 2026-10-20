# Ontoly Software Graph

使用 Ontoly 的确定性 Software Graph 和 MCP 能力，让 AI 编程代理在搜索源码之前，优先基于图谱证据理解代码库。

## 适用场景

- 架构审查
- 请求链路追踪
- 依赖分析
- 重构影响分析
- 配置与环境变量审计
- 服务、模块、控制器、路由定位
- 代码库 onboarding

## 核心原则

1. 先确认 Ontoly graph 是否存在。
2. 如果缺失且允许本地分析，运行 `ontoly build .`。
3. 优先使用 Ontoly CLI 或 MCP 查询 graph。
4. 只有当 graph 无法回答、过期或不完整时，才回退到源码搜索。
5. 回答必须包含节点、边、源码位置、诊断或框架分析等证据。

## 安装 Ontoly

```bash
npm install -D ontoly
```

或使用 pnpm：

```bash
pnpm add -D ontoly
```

## 示例问题

- Explain this repository.
- Trace the login request.
- Which service owns authentication?
- What breaks if I remove `UserRepository`?
- Which packages depend on `AuthModule`?

